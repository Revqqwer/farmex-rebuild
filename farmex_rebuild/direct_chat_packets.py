"""Source direct Mage/Rogue/Priest chat builders and own queue frames.

No original/native code execution, real allocation, network send or skill ACK.
Copy semantics are normal-path projections into bounded own bytearrays.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState,enqueue

FIRST_TEMPLATE=bytes.fromhex('3101000000000000000000000000000000000000000000000000000000000000000000000000000000000f0000000000')
TP_SECOND_TEMPLATE=bytes.fromhex('31030000000000000000000000000000000000000000000000000000000000000000')
PRIEST_SECOND_TEMPLATE=bytes.fromhex('3103000000000000000000000000000000000000000000000000')
SW_SECOND_TEMPLATE=bytes.fromhex('3103000000000000000000000000000000000000000000000000000000000000000000000000')
WOLF_FIRST_TEMPLATE=bytes.fromhex('31010000000000000000ffffffff00000000000000000000000000000000000000000000000000000000110000000000')
WOLF_SECOND_TEMPLATE=bytes.fromhex('31030000000000000000ffffffff000000000000000000000000000000000000000000000000')
FIXED_RELATIVES={'0049e8c8':4,'004d3674':0x20d,'004d3690':0x217,'004d36ac':4,'004e08e0':10,'004e103c':30}
#first,second,target-copy width,zero-guard width,coordinate layout,second delay.
DIRECT_LAYOUTS=MappingProxyType({
 '0049e8c8':(FIRST_TEMPLATE,TP_SECOND_TEMPLATE,4,0,'tp',1500),
 '004d3568':(FIRST_TEMPLATE,PRIEST_SECOND_TEMPLATE,2,2,'',1500),
 '004d3674':(FIRST_TEMPLATE,PRIEST_SECOND_TEMPLATE,2,2,'',1500),
 '004d3690':(FIRST_TEMPLATE,PRIEST_SECOND_TEMPLATE,2,2,'',1500),
 '004d36ac':(FIRST_TEMPLATE,PRIEST_SECOND_TEMPLATE,4,4,'',1500),
 '004e08e0':(FIRST_TEMPLATE,SW_SECOND_TEMPLATE,2,0,'',1500),
 '004e103c':(WOLF_FIRST_TEMPLATE,WOLF_SECOND_TEMPLATE,0,0,'wolf',1700)})
def _raw(v,optional=False):
    if optional and v is None:return
    if type(v) is not int or not 0<=v<=0xffffffff:raise ValueError('Raw direct-packet DWORD required')

@dataclass(frozen=True)
class DirectChatArgs:
    helper:str
    context_dword:int
    target_argument_dword:object=None
    relative_skill:object=None
    def __post_init__(self):
        if self.helper not in DIRECT_LAYOUTS:raise ValueError('Known direct builder helper required')
        _raw(self.context_dword)
        if self.helper=='004e103c':
            if self.target_argument_dword is not None:raise ValueError('Wolf source helper has no target argument')
        else:_raw(self.target_argument_dword)
        if self.helper=='004d3568':_raw(self.relative_skill)
        else:
            fixed=FIXED_RELATIVES[self.helper]
            if self.relative_skill is not None:_raw(self.relative_skill)
            if self.relative_skill is not None and self.relative_skill!=fixed:raise ValueError('Fixed helper relative skill differs from source')
            object.__setattr__(self,'relative_skill',fixed)
    @property
    def push_order(self):
        if self.helper=='004e103c':return (self.context_dword,)
        if self.helper=='004d3568':return (self.target_argument_dword,self.relative_skill,self.context_dword)
        return (self.target_argument_dword,self.context_dword)

@dataclass(frozen=True)
class QueueAttempt:
    gate:object=None
    tick:object=None
    normal_returned:object=None
    def __post_init__(self):
        _raw(self.gate,True);_raw(self.tick,True)
        if self.normal_returned is not None and type(self.normal_returned) is not bool:raise ValueError('Separate enqueue normal receipt required')

@dataclass(frozen=True)
class DirectChatObservation:
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    enqueues:tuple=()
    def __post_init__(self):
        values=dict(self.values);returns=dict(self.normal_returns)
        for v in values.values():_raw(v)
        if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate direct helper normal receipts required')
        if type(self.enqueues) is not tuple or any(not isinstance(v,QueueAttempt) for v in self.enqueues):raise ValueError('Two positional own enqueue observations required')
        object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(returns))

@dataclass(frozen=True)
class DirectChatBuildPlan:
    complete:bool
    args:DirectChatArgs
    status:str
    action_id:object=None
    payloads:tuple=()
    steps:tuple=()
    missing:str=''
    needed:object=None
    native_execution_verified:bool=False
    input_snapshot:object=None

class _Missing(Exception):
    def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+(' normal return' if kind=='normal' else ' value'))

def plan_direct_chat_packets(args,o):
    if not isinstance(args,DirectChatArgs) or not isinstance(o,DirectChatObservation):raise ValueError('Typed direct arguments/observations required')
    steps=[];action=None
    def result(ok,status,payloads=(),error=None):
        return DirectChatBuildPlan(ok,args,status,action,payloads,tuple(steps),'' if error is None else str(error),None if error is None else error.needed,input_snapshot=o)
    def normal(label):
        steps.append(('normal_return',label))
        if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
    def value(label):
        steps.append(('source_value',label))
        if label not in o.values:raise _Missing('value',label)
        return o.values[label]
    def put(buf,offset,width,v):buf[offset:offset+width]=v.to_bytes(4,'little')[:width]
    try:
        normal('frame_setup');normal('class_getter');cls=value('class_eax')
        action=(cls*1000+args.relative_skill)&0xffffffff
        normal('actor_getter');actor=value('actor_eax')
        first_template,second_template,target_width,guard_width,coordinate_mode,delay=DIRECT_LAYOUTS[args.helper]
        if guard_width and args.target_argument_dword&((1<<(guard_width*8))-1)==0:
            return result(True,'source_zero_target_'+('WORD' if guard_width==2 else 'DWORD')+'_skip')
        coords={}
        if coordinate_mode:
            for axis in ('x','y','z'):
                normal(axis+'_getter');coords[axis]=value(axis+'_eax')
        first=bytearray(first_template);second=bytearray(second_template)
        for buf in (first,second):
            put(buf,2,4,action);put(buf,6,4,actor)
            if target_width:put(buf,10,target_width,args.target_argument_dword)
        if coordinate_mode:
            axes=('x','y','z') if coordinate_mode=='tp' else ('x','z','y')
            for buf in (second,) if coordinate_mode=='tp' else (first,second):
                for offset,axis in zip((14,18,22),axes):put(buf,offset,4,coords[axis])
        steps.append(('owned_bounded_copy_projection',len(first),len(second)))
        return result(True,'packets_built',((bytes(first),0),(bytes(second),delay)))
    except _Missing as error:return result(False,'needs_observation',error=error)

@dataclass(frozen=True)
class DirectChatExecutionPlan:
    complete:bool
    build:DirectChatBuildPlan
    queue:QueueState
    enqueue_decisions:tuple=()
    missing:str=''
    native_execution_verified:bool=False
    packet_delivery_verified:bool=False
    helper_EAX_verified:bool=False
    consumed_gates:tuple=()

class DirectChatPacketFrame:
    def __init__(self,args,queue=None):
        if not isinstance(args,DirectChatArgs):raise ValueError('Stable direct source arguments required')
        self.args=args;self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own queue required')
        self.observation=DirectChatObservation();self.build=None;self.decisions=[];self.gates={};self.phase=0;self.final=None
    def advance(self,o):
        if not isinstance(o,DirectChatObservation):raise ValueError('Typed direct observations required')
        if self.final is not None:return self.final
        def result(complete=False,missing=''):
            return DirectChatExecutionPlan(complete,self.build or p,self.queue,tuple(self.decisions),missing,consumed_gates=tuple(sorted(self.gates.items())))
        if self.build is None:
            for _ in range(20):
                p=plan_direct_chat_packets(self.args,self.observation)
                if p.complete:self.build=p;break
                kind,label=p.needed
                if kind=='normal':
                    if o.normal_returns.get(label) is not True:return result(missing=p.missing)
                    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
                else:
                    if label not in o.values:return result(missing=p.missing)
                    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
            else:raise ValueError('Direct builder exceeded source prefix budget')
        while self.phase<len(self.build.payloads):
            i=self.phase
            sample=o.enqueues[i] if i<len(o.enqueues) else QueueAttempt()
            if len(self.decisions)<=i:
                if i not in self.gates and sample.gate is not None:self.gates[i]=sample.gate
                payload,delay=self.build.payloads[i];gate=self.gates.get(i)
                decision=enqueue(self.queue,payload,len(payload),delay,gate,sample.tick if gate else None)
                if decision.state is None:return result(missing='enqueue%d: '%i+decision.missing)
                self.queue=decision.state;self.decisions.append(decision)
            if sample.normal_returned is not True:return result(missing='enqueue%d helper normal return'%i)
            self.phase+=1
        if o.normal_returns.get('return_span') is not True:return result(missing='direct return span normal return')
        self.final=result(True);return self.final

def direct_binding_gap(plan,args):
    if plan is None:return None
    if not isinstance(plan,DirectChatExecutionPlan):raise ValueError('Typed direct execution child required')
    if plan.build.args!=args:raise ValueError('Direct child arguments differ from reached consumer call')
    return None if plan.complete else plan.missing or 'incomplete direct child'

def retain_direct_snapshot(previous,new):
    """Retain consumed builder/own-queue prefix, with no live-state claim."""
    if previous is None:return new
    if previous.complete:return previous
    if previous.build.args!=new.build.args:raise ValueError('Bound direct invocation identity changed')
    a=previous.build.input_snapshot;b=new.build.input_snapshot
    if not isinstance(a,DirectChatObservation) or not isinstance(b,DirectChatObservation):raise ValueError('Generated direct builder snapshots required')
    for step in previous.build.steps:
        if step[0]=='source_value':
            label=step[1]
            if label in a.values and b.values.get(label)!=a.values[label]:raise ValueError('Consumed direct getter value changed')
        elif step[0]=='normal_return':
            label=step[1]
            if a.normal_returns.get(label) is True and b.normal_returns.get(label) is not True:raise ValueError('Consumed direct normal return regressed')
    if previous.build.complete and (not new.build.complete or previous.build.payloads!=new.build.payloads):raise ValueError('Completed direct builder changed')
    n=len(previous.enqueue_decisions)
    if new.enqueue_decisions[:n]!=previous.enqueue_decisions:raise ValueError('Consumed direct enqueue changed')
    gates=dict(new.consumed_gates)
    if any(gates.get(k)!=v for k,v in previous.consumed_gates):raise ValueError('Consumed direct gate changed')
    n=len(previous.queue.records)
    if new.queue.records[:n]!=previous.queue.records or new.queue.next_id<previous.queue.next_id:raise ValueError('Direct own queue prefix changed')
    return new
