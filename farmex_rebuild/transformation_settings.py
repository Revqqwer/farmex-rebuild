"""0040929a..004094ad bounded producer replay; external StrToInt not emulated."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from transformation import SKILLS

@dataclass(frozen=True)
class TransformationSettingsObservation:
 entry_reached:bool=False
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 wait_text:object=None
 parser_route:object=None
 def __post_init__(self):
  if type(self.entry_reached) is not bool:raise ValueError('Explicit bounded producer entry receipt required')
  values=dict(self.values);returns=dict(self.normal_returns)
  if any(type(v) is not int or not 0<=v<=0xffffffff for v in values.values()):raise ValueError('Raw source getter/parser DWORD required')
  if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate producer helper normal returns required')
  if self.wait_text is not None and type(self.wait_text) is not str:raise ValueError('Captured Unicode wait text required')
  if self.parser_route not in (None,'normal','exception_unresolved'):raise ValueError('Explicit parser normal/unknown exception route required')
  object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(returns))

@dataclass(frozen=True)
class TransformationSettingsPlan:
 complete:bool
 status:str
 stores:tuple=()
 calls:tuple=()
 selected_skill:object=None
 milliseconds_dword:object=None
 missing:str=''
 needed:object=None
 whole_producer_verified:bool=False
 lexical_conversion_verified:bool=False
 periodic_consumer_verified:bool=False
 native_execution_verified:bool=False

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def plan_transformation_settings(o,*,context=0x562050):
 if not isinstance(o,TransformationSettingsObservation):raise ValueError('Typed transformation producer observation required')
 if type(context) is not int or not 0<=context<=0xffffffff:raise ValueError('Raw producer context required')
 stores=[];calls=[];skill=None;millis=None
 def result(status,error=None):
  return TransformationSettingsPlan(error is None,status,tuple(stores),tuple(calls),skill,millis,
   '' if error is None else str(error),None if error is None else error.needed)
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def normal(label,helper,args=()):
  calls.append((helper,args,label))
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def store(offset,width,value):stores.append(((context+offset)&0xffffffff,width,value))
 try:
  if not o.entry_reached:raise _Missing('entry','0040929a')
  normal('enabled','VCL_Checked_getter_span',('form_field',0x4c0))
  store(0x20,1,value('enabled_eax')&255);store(0x21,1,1)
  normal('text_init','00404a78')
  normal('wait_text','VCL_Text_getter_span',('form_field',0x4cc))
  if o.wait_text is None:raise _Missing('text','wait_text')
  if o.parser_route is None:raise _Missing('route','parser_route')
  if o.parser_route=='exception_unresolved':raise _Missing('unmodeled','StrToInt_exception_unwind')
  normal('parser','rtl_StrToInt32',(o.wait_text,))
  millis=(value('parser_eax')*1000)&0xffffffff;store(0x28,4,millis)
  normal('wait_cleanup','00505c64',('wait_text_temporary',))
  normal('route','VCL_Checked_getter_span',('form_field',0x4c4))
  store(0x22,1,value('route_eax')&255)
  normal('combo','VCL_ItemIndex_getter_span',('form_field',0x4c8))
  index=value('combo_eax');skill=SKILLS[index] if index<18 else SKILLS[0]
  store(0x24,4,skill)
  return result('next_producer_span_reached')
 except _Missing as error:return result('needs_observation',error)

class TransformationSettingsFrame:
 def __init__(self,*,context=0x562050):
  self.context=context;self.observation=TransformationSettingsObservation();self.final=None
  plan_transformation_settings(self.observation,context=context)
 def advance(self,o):
  if not isinstance(o,TransformationSettingsObservation):raise ValueError('Typed transformation producer observation required')
  if self.final is not None:return self.final
  for _ in range(24):
   p=plan_transformation_settings(self.observation,context=self.context)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind=='unmodeled':return p
   if kind=='entry':
    if not o.entry_reached:return p
    self.observation=replace(self.observation,entry_reached=True)
   elif kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   elif kind=='value':
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
   else:
    v=getattr(o,label)
    if v is None:return p
    self.observation=replace(self.observation,**{label:v})
  raise ValueError('Transformation producer observation budget exceeded')
