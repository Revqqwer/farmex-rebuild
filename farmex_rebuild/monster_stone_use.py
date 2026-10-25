"""004c567c item-scan worker +004ca900 six-byte own queue; no game effects."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState,enqueue
from direct_chat_packets import QueueAttempt
from genie_recovery import GenieRecoveryObservation,GenieRecoveryScanFrame
from bot_switch import BotSwitchObservation,BotSwitchFrame
from monster_stone import MS_ENABLE_INPUT

TARGET=b'Monster Stone'
TEMPLATE=bytes.fromhex('5f0600000000')

def raw(value):
 if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw MS-use DWORD required')

@dataclass(frozen=True)
class MSItemUsePlan:
 complete:bool
 payload:bytes
 queue:QueueState
 missing:str=''
 context:int=0x561ef8
 native_execution_verified:bool=False
 delivery_verified:bool=False

class MSItemUseFrame:
 def __init__(self,item_id,queue=None):
  raw(item_id);self.payload=TEMPLATE[:2]+item_id.to_bytes(4,'little')
  self.queue=QueueState() if queue is None else queue
  if not isinstance(self.queue,QueueState):raise ValueError('Own MS item queue required')
  self.normals=set();self.gate=None;self.decision=None;self.final=None
 def advance(self,attempt,returns):
  if not isinstance(attempt,QueueAttempt) or any(type(v) is not bool for v in returns.values()):raise ValueError('Typed enqueue attempt and normal receipts required')
  if self.final is not None:return self.final
  def result(missing=''):return MSItemUsePlan(not missing,self.payload,self.queue,missing)
  for label in ('item_frame_setup','item_copy'):
   if label not in self.normals:
    if returns.get(label) is not True:return result(label+' normal return')
    self.normals.add(label)
  if self.decision is None:
   if self.gate is None and attempt.gate is not None:self.gate=attempt.gate
   decision=enqueue(self.queue,self.payload,6,0,self.gate,attempt.tick if self.gate else None)
   if decision.state is None:return result(decision.missing)
   self.queue=decision.state;self.decision=decision
  if 'enqueue' not in self.normals:
   if attempt.normal_returned is not True:return result('item enqueue normal return')
   self.normals.add('enqueue')
  if returns.get('item_return_span') is not True:return result('item return span normal return')
  self.final=result();return self.final

@dataclass(frozen=True)
class MSUseObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 scan:object=None
 attempt:QueueAttempt=field(default_factory=QueueAttempt)
 stop_inputs:object=None
 def __post_init__(self):
  values=dict(self.values);returns=dict(self.normal_returns)
  for name,value in values.items():
   raw(value)
   if name.endswith('_byte') and value>255:raise ValueError('Raw MS context BYTE required')
  if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate MS-use normal receipts required')
  if self.scan is not None and not isinstance(self.scan,GenieRecoveryObservation):raise ValueError('Typed fresh inventory scan required')
  if not isinstance(self.attempt,QueueAttempt):raise ValueError('Typed item enqueue attempt required')
  if self.stop_inputs is not None and not isinstance(self.stop_inputs,BotSwitchObservation):raise ValueError('Typed bot stop inputs required')
  object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(returns))

@dataclass(frozen=True)
class MSUsePlan:
 complete:bool
 status:str
 calls:tuple=()
 stores:tuple=()
 ui_updates:tuple=()
 scan:object=None
 item:object=None
 stop:object=None
 missing:str=''
 needed:object=None
 native_execution_verified:bool=False
 MonsterStone_effect_verified:bool=False

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def _plan(o,scan_child,item_child,stop_child):
 calls=[];stores=[];ui=[];scan=None;item=None;stop=None;status='needs_observation'
 def result(error=None):return MSUsePlan(error is None,status,tuple(calls),tuple(stores),tuple(ui),scan,item,stop,'' if error is None else str(error),None if error is None else error.needed)
 def normal(label,helper,args=()):
  calls.append((helper,args,label))
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def tick(label):normal(label,'GetTickCount');return value(label)
 def finish():normal('worker_return','source_normal_epilogue');return result()
 try:
  normal('worker_setup','opaque_frame_setup')
  for i,zone in enumerate((0x51,0x52,0x53),1):
   label='area%d'%i;normal(label,'0046209c')
   if value(label+'_eax')==zone:status='excluded_area';return finish()
  now=tick('cooldown_tick');lo=value('cooldown_low');hi=value('cooldown_high')
  delta=(now-((hi<<32)|lo))&0xffffffffffffffff
  if delta&(1<<63):delta-=1<<64
  if delta<1000:status='cooldown_wait';return finish()
  scan=scan_child()
  if not scan.complete:raise _Missing('scan','inventory')
  if scan.selected_slot is not None:
   item=item_child(scan.item_id)
   if not item.complete:raise _Missing('item','item_use')
   normal('item_use','004ca900',(scan.item_id,0x561ef8));status='item_helper_returned'
  else:
   normal('completion_message_span','opaque_message_and_first_cleanup',(b'Tamamlandi !',))
   normal('disable_checkbox','VCL_Checked_setter',(MS_ENABLE_INPUT,0));ui.append((MS_ENABLE_INPUT,False))
   stop=stop_child()
   if stop is not None and not stop.complete:raise _Missing('stop','bot_stop')
   normal('bot_stop','0040ae0c',(0,0x561f34))
   if value('alarm_byte'):normal('alarm_span','opaque_alarm_and_cleanup',(b'Default',0x569568))
   normal('completion_tail_cleanup','opaque_message_tail_cleanup');status='inventory_exhausted'
  stamp=tick('post_tick');stores.extend(((0x56fb40,4,stamp),(0x56fb44,4,0)))
  return finish()
 except _Missing as error:return result(error)

class MSUseFrame:
 def __init__(self,queue=None,*,owned_byte_compare=False):
  self.queue=QueueState() if queue is None else queue
  if not isinstance(self.queue,QueueState):raise ValueError('Own MS queue required')
  self.scan_frame=GenieRecoveryScanFrame(owned_byte_compare=owned_byte_compare,target_name=TARGET,payload_template=None,frame_setup_required=False)
  self.item_frame=None;self.stop_frame=None;self.observation=MSUseObservation();self.final=None
 def advance(self,o):
  if not isinstance(o,MSUseObservation):raise ValueError('Typed MS-use observations required')
  if self.final is not None:return self.final
  def scan():return self.scan_frame.advance(o.scan or GenieRecoveryObservation())
  def item(item_id):
   if self.item_frame is None:self.item_frame=MSItemUseFrame(item_id,self.queue)
   p=self.item_frame.advance(o.attempt,o.normal_returns);self.queue=p.queue;return p
  def stop():
   if self.stop_frame is None:
    if o.stop_inputs is None:return None
    self.stop_frame=BotSwitchFrame(0x561f34,0)
   return self.stop_frame.advance(o.stop_inputs or BotSwitchObservation())
  for _ in range(64):
   p=_plan(self.observation,scan,item,stop)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind in ('scan','item','stop'):return p
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('MS-use source prefix budget exceeded')
