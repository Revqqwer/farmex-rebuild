"""004b1558 captured add-button normal path, without UI or game actions."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from source_integer import SourceIntegerFrame,SourceIntegerObservation
from message_list_add import MessageListAddFrame,MessageListAddObservation

@dataclass(frozen=True)
class MessageAddClickObservation:
    entry_reached:bool=False
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    texts:object=field(default_factory=dict)
    integer:object=None
    add:object=None
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit button post-prologue entry required')
        for group in ('values','normal_returns','texts'):
            data=dict(getattr(self,group))
            if group=='values' and any(type(v) is not int or not 0<=v<=0xffffffff for v in data.values()):raise ValueError('Raw button DWORD operands required')
            if group=='normal_returns' and any(type(v) is not bool for v in data.values()):raise ValueError('Separate helper normal receipts required')
            if group=='texts' and any(type(v) is not str for v in data.values()):raise ValueError('Captured Unicode text required')
            object.__setattr__(self,group,MappingProxyType(data))
        if {'integer','add'}&self.normal_returns.keys():raise ValueError('Use typed children and separate parent receipts')
        if self.integer is not None and not isinstance(self.integer,SourceIntegerObservation):raise ValueError('Typed source integer required')
        if self.add is not None and not isinstance(self.add,MessageListAddObservation):raise ValueError('Typed add child required')

@dataclass(frozen=True)
class MessageAddClickPlan:
    complete:bool
    calls:tuple=()
    integer:object=None
    add:object=None
    physical_pushes:object=None
    needed:object=None
    next_address:object=None
    whole_function_verified:bool=False
    codec_verified:bool=False
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class _Wait(Exception):
    def __init__(self,kind,key):self.needed=(kind,key);super().__init__(key)

class MessageAddClickFrame:
    def __init__(self):
        self.observation=MessageAddClickObservation();self.integer=None;self.add=None;self.final=None
    def _plan(self,incoming):
        o=self.observation;calls=[];integer=None;add=None;pushes=None
        def result(wait=None):return MessageAddClickPlan(wait is None,tuple(calls),integer,add,pushes,None if wait is None else wait.needed,0x4b168d if wait is None else None)
        def normal(key,target,args=()):
            calls.append((target,args,key))
            if o.normal_returns.get(key) is not True:raise _Wait('normal',key)
        def get(kind,key):
            group=o.values if kind=='value' else o.texts
            if key not in group:raise _Wait(kind,key)
            return group[key]
        try:
            if not o.entry_reached:raise _Wait('entry','004b156f')
            normal('delay_text_init','00404a78')
            normal('delay_text_get','VCL_Text_getter',('form_field',0xbb4))
            delay_text=get('text','delay')
            if self.integer is None:self.integer=SourceIntegerFrame(delay_text,10)
            calls.append(('0045ef80',(10,delay_text),'typed_integer'))
            integer=self.integer.advance(incoming.integer or SourceIntegerObservation())
            if not integer.complete:raise _Wait('integer',integer.needed)
            normal('integer_parent_return','0045ef80_parent_return')
            delay=integer.low_dword
            normal('message_text_init','00404a78')
            normal('message_text_get','VCL_Text_getter',('form_field',0xbb0))
            message_text=get('text','message')
            normal('message_ansi_convert','004073a0',(message_text,))
            message_handle=get('value','message_ansi_dword')
            normal('channel_text_init','00404a78')
            normal('channel_index_get','VCL_ComboBox_virtual_130',('form_field',0xbac))
            index=get('value','channel_index_eax')
            # Source saves the slot address before index getter, dereferences after it.
            strings=get('value','fresh_combo_strings_object_dword')
            normal('channel_item_get','VCL_Strings_virtual_0c',(strings,index))
            channel_text=get('text','channel')
            normal('channel_ansi_convert','004073a0',(channel_text,))
            channel_handle=get('value','channel_ansi_dword')
            pushes=(delay,message_handle,channel_handle,0x569910)
            calls.append(('0045ca20',pushes,'typed_add'))
            if self.add is None:self.add=MessageListAddFrame(channel_handle,message_handle)
            add=self.add.advance(incoming.add or MessageListAddObservation())
            if not add.complete:raise _Wait('add',add.needed)
            normal('add_parent_return','0045ca20_parent_return')
            for role,target in (('channel_ansi','004040f8'),('channel_unicode','00505c64'),('message_ansi','004040f8'),('message_unicode','00505c64'),('delay_unicode','00505c64')):
                normal(role+'_cleanup',target)
            return result()
        except _Wait as wait:return result(wait)
    def advance(self,incoming):
        if not isinstance(incoming,MessageAddClickObservation):raise ValueError('Typed add-button observation required')
        if self.final is not None:return self.final
        for _ in range(64):
            plan=self._plan(incoming)
            if plan.complete:self.final=plan;return plan
            kind,key=plan.needed
            if kind in ('integer','add'):return plan
            if kind=='entry':
                if not incoming.entry_reached:return plan
                self.observation=replace(self.observation,entry_reached=True)
            else:
                group={'normal':'normal_returns','value':'values','text':'texts'}[kind]
                data=getattr(incoming,group)
                if key not in data or (kind=='normal' and data[key] is not True):return plan
                self.observation=replace(self.observation,**{group:{**getattr(self.observation,group),key:data[key]}})
        raise AssertionError('Bounded add-button capture budget exceeded')
