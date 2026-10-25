"""0046c1a0/0046c2ac normal fresh-vector membership caller; no native IO."""
from dataclasses import dataclass
from source_unicode import UnicodeEqualityObservation,plan_unicode_equality,utf16_key

def _raw(v):
    if v is not None and (type(v) is not int or not 0<=v<1<<32):raise ValueError('Raw DWORD required')

def _normal(v):
    if v is not None and type(v) is not bool:raise ValueError('Separate normal-return boolean required')

def source_vector_count(begin,end):
    """low32 SUB, signed conditional ADD3, SAR2; unsigned caller comparison."""
    _raw(begin);_raw(end)
    if begin is None:raise ValueError('Observed vector begin required')
    if begin==0:return 0
    if end is None:raise ValueError('Observed fresh vector end required')
    delta=(end-begin)&0xffffffff
    signed=delta-(1<<32) if delta&0x80000000 else delta
    if signed<0:
        delta=(delta+3)&0xffffffff
        signed=delta-(1<<32) if delta&0x80000000 else delta
    return (signed>>2)&0xffffffff

@dataclass(frozen=True)
class NameFilterIteration:
    index:int
    count_begin_dword:object=None
    count_end_dword:object=None
    slot_base_dword:object=None
    conversion_returned:object=None
    converted_text:object=None
    equality:object=None
    temporary_cleanup_returned:object=None
    def __post_init__(self):
        _raw(self.index)
        if self.index is None:raise ValueError('Explicit iteration index required')
        for v in (self.count_begin_dword,self.count_end_dword,self.slot_base_dword):_raw(v)
        for v in (self.conversion_returned,self.temporary_cleanup_returned):_normal(v)
        if self.converted_text is not None:utf16_key(self.converted_text)
        if self.equality is not None and not isinstance(self.equality,UnicodeEqualityObservation):raise ValueError('Typed equality observation required')

@dataclass(frozen=True)
class NameFilterObservation:
    input_copy_returned:object=None
    input_text:object=None
    iterations:tuple=()
    input_cleanup_returned:object=None
    def __post_init__(self):
        _normal(self.input_copy_returned);_normal(self.input_cleanup_returned)
        if self.input_text is not None:utf16_key(self.input_text)
        if type(self.iterations) is not tuple or any(not isinstance(v,NameFilterIteration) for v in self.iterations):raise ValueError('Ordered typed fresh iterations required')

@dataclass(frozen=True)
class NameFilterPlan:
    complete:bool
    status:str
    kind:str
    input_text:object=None
    al:object=None
    eax_dword:object=None
    match_index:object=None
    steps:tuple=()
    equality_plans:tuple=()
    missing:str=''
    native_execution_verified:bool=False

def plan_name_filter(kind,o):
    if kind not in ('primary','secondary'):raise ValueError('Source primary/secondary filter required')
    if not isinstance(o,NameFilterObservation):raise ValueError('Typed filter observation required')
    steps=[];equalities=[];match=None;index=0
    vector_offset,slot_offset=(0xe0,0xf0) if kind=='primary' else (0x100,0x110)
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def normal(v,label):
        steps.append(('normal_return',label))
        if v is not True:raise Missing(label)
    def result(complete,al=None,eax=None,missing=''):
        return NameFilterPlan(complete,'membership_modeled' if complete else 'needs_observation',kind,
            o.input_text,al,eax,match,tuple(steps),tuple(equalities),missing)
    try:
        normal(o.input_copy_returned,'00505bf4 input Unicode copy/refcount span')
        while True:
            if index>=len(o.iterations):raise Missing('fresh vector count at index%d'%index)
            row=o.iterations[index]
            if row.index!=index:raise ValueError('Name filter iteration order mismatch')
            begin=need(row.count_begin_dword,'fresh count begin')
            end=None if begin==0 else need(row.count_end_dword,'fresh count end')
            count=source_vector_count(begin,end)
            steps.append(('vector_count',index,vector_offset,begin,end,count))
            if count<=index:
                normal(o.input_cleanup_returned,'input Unicode final cleanup')
                return result(True,0,0)
            base=need(row.slot_base_dword,'fresh slot base (not cached count begin)')
            address=(base+((index<<2)&0xffffffff))&0xffffffff
            steps.append(('slot_conversion',index,slot_offset,base,address))
            normal(row.conversion_returned,'00403d84 slot conversion')
            eq=need(row.equality,'00505d3c Unicode equality observation')
            if eq.use_owned_text_model:
                left=need(o.input_text,'input post-copy Unicode text')
                right=need(row.converted_text,'slot post-conversion Unicode text')
                if eq.left_text is None or eq.right_text is None or utf16_key(eq.left_text)!=utf16_key(left) or utf16_key(eq.right_text)!=utf16_key(right):
                    raise ValueError('Owned equality text must match filter input and converted slot')
            ep=plan_unicode_equality(eq);equalities.append((index,ep))
            if not ep.complete:raise Missing(ep.missing)
            # EAX comparison result is saved before temporary cleanup, restored
            # into EDX, and tested through DL; cleanup cannot replace its AL.
            normal(row.temporary_cleanup_returned,'temporary Unicode cleanup before TEST DL')
            steps.append(('saved_comparison_al',index,ep.al))
            if ep.al:
                match=index
                normal(o.input_cleanup_returned,'input Unicode match cleanup')
                # MOV AL,1 preserves an otherwise unobserved upper EAX after
                # temporary cleanup. Do not claim full EAX=1.
                return result(True,1)
            index=(index+1)&0xffffffff
    except Missing as e:return result(False,missing=str(e))
