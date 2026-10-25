"""Reached 004eb6a6 route-mode/motion/exit composition, no game IO."""
from dataclasses import dataclass,field
from route_resume import RouteResumeState,RouteResumeObservation,plan_route_resume
from route_resume_paths import RouteResumePathObservation,plan_route_resume_path
from source_coin import GuardedDwordSample,plan_guarded_dword

def _raw(value,bits=32):
    if value is not None and (type(value) is not int or not 0<=value<1<<bits):
        raise ValueError('Raw route motion integer required')

def _signed(value,bits=32):
    return value-(1<<bits) if value&(1<<(bits-1)) else value

@dataclass(frozen=True)
class RouteMotionObservation:
    global_samples:tuple=()
    route_flag574_byte:object=None
    route_index548_dword:object=None
    label_span_returned:object=None
    metric_ftol_dword:object=None
    tick_dword:object=None
    stamp_qword:object=None
    guarded_root:object=None
    guarded_value:object=None
    move_helper_returned:object=None
    resume:RouteResumePathObservation=field(default_factory=RouteResumePathObservation)
    def __post_init__(self):
        if type(self.global_samples) is not tuple:raise ValueError('Ordered global samples required')
        for row in self.global_samples:
            if type(row) is not tuple or len(row)!=2:raise ValueError('Global address/value pair required')
            if row[0] is None:raise ValueError('Known global address required')
            _raw(row[0]);_raw(row[1])
        _raw(self.route_flag574_byte,8)
        for value in (self.route_index548_dword,self.metric_ftol_dword,self.tick_dword):_raw(value)
        _raw(self.stamp_qword,64)
        for value in (self.label_span_returned,self.move_helper_returned):
            if value is not None and type(value) is not bool:raise ValueError('Explicit normal return required')
        for value in (self.guarded_root,self.guarded_value):
            if value is not None and not isinstance(value,GuardedDwordSample):raise ValueError('Typed guarded sample required')
        if not isinstance(self.resume,RouteResumePathObservation):raise ValueError('Typed independent exit observations required')

@dataclass(frozen=True)
class RouteMotionDecision:
    complete:bool
    status:str
    state:RouteResumeState
    prospective_state:RouteResumeState
    steps:tuple=()
    global_reads:tuple=()
    guarded_plans:tuple=()
    writes:tuple=()
    exit_plan:object=None
    elapsed_signed:object=None
    metric_signed:object=None
    missing:str=''
    live_compatibility_verified:bool=False

def plan_route_motion(state,o):
    """Input contract reaches 4eb6a6; preceding route work remains external."""
    if not isinstance(state,RouteResumeState) or not isinstance(o,RouteMotionObservation):raise ValueError('Typed route motion inputs required')
    steps=[];reads=[];guards=[];pos=0;exit_plan=None;elapsed=None;metric=None
    candidate=state;writes=()
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def g(address,bits=32):
        nonlocal pos
        steps.append(('global_read',address,bits))
        if pos>=len(o.global_samples):raise Missing('global sample%d at%08x'%(pos,address))
        at,value=o.global_samples[pos];pos+=1
        if at!=address:raise ValueError('Route motion global sample address mismatch')
        _raw(value,bits);reads.append((at,value));return need(value,'global value at%08x'%at)
    def normal(value,label):
        steps.append(('normal_return',label))
        if value is not True:raise Missing(label)
    def result(complete,status,missing=''):
        return RouteMotionDecision(complete,status,candidate if complete else state,candidate,
            tuple(steps),tuple(reads),tuple(guards),writes,exit_plan,elapsed,metric,missing)
    def coordinates(y_address,x_address,helper):
        # Source signed DWORD -> FSTP float conversions/native effects are not
        # approximated; these retain the raw input order of the opaque helper.
        y=g(y_address);x=g(x_address)
        steps.append((helper,'physical_push_y_x_signed_dwords',_signed(y),_signed(x)))
    def metric_result(y_address,x_address):
        coordinates(y_address,x_address,'00460548 -> __ftol EAX observation')
        return _signed(need(o.metric_ftol_dword,'metric helper/__ftol low DWORD'))
    def guarded(address,sample):
        p=plan_guarded_dword(address&0xffffffff,sample);guards.append(p)
        steps.append(('0045dc44',address&0xffffffff))
        if not p.complete:raise Missing(p.missing)
        return p.value_dword
    def movement_guard():
        if g(0x561f7e,8):return 'movement_locked'
        root=guarded(g(0x553e7c),o.guarded_root)
        value=guarded((root+g(0x554034))&0xffffffff,o.guarded_value)
        if value==6:return 'movement_field_exact6'
        return None
    def exit_at(kind):
        nonlocal candidate,writes,exit_plan
        steps.append(('exit_path',kind))
        if kind=='common':
            exit_plan=plan_route_resume(state,o.resume.tail)
            candidate=exit_plan.state
        else:
            exit_plan=plan_route_resume_path(kind,state,o.resume)
            candidate=exit_plan.prospective_state
        writes=exit_plan.writes
        if not exit_plan.complete:raise Missing('exit path: '+exit_plan.missing)
        return result(True,'exit_'+kind)
    try:
        if g(0x561f58)==0:
            steps.append(('object_read',0x574,'BYTE'))
            if need(o.route_flag574_byte,'object BYTE574'):
                steps.append(('object_read',0x548,'signed DWORD'))
                if _signed(need(o.route_index548_dword,'index guard DWORD548'))>=0:
                    # Two additional fresh indices, string conversion and UI
                    # update are inside this explicit unresolved span.
                    normal(o.label_span_returned,'004eb6cb..004eb711 index/string/UI span')
            metric=metric_result(0x562004,0x562000)
            # FILD of the signed integer is exact. Disk FLD constant is1.5.
            if metric>70 or metric<2:return exit_at('timed')
            steps.append(('GetTickCount',))
            tick=need(o.tick_dword,'motion GetTickCount DWORD')
            stamp=need(o.stamp_qword,'motion stamp QWORD56ff9c')
            elapsed=_signed((tick-stamp)&((1<<64)-1),64)
            if elapsed<1500:return result(True,'movement_wait_no_tail')
            blocked=movement_guard()
            if blocked:return result(True,blocked)
            coordinates(0x562004,0x562000,'004646b4')
            normal(o.move_helper_returned,'004646b4 normal return')
            # Source mode0 returns directly after move; it must not enable via
            # a convenience common-tail call.
            return result(True,'movement_return_no_tail')
        # Native code rereads this global rather than reusing the first mode.
        if g(0x561f58)!=2:return exit_at('common')
        if g(0x56fa88)==0:return exit_at('optional')
        if g(0x56fa8c)==0:return exit_at('optional')
        metric=metric_result(0x56fa8c,0x56fa88)
        if metric<2:return exit_at('optional')
        blocked=movement_guard()
        if blocked:return result(True,blocked)
        coordinates(0x56fa8c,0x56fa88,'004646b4')
        normal(o.move_helper_returned,'004646b4 normal return')
        return exit_at('optional')
    except Missing as e:return result(False,'needs_observation',str(e))
