"""462ed8 stat-name/462d20 skill query replay; opaque string/guard receipts."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType

STAT_FIELDS=((b'STR',0x5540f4),(b'HP',0x5540f8),(b'DEX',0x5540fc),(b'MP',0x554104),(b'INT',0x554100))
SKILL_FIELDS={1:0x554058,2:0x55405c,3:0x554060,4:0x554064}

def dword(v):
 if type(v) is not int or not 0<=v<=0xffffffff:raise ValueError('Raw allocation query DWORD required')

@dataclass(frozen=True)
class AllocationQueryObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 def __post_init__(self):
  v=dict(self.values);n=dict(self.normal_returns)
  for x in v.values():dword(x)
  if any(type(x) is not bool for x in n.values()):raise ValueError('Separate allocation query normal receipts required')
  object.__setattr__(self,'values',MappingProxyType(v));object.__setattr__(self,'normal_returns',MappingProxyType(n))

@dataclass(frozen=True)
class AllocationQueryPlan:
 complete:bool
 kind:str
 argument:int
 return_eax:object=None
 selected_field:object=None
 comparisons:tuple=()
 reads:tuple=()
 calls:tuple=()
 missing:str=''
 needed:object=None
 native_execution_verified:bool=False
 string_runtime_verified:bool=False
 name_pointer_identity_verified:bool=False

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def plan_allocation_query(kind,argument,o):
 if kind not in ('stat','skill') or not isinstance(o,AllocationQueryObservation):raise ValueError('Known typed allocation query required')
 dword(argument);reads=[];calls=[];comparisons=[];eax=None;selected=None
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def read(label,address):reads.append((address&0xffffffff,4,label));return value(label)
 def normal(label,helper,args=()):
  calls.append((helper,args,label))
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def guarded(label,address):normal(label,'0045dc44',(address&0xffffffff,));return value(label+'_eax')
 def result(error=None):return AllocationQueryPlan(error is None,kind,argument,eax,selected,tuple(comparisons),tuple(reads),tuple(calls),'' if error is None else str(error),None if error is None else error.needed)
 try:
  if kind=='stat':
   normal('entry_setup','opaque_SEH_setup')
   normal('argument_copy','opaque_AnsiString_argument_copy',(argument,))
   for i,(literal,field_address) in enumerate(STAT_FIELDS):
    pre='compare%d.'%i
    normal(pre+'literal_init','004040bc',(literal,))
    normal(pre+'compare','opaque_AnsiString_equality',(argument,literal))
    matched=value(pre+'eax')&255
    comparisons.append((literal,matched))
    normal(pre+'literal_cleanup','004040f8')
    if matched:
     selected=literal
     slot=read('root_slot',0x553e7c);root=guarded('root',slot)
     offset=read('field_offset',field_address);eax=guarded('field',root+offset)
     break
   else:eax=0
   normal('argument_cleanup','004040f8',(argument,))
  elif argument in SKILL_FIELDS:
   selected=argument
   slot=read('root_slot',0x553e80);root=guarded('root',slot)
   offset=read('context_offset',0x554054);context=guarded('context',root+offset)
   offset=read('field_offset',SKILL_FIELDS[argument]);eax=guarded('field',context+offset)
  else:
   # All unsupported comparisons are CMP [EBP+8],imm; none assign EAX.
   eax=value('incoming_eax')
  normal('return','source_normal_return')
  return result()
 except _Missing as error:return result(error)

class AllocationQueryFrame:
 def __init__(self,kind,argument):
  self.kind=kind;self.argument=argument;self.observation=AllocationQueryObservation();self.final=None
  plan_allocation_query(kind,argument,self.observation)
 def advance(self,o):
  if not isinstance(o,AllocationQueryObservation):raise ValueError('Typed allocation query observations required')
  if self.final is not None:return self.final
  for _ in range(256):
   p=plan_allocation_query(self.kind,self.argument,self.observation)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('Own allocation query observation budget exceeded')
