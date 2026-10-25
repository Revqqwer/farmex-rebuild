"""Readiness/session/slot-switch helper control replay; all stores are inert."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType

@dataclass(frozen=True)
class CallbackLifecycleObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 predicate_child:object=None
 replacement_child:object=None
 def __post_init__(self):
  v=dict(self.values);n=dict(self.normal_returns)
  if any(type(x) is not int or not 0<=x<1<<(8 if k.endswith('_byte') else 32) for k,x in v.items()):raise ValueError('Raw lifecycle BYTE/DWORD required')
  if any(type(x) is not bool for x in n.values()):raise ValueError('Separate lifecycle normal receipts required')
  for child in (self.predicate_child,self.replacement_child):
   if child is not None and not isinstance(child,CallbackLifecycleObservation):raise ValueError('Typed lifecycle child required')
  object.__setattr__(self,'values',MappingProxyType(v));object.__setattr__(self,'normal_returns',MappingProxyType(n))

@dataclass(frozen=True)
class CallbackLifecyclePlan:
 complete:bool
 kind:str
 return_al:object=None
 return_eax:object=None
 reads:tuple=()
 calls:tuple=()
 stores:tuple=()
 children:tuple=()
 missing:str=''
 needed:object=None
 native_execution_verified:bool=False
 memory_effects_verified:bool=False
 full_return_registers_verified:bool=False

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def plan_callback_lifecycle(kind,o,*,target_slot=None,_child=None):
 if kind not in ('ready','stamp','switch','predicate','replace') or not isinstance(o,CallbackLifecycleObservation):raise ValueError('Known typed lifecycle helper required')
 if kind=='replace' and (type(target_slot) is not int or not 0<=target_slot<=0xffffffff):raise ValueError('Raw replacement slot required')
 reads=[];calls=[];stores=[];children=[];al=None;eax=None
 def result(error=None):return CallbackLifecyclePlan(error is None,kind,al,eax,tuple(reads),tuple(calls),tuple(stores),tuple(children),'' if error is None else str(error),None if error is None else error.needed)
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def read(label,address,width=4):reads.append((address,width,label));return value(label)
 def flag(label,address):return read(label+'_byte',address,1)!=0
 def normal(label,helper,args=()):
  calls.append((helper,args,label))
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def finish():normal('return','source_normal_return');return result()
 def child(label,child_kind,inputs,slot=None):
  p=_child(label,child_kind,slot) if _child is not None else CallbackLifecycleFrame(child_kind,target_slot=slot).advance(inputs)
  children.append((label,p))
  if not p.complete:raise _Missing('child',label)
  return p
 try:
  if kind=='predicate':
   ok=True
   for i in range(5):
    if not flag('predicate%d'%i,0x555e1d+i):ok=False;break
   if ok and not flag('predicate5',0x555e22):al=0;eax=0
   else:al=1 #MOV AL1 does not define the upper EAX bits.
   return finish()
  if kind=='replace':
   if read('saved_original',0x554228)==0:
    normal('guarded_original','0045dc44',(target_slot,));old=value('original_eax')
    stores.append((0x554228,4,old))
   normal('replacement_copy','captured_memcpy4',(target_slot,0x46eca8,4))
   stores.append((target_slot,4,0x46eca8));return finish()
  if kind=='ready':
   normal('object_check','004fc95c',(0x55424c,))
   if value('object_check_eax')&255==0:al=0;eax=0;return finish()
   nonzero=read('stamp_high',0x5620a8)!=0 or read('stamp_low',0x5620a4)!=0
   if nonzero and flag('notice_enabled',0x555df9) and flag('state_active',0x561f6d) and not flag('notice_done',0x553d35) and flag('notice_enabled_fresh',0x555df9):
    normal('notice_prepare','004fc26c',(0x55424c,));stores.append((0x553d35,1,1))
   al=1;return finish()
  if kind=='stamp':
   if flag('special',0x553e45):
    if read('stamp_high',0x5620a8)==0 and read('stamp_low',0x5620a4)==0:
     normal('tick','GetTickCount');stores.extend(((0x5620a4,4,value('tick_eax')),(0x5620a8,4,0)))
    return finish()
   if not flag('initialized',0x561f54):
    normal('initialize','004a0f8c');normal('tick','GetTickCount')
    stores.extend(((0x5620a4,4,value('tick_eax')),(0x5620a8,4,0),(0x561f54,1,1),(0x553d34,1,0)))
   elif not flag('profile_done',0x553d34) and flag('state_active',0x561f6d):
    if not flag('profile_enabled',0x561f55):normal('profile_refresh','00405a58',(0x561f34,))
    stores.append((0x553d34,1,1))
   return finish()
  if read('mode',0x561f58)==4 and flag('mode4_skip',0x569838):return finish()
  if flag('sleep_enabled',0x553e3c):
   milliseconds=read('sleep_ms',0x553e40);normal('sleep','SleepEx',(0,milliseconds))
  calls.append(('0046eb8c',(),'switch_predicate'))
  if o.predicate_child is not None or _child is not None and _child('has_predicate','predicate',None):
   p=child('switch_predicate','predicate',o.predicate_child or CallbackLifecycleObservation());verdict=p.return_al;known_eax=p.return_eax
  else:verdict=None;known_eax=None
  if o.normal_returns.get('switch_predicate') is not True:raise _Missing('normal','switch_predicate')
  observed=value('predicate_eax')
  if verdict is not None and observed&255!=verdict:raise ValueError('Lifecycle predicate differs from caller AL')
  if known_eax is not None and observed!=known_eax:raise ValueError('Lifecycle predicate differs from known full EAX')
  if observed&255:
   slot=read('target_slot',0x554218);calls.append(('0046b8fc',(0x46eca8,slot,0x554228),'replacement'))
   if o.replacement_child is not None or _child is not None and _child('has_replacement','replace',slot):
    child('replacement','replace',o.replacement_child or CallbackLifecycleObservation(),slot)
   if o.normal_returns.get('replacement') is not True:raise _Missing('normal','replacement')
  return finish()
 except _Missing as error:return result(error)

class CallbackLifecycleFrame:
 def __init__(self,kind,*,target_slot=None):
  self.kind=kind;self.slot=target_slot;self.observation=CallbackLifecycleObservation();self.frames={};self.final=None
  plan_callback_lifecycle(kind,self.observation,target_slot=target_slot)
 def advance(self,o):
  if not isinstance(o,CallbackLifecycleObservation):raise ValueError('Typed lifecycle observations required')
  for label,inputs in (('switch_predicate',o.predicate_child),('replacement',o.replacement_child)):
   if inputs is not None and label not in self.frames and self.observation.normal_returns.get(label) is True:raise ValueError('Cannot retroactively bind opaque lifecycle helper')
  if self.final is not None:return self.final
  def child(label,kind,slot):
   if label.startswith('has_'):
    name='switch_predicate' if label=='has_predicate' else 'replacement'
    inputs=o.predicate_child if name=='switch_predicate' else o.replacement_child
    return name in self.frames or inputs is not None
   inputs=o.predicate_child if label=='switch_predicate' else o.replacement_child
   if label not in self.frames:self.frames[label]=CallbackLifecycleFrame(kind,target_slot=slot)
   return self.frames[label].advance(inputs or CallbackLifecycleObservation())
  for _ in range(256):
   p=plan_callback_lifecycle(self.kind,self.observation,target_slot=self.slot,_child=child)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind=='child':return p
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('Own lifecycle observation budget exceeded')
