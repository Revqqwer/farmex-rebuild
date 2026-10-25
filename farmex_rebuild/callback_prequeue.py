"""46f520..46f8be normal-path control replay; no native/helper/queue execution."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState
from event_callback import EventCallbackObservation,EventCallbackFrame
from callback_lifecycle import CallbackLifecycleObservation,CallbackLifecycleFrame
from disconnect_routine import DisconnectRoutineObservation,DisconnectRoutineFrame

LIFECYCLE_KINDS={'ready':'ready','prelude1':'stamp','prelude2':'switch'}

@dataclass(frozen=True)
class CallbackPreQueueObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 lifecycle_children:object=field(default_factory=dict)
 disconnected:object=None
 def __post_init__(self):
  v=dict(self.values);n=dict(self.normal_returns)
  if any(type(x) is not int or not 0<=x<1<<(8 if k.endswith('_byte') else 16 if k.endswith('_ax') else 32) for k,x in v.items()):raise ValueError('Raw callback BYTE/AX/DWORD required')
  if any(type(x) is not bool for x in n.values()):raise ValueError('Separate prequeue normal receipts required')
  object.__setattr__(self,'values',MappingProxyType(v));object.__setattr__(self,'normal_returns',MappingProxyType(n))
  children=dict(self.lifecycle_children)
  if any(k not in LIFECYCLE_KINDS or not isinstance(v,CallbackLifecycleObservation) for k,v in children.items()):raise ValueError('Typed callback lifecycle children required')
  object.__setattr__(self,'lifecycle_children',MappingProxyType(children))
  if self.disconnected is not None and not isinstance(self.disconnected,DisconnectRoutineObservation):raise ValueError('Typed disconnected routine child required')

@dataclass(frozen=True)
class CallbackPreQueuePlan:
 complete:bool
 status:str
 reads:tuple=()
 calls:tuple=()
 stores:tuple=()
 next_source_address:object=None
 queue_consumer_reached:bool=False
 missing:str=''
 needed:object=None
 whole_callback_verified:bool=False
 callback_return_verified:bool=False
 native_execution_verified:bool=False
 queue_effect_verified:bool=False
 FPU_semantics_verified:bool=False
 children:tuple=()

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def signed(v,bits):return v if v<1<<(bits-1) else v-(1<<bits)

def plan_callback_prequeue(o,*,_child=None):
 if not isinstance(o,CallbackPreQueueObservation):raise ValueError('Typed callback prequeue observations required')
 reads=[];calls=[];stores=[];queue_reached=False;children=[]
 def result(status,error=None,next_at=None):return CallbackPreQueuePlan(error is None,status,tuple(reads),tuple(calls),tuple(stores),next_at,queue_reached,'' if error is None else str(error),None if error is None else error.needed,children=tuple(children))
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def read(label,address,width=4):reads.append((address&0xffffffff,width,label));return value(label)
 def flag(label,address):return read(label+'_byte',address,1)!=0
 def normal(label,helper,args=()):
  calls.append((helper,args,label))
  child=None
  if _child is not None:child=_child(label)
  elif label in o.lifecycle_children:child=CallbackLifecycleFrame(LIFECYCLE_KINDS[label]).advance(o.lifecycle_children[label])
  elif label=='disconnected_worker' and o.disconnected is not None:
   child=DisconnectRoutineFrame(context=0x562194).advance(replace(o.disconnected,boundary=replace(o.disconnected.boundary,entry_reached=True)))
  if child is not None:
   children.append((label,child))
   if not child.complete:raise _Missing('child',label)
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def guarded(label,address):normal(label,'0045dc44',(address&0xffffffff,));return value(label+'_eax')
 def tick(label):normal(label,'GetTickCount');return value(label+'_eax')
 def store(address,width,v):stores.append((address,width,v))
 def cleanup(status):return result(status,next_at=0x46fb09)
 def direct_exit(status):normal('direct_SEH_restore','captured_SEH_restore');return result(status,next_at=0x46fb2f)
 def reset_recovery():store(0x56221d,1,0)
 def bot(label,helper):normal(label,helper,(1,0x561f34)) #Physical PUSH order.
 def coordinates(prefix):
  read(prefix+'.y_integer',0x562004);normal(prefix+'.y_fstp','captured_FILD_FSTP');y=value(prefix+'.y_bits')
  read(prefix+'.x_integer',0x562000);normal(prefix+'.x_fstp','captured_FILD_FSTP');x=value(prefix+'.x_bits')
  return y,x
 try:
  normal('entry_setup','opaque_SEH_setup')
  slot=read('header1_slot',0x553f3c);root=guarded('header1_root',slot)
  offset=read('header1_offset',0x5541a0);first=guarded('header1_field',root+offset)
  slot=read('header2_slot',0x553f64);root=guarded('header2_root',slot)
  offset=read('header2_offset',0x5541e4);second=guarded('header2_field',root+offset)
  normal('ready','0046edb0')
  ready=value('ready_eax');ready_child=dict(children).get('ready')
  if ready_child is not None:
   if ready&255!=ready_child.return_al:raise ValueError('Readiness child differs from caller AL')
   if ready_child.return_eax is not None and ready!=ready_child.return_eax:raise ValueError('Readiness child differs from known full EAX')
  if ready&255==0:return cleanup('not_ready')
  normal('prelude1','0046eccc');normal('prelude2','0046ed60')
  if flag('profile_enabled',0x561f55):normal('profile_refresh','00408be0',(0x56209c,))
  normal('connection','00462738')
  if value('connection_eax')!=1:
   normal('disconnected_worker','00459970',(0x562194,));return cleanup('connection_not_one')
  if flag('pending',0x562208):
   if first==0 and second==0:
    store(0x562208,1,0);now=tick('pending_tick');store(0x562214,4,now);store(0x562218,4,0)
    normal('pending_ui_setter','opaque_VCL_setter',(0x478,1));store(0x56221d,1,1)
   return direct_exit('pending_exit')
  if flag('recovery',0x56221d):
   now=tick('recovery_tick');lo=read('recovery_low',0x562214);hi=read('recovery_high',0x562218)
   if signed((now-((hi<<32)|lo))&0xffffffffffffffff,64)<=5000:return cleanup('recovery_wait')
   low=read('recovery_toggle_byte',0x56228c,1);push=value('recovery_toggle_push_ecx')
   if push&255!=low:raise ValueError('Captured PUSH ECX low byte differs from source MOV CL')
   normal('recovery_toggle','00464678',(push,));normal('recovery_prepare','004f6314',(0x5680bc,))
   if flag('flag_562202',0x562202):
    store(0x562202,1,0);reset_recovery();normal('recovery_ui_setter','opaque_VCL_setter',(0x458,1))
    return direct_exit('recovery_UI_exit')
   mode=read('recovery_mode_first',0x561f58)
   if mode!=0:
    if read('recovery_mode_second',0x561f58)==2:
     reset_recovery()
     if flag('restore_bot',0x56222c):bot('mode2_stop','0040ae0c')
    return cleanup('recovery_other_mode')
   if not flag('recovery_setup_done',0x56221c):
    normal('recovery_setup','00459fb0',(0x562194,));store(0x56221c,1,1)
   if flag('exclusive',0x561f6f):
    if flag('exclusive_restore_bot',0x56222c):bot('exclusive_start','0040ac18')
    reset_recovery();return cleanup('recovery_exclusive')
   if not flag('combat_active',0x561f6e):return cleanup('recovery_combat_disabled')
   if not flag('return_coordinates',0x56222d):
    reset_recovery()
    if flag('no_coordinates_restore_bot',0x56222c):bot('no_coordinates_stop','0040ae0c')
    return cleanup('recovery_no_coordinates')
   pushes=coordinates('distance_input');normal('distance','00460548',pushes)
   normal('distance_ftol','captured_ftol');distance=value('distance_eax')
   normal('compare1','captured_FPU_compare');ax=value('compare1_ax')
   if (ax>>8)&0x45==0 and signed(distance,32)<50:
    pushes=coordinates('movement_input');normal('movement','004646b4',pushes);return cleanup('recovery_move')
   normal('compare2','captured_FPU_compare');ax=value('compare2_ax')
   parity_even=bin((ax>>8)&5).count('1')%2==0
   if not parity_even:
    slot=read('actor_slot',0x553e7c);root=guarded('actor_root',slot);offset=read('actor_state_offset',0x554020)
    normal('actor_state','0045dbdc',((root+offset)&0xffffffff,))
    if value('actor_state_eax')&255:return cleanup('recovery_actor_busy')
    normal('recovery_arrival','00459fb0',(0x562194,))
    if flag('arrival_restore_bot',0x56222c):bot('arrival_stop','0040ae0c')
    reset_recovery();return cleanup('recovery_arrival')
   bot('distance_start','0040ac18')
   normal('notice_construct','opaque_ANSI_literal_constructor')
   handle=value('notice_string_handle');normal('notice_dispatch','004ebcbc',(handle,0x5687a8))
   normal('notice_cleanup','004040f8');reset_recovery();return cleanup('recovery_notice')
  if first==0 and flag('guard_profile_enabled',0x561f55):
   normal('fixed_guard','0046f33c')
   if value('fixed_guard_eax')&255:return cleanup('fixed_guard_exit')
  normal('work_queue','00458c70',(0x562194,));queue_reached=True
  normal('queue_consumer','004c79a0',(0x561ef8,))
  return result('post_queue_boundary',next_at=0x46f8be)
 except _Missing as error:return result('needs_observation',error)

class CallbackPreQueueFrame:
 def __init__(self):self.observation=CallbackPreQueueObservation();self.final=None;self.frames={}
 def advance(self,o):
  if not isinstance(o,CallbackPreQueueObservation):raise ValueError('Typed callback prequeue observations required')
  for label in o.lifecycle_children:
   if self.observation.normal_returns.get(label) is True and label not in self.frames:raise ValueError('Cannot retroactively bind opaque callback prelude')
  if o.disconnected is not None and self.observation.normal_returns.get('disconnected_worker') is True and 'disconnected_worker' not in self.frames:raise ValueError('Cannot retroactively bind opaque disconnected worker')
  if self.final is not None:return self.final
  def child(label):
   if label=='disconnected_worker':
    if label not in self.frames:
     if o.disconnected is None:return None
     self.frames[label]=DisconnectRoutineFrame(context=0x562194)
    observed=o.disconnected or DisconnectRoutineObservation()
    return self.frames[label].advance(replace(observed,boundary=replace(observed.boundary,entry_reached=True)))
   if label not in self.frames:
    if label not in o.lifecycle_children:return None
    self.frames[label]=CallbackLifecycleFrame(LIFECYCLE_KINDS[label])
   return self.frames[label].advance(o.lifecycle_children.get(label,CallbackLifecycleObservation()))
  for _ in range(512):
   p=plan_callback_prequeue(self.observation,_child=child)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind=='child':return p
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('Own callback prequeue observation budget exceeded')

@dataclass(frozen=True)
class CallbackEntryEventObservation:
 pre:CallbackPreQueueObservation=field(default_factory=CallbackPreQueueObservation)
 post:EventCallbackObservation=field(default_factory=EventCallbackObservation)
 post_drain_queue:object=None
 def __post_init__(self):
  if not isinstance(self.pre,CallbackPreQueueObservation) or not isinstance(self.post,EventCallbackObservation):raise ValueError('Typed callback segment observations required')
  if self.post_drain_queue is not None and not isinstance(self.post_drain_queue,QueueState):raise ValueError('Explicit own post-drain QueueState required')

@dataclass(frozen=True)
class CallbackEntryEventPlan:
 complete:bool
 pre:CallbackPreQueuePlan
 post:object=None
 queue:object=None
 next_source_address:object=None
 missing:str=''
 needed:object=None
 whole_callback_verified:bool=False
 callback_return_verified:bool=False
 native_execution_verified:bool=False

class CallbackEntryEventFrame:
 def __init__(self):self.pre=CallbackPreQueueFrame();self.post=None;self.final=None
 def advance(self,o):
  if not isinstance(o,CallbackEntryEventObservation):raise ValueError('Typed callback entry/event observation required')
  if self.final is not None:return self.final
  pre=self.pre.advance(o.pre)
  if not pre.complete:return CallbackEntryEventPlan(False,pre,missing=pre.missing,needed=('pre',pre.needed))
  if pre.next_source_address!=0x46f8be:
   self.final=CallbackEntryEventPlan(True,pre,next_source_address=pre.next_source_address);return self.final
  if self.post is None:
   if o.post_drain_queue is None:return CallbackEntryEventPlan(False,pre,next_source_address=0x46f8be,missing='fresh own queue after consumer return',needed=('queue_state','post_drain'))
   self.post=EventCallbackFrame(queue=o.post_drain_queue)
  post=self.post.advance(replace(o.post,entry_reached=True))
  result=CallbackEntryEventPlan(post.complete,pre,post,post.queue,post.next_source_address,post.missing,None if post.complete else ('post',post.needed))
  if post.complete:self.final=result
  return result
