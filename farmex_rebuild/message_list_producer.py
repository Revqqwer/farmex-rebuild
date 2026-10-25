"""0045c488 captured row producer; owned immutable projections, no native UI/heap."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from source_integer import SourceIntegerFrame,SourceIntegerObservation

@dataclass(frozen=True)
class MessageListRow:
    channel_bytes:bytes
    message_bytes:bytes
    delay_dword:int
    source_index:int

@dataclass(frozen=True)
class MessageListObservation:
    entry_reached:bool=False
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    texts:object=field(default_factory=dict)
    ansi_bytes:object=field(default_factory=dict)
    integer_inputs:object=field(default_factory=dict)
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit message-list post-prologue entry required')
        groups={k:dict(getattr(self,k)) for k in ('values','normal_returns','texts','ansi_bytes','integer_inputs')}
        if any(type(v) is not int or not 0<=v<=0xffffffff for v in groups['values'].values()):raise ValueError('Raw list producer DWORD required')
        if any(type(v) is not bool for v in groups['normal_returns'].values()):raise ValueError('Separate list helper normal receipts required')
        if any(type(v) is not str for v in groups['texts'].values()):raise ValueError('Captured Unicode cell text required')
        if any(type(v) is not bytes for v in groups['ansi_bytes'].values()):raise ValueError('Captured immutable ANSI bytes required')
        if any(not isinstance(v,SourceIntegerObservation) for v in groups['integer_inputs'].values()):raise ValueError('Typed integer child observations required')
        for key,value in groups.items():object.__setattr__(self,key,MappingProxyType(value))

@dataclass(frozen=True)
class MessageListPlan:
    complete:bool
    status:str
    cleared:bool=False
    rows:tuple=()
    stores:tuple=()
    calls:tuple=()
    conversions:tuple=()
    candidate:object=None
    needed:object=None
    next_address:object=None
    whole_function_verified:bool=False
    lexical_conversion_verified:bool=False
    codec_verified:bool=False
    native_execution_verified:bool=False

class _Wait(Exception):
    def __init__(self,kind,key):self.needed=(kind,key);super().__init__(key)

def _signed32(value):return value if value<0x80000000 else value-(1<<32)

def _plan(o,context,budget,integer,fast_end):
    rows=[];calls=[];stores=[];conversions=[];cleared=False;candidate=None
    def result(status,wait=None):
        return MessageListPlan(wait is None,status,cleared,tuple(rows),tuple(stores),tuple(calls),
            tuple(conversions),candidate,None if wait is None else wait.needed,0x45c70a if wait is None else None)
    def get(kind,key):
        group=getattr(o,{'value':'values','text':'texts','ansi':'ansi_bytes'}[kind])
        if key not in group:raise _Wait(kind,key)
        return group[key]
    def normal(key,target,args=()):
        calls.append((target,args,key))
        if o.normal_returns.get(key) is not True:raise _Wait('normal',key)
    def string_cell(prefix,role,cell):
        normal(prefix+role+'_init','00404a78')
        helper='0045f7f4' if cell is None else '0045f6e0'
        normal(prefix+role+'_get',helper,('form_field',0xb98,len(rows),cell))
        text=get('text',prefix+role)
        normal(prefix+role+'_ansi','004073a0',('captured_unicode',text))
        data=get('ansi',prefix+role)
        normal(prefix+role+'_unicode_cleanup','00505c64')
        return data
    try:
        if not o.entry_reached:raise _Wait('entry','0045c499')
        normal('clear_end_iterator','0045c740',(context,))
        normal('clear_begin_iterator','0045c71c',(context,))
        normal('clear_range','0045c764',('captured_iterators',context))
        cleared=True
        for index in range(budget+1):
            prefix='row%d.'%index
            normal(prefix+'count','VCL_Items_Count',('form_field',0xb98))
            if _signed32(get('value',prefix+'count_eax'))<=index:
                return result('source_list_end_reached')
            if index==budget:raise _Wait('budget','row_limit')
            channel=string_cell(prefix,'channel',None)
            message=string_cell(prefix,'message',0)
            normal(prefix+'delay_init','00404a78')
            normal(prefix+'delay_get','0045f6e0',('form_field',0xb98,index,1))
            text=get('text',prefix+'delay')
            child=integer(prefix+'delay_integer',text);conversions.append((index,child))
            if not child.complete:raise _Wait('integer',prefix+'delay_integer')
            normal(prefix+'parser_outer','0045ef80',(10,'captured_delay_text'))
            seconds=child.low_dword
            normal(prefix+'delay_unicode_cleanup','00505c64')
            normal(prefix+'record_channel_init','00404148')
            normal(prefix+'record_message_init','00404148')
            normal(prefix+'record_channel_assign','005050e4',('captured_channel',))
            normal(prefix+'record_message_assign','005050e4',('captured_message',))
            candidate=MessageListRow(channel,message,(seconds*1000)&0xffffffff,index)
            normal(prefix+'size','0045c814',(context,));size=get('value',prefix+'size_eax')
            normal(prefix+'capacity','0045c83c',(context,));capacity=get('value',prefix+'capacity_eax')
            if size<capacity:
                end=get('value',prefix+'end_dword')
                normal(prefix+'fast_append','0045c864',(candidate,1,end,context)) #Physical pushes.
                new_end=fast_end(prefix+'new_end_eax',(end+12)&0xffffffff)
                stores.append(((context+0x14)&0xffffffff,4,new_end))
            else:
                normal(prefix+'grow_end_iterator','0045c740',(context,))
                normal(prefix+'grow_insert','0045c8c8',('captured_end_iterator',candidate,context))
            # These are owned records passed to append, not observed native heap contents.
            rows.append(candidate)
            for role in ('record_message','record_channel','original_message','original_channel'):
                normal(prefix+role+'_cleanup','004040f8')
        raise AssertionError('Message list bounded loop invariant')
    except _Wait as wait:return result('needs_observation',wait)

class MessageListFrame:
    def __init__(self,*,context=0x569910,row_budget=64):
        if type(context) is not int or not 0<=context<=0xffffffff:raise ValueError('Raw producer context required')
        if type(row_budget) is not int or row_budget<1:raise ValueError('Positive own row budget required')
        self.context=context;self.budget=row_budget;self.observation=MessageListObservation()
        self.integers={};self.fast_returns={};self.final=None
    def extend_budget(self,new_budget):
        if type(new_budget) is not int or new_budget<=self.budget:raise ValueError('Larger explicit own row budget required')
        self.budget=new_budget
    def advance(self,incoming):
        if not isinstance(incoming,MessageListObservation):raise ValueError('Typed list producer observations required')
        if self.final is not None:return self.final
        def integer(key,text):
            if key not in self.integers:self.integers[key]=SourceIntegerFrame(text,10)
            return self.integers[key].advance(incoming.integer_inputs.get(key,SourceIntegerObservation()))
        def fast_end(key,expected):
            if key not in self.fast_returns:
                if incoming.values.get(key,expected)!=expected:raise ValueError('Fast append EAX contradicts source end+12')
                self.fast_returns[key]=expected
            return self.fast_returns[key]
        for _ in range(32768):
            plan=_plan(self.observation,self.context,self.budget,integer,fast_end)
            if plan.complete:self.final=plan;return plan
            kind,key=plan.needed
            if kind in ('integer','budget'):return plan
            if kind=='entry':
                if not incoming.entry_reached:return plan
                self.observation=replace(self.observation,entry_reached=True)
            elif kind=='normal':
                if incoming.normal_returns.get(key) is not True:return plan
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,key:True})
            else:
                group={'value':'values','text':'texts','ansi':'ansi_bytes'}[kind]
                values=getattr(incoming,group)
                if key not in values:return plan
                self.observation=replace(self.observation,**{group:{**getattr(self.observation,group),key:values[key]}})
        raise AssertionError('Message list capture budget exceeded')
