"""Reached common tail4eb9c9..4eb9f7 only; no route-completion detection."""
from dataclasses import dataclass
from source_coin import GuardedDwordSample,GuardedByteSample,plan_guarded_dword,plan_guarded_byte

@dataclass(frozen=True)
class RouteResumeState:
    active_byte:int
    enable_byte:int
    def __post_init__(self):
        for v in (self.active_byte,self.enable_byte):
            if type(v) is not int or not 0<=v<256:raise ValueError('Raw route-tail state BYTE required')

@dataclass(frozen=True)
class RouteResumeObservation:
    global_samples:tuple=()
    root_sample:object=None
    byte_sample:object=None
    def __post_init__(self):
        if type(self.global_samples) is not tuple:raise ValueError('Ordered route-tail global samples required')
        for row in self.global_samples:
            if type(row) is not tuple or len(row)!=2:raise ValueError('Tail global address/value pair required')
            for v in row:
                if v is not None and (type(v) is not int or not 0<=v<1<<32):raise ValueError('Raw route-tail DWORD required')
            if row[0] is None:raise ValueError('Known global address required')
        if self.root_sample is not None and not isinstance(self.root_sample,GuardedDwordSample):raise ValueError('Typed root sample required')
        if self.byte_sample is not None and not isinstance(self.byte_sample,GuardedByteSample):raise ValueError('Typed byte sample required')

@dataclass(frozen=True)
class RouteResumeDecision:
    complete:bool
    status:str
    state:RouteResumeState
    root_plan:object=None
    byte_plan:object=None
    global_reads:tuple=()
    writes:tuple=()
    missing:str=''
    independently_verified:bool=False

@dataclass(frozen=True)
class RouteConditionDecision:
    complete:bool
    root_plan:object=None
    byte_plan:object=None
    global_reads:tuple=()
    missing:str=''

def plan_route_condition(o):
    """One fresh root/offset/BYTE read; no route-state writes."""
    if not isinstance(o,RouteResumeObservation):raise ValueError('Typed route condition inputs required')
    reads=[];root=None;byte=None;index=0
    class Missing(Exception):pass
    def g(address):
        nonlocal index
        if index>=len(o.global_samples):raise Missing('tail global sample%d at%08x'%(index,address))
        at,value=o.global_samples[index];index+=1
        if at!=address:raise ValueError('Tail global address mismatch')
        reads.append((at,value))
        if value is None:raise Missing('tail global value at%08x'%at)
        return value
    try:
        root=plan_guarded_dword(g(0x553e7c),o.root_sample)
        if not root.complete:raise Missing(root.missing)
        address=(root.value_dword+g(0x554020))&0xffffffff
        byte=plan_guarded_byte(address,o.byte_sample)
        if not byte.complete:raise Missing(byte.missing)
        return RouteConditionDecision(True,root,byte,tuple(reads))
    except Missing as e:return RouteConditionDecision(False,root,byte,tuple(reads),str(e))

def plan_route_resume(state,o):
    if not isinstance(state,RouteResumeState):raise ValueError('Typed reached route-tail state required')
    p=plan_route_condition(o)
    if not p.complete:return RouteResumeDecision(False,'needs_observation',state,p.root_plan,p.byte_plan,p.global_reads,missing=p.missing)
    if p.byte_plan.eax_dword&255:return RouteResumeDecision(True,'no_tail_writes',state,p.root_plan,p.byte_plan,p.global_reads)
    return RouteResumeDecision(True,'enable_written',RouteResumeState(0,1),p.root_plan,p.byte_plan,p.global_reads,
        (('object',0x5d9,1,0),('global',0x561f6c,1,1)))
