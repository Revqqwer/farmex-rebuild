"""0040d224 manual1/leader4/AutoZ5 local call/write plans. Never execute helpers.

Repeated ID reads remain separate observations. A ready write is not evidence
that the lookup pointer is valid; AutoZ source does not test that pointer.
"""
from dataclasses import dataclass
from typing import Optional,Tuple

def raw(value,maximum=0xffffffff):
    if value is not None and (type(value) is not int or not 0<=value<=maximum):raise ValueError('Raw source value required')

@dataclass(frozen=True)
class TargetBranchObservation:
    enabled_38: Optional[int] = None
    blocked_74: Optional[int] = None
    target_ids: Tuple[Optional[int],...] = ()
    lookup_pointer: Optional[int] = None
    visibility_al: Optional[int] = None
    autoz_state: Optional[int] = None
    refresh_returned: Optional[bool] = None
    def __post_init__(self):
        raw(self.enabled_38,255);raw(self.blocked_74,255);raw(self.visibility_al,255)
        raw(self.lookup_pointer);raw(self.autoz_state)
        if type(self.target_ids) is not tuple:raise ValueError('Ordered ID reads required')
        for value in self.target_ids:raw(value)
        if self.refresh_returned is not None and type(self.refresh_returned) is not bool:raise ValueError('Explicit refresh return required')

@dataclass(frozen=True)
class TargetBranchPlan:
    status: str
    calls: tuple = ()
    writes: tuple = ()
    missing: str = ''
    independently_verified: bool = False

class _Missing(Exception):pass

@dataclass(frozen=True)
class LeaderTargetObservation:
    enabled_38: Optional[int] = None
    blocked_74: Optional[int] = None
    party_count_dword: Optional[int] = None
    leader_word: Optional[int] = None
    leader_pointer: Optional[int] = None
    leader_target_id: Optional[int] = None
    target_pointer: Optional[int] = None
    comparison_ah: Optional[int] = None
    maximum_hp_dword: Optional[int] = None
    current_hp_dword: Optional[int] = None
    def __post_init__(self):
        for name in self.__dataclass_fields__:
            raw(getattr(self,name),255 if name in ('enabled_38','blocked_74','comparison_ah') else 65535 if name=='leader_word' else 0xffffffff)

def plan_leader_target(obs):
    if not isinstance(obs,LeaderTargetObservation):raise ValueError('Typed leader observations required')
    calls=[]
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def result(status,writes=(),missing=''):return TargetBranchPlan(status,tuple(calls),tuple(writes),missing)
    def clear():return result('local_clear_plan',((0x118,0),(0x108,0),(0x10c,0)))
    try:
        if need(obs.enabled_38,'config+38')==0 or need(obs.blocked_74,'config+74')!=0:return result('outer_skipped')
        calls.append(('004645e4',()))
        count=need(obs.party_count_dword,'004645e4 EAX')
        if (count-0x100000000 if count&0x80000000 else count)<2:return result('local_no_write')
        leader=need(obs.leader_word,'WORD005695ae')
        calls.append(('00464a10',(leader,)))
        pointer=need(obs.leader_pointer,'leader lookup return')
        if pointer==0:return clear()
        calls.append(('read_offset:00554044',(pointer,)))
        identifier=need(obs.leader_target_id,'leader target DWORD')
        # CMP identifier,0 / JC cannot reject any DWORD, including0.
        calls.append(('00464a10',(identifier,)))
        target=need(obs.target_pointer,'target lookup return')
        if target==0:return clear()
        for offset in ('00554008','00554010','00553fbc','00553fb8'):
            calls.append(('read_offset:'+offset,(target,)))
        calls.append(('00460548/FCOM_status',()))
        # Raw AH avoids fabricating x87 extended precision/coordinate semantics.
        ah=need(obs.comparison_ah,'FCOM status AH')
        if ah&5==0:return result('local_write_plan',((0x108,target),(0x10c,identifier),(0x118,1)))
        maximum=need(obs.maximum_hp_dword,'maximum HP DWORD')&0xffff
        if maximum==0:return result('local_no_write')
        current=need(obs.current_hp_dword,'current HP DWORD')&0xffff
        return clear() if current==0 else result('local_no_write')
    except _Missing as error:return result('needs_observation',missing=str(error))

def plan_target_branch(mode,obs):
    if type(mode) is int and mode==4:return plan_leader_target(obs)
    if type(mode) is not int or mode not in (1,5) or not isinstance(obs,TargetBranchObservation):
        raise ValueError('Manual1/AutoZ5 typed observation required')
    calls=[];writes=[];id_index=0
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def read_id():
        nonlocal id_index
        calls.append(('00462630',()))
        value=obs.target_ids[id_index] if id_index<len(obs.target_ids) else None
        id_index+=1
        return need(value,'00462630 read%d'%id_index)
    def clear():
        writes.extend(((0x118,0),(0x108,0),(0x10c,0)))
        return TargetBranchPlan('local_clear_plan',tuple(calls),tuple(writes))
    try:
        if need(obs.enabled_38,'config+38')==0:return TargetBranchPlan('outer_skipped')
        if need(obs.blocked_74,'config+74')!=0:return TargetBranchPlan('outer_skipped')
        if mode==5:
            calls.append(('read_chain:00553e7c/00554034',()))
            if need(obs.autoz_state,'second0045dc44 actor-state return')==0:
                calls.append(('00464b2c',()))
                if obs.refresh_returned is not True:raise _Missing('00464b2c completed return')
        if read_id()==0:return clear()
        identifier=read_id()
        if mode==1:
            calls.append(('00464a10',(identifier,)))
            pointer=need(obs.lookup_pointer,'00464a10 return')
            if pointer==0:return clear()
            calls.append(('00464c2c',(pointer,)))
            if need(obs.visibility_al,'00464c2c AL')==0:return clear()
            writes.append((0x108,pointer))
            writes.append((0x10c,read_id()))
        else:
            writes.append((0x10c,identifier))
            calls.append(('00464a10',(identifier,)))
            writes.append((0x108,need(obs.lookup_pointer,'00464a10 return')))
        writes.append((0x118,1))
        return TargetBranchPlan('local_write_plan',tuple(calls),tuple(writes))
    except _Missing as error:return TargetBranchPlan('needs_observation',tuple(calls),tuple(writes),str(error))
