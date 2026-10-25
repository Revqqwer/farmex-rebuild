"""4655e8 relative-ID wrapper -> shared lookup/dispatch operand role.

Does not call465640. All helper returns and operand maps are explicit own
snapshots; no native invocation or live profile inference.
"""
from dataclasses import dataclass
from skill_native_plans import SkillObservation,SkillPlan,plan_alternate_skill
from native_profile_versions import versioned_profile_globals

def _raw(v,optional=False):
    if optional and v is None:return
    if type(v) is not int or not 0<=v<=0xffffffff:raise ValueError('Raw generic skill DWORD required')

@dataclass(frozen=True)
class GenericSkillObservation:
    relative_skill:int
    actor_id:int
    class_eax:object=None
    class_helper_returned:object=None
    lookup_wrapper_returned:object=None
    native_target_returned:object=None
    operands:object=None
    module_sha256:object=None
    profile:object=None
    def __post_init__(self):
        _raw(self.relative_skill);_raw(self.actor_id);_raw(self.class_eax,True)
        for name in ('class_helper_returned','lookup_wrapper_returned','native_target_returned'):
            value=getattr(self,name)
            if value is not None and type(value) is not bool:raise ValueError('Separate generic helper normal receipts required')
        if self.operands is not None and not isinstance(self.operands,SkillObservation):raise ValueError('Typed immutable skill operand snapshot required')
        if self.module_sha256 is not None or self.profile is not None:
            expected=versioned_profile_globals(self.module_sha256,self.profile,'skill')
            if self.operands is not None and any(self.operands.globals.get(k)!=v for k,v in expected.items()):
                raise ValueError('Generic operand fixture differs from selected source hash/profile')

@dataclass(frozen=True)
class GenericSkillPlan:
    complete:bool
    relative_skill:int
    actor_id:int
    action_id:object=None
    operand_plan:object=None
    returned_eax:object=None
    steps:tuple=()
    missing:str=''
    module_sha256:object=None
    profile:object=None
    source_helper:str='004655e8'
    native_execution_verified:bool=False
    skill_effect_verified:bool=False
    input_snapshot:object=None
    def __post_init__(self):
        _raw(self.relative_skill);_raw(self.actor_id);_raw(self.action_id,True);_raw(self.returned_eax,True)
        if type(self.complete) is not bool or self.source_helper!='004655e8':raise ValueError('Known generic source plan required')
        if self.complete and (self.action_id is None or self.returned_eax is None or self.missing or not isinstance(self.operand_plan,SkillPlan) or self.operand_plan.status!='native_return_observed'):
            raise ValueError('Complete generic operand/result plan required')
        if self.complete and (not self.operand_plan.calls or self.operand_plan.calls[-1].helper!='004655e8' or len(self.operand_plan.calls[-1].push_order)!=2 or self.operand_plan.calls[-1].push_order[1]!=self.actor_id):
            raise ValueError('Actual generic dispatch role/actor required')

def plan_generic_chat_skill(o):
    if not isinstance(o,GenericSkillObservation):raise ValueError('Typed relative skill invocation required')
    action=None;inner=None;steps=[]
    def result(ok,missing=''):
        return GenericSkillPlan(ok,o.relative_skill,o.actor_id,action,inner,
            o.operands.native_return if ok else None,tuple(steps),missing,o.module_sha256,o.profile,input_snapshot=o)
    steps.append(('opaque_class_helper','0046256c'))
    if o.class_helper_returned is not True:return result(False,'0046256c normal return')
    if o.class_eax is None:return result(False,'class helper raw EAX')
    action=(o.class_eax*1000+o.relative_skill)&0xffffffff
    steps.append(('IMUL_ADD_low32',o.class_eax,1000,o.relative_skill,action))
    if o.operands is None:return result(False,'bound lookup/dispatch operand snapshot')
    if o.operands.action_id!=action or o.operands.actor_id!=o.actor_id:
        raise ValueError('Generic computed action/actor differs from bound operand snapshot')
    # Stable maps are an own contract. Separate normal receipts remain required.
    if o.lookup_wrapper_returned is not True:return result(False,'00464990 wrapper normal return')
    inner=plan_alternate_skill(o.operands,dispatch_helper='004655e8')
    if inner.status=='needs_observation':return result(False,inner.missing)
    if o.native_target_returned is not True:return result(False,'generic indirect target normal return')
    if o.operands.native_return is None:return result(False,'generic indirect target raw EAX')
    steps.append(('raw_EAX_forwarded',o.operands.native_return))
    return result(True)

def versioned_generic_skill(module_sha256,profile,relative_skill,actor_id,class_eax,*,direct_words=None,
                            lookup_return=None,native_return=None,class_helper_returned=None,
                            lookup_wrapper_returned=None,native_target_returned=None,runtime_globals=None):
    _raw(class_eax);_raw(relative_skill);_raw(actor_id)
    globals=versioned_profile_globals(module_sha256,profile,'skill',runtime_globals=runtime_globals)
    action=(class_eax*1000+relative_skill)&0xffffffff
    operands=SkillObservation(action,actor_id,globals,{} if direct_words is None else direct_words,lookup_return,native_return)
    return GenericSkillObservation(relative_skill,actor_id,class_eax,class_helper_returned,lookup_wrapper_returned,
                                   native_target_returned,operands,module_sha256,profile)

def generic_binding_gap(plan,relative_skill,actor_id):
    if plan is None:return None
    if not isinstance(plan,GenericSkillPlan):raise ValueError('Typed generic child plan required')
    if plan.relative_skill!=relative_skill or plan.actor_id!=actor_id:
        raise ValueError('Generic child arguments differ from reached consumer call')
    return None if plan.complete else plan.missing or 'incomplete generic child'

def retain_generic_snapshot(previous,new):
    """Own stable-snapshot enrichment, not a live mutable-map execution model."""
    if previous is None:return new
    if previous.complete:return previous
    a=previous.input_snapshot;b=new.input_snapshot
    if not isinstance(a,GenericSkillObservation) or not isinstance(b,GenericSkillObservation):
        raise ValueError('Bound frame requires generated generic input snapshots')
    for name in ('relative_skill','actor_id','module_sha256','profile'):
        if getattr(a,name)!=getattr(b,name):raise ValueError('Bound generic invocation identity changed')
    if a.class_eax is not None and b.class_eax!=a.class_eax:raise ValueError('Bound generic class snapshot changed')
    for name in ('class_helper_returned','lookup_wrapper_returned','native_target_returned'):
        if getattr(a,name) is True and getattr(b,name) is not True:raise ValueError('Consumed generic return regressed')
    if a.operands is not None:
        if b.operands is None:raise ValueError('Bound generic operand snapshot disappeared')
        for name in ('action_id','actor_id'):
            if getattr(a.operands,name)!=getattr(b.operands,name):raise ValueError('Bound generic operand identity changed')
        for name in ('globals','direct_words'):
            for k,v in getattr(a.operands,name).items():
                if getattr(b.operands,name).get(k)!=v:raise ValueError('Stable generic operand map changed')
        for name in ('lookup_return','native_return'):
            old=getattr(a.operands,name)
            if old is not None and getattr(b.operands,name)!=old:raise ValueError('Bound generic raw return changed')
    return new
