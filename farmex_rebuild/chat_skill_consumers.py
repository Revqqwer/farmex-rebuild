"""Mage4994bc/Rogue4da568 plans and Priest delegate; no native skill execution.

Every helper/protection effect is opaque. Stores are inert projections, not
receipts of actual writes. TRUE source return promises only lowAL1.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from generic_chat_skill import GenericSkillPlan,generic_binding_gap,retain_generic_snapshot
from direct_chat_packets import DirectChatArgs,DirectChatExecutionPlan,direct_binding_gap,retain_direct_snapshot

BYTE_VALUES={'pending_byte','lock_byte','alternate_byte'}
WORD_VALUES={'direct_sender_word'}
def _raw(v,width=4):
    if type(v) is not int or not 0<=v<1<<(8*width):raise ValueError('Raw consumer observation with exact width required')
def _signed(v):return v-(1<<32) if v&0x80000000 else v

@dataclass(frozen=True)
class ChatConsumerObservation:
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    generic_execution:object=None
    direct_execution:object=None
    def __post_init__(self):
        values=dict(self.values);returns=dict(self.normal_returns)
        for name,v in values.items():_raw(v,1 if name in BYTE_VALUES else 2 if name in WORD_VALUES else 4)
        if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate consumer helper normal receipts required')
        object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(returns))
        if self.generic_execution is not None and not isinstance(self.generic_execution,GenericSkillPlan):raise ValueError('Typed bound generic skill plan required')
        if self.direct_execution is not None and not isinstance(self.direct_execution,DirectChatExecutionPlan):raise ValueError('Typed bound direct execution required')

@dataclass(frozen=True)
class ChatConsumerPlan:
    family:str
    complete:bool
    return_low_al:object=None
    stores:tuple=()
    steps:tuple=()
    missing:str=''
    needed:object=None
    true_full_eax_verified:bool=False
    native_execution_verified:bool=False
    skill_effect_verified:bool=False
    generic_execution:object=None
    actor_context_dword:object=None
    direct_execution:object=None

class _Missing(Exception):
    def __init__(self,kind,label):self.needed=(kind,label);super().__init__('bound generic: '+label if kind=='bound' else 'bound direct: '+label if kind=='direct' else label+(' normal return' if kind=='normal' else ' value'))

def plan_chat_consumer(family,context_dword,o):
    if family=='Priest':
        from priest_chat_consumer import plan_priest_chat_consumer
        return plan_priest_chat_consumer(context_dword,o)
    if family not in ('Mage','Rogue') or not isinstance(o,ChatConsumerObservation):raise ValueError('Known typed Mage/Rogue consumer required')
    _raw(context_dword);steps=[];stores=[];bound=None;direct_bound=None
    def result(low=None,error=None):
        return ChatConsumerPlan(family,error is None,low,tuple(stores),tuple(steps),'' if error is None else str(error),None if error is None else error.needed,generic_execution=bound,actor_context_dword=context_dword,direct_execution=direct_bound)
    def direct(label,helper,target=None):
        nonlocal direct_bound
        direct_bound=o.direct_execution
        gap=direct_binding_gap(direct_bound,DirectChatArgs(helper,context_dword,target))
        if gap is not None:raise _Missing('direct',gap)
        call(label,helper,(context_dword,) if target is None else (target,context_dword))
    def value(label):
        steps.append(('source_value',label))
        if label not in o.values:raise _Missing('value',label)
        return o.values[label]
    def call(label,address,pushes=()):
        steps.append(('opaque_helper',address,pushes,label))
        if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
    def store(address,width,v):stores.append((address,width,v));steps.append(('store_plan',address,width,v))
    def memory_state(prefix,offset_slot):
        slot=value(prefix+'_root_slot');steps.append(('source_global',0x553e7c,slot))
        call(prefix+'_root','0045dc44',(slot,));root=value(prefix+'_root_eax')
        offset=value(prefix+'_offset');steps.append(('source_global',offset_slot,offset))
        call(prefix+'_state','0045dc44',((root+offset)&0xffffffff,))
        return value(prefix+'_state_eax') #Source uses DWORD, not BYTE.
    def stop_movement_if_needed():
        if memory_state('movement',0x554020):call('stop_movement','00464714')
    def target_cleanup():
        call('target_probe','00462630')
        # TEST EAX,EAX clearsCF. Source JC is therefore never taken here.
        steps.append(('TEST_EAX_EAX_CF',0,'source_JC_not_taken'))
        if memory_state('target',0x55403c):
            steps.append(('push_literal_before_target_helper',0))
            call('fresh_target_id','00462630');target=value('fresh_target_eax')
            call('target_action','00465ef8',(0,target))
    def lock(delay):
        store(0x561f80,4,delay)
        call('post_delay_tick','GetTickCount');tick=value('post_delay_tick')
        store(0x561f84,4,tick);store(0x561f7e,1,1)
    def generic(skill):
        nonlocal bound
        sender=value('generic_sender_dword')
        bound=o.generic_execution
        gap=generic_binding_gap(bound,skill,sender)
        if gap is not None:raise _Missing('bound',gap)
        call('generic_skill','004655e8',(sender,skill))
        eax=value('generic_skill_eax')
        if bound is not None and eax!=bound.returned_eax:raise ValueError('Consumer EAX differs from bound generic raw return')
        if eax==0:return result(0)
        lock(2000);store(0x5693a0,1,0);return result(1)
    try:
        if value('pending_byte')==0:return result(0)
        if value('lock_byte')!=0:return result(0)
        kind=value('kind_dword')
        if family=='Mage':
            if kind!=1:return result(0)
            for label,address,threshold in (('level','00462670',10),('mage_gate','004611e0',5),('mage_gate2','004645e4',2)):
                call(label,address)
                if _signed(value(label+'_eax'))<threshold:return result(0)
            sender=value('lookup_sender_dword');call('party_lookup','004cb898',(sender,0x569584))
            index=value('party_index_eax')
            if _signed(index)<0:return result(0)
            stop_movement_if_needed();target_cleanup()
            call('select_index','00464650',(index,))
            if value('alternate_byte')!=0:return generic(4)
            lock(1500)
            sender=value('direct_sender_dword');direct('direct_mage','0049e8c8',sender)
            store(0x5693a0,1,0);return result(1)
        if kind!=1:
            if value('kind_second_dword')!=2:return result(0)
            kind=2
        call('level','00462670')
        if _signed(value('level_eax'))<(10 if kind==1 else 30):
            store(0x5693a0,1,0);return result(0)
        if value('alternate_byte')!=0:
            target_cleanup();return generic(10 if kind==1 else 30)
        lock(1500);stop_movement_if_needed()
        if kind==1:
            word=value('direct_sender_word');pushed=value('direct_sender_push_dword')
            # MOV DX,WORD leaves upperEDX unknown; require full pushed value separately.
            if pushed&0xffff!=word:raise ValueError('Observed full EDX push differs from fresh sender WORD')
            direct('direct_sw','004e08e0',pushed)
        else:direct('direct_wolf','004e103c')
        store(0x5693a0,1,0);return result(1)
    except _Missing as error:return result(error=error)

class ChatConsumerFrame:
    def __init__(self,family,context_dword):
        plan_chat_consumer(family,context_dword,ChatConsumerObservation())
        self.family=family;self.context_dword=context_dword;self.observation=ChatConsumerObservation();self.final=None
    def advance(self,o):
        if not isinstance(o,ChatConsumerObservation):raise ValueError('Typed consumer observations required')
        if self.final is not None:return self.final
        for _ in range(64):
            p=plan_chat_consumer(self.family,self.context_dword,self.observation)
            if p.complete:self.final=p;return p
            kind,label=p.needed
            if o.direct_execution is not None and (kind=='direct' or kind=='normal' and label in ('direct_mage','direct_sw','direct_wolf','direct_skill')):
                direct=retain_direct_snapshot(self.observation.direct_execution,o.direct_execution)
                self.observation=replace(self.observation,direct_execution=direct)
                p=plan_chat_consumer(self.family,self.context_dword,self.observation)
                if p.complete:self.final=p;return p
                kind,label=p.needed
            if o.generic_execution is not None and (kind=='bound' or kind=='normal' and label=='generic_skill' or kind=='value' and label=='generic_skill_eax'):
                bound=retain_generic_snapshot(self.observation.generic_execution,o.generic_execution)
                self.observation=replace(self.observation,generic_execution=bound)
                p=plan_chat_consumer(self.family,self.context_dword,self.observation)
                if p.complete:self.final=p;return p
                kind,label=p.needed
            if kind in ('bound','direct'):return p
            if kind=='normal':
                if o.normal_returns.get(label) is not True:return p
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
            else:
                if label not in o.values:return p
                self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
        raise ValueError('Consumer frame exceeded source prefix budget')
