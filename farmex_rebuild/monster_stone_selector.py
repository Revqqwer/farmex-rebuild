"""004c50d0 captured iterator/operand replay. Stack-ID origin remains unresolved."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from monster_stone_boss_filter import MSBossFilterObservation,MSBossFilterFrame
from target_guards import TargetGuardObservation,TargetGuardFrame

@dataclass(frozen=True)
class MSSelectorObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 names:object=field(default_factory=dict)
 boss_filters:object=field(default_factory=dict)
 actor_guards:object=field(default_factory=dict)
 id_guards:object=field(default_factory=dict)
 def __post_init__(self):
  values=dict(self.values);returns=dict(self.normal_returns);names=dict(self.names)
  if any(type(v) is not int or not 0<=v<=0xffffffff for v in values.values()):raise ValueError('Raw selector DWORD required')
  if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate selector helper normal returns required')
  if any(type(k) is not int or k<0 or type(v) is not str for k,v in names.items()):raise ValueError('Captured final Unicode candidate names required')
  filters=dict(self.boss_filters)
  if any(type(k) is not int or k<0 or not isinstance(v,MSBossFilterObservation) for k,v in filters.items()):raise ValueError('Typed per-candidate boss-filter observations required')
  object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(returns));object.__setattr__(self,'names',MappingProxyType(names))
  object.__setattr__(self,'boss_filters',MappingProxyType(filters))
  for attr in ('actor_guards','id_guards'):
   guards=dict(getattr(self,attr))
   if any(type(k) is not int or k<0 or not isinstance(v,TargetGuardObservation) for k,v in guards.items()):raise ValueError('Typed per-candidate guard observations required')
   object.__setattr__(self,attr,MappingProxyType(guards))

@dataclass(frozen=True)
class MSSelectorPlan:
 complete:bool
 status:str
 return_eax:object=None
 best_id:int=0
 best_pointer:int=0
 best_metric:int=50
 selections:tuple=()
 calls:tuple=()
 reads:tuple=()
 stores:tuple=()
 missing:str=''
 needed:object=None
 stack_ID_source_verified:bool=False
 iterator_ABI_verified:bool=False
 native_execution_verified:bool=False
 boss_filter_children:tuple=()
 guard_children:tuple=()

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def plan_ms_selector(o,*,context=0x56216c,candidate_budget=64,_boss_filter=None,_guard=None):
 if not isinstance(o,MSSelectorObservation):raise ValueError('Typed selector observations required')
 if type(context) is not int or not 0<=context<=0xffffffff:raise ValueError('Raw selector context required')
 if type(candidate_budget) is not int or candidate_budget<1:raise ValueError('Explicit positive own iteration budget required')
 calls=[];reads=[];stores=[];selected=[];children=[];guards=[];best_id=0;best_pointer=0;best_metric=50;result=None
 def finish(status,error=None):
  return MSSelectorPlan(error is None,status,result,best_id,best_pointer,best_metric,tuple(selected),tuple(calls),tuple(reads),tuple(stores),'' if error is None else str(error),None if error is None else error.needed,boss_filter_children=tuple(children),guard_children=tuple(guards))
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def read(label,address,width=4):reads.append((address&0xffffffff,width,label));return value(label)
 def normal(label,helper,args=()):
  calls.append((helper,args,label))
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def dword(label,address):normal(label,'0045dc44',(address&0xffffffff,));return value(label+'_eax')
 def guard(index,kind,argument,label,helper,pushes):
  child=None;mapping=o.actor_guards if kind=='actor' else o.id_guards
  if _guard is not None:child=_guard(index,kind,argument)
  elif index in mapping:child=TargetGuardFrame(kind,argument).advance(mapping[index])
  if child is not None:
   guards.append((index,kind,child))
   if not child.complete:raise _Missing('guard',label)
  normal(label,helper,pushes);eax=value(label+'_eax')
  if child is not None and child.return_eax!=eax:raise ValueError('Guard child full EAX differs from captured outer result')
  return eax
 try:
  normal('frame_setup','opaque_frame_setup');normal('name_init','opaque_UnicodeString_init')
  if read('buffer_check',0x56fb3c)==0:
   normal('allocate','VirtualAlloc',(0x40,0x1000,0x255,0));allocation=value('allocation_eax')
   stores.append((0x56fb3c,4,allocation)) #Source does not guard allocation0.
  root=dword('tree_root',read('tree_root_slot',0x553e8c))
  sentinel=dword('sentinel',(root+0x60)&0xffffffff)
  node=dword('first_node',sentinel)
  buffer=read('buffer_initial_write',0x56fb3c)
  normal('initialize_iterator','0045ddf4',(node,buffer))
  for index in range(candidate_budget):
   pre='n%d.'%index
   actor=dword(pre+'actor',(node+0x14)&0xffffffff)
   state=dword(pre+'state',actor+read(pre+'state_offset',0x554034))
   offset=read(pre+'first_offset',0x554008)
   normal(pre+'first_coordinate','0045ddb8',((actor+offset)&0xffffffff,));first=value(pre+'first_bits')
   offset=read(pre+'second_offset',0x554010)
   normal(pre+'second_coordinate','0045ddb8',((actor+offset)&0xffffffff,));second=value(pre+'second_bits')
   normal(pre+'metric1','00460548',(second,first));normal(pre+'metric1_ftol','source___ftol');metric1=value(pre+'metric1_eax')
   normal(pre+'metric2','004605cc',(second,first,0x425c0000,0x425c0000));normal(pre+'metric2_ftol','source___ftol');metric2=value(pre+'metric2_eax')
   offset=read(pre+'kind_offset',0x554038)
   normal(pre+'kind','0045dbdc',((actor+offset)&0xffffffff,));kind=value(pre+'kind_eax')&255
   if kind!=10 and state not in (5,4,13) and (metric1<=best_metric or metric2<=50):
    storage=dword(pre+'name_storage',actor+read(pre+'name_storage_offset',0x553fec))
    offset=read(pre+'name_data_offset',0x553fe8)
    if storage>=16:address=dword(pre+'name_pointer',actor+offset);count=storage
    else:address=(actor+offset)&0xffffffff;count=50
    if count>512:raise _Missing('unmodeled','source_name_copy_above512')
    normal(pre+'name_copy','0045dca8',(count,address))
    normal(pre+'name_convert_cleanup','opaque_ANSI_to_Unicode_and_cleanup')
    if index not in o.names:raise _Missing('name',str(index))
    name=o.names[index]
    if guard(index,'actor',actor,pre+'actor_guard','00464c2c',(actor,))&255:
     #The two EBP-48 reads have no explicit writer in the covered body.
     #Require source-bound snapshots; do not invent ID from actor pointer.
     reads.append(('EBP-48',4,pre+'stack_id_for_guard'))
     candidate=value(pre+'stack_id_for_guard')
     if guard(index,'id_list',candidate,pre+'target_guard','0040b894',(candidate,0x561f34))&255==1:
      mode=read(pre+'mode_dword',context)
      if mode==0 and metric1<=best_metric:
       child=None
       if _boss_filter is not None:child=_boss_filter(index,name)
       elif index in o.boss_filters:child=MSBossFilterFrame(candidate_name=name,context=context).advance(o.boss_filters[index])
       if child is not None:
        children.append((index,child))
        if not child.complete:raise _Missing('boss_filter',pre+'boss_filter')
       normal(pre+'boss_filter','004c4f64',(name,context))
       filter_al=value(pre+'boss_filter_eax')&255
       if child is not None and child.return_al!=filter_al:raise ValueError('Boss-filter child AL differs from captured outer result')
       if filter_al:
        reads.append(('EBP-48',4,pre+'stack_id_for_selection'));candidate=value(pre+'stack_id_for_selection')
        best_id=candidate;best_pointer=actor;best_metric=metric1;selected.append((index,candidate,actor,metric1))
   iterator_buffer=read(pre+'iterator_buffer',0x56fb3c)
   target=read(pre+'iterator_target',0x553eb0)
   normal(pre+'iterator','indirect_iterator_Pushad_Pushfd',(target,iterator_buffer,()))
   next_buffer=read(pre+'next_buffer',0x56fb3c)
   node=dword(pre+'next_node',next_buffer)
   if node==sentinel:break
  else:raise _Missing('budget','source_iterator_still_open')
  if best_id!=0 and best_id<0x80000000:
   stores.extend(((0x562040,4,best_id),(0x56203c,4,best_pointer),(0x562048,4,0),(0x562044,1,0),(0x56204c,1,1)))
   status='selected';return_value=best_id
  else:
   stores.extend(((0x56204c,1,0),(0x56203c,4,0),(0x562040,4,0)));status='none_selected';return_value=0
  normal('return_cleanup','opaque_UnicodeString_cleanup_and_return');result=return_value
  return finish(status)
 except _Missing as error:return finish('needs_observation',error)

class MSSelectorFrame:
 def __init__(self,*,context=0x56216c,candidate_budget=64):
  self.context=context;self.budget=candidate_budget;self.observation=MSSelectorObservation();self.final=None;self.filters={};self.guards={}
  plan_ms_selector(self.observation,context=context,candidate_budget=candidate_budget)
 def extend_budget(self,new_budget):
  if type(new_budget) is not int or new_budget<=self.budget:raise ValueError('Larger explicit local iteration budget required')
  self.budget=new_budget
 def advance(self,o):
  if not isinstance(o,MSSelectorObservation):raise ValueError('Typed selector observations required')
  if self.final is not None:return self.final
  def boss_filter(index,name):
   if index not in self.filters:
    if 'n%d.boss_filter'%index in self.observation.normal_returns:
     if index in o.boss_filters:raise ValueError('Cannot retroactively bind consumed boss-filter call')
     return None
    if index not in o.boss_filters:return None
    self.filters[index]=MSBossFilterFrame(candidate_name=name,context=self.context)
   frame=self.filters[index]
   if frame.candidate_name!=name:raise ValueError('Consumed boss candidate name changed')
   return frame.advance(o.boss_filters.get(index,MSBossFilterObservation()))
  def guard(index,kind,argument):
   key=(index,kind);mapping=o.actor_guards if kind=='actor' else o.id_guards
   label='n%d.%s'%(index,'actor_guard' if kind=='actor' else 'target_guard')
   if key not in self.guards:
    if label in self.observation.normal_returns:
     if index in mapping:raise ValueError('Cannot retroactively bind consumed guard call')
     return None
    if index not in mapping:return None
    self.guards[key]=TargetGuardFrame(kind,argument)
   frame=self.guards[key]
   if frame.argument!=argument:raise ValueError('Consumed guard argument changed')
   return frame.advance(mapping.get(index,TargetGuardObservation()))
  for _ in range(16384):
   p=plan_ms_selector(self.observation,context=self.context,candidate_budget=self.budget,_boss_filter=boss_filter,_guard=guard)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind in ('budget','unmodeled','boss_filter','guard'):return p
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   elif kind=='name':
    index=int(label)
    if index not in o.names:return p
    self.observation=replace(self.observation,names={**self.observation.names,index:o.names[index]})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('Selector own observation budget exceeded')
