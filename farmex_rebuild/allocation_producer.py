"""00457700..00457c5f stat/skill list producer replay; no native UI/container IO."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from source_integer import SourceIntegerObservation,SourceIntegerFrame
from auto_allocation import ROOT

ALLOCATION_LISTS={'stat':ROOT+'LwAutoStat','skill':ROOT+'LwAutoSkill'}

@dataclass(frozen=True)
class AllocationRow:
 name_bytes:bytes
 action_dword:int
 threshold_dword:int
 source_index:int

@dataclass(frozen=True)
class AllocationProducerObservation:
 entry_reached:bool=False
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 texts:object=field(default_factory=dict)
 names:object=field(default_factory=dict)
 integer_inputs:object=field(default_factory=dict)
 def __post_init__(self):
  if type(self.entry_reached) is not bool:raise ValueError('Explicit bounded producer entry required')
  groups={k:dict(getattr(self,k)) for k in ('values','normal_returns','texts','names','integer_inputs')}
  if any(type(v) is not int or not 0<=v<=0xffffffff for v in groups['values'].values()):raise ValueError('Raw list producer DWORD required')
  if any(type(v) is not bool for v in groups['normal_returns'].values()):raise ValueError('Separate list producer normal returns required')
  if any(type(v) is not str for v in groups['texts'].values()):raise ValueError('Captured Unicode list text required')
  if any(type(v) is not bytes for v in groups['names'].values()):raise ValueError('Captured final ANSI name bytes required')
  if any(not isinstance(v,SourceIntegerObservation) for v in groups['integer_inputs'].values()):raise ValueError('Typed integer conversion child required')
  for k,v in groups.items():object.__setattr__(self,k,MappingProxyType(v))

@dataclass(frozen=True)
class AllocationProducerPlan:
 complete:bool
 status:str
 stat_rows:tuple=()
 skill_rows:tuple=()
 cleared_vectors:tuple=()
 stores:tuple=()
 calls:tuple=()
 conversions:tuple=()
 missing:str=''
 needed:object=None
 whole_producer_verified:bool=False
 codec_verified:bool=False
 native_execution_verified:bool=False

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def signed(v):return v if v<0x80000000 else v-0x100000000

def plan_allocation_producer(o,*,context=0x562194,row_budget=64,_integer=None,_fast_end=None):
 if not isinstance(o,AllocationProducerObservation):raise ValueError('Typed allocation producer observation required')
 if type(context) is not int or not 0<=context<=0xffffffff:raise ValueError('Raw producer context required')
 if type(row_budget) is not int or row_budget<1:raise ValueError('Positive local row budget required')
 rows={'stat':[],'skill':[]};cleared=[];stores=[];calls=[];conversions=[]
 def result(status,error=None):
  return AllocationProducerPlan(error is None,status,tuple(rows['stat']),tuple(rows['skill']),tuple(cleared),tuple(stores),tuple(calls),tuple(conversions),
   '' if error is None else str(error),None if error is None else error.needed)
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def normal(label,helper,args=()):
  calls.append((helper,args,label))
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def text(label):
  if label not in o.texts:raise _Missing('text',label)
  return o.texts[label]
 def integer(label,source):
  child=_integer(label,source) if _integer is not None else SourceIntegerFrame(source,0xffffffff).advance(o.integer_inputs.get(label,SourceIntegerObservation()))
  conversions.append((label,child))
  if not child.complete:raise _Missing('integer',label)
  normal(label,'0045ef80',(0xffffffff,source))
  return child.low_dword
 try:
  if not o.entry_reached:raise _Missing('entry','00457700')
  for domain,offset,form in (('stat',0x20,0xf48),('skill',0x21,0xf4c)):
   normal(domain+'_enabled','VCL_Checked_getter_span',('form_field',form))
   stores.append(((context+offset)&0xffffffff,1,value(domain+'_enabled_eax')&255))
  for domain,vector_offset,form in (('stat',0x28,0xf40),('skill',0x48,0xf44)):
   normal(domain+'_clear','opaque_begin_end_004589e8_erase_span',((context+vector_offset)&0xffffffff,))
   cleared.append(domain)
   for index in range(row_budget):
    pre='%s%d.'%(domain,index)
    normal(pre+'count','VCL_ListItems_Count',('form_field',form))
    if signed(value(pre+'count_eax'))<=index:break
    normal(pre+'row_init','00404148')
    normal(pre+'name_get','0045f6e0',('form_field',form,index,0));source=text(pre+'name')
    normal(pre+'name_conversion_cleanup','opaque_004073a0_AnsiString_assignment_cleanup',(source,))
    if pre+'name' not in o.names:raise _Missing('name',pre+'name')
    name=o.names[pre+'name']
    normal(pre+'caption_get','0045f7f4',('form_field',form,index))
    action=integer(pre+'action_integer',text(pre+'caption'))
    normal(pre+'caption_cleanup','00505c64')
    normal(pre+'threshold_get','0045f6e0',('form_field',form,index,1))
    threshold=integer(pre+'threshold_integer',text(pre+'threshold'))
    normal(pre+'threshold_cleanup','00505c64')
    normal(pre+'size','00458a98',((context+vector_offset)&0xffffffff,));size=value(pre+'size_eax')
    normal(pre+'capacity','00458ac0',((context+vector_offset)&0xffffffff,));capacity=value(pre+'capacity_eax')
    row=AllocationRow(name,action,threshold,index)
    if size<capacity:
     end=value(pre+'end_dword')
     normal(pre+'fast_append','00458ae8',(row,1,end,(context+vector_offset)&0xffffffff))
     new_end=(end+12)&0xffffffff #Normal-return helper tail: end+12*count; caller count is1.
     observed=_fast_end(pre+'new_end_eax',new_end) if _fast_end is not None else o.values.get(pre+'new_end_eax',new_end)
     if observed!=new_end:raise ValueError('Captured fast append EAX contradicts source end+12')
     stores.append(((context+vector_offset+0x14)&0xffffffff,4,new_end))
    else:normal(pre+'reallocate','opaque_end_iterator_00458b4c_insert_span',(row,(context+vector_offset)&0xffffffff))
    rows[domain].append(row)
    normal(pre+'row_cleanup','004040f8')
   else:raise _Missing('budget',domain+'_UI_count_still_open')
  return result('next_general_settings_span_reached')
 except _Missing as error:return result('needs_observation',error)

class AllocationProducerFrame:
 def __init__(self,*,context=0x562194,row_budget=64):
  self.context=context;self.budget=row_budget;self.observation=AllocationProducerObservation();self.children={};self.fast_returns={};self.final=None
  plan_allocation_producer(self.observation,context=context,row_budget=row_budget)
 def extend_budget(self,new_budget):
  if type(new_budget) is not int or new_budget<=self.budget:raise ValueError('Larger explicit row budget required')
  self.budget=new_budget
 def advance(self,o):
  if not isinstance(o,AllocationProducerObservation):raise ValueError('Typed allocation producer observation required')
  if self.final is not None:return self.final
  def integer(label,source):
   if label not in self.children:self.children[label]=SourceIntegerFrame(source,0xffffffff)
   frame=self.children[label]
   if frame.text!=source:raise ValueError('Consumed integer text changed')
   return frame.advance(o.integer_inputs.get(label,SourceIntegerObservation()))
  def fast_end(label,expected):
   if label not in self.fast_returns:
    if o.values.get(label,expected)!=expected:raise ValueError('Captured fast append EAX contradicts source end+12')
    self.fast_returns[label]=expected
   return self.fast_returns[label]
  for _ in range(32768):
   p=plan_allocation_producer(self.observation,context=self.context,row_budget=self.budget,_integer=integer,_fast_end=fast_end)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind in ('integer','budget'):return p
   if kind=='entry':
    if not o.entry_reached:return p
    self.observation=replace(self.observation,entry_reached=True)
   elif kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    group={'value':'values','text':'texts','name':'names'}[kind];incoming=getattr(o,group)
    if label not in incoming:return p
    self.observation=replace(self.observation,**{group:{**getattr(self.observation,group),label:incoming[label]}})
  raise ValueError('Allocation producer own observation budget exceeded')
