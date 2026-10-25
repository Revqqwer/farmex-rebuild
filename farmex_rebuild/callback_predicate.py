"""0046ebd0 predicate from explicit source snapshots, without memory effects."""
from dataclasses import dataclass
from source_random import SourceRandomObservation,replay_source_random

def _unsigned(value,bits):
    if value is not None and (type(value) is not int or not 0<=value<(1<<bits)):
        raise ValueError('Unsigned source scalar required')

def _signed(value,bits):
    value&=(1<<bits)-1
    return value-(1<<bits) if value&(1<<(bits-1)) else value

@dataclass(frozen=True)
class CallbackPredicateObservation:
    mode_byte:object=None             # 00555df8
    enabled_byte:object=None          # 00555e1c
    field_555dd8:object=None
    field_555de4:object=None
    field_555ddc:object=None
    field_555de0:object=None
    minutes_dword:object=None         # 00553d30
    random_return:object=None         # 00467cc4(3,20), only reached when minutes=0
    tick:object=None                  # separate GetTickCount, not caller tick
    stamp_qword:object=None           # 00555e2c/00555e30, sampled after clock
    random_inputs:object=None
    def __post_init__(self):
        _unsigned(self.mode_byte,8);_unsigned(self.enabled_byte,8)
        for value in (self.field_555dd8,self.field_555de4,self.field_555ddc,
                      self.field_555de0,self.minutes_dword,self.random_return,self.tick):
            _unsigned(value,32)
        _unsigned(self.stamp_qword,64)
        if self.random_inputs is not None and not isinstance(self.random_inputs,SourceRandomObservation):
            raise ValueError('Typed random helper snapshot required')

@dataclass(frozen=True)
class CallbackPredicatePlan:
    status:str
    complete:bool
    al:object=None
    minutes_dword_after:object=None
    calls:tuple=()
    writes:tuple=()
    missing:str=''
    native_execution_verified:bool=False
    random_plan:object=None

def replay_callback_predicate(observation):
    if not isinstance(observation,CallbackPredicateObservation):
        raise ValueError('Typed predicate observation required')
    o=observation;calls=[];writes=[];minutes=None;random_plan=None
    class Missing(Exception):pass
    def need(value,name):
        if value is None:raise Missing(name)
        return value
    def result(status,complete=False,al=None,missing=''):
        return CallbackPredicatePlan(status,complete,al,minutes,tuple(calls),tuple(writes),missing,
                                     random_plan=random_plan)
    def returned(al):
        if al:writes.append((0x555e23,1,8))
        return result('predicate_return_planned',True,al)
    try:
        mode=need(o.mode_byte,'00555df8 BYTE')
        if mode:
            if not need(o.enabled_byte,'00555e1c BYTE'):return returned(0)
            for value,name in ((o.field_555dd8,'00555dd8'),(o.field_555de4,'00555de4'),
                               (o.field_555ddc,'00555ddc'),(o.field_555de0,'00555de0')):
                if _signed(need(value,name+' DWORD'),32)>=0:return returned(0)
            minutes=need(o.minutes_dword,'00553d30 DWORD')
            if minutes==0:
                calls.append(('00467cc4',(3,20)))
                if o.random_inputs is not None:
                    if o.random_return is not None:raise ValueError('Bound random helper cannot also assert its return')
                    random_plan=replay_source_random(3,20,o.random_inputs)
                    calls.extend(random_plan.calls)
                    if not random_plan.complete:
                        if random_plan.status=='needs_random_observation':raise Missing(random_plan.missing)
                        return result('predicate_random_fault',missing=random_plan.status)
                    minutes=random_plan.result_dword
                else:minutes=need(o.random_return,'predicate random helper DWORD return')
                writes.append((0x553d30,minutes,32))
            threshold=_signed(minutes*60000,32)
        else:threshold=300000
        calls.append(('005074da',()))
        tick=need(o.tick,'predicate GetTickCount DWORD')
        stamp=need(o.stamp_qword,'fresh00555e2c QWORD after predicate clock')
        return returned(int(_signed(tick-stamp,64)<=threshold))
    except Missing as error:
        return result('needs_predicate_observation',missing=str(error))
