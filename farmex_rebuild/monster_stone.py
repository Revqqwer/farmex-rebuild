"""MS33-instruction setting producer and28-instruction enable callback models."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from bot_switch import BotSwitchObservation,BotSwitchFrame

ROOT='frmMain/MainTab/sheetMSDraki/GroupBox60/'
MS_SETTING_INPUTS=(ROOT+'GroupBox50/rdMSEndMob',ROOT+'GroupBox50/rdMSAllMob',ROOT+'chAnyMSEndAlarm')
MS_ENABLE_INPUT=ROOT+'chEnableMSMode'
WALLHACK_INPUT='frmMain/MainTab/SheetGenel/GroupBox48/chwh'

def raw(value,optional=False):
 if optional and value is None:return
 if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw MS DWORD required')

@dataclass(frozen=True)
class MSObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 bot_start_inputs:object=None
 def __post_init__(self):
  values=dict(self.values);returns=dict(self.normal_returns)
  for value in values.values():raw(value)
  if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate MS helper normal receipts required')
  if self.bot_start_inputs is not None and not isinstance(self.bot_start_inputs,BotSwitchObservation):raise ValueError('Typed bot start child inputs required')
  object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(returns))

@dataclass(frozen=True)
class MSPlan:
 complete:bool
 stores:tuple=()
 calls:tuple=()
 ui_updates:tuple=()
 mode_after:object=None
 missing:str=''
 needed:object=None
 bot_start:object=None
 native_execution_verified:bool=False
 MonsterStone_effect_verified:bool=False

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

class _Plan:
 def __init__(self,o):
  if not isinstance(o,MSObservation):raise ValueError('Typed MS observations required')
  self.o=o;self.stores=[];self.calls=[];self.ui=[];self.mode=None;self.child=None
 def normal(self,label,helper,args=()):
  self.calls.append((helper,args,label))
  if self.o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def getter(self,label):
  self.normal(label,'VCL_Checked_getter')
  if label+'_eax' not in self.o.values:raise _Missing('value',label+'_eax')
  return self.o.values[label+'_eax']&255
 def result(self,error=None):
  return MSPlan(error is None,tuple(self.stores),tuple(self.calls),tuple(self.ui),self.mode,
   '' if error is None else str(error),None if error is None else error.needed,self.child)

def plan_ms_settings(o,*,previous_mode=None,context=0x56216c):
 raw(previous_mode,True);raw(context);p=_Plan(o);p.mode=previous_mode
 try:
  if p.getter('boss'):
   p.mode=0;p.stores.append((context,4,0))
  elif p.getter('all_mobs'):
   p.mode=1;p.stores.append((context,4,1))
  alarm=p.getter('alarm');p.stores.append(((context+4)&0xffffffff,1,alarm))
  p.normal('settings_return','source_normal_return_span')
  return p.result()
 except _Missing as error:return p.result(error)

def plan_ms_activation(o,*,_bot_start=None):
 p=_Plan(o)
 try:
  if p.getter('enabled'):
   p.normal('wallhack_setter','VCL_Checked_setter',(WALLHACK_INPUT,1))
   p.ui.append((WALLHACK_INPUT,True));p.stores.append((0x561f5c,4,1))
   if _bot_start is not None:p.child=_bot_start()
   elif o.bot_start_inputs is not None:p.child=BotSwitchFrame(0x561f34,1).advance(o.bot_start_inputs)
   if p.child is not None and not p.child.complete:raise _Missing('child','bot_start')
   p.normal('bot_start','0040ae0c',(1,0x561f34))
  else:p.stores.append((0x561f5c,4,0))
  p.normal('activation_return','source_normal_return_span')
  return p.result()
 except _Missing as error:return p.result(error)

class MSFrame:
 def __init__(self,*,activation=False,previous_mode=None,context=0x56216c):
  if type(activation) is not bool:raise ValueError('Explicit MS frame kind required')
  raw(previous_mode,True);raw(context)
  self.activation=activation;self.previous_mode=previous_mode;self.context=context
  self.observation=MSObservation();self.child=None;self.final=None
 def advance(self,o):
  if not isinstance(o,MSObservation):raise ValueError('Typed MS observations required')
  if self.final is not None:return self.final
  def child():
   if self.child is None:
    if o.bot_start_inputs is None:return None
    self.child=BotSwitchFrame(0x561f34,1)
   return self.child.advance(o.bot_start_inputs or BotSwitchObservation())
  for _ in range(24):
   p=plan_ms_activation(self.observation,_bot_start=child) if self.activation else plan_ms_settings(self.observation,previous_mode=self.previous_mode,context=self.context)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind=='child':return p
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('MS source observation budget exceeded')

def compile_ms_settings(values,*,previous_mode=None):
 def checked(path):
  v=values.get(path)
  if type(v) is not bool:raise ValueError('MS source checkbox/radio boolean required: '+path)
  return int(v)
 boss=checked(MS_SETTING_INPUTS[0]);v={'boss_eax':boss}
 if not boss:v['all_mobs_eax']=checked(MS_SETTING_INPUTS[1])
 v['alarm_eax']=checked(MS_SETTING_INPUTS[2])
 return plan_ms_settings(MSObservation(v,{k:True for k in ('boss','all_mobs','alarm','settings_return')}),previous_mode=previous_mode)
