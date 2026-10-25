"""Route callback's signed inline/pointer name producer, captured data only.

Distinct from merchant metadata: inline mode does not read a pointer DWORD.
No process reads, VirtualProtect, native string calls or encoding guesses.
"""
from dataclasses import dataclass,replace
from source_coin import GuardedDwordSample,plan_guarded_dword
from game_text import npc_text_request,replay_text_copy
from route_npc_click import NpcValueCapture


@dataclass(frozen=True)
class RouteNpcNameObservation:
    storage_offset_dword:object=None
    storage_sample:object=None
    storage_returned:object=None
    local_ansi_init_returned:object=None
    std_factory_returned:object=None
    std_copy_returned:object=None
    std_initial_cleanup_returned:object=None
    name_offset_dword:object=None
    pointer_sample:object=None
    pointer_returned:object=None
    temporary_ansi_init_returned:object=None
    readable:object=None
    copied_bytes:object=None
    copy_returned:object=None
    ansi_assignment_returned:object=None
    temporary_cleanup_returned:object=None
    std_assignment_returned:object=None


@dataclass(frozen=True)
class RouteNpcNamePlan:
    complete:bool
    status:str
    name_bytes:object=None
    capture:object=None
    request:object=None
    copy:object=None
    steps:tuple=()
    guards:tuple=()
    needed:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


def plan_route_npc_name(actor,o=None):
    if type(actor) is not int or not 0<actor<=0xffffffff:
        raise ValueError('Nonzero source actor DWORD required')
    o=RouteNpcNameObservation() if o is None else o
    if not isinstance(o,RouteNpcNameObservation):raise ValueError('Typed route name observations required')
    steps=[];guards=[];request=None;copy=None
    class Missing(Exception):pass
    def need(field,kind):
        value=getattr(o,field)
        if value is None:raise Missing(field)
        if kind=='dword':
            if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw reached DWORD required: '+field)
        elif type(value) is not kind:raise ValueError('Reached name value type differs: '+field)
        return value
    def normal(field,helper):
        steps.append(('normal_return',helper,field))
        if need(field,bool) is not True:raise Missing(field)
    def guarded(address,field,returned):
        sample=getattr(o,field)
        if sample is not None and not isinstance(sample,GuardedDwordSample):raise ValueError('Typed reached guarded sample required')
        steps.append(('0045dc44',address))
        plan=plan_guarded_dword(address,sample);guards.append(plan)
        if not plan.complete:raise Missing(field+':'+plan.missing)
        normal(returned,'0045dc44')
        return plan.value_dword
    def out(complete,status,data=None,needed=None):
        return RouteNpcNamePlan(complete,status,data,NpcValueCapture(data,True) if complete else None,
                                request,copy,tuple(steps),tuple(guards),needed)
    try:
        steps.append(('global',0x553fec));offset=need('storage_offset_dword','dword')
        storage=guarded((actor+offset)&0xffffffff,'storage_sample','storage_returned')
        for field,helper in (('local_ansi_init_returned','00404148'),('std_factory_returned','00403808'),
                             ('std_copy_returned','0040382c'),('std_initial_cleanup_returned','00403860')):
            normal(field,helper)
        steps.append(('global',0x553fe8));offset=need('name_offset_dword','dword')
        signed=storage if storage<0x80000000 else storage-(1<<32)
        pointer=None
        if signed>=16:pointer=guarded((actor+offset)&0xffffffff,'pointer_sample','pointer_returned')
        request=npc_text_request(actor,offset,storage,pointer,signed_threshold=True)
        normal('temporary_ansi_init_returned','00404148')
        steps.append(('0045dca8',request.address,request.byte_count))
        readable=need('readable',bool)
        # Unreadable memory chooses the empty source fallback before memcpy.
        copied=need('copied_bytes',bytes) if readable and request.byte_count<=512 else None
        copy=replay_text_copy(request.byte_count,readable,copied)
        if copy.status not in ('complete','needs_codepage'):
            return out(False,'copy:'+copy.status,needed='copy:'+copy.status)
        normal('copy_returned','0045dca8')
        normal('ansi_assignment_returned','AnsiString assignment')
        normal('temporary_cleanup_returned','004040f8')
        # Source then assigns a NUL-terminated ANSI pointer into std::string.
        # No Unicode decoding is needed for this byte-search input.
        normal('std_assignment_returned','004038e4')
        return out(True,'captured_route_name',copy.ansi_bytes)
    except Missing as error:return out(False,'needs_observation',needed=str(error))


class RouteNpcNameFrame:
    """One actor/name invocation, retaining only consumed observations."""
    def __init__(self,actor):
        self.actor=actor;self.observation=RouteNpcNameObservation();self.final=None
        plan_route_npc_name(actor,self.observation)
    def advance(self,incoming=None):
        if self.final is not None:return self.final
        incoming=RouteNpcNameObservation() if incoming is None else incoming
        if not isinstance(incoming,RouteNpcNameObservation):raise ValueError('Typed route name capture required')
        for _ in range(32):
            p=plan_route_npc_name(self.actor,self.observation)
            if p.complete:self.final=p;return p
            needed=p.needed
            if needed.startswith('copy:'):return p
            if ':' in needed:
                group=needed.split(':',1)[0];sample=getattr(incoming,group)
                if sample is None:return p
                if not isinstance(sample,GuardedDwordSample):raise ValueError('Typed reached name sample required')
                offset=self.observation.storage_offset_dword if group=='storage_sample' else self.observation.name_offset_dword
                address=(self.actor+offset)&0xffffffff
                if sample.address!=address:raise ValueError('Reached name sample address mismatch')
                current=getattr(self.observation,group) or GuardedDwordSample(address)
                sub='protection_return_dword' if current.protection_return_dword is None else 'value_dword'
                value=getattr(sample,sub)
                if value is None:return p
                self.observation=replace(self.observation,**{group:replace(current,**{sub:value})})
                continue
            value=getattr(incoming,needed)
            if value is None:return p
            if needed.endswith('_returned') or needed=='readable':
                if type(value) is not bool:raise ValueError('Explicit reached name receipt/guard required')
                if needed.endswith('_returned') and value is not True:return p
            elif needed=='copied_bytes':
                if type(value) is not bytes:raise ValueError('Exact reached name byte range required')
                if len(value)<p.request.byte_count:return p
                if len(value)!=p.request.byte_count:raise ValueError('Name byte range length mismatch')
            elif type(value) is not int or not 0<=value<=0xffffffff:
                raise ValueError('Raw reached name DWORD required')
            self.observation=replace(self.observation,**{needed:value})
        raise ValueError('Own name advancement budget exhausted')
