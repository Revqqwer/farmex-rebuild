"""Bounded46f8be..46f97d callback segment, entered explicitly after queue drain."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState
from event_join import EventJoinObservation,EventJoinFrame

@dataclass(frozen=True)
class EventCallbackObservation:
 entry_reached:bool=False
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 event_child:object=None
 def __post_init__(self):
  if type(self.entry_reached) is not bool:raise ValueError('Explicit post-drain callback entry required')
  v=dict(self.values);n=dict(self.normal_returns)
  if any(type(x) is not int or not 0<=x<1<<(8 if k.endswith('_byte') else 32) for k,x in v.items()):raise ValueError('Raw event callback BYTE/DWORD required')
  if any(type(x) is not bool for x in n.values()):raise ValueError('Separate callback normal receipts required')
  if self.event_child is not None and not isinstance(self.event_child,EventJoinObservation):raise ValueError('Typed event worker child required')
  object.__setattr__(self,'values',MappingProxyType(v));object.__setattr__(self,'normal_returns',MappingProxyType(n))

@dataclass(frozen=True)
class EventCallbackPlan:
 complete:bool
 status:str
 queue:QueueState
 reads:tuple=()
 calls:tuple=()
 stores:tuple=()
 event_reached:bool=False
 event_plan:object=None
 next_source_address:object=None
 missing:str=''
 needed:object=None
 whole_callback_verified:bool=False
 callback_return_verified:bool=False
 native_execution_verified:bool=False

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def plan_event_callback(o,queue=None,*,_event=None):
 if not isinstance(o,EventCallbackObservation):raise ValueError('Typed post-drain callback observation required')
 queue=QueueState() if queue is None else queue
 if not isinstance(queue,QueueState):raise ValueError('Explicit own post-drain queue required')
 reads=[];calls=[];stores=[];reached=False;child=None
 def result(status,error=None,next_at=None):return EventCallbackPlan(error is None,status,queue,tuple(reads),tuple(calls),tuple(stores),reached,child,next_at,'' if error is None else str(error),None if error is None else error.needed)
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def read(label,address,width=1):reads.append((address,width,label));return value(label)
 def normal(label,helper,args=()):
  calls.append((helper,args,label))
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def skip(status,reset=False):
  if reset:stores.extend(((0x568dc0,4,14),(0x568dbc,1,0)))
  return result(status,next_at=0x46fb09)
 try:
  if not o.entry_reached:raise _Missing('entry','after004c79a0_return')
  if read('vip_active_byte',0x5690b8):normal('vip_storage','004ff934',(0x5690b8,))
  elif read('inn_active_byte',0x5690e0):normal('inn_storage','00470a94',(0x5690e0,))
  elif read('worker_active_byte',0x568dbc):
   normal('vip_probe','004fe3a0',(0x5690b8,))
   if value('vip_probe_eax')&255:return skip('worker_reset_vip',True)
   normal('inn_probe','0046fe90',(0x5690e0,))
   if value('inn_probe_eax')&255:return skip('worker_reset_inn',True)
   if read('exclusive_byte',0x561f6f):return skip('worker_reset_exclusive',True)
   normal('health_probe','004611a0');health=value('health_eax');health=health if health<0x80000000 else health-0x100000000
   if health<=0:return skip('worker_reset_health',True)
   normal('worker_step','004ee5b0',(0x5687a8,));step=value('worker_step_eax')
   stores.append((0x568dc0,4,step))
   compared=read('worker_step_compare',0x568dc0,4)
   return skip('worker_step_reset' if compared==43 else 'worker_step_exit',compared==43)
  reached=True;calls.append(('0045a4dc',(0x562194,),'event_worker'))
  if _event is not None:child=_event()
  elif o.event_child is not None:child=EventJoinFrame(queue=queue).advance(o.event_child)
  if child is not None:
   queue=child.queue
   if not child.complete:raise _Missing('child','event_worker')
  if o.normal_returns.get('event_worker') is not True:raise _Missing('normal','event_worker')
  # The following instruction reads bot_enabled; it is outside this segment.
  return result('event_fallthrough',next_at=0x46f97d)
 except _Missing as error:return result('needs_observation',error)

class EventCallbackFrame:
 def __init__(self,queue=None):
  self.queue=QueueState() if queue is None else queue;self.observation=EventCallbackObservation();self.event_frame=None;self.final=None
  plan_event_callback(self.observation,self.queue)
 def advance(self,o):
  if not isinstance(o,EventCallbackObservation):raise ValueError('Typed event callback observation required')
  if o.event_child is not None and self.event_frame is None and self.observation.normal_returns.get('event_worker') is True:raise ValueError('Cannot retroactively bind completed opaque event worker')
  if self.final is not None:return self.final
  def child():
   if self.event_frame is None:
    if o.event_child is None:return None
    self.event_frame=EventJoinFrame(queue=self.queue)
   p=self.event_frame.advance(o.event_child or EventJoinObservation());self.queue=p.queue;return p
  for _ in range(256):
   p=plan_event_callback(self.observation,self.queue,_event=child)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind=='child':return p
   if kind=='entry':
    if not o.entry_reached:return p
    self.observation=replace(self.observation,entry_reached=True)
   elif kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('Own event callback observation budget exceeded')
