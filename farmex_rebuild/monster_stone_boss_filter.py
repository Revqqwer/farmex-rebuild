"""004c4f64 conditional operand replay; no target memory or guessed string codec."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType

# Pinned startup literals, not proof of a live vector or locale-equivalent equality.
STARTUP_BOSS_NAMES=(b'Upertaurs',b'Countral',b'Indy Archer',b'Obelisk',b'Dragonia',
 b'Rampage Orc',b'Kekurisharesause',b'Laonbelisk',b'Revenge Knight',b'Black Guard',
 b'Alphabet',b'Goddess Ymir',b'Dungeon Keeper')

@dataclass(frozen=True)
class MSBossFilterObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 def __post_init__(self):
  values=dict(self.values);returns=dict(self.normal_returns)
  if any(type(v) is not int or not 0<=v<=0xffffffff for v in values.values()):raise ValueError('Raw boss-filter DWORD required')
  if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate helper normal returns required')
  object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(returns))

@dataclass(frozen=True)
class MSBossFilterPlan:
 complete:bool
 status:str
 return_al:object=None
 return_eax:object=None
 matched_index:object=None
 counts:tuple=()
 reads:tuple=()
 calls:tuple=()
 missing:str=''
 needed:object=None
 string_semantics_verified:bool=False
 live_vector_verified:bool=False
 native_execution_verified:bool=False

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def _count(begin,end):
 delta=(end-begin)&0xffffffff
 signed=delta if delta<0x80000000 else delta-0x100000000
 return ((signed+(3 if signed<0 else 0))>>2)&0xffffffff

def plan_ms_boss_filter(o,*,candidate_name,context=0x56216c,entry_budget=64):
 if not isinstance(o,MSBossFilterObservation):raise ValueError('Typed boss-filter observations required')
 if type(candidate_name) is not str:raise ValueError('Captured Unicode candidate required')
 if type(context) is not int or not 0<=context<=0xffffffff:raise ValueError('Raw context required')
 if type(entry_budget) is not int or entry_budget<1:raise ValueError('Explicit positive local budget required')
 calls=[];reads=[];counts=[];matched=None;al=None;eax=None
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def read(label,address):reads.append((address&0xffffffff,4,label));return value(label)
 def normal(label,helper,args=()):
  calls.append((helper,args,label))
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def result(status,error=None):
  return MSBossFilterPlan(error is None,status,al,eax,matched,tuple(counts),tuple(reads),tuple(calls),
   '' if error is None else str(error),None if error is None else error.needed)
 def finish(status,found=False):
  nonlocal al,eax
  normal('return_cleanup','00505c64',('candidate_copy',))
  al=int(found);eax=None if found else 0 #Source success writes AL only.
  return result(status)
 try:
  normal('frame_setup','opaque_frame_setup_and_argument_copy',(candidate_name,))
  normal('empty_compare','00505d3c',(candidate_name,'source_empty_string'))
  empty=value('empty_compare_eax')&255
  normal('empty_cleanup','00505c64',('empty_temporary',))
  if empty:return finish('empty_candidate')
  for i in range(entry_budget):
   pre='e%d.'%i
   begin=read(pre+'begin_check',context+0x18)
   if begin==0:count=0
   else:
    end=read(pre+'end',context+0x1c)
    fresh=read(pre+'begin_subtract',context+0x18)
    count=_count(fresh,end)
   counts.append(count)
   if count<=i:return finish('no_match') #Unsigned JA source loop gate.
   normal(pre+'candidate_convert','004073a0',(candidate_name,))
   begin=read(pre+'begin_entry',context+0x18)
   address=(begin+4*i)&0xffffffff
   normal(pre+'compare','00505134',('converted_candidate_temporary',address))
   comparison=value(pre+'compare_eax')&255
   normal(pre+'temporary_cleanup','004040f8',('converted_candidate_temporary',))
   if comparison:
    matched=i;return finish('matched',True)
  raise _Missing('budget','source_vector_loop_still_open')
 except _Missing as error:return result('needs_observation',error)

class MSBossFilterFrame:
 def __init__(self,*,candidate_name,context=0x56216c,entry_budget=64):
  self.candidate_name=candidate_name;self.context=context;self.budget=entry_budget
  self.observation=MSBossFilterObservation();self.final=None
  plan_ms_boss_filter(self.observation,candidate_name=candidate_name,context=context,entry_budget=entry_budget)
 def extend_budget(self,new_budget):
  if type(new_budget) is not int or new_budget<=self.budget:raise ValueError('Larger explicit local budget required')
  self.budget=new_budget
 def advance(self,o):
  if not isinstance(o,MSBossFilterObservation):raise ValueError('Typed boss-filter observations required')
  if self.final is not None:return self.final
  for _ in range(16384):
   p=plan_ms_boss_filter(self.observation,candidate_name=self.candidate_name,context=self.context,entry_budget=self.budget)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind=='budget':return p
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('Boss-filter own observation budget exceeded')
