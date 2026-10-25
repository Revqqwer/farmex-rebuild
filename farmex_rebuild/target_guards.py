"""00464c2c actor callback gate and0040b894 ID-vector exclusion replay."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType

@dataclass(frozen=True)
class TargetGuardObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 def __post_init__(self):
  values=dict(self.values);normals=dict(self.normal_returns)
  if any(type(v) is not int or not 0<=v<(1<<(8 if k.endswith('_byte') else 32)) for k,v in values.items()):raise ValueError('Raw guard BYTE/DWORD required')
  if any(type(v) is not bool for v in normals.values()):raise ValueError('Separate guard normal returns required')
  object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(normals))

@dataclass(frozen=True)
class TargetGuardPlan:
 complete:bool
 status:str
 return_eax:object=None
 return_al:object=None
 reads:tuple=()
 calls:tuple=()
 counts:tuple=()
 callback_invocation:object=None
 missing:str=''
 needed:object=None
 ID_origin_verified:bool=False
 callback_ABI_verified:bool=False
 native_execution_verified:bool=False

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def pointer_count(begin,end):
 difference=(end-begin)&0xffffffff
 signed=difference if difference<0x80000000 else difference-0x100000000
 return ((signed+(3 if signed<0 else 0))>>2)&0xffffffff

def plan_target_guard(kind,argument,o,*,context=0x561f34,entry_budget=64):
 if kind not in ('actor','id_list') or not isinstance(o,TargetGuardObservation):raise ValueError('Known typed guard required')
 if any(type(v) is not int or not 0<=v<=0xffffffff for v in (argument,context)):raise ValueError('Raw guard argument/context required')
 if type(entry_budget) is not int or entry_budget<1:raise ValueError('Positive local entry budget required')
 reads=[];calls=[];counts=[];callback=None;eax=None
 def result(status,error=None):
  return TargetGuardPlan(error is None,status,eax,None if eax is None else eax&255,tuple(reads),tuple(calls),tuple(counts),callback,
   '' if error is None else str(error),None if error is None else error.needed)
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def read(label,address,width=4):reads.append((address&0xffffffff,width,label));return value(label)
 def normal(label,helper,args=()):
  calls.append((helper,args,label))
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def finish(status,result_eax):
  nonlocal eax
  normal('return','source_normal_return');eax=result_eax;return result(status)
 try:
  if kind=='actor':
   if argument==0:return finish('null_actor',0)
   slot=read('guarded_root_slot',0x553e7c)
   normal('guarded_root','0045dc44',(slot,));root=value('guarded_root_eax')
   if read('first_profile_byte',0x553e46,1)&255==1:pushes=(argument,root)
   elif read('second_profile_byte',0x553e46,1)&255==2:pushes=(argument,)
   else:return finish('unsupported_profile',0)
   slot=read('direct_root_slot',0x553e7c);ecx=read('direct_root',slot)
   target=read('callback_target',0x553ea0)
   callback=(target,ecx,pushes)
   normal('callback','opaque_indirect_actor_callback',callback)
   returned=value('callback_eax')
   return finish('accepted' if returned&255==1 else 'rejected',returned if returned&255==1 else 0)
  normal('frame_setup','opaque_504c08')
  def vector_count(prefix):
   begin=read(prefix+'begin_check',context+0x208)
   if begin==0:n=0
   else:
    end=read(prefix+'end',context+0x20c)
    fresh=read(prefix+'begin_subtract',context+0x208)
    n=pointer_count(fresh,end)
   counts.append(n);return n
  if vector_count('initial.')==0:return finish('empty_list',1)
  for i in range(entry_budget):
   pre='e%d.'%i
   if vector_count(pre)<=i:
    #The loop count path leaves EAX=context+1f8; source writes AL only.
    return finish('not_listed',(((context+0x1f8)&0xffffffff)&0xffffff00)|1)
   begin=read(pre+'begin_entry',context+0x208)
   item=read(pre+'id',(begin+i*4)&0xffffffff)
   if item==argument:return finish('listed',0)
  raise _Missing('budget','source_ID_vector_still_open')
 except _Missing as error:return result('needs_observation',error)

class TargetGuardFrame:
 def __init__(self,kind,argument,*,context=0x561f34,entry_budget=64):
  self.kind=kind;self.argument=argument;self.context=context;self.budget=entry_budget
  self.observation=TargetGuardObservation();self.final=None
  plan_target_guard(kind,argument,self.observation,context=context,entry_budget=entry_budget)
 def extend_budget(self,new_budget):
  if type(new_budget) is not int or new_budget<=self.budget:raise ValueError('Larger explicit local budget required')
  self.budget=new_budget
 def advance(self,o):
  if not isinstance(o,TargetGuardObservation):raise ValueError('Typed guard observations required')
  if self.final is not None:return self.final
  for _ in range(16384):
   p=plan_target_guard(self.kind,self.argument,self.observation,context=self.context,entry_budget=self.budget)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind=='budget':return p
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('Target guard own observation budget exceeded')
