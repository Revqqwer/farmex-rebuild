"""0046f9b4..0046faa8 caller plan, without pointer/helper/native effects.

The predicate can use explicit AL or a bound source snapshot model.
The pointer-replacement helper remains an observed opaque call.
Random returns are supplied or calculated from explicit clock/CRT observations.
"""
from dataclasses import dataclass,replace
from callback_predicate import CallbackPredicateObservation,replay_callback_predicate
from source_random import SourceRandomObservation,replay_source_random

def _uint(value,bits):
    if value is not None and (type(value) is not int or not 0<=value<(1<<bits)):
        raise ValueError('Unsigned source scalar required')

def _signed(value,bits):
    value&=(1<<bits)-1
    return value-(1<<bits) if value&(1<<(bits-1)) else value

@dataclass(frozen=True)
class CallbackInterludeState:
    interval_dword:object=None       # 005620cc
    last_attempt_qword:object=None   # 005620d4/005620d8
    def __post_init__(self):
        _uint(self.interval_dword,32);_uint(self.last_attempt_qword,64)

@dataclass(frozen=True)
class CallbackInterludeObservation:
    tick:object=None
    session_stamp_qword:object=None  # 005620a4/005620a8
    initial_random_return:object=None
    session_stamp_after_random:object=None
    last_attempt_after_random:object=None
    predicate_al:object=None
    flag_after_predicate:object=None # fresh 00555e23
    target_554218:object=None
    replacement_returned:object=None
    final_random_return:object=None
    predicate_inputs:object=None
    initial_random_inputs:object=None
    final_random_inputs:object=None
    def __post_init__(self):
        for value in (self.tick,self.initial_random_return,self.target_554218,self.final_random_return):_uint(value,32)
        for value in (self.session_stamp_qword,self.session_stamp_after_random,self.last_attempt_after_random):_uint(value,64)
        for value in (self.predicate_al,self.flag_after_predicate):_uint(value,8)
        if self.replacement_returned is not None and type(self.replacement_returned) is not bool:
            raise ValueError('Explicit normal helper return required')
        if self.predicate_inputs is not None and not isinstance(self.predicate_inputs,CallbackPredicateObservation):
            raise ValueError('Typed predicate snapshot required')
        for value in (self.initial_random_inputs,self.final_random_inputs):
            if value is not None and not isinstance(value,SourceRandomObservation):
                raise ValueError('Typed random helper snapshot required')

@dataclass(frozen=True)
class CallbackInterludePlan:
    status:str
    complete:bool
    state:CallbackInterludeState
    prospective_state:CallbackInterludeState
    calls:tuple=()
    writes:tuple=()
    missing:str=''
    segment_fallthrough_planned:bool=False
    native_execution_verified:bool=False
    predicate_plan:object=None
    initial_random_plan:object=None
    final_random_plan:object=None

def replay_callback_interlude(state,observation):
    if not isinstance(state,CallbackInterludeState) or not isinstance(observation,CallbackInterludeObservation):
        raise ValueError('Typed interlude state/observations required')
    o=observation;candidate=state;calls=[];writes=[];predicate_plan=None
    initial_random_plan=None;final_random_plan=None
    class _Missing(Exception):pass
    class _Fault(Exception):pass
    def need(value,name):
        if value is None:raise _Missing(name)
        return value
    def result(status,complete=False,missing=''):
        return CallbackInterludePlan(status,complete,candidate if complete else state,candidate,
            tuple(calls),tuple(writes),missing,complete,predicate_plan=predicate_plan,
            initial_random_plan=initial_random_plan,final_random_plan=final_random_plan)
    def random_value(inputs,raw,label):
        if inputs is None:return need(raw,label),None
        if raw is not None:raise ValueError('Bound random helper cannot also assert its return')
        plan=replay_source_random(60000,300000,inputs)
        calls.extend(plan.calls)
        return plan.result_dword,plan
    def require_random(plan):
        if plan is not None and not plan.complete:
            if plan.status=='needs_random_observation':raise _Missing(plan.missing)
            raise _Fault(plan.status)
    try:
        calls.append(('005074da',()))
        tick=need(o.tick,'interlude GetTickCount DWORD')
        stamp=need(o.session_stamp_qword,'005620a4 QWORD')
        if (tick-stamp)&0xffffffffffffffff==0:return result('session_delta_zero',True)
        interval=need(state.interval_dword,'005620cc DWORD')
        last=state.last_attempt_qword
        if interval==0:
            calls.append(('00467cc4',(60000,300000)))
            # The opaque helper may modify other globals. Only its explicit
            # result store and subsequent fresh reads are modeled as known.
            candidate=CallbackInterludeState(None,None)
            interval,initial_random_plan=random_value(o.initial_random_inputs,o.initial_random_return,
                                                      'initial random helper DWORD return')
            require_random(initial_random_plan)
            candidate=replace(candidate,interval_dword=interval)
            writes.append((0x5620cc,interval,32))
            stamp=need(o.session_stamp_after_random,'fresh005620a4 after initial random helper')
            last=o.last_attempt_after_random
        if _signed(tick-stamp,64)<=_signed(interval,32):return result('session_interval_wait',True)
        last=need(last,'005620d4 QWORD after initial random helper' if state.interval_dword==0 else '005620d4 QWORD')
        candidate=replace(candidate,last_attempt_qword=last)
        if _signed(tick-last,64)<_signed(interval,32):return result('attempt_interval_wait',True)
        calls.append(('0046ebd0',()))
        candidate=CallbackInterludeState(None,None)
        if o.predicate_inputs is not None:
            if o.predicate_al is not None:raise ValueError('Bound predicate cannot also assert an AL return')
            predicate_plan=replay_callback_predicate(o.predicate_inputs)
            calls.extend(predicate_plan.calls);writes.extend(predicate_plan.writes)
            if not predicate_plan.complete:
                if predicate_plan.status=='predicate_random_fault':raise _Fault(predicate_plan.missing)
                raise _Missing(predicate_plan.missing)
            predicate=predicate_plan.al
        else:predicate=need(o.predicate_al,'0046ebd0 AL return')
        flag=need(o.flag_after_predicate,'fresh00555e23 BYTE') if predicate else None
        if not predicate or not flag:
            target=need(o.target_554218,'00554218 DWORD')
            calls.append(('0046b8fc',(0x554228,target,0x46eca8)))
            if o.replacement_returned is not True:raise _Missing('0046b8fc normal return')
        candidate=replace(candidate,last_attempt_qword=tick)
        writes.extend(((0x5620d4,tick,32),(0x5620d8,0,32)))
        calls.append(('00467cc4',(60000,300000)))
        interval,final_random_plan=random_value(o.final_random_inputs,o.final_random_return,
                                                'final random helper DWORD return')
        require_random(final_random_plan)
        # 00467cc4's recovered body uses clock/CRT rand and stack locals;
        # it has no source store to these two caller timer globals.
        candidate=CallbackInterludeState(interval,tick)
        writes.append((0x5620cc,interval,32))
        return result('interlude_return_planned',True)
    except _Missing as error:return result('needs_interlude_observation',missing=str(error))
    except _Fault as error:return result('random_helper_fault',missing=str(error))
