"""Pinned VCL Clear/DeleteSelected normal paths; no window or native calls."""
from dataclasses import dataclass
from source_unicode import utf16_key

def _rows(v):
    if type(v) is not tuple:raise ValueError('Immutable Unicode rows required')
    for s in v:utf16_key(s)
def _raw(v,bits):
    if v is not None and (type(v) is not int or not 0<=v<1<<bits):raise ValueError('Raw unsigned value required')
def _normal(v):
    if v is not None and type(v) is not bool:raise ValueError('Explicit normal-return receipt required')

@dataclass(frozen=True)
class VclDeleteSample:
    index_dword:int
    selected_returned:object=None
    selected_al:object=None
    delete_returned:object=None
    rows_after_delete:object=None
    def __post_init__(self):
        _raw(self.index_dword,32)
        if self.index_dword is None:raise ValueError('Explicit call index required')
        _raw(self.selected_al,8)
        _normal(self.selected_returned);_normal(self.delete_returned)
        if self.rows_after_delete is not None:_rows(self.rows_after_delete)

@dataclass(frozen=True)
class VclMutationObservation:
    multi_select_byte:object=None
    count_returned:object=None
    count_dword:object=None
    first_index_returned:object=None
    first_index_dword:object=None
    second_index_returned:object=None
    second_index_dword:object=None
    samples:tuple=()
    clear_returned:object=None
    rows_after_clear:object=None
    def __post_init__(self):
        _raw(self.multi_select_byte,8)
        for v in (self.count_dword,self.first_index_dword,self.second_index_dword):_raw(v,32)
        for v in (self.count_returned,self.first_index_returned,self.second_index_returned,self.clear_returned):_normal(v)
        if type(self.samples) is not tuple or any(not isinstance(v,VclDeleteSample) for v in self.samples):
            raise ValueError('Ordered typed call samples required')
        if self.rows_after_clear is not None:_rows(self.rows_after_clear)

@dataclass(frozen=True)
class VclMutationPlan:
    complete:bool
    action:str
    entry:tuple
    state:tuple
    prospective:tuple
    delete_indices:tuple
    steps:tuple
    missing:str=''
    native_execution_verified:bool=False

def plan_vcl_mutation(action,rows,o,*,iteration_budget=512):
    if action not in ('clear','remove') or not isinstance(o,VclMutationObservation):raise ValueError('Known action/typed observations required')
    _rows(rows)
    if type(iteration_budget) is not int or iteration_budget<1:raise ValueError('Positive own iteration budget required')
    prospective=rows;steps=[];indices=[];cursor=0
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def normal(v,label):
        steps.append(('normal_return',label))
        if v is not True:raise Missing(label)
    def result(ok,missing=''):
        return VclMutationPlan(ok,action,rows,prospective if ok else rows,prospective,tuple(indices),tuple(steps),missing)
    def sample(index):
        nonlocal cursor
        if cursor>=iteration_budget:raise Missing('own iteration budget; source loop not complete')
        if cursor>=len(o.samples):raise Missing('fresh ordered selection/delete sample')
        s=o.samples[cursor];cursor+=1
        if s.index_dword!=index:raise ValueError('Reached sample index differs from source call')
        return s
    def delete(index,s):
        nonlocal prospective
        steps.append(('Items_virtual',0x4c,index));indices.append(index)
        normal(s.delete_returned,'Items.Delete normal return')
        prospective=need(s.rows_after_delete,'post-delete Unicode rows')
    try:
        if action=='clear':
            steps.append(('Items_virtual',0x48))
            normal(o.clear_returned,'Items.Clear normal return')
            prospective=need(o.rows_after_clear,'post-clear Unicode rows')
            return result(True)
        multi=need(o.multi_select_byte,'control+2a0 BYTE')
        if multi==0:
            steps.append(('control_virtual',0x130,1))
            normal(o.first_index_returned,'first ItemIndex getter')
            first=need(o.first_index_dword,'first ItemIndex DWORD')
            if first==0xffffffff:return result(True)
            steps.append(('control_virtual',0x130,2))
            normal(o.second_index_returned,'second fresh ItemIndex getter')
            index=need(o.second_index_dword,'second ItemIndex DWORD')
            # No second -1/bounds guard in the source caller.
            delete(index,sample(index))
            return result(True)
        steps.append(('Items_virtual',0x14))
        normal(o.count_returned,'Items.Count normal return')
        index=(need(o.count_dword,'Items.Count DWORD')-1)&0xffffffff
        if index&0x80000000:return result(True)
        while True:
            steps.append(('GetSelected',0x50d3ddf4,index))
            s=sample(index)
            normal(s.selected_returned,'GetSelected normal return')
            if need(s.selected_al,'GetSelected AL')!=0:delete(index,s)
            index=(index-1)&0xffffffff
            if index==0xffffffff:return result(True)
    except Missing as error:return result(False,str(error))
