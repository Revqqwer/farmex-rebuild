"""Bounded0046f520 unlock->mode2 mining bridge. No callback/hook execution.

The interposed0046f9b4..0046faa8 segment accepts a scoped caller model or legacy
normal-completion observation. Its helper effects and the fresh post-segment
lock remain independent observations. Queue/helper effects before the timer
are not inferred; existing lock API explicitly bounds that prefix.
"""
from dataclasses import dataclass,replace
from typing import Optional
from attack_lock import AttackLockState,LockCallbackObservation,AttackLockPlan,plan_callback_attack_unlock
from action_queue import CallbackQueueGate
from mining_frame import MiningFrameState,MiningFrameObservation,MiningFrameDecision,replay_mining_frame
from control_frame import ControlFrameState
from control_callback import ControlCallbackState,ControlCallbackInputs,ControlCallbackDecision,replay_control_callback
from callback_interlude import CallbackInterludeState,CallbackInterludeObservation,CallbackInterludePlan,replay_callback_interlude

@dataclass(frozen=True)
class MiningCallbackState:
    lock:AttackLockState
    frame:MiningFrameState
    control:Optional[ControlFrameState]=None
    interlude:Optional[CallbackInterludeState]=None

    def __post_init__(self):
        if not isinstance(self.lock,AttackLockState) or not isinstance(self.frame,MiningFrameState):raise ValueError('Typed callback state required')
        if self.control is not None and not isinstance(self.control,ControlFrameState):raise ValueError('Typed control frame state required')
        if self.interlude is not None and not isinstance(self.interlude,CallbackInterludeState):raise ValueError('Typed interlude state required')

@dataclass(frozen=True)
class MiningCallbackObservation:
    gate:CallbackQueueGate
    prefix:LockCallbackObservation
    timer_tick:Optional[int]=None
    post_timer_completed:Optional[bool]=None
    post_timer_lock:Optional[AttackLockState]=None
    mode_after_segment:Optional[int]=None
    frame:Optional[MiningFrameObservation]=None
    control:Optional[ControlCallbackInputs]=None
    interlude:Optional[CallbackInterludeObservation]=None

    def __post_init__(self):
        if not isinstance(self.gate,CallbackQueueGate) or not isinstance(self.prefix,LockCallbackObservation):raise ValueError('Typed callback observations required')
        for value in (self.timer_tick,self.mode_after_segment):
            if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):raise ValueError('Raw DWORD required')
        if self.post_timer_completed is not None and type(self.post_timer_completed) is not bool:raise ValueError('Explicit segment completion required')
        if self.post_timer_lock is not None and not isinstance(self.post_timer_lock,AttackLockState):raise ValueError('Typed post-segment lock required')
        if self.frame is not None and not isinstance(self.frame,MiningFrameObservation):raise ValueError('Typed frame observations required')
        if self.control is not None and not isinstance(self.control,ControlCallbackInputs):raise ValueError('Typed bound control inputs required')
        if self.interlude is not None and not isinstance(self.interlude,CallbackInterludeObservation):raise ValueError('Typed interlude observation required')

@dataclass(frozen=True)
class MiningCallbackDecision:
    status:str
    complete:bool
    state:MiningCallbackState
    prospective_state:MiningCallbackState
    unlock:AttackLockPlan
    frame:Optional[MiningFrameDecision]=None
    missing:tuple=()
    native_execution_verified:bool=False
    server_acknowledged:bool=False
    control:Optional[ControlCallbackDecision]=None
    interlude:Optional[CallbackInterludePlan]=None

def replay_mining_callback(configuration,state,observation,now_ms):
    if not isinstance(state,MiningCallbackState) or not isinstance(observation,MiningCallbackObservation):raise ValueError('Typed callback state/observations required')
    control=None;control_state=state.control;interlude=None;interlude_state=state.interlude
    if observation.interlude is not None and observation.post_timer_completed is not None:
        raise ValueError('External intermediate completion conflicts with bound interlude model')
    if observation.control is not None:
        control=replay_control_callback(ControlCallbackState(state.lock,state.control),
            observation.gate,observation.prefix,observation.control,observation.timer_tick)
        unlock=control.unlock;control_state=control.prospective_state.control
        candidate=MiningCallbackState(control.prospective_state.lock,state.frame,control_state,interlude_state)
    else:
        unlock=plan_callback_attack_unlock(state.lock,observation.gate,observation.prefix,observation.timer_tick)
        candidate=MiningCallbackState(unlock.state,state.frame,control_state,interlude_state)
    frame=None
    def result(status,complete,missing=()):
        return MiningCallbackDecision(status,complete,candidate if complete else state,candidate,unlock,frame,tuple(missing),control=control,interlude=interlude)
    if not unlock.complete:return result('needs_callback_observation',False,(unlock.reason,))
    if not unlock.timer_reached:return result('callback_skipped_mining',True)
    if observation.interlude is not None:
        if interlude_state is None:return result('needs_interlude_state',False,('typed interlude state',))
        interlude=replay_callback_interlude(interlude_state,observation.interlude)
        interlude_state=interlude.prospective_state
        candidate=replace(candidate,interlude=interlude_state)
        if not interlude.complete:return result('needs_interlude_observation',False,(interlude.missing,))
    elif observation.post_timer_completed is not True:
        return result('needs_post_timer_segment',False,('0046f9b4..0046faa8 normal completion',))
    if observation.post_timer_lock is None:
        return result('needs_post_timer_lock',False,('fresh lock after intermediate segment',))
    candidate=MiningCallbackState(observation.post_timer_lock,state.frame,control_state,interlude_state)
    if observation.mode_after_segment is None:return result('needs_callback_mode',False,('00561f58 DWORD',))
    if observation.mode_after_segment!=2:return result('other_callback_mode_unmodeled',False,('mode2 mining branch required',))
    if observation.frame is None:return result('needs_mining_frame',False,('frame',))
    nested=observation.frame;lock=observation.post_timer_lock
    if nested.speed is not None:
        speed=dict(nested.speed);speed['lock_561f7e']=lock.byte
        nested=replace(nested,speed=speed)
    # Only carry a timer result straight to route when no intervening effect
    # helper is selected. Other paths supply fresh route-entry observations.
    if (nested.pipeline is not None and configuration.fields.get(0x6047)==0
            and nested.scheduler.get('merchant_after_speed')==0
            and nested.scheduler.get('mining_after_merchant')==0):
        nested=replace(nested,pipeline=replace(nested.pipeline,
            outer=replace(nested.pipeline.outer,blocked_561f7e=bool(lock.byte))))
    frame=replay_mining_frame(configuration,state.frame,nested,now_ms)
    # Swift may replace the lock after the timer, in this very invocation.
    if frame.speed is not None:
        fields={'byte':lock.byte,'duration_ms':lock.duration_ms,'started_ms':lock.started_ms}
        names={0x561f7e:'byte',0x561f80:'duration_ms',0x561f84:'started_ms'}
        for address,value,width in frame.speed.writes:
            if address in names:fields[names[address]]=value
        lock=AttackLockState(**fields)
    if frame.maintenance_return_assumed_from_local_plan and observation.frame.post_maintenance_lock_byte is not None:
        # This observed BYTE is later than speed's writes in source order.
        lock=replace(lock,byte=observation.frame.post_maintenance_lock_byte)
    candidate=MiningCallbackState(lock,frame.prospective_state,control_state,interlude_state)
    return result('callback_mining_planned' if frame.complete else 'needs_nested_mining_observation',frame.complete,frame.missing)
