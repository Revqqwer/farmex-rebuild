"""46f97d..46fb33 tail control replay with captured helper/cleanup returns."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState
from main_worker import MainWorkerObservation,MainWorkerFrame

ENTRIES=(0x46f97d,0x46fb09,0x46fb2f)

@dataclass(frozen=True)
class CallbackTailObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 main_child:object=None
 def __post_init__(self):
  v=dict(self.values);n=dict(self.normal_returns)
  if any(type(x) is not int or not 0<=x<1<<(8 if k.endswith('_byte') else 32) for k,x in v.items()):raise ValueError('Raw callback tail BYTE/DWORD required')
  if any(type(x) is not bool for x in n.values()):raise ValueError('Separate tail normal receipts required')
  if self.main_child is not None and not isinstance(self.main_child,MainWorkerObservation):raise ValueError('Typed main worker child required')
  object.__setattr__(self,'values',MappingProxyType(v));object.__setattr__(self,'normal_returns',MappingProxyType(n))

@dataclass(frozen=True)
class CallbackTailPlan:
 complete:bool
 queue:QueueState
 entry:int
 reads:tuple=()
 calls:tuple=()
 stores:tuple=()
 main_plan:object=None
 missing:str=''
 needed:object=None
 normal_return_receipt:bool=False
 native_execution_verified:bool=False
 whole_callback_verified:bool=False
 callback_ABI_verified:bool=False
 queue_effect_verified:bool=False

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def signed(v,bits):return v if v<1<<(bits-1) else v-(1<<bits)

def plan_callback_tail(o,queue=None,*,entry=0x46f97d,_main=None):
 if not isinstance(o,CallbackTailObservation) or entry not in ENTRIES:raise ValueError('Typed tail observation and known entry required')
 queue=QueueState() if queue is None else queue
 if not isinstance(queue,QueueState):raise ValueError('Own tail-entry queue required')
 reads=[];calls=[];stores=[];main=None
 def result(error=None):return CallbackTailPlan(error is None,queue,entry,tuple(reads),tuple(calls),tuple(stores),main,'' if error is None else str(error),None if error is None else error.needed,normal_return_receipt=error is None)
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def read(label,address,width=4):reads.append((address&0xffffffff,width,label));return value(label)
 def normal(label,helper,args=()):
  calls.append((helper,args,label))
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def tick(label):normal(label,'GetTickCount');return value(label+'_eax')
 def elapsed(label,clock,low_address):
  lo=read(label+'_low',low_address);hi=read(label+'_high',low_address+4)
  return signed((clock-((hi<<32)|lo))&0xffffffffffffffff,64)
 def random(label):normal(label,'00467cc4',(300000,60000));return value(label+'_eax')
 def interlude():
  now=tick('interlude_tick')
  if elapsed('initial_session',now,0x5620a4)==0:return
  if read('initial_interval',0x5620cc)==0:stores.append((0x5620cc,4,random('initial_random')))
  session=elapsed('fresh_session',now,0x5620a4);threshold=signed(read('session_interval',0x5620cc),32)
  if session<=threshold:return
  attempt=elapsed('fresh_attempt',now,0x5620d4);threshold=signed(read('attempt_interval',0x5620cc),32)
  if attempt<threshold:return
  normal('predicate','0046ebd0');predicate=value('predicate_eax')&255
  if predicate==0 or read('predicate_flag_byte',0x555e23,1)==0:
   target=read('replacement_target',0x554218)
   normal('replacement','0046b8fc',(0x46eca8,target,0x554228))
  stores.extend(((0x5620d4,4,now),(0x5620d8,4,0)))
  stores.append((0x5620cc,4,random('final_random')))
 try:
  if entry==0x46f97d:
   if read('bot_enabled_byte',0x561f60,1):normal('control','00458f98',(0x562194,))
   if read('attack_lock_byte',0x561f7e,1):
    now=tick('unlock_tick');started=read('lock_started',0x561f84);duration=read('lock_duration',0x561f80)
    if (now-started)&0xffffffff>=duration:stores.append((0x561f7e,1,0))
   interlude()
   if read('mode_zero',0x561f58)==0:
    calls.append(('0046ee14',(),'main_worker'))
    if _main is not None:
     outcome=_main()
     if outcome is not None:main,queue=outcome
    elif o.main_child is not None:
     frame=MainWorkerFrame(queue);main=frame.advance(o.main_child);queue=frame.queue
    if main is not None and not main.complete:raise _Missing('child','main_worker')
    if o.normal_returns.get('main_worker') is not True:raise _Missing('normal','main_worker')
   elif read('mode_two',0x561f58)==2:normal('mode2','0047b7fc',(0x569a98,))
   elif read('mode_three',0x561f58)==3:normal('mode3','004f82e8',(0x569a30,))
   elif read('mode_four',0x561f58)==4:normal('mode4','0046f1b8')
   elif read('mode_five',0x561f58)==5:normal('mode5','00471284',(0x569a20,))
  if entry!=0x46fb2f:
   slot=read('cleanup_root_slot',0x553e80);root=read('cleanup_root',slot)
   offset=read('cleanup_offset',0x5540d4);ecx=read('cleanup_ecx',root+offset)
   target=read('cleanup_target',0x554228)
   normal('cleanup_callback','opaque_indirect_callback',(target,ecx,()))
   normal('SEH_restore','captured_SEH_restore')
  normal('epilogue','captured_callback_epilogue_return')
  return result()
 except _Missing as error:return result(error)

class CallbackTailFrame:
 def __init__(self,queue=None,*,entry=0x46f97d):
  self.queue=QueueState() if queue is None else queue;self.entry=entry;self.observation=CallbackTailObservation();self.main=None;self.final=None
  plan_callback_tail(self.observation,self.queue,entry=entry)
 def advance(self,o):
  if not isinstance(o,CallbackTailObservation):raise ValueError('Typed callback tail observation required')
  if o.main_child is not None and self.main is None and self.observation.normal_returns.get('main_worker') is True:raise ValueError('Cannot retroactively bind completed opaque main worker')
  if self.final is not None:return self.final
  def main():
   if self.main is None:
    if o.main_child is None:return None
    self.main=MainWorkerFrame(self.queue)
   p=self.main.advance(o.main_child or MainWorkerObservation());self.queue=self.main.queue;return p,self.queue
  for _ in range(512):
   p=plan_callback_tail(self.observation,self.queue,entry=self.entry,_main=main)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind=='child':return p
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('Own callback tail observation budget exceeded')
