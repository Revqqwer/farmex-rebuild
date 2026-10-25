"""0045ca20 normal list-add plan; captured VCL effects, no native/UI mutation."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from message_list_producer import MessageListFrame,MessageListObservation

LIST_PATH='frmMain/MainTab/sheetFlood/grpFlood/lwFlooding'

@dataclass(frozen=True)
class MessageListAddObservation:
    entry_reached:bool=False
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    texts:object=field(default_factory=dict)
    producer:object=None
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit add post-prologue entry required')
        for group in ('values','normal_returns','texts'):
            data=dict(getattr(self,group))
            if group=='values' and any(type(v) is not int or not 0<=v<=0xffffffff for v in data.values()):raise ValueError('Raw add DWORD operands required')
            if group=='normal_returns' and any(type(v) is not bool for v in data.values()):raise ValueError('Separate helper normal receipts required')
            if group=='texts' and any(type(v) is not str for v in data.values()):raise ValueError('Captured converted Unicode text required')
            object.__setattr__(self,group,MappingProxyType(data))
        if 'producer' in self.normal_returns:raise ValueError('Use typed producer child and separate parent return')
        if self.producer is not None and not isinstance(self.producer,MessageListObservation):raise ValueError('Typed list producer child required')

@dataclass(frozen=True)
class MessageListAddPlan:
    complete:bool
    status:str
    calls:tuple=()
    ui_intents:tuple=()
    producer:object=None
    needed:object=None
    next_address:object=None
    whole_function_verified:bool=False
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class _Wait(Exception):
    def __init__(self,kind,key):self.needed=(kind,key);super().__init__(key)

class MessageListAddFrame:
    """Own projection only. The child re-reads captured source UI independently."""
    def __init__(self,channel_argument,message_argument,*,context=0x569910):
        if any(type(v) is not int or not 0<=v<=0xffffffff for v in (channel_argument,message_argument,context)):raise ValueError('Raw source add arguments required')
        self.channel=channel_argument;self.message=message_argument;self.context=context
        self.observation=MessageListAddObservation();self.child=MessageListFrame(context=context);self.final=None
    def _plan(self,incoming):
        o=self.observation;calls=[];intents=[];producer=None;accepted=None
        def result(status,wait=None):
            boundary=(0x45cb9c if accepted else 0x45ca93) if wait is None else None
            return MessageListAddPlan(wait is None,status,tuple(calls),tuple(intents),producer,None if wait is None else wait.needed,boundary)
        def normal(key,target,args=()):
            calls.append((target,args,key))
            if o.normal_returns.get(key) is not True:raise _Wait('normal',key)
        def value(key):
            if key not in o.values:raise _Wait('value',key)
            return o.values[key]
        def text(key):
            if key not in o.texts:raise _Wait('text',key)
            return o.texts[key]
        try:
            if not o.entry_reached:raise _Wait('entry','0045ca30')
            normal('message_argument_copy','00504ef8',('stack+10',self.message))
            normal('channel_argument_copy','00504ef8',('stack+c',self.channel))
            delay=value('post_copy_delay_dword')
            signed_delay=delay if delay<0x80000000 else delay-(1<<32)
            accepted=signed_delay>=5
            if accepted:
                normal('item_add','VCL_Items_Add',(LIST_PATH,))
                item=value('created_item_eax');intents.append(('add_item',LIST_PATH,item))
                normal('channel_to_unicode','00403d84',('copied_channel_argument',))
                channel=text('converted_channel')
                normal('caption_set','VCL_Item_SetCaption',(item,channel));intents.append(('caption',item,channel))
                normal('channel_unicode_cleanup','00505c64')
                normal('message_to_unicode','00403d84',('copied_message_argument',))
                message=text('converted_message')
                normal('message_subitem_append','VCL_SubItems_virtual_3c',(item,message));intents.append(('append_subitem',item,message))
                normal('message_unicode_cleanup','00505c64')
                # Formatting is a captured native helper result, not str(delay).
                normal('delay_to_unicode','00407360',(delay,));delay_text=text('converted_delay')
                normal('delay_subitem_append','VCL_SubItems_virtual_3c',(item,delay_text));intents.append(('append_subitem',item,delay_text))
                normal('delay_unicode_cleanup','00505c64')
                calls.append(('0045c488',(self.context,),'typed_producer'))
                producer=self.child.advance(incoming.producer or MessageListObservation())
                if not producer.complete:raise _Wait('producer',producer.needed)
                normal('producer_parent_return','0045c488_parent_return')
            normal('channel_argument_cleanup','004040f8',('stack+c',))
            normal('message_argument_cleanup','004040f8',('stack+10',))
            return result('row_added_and_recompiled' if accepted else 'delay_rejected')
        except _Wait as wait:return result('needs_observation',wait)
    def advance(self,incoming):
        if not isinstance(incoming,MessageListAddObservation):raise ValueError('Typed add observation required')
        if self.final is not None:return self.final
        for _ in range(64):
            plan=self._plan(incoming)
            if plan.complete:self.final=plan;return plan
            kind,key=plan.needed
            if kind=='producer':return plan
            if kind=='entry':
                if not incoming.entry_reached:return plan
                self.observation=replace(self.observation,entry_reached=True)
            else:
                group={'normal':'normal_returns','value':'values','text':'texts'}[kind]
                source=getattr(incoming,group)
                if key not in source or (kind=='normal' and source[key] is not True):return plan
                self.observation=replace(self.observation,**{group:{**getattr(self.observation,group),key:source[key]}})
        raise AssertionError('Bounded list-add capture budget exceeded')
