"""0046c3b8 UI-to-vector normal caller; own projection, no game/native IO."""
from dataclasses import dataclass,replace
from source_name_filter import NameFilterObservation,source_vector_count,plan_name_filter
from source_unicode import utf16_key

def _dword(v):
    if v is not None and (type(v) is not int or not 0<=v<1<<32):raise ValueError('Raw DWORD required')
def _normal(v):
    if v is not None and type(v) is not bool:raise ValueError('Explicit normal-return boolean required')
def _bytes_tuple(v):
    if v is not None and (type(v) is not tuple or any(type(x) is not bytes for x in v)):raise ValueError('Exact immutable ANSI rows required')

@dataclass(frozen=True)
class NameListsState:
    white:tuple=()
    black:tuple=()
    def __post_init__(self):
        for v in (self.white,self.black):
            _bytes_tuple(v)
            if v is None:raise ValueError('Known own list state required')

@dataclass(frozen=True)
class NameListRefreshRow:
    index:int
    ui_count_dword:object=None
    text_get_returned:object=None
    unicode_text:object=None
    ansi_conversion_returned:object=None
    ansi_bytes:object=None
    assignment_cleanup_returned:object=None
    vector_size_dword:object=None
    vector_capacity_dword:object=None
    insertion_returned:object=None
    fast_end_dword:object=None
    def __post_init__(self):
        _dword(self.index)
        if self.index is None:raise ValueError('Explicit list index required')
        for v in (self.ui_count_dword,self.vector_size_dword,self.vector_capacity_dword,self.fast_end_dword):_dword(v)
        for v in (self.text_get_returned,self.ansi_conversion_returned,self.assignment_cleanup_returned,self.insertion_returned):_normal(v)
        if self.unicode_text is not None:utf16_key(self.unicode_text)
        if self.ansi_bytes is not None and type(self.ansi_bytes) is not bytes:raise ValueError('Captured post-conversion ANSI bytes required')

@dataclass(frozen=True)
class NameListRefreshObservation:
    scratch_init_returned:object=None
    black_reset_returned:object=None
    white_reset_returned:object=None
    black_after_reset:object=None
    white_after_reset:object=None
    black_rows:tuple=()
    white_rows:tuple=()
    final_cleanup_returned:object=None
    def __post_init__(self):
        for v in (self.scratch_init_returned,self.black_reset_returned,self.white_reset_returned,self.final_cleanup_returned):_normal(v)
        _bytes_tuple(self.black_after_reset);_bytes_tuple(self.white_after_reset)
        for v in (self.black_rows,self.white_rows):
            if type(v) is not tuple or any(not isinstance(r,NameListRefreshRow) for r in v):raise ValueError('Ordered typed refresh rows required')

@dataclass(frozen=True)
class NameListRefreshPlan:
    complete:bool
    status:str
    entry:NameListsState
    state:NameListsState
    prospective_white:object=None
    prospective_black:object=None
    steps:tuple=()
    writes:tuple=()
    missing:str=''
    native_execution_verified:bool=False

