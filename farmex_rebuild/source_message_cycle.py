"""0045cce8 ordered fresh operands and bounded46f1b8 gate; inert plans only.

The channel/text helper remains an opaque normal-return boundary. Raw vector
addresses are calculated but never dereferenced; no messages are sent.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType

def _raw(value,bits=32):
    if value is not None and (type(value) is not int or not 0<=value<1<<bits):raise ValueError('Raw message-cycle operand required')

def _signed(value,bits):return value if value<1<<(bits-1) else value-(1<<bits)
def _divide12(value):
    signed=_signed(value&0xffffffff,32)
    return -(abs(signed)//12) if signed<0 else signed//12

@dataclass(frozen=True)
class SourceMessageCycleObservation:
    entry_reached:bool=False
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit cycle post-prologue entry required')
        values=dict(self.values);normals=dict(self.normal_returns)
        for value in values.values():
            _raw(value)
            if value is None:raise ValueError('Explicit reached cycle operand required')
        if any(type(v) is not bool for v in normals.values()):raise ValueError('Separate cycle normal receipts required')
        object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(normals))

@dataclass(frozen=True)
class SourceMessageCyclePlan:
    complete:bool
    status:str
    calls:tuple=()
    reads:tuple=()
    stores:tuple=()
    needed:object=None
    first_count_signed:object=None
    tail_count_signed:object=None
    elapsed_signed_qword:object=None
    helper_pushes:tuple=()
    next_address:object=None
    whole_function_verified:bool=False
    native_execution_verified:bool=False
    delivery_verified:bool=False
    live_compatibility_verified:bool=False

class _Wait(Exception):
    def __init__(self,kind,key):self.needed=(kind,key);super().__init__(key)

def _plan(o,context):
    calls=[];reads=[];stores=[];first=tail=elapsed=None;pushes=()
    def result(status,wait=None):
        return SourceMessageCyclePlan(wait is None,status,tuple(calls),tuple(reads),tuple(stores),
            None if wait is None else wait.needed,first,tail,elapsed,pushes,0x45cdc8 if wait is None else None)
    def value(key):
        if key not in o.values:raise _Wait('value',key)
        return o.values[key]
    def read(key,address):
        reads.append((address&0xffffffff,4,key));return value(key)
    def normal(key,target,args=()):
        calls.append((target,args,key))
        if o.normal_returns.get(key) is not True:raise _Wait('normal',key)
    def count(prefix):
        if read(prefix+'_test_begin',context+0x10)==0:return 0
        end=read(prefix+'_end',context+0x14)
        begin=read(prefix+'_subtract_begin',context+0x10)
        return _divide12(end-begin)
    def row(prefix,offset):
        index=read(prefix+'_index',context+0x24)
        begin=read(prefix+'_begin',context+0x10)
        # Source has no preceding index bounds check or modulo normalization.
        return read(prefix+'_value',begin+((index*12)&0xffffffff)+offset)
    try:
        if not o.entry_reached:raise _Wait('entry','0045cceb')
        first=count('first')
        if first==0:return result('first_count_zero')
        normal('first_tick','GetTickCount');tick=value('first_tick_eax')
        low=read('last_tick_low',context+0x28);high=read('last_tick_high',context+0x2c)
        elapsed=_signed((tick-((high<<32)|low))&((1<<64)-1),64)
        delay=_signed(row('delay',8),32)
        due=elapsed>=delay
        if due:
            field4=row('argument4',4);field0=row('argument0',0)
            pushes=(field4,field0,context)
            normal('message_helper','0045c1f8',pushes)
            normal('second_tick','GetTickCount');stamp=value('second_tick_eax')
            stores.extend((((context+0x28)&0xffffffff,4,stamp),((context+0x2c)&0xffffffff,4,0)))
            before=read('increment_index_before',context+0x24)
            stores.append(((context+0x24)&0xffffffff,4,(before+1)&0xffffffff))
        tail=count('tail')
        current=read('tail_compare_index',context+0x24)
        if tail&0xffffffff==current:
            stores.append(((context+0x24)&0xffffffff,4,0))
            return result('helper_returned_tail_reset' if due else 'waiting_tail_reset')
        return result('helper_returned_index_retained' if due else 'waiting_index_retained')
    except _Wait as wait:return result('needs_observation',wait)

class SourceMessageCycleFrame:
    def __init__(self,*,context=0x569910):
        _raw(context)
        if context is None:raise ValueError('Explicit source message context required')
        self.context=context;self.observation=SourceMessageCycleObservation();self.final=None
    def advance(self,incoming):
        if not isinstance(incoming,SourceMessageCycleObservation):raise ValueError('Typed message-cycle observations required')
        if self.final is not None:return self.final
        for _ in range(40):
            plan=_plan(self.observation,self.context)
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
        raise AssertionError('Message-cycle reached capture budget exceeded')

@dataclass(frozen=True)
class MessageCallbackObservation:
    entry_reached:bool=False
    gate_byte:object=None
    cycle:object=None
    cycle_parent_returned:object=None
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit bounded callback entry required')
        _raw(self.gate_byte,8)
        if self.cycle is not None and not isinstance(self.cycle,SourceMessageCycleObservation):raise ValueError('Typed source cycle child required')
        if self.cycle_parent_returned is not None and type(self.cycle_parent_returned) is not bool:raise ValueError('Separate cycle parent normal receipt required')

@dataclass(frozen=True)
class MessageCallbackPlan:
    complete:bool
    child:object=None
    needed:object=None
    next_address:object=None
    native_execution_verified:bool=False
    delivery_verified:bool=False

class MessageCallbackFrame:
    """Only46f1bb..46f1cf, not the whole enclosing callback."""
    def __init__(self):
        self.entry=False;self.gate=None;self.child=SourceMessageCycleFrame();self.final=None
    def advance(self,o):
        if not isinstance(o,MessageCallbackObservation):raise ValueError('Typed callback observations required')
        if self.final is not None:return self.final
        if not self.entry:
            if not o.entry_reached:return MessageCallbackPlan(False,needed='entry_reached')
            self.entry=True
        if self.gate is None:
            if o.gate_byte is None:return MessageCallbackPlan(False,needed='gate_byte')
            self.gate=o.gate_byte
        if self.gate==0:
            self.final=MessageCallbackPlan(True,next_address=0x46f1cf);return self.final
        child=self.child.advance(o.cycle or SourceMessageCycleObservation())
        if not child.complete:return MessageCallbackPlan(False,child,('cycle',child.needed))
        if o.cycle_parent_returned is not True:return MessageCallbackPlan(False,child,'cycle_parent_returned')
        self.final=MessageCallbackPlan(True,child,next_address=0x46f1cf);return self.final
