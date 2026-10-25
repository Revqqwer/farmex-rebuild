"""MS movement115 and target-entry30 instruction operand/normal-path models."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from motion_genie_helpers import MotionGenieObservation,MotionGenieFrame
from monster_stone_selector import MSSelectorObservation,MSSelectorFrame

@dataclass(frozen=True)
class MSCombatObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 motion_inputs:object=None
 selector_inputs:object=None
 def __post_init__(self):
  values=dict(self.values);returns=dict(self.normal_returns)
  for label,value in values.items():
   bits=16 if label.endswith('_ax') else 8 if label.endswith('_byte') else 32
   if type(value) is not int or not 0<=value<1<<bits:raise ValueError('Raw MS combat operand required')
  if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate MS combat normal returns required')
  if self.motion_inputs is not None and not isinstance(self.motion_inputs,MotionGenieObservation):raise ValueError('Typed movement-helper inputs required')
  if self.selector_inputs is not None and not isinstance(self.selector_inputs,MSSelectorObservation):raise ValueError('Typed selector inputs required')
  object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(returns))

@dataclass(frozen=True)
class MSCombatPlan:
 complete:bool
 status:str
 calls:tuple=()
 reads:tuple=()
 stores:tuple=()
 moves:tuple=()
 unused_local_byte:object=None
 motion_child:object=None
 missing:str=''
 needed:object=None
 native_execution_verified:bool=False
 movement_verified:bool=False
 attack_verified:bool=False
 selector_child:object=None

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

class _Planner:
 def __init__(self,o,context):
  if not isinstance(o,MSCombatObservation):raise ValueError('Typed MS combat observations required')
  if type(context) is not int or not 0<=context<=0xffffffff:raise ValueError('Raw MS context required')
  self.o=o;self.context=context;self.calls=[];self.reads=[];self.stores=[];self.moves=[];self.local=None;self.child=None;self.selector=None
 def result(self,status,error=None):
  return MSCombatPlan(error is None,status,tuple(self.calls),tuple(self.reads),tuple(self.stores),tuple(self.moves),self.local,self.child,
   '' if error is None else str(error),None if error is None else error.needed,selector_child=self.selector)
 def value(self,label):
  if label not in self.o.values:raise _Missing('value',label)
  return self.o.values[label]
 def read(self,label,address,width=4):
  self.reads.append((address&0xffffffff,width,label));return self.value(label)
 def normal(self,label,helper,args=()):
  self.calls.append((helper,args,label))
  if self.o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def root(self,prefix):
  slot=self.read(prefix+'_root_slot',0x553e7c)
  self.normal(prefix+'_root','0045dc44',(slot,));return self.value(prefix+'_root_eax')
 def finish(self,status,label):self.normal(label,'source_normal_return');return self.result(status)

def plan_ms_movement(o,*,context=0x56216c,_motion=None):
 p=_Planner(o,context)
 def compare(label,mask):
  ax=p.value(label);p.reads.append(('FNSTSW_AX',16,label,ax,mask));return (ax>>8)&mask
 def move(label,pushes):
  if _motion is not None:p.child=_motion(pushes)
  elif o.motion_inputs is not None:p.child=MotionGenieFrame('004646b4',pushes).advance(o.motion_inputs)
  if p.child is not None and not p.child.complete:raise _Missing('motion',label)
  p.normal(label,'004646b4',pushes);p.moves.append(pushes)
 try:
  if p.read('active_byte',0x561f6c,1)==0:return p.finish('inactive','movement_return')
  for i,wanted in enumerate((0x51,0x52,0x53),1):
   label='area%d'%i;p.normal(label,'0046209c')
   if p.value(label+'_eax')==wanted:break
  else:return p.finish('outside_area','movement_return')
  root=p.root('state');offset=p.read('state_offset',0x55402c)
  p.normal('state','0045dbdc',((root+offset)&0xffffffff,))
  if p.value('state_eax')&255:return p.finish('state_blocked','movement_return')
  root=p.root('float');offset=p.read('float_offset',0x554030)
  p.normal('status_float','0045ddb8',((root+offset)&0xffffffff,))
  if compare('status_compare_ax',0x45)==0:return p.finish('float_gate_blocked','movement_return')
  root=p.root('stance');offset=p.read('stance_offset',0x554034)
  p.normal('stance','0045dc44',((root+offset)&0xffffffff,))
  if p.value('stance_eax')==6:return p.finish('stance_blocked','movement_return')
  if p.read('other_block_byte',0x561f7e,1):return p.finish('other_blocked','movement_return')
  if p.read('no_attack_byte',0x561fa8,1):return p.finish('no_attack_blocked','movement_return')
  if p.read('mode_dword',context)==0:
   p.normal('boss_distance','00460548',(0x425c0000,0x425c0000))
   if compare('boss_compare_ax',0x45)==0:
    move('boss_move',(0x425c0000,0x425c0000));return p.finish('boss_move_returned','movement_return')
  if p.read('follow_byte',context+5,1)==0:return p.finish('follow_disabled','movement_return')
  if p.read('target_available_byte',0x56204c,1)==0:return p.finish('target_unavailable','movement_return')
  target=p.read('target_pointer',0x56203c)
  offset=p.read('first_coordinate_offset',0x554008)
  p.normal('first_coordinate','0045ddb8',((target+offset)&0xffffffff,));first=p.value('first_coordinate_bits')
  offset=p.read('second_coordinate_offset',0x554010)
  p.normal('second_coordinate','0045ddb8',((target+offset)&0xffffffff,));second=p.value('second_coordinate_bits')
  pushes=(second,first)
  p.normal('first_distance','00460548',pushes);p.value('first_distance_float_bits') #Independent FSTP float capture.
  p.normal('second_distance','00460548',pushes)
  if compare('second_distance_compare_ax',0x45):return p.finish('second_distance_blocked','movement_return')
  mask=compare('first_distance_compare_ax',0x41)
  if bin(mask).count('1')%2==0:return p.finish('first_distance_blocked','movement_return') #JP after TEST AH,41.
  move('target_move',pushes);return p.finish('target_move_returned','movement_return')
 except _Missing as error:return p.result('needs_observation',error)

def plan_ms_target_entry(o,*,context=0x56216c,_selector=None):
 p=_Planner(o,context);p.local=0
 try:
  if p.read('active_byte',0x561f6c,1)==0:return p.finish('inactive','target_entry_return')
  if p.read('no_attack_byte',0x561fa8,1):return p.finish('no_attack_blocked','target_entry_return')
  p.local=int(p.read('mode_dword',context)==0) #Source local byte has no later read in this body.
  p.normal('prepare_target','0040b294',(0x561f34,))
  target=p.read('current_target_dword',0x562040)
  p.normal('target_guard','0040b978',(target,0x561f34))
  if p.value('target_guard_eax')&255:
   if _selector is not None:p.selector=_selector()
   elif o.selector_inputs is not None:p.selector=MSSelectorFrame(context=context).advance(o.selector_inputs)
   if p.selector is not None and not p.selector.complete:raise _Missing('selector','select_target')
   p.normal('select_target','004c50d0',(context,));result=p.value('selected_target_eax')
   if p.selector is not None and p.selector.return_eax!=result:raise ValueError('Captured selector EAX differs from generated child')
   p.stores.append((0x562040,4,result))
   return p.finish('target_selected','target_entry_return')
  return p.finish('target_guard_false','target_entry_return')
 except _Missing as error:return p.result('needs_observation',error)

class MSCombatFrame:
 def __init__(self,kind,*,context=0x56216c):
  if kind not in ('movement','target_entry'):raise ValueError('Known MS combat frame required')
  self.kind=kind;self.context=context;self.observation=MSCombatObservation();self.motion=None;self.selector=None;self.final=None
 def advance(self,o):
  if not isinstance(o,MSCombatObservation):raise ValueError('Typed MS combat observations required')
  if self.final is not None:return self.final
  def motion(pushes):
   if self.motion is None:
    if o.motion_inputs is None:return None
    self.motion=MotionGenieFrame('004646b4',pushes)
   if self.motion.push_order!=pushes:raise ValueError('Consumed movement arguments changed')
   return self.motion.advance(o.motion_inputs or MotionGenieObservation())
  def selector():
   if self.selector is None:
    if o.selector_inputs is None:return None
    self.selector=MSSelectorFrame(context=self.context)
   return self.selector.advance(o.selector_inputs or MSSelectorObservation())
  for _ in range(80):
   p=plan_ms_movement(self.observation,context=self.context,_motion=motion) if self.kind=='movement' else plan_ms_target_entry(self.observation,context=self.context,_selector=selector)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind in ('motion','selector'):return p
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('MS combat source observation budget exceeded')
