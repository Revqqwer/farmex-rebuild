"""4631c8/4631e8 ordered DWORD-root/BYTE-field plans; no protection changes."""
from dataclasses import dataclass,replace
from types import MappingProxyType
from motion_genie_helpers import MotionGenieObservation,_Planner,_Missing
from native_profile_versions import LEGACY_SOURCE_SHA256,CURRENT_SOURCE_SHA256

GETTER_OFFSET_SLOTS=MappingProxyType({'004631c8':0x554070,'004631e8':0x554074})
SOURCE_GETTER_ROOTS=MappingProxyType({LEGACY_SOURCE_SHA256:MappingProxyType({'us':0x1115574,'steam':0x11ea638}),
                                  CURRENT_SOURCE_SHA256:MappingProxyType({'us':0x11289c0,'steam':0x11e9638})})
def source_getter_globals(module_sha256,profile,helper):
    if helper not in GETTER_OFFSET_SLOTS or module_sha256 not in SOURCE_GETTER_ROOTS or profile not in ('us','steam'):
        raise ValueError('Explicit known source hash/profile/getter required')
    return ((0x553e7c,SOURCE_GETTER_ROOTS[module_sha256][profile]),(GETTER_OFFSET_SLOTS[helper],0x760 if helper=='004631c8' else 0x75c))

@dataclass(frozen=True)
class GenieGetterPlan:
    helper:str
    complete:bool
    raw_eax:object=None
    low_al:object=None
    steps:tuple=()
    missing:str=''
    request:object=None
    module_sha256:object=None
    profile:object=None
    input_snapshot:object=None
    native_execution_verified:bool=False
    protection_side_effects_emulated:bool=False

def plan_genie_getter(helper,o,*,module_sha256=None,profile=None):
    if helper not in GETTER_OFFSET_SLOTS:raise ValueError('Known Genie BYTE getter required')
    expected=None
    if module_sha256 is not None or profile is not None:expected=source_getter_globals(module_sha256,profile,helper)
    p=_Planner(o);raw=None
    def result(error=None):return GenieGetterPlan(helper,error is None,raw,None if raw is None else raw&255,
        tuple(p.steps),'' if error is None else str(error),None if error is None else error.request,module_sha256,profile,o)
    def global_value(slot,index):
        value=p.read('global',slot)
        if expected is not None and (slot,value)!=expected[index]:raise ValueError('Getter fixture global conflicts with selected source profile')
        return value
    try:
        root_slot=global_value(0x553e7c,0)
        root=p.read('guarded',root_slot,4)
        offset=global_value(GETTER_OFFSET_SLOTS[helper],1)
        raw=p.read('guarded',(root+offset)&0xffffffff,1)
        p.normal('wrapper_return')
        return result()
    except _Missing as error:return result(error)

def source_getter_observation(module_sha256,profile,helper,guarded_reads=(),normal_returns=None):
    """Explicit source fixture literals; not loaded-game values or a detector."""
    return MotionGenieObservation(global_samples=source_getter_globals(module_sha256,profile,helper),guarded_reads=guarded_reads,
        normal_returns={} if normal_returns is None else normal_returns)

class GenieGetterFrame:
    def __init__(self,helper,*,module_sha256=None,profile=None):
        self.helper=helper;self.module_sha256=module_sha256;self.profile=profile;self.observation=MotionGenieObservation();self.final=None
        plan_genie_getter(helper,self.observation,module_sha256=module_sha256,profile=profile)
    def advance(self,o):
        if not isinstance(o,MotionGenieObservation):raise ValueError('Typed ordered getter observations required')
        if self.final is not None:return self.final
        for _ in range(10):
            p=plan_genie_getter(self.helper,self.observation,module_sha256=self.module_sha256,profile=self.profile)
            if p.complete:self.final=p;return p
            req=p.request
            if req.kind=='normal':
                if o.normal_returns.get(req.label) is not True:return p
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,req.label:True})
            else:
                name={'global':'global_samples','guarded':'guarded_reads'}[req.kind];supplied=getattr(o,name)
                if req.index>=len(supplied):return p
                row=supplied[req.index]
                if req.kind=='guarded' and not row.normal_returned:return p
                cached=getattr(self.observation,name);assert req.index==len(cached)
                self.observation=replace(self.observation,**{name:cached+(row,)})
        raise ValueError('Genie getter exceeded source operand budget')

def getter_binding_gap(plan,helper):
    if plan is None:return None
    if not isinstance(plan,GenieGetterPlan) or plan.helper!=helper:raise ValueError('Bound getter helper identity differs from source call')
    if not isinstance(plan.input_snapshot,MotionGenieObservation):raise ValueError('Generated getter snapshot required')
    canonical=plan_genie_getter(helper,plan.input_snapshot,module_sha256=plan.module_sha256,profile=plan.profile)
    for name in ('complete','raw_eax','low_al','steps','missing','request','native_execution_verified','protection_side_effects_emulated'):
        if getattr(plan,name)!=getattr(canonical,name):raise ValueError('Bound getter result differs from its generated snapshot')
    return None if plan.complete else plan.missing or 'incomplete getter'

def retain_getter_snapshot(previous,new):
    if previous is None:return new
    if previous.complete:return previous
    getter_binding_gap(previous,previous.helper);getter_binding_gap(new,new.helper)
    if (previous.helper,previous.module_sha256,previous.profile)!=(new.helper,new.module_sha256,new.profile):raise ValueError('Bound getter invocation identity changed')
    a=previous.input_snapshot;b=new.input_snapshot
    for step in previous.steps:
        if step[0] in ('global','guarded'):
            name='global_samples' if step[0]=='global' else 'guarded_reads';i=step[1];old=getattr(a,name);fresh=getattr(b,name)
            if i<len(old) and (step[0]!='guarded' or old[i].normal_returned):
                if i>=len(fresh) or old[i]!=fresh[i]:raise ValueError('Consumed getter operand changed')
        elif step[0]=='normal_return' and a.normal_returns.get(step[1]) is True:
            if b.normal_returns.get(step[1]) is not True:raise ValueError('Consumed getter wrapper return regressed')
    return new

class GetterBindings:
    """Reached-only typed child validation; opaque legacy calls remain explicit."""
    def __init__(self,plans,expected_identity=None):self.plans=plans;self.used={};self.identity=expected_identity
    def enter(self,label,helper):
        plan=self.plans.get(label)
        if plan is None:return None
        self.used[label]=plan
        gap=getter_binding_gap(plan,helper);identity=(plan.module_sha256,plan.profile)
        if self.identity is not None and identity!=self.identity:raise ValueError('Reached getter source hash/profile identities differ')
        self.identity=identity;return gap
    def check_eax(self,label,value):
        if label in self.used and self.used[label].raw_eax!=value:raise ValueError('Parent raw EAX differs from bound getter return')
