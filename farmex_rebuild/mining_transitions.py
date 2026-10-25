"""004779dc start and476c7c/476d44 candidate queries. Pure captured replay."""
from dataclasses import dataclass
from typing import Optional
from collections.abc import Mapping
from mining_configuration import MiningPanelConfiguration

@dataclass(frozen=True)
class MiningOreStartPlan:
    status:str
    complete:bool
    calls:tuple=()
    writes:tuple=()
    missing:str=''
    native_execution_verified:bool=False
    server_acknowledged:bool=False

class _Missing(Exception):pass

def plan_mining_ore_start(configuration,observations):
    if not isinstance(configuration,MiningPanelConfiguration) or not isinstance(observations,Mapping):raise ValueError('Typed inputs required')
    calls=[];writes=[]
    def need(key,bits=32):
        value=observations.get(key)
        if value is None:raise _Missing(key)
        if type(value) is not int or not 0<=value<(1<<bits):raise ValueError('Raw observation required')
        return value
    def call(address,*args):
        calls.append((address,args));key='returned:'+address;value=observations.get(key)
        if value is not None and type(value) is not bool:raise ValueError('Explicit normal return required')
        if value is not True:raise _Missing(key)
    try:
        if need('gate_4631a8',8)==1:call('004c806c',0x561ef8,0)
        flag=configuration.fields.get(0x6046)
        if flag is None:raise _Missing('panel+6046')
        if type(flag) is not int or not 0<=flag<=255:raise ValueError('Raw extraction flag required')
        if flag:
            match=need('name_first_equal',8)!=0
            if not match:match=need('name_second_equal',8)!=0
            if match:
                slot=need('free_slot_463a8c')&0xffff
                writes.append(('object+5f70',slot,32))
                if slot!=0xff:
                    name=observations.get('fresh_slot6_name')
                    if name is None:raise _Missing('fresh_slot6_name')
                    if type(name) is not bytes:raise ValueError('Fresh managed ANSI bytes required')
                    writes.append(('object+5f74',name,'ansi'))
                    writes.append(('object+5f70',slot+14,32))
                    call('0046526c',6,0)
        writes.extend((('global+561f6c',0,8),('object+5f54',1,8),
                       ('object+5f58',0,32),('object+5f68',14,32)))
        tick=need('start_tick');writes.extend((('object+5f60',tick,32),('object+5f64',0,32)))
        return MiningOreStartPlan('ore_start_planned',True,tuple(calls),tuple(writes))
    except _Missing as exc:
        return MiningOreStartPlan('needs_observation',False,tuple(calls),tuple(writes),str(exc))

@dataclass(frozen=True)
class MiningCandidateSlot:
    classifier_index:Optional[int]=None
    rule_flag:Optional[int]=None

    def __post_init__(self):
        for value,maximum in ((self.classifier_index,0xffffffff),(self.rule_flag,255)):
            if value is not None and (type(value) is not int or not 0<=value<=maximum):raise ValueError('Raw candidate observation required')

@dataclass(frozen=True)
class MiningCandidatePlan:
    status:str
    complete:bool
    available:Optional[bool]=None
    checked_slots:tuple=()
    rule_reads:tuple=()
    missing:str=''
    independently_verified:bool=False

def plan_mining_candidates(kind,configuration,slots):
    if kind not in ('sell','bank') or not isinstance(configuration,MiningPanelConfiguration) or not isinstance(slots,Mapping):raise ValueError('Typed candidate query inputs required')
    vip=configuration.fields.get(0x604c)
    if vip is None:return MiningCandidatePlan('needs_observation',False,missing='panel+604c')
    if type(vip) is not int or not 0<=vip<=255:raise ValueError('Raw VIP flag required')
    if vip:return MiningCandidatePlan('vip_short_circuit',True,True)
    checked=[];reads=[];offset=6 if kind=='sell' else 4
    for slot in range(14,42):
        checked.append(slot);o=slots.get(slot)
        if o is None or (isinstance(o,MiningCandidateSlot) and o.classifier_index is None):
            return MiningCandidatePlan('needs_observation',False,checked_slots=tuple(checked),rule_reads=tuple(reads),missing='slot%d classifier index'%slot)
        if not isinstance(o,MiningCandidateSlot):raise ValueError('Typed slot observation required')
        if o.classifier_index&0x80000000:continue
        reads.append((o.classifier_index,offset))
        if o.rule_flag is None:
            return MiningCandidatePlan('needs_observation',False,checked_slots=tuple(checked),rule_reads=tuple(reads),missing='slot%d rule BYTE'%slot)
        if o.rule_flag:return MiningCandidatePlan('candidate_found',True,True,tuple(checked),tuple(reads))
    return MiningCandidatePlan('no_candidate',True,False,tuple(checked),tuple(reads))
