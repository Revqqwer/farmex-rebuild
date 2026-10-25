"""00458df8 automatic stat/skill allocation control replay, no game actions."""
from dataclasses import dataclass,field,replace
import re
from types import MappingProxyType
from allocation_actions import AllocationActionObservation,AllocationActionFrame,plan_allocation_action
from allocation_queries import AllocationQueryObservation,AllocationQueryFrame,plan_allocation_query,SKILL_FIELDS

ROOT='frmMain/MainTab/SheetDiger/grpAutoSkillStat/'
AUTO_ALLOCATION_FLAGS=(ROOT+'chAutoStat',ROOT+'chAutoSkill')

@dataclass(frozen=True)
class AutoAllocationObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 action_children:object=field(default_factory=dict)
 query_children:object=field(default_factory=dict)
 def __post_init__(self):
  values=dict(self.values);returns=dict(self.normal_returns)
  if any(type(v) is not int or not 0<=v<1<<(8 if k.endswith('_byte') else 32) for k,v in values.items()):raise ValueError('Raw allocation BYTE/DWORD required')
  if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate allocation normal receipts required')
  object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(returns))
  children=dict(self.action_children)
  if any(type(k) is not str or not re.fullmatch(r'(stat|skill)[0-9]+\.action',k) or not isinstance(v,AllocationActionObservation) for k,v in children.items()):raise ValueError('Typed allocation action children at row action keys required')
  object.__setattr__(self,'action_children',MappingProxyType(children))
  queries=dict(self.query_children)
  if any(type(k) is not str or not re.fullmatch(r'(stat|skill)[0-9]+\.query',k) or not isinstance(v,AllocationQueryObservation) for k,v in queries.items()):raise ValueError('Typed allocation query children at row query keys required')
  object.__setattr__(self,'query_children',MappingProxyType(queries))

@dataclass(frozen=True)
class AutoAllocationPlan:
 complete:bool
 status:str
 calls:tuple=()
 reads:tuple=()
 counts:tuple=()
 actions:tuple=()
 stores:tuple=()
 missing:str=''
 needed:object=None
 native_execution_verified:bool=False
 allocation_effect_verified:bool=False
 children:tuple=()

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def signed(v,bits=32):return v if v<1<<(bits-1) else v-(1<<bits)

def bind_query_entry(domain,index,argument,o):
 if domain=='skill' and argument not in SKILL_FIELDS:
  # 458ef7 MOV EAX,index; 458efa LEA EAX,[EAX+EAX*2].
  # ECX holds the vector base; PUSH and CALL leave that EAX intact.
  incoming=(index*3)&0xffffffff
  if 'incoming_eax' in o.values and o.values['incoming_eax']!=incoming:raise ValueError('Skill query incoming EAX differs from source caller row index')
  return replace(o,values={**o.values,'incoming_eax':incoming})
 return o

def plan_auto_allocation(o,*,context=0x562194,row_budget=64):
 if not isinstance(o,AutoAllocationObservation):raise ValueError('Typed allocation observations required')
 if type(context) is not int or not 0<=context<=0xffffffff:raise ValueError('Raw allocation context required')
 if type(row_budget) is not int or row_budget<1:raise ValueError('Positive local row budget required')
 calls=[];reads=[];counts=[];actions=[];stores=[];children=[]
 def result(status,error=None):return AutoAllocationPlan(error is None,status,tuple(calls),tuple(reads),tuple(counts),tuple(actions),tuple(stores),'' if error is None else str(error),None if error is None else error.needed,children=tuple(children))
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def read(label,address,width=4):reads.append((address&0xffffffff,width,label));return value(label)
 def normal(label,helper,args=()):
  calls.append((helper,args,label))
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def tick(label):normal(label,'GetTickCount');return value(label+'_eax')
 def finish(status):normal('return','source_normal_return');return result(status)
 def count(domain,index,offset):
  pre='%s%d.'%(domain,index)
  begin=read(pre+'begin_check',context+offset)
  if begin==0:n=0
  else:
   end=read(pre+'end',context+offset+4);fresh=read(pre+'begin_subtract',context+offset)
   difference=signed((end-fresh)&0xffffffff)
   quotient=abs(difference)//12;n=(-quotient if difference<0 else quotient)&0xffffffff
  counts.append((domain,index,n));return n
 def query(domain,index,argument,helper):
  label=domain+'%d.query'%index;child=None
  if label in o.query_children:
   query_o=bind_query_entry(domain,index,argument,o.query_children[label])
   child=plan_allocation_query(domain,argument,query_o);children.append((label,child))
   if not child.complete:
    calls.append((helper,(argument,),label));raise _Missing('child',label)
  normal(label,helper,(argument,));returned=value(label+'_eax')
  if child is not None and returned!=child.return_eax:raise ValueError('Allocation query child differs from captured caller full EAX')
  return signed(returned)
 def action(domain,index,argument,helper):
  label=domain+'%d.action'%index
  if label in o.action_children:
   child=plan_allocation_action(domain,argument,o.action_children[label]);children.append((label,child))
   if not child.complete:
    calls.append((helper,(argument,),label));raise _Missing('child',label)
  normal(label,helper,(argument,));actions.append((domain,index,argument))
  now=tick('post_tick');stores.extend(((0x553cac,4,now),(0x553cb0,4,0)))
  return finish(domain+'_action_returned')
 try:
  now=tick('initial_tick');lo=read('cooldown_low',0x553cac);hi=read('cooldown_high',0x553cb0)
  elapsed=signed((now-((hi<<32)|lo))&0xffffffffffffffff,64)
  if elapsed<500:return finish('cooldown_wait')
  if read('stat_enabled_byte',context+0x20,1):
   normal('free_stat','00462eb8')
   if signed(value('free_stat_eax'))>0:
    for i in range(row_budget):
     pre='stat%d.'%i
     if count('stat',i,0x38)<=i:break
     begin=read(pre+'query_begin',context+0x38);key=read(pre+'key',begin+12*i)
     current=query('stat',i,key,'00462ed8')
     begin=read(pre+'threshold_begin',context+0x38);threshold=signed(read(pre+'threshold',begin+12*i+8))
     if current<threshold:
      begin=read(pre+'action_begin',context+0x38);argument=read(pre+'action_argument',begin+12*i+4)
      return action('stat',i,argument,'004650d8')
    else:raise _Missing('budget','stat_vector_still_open')
  if read('skill_enabled_byte',context+0x21,1):
   normal('free_skill','00462e8c')
   if signed(value('free_skill_eax'))>0:
    for i in range(row_budget):
     pre='skill%d.'%i
     if count('skill',i,0x58)<=i:break
     begin=read(pre+'query_begin',context+0x58);key=read(pre+'query_argument',begin+12*i+4)
     current=query('skill',i,key,'00462d20')
     begin=read(pre+'threshold_begin',context+0x58);threshold=signed(read(pre+'threshold',begin+12*i+8))
     if threshold>current:
      normal(pre+'level','00462670')
      if signed(value(pre+'level_eax'))<=current:return finish('skill_level_blocked')
      begin=read(pre+'action_begin',context+0x58);argument=read(pre+'action_argument',begin+12*i+4)
      return action('skill',i,argument,'00465ec4')
    else:raise _Missing('budget','skill_vector_still_open')
  return finish('no_action')
 except _Missing as error:return result('needs_observation',error)

