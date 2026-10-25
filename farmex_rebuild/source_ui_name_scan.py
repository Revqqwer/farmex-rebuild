"""0046601c normal UI duplicate scan; fresh signed count/conversions, no IO."""
from dataclasses import dataclass
from source_unicode import UnicodeEqualityObservation,plan_unicode_equality,utf16_key

def _normal(v):
    if v is not None and type(v) is not bool:raise ValueError('Explicit normal-return boolean required')

@dataclass(frozen=True)
class UiNameScanRow:
    index:int
    count_dword:object=None
    needle_conversion_returned:object=None
    needle_unicode:object=None
    item_getter_returned:object=None
    item_unicode:object=None
    equality:object=None
    temporary_cleanups_returned:object=None
    def __post_init__(self):
        for v in (self.index,self.count_dword):
            if v is not None and (type(v) is not int or not 0<=v<1<<32):raise ValueError('Raw iteration/count DWORD required')
        if self.index is None:raise ValueError('Explicit iteration index required')
        for v in (self.needle_conversion_returned,self.item_getter_returned,self.temporary_cleanups_returned):_normal(v)
        for text in (self.needle_unicode,self.item_unicode):
            if text is not None:utf16_key(text)
        if self.equality is not None and not isinstance(self.equality,UnicodeEqualityObservation):raise ValueError('Typed equality observation required')

@dataclass(frozen=True)
class UiNameScanObservation:
    input_copy_returned:object=None
    input_ansi_bytes:object=None
    iterations:tuple=()
    input_cleanup_returned:object=None
    def __post_init__(self):
        _normal(self.input_copy_returned);_normal(self.input_cleanup_returned)
        if self.input_ansi_bytes is not None and type(self.input_ansi_bytes) is not bytes:raise ValueError('Exact ANSI input required')
        if type(self.iterations) is not tuple or any(not isinstance(r,UiNameScanRow) for r in self.iterations):raise ValueError('Ordered typed UI scan rows required')

@dataclass(frozen=True)
class UiNameScanPlan:
    complete:bool
    status:str
    input_ansi_bytes:object=None
    al:object=None
    eax_dword:object=None
    match_index:object=None
    steps:tuple=()
    equality_plans:tuple=()
    missing:str=''
    native_execution_verified:bool=False

def plan_ui_name_scan(o):
    if not isinstance(o,UiNameScanObservation):raise ValueError('Typed UI scan observation required')
    steps=[];eqs=[];match=None;index=0
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def normal(v,label):
        steps.append(('normal_return',label))
        if v is not True:raise Missing(label)
    def result(complete,al=None,eax=None,missing=''):
        return UiNameScanPlan(complete,'duplicate_scan_modeled' if complete else 'needs_observation',
            o.input_ansi_bytes,al,eax,match,tuple(steps),tuple(eqs),missing)
    try:
        normal(o.input_copy_returned,'00504ef8 ANSI input copy')
        while True:
            if index>=len(o.iterations):raise Missing('fresh UI count at index%d'%index)
            row=o.iterations[index]
            if row.index!=index:raise ValueError('UI duplicate scan index/order mismatch')
            count=need(row.count_dword,'fresh UI count DWORD')
            signed=count-(1<<32) if count&0x80000000 else count
            signed_index=index-(1<<32) if index&0x80000000 else index
            steps.append(('UI_count',index,0x14,count))
            if signed<=signed_index:
                normal(o.input_cleanup_returned,'final ANSI input cleanup')
                return result(True,0,0)
            # Conversion is inside the source loop,not cached for all items.
            normal(row.needle_conversion_returned,'00403d84 fresh ANSI needle conversion')
            steps.append(('UI_item_getter',index,0xc))
            normal(row.item_getter_returned,'fresh Unicode UI item getter')
            eq=need(row.equality,'00505d3c equality observation')
            if eq.use_owned_text_model:
                left=need(row.needle_unicode,'fresh converted Unicode needle')
                right=need(row.item_unicode,'fresh Unicode UI item')
                if eq.left_text is None or eq.right_text is None or utf16_key(eq.left_text)!=utf16_key(left) or utf16_key(eq.right_text)!=utf16_key(right):
                    raise ValueError('Owned equality input mismatch')
            p=plan_unicode_equality(eq);eqs.append((index,p))
            if not p.complete:raise Missing(p.missing)
            # Save EAX before both cleanups,POP EAX,TEST AL; unlike vector
            # filter0046c1a0,known upper EAX bits survive this match path.
            normal(row.temporary_cleanups_returned,'two temporary Unicode cleanups')
            steps.append(('restored_comparison_eax',index,p.eax_dword,p.al))
            if p.al:
                match=index
                normal(o.input_cleanup_returned,'matched ANSI input cleanup')
                return result(True,1,p.eax_dword)
            index=(index+1)&0xffffffff
    except Missing as e:return result(False,missing=str(e))
