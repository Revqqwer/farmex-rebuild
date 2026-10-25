"""004ca220 bounded own PM-request wire/queue frame; never sends to a game.

Fresh WORD/check/copy/add lengths and helper returns remain independent.
The100-byte nominal array is followed by a dead4-byte pointer, then the index.
Counter-aliasing copies and uninitialized enqueue tails stay unresolved.
"""
from dataclasses import dataclass,field
from types import MappingProxyType
from action_queue import QueueState
from direct_chat_packets import QueueAttempt
from event_packets import EventEnqueueFrame

NOMINAL_BUFFER_BYTES=100
COUNTER_OFFSET=104


@dataclass(frozen=True)
class PrivateChatObservation:
    entry_reached: bool=False
    values: object=field(default_factory=dict)
    normal_returns: object=field(default_factory=dict)
    data_bytes: object=None
    attempt: QueueAttempt=field(default_factory=QueueAttempt)
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit helper entry required')
        values=dict(self.values);returns=dict(self.normal_returns)
        for key,value in values.items():
            bits=16 if key=='length_word' else 32
            if type(value) is not int or not 0<=value<1<<bits:raise ValueError('Raw helper operand required')
        if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate helper normal-return receipts required')
        if self.data_bytes is not None and type(self.data_bytes) is not bytes:raise ValueError('Immutable captured name bytes required')
        if not isinstance(self.attempt,QueueAttempt):raise ValueError('Own queue attempt required')
        object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(returns))


@dataclass(frozen=True)
class PrivateChatPlan:
    complete: bool
    status: str
    queue: QueueState
    calls: tuple=()
    initialized_bytes: bytes=b''
    enqueue_length: int=0
    payload: object=None
    c_string_pointer: object=None
    needed: object=None
    native_execution_verified: bool=False
    delivery_verified: bool=False
    live_compatibility_verified: bool=False


class _Wait(Exception):
    def __init__(self,kind,key):self.needed=(kind,key)


class PrivateChatRequestFrame:
    def __init__(self,name_argument_dword,queue=None,*,context=0x561ef8):
        for v in (name_argument_dword,context):
            if type(v) is not int or not 0<=v<1<<32:raise ValueError('Raw private-chat argument/context required')
        self.argument=name_argument_dword;self.context=context
        self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own queue required')
        self.entry=False;self.values={};self.normals=set();self.calls=[];self.emitted=set()
        self.buffer=b'';self.index=0;self.data=None;self.pointer=None;self.payload=None
        self.enqueue=None;self.final=None
    def _result(self,status,needed=None):
        return PrivateChatPlan(needed is None,status,self.queue,tuple(self.calls),self.buffer,
            self.index,self.payload,self.pointer,needed)
    def advance(self,o):
        if not isinstance(o,PrivateChatObservation):raise ValueError('Typed private-chat observations required')
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
                if not o.entry_reached:raise _Wait('entry','004ca233')
                self.entry=True
            normal('argument_copy','00504ef8',('parameter_0c',))
            pointer=value('fresh_name_parameter_dword')
            self.pointer=pointer if pointer else 0x5479b5
            normal('string_factory','00403808')
            normal('string_copy','0040382c')
            normal('initial_string_cleanup','00403860')
            normal('string_assign','004038e4',(self.pointer,))
            normal('opcode_append','004c7623',(0x35,));emit('opcode',b'\x35')
            normal('subopcode_append','004c7623',(1,));emit('subopcode',b'\x01')
            word=value('length_word')
            normal('word_append','004c7666',(word,));emit('word',word.to_bytes(2,'little'))
            if value('string_check_length_dword'):
                copied=value('copy_length_dword')
                if 4+copied>COUNTER_OFFSET:raise _Wait('scope','source_stack_alias_copy')
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
            normal('argument_cleanup','004040f8')
            self.final=self._result('own_private_chat_request_projected')
            return self.final
        except _Wait as error:
            return self._result('needs_observation',error.needed)
