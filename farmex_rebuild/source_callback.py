"""Compose normal callback control segments; native semantics stay unverified."""
from dataclasses import dataclass,field
from action_queue import QueueState
from callback_prequeue import CallbackEntryEventObservation,CallbackEntryEventFrame
from callback_tail import CallbackTailObservation,CallbackTailFrame

@dataclass(frozen=True)
class SourceCallbackObservation:
 entry_event:CallbackEntryEventObservation=field(default_factory=CallbackEntryEventObservation)
 tail:CallbackTailObservation=field(default_factory=CallbackTailObservation)
 early_tail_queue:object=None
 def __post_init__(self):
  if not isinstance(self.entry_event,CallbackEntryEventObservation) or not isinstance(self.tail,CallbackTailObservation):raise ValueError('Typed callback segment observations required')
  if self.early_tail_queue is not None and not isinstance(self.early_tail_queue,QueueState):raise ValueError('Fresh own early-exit queue required')

@dataclass(frozen=True)
class SourceCallbackPlan:
 complete:bool
 entry_event:object
 tail:object=None
 queue:object=None
 missing:str=''
 needed:object=None
 normal_return_receipt:bool=False
 whole_callback_verified:bool=False
 callback_ABI_verified:bool=False
 native_execution_verified:bool=False
 live_compatibility_verified:bool=False

class SourceCallbackFrame:
 def __init__(self):self.entry=CallbackEntryEventFrame();self.tail=None;self.final=None
 def advance(self,o):
  if not isinstance(o,SourceCallbackObservation):raise ValueError('Typed complete callback control observations required')
  if self.final is not None:return self.final
  entry=self.entry.advance(o.entry_event)
  if not entry.complete:return SourceCallbackPlan(False,entry,queue=entry.queue,missing=entry.missing,needed=('entry_event',entry.needed))
  if self.tail is None:
   queue=entry.queue
   if queue is None:
    if o.early_tail_queue is None:return SourceCallbackPlan(False,entry,missing='fresh own queue at early tail entry',needed=('queue_state','early_tail'))
    queue=o.early_tail_queue
   self.tail=CallbackTailFrame(queue,entry=entry.next_source_address)
  tail=self.tail.advance(o.tail)
  p=SourceCallbackPlan(tail.complete,entry,tail,tail.queue,tail.missing,None if tail.complete else ('tail',tail.needed),tail.normal_return_receipt)
  if p.complete:self.final=p
  return p
