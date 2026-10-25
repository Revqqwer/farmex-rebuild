"""00464a10 ->004649e4 captured indirect lookup; no target call execution."""
from dataclasses import dataclass,replace
from route_npc_click import NpcValueCapture


@dataclass(frozen=True)
class LookupContextSample:
    address:int
    value_dword:object=None


@dataclass(frozen=True)
class NpcLookupObservation:
    context_address_dword:object=None
    context_sample:object=None
    target_address_dword:object=None
    edx_dword:object=None
    indirect_returned:object=None
    result_eax:object=None
    inner_returned:object=None
    outer_returned:object=None


@dataclass(frozen=True)
class IndirectLookupCall:
    target_dword:int
    eax_dword:int
    ecx_dword:int
    edx_dword:int
    pushes:tuple
    entry_stack_dwords:tuple


@dataclass(frozen=True)
class NpcLookupPlan:
    complete:bool
    input_id_dword:int
    call:object=None
    capture:object=None
    steps:tuple=()
    needed:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


def raw(value):
    if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw reached lookup DWORD required')
    return value


def plan_npc_actor_lookup(input_id,o=None):
    raw(input_id);o=NpcLookupObservation() if o is None else o
    if not isinstance(o,NpcLookupObservation):raise ValueError('Typed lookup observation required')
    steps=[];call=None
    class Missing(Exception):pass
    def value(field):
        v=getattr(o,field)
        if v is None:raise Missing((field,))
        return raw(v)
    def normal(field):
        v=getattr(o,field)
        if v is not None and type(v) is not bool:raise ValueError('Explicit lookup normal receipt required')
        if v is not True:raise Missing((field,))
    def out(ok=False,eax=None,needed=None):
        return NpcLookupPlan(ok,input_id,call,NpcValueCapture(eax,True) if ok else None,tuple(steps),needed)
    try:
        steps.append(('global',0x553e8c));address=value('context_address_dword')
        steps.append(('direct_dword',address))
        sample=o.context_sample
        if sample is None:raise Missing(('context_sample','value_dword'))
        if not isinstance(sample,LookupContextSample) or raw(sample.address)!=address:
            raise ValueError('Reached lookup context sample address mismatch')
        if sample.value_dword is None:raise Missing(('context_sample','value_dword'))
        context=raw(sample.value_dword)
        steps.append(('global',0x553e9c));target=value('target_address_dword')
        edx=value('edx_dword')
        # Actual instruction context, not a guessed C/C++ function signature.
        call=IndirectLookupCall(target,0,context,edx,(1,input_id),(input_id,1))
        steps.append(('indirect_call_context',call))
        normal('indirect_returned');eax=value('result_eax')
        normal('inner_returned');normal('outer_returned')
        return out(True,eax)
    except Missing as error:return out(needed=error.args[0])


class NpcLookupFrame:
    """Freeze only consumed context/target/register/result and True receipts.

    Source has no context/target null guards. A zero address never fabricates
    a zero lookup result or a normal return. There are no native operations.
    """
    def __init__(self,input_id):
        raw(input_id);self.input_id=input_id;self.observation=NpcLookupObservation();self.final=None
    def advance(self,incoming=None):
        if self.final is not None:return self.final
        incoming=NpcLookupObservation() if incoming is None else incoming
        if not isinstance(incoming,NpcLookupObservation):raise ValueError('Typed lookup capture required')
        for _ in range(12):
            p=plan_npc_actor_lookup(self.input_id,self.observation)
            if p.complete:self.final=p;return p
            if len(p.needed)==2:
                sample=incoming.context_sample
                if sample is None:return p
                if not isinstance(sample,LookupContextSample) or raw(sample.address)!=self.observation.context_address_dword:
                    raise ValueError('Reached lookup context sample address mismatch')
                if sample.value_dword is None:return p
                raw(sample.value_dword)
                self.observation=replace(self.observation,context_sample=sample)
            else:
                field=p.needed[0];v=getattr(incoming,field)
                if v is None:return p
                if field.endswith('_returned'):
                    if type(v) is not bool:raise ValueError('Explicit reached lookup receipt required')
                    if v is not True:return p
                else:raw(v)
                self.observation=replace(self.observation,**{field:v})
        raise ValueError('Own lookup advancement budget exhausted')
