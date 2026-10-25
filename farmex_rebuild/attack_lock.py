"""0046f991 timer segment and bounded callback reachability, pure plans only.

This is not the whole callback. Its other writes and side effects are omitted.
The lock state passed here is an explicit observation at the timer segment after
the preceding helpers. Completion flags do not claim those helpers are pure.
"""
from dataclasses import dataclass,field,replace
from typing import Mapping,Optional,Tuple
from action_queue import CallbackQueueGate,QueueState,drain_on_callback

@dataclass(frozen=True)
class AttackLockState:
    byte: int = 0             # 00561f7e
    duration_ms: int = 0      # 00561f80
    started_ms: int = 0       # 00561f84

    def __post_init__(self):
        if type(self.byte) is not int or not 0<=self.byte<=255:raise ValueError('Lock BYTE required')
        for v in (self.duration_ms,self.started_ms):
            if type(v) is not int or not 0<=v<=0xffffffff:raise ValueError('Lock DWORD required')

@dataclass(frozen=True)
class LockCallbackObservation:
    byte_5690b8: Optional[int] = None
    byte_5690e0: Optional[int] = None
    byte_568dbc: Optional[int] = None
    byte_561f60: Optional[int] = None
    completed: Mapping[str,Optional[bool]] = field(default_factory=dict)

    def __post_init__(self):
        for v in (self.byte_5690b8,self.byte_5690e0,self.byte_568dbc,self.byte_561f60):
            if v is not None and (type(v) is not int or not 0<=v<=255):raise ValueError('BYTE or unknown required')
        if not isinstance(self.completed,Mapping):raise ValueError('Completion mapping required')
        if any(v is not None and type(v) is not bool for v in self.completed.values()):raise ValueError('Completion bool or unknown required')

@dataclass(frozen=True)
class AttackLockPlan:
    status: str
    state: AttackLockState
    complete: bool
    timer_reached: bool
    calls: Tuple[str,...] = ()
    writes: Tuple[Tuple[str,int],...] = ()
    reason: str = ''
    independently_verified: bool = False

def plan_attack_unlock(state,clock=None):
    if not isinstance(state,AttackLockState):raise ValueError('Typed lock state required')
    if clock is not None and (type(clock) is not int or not 0<=clock<=0xffffffff):raise ValueError('DWORD clock required')
    if not state.byte:return AttackLockPlan('already_unlocked',state,True,True)
    if clock is None:return AttackLockPlan('needs_observation',state,False,True,reason='unlock GetTickCount')
    if (clock-state.started_ms)&0xffffffff < state.duration_ms:
        return AttackLockPlan('wait_lock_duration',state,True,True,('005074da',))
    return AttackLockPlan('lock_cleared',replace(state,byte=0),True,True,('005074da',),(('00561f7e',0),))

def plan_callback_attack_unlock(state,gate,observation,clock=None):
    if not isinstance(state,AttackLockState) or not isinstance(gate,CallbackQueueGate) or not isinstance(observation,LockCallbackObservation):
        raise ValueError('Typed lock, callback gate and observations required')
    # Empty queue asks the existing bounded outer-gate model about reachability
    # only; actual queue execution must be independently observed below.
    reachable=drain_on_callback(QueueState(),gate,{})
    if reachable.status=='needs_observation':return AttackLockPlan('needs_observation',state,False,False,reason=reachable.missing)
    if reachable.status=='callback_skipped_queue':return AttackLockPlan('callback_skipped_lock',state,True,False,reason=reachable.missing)
    calls=[]
    class _Missing(Exception):pass
    def need(v,key):
        if v is None:raise _Missing(key)
        return v
    def completed(address):
        calls.append(address)
        if need(observation.completed.get(address),'completed:'+address) is not True:raise _Missing('completed:'+address)
    try:
        completed('00458c70');completed('004c79a0')
        if need(observation.byte_5690b8,'byte:005690b8'):
            completed('004ff918')
        elif need(observation.byte_5690e0,'byte:005690e0'):
            completed('00470a94')
        elif need(observation.byte_568dbc,'byte:00568dbc'):
            # Every path through this worker branch exits before0046f991.
            return AttackLockPlan('worker_skipped_lock',state,True,False,tuple(calls),reason='00568dbc branch')
        completed('0045a4dc')
        if need(observation.byte_561f60,'byte:00561f60'):completed('00458f98')
        result=plan_attack_unlock(state,clock)
        return replace(result,calls=tuple(calls)+result.calls)
    except _Missing as exc:
        return AttackLockPlan('needs_observation',state,False,False,tuple(calls),reason=str(exc))

def apply_lock_write_plans(state,writes):
    """Reduce known local lock-field plans, never memory writes or helper effects."""
    if not isinstance(state,AttackLockState):raise ValueError('Typed lock required')
    names={'00561f7e':'byte','00561f80':'duration_ms','00561f84':'started_ms'}
    for address,value in writes:
        if address in names:state=replace(state,**{names[address]:value})
    return state