class AutoAllocationFrame:
 def __init__(self,*,context=0x562194,row_budget=64):
  self.context=context;self.budget=row_budget;self.observation=AutoAllocationObservation();self.final=None;self.action_frames={};self.query_frames={}
  plan_auto_allocation(self.observation,context=context,row_budget=row_budget)
 def extend_budget(self,new_budget):
  if type(new_budget) is not int or new_budget<=self.budget:raise ValueError('Larger explicit local row budget required')
  self.budget=new_budget
 def advance(self,o):
  if not isinstance(o,AutoAllocationObservation):raise ValueError('Typed allocation observations required')
  for label in o.action_children:
   if self.observation.normal_returns.get(label) is True and label not in self.action_frames:
    raise ValueError('Cannot retroactively bind an opaque completed allocation action')
  for label in o.query_children:
   if self.observation.normal_returns.get(label) is True and label not in self.query_frames:
    raise ValueError('Cannot retroactively bind an opaque completed allocation query')
  if self.final is not None:return self.final
  for _ in range(16384):
   p=plan_auto_allocation(self.observation,context=self.context,row_budget=self.budget)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind=='budget':return p
   if kind in ('normal','child') and (label in self.query_frames or label in o.query_children):
    if label not in self.query_frames:
     helper,args,call_label=p.calls[-1]
     if call_label!=label or helper not in ('00462ed8','00462d20'):raise ValueError('Query child must bind reached allocation helper')
     self.query_frames[label]=AllocationQueryFrame('stat' if helper=='00462ed8' else 'skill',args[0])
    frame=self.query_frames[label]
    index=int(re.fullmatch(r'(?:stat|skill)([0-9]+)\.query',label)[1])
    incoming_o=o.query_children.get(label,AllocationQueryObservation())
    if 'incoming_eax' in frame.observation.values:
     incoming_o=replace(incoming_o,values={k:v for k,v in incoming_o.values.items() if k!='incoming_eax'})
    query_o=bind_query_entry(frame.kind,index,frame.argument,incoming_o)
    child=frame.advance(query_o)
    self.observation=replace(self.observation,query_children={**self.observation.query_children,label:frame.observation})
    if not child.complete:return plan_auto_allocation(self.observation,context=self.context,row_budget=self.budget)
    if o.normal_returns.get(label) is not True:return plan_auto_allocation(self.observation,context=self.context,row_budget=self.budget)
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
    continue
   if kind in ('normal','child') and (label in self.action_frames or label in o.action_children):
    if label not in self.action_frames:
     helper,args,call_label=p.calls[-1]
     if call_label!=label or helper not in ('004650d8','00465ec4'):raise ValueError('Action child must bind reached allocation helper')
     self.action_frames[label]=AllocationActionFrame('stat' if helper=='004650d8' else 'skill',args[0])
    frame=self.action_frames[label];child=frame.advance(o.action_children.get(label,AllocationActionObservation()))
    self.observation=replace(self.observation,action_children={**self.observation.action_children,label:frame.observation})
    if not child.complete:return plan_auto_allocation(self.observation,context=self.context,row_budget=self.budget)
    if o.normal_returns.get(label) is not True:return plan_auto_allocation(self.observation,context=self.context,row_budget=self.budget)
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
    continue
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('Allocation own observation budget exceeded')
