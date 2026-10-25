"""4650d8/465ec4 inert operand replay; no native dispatch or point mutation."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType

def dword(v):
 if type(v) is not int or not 0<=v<=0xffffffff:raise ValueError('Raw allocation action DWORD required')

@dataclass(frozen=True)
class AllocationActionObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 def __post_init__(self):
  v=dict(self.values);n=dict(self.normal_returns)
  for x in v.values():dword(x)
  if any(type(x) is not bool for x in n.values()):raise ValueError('Separate action normal receipts required')
  object.__setattr__(self,'values',MappingProxyType(v));object.__setattr__(self,'normal_returns',MappingProxyType(n))

@dataclass(frozen=True)
class AllocationActionPlan:
 complete:bool
 kind:str
 argument:int
 reads:tuple=()
 calls:tuple=()
 invocation:object=None
 missing:str=''
 needed:object=None
 native_execution_verified:bool=False
 allocation_effect_verified:bool=False
 callback_ABI_verified:bool=False

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def plan_allocation_action(kind,argument,o):
 if kind not in ('stat','skill') or not isinstance(o,AllocationActionObservation):raise ValueError('Known typed allocation action required')
 dword(argument);reads=[];calls=[];invocation=None
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def read(label,address):reads.append((address&0xffffffff,4,label));return value(label)
 def normal(label,helper,args=()):
  calls.append((helper,args,label))
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def guarded(label,address):
  normal(label,'0045dc44',(address&0xffffffff,));return value(label+'_eax')
 def result(error=None):return AllocationActionPlan(error is None,kind,argument,tuple(reads),tuple(calls),invocation,'' if error is None else str(error),None if error is None else error.needed)
 try:
  if kind=='stat':
   slot=read('guarded_root_slot',0x553e80);root=guarded('guarded_root',slot)
   offset=read('guarded_first_offset',0x554108);first=guarded('guarded_first',root+offset)
   offset=read('guarded_second_offset',0x55410c);second=guarded('guarded_second',first+offset)
   offset=read('stat_table_offset',0x554110)
   selected=guarded('guarded_stat_entry',second+offset+((argument<<2)&0xffffffff))
   # These are fresh direct loads, not reuse of the guarded chain.
   slot=read('direct_root_slot',0x553e80);root=read('direct_root',slot)
   offset=read('direct_first_offset',0x554108);first=read('direct_first',root+offset)
   offset=read('direct_second_offset',0x55410c);ecx=read('direct_second',first+offset)
   offset=read('callback_offset',0x554200);vtable=read('vtable',ecx)
   target=read('callback_target',vtable+offset);pushes=(1,selected)
  else:
   slot=read('direct_root_slot',0x553e80);root=read('direct_root',slot)
   offset=read('skill_context_offset',0x554054);ecx=read('skill_context',root+offset)
   target=read('callback_target',0x553f0c);pushes=((argument+4)&0xffffffff,)
  invocation=(target,ecx,pushes)
  normal('callback','opaque_indirect_allocation_callback',invocation)
  normal('return','source_normal_return')
  return result()
 except _Missing as error:return result(error)

class AllocationActionFrame:
 def __init__(self,kind,argument):
  self.kind=kind;self.argument=argument;self.observation=AllocationActionObservation();self.final=None
  plan_allocation_action(kind,argument,self.observation)
 def advance(self,o):
  if not isinstance(o,AllocationActionObservation):raise ValueError('Typed allocation action observations required')
  if self.final is not None:return self.final
  for _ in range(128):
   p=plan_allocation_action(self.kind,self.argument,self.observation)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('Own allocation action observation budget exceeded')
