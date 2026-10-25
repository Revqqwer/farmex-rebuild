"""004ca9b0 immutable source templates, fresh NPC reads and own queue prefixes.

Uses the existing target-prepare/EventEnqueue children. No send, process access
or server acknowledgement is performed. Queue changes are owned local state.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState
from direct_chat_packets import QueueAttempt
from event_packets import EventPacketObservation,EventPacketFrame,EventEnqueueFrame
from item_break_cycle import ItemBreakCycleObservation,ItemBreakClockObservation,_raw,_receipts
from item_break_npc import ItemBreakNpcCycleFrame

FIRST_TEMPLATE=bytes.fromhex('640725100000')
SECOND_TEMPLATE=bytes.fromhex('55000f31363034375f4d6f6972612e6c7561ff')
REQUESTS=((FIRST_TEMPLATE,200),(SECOND_TEMPLATE,250))

@dataclass(frozen=True)
class ItemBreakRequestObservation:
    entry_reached:bool=False
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    target_child:object=None
    attempts:object=field(default_factory=dict)
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit post-prologue request entry required')
        values=dict(self.values);normals=dict(self.normal_returns);attempts=dict(self.attempts)
        for value in values.values():
            _raw(value,32)
            if value is None:raise ValueError('Explicit fresh selected-NPC EAX required')
        if any(type(v) is not bool for v in normals.values()):raise ValueError('Separate request normal receipts required')
        if self.target_child is not None and not isinstance(self.target_child,EventPacketObservation):raise ValueError('Typed target-prepare child required')
        if any(type(k) is not int or k not in (0,1) or not isinstance(v,QueueAttempt) for k,v in attempts.items()):raise ValueError('Two ordered typed enqueue attempts required')
        for key,value in (('values',values),('normal_returns',normals),('attempts',attempts)):
            object.__setattr__(self,key,MappingProxyType(value))

@dataclass(frozen=True)
class ItemBreakRequestPlan:
    complete:bool
    status:str
    queue:QueueState
    calls:tuple=()
    payloads:tuple=()
    target:object=None
    children:tuple=()
    needed:object=None
    next_address:object=None
    whole_function_verified:bool=False
    native_execution_verified:bool=False
    delivery_verified:bool=False
    live_compatibility_verified:bool=False

class ItemBreakRequestFrame:
    def __init__(self,queue=None,*,context=0x561ef8):
        _raw(context,32)
        if context is None:raise ValueError('Explicit queue context required')
        self.context=context;self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own queue required')
        self.entry=False;self.normals=set();self.first=None;self.second=None;self.payloads=()
        self.calls=[];self.target_frame=None;self.target=None;self.target_done=False
        self.frames={};self.children={};self.completed=set();self.final=None
    def _result(self,needed=None,status='needs_observation',exit_address=None):
        return ItemBreakRequestPlan(needed is None,status,self.queue,tuple(self.calls),self.payloads,
            self.target,tuple(sorted(self.children.items())),needed,exit_address)
    def advance(self,o):
        if not isinstance(o,ItemBreakRequestObservation):raise ValueError('Typed request observations required')
        if self.final is not None:return self.final
        if not self.entry:
            if not o.entry_reached:return self._result(('entry','004ca9c2'))
            self.entry=True
        for label in ('first_selected','second_selected'):
            if label=='second_selected' and self.first==0:break
            if label not in self.normals:
                if not any(c[2]==label for c in self.calls):self.calls.append(('00462630',(),label))
                if o.normal_returns.get(label) is not True:return self._result(('normal',label))
                self.normals.add(label)
            attr='first' if label=='first_selected' else 'second'
            if getattr(self,attr) is None:
                key=label+'_eax'
                if key not in o.values:return self._result(('value',key))
                setattr(self,attr,o.values[key])
            if label=='first_selected':
                if self.first==0:
                    self.final=self._result(status='first_selected_zero',exit_address=0x4ca9cb)
                    return self.final
                self.payloads=(FIRST_TEMPLATE,SECOND_TEMPLATE)
        if not self.target_done:
            if self.target_frame is None:
                self.target_frame=EventPacketFrame('target_prepare',self.queue,target=self.second)
                self.calls.append(('004c8f7c',(self.second,self.context),'target_parent')) #Physical PUSH order.
            self.target=self.target_frame.advance(o.target_child or EventPacketObservation())
            self.queue=self.target.queue
            if not self.target.complete:return self._result(('target_child',self.target.needed))
            if o.normal_returns.get('target_parent') is not True:return self._result(('normal','target_parent'))
            self.target_done=True
        for index,(payload,delay) in enumerate(REQUESTS):
            if index in self.completed:continue
            if index not in self.frames:
                self.frames[index]=EventEnqueueFrame(payload,delay,self.queue)
                self.calls.append(('004c7710',(self.context,payload,len(payload),delay),index))
            child=self.frames[index].advance(o.attempts.get(index,QueueAttempt()))
            self.children[index]=child;self.queue=child.queue
            if not child.complete:return self._result(('enqueue',index,child.needed))
            self.completed.add(index)
        self.final=self._result(status='request_helpers_returned',exit_address=0x4caa3c)
        return self.final

@dataclass(frozen=True)
class ItemBreakRequestCyclePlan:
    complete:bool
    caller:object
    request:object
    queue:QueueState
    needed:object=None
    native_execution_verified:bool=False
    delivery_verified:bool=False
    live_compatibility_verified:bool=False

class ItemBreakRequestCycleFrame:
    """Own inventory -> NPC -> clock -> action-child composition; no native IO."""
    def __init__(self,queue=None,*,context=0x569a20):
        self.caller=ItemBreakNpcCycleFrame(context=context)
        self.request=ItemBreakRequestFrame(queue)
        self.request_result=None;self.parent_returned=False
    def advance(self,caller,request=None,npc=None,guard=None,*,guard_parent_returned=None,
                npc_parent_returned=None,action_parent_returned=None):
        if not isinstance(caller,ItemBreakCycleObservation):raise ValueError('Typed caller required')
        if caller.clock_inputs is not None and caller.clock_inputs.action_returned is not None:
            raise ValueError('Typed request child owns clock action-return binding')
        if request is not None and not isinstance(request,ItemBreakRequestObservation):raise ValueError('Typed request child required')
        _receipts(action_parent_returned)
        def bound():
            if not self.parent_returned:return caller
            return replace(caller,clock_inputs=replace(caller.clock_inputs or ItemBreakClockObservation(),action_returned=True))
        plan=self.caller.advance(bound(),npc,guard,guard_parent_returned=guard_parent_returned,
                                 npc_parent_returned=npc_parent_returned)
        clock=plan.caller.caller.clock
        if plan.needed=='clock_inputs' and clock is not None and clock.needed=='action_returned':
            self.request_result=self.request.advance(request or ItemBreakRequestObservation())
            if not self.request_result.complete:
                return ItemBreakRequestCyclePlan(False,plan,self.request_result,self.request.queue,('request',self.request_result.needed))
            if action_parent_returned is not True:
                return ItemBreakRequestCyclePlan(False,plan,self.request_result,self.request.queue,'action_parent_returned')
            self.parent_returned=True
            plan=self.caller.advance(bound(),npc,guard,guard_parent_returned=guard_parent_returned,
                                     npc_parent_returned=npc_parent_returned)
        return ItemBreakRequestCyclePlan(plan.complete,plan,self.request_result,self.request.queue,plan.needed)
