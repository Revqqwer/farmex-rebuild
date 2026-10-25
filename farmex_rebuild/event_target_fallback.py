"""464a20 ordered operand replay; allocation/stores/callbacks are inert plans."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState

@dataclass(frozen=True)
class EventFallbackObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 def __post_init__(self):
  v=dict(self.values);n=dict(self.normal_returns)
  if any(type(x) is not int or not 0<=x<1<<(8 if k.endswith('_byte') else 32) for k,x in v.items()):raise ValueError('Raw fallback BYTE/DWORD required')
  if any(type(x) is not bool for x in n.values()):raise ValueError('Separate fallback normal receipts required')
  object.__setattr__(self,'values',MappingProxyType(v));object.__setattr__(self,'normal_returns',MappingProxyType(n))

@dataclass(frozen=True)
class EventFallbackPlan:
 complete:bool
 status:str
 queue:QueueState
 reads:tuple=()
 calls:tuple=()
 stores:tuple=()
 callbacks:tuple=()
 missing:str=''
 needed:object=None
 native_execution_verified:bool=False
 callback_ABI_verified:bool=False
 allocation_effect_verified:bool=False
 memory_writes_verified:bool=False
 return_registers_verified:bool=False

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def plan_event_fallback(o,queue=None):
 if not isinstance(o,EventFallbackObservation):raise ValueError('Typed fallback observations required')
 queue=QueueState() if queue is None else queue
 if not isinstance(queue,QueueState):raise ValueError('Own fallback queue required')
 reads=[];calls=[];stores=[];callbacks=[]
 def result(status,error=None):return EventFallbackPlan(error is None,status,queue,tuple(reads),tuple(calls),tuple(stores),tuple(callbacks),'' if error is None else str(error),None if error is None else error.needed)
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def read(label,address,width=4):reads.append((address&0xffffffff,width,label));return value(label)
 def normal(label,helper,args=()):
  calls.append((helper,args,label))
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def callback(label,target,ecx,pushes):
  callbacks.append((label,target,ecx,pushes));normal(label,'opaque_indirect_callback',(target,ecx,pushes))
 def guarded(label,address):normal(label,'0045dc44',(address&0xffffffff,));return value(label+'_eax')
 def finish(status):normal('return','source_normal_return');return result(status)
 try:
  if read('first_profile_byte',0x553e46,1)==1:
   slot=read('profile1_root_slot',0x553e80);ecx=read('profile1_ecx',slot);target=read('profile1_target',0x553eac)
   callback('profile1_callback',target,ecx,());return finish('profile1_returned')
  if read('second_profile_byte',0x553e46,1)!=2:return finish('unsupported_profile')
  if read('allocation_before',0x553d18)==0:
   normal('allocate','VirtualAlloc',(0x40,0x1000,12,0)) #Physical PUSH order, never executed.
   allocated=value('allocate_eax');stores.append((0x553d18,4,allocated,'allocation_pointer'))
  for i,offset_global in enumerate((0x554008,0x55400c,0x554010)):
   pre='component%d.'%i
   slot=read(pre+'root_slot',0x553e7c);root=guarded(pre+'root',slot)
   offset=read(pre+'offset',offset_global)
   normal(pre+'float','0045ddb8',((root+offset)&0xffffffff,))
   pointer=read(pre+'allocation',0x553d18)
   # Raw post-FSTP bits are captured; no x87 rounding/exceptions are invented.
   normal(pre+'fstp','captured_FSTP_span');bits=value(pre+'fstp_bits')
   stores.append(((pointer+4*i)&0xffffffff,4,bits,pre+'float_store'))
  slot=read('discarded_root_slot',0x553e7c);read('discarded_root',slot) #Read occurs even though ECX is overwritten.
  pointer=read('argument_allocation',0x553d18)
  slot=read('search_root_slot',0x553e8c);ecx=read('search_ecx',slot);target=read('search_target',0x553eac)
  callback('search_callback',target,ecx,(pointer,));found=value('search_eax')
  if found==0:return finish('search_zero')
  slot=read('select_root_slot',0x553e80);ecx=read('select_ecx',slot);target=read('select_target',0x553ea4)
  callback('select_callback',target,ecx,(found,))
  slot=read('confirm_root_slot',0x553e7c);ecx=read('confirm_ecx',slot);target=read('confirm_target',0x553eb4)
  callback('confirm_callback',target,ecx,(0,found))
  return finish('profile2_returned')
 except _Missing as error:return result('needs_observation',error)

class EventFallbackFrame:
 def __init__(self,queue=None):
  self.queue=QueueState() if queue is None else queue;self.observation=EventFallbackObservation();self.final=None
  plan_event_fallback(self.observation,self.queue)
 def advance(self,o):
  if not isinstance(o,EventFallbackObservation):raise ValueError('Typed fallback observations required')
  if self.final is not None:return self.final
  for _ in range(512):
   p=plan_event_fallback(self.observation,self.queue)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('Own fallback observation budget exceeded')
