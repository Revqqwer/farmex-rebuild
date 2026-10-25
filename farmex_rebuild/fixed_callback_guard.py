"""0046f33c fixed-skill tail and bounded queue reachability; no game IO."""
from dataclasses import dataclass,replace
from action_queue import QueueState,CallbackQueueGate,drain_on_callback
from transformation import DirectSkillFrame,TransformationUseSamples,raw,normal_type

FIXED_SKILL=0x7a3dc

@dataclass(frozen=True)
class FixedGuardState:
    last_tick_dword:object=None
    def __post_init__(self):raw(self.last_tick_dword,True)

@dataclass(frozen=True)
class FixedGuardObservation:
    mode_byte_561f7c:object=None
    enabled_byte_561ede:object=None
    initial_tick_dword:object=None
    check_returned:object=None
    check_eax_dword:object=None
    cast_inputs:object=None
    post_cast_tick_dword:object=None
    def __post_init__(self):
        for v in (self.mode_byte_561f7c,self.enabled_byte_561ede):
            raw(v,True)
            if v is not None and v>255:raise ValueError('Raw guard BYTE required')
        for v in (self.initial_tick_dword,self.check_eax_dword,self.post_cast_tick_dword):raw(v,True)
        normal_type(self.check_returned)
        if self.cast_inputs is not None and not isinstance(self.cast_inputs,TransformationUseSamples):raise ValueError('Typed direct cast inputs required')

@dataclass(frozen=True)
class FixedGuardPlan:
    complete:bool
    status:str
    state:FixedGuardState
    queue:QueueState
    al:object=None
    eax_dword:object=None
    elapsed_dword:object=None
    cast_plan:object=None
    missing:str=''
    native_execution_verified:bool=False

class FixedGuardFrame:
    def __init__(self,state,queue=None):
        if not isinstance(state,FixedGuardState):raise ValueError('Typed stored guard tick required')
        self.state=state;self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own guard queue required')
        self.mode=None;self.enabled=None;self.tick=None;self.elapsed=None;self.checked=False;self.check_eax=None
        self.cast=None;self.cast_plan=None;self.final=None
    def advance(self,o):
        if not isinstance(o,FixedGuardObservation):raise ValueError('Typed fixed guard observations required')
        def result(ok,status,al=None,eax=None,missing=''):
            return FixedGuardPlan(ok,status,self.state,self.queue,al,eax,self.elapsed,self.cast_plan,missing)
        def gap(label):return result(False,'needs_observation',missing=label)
        def zero(status):
            self.final=result(True,status,0,0);return self.final
        if self.final is not None:return self.final
        if self.mode is None:
            if o.mode_byte_561f7c is None:return gap('00561f7c BYTE')
            self.mode=o.mode_byte_561f7c
        if self.mode!=0:return gap('manual CAPTCHA branch; no automatic challenge handling or inferred AL')
        if self.enabled is None:
            if o.enabled_byte_561ede is None:return gap('00561ede BYTE')
            self.enabled=o.enabled_byte_561ede
        if self.enabled==0:return zero('disabled')
        if self.tick is None:
            if o.initial_tick_dword is None:return gap('initial GetTickCount DWORD')
            self.tick=o.initial_tick_dword
        if self.state.last_tick_dword is None:return gap('stored00553d3c DWORD')
        if self.elapsed is None:self.elapsed=(self.tick-self.state.last_tick_dword)&0xffffffff
        if self.elapsed<5000:return zero('waiting_5000')
        if not self.checked:
            if o.check_returned is not True:return gap('00464268 fixed-skill normal return')
            self.checked=True
        if self.check_eax is None:
            if o.check_eax_dword is None:return gap('fixed-skill check EAX')
            self.check_eax=o.check_eax_dword
        if self.check_eax&255==0:return zero('fixed_skill_unavailable')
        if self.cast is None:self.cast=DirectSkillFrame(FIXED_SKILL,self.queue)
        if self.cast_plan is None or not self.cast_plan.complete:
            if o.cast_inputs is None:return gap('direct004c8388 inputs')
            self.cast_plan=self.cast.advance(o.cast_inputs);self.queue=self.cast.queue
            if not self.cast_plan.complete:return gap('direct cast:'+self.cast_plan.missing)
        if o.post_cast_tick_dword is None:return gap('post-cast GetTickCount DWORD')
        self.state=FixedGuardState(o.post_cast_tick_dword)
        eax=(o.post_cast_tick_dword&0xffffff00)|1
        self.final=result(True,'fixed_cast_returned',1,eax);return self.final

@dataclass(frozen=True)
class FixedGuardQueuePlan:
    complete:bool
    queue:QueueState
    guard_state:FixedGuardState
    guard_plan:object=None
    queue_decision:object=None
    missing:str=''
    native_execution_verified:bool=False

class FixedGuardQueueFrame:
    """Existing callback queue gates plus bound helper, not the full callback."""
    def __init__(self,queue,gate,guard_state):
        if not isinstance(gate,CallbackQueueGate):raise ValueError('Typed callback queue gate required')
        self.gate=gate;self.guard=FixedGuardFrame(guard_state,queue);self.final=None;self.post_work_queue=None
    def advance(self,observation,queue_samples=None,*,work_queue_returned=None,post_work_queue=None):
        if self.final is not None:return self.final
        if queue_samples is None:queue_samples={}
        # Empty own queue probes reachability without planning any record send.
        active_gate=replace(self.gate,helper_46f33c=None)
        decision=drain_on_callback(QueueState(),active_gate,{})
        guard_plan=None
        if decision.state is None and decision.missing=='0046f33c AL':
            if self.gate.helper_46f33c is not None:raise ValueError('Raw guard AL conflicts with bound guard')
            guard_plan=self.guard.advance(observation)
            if not guard_plan.complete:
                return FixedGuardQueuePlan(False,self.guard.queue,self.guard.state,guard_plan,missing=guard_plan.missing)
            active_gate=replace(self.gate,helper_46f33c=guard_plan.al)
            decision=drain_on_callback(QueueState(),active_gate,{})
        if decision.state is None:
            return FixedGuardQueuePlan(False,self.guard.queue,self.guard.state,guard_plan,decision,decision.missing)
        if decision.status=='callback_skipped_queue':
            decision=drain_on_callback(self.guard.queue,active_gate,{})
        else:
            if self.post_work_queue is None:
                if work_queue_returned is not None and type(work_queue_returned) is not bool:raise ValueError('Separate work queue normal return required')
                if work_queue_returned is not True:
                    return FixedGuardQueuePlan(False,self.guard.queue,self.guard.state,guard_plan,missing='00458c70 work queue normal return')
                if post_work_queue is None:
                    return FixedGuardQueuePlan(False,self.guard.queue,self.guard.state,guard_plan,missing='fresh queue after00458c70')
                if not isinstance(post_work_queue,QueueState):raise ValueError('Typed post-work-helper queue required')
                self.post_work_queue=post_work_queue
            decision=drain_on_callback(self.post_work_queue,active_gate,queue_samples)
            if decision.state is None:
                return FixedGuardQueuePlan(False,self.post_work_queue,self.guard.state,guard_plan,decision,decision.missing)
        self.final=FixedGuardQueuePlan(True,decision.state,self.guard.state,guard_plan,decision)
        return self.final
