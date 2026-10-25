"""Bind00458f98 local plan into the bounded callback->unlock prefix.

Other prefix helpers remain explicit return observations. Post-helper lock is
fresh independent data, never inferred from the pre-call persisted lock or a
stop/Town/message plan. No callback/helper/clock/game operation is executed.
"""
from dataclasses import dataclass,replace
from attack_lock import AttackLockState,AttackLockPlan,plan_callback_attack_unlock
from control_frame import ControlFrameState,ControlFrameConfiguration,ControlFrameObservation,replay_control_frame

@dataclass(frozen=True)
class ControlCallbackState:
    lock:AttackLockState
    control:object=None

@dataclass(frozen=True)
class ControlCallbackInputs:
    configuration:object=None
    frame_observation:object=None
    timer_lock:object=None
    def __post_init__(self):
        if self.configuration is not None and not isinstance(self.configuration,ControlFrameConfiguration):raise ValueError('Typed control configuration required')
        if self.frame_observation is not None and not isinstance(self.frame_observation,ControlFrameObservation):raise ValueError('Typed control frame observation required')
        if self.timer_lock is not None and not isinstance(self.timer_lock,AttackLockState):raise ValueError('Fresh timer-entry lock required')

@dataclass(frozen=True)
class ControlCallbackDecision:
    status:str
    complete:bool
    state:ControlCallbackState
    prospective_state:ControlCallbackState
    unlock:AttackLockPlan
    control:object=None
    control_return_assumed_from_local_plan:bool=False
    native_execution_verified:bool=False

def replay_control_callback(state,gate,prefix,inputs,timer_tick=None):
    if not isinstance(state,ControlCallbackState) or not isinstance(state.lock,AttackLockState) or not isinstance(inputs,ControlCallbackInputs):raise ValueError('Typed control callback inputs/state required')
    if state.control is not None and not isinstance(state.control,ControlFrameState):raise ValueError('Typed control state required')
    if '00458f98' in prefix.completed:raise ValueError('External00458f98 completion conflicts with bound control model')
    # The probe can establish source reachability without assuming control return.
    probe=plan_callback_attack_unlock(state.lock,gate,prefix,None)
    control=None;candidate=state;assumed=False
    def result(status,complete,unlock):
        return ControlCallbackDecision(status,complete,candidate if complete else state,candidate,unlock,control,assumed)
    reached=not probe.complete and not probe.timer_reached and probe.reason=='completed:00458f98'
    if reached:
        if inputs.configuration is None or inputs.frame_observation is None or state.control is None:
            return result('needs_control_frame',False,replace(probe,reason='typed control config/state/observation'))
        control=replay_control_frame(inputs.configuration,state.control,inputs.frame_observation)
        candidate=ControlCallbackState(state.lock,control.prospective_state)
        if not control.complete:
            return result('needs_control_observation',False,replace(probe,reason='control:'+control.missing))
        if not control.source_return_planned:
            return result('control_return_unproven',False,replace(probe,reason='termination/call plan does not prove control return'))
        assumed=True
    elif not probe.timer_reached:
        # Outer gate/worker exit or an earlier helper gap precedes the control call.
        return result('callback_skipped_control' if probe.complete else 'needs_prefix_observation',probe.complete,probe)
    if inputs.timer_lock is None:
        return result('needs_timer_lock_observation',False,
            AttackLockPlan('needs_observation',state.lock,False,False,probe.calls,reason='fresh lock at0046f991 after prefix/control helpers'))
    bound_prefix=replace(prefix,completed={**prefix.completed,**({'00458f98':True} if assumed else {})})
    unlock=plan_callback_attack_unlock(inputs.timer_lock,gate,bound_prefix,timer_tick)
    candidate=ControlCallbackState(unlock.state,candidate.control)
    return result('control_callback_unlock_planned' if unlock.complete else 'needs_unlock_observation',unlock.complete,unlock)
