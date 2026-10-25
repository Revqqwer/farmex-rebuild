"""Reached 4eb7f4/4eb987 paths only; earlier selection remains external."""
from dataclasses import dataclass,field
from route_resume import RouteResumeState,RouteResumeObservation,plan_route_condition,plan_route_resume

WRITES=(('object',0x5d9,1,0),('global',0x561f6c,1,1))

@dataclass(frozen=True)
class RouteResumePathObservation:
    condition:RouteResumeObservation=field(default_factory=RouteResumeObservation)
    tail:RouteResumeObservation=field(default_factory=RouteResumeObservation)
    tick_dword:object=None
    stamp_qword:object=None
    limit_dword:object=None
    compare_span_returned:object=None
    comparison_al:object=None
    notification_returned:object=None
    optional_flag_byte:object=None
    optional_helper_returned:object=None
    def __post_init__(self):
        if not isinstance(self.condition,RouteResumeObservation) or not isinstance(self.tail,RouteResumeObservation):
            raise ValueError('Independent typed first and tail observations required')
        for name,bits in (('tick_dword',32),('stamp_qword',64),('limit_dword',32),('comparison_al',8),('optional_flag_byte',8)):
            v=getattr(self,name)
            if v is not None and (type(v) is not int or not 0<=v<1<<bits):raise ValueError('Raw path integer required: '+name)
        for name in ('compare_span_returned','notification_returned','optional_helper_returned'):
            v=getattr(self,name)
            if v is not None and type(v) is not bool:raise ValueError('Explicit normal return required: '+name)

@dataclass(frozen=True)
class RouteResumePathDecision:
    complete:bool
    status:str
    state:RouteResumeState
    prospective_state:RouteResumeState
    steps:tuple=()
    writes:tuple=()
    first_condition:object=None
    tail:object=None
    elapsed_signed:object=None
    limit_signed:object=None
    missing:str=''
    live_compatibility_verified:bool=False

def _signed(v,bits):
    return v-(1<<bits) if v&(1<<(bits-1)) else v

def plan_route_resume_path(kind,state,o):
    """Pure whole-span trial; incomplete prospective writes are never committed."""
    if kind not in ('timed','optional'):raise ValueError('Reached path must be timed or optional')
    if not isinstance(state,RouteResumeState) or not isinstance(o,RouteResumePathObservation):raise ValueError('Typed path inputs required')
    steps=[];writes=[];candidate=state;first=None;tail=None;elapsed=None;limit=None
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def returned(value,label):
        steps.append(('opaque_normal_return',label))
        if value is not True:raise Missing(label)
    def result(complete,status,missing=''):
        return RouteResumePathDecision(complete,status,candidate if complete else state,candidate,
            tuple(steps),tuple(writes),first,tail,elapsed,limit,missing)
    try:
        steps.append(('condition','004eb7f4' if kind=='timed' else '004eb987'))
        first=plan_route_condition(o.condition)
        if not first.complete:raise Missing('first condition: '+first.missing)
        if first.byte_plan.eax_dword&255==0:
            if kind=='timed':
                steps.append(('GetTickCount',))
                tick=need(o.tick_dword,'GetTickCount DWORD')
                steps.append(('read',0x56ff9c,'QWORD'))
                stamp=need(o.stamp_qword,'stamp QWORD56ff9c')
                elapsed=_signed((tick-stamp)&((1<<64)-1),64)
                steps.append(('read',0x56ffa4,'signed DWORD'))
                limit=_signed(need(o.limit_dword,'limit DWORD56ffa4'),32)
                if limit>elapsed:return result(True,'timed_wait_no_tail')
                # String construction, comparison, and cleanup remain opaque.
                returned(o.compare_span_returned,'004eb843..004eb885 comparison/string span')
                al=need(o.comparison_al,'saved comparison AL')
                if al:returned(o.notification_returned,'00459fb0(00562194) normal return')
            else:
                steps.append(('read',0x56fade,'BYTE'))
                if need(o.optional_flag_byte,'optional flag BYTE56fade'):
                    returned(o.optional_helper_returned,'0047789c(00569a98) normal return')
            writes.extend(WRITES);candidate=RouteResumeState(0,1)
            steps.append(('pre_tail_writes',))
        steps.append(('fresh_common_tail','004eb9c9'))
        tail=plan_route_resume(candidate,o.tail)
        if not tail.complete:raise Missing('common tail: '+tail.missing)
        writes.extend(tail.writes);candidate=tail.state
        return result(True,'returned_via_common_tail')
    except Missing as e:return result(False,'needs_observation',str(e))
