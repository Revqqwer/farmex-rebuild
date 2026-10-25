"""0045c1f8 channel branch/call plans; native strings/serializer remain opaque."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from source_message_cycle import SourceMessageCycleFrame,SourceMessageCycleObservation,_raw

CHANNELS=(('all',b'All Chat',0),('party',b'Party',2),('clan',b'Clan',3),
          ('shout',b'Shout',1),('merchant',b'Merchant',4),('noah',b'Noah Knight',0x22))

@dataclass(frozen=True)
class MessageChannelObservation:
    entry_reached:bool=False
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit channel post-prologue entry required')
        values=dict(self.values);normals=dict(self.normal_returns)
        for value in values.values():
            _raw(value)
            if value is None:raise ValueError('Explicit raw comparison/argument required')
        if any(type(v) is not bool for v in normals.values()):raise ValueError('Separate channel helper normal receipts required')
        object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(normals))

@dataclass(frozen=True)
class MessageChannelPlan:
    complete:bool
    status:str
    source_arguments:tuple
    calls:tuple=()
    channel_key:object=None
    channel_id:object=None
    serializer_physical_pushes:tuple=()
    needed:object=None
    next_address:object=None
    whole_function_verified:bool=False
    string_equality_verified:bool=False
    native_execution_verified:bool=False
    delivery_verified:bool=False

class _Wait(Exception):
    def __init__(self,kind,key):self.needed=(kind,key);super().__init__(key)

def _plan(o,args):
    calls=[];selected_key=selected_id=None;pushes=()
    def result(status,wait=None):
        return MessageChannelPlan(wait is None,status,args,tuple(calls),selected_key,selected_id,pushes,
            None if wait is None else wait.needed,0x45c479 if wait is None else None)
    def normal(key,target,arguments=()):
        calls.append((target,arguments,key))
        if o.normal_returns.get(key) is not True:raise _Wait('normal',key)
    def value(key):
        if key not in o.values:raise _Wait('value',key)
        return o.values[key]
    try:
        if not o.entry_reached:raise _Wait('entry','0045c208')
        normal('message_argument_copy','00504ef8',('parameter_10',))
        normal('channel_argument_copy','00504ef8',('parameter_c',))
        for key,literal,identifier in CHANNELS:
            normal(key+'_literal','004040bc',(literal,))
            normal(key+'_compare','00505134',('parameter_c',literal))
            eax=value(key+'_compare_eax')
            normal(key+'_literal_cleanup','004040f8',(key+'_temporary',2))
            if eax&255:
                selected_key=key;selected_id=identifier
                break
        if selected_key is not None:
            # Stack parameter+10 is read after opaque managed operations; its
            # current DWORD is a separate capture from the caller input handle.
            message=value('fresh_message_argument_dword')
            pushes=(message,selected_id,0x561ef8)
            normal('serializer','004c9b74',pushes)
        normal('channel_argument_cleanup','004040f8',('parameter_c',2))
        normal('message_argument_cleanup','004040f8',('parameter_10',2))
        return result('serializer_returned' if selected_key is not None else 'no_channel_match')
    except _Wait as wait:return result('needs_observation',wait)

class MessageChannelFrame:
    def __init__(self,channel_argument,message_argument,*,source_context=0x569910):
        for value in (channel_argument,message_argument,source_context):
            _raw(value)
            if value is None:raise ValueError('Explicit source arguments required')
        self.arguments=(source_context,channel_argument,message_argument)
        self.observation=MessageChannelObservation();self.final=None
    def advance(self,incoming):
        if not isinstance(incoming,MessageChannelObservation):raise ValueError('Typed channel observations required')
        if self.final is not None:return self.final
        for _ in range(48):
            plan=_plan(self.observation,self.arguments)
            if plan.complete:self.final=plan;return plan
            kind,key=plan.needed
            if kind=='entry':
                if not incoming.entry_reached:return plan
                self.observation=replace(self.observation,entry_reached=True)
            elif kind=='normal':
                if incoming.normal_returns.get(key) is not True:return plan
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,key:True})
            else:
                if key not in incoming.values:return plan
                self.observation=replace(self.observation,values={**self.observation.values,key:incoming.values[key]})
        raise AssertionError('Channel reached capture budget exceeded')

@dataclass(frozen=True)
class ChannelMessageCyclePlan:
    complete:bool
    cycle:object
    channel:object=None
    needed:object=None
    native_execution_verified:bool=False
    delivery_verified:bool=False

class ChannelMessageCycleFrame:
    """Source field0 -> channel, field4 -> message; no actual send/queue I/O."""
    def __init__(self,*,context=0x569910):
        self.cycle=SourceMessageCycleFrame(context=context);self.channel=None;self.channel_result=None;self.parent=False
    def advance(self,cycle,channel=None,*,channel_parent_returned=None):
        if not isinstance(cycle,SourceMessageCycleObservation):raise ValueError('Typed source cycle required')
        if 'message_helper' in cycle.normal_returns:raise ValueError('Typed channel child owns helper parent-return binding')
        if channel is not None and not isinstance(channel,MessageChannelObservation):raise ValueError('Typed channel child required')
        if channel_parent_returned is not None and type(channel_parent_returned) is not bool:raise ValueError('Separate channel parent normal receipt required')
        def bound():return replace(cycle,normal_returns={**cycle.normal_returns,'message_helper':True}) if self.parent else cycle
        plan=self.cycle.advance(bound())
        if plan.needed==('normal','message_helper'):
            if self.channel is None:
                field4,field0,context=plan.helper_pushes
                self.channel=MessageChannelFrame(field0,field4,source_context=context)
            self.channel_result=self.channel.advance(channel or MessageChannelObservation())
            if not self.channel_result.complete:
                return ChannelMessageCyclePlan(False,plan,self.channel_result,('channel',self.channel_result.needed))
            if channel_parent_returned is not True:
                return ChannelMessageCyclePlan(False,plan,self.channel_result,'channel_parent_returned')
            self.parent=True;plan=self.cycle.advance(bound())
        return ChannelMessageCyclePlan(plan.complete,plan,self.channel_result,plan.needed)
