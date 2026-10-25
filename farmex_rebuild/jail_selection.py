"""0046ce04 checked-window UI -> own vector projection; no VCL/native calls."""
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from jail_protection import JailObservation

@dataclass(frozen=True)
class JailSelectionObservation:
    source: JailObservation = field(default_factory=JailObservation)
    ansi_bytes: object = field(default_factory=dict)
    after_reset: object = None
    def __post_init__(self):
        if not isinstance(self.source,JailObservation):raise ValueError('Typed selection source required')
        b=dict(self.ansi_bytes)
        if any(type(k) is not str or type(v) is not bytes for k,v in b.items()):raise ValueError('Captured ANSI bytes required')
        if self.after_reset is not None and (type(self.after_reset) is not tuple or any(type(v) is not bytes for v in self.after_reset)):
            raise ValueError('Explicit immutable rows after reset required')
        object.__setattr__(self,'ansi_bytes',MappingProxyType(b))

@dataclass(frozen=True)
class JailSelectionPlan:
    complete: bool
    rows: tuple
    calls: tuple = ()
    stores: tuple = ()
    needed: object = None
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False
    whole_function_verified: bool = False

class _Wait(Exception):
    def __init__(self,kind,label):self.needed=(kind,label)

def plan_jail_selection(o,*,initial_rows=(),context=0x5690f8):
    if not isinstance(o,JailSelectionObservation) or type(initial_rows) is not tuple or any(type(v) is not bytes for v in initial_rows):
        raise ValueError('Typed selection and own initial rows required')
    if type(context) is not int or not 0<=context<1<<32:raise ValueError('Raw context required')
    rows=initial_rows;calls=[];stores=[];vector=(context+0xc0)&0xffffffff
    def result(error=None):return JailSelectionPlan(error is None,rows,tuple(calls),tuple(stores),None if error is None else error.needed)
    def value(label):
        if label not in o.source.values:raise _Wait('value',label)
        return o.source.values[label]
    def normal(label,helper,pushes=()):
        calls.append((helper,pushes,label))
        if o.source.normal_returns.get(label) is not True:raise _Wait('normal',label)
    try:
        if not o.source.entry_reached:raise _Wait('entry','0046ce04')
        normal('prologue','source_SEH_prologue_span')
        normal('scratch_init','00404148',('scratch_ansi',))
        normal('reset_end','00409e98',(vector,'end_iterator'))
        normal('reset_begin','00409e74',(vector,'begin_iterator'))
        normal('reset_erase','00409ebc',(vector,'result_iterator','begin_end_copies'))
        if o.after_reset is None:raise _Wait('reset','after_reset')
        rows=o.after_reset
        index=0
        while True:
            p='row%d.'%index
            normal(p+'count','TListItems.GetCount',('form_3d4_items_2cc',))
            count=value(p+'count_eax');signed_count=count-(1<<32) if count&0x80000000 else count
            signed_index=index-(1<<32) if index&0x80000000 else index
            if signed_count<=signed_index:break
            normal(p+'item','TListItems.GetItem',('form_3d4_items_2cc',index))
            normal(p+'checked','TListItem.GetChecked',('captured_item',))
            if value(p+'checked_eax')&255:
                normal(p+'text_prepare','00404a78',('unicode_temp',))
                normal(p+'text_get','0045f7f4',(index,'form_3d4','unicode_result'))
                normal(p+'ansi_convert','004073a0',('unicode_temp','ansi_temp'))
                if p+'title' not in o.ansi_bytes:raise _Wait('bytes',p+'title')
                title=o.ansi_bytes[p+'title']
                normal(p+'scratch_assign','005050e4',('ansi_temp','scratch_ansi'))
                normal(p+'ansi_cleanup','004040f8',(2,'ansi_temp'))
                normal(p+'unicode_cleanup','00505c64',(2,'unicode_temp'))
                normal(p+'size','00409f6c',(vector,));size=value(p+'size_eax')
                normal(p+'capacity','00409f94',(vector,));capacity=value(p+'capacity_eax')
                if size<capacity:
                    end=value(p+'end_pointer')
                    normal(p+'insert','00409fbc',('scratch_ansi',1,end,vector))
                    returned=value(p+'insert_eax')
                    stores.append(((vector+0x14)&0xffffffff,4,returned))
                else:
                    normal(p+'slow_end','00409e98',(vector,'end_iterator'))
                    normal(p+'insert','0040a01c',('scratch_ansi','end_iterator_copy',vector,'result_iterator'))
                rows=rows+(title,)
            index=(index+1)&0xffffffff
        normal('final_cleanup','004040f8',(2,'scratch_ansi'))
        normal('epilogue','source_FS_restore_stack_return_span')
        return result()
    except _Wait as e:return result(e)

class JailSelectionFrame:
    def __init__(self,*,initial_rows=(),context=0x5690f8):
        self.initial_rows=initial_rows;self.context=context
        self.observation=JailSelectionObservation();self.final=None
        plan_jail_selection(self.observation,initial_rows=initial_rows,context=context)
    def advance(self,o):
        if not isinstance(o,JailSelectionObservation):raise ValueError('Typed selection observation required')
        if self.final is not None:return self.final
        while True:
            p=plan_jail_selection(self.observation,initial_rows=self.initial_rows,context=self.context)
            if p.complete:self.final=p;return p
            kind,label=p.needed;source=self.observation.source
            if kind=='entry':
                if not o.source.entry_reached:return p
                source=replace(source,entry_reached=True)
            elif kind=='normal':
                if o.source.normal_returns.get(label) is not True:return p
                source=replace(source,normal_returns={**source.normal_returns,label:True})
            elif kind=='value':
                if label not in o.source.values:return p
                source=replace(source,values={**source.values,label:o.source.values[label]})
            elif kind=='bytes':
                if label not in o.ansi_bytes:return p
                self.observation=replace(self.observation,ansi_bytes={**self.observation.ansi_bytes,label:o.ansi_bytes[label]});continue
            elif kind=='reset':
                if o.after_reset is None:return p
                self.observation=replace(self.observation,after_reset=o.after_reset);continue
            else:raise AssertionError('Unknown selection observation')
            self.observation=replace(self.observation,source=source)
