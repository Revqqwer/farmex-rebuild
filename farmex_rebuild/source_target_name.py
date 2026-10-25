"""00462630 target-ID and00466144 name-by-index normal plans; no native IO."""
from dataclasses import dataclass
from source_coin import SourceCoinObservation,plan_guarded_dword
from game_text import npc_text_request,replay_text_copy

def _raw(v):
    if v is not None and (type(v) is not int or not 0<=v<1<<32):raise ValueError('Raw DWORD required')
def _normal(v):
    if v is not None and type(v) is not bool:raise ValueError('Separate normal-return observation required')

@dataclass(frozen=True)
class TargetIdPlan:
    complete:bool
    target_id_dword:object=None
    steps:tuple=()
    guarded_plans:tuple=()
    missing:str=''
    native_execution_verified:bool=False

def plan_target_id(o):
    # Reuse the immutable global/guarded-sample carrier,not coin addresses.
    if not isinstance(o,SourceCoinObservation):raise ValueError('Typed root/global/guarded observations required')
    steps=[];guards=[];gp=0;sp=0
    class Missing(Exception):pass
    def g(address):
        nonlocal gp
        steps.append(('global',address))
        if gp>=len(o.global_samples):raise Missing('target ID global at%08x'%address)
        at,value=o.global_samples[gp];gp+=1
        if at!=address:raise ValueError('Target-ID global order mismatch')
        if value is None:raise Missing('target ID global value')
        return value
    def dword(address):
        nonlocal sp
        address&=0xffffffff;sample=None
        if address:
            sample=o.guarded_samples[sp] if sp<len(o.guarded_samples) else None;sp+=1
        p=plan_guarded_dword(address,sample);guards.append(p)
        if not p.complete:raise Missing(p.missing)
        return p.value_dword
    try:
        pointer=dword(g(0x553e7c));value=dword(pointer+g(0x554044))
        return TargetIdPlan(True,value,tuple(steps),tuple(guards))
    except Missing as e:return TargetIdPlan(False,steps=tuple(steps),guarded_plans=tuple(guards),missing=str(e))

@dataclass(frozen=True)
class NameByIndexObservation:
    string_init_returned:object=None
    lookup_pointer_dword:object=None
    lookup_returned:object=None
    global_samples:tuple=()
    guarded_samples:tuple=()
    name_span_returned:object=None
    use_captured_copy:bool=False
    readable:object=None
    copied_bytes:object=None
    copy_codec:object=None
    unicode_text:object=None
    ansi_output_span_returned:object=None
    ansi_output_bytes:object=None
    fallback_span_returned:object=None
    def __post_init__(self):
        _raw(self.lookup_pointer_dword)
        SourceCoinObservation(self.global_samples,self.guarded_samples)
        for v in (self.string_init_returned,self.lookup_returned,self.name_span_returned,self.readable,
                  self.ansi_output_span_returned,self.fallback_span_returned):_normal(v)
        if type(self.use_captured_copy) is not bool:raise ValueError('Explicit own byte-copy selection required')
        for v in (self.copied_bytes,self.ansi_output_bytes):
            if v is not None and type(v) is not bytes:raise ValueError('Exact name bytes required')
        for v in (self.copy_codec,self.unicode_text):
            if v is not None and type(v) is not str:raise ValueError('Explicit text/codec required')

@dataclass(frozen=True)
class NameByIndexPlan:
    complete:bool
    status:str
    index_dword:object=None
    ansi_bytes:object=None
    unicode_text:object=None
    text_request:object=None
    copy_plan:object=None
    steps:tuple=()
    guarded_plans:tuple=()
    missing:str=''
    native_execution_verified:bool=False

def plan_name_by_index(index_dword,o):
    _raw(index_dword)
    if not isinstance(o,NameByIndexObservation):raise ValueError('Typed name lookup observations required')
    steps=[];guards=[];request=None;copy=None;unicode=None;gp=0;sp=0
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def normal(v,label):
        steps.append(('normal_return',label))
        if v is not True:raise Missing(label)
    def result(complete,status,ansi=None,missing=''):
        return NameByIndexPlan(complete,status,index_dword,ansi,unicode,request,copy,tuple(steps),tuple(guards),missing)
    def fallback():
        normal(o.fallback_span_returned,'literal523705 empty ANSI assignment and cleanups')
        return result(True,'empty_fallback',b'')
    def g(address):
        nonlocal gp
        steps.append(('global',address))
        if gp>=len(o.global_samples):raise Missing('name global at%08x'%address)
        at,value=o.global_samples[gp];gp+=1
        if at!=address:raise ValueError('Name lookup global read order mismatch')
        return need(value,'name global value')
    def dword(address):
        nonlocal sp
        address&=0xffffffff;sample=None
        if address:
            sample=o.guarded_samples[sp] if sp<len(o.guarded_samples) else None;sp+=1
        p=plan_guarded_dword(address,sample);guards.append(p)
        if not p.complete:raise Missing(p.missing)
        return p.value_dword
    try:
        normal(o.string_init_returned,'00404a78 local Unicode initialization')
        raw=need(index_dword,'name lookup signed index');signed=raw-(1<<32) if raw&0x80000000 else raw
        if signed<0 or signed>=3000:return fallback()
        steps.append(('00464a10',raw));normal(o.lookup_returned,'00464a10 independent normal return')
        pointer=need(o.lookup_pointer_dword,'record pointer')
        if pointer==0:return fallback()
        length=dword(pointer+g(0x553fec));offset=g(0x553fe8)
        signed_length=length-(1<<32) if length&0x80000000 else length
        indirect=dword(pointer+offset) if signed_length>=16 else None
        request=npc_text_request(pointer,offset,length,indirect,signed_threshold=True)
        normal(o.name_span_returned,'0045dca8 copy/Unicode assignment/temporary cleanups')
        unicode=o.unicode_text
        if o.use_captured_copy:
            if unicode is not None:raise ValueError('Captured copy conflicts with raw Unicode name')
            copy=replay_text_copy(request.byte_count,o.readable,o.copied_bytes,codec=o.copy_codec)
            if copy.status!='complete':raise Missing('name byte copy: '+copy.status)
            unicode=copy.text
        normal(o.ansi_output_span_returned,'004073a0 ANSI output assignment and final cleanups')
        ansi=need(o.ansi_output_bytes,'post-conversion output ANSI bytes')
        return result(True,'name_by_index_modeled',ansi)
    except Missing as e:return result(False,'needs_observation',missing=str(e))
