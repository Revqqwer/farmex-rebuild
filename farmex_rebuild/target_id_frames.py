"""Demand-cached00462630 root/offset/target DWORD reads; no native effects."""
from dataclasses import dataclass,replace
from source_coin import GuardedDwordSample,plan_guarded_dword
from route_npc_click import NpcValueCapture


@dataclass(frozen=True)
class TargetIdObservation:
    root_address_dword:object=None
    root_sample:object=None
    root_returned:object=None
    offset_dword:object=None
    target_sample:object=None
    target_returned:object=None
    getter_returned:object=None


@dataclass(frozen=True)
class TargetIdFramePlan:
    complete:bool
    value:object=None
    capture:object=None
    root:object=None
    address:object=None
    steps:tuple=()
    guards:tuple=()
    needed:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


def plan_target_id_capture(o):
    if not isinstance(o,TargetIdObservation):raise ValueError('Typed target getter capture required')
    steps=[];guards=[];root=None;address=None
    class Missing(Exception):pass
    def value(field):
        v=getattr(o,field)
        if v is None:raise Missing((field,))
        if type(v) is not int or not 0<=v<=0xffffffff:raise ValueError('Raw reached target DWORD required')
        return v
    def normal(field):
        v=getattr(o,field)
        if v is not None and type(v) is not bool:raise ValueError('Separate target helper normal receipt required')
        if v is not True:raise Missing((field,))
    def guarded(at,field):
        sample=getattr(o,field)
        p=plan_guarded_dword(at,sample);guards.append(p);steps.append(('0045dc44',at))
        if not p.complete:
            sub='protection_return_dword' if sample is None or sample.protection_return_dword is None else 'value_dword'
            raise Missing((field,sub))
        return p.value_dword
    def out(ok=False,result=None,needed=None):
        return TargetIdFramePlan(ok,result,NpcValueCapture(result,True) if ok else None,root,address,
                                 tuple(steps),tuple(guards),needed)
    try:
        steps.append(('global',0x553e7c));slot=value('root_address_dword')
        root_value=guarded(slot,'root_sample');normal('root_returned');root=root_value
        steps.append(('global',0x554044));address=(root+value('offset_dword'))&0xffffffff
        target=guarded(address,'target_sample');normal('target_returned')
        normal('getter_returned');return out(True,target)
    except Missing as error:return out(needed=error.args[0])


class TargetIdFrame:
    """One invocation. Instantiate separately for each source call site.

    Reached root/offset and nested protection/value captures are frozen only
    when consumed; False returns and unreached fields remain replaceable.
    Plans/step descriptions cannot execute native memory or protection APIs.
    """
    def __init__(self):self.observation=TargetIdObservation();self.final=None
    def advance(self,incoming=None):
        if self.final is not None:return self.final
        incoming=TargetIdObservation() if incoming is None else incoming
        if not isinstance(incoming,TargetIdObservation):raise ValueError('Typed target getter capture required')
        for _ in range(16):
            p=plan_target_id_capture(self.observation)
            if p.complete:self.final=p;return p
            path=p.needed
            if len(path)==1:
                field=path[0];v=getattr(incoming,field)
                if v is None:return p
                if field.endswith('_returned'):
                    if type(v) is not bool:raise ValueError('Explicit reached target receipt required')
                    if v is not True:return p
                elif type(v) is not int or not 0<=v<=0xffffffff:
                    raise ValueError('Raw reached target DWORD required')
                self.observation=replace(self.observation,**{field:v})
            else:
                field,sub=path;sample=getattr(incoming,field)
                if sample is None:return p
                if not isinstance(sample,GuardedDwordSample):raise ValueError('Typed reached guarded target sample required')
                at=self.observation.root_address_dword if field=='root_sample' else p.address
                if sample.address!=at:raise ValueError('Reached target sample address mismatch')
                v=getattr(sample,sub)
                if v is None:return p
                current=getattr(self.observation,field) or GuardedDwordSample(at)
                self.observation=replace(self.observation,**{field:replace(current,**{sub:v})})
        raise ValueError('Own target advancement budget exhausted')
