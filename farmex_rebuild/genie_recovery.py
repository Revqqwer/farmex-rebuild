"""4ca588 Spirit-of-Genie scan and own7byte queue; no real inventory or send."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState,enqueue
from direct_chat_packets import QueueAttempt
from mining_slot_name import SlotNameObservation,plan_slot_name
from upgrade_packets import UpgradeItemObservation,plan_upgrade_item
from inventory_getter_frames import InventoryGetterFrame

TARGET_NAME=b'Spirit of Genie'
TEMPLATE=bytes.fromhex('97010100000000')
def raw(value,optional=False):
    if optional and value is None:return
    if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw recovery DWORD required')

@dataclass(frozen=True)
class RecoverySlotSample:
    name_bytes:object=None
    comparison_eax:object=None
    item_id_eax:object=None
    name_inputs:object=None
    item_inputs:object=None
    def __post_init__(self):
        if self.name_bytes is not None and type(self.name_bytes) is not bytes:raise ValueError('Immutable final ANSI name snapshot required')
        raw(self.comparison_eax,True);raw(self.item_id_eax,True)
        if self.name_inputs is not None and not isinstance(self.name_inputs,SlotNameObservation):raise ValueError('Typed slot-name input required')
        if self.item_inputs is not None and not isinstance(self.item_inputs,UpgradeItemObservation):raise ValueError('Typed item-ID input required')

@dataclass(frozen=True)
class GenieRecoveryObservation:
    samples:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    attempt:QueueAttempt=field(default_factory=QueueAttempt)
    def __post_init__(self):
        samples=dict(self.samples);returns=dict(self.normal_returns)
        if any(type(k) is not int or not 14<=k<=41 for k in samples):raise ValueError('Source absolute slots14..41 required')
        if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate recovery normal receipts required')
        if not isinstance(self.attempt,QueueAttempt):raise ValueError('Typed single enqueue attempt required')
        object.__setattr__(self,'samples',MappingProxyType(samples));object.__setattr__(self,'normal_returns',MappingProxyType(returns))

@dataclass(frozen=True)
class GenieRecoveryScan:
    complete:bool
    visited_slots:tuple=()
    selected_slot:object=None
    item_id:object=None
    payload:object=None
    calls:tuple=()
    missing:str=''
    needed:object=None
    owned_byte_compare:bool=False
    native_equivalence_verified:bool=False
    getter_executions:tuple=()

class _Missing(Exception):
    def __init__(self,needed,label):self.needed=needed;super().__init__(label)

def plan_genie_recovery_scan(o,*,owned_byte_compare=False,target_name=TARGET_NAME,payload_template=TEMPLATE,frame_setup_required=True):
    if not isinstance(o,GenieRecoveryObservation) or type(owned_byte_compare) is not bool:raise ValueError('Typed recovery scan and explicit comparison policy required')
    if type(target_name) is not bytes or type(frame_setup_required) is not bool:raise ValueError('Immutable scan literal and explicit setup policy required')
    if payload_template is not None and (type(payload_template) is not bytes or len(payload_template)!=7):raise ValueError('Seven-byte recovery template or explicit scan-only policy required')
    visited=[];calls=[];selected=None;item=None;getters=[]
    def result(ok,error=None,payload=None):return GenieRecoveryScan(ok,tuple(visited),selected,item,payload,tuple(calls),'' if error is None else str(error),None if error is None else error.needed,owned_byte_compare,getter_executions=tuple(getters))
    def normal(label,helper,semantic_args=()):
        calls.append((helper,semantic_args,label))
        if o.normal_returns.get(label) is not True:raise _Missing(('normal',label),label+' normal return')
    def value(slot,field):
        sample=o.samples.get(slot)
        if sample is not None and not isinstance(sample,RecoverySlotSample):raise ValueError('Typed reached recovery slot required')
        v=None if sample is None else getattr(sample,field)
        bound_field={'name_bytes':'name_inputs','item_id_eax':'item_inputs'}.get(field)
        bound=None if sample is None or bound_field is None else getattr(sample,bound_field)
        if bound is not None:
            child=plan_slot_name(slot,bound) if bound_field=='name_inputs' else plan_upgrade_item(slot,bound)
            getters.append((slot,bound_field,child))
            resolved=child.ansi_bytes if bound_field=='name_inputs' else child.result_dword
            if resolved is None:raise _Missing(('bound',slot,bound_field),'slot%d %s: %s'%(slot,bound_field,child.missing))
            if v is not None and v!=resolved:raise ValueError('Recovery raw result differs from bound inventory getter')
            return resolved
        if v is None:raise _Missing(('sample',slot,field),'slot%d %s'%(slot,field))
        return v
    try:
        if frame_setup_required:normal('frame_setup','opaque_frame_setup')
        for slot in range(14,42):
            visited.append(slot)
            normal('setup:%d'%slot,'opaque_literal_and_name_object_setup')
            normal('name:%d'%slot,'00463670',(slot,));name=value(slot,'name_bytes')
            normal('compare:%d'%slot,'source_equality_wrapper',(slot,))
            comparison=int(name==target_name) if owned_byte_compare else value(slot,'comparison_eax')
            if comparison not in (0,1):raise ValueError('Source equality wrapper returns only DWORD0/1')
            # Source saves comparison EAX across both object cleanup calls.
            normal('cleanup:%d'%slot,'opaque_two_object_cleanup')
            if comparison:
                selected=slot;normal('item:%d'%slot,'004634a4',(slot,));item=value(slot,'item_id_eax')
                if item and payload_template is not None:
                    payload=bytearray(payload_template);payload[3:7]=item.to_bytes(4,'little')
                    return result(True,payload=bytes(payload))
                return result(True) #First name match stops, even if fresh ID is zero.
        item=0;return result(True)
    except _Missing as error:return result(False,error)

class GenieRecoveryScanFrame:
    def __init__(self,*,owned_byte_compare=False,target_name=TARGET_NAME,payload_template=TEMPLATE,frame_setup_required=True):
        if type(owned_byte_compare) is not bool:raise ValueError('Explicit comparison policy required')
        self.owned_byte_compare=owned_byte_compare;self.observation=GenieRecoveryObservation();self.final=None;self.getter_frames={}
        self.scan_options=dict(target_name=target_name,payload_template=payload_template,frame_setup_required=frame_setup_required)
    def advance(self,o):
        if not isinstance(o,GenieRecoveryObservation):raise ValueError('Typed recovery observation required')
        if self.final is not None:return self.final
        for _ in range(256):
            p=plan_genie_recovery_scan(self.observation,owned_byte_compare=self.owned_byte_compare,**self.scan_options)
            if p.complete:self.final=p;return p
            if p.needed[0]=='normal':
                label=p.needed[1]
                if o.normal_returns.get(label) is not True:return p
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
            else:
                _,slot,field=p.needed;sample=o.samples.get(slot)
                if sample is None:return p
                if not isinstance(sample,RecoverySlotSample):raise ValueError('Typed reached recovery slot required')
                bound_field=field if p.needed[0]=='bound' else {'name_bytes':'name_inputs','item_id_eax':'item_inputs'}.get(field)
                bound=None if bound_field is None else getattr(sample,bound_field)
                key=(slot,bound_field)
                if bound is not None or key in self.getter_frames:
                    frame=self.getter_frames.setdefault(key,InventoryGetterFrame(slot,name=bound_field=='name_inputs'))
                    child=frame.advance(bound or (SlotNameObservation() if bound_field=='name_inputs' else UpgradeItemObservation()))
                    resolved=child.ansi_bytes if bound_field=='name_inputs' else child.result_dword
                    raw_field='name_bytes' if bound_field=='name_inputs' else 'item_id_eax'
                    observed=getattr(sample,raw_field)
                    if resolved is not None and observed is not None and observed!=resolved:raise ValueError('Recovery raw result differs from bound inventory getter')
                    cached=self.observation.samples.get(slot,RecoverySlotSample())
                    self.observation=replace(self.observation,samples={**self.observation.samples,slot:replace(cached,**{bound_field:frame.observation})})
                    p=plan_genie_recovery_scan(self.observation,owned_byte_compare=self.owned_byte_compare,**self.scan_options)
                    if not p.complete and p.needed[0]=='bound':return p
                    continue
                v=getattr(sample,field)
                if v is None:return p
                cached=self.observation.samples.get(slot,RecoverySlotSample())
                self.observation=replace(self.observation,samples={**self.observation.samples,slot:replace(cached,**{field:v})})
        raise ValueError('Recovery scan exceeded28slot normal-path budget')

@dataclass(frozen=True)
class GenieRecoveryPlan:
    complete:bool
    context_dword:int
    scan:GenieRecoveryScan
    queue:QueueState
    return_low_al:object=None
    source_return_eax:object=None
    enqueue_decision:object=None
    missing:str=''
    helper:str='004ca588'
    native_execution_verified:bool=False
    packet_delivery_verified:bool=False
    Genie_effect_verified:bool=False
    @property
    def push_order(self):return (self.context_dword,)

class GenieRecoveryFrame:
    def __init__(self,context_dword,queue=None,*,owned_byte_compare=False):
        raw(context_dword);self.context=context_dword;self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own recovery queue required')
        self.scan_frame=GenieRecoveryScanFrame(owned_byte_compare=owned_byte_compare);self.decision=None;self.gate=None;self.enqueue_returned=False;self.final=None
    def advance(self,o):
        if not isinstance(o,GenieRecoveryObservation):raise ValueError('Typed recovery observation required')
        if self.final is not None:return self.final
        scan=self.scan_frame.advance(o)
        def result(ok=False,missing=''):
            low=(1 if scan.payload is not None else 0) if ok else None
            return GenieRecoveryPlan(ok,self.context,scan,self.queue,low,0 if low==0 else None,self.decision,missing)
        if not scan.complete:return result(missing=scan.missing)
        if scan.payload is not None:
            if self.decision is None:
                if self.gate is None and o.attempt.gate is not None:self.gate=o.attempt.gate
                decision=enqueue(self.queue,scan.payload,7,0,self.gate,o.attempt.tick if self.gate else None)
                if decision.state is None:return result(missing=decision.missing)
                self.queue=decision.state;self.decision=decision
            if not self.enqueue_returned:
                if o.attempt.normal_returned is not True:return result(missing='enqueue helper normal return')
                self.enqueue_returned=True
        if o.normal_returns.get('return_span') is not True:return result(missing='recovery return span normal return')
        self.final=result(True);return self.final
