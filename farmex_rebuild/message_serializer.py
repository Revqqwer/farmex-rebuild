"""004c9b74 bounded owned wire/queue replay; no native reads, writes or sends.

Fresh local string length reads remain separate. The four bytes after the
nominal512-byte array are a dead pointer local; counter-aliasing copies and
uninitialized enqueue tails remain unresolved.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState
from direct_chat_packets import QueueAttempt
from event_packets import EventEnqueueFrame
from message_channels import MessageChannelObservation,ChannelMessageCycleFrame
from source_message_cycle import SourceMessageCycleObservation

WIRE_MODES={0:1,1:5,2:3,3:6,4:14,5:15,7:7,8:8,9:9,10:10,11:11,12:12,
            13:13,14:14,15:15,16:16,17:17,34:34}
NOMINAL_PACKET_BYTES=512
COUNTER_OFFSET=516

@dataclass(frozen=True)
class MessageSerializerObservation:
    entry_reached:bool=False
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    data_bytes:object=None
    attempt:QueueAttempt=field(default_factory=QueueAttempt)
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit serializer post-prologue entry required')
        values=dict(self.values);normals=dict(self.normal_returns)
        for key,value in values.items():
            bits=16 if key=='length_word' else 32
            if type(value) is not int or not 0<=value<1<<bits:raise ValueError('Raw serializer operand required')
        if any(type(v) is not bool for v in normals.values()):raise ValueError('Separate serializer helper normals required')
        if self.data_bytes is not None and type(self.data_bytes) is not bytes:raise ValueError('Immutable captured string bytes required')
        if not isinstance(self.attempt,QueueAttempt):raise ValueError('Typed own enqueue attempt required')
        object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(normals))

@dataclass(frozen=True)
class MessageSerializerPlan:
    complete:bool
    status:str
    queue:QueueState
    calls:tuple=()
    initialized_bytes:bytes=b''
    enqueue_length:int=0
    payload:object=None
    wire_mode:object=None
    c_string_pointer:object=None
    needed:object=None
    whole_function_verified:bool=False
    native_execution_verified:bool=False
    delivery_verified:bool=False
    live_compatibility_verified:bool=False

class _Wait(Exception):
    def __init__(self,kind,key):self.needed=(kind,key);super().__init__(key)

class MessageSerializerFrame:
    def __init__(self,mode,message_argument,queue=None,*,context=0x561ef8):
        for value in (mode,message_argument,context):
            if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw serializer arguments required')
        self.mode=mode;self.message_argument=message_argument;self.context=context
        self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own queue required')
        self.entry=False;self.values={};self.normals=set();self.calls=[];self.emitted=set()
        self.buffer=b'';self.index=0;self.data=None;self.pointer=None;self.payload=None
        self.enqueue=None;self.final=None
    def _result(self,status,needed=None):
        return MessageSerializerPlan(needed is None,status,self.queue,tuple(self.calls),self.buffer,
            self.index,self.payload,WIRE_MODES.get(self.mode),self.pointer,needed)
    def advance(self,o):
        if not isinstance(o,MessageSerializerObservation):raise ValueError('Typed serializer observations required')
        if self.final is not None:return self.final
        def normal(key,target,args=()):
            if key not in self.normals:
                if not any(c[2]==key for c in self.calls):self.calls.append((target,args,key))
                if o.normal_returns.get(key) is not True:raise _Wait('normal',key)
                self.normals.add(key)
        def value(key):
            if key not in self.values:
                if key not in o.values:raise _Wait('value',key)
                self.values[key]=o.values[key]
            return self.values[key]
        def emit(key,data):
            if key not in self.emitted:
                self.buffer+=data;self.index+=len(data);self.emitted.add(key)
        try:
            if not self.entry:
                if not o.entry_reached:raise _Wait('entry','004c9b87')
                self.entry=True
            normal('argument_copy','00504ef8',('parameter_10',))
            parameter=value('fresh_message_parameter_dword')
            self.pointer=parameter if parameter else 0x5479b4
            normal('string_factory','00403808')
            normal('string_copy','0040382c')
            normal('initial_string_cleanup','00403860')
            normal('string_assign','004038e4',(self.pointer,))
            normal('opcode_append','004c7623',(0x10,));emit('opcode',b'\x10')
            if self.mode in WIRE_MODES:
                wire=WIRE_MODES[self.mode]
                normal('wire_append','004c7623',(wire,));emit('wire',bytes([wire]))
                word=value('length_word')
                normal('word_append','004c7666',(word,));emit('word',word.to_bytes(2,'little'))
                check=value('string_check_length_dword')
                if check:
                    copied=value('copy_length_dword')
                    if 4+copied>COUNTER_OFFSET:
                        raise _Wait('scope','source_stack_alias_copy')
                    normal('string_data','00403b74',('stack_string',))
                    data_pointer=value('string_data_eax')
                    if self.data is None:
                        if copied==0:self.data=b''
                        else:
                            if o.data_bytes is None or len(o.data_bytes)<copied:raise _Wait('bytes','string_copy_data')
                            self.data=o.data_bytes[:copied]
                    normal('string_memcpy','source_memcpy',(4,data_pointer,copied))
                    if 'string_copy' not in self.emitted:
                        self.buffer+=self.data;self.emitted.add('string_copy')
                    added=value('add_length_dword')
                    if 'string_index' not in self.emitted:
                        self.index=(4+added)&0xffffffff;self.emitted.add('string_index')
                normal('string_append_parent','004c76cc')
            if self.index>len(self.buffer):raise _Wait('scope','uninitialized_enqueue_tail')
            self.payload=self.buffer[:self.index]
            if self.enqueue is None:
                self.calls.append(('004c7710',(self.context,self.index,0),'enqueue'))
                self.enqueue=EventEnqueueFrame(self.payload,0,self.queue)
            child=self.enqueue.advance(o.attempt);self.queue=child.queue
            if not child.complete:raise _Wait('enqueue',str(child.needed))
            normal('final_string_cleanup','00403860')
            normal('argument_cleanup','004040f8',('parameter_10',2))
            self.final=self._result('own_queue_helper_returned');return self.final
        except _Wait as wait:return self._result('needs_observation',wait.needed)

@dataclass(frozen=True)
class SerializedChannelCyclePlan:
    complete:bool
    channel_cycle:object
    serializer:object
    queue:QueueState
    needed:object=None
    native_execution_verified:bool=False
    delivery_verified:bool=False

class SerializedChannelCycleFrame:
    """Own cycle -> channel -> serializer -> queue, with separate parent normals."""
    def __init__(self,queue=None,*,context=0x569910):
        self.cycle=ChannelMessageCycleFrame(context=context)
        self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own initial queue required')
        self.serializer=None;self.result=None;self.parent=False
    def advance(self,cycle,channel=None,serializer=None,*,channel_parent_returned=None,serializer_parent_returned=None):
        if not isinstance(cycle,SourceMessageCycleObservation):raise ValueError('Typed cycle required')
        if channel is not None and not isinstance(channel,MessageChannelObservation):raise ValueError('Typed channel required')
        if channel is not None and 'serializer' in channel.normal_returns:raise ValueError('Typed serializer owns its parent-return binding')
        if serializer is not None and not isinstance(serializer,MessageSerializerObservation):raise ValueError('Typed serializer child required')
        if serializer_parent_returned is not None and type(serializer_parent_returned) is not bool:raise ValueError('Separate serializer parent normal required')
        def bound():
            current=channel or MessageChannelObservation()
            return replace(current,normal_returns={**current.normal_returns,'serializer':True}) if self.parent else current
        plan=self.cycle.advance(cycle,bound(),channel_parent_returned=channel_parent_returned)
        if plan.needed==('channel',('normal','serializer')):
            if self.serializer is None:
                message,mode,context=plan.channel.serializer_physical_pushes
                self.serializer=MessageSerializerFrame(mode,message,self.queue,context=context)
            self.result=self.serializer.advance(serializer or MessageSerializerObservation());self.queue=self.result.queue
            if not self.result.complete:return SerializedChannelCyclePlan(False,plan,self.result,self.queue,('serializer',self.result.needed))
            if serializer_parent_returned is not True:return SerializedChannelCyclePlan(False,plan,self.result,self.queue,'serializer_parent_returned')
            self.parent=True;plan=self.cycle.advance(cycle,bound(),channel_parent_returned=channel_parent_returned)
        return SerializedChannelCyclePlan(plan.complete,plan,self.result,self.queue,plan.needed)