def plan_name_list_refresh(state,o):
    if not isinstance(state,NameListsState) or not isinstance(o,NameListRefreshObservation):raise ValueError('Typed name list state/observation required')
    steps=[];writes=[];white=None;black=None
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def normal(v,label):
        steps.append(('normal_return',label))
        if v is not True:raise Missing(label)
    def result(complete,missing=''):
        accepted=NameListsState(white,black) if complete else state
        return NameListRefreshPlan(complete,'list_refresh_modeled' if complete else 'needs_observation',state,accepted,
            white,black,tuple(steps),tuple(writes),missing)
    try:
        normal(o.scratch_init_returned,'00404148 ANSI scratch initialization')
        normal(o.black_reset_returned,'context100 end/begin/erase span')
        black=need(o.black_after_reset,'observed black rows after reset; normal return alone is insufficient')
        normal(o.white_reset_returned,'contexte0 end/begin/erase span')
        white=need(o.white_after_reset,'observed white rows after reset; normal return alone is insufficient')
        for kind,field,offset,rows in (('black',0x3f0,0x100,o.black_rows),('white',0x3d4,0xe0,o.white_rows)):
            index=0
            while True:
                if index>=len(rows):raise Missing('fresh %s UI count at index%d'%(kind,index))
                row=rows[index]
                if row.index!=index:raise ValueError('Refresh row index/order mismatch')
                count=need(row.ui_count_dword,'fresh '+kind+' UI count')
                signed_count=count-(1<<32) if count&0x80000000 else count
                signed_index=index-(1<<32) if index&0x80000000 else index
                steps.append(('UI_count',kind,index,field,0x14,count))
                if signed_count<=signed_index:break
                steps.append(('UI_item',kind,index,field,0xc))
                normal(row.text_get_returned,kind+' Unicode item getter')
                normal(row.ansi_conversion_returned,'004073a0 Unicode-to-ANSI conversion')
                ansi=need(row.ansi_bytes,kind+' post-conversion ANSI bytes')
                normal(row.assignment_cleanup_returned,'005050e4 assignment and temporary cleanup')
                size=need(row.vector_size_dword,'00409f6c fresh size DWORD')
                capacity=need(row.vector_capacity_dword,'00409f94 separate fresh capacity DWORD')
                fast=size<capacity
                steps.append(('vector_insert',kind,index,offset,'00409fbc' if fast else '0040a01c',size,capacity,ansi))
                normal(row.insertion_returned,kind+(' fast insertion' if fast else ' reallocating insertion'))
                if fast:
                    end=need(row.fast_end_dword,kind+' fast insertion returned end EAX')
                    writes.append((kind,offset+0x14,end))
                # Own content projection only; native allocator/refcount and
                # insert-helper effects are not certified by these receipts.
                if kind=='black':black=black+(ansi,)
                else:white=white+(ansi,)
                index=(index+1)&0xffffffff
        normal(o.final_cleanup_returned,'004040f8 final ANSI scratch cleanup')
        return result(True)
    except Missing as e:return result(False,str(e))

def filter_refreshed_names(refresh,kind,o,*,stable_same_invocation=False,codec=None):
    """Explicit own stable-list bridge; preserve all source helper receipts.

    Uses actual supplied count/base observations; does not invent pointers,
    native codepage, equality flags or helper returns.
    """
    if not isinstance(refresh,NameListRefreshPlan) or not isinstance(o,NameFilterObservation):raise ValueError('Typed refresh and filter inputs required')
    if kind not in ('primary','secondary'):raise ValueError('Source filter kind required')
    if stable_same_invocation is not True:raise ValueError('Explicit own stable same-invocation list contract required')
    if not refresh.complete:raise ValueError('Incomplete refresh cannot bind accepted list')
    if type(codec) is not str:raise ValueError('Explicit own ANSI conversion codec required')
    content=refresh.state.white if kind=='primary' else refresh.state.black
    if o.input_copy_returned is not True:return plan_name_filter(kind,o)
    rows=[]
    for index,row in enumerate(o.iterations):
        if row.index!=index:raise ValueError('Filter iteration order mismatch')
        if row.count_begin_dword is None or (row.count_begin_dword!=0 and row.count_end_dword is None):
            rows.append(row);break
        if source_vector_count(row.count_begin_dword,row.count_end_dword)!=len(content):raise ValueError('Stable list count observation mismatch')
        if index>=len(content) or row.conversion_returned is not True:
            rows.append(row);break
        if index<len(content):
            text=content[index].decode(codec,errors='strict')
            if row.converted_text is not None and utf16_key(row.converted_text)!=utf16_key(text):raise ValueError('Converted slot text conflicts with explicit own codec')
            eq=row.equality
            if eq is not None and eq.use_owned_text_model:
                if eq.left_text is not None and (o.input_text is None or utf16_key(eq.left_text)!=utf16_key(o.input_text)):raise ValueError('Owned comparison input mismatch')
                if eq.right_text is not None and utf16_key(eq.right_text)!=utf16_key(text):raise ValueError('Owned comparison slot mismatch')
                eq=replace(eq,left_text=o.input_text,right_text=text)
            row=replace(row,converted_text=text,equality=eq)
        rows.append(row)
        probe=plan_name_filter(kind,replace(o,iterations=tuple(rows)))
        if probe.complete or probe.missing!='fresh vector count at index%d'%(index+1):return probe
    return plan_name_filter(kind,replace(o,iterations=tuple(rows)))
