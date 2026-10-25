"""0046ee14 captured control-flow replay with optional generated MS children."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from monster_stone_use import MSUseFrame,MSUseObservation
from monster_stone_combat import MSCombatFrame,MSCombatObservation
from action_queue import QueueState
from genie_worker import GenieWorkerObservation,GenieWorkerFrame
from notice_genie_window import NoticeGenieObservation
from auto_allocation import AutoAllocationObservation,AutoAllocationFrame

@dataclass(frozen=True)
class MainGenieObservation:
 prefix:GenieWorkerObservation=field(default_factory=GenieWorkerObservation)
 notice:object=None
 def __post_init__(self):
  if not isinstance(self.prefix,GenieWorkerObservation):raise ValueError('Typed general Genie prefix required')
  if self.notice is not None and not isinstance(self.notice,NoticeGenieObservation):raise ValueError('Typed reached Notice tail required')

CHILD_TYPES={'ms_use':MSUseObservation,'ms_movement':MSCombatObservation,'ms_target':MSCombatObservation,'genie_worker':MainGenieObservation,'common_genie':AutoAllocationObservation}

@dataclass(frozen=True)
class MainWorkerObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 children:object=field(default_factory=dict)
 def __post_init__(self):
  values=dict(self.values);normals=dict(self.normal_returns);children=dict(self.children)
  for k,v in values.items():
   bits=8 if k.endswith('_byte') else 32
   if type(v) is not int or not 0<=v<1<<bits:raise ValueError('Raw main-worker operand required')
  if any(type(v) is not bool for v in normals.values()):raise ValueError('Separate main-worker normal returns required')
  if any(k not in CHILD_TYPES or not isinstance(v,CHILD_TYPES[k]) for k,v in children.items()):raise ValueError('Known typed main-worker child required')
  object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(normals));object.__setattr__(self,'children',MappingProxyType(children))

@dataclass(frozen=True)
class MainWorkerPlan:
 complete:bool
 status:str
 calls:tuple=()
 reads:tuple=()
 stores:tuple=()
 children:tuple=()
 comparisons:tuple=()
 missing:str=''
 needed:object=None
 whole_worker_verified:bool=False
 native_execution_verified:bool=False
 live_compatibility_verified:bool=False

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def _signed(v,bits):return v if v<1<<(bits-1) else v-(1<<bits)

def plan_main_worker(o,*,_child=None):
 if not isinstance(o,MainWorkerObservation):raise ValueError('Typed main-worker observation required')
 calls=[];reads=[];stores=[];children=[];comparisons=[]
 def result(status,error=None):
  return MainWorkerPlan(error is None,status,tuple(calls),tuple(reads),tuple(stores),tuple(children),tuple(comparisons),
   '' if error is None else str(error),None if error is None else error.needed)
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def read(label,address,width=4):reads.append((address,width,label));return value(label)
 def flag(label,address):return read(label,address,1)
 def call(label,helper,pushes=()):
  calls.append((helper,pushes,label))
  child=None
  if label in CHILD_TYPES:
   if _child is not None:child=_child(label)
   elif label in o.children:
    if label=='genie_worker':
     inputs=o.children[label];child=GenieWorkerFrame().advance(inputs.prefix,inputs.notice)
    elif label=='common_genie':child=AutoAllocationFrame().advance(o.children[label])
    else:
     frame=MSUseFrame() if label=='ms_use' else MSCombatFrame('movement' if label=='ms_movement' else 'target_entry')
     child=frame.advance(o.children[label])
   if child is not None:
    children.append((label,child))
    if not child.complete:raise _Missing('child',label)
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def tick(label):call(label,'GetTickCount');return value(label+'_eax')
 def elapsed(now,lo,hi):return _signed((now-((hi<<32)|lo))&0xffffffffffffffff,64)
 def stamp(low,now):stores.extend(((low,4,now),(low+4,4,0)))
 def finish(status):call('worker_return','source_normal_epilogue');return result(status)
 try:
  call('frame_setup','opaque_504c08')
  call('prelude','00416c10',(0x5622ac,))
  if flag('enabled_byte',0x561f60)==0:return finish('disabled')
  if flag('exclusive_byte',0x561f6f):
   call('exclusive','004eb154',(0x5687a8,));return finish('exclusive_return')
  if flag('notice_first_byte',0x568d33) and flag('notice_second_byte',0x568d80):
   now=tick('notice_tick');lo=read('notice_low',0x561fbc);hi=read('notice_high',0x561fc0)
   delta=elapsed(now,lo,hi);comparisons.append(('notice_elapsed_signed64',delta,1000))
   if delta>=1000:call('notice_span','opaque_004040bc_004ebcbc_004040f8',(0x527af8,0x5687a8))
   return finish('notice_return')
  if read('pre_mode_dword',0x561f5c)==0 and flag('pre_flag_byte',0x568d81):call('pre_mode_zero','004eb2c4',(0x5687a8,))
  if flag('first_active_byte',0x561f6c):call('active_prelude','004ed3a0',(0x5687a8,))
  if read('route_mode_dword',0x561f5c)==0 and flag('route_active_byte',0x561f6c):call('route','0046d30c',(0x5690f8,))
  now=tick('activity_tick')
  lo=read('activity_zero_low',0x5620a4);hi=read('activity_zero_high',0x5620a8)
  delta=elapsed(now,lo,hi);comparisons.append(('activity_zero_check_signed64',delta,0))
  if delta!=0:
   if read('interval_check_dword',0x5620cc)==0:
    call('initial_interval','00467cc4',(0x493e0,0xea60));stores.append((0x5620cc,4,value('initial_interval_eax')))
   lo=read('activity_low',0x5620a4);hi=read('activity_high',0x5620a8)
   delta=elapsed(now,lo,hi);threshold=_signed(read('activity_interval_dword',0x5620cc),32)
   comparisons.append(('activity_elapsed_gt_signed_interval',delta,threshold))
   if delta>threshold:
    lo=read('periodic_low',0x5620d4);hi=read('periodic_high',0x5620d8)
    delta=elapsed(now,lo,hi);threshold=_signed(read('periodic_interval_dword',0x5620cc),32)
    comparisons.append(('periodic_elapsed_ge_signed_interval',delta,threshold))
    if delta>=threshold:
     call('periodic_guard','0046ebd0')
     if value('periodic_guard_eax')&255==0 or flag('periodic_flag_byte',0x555e23)==0:
      pointer=read('callback_argument_dword',0x554218)
      call('periodic_callback','0046b8fc',(0x46eca8,pointer,0x554228))
     stamp(0x5620d4,now)
     call('next_interval','00467cc4',(0x493e0,0xea60));stores.append((0x5620cc,4,value('next_interval_eax')))
  if read('ms_mode_dword',0x561f5c)==1 and flag('ms_block_byte',0x561f70)==0:
   if flag('ms_use_active_byte',0x561f6c):call('ms_use','004c567c',(0x56216c,))
   if flag('ms_movement_active_byte',0x561f6c):call('ms_movement','004c54c8',(0x56216c,))
  if flag('combat_enabled_byte',0x561f6e)==0:return finish('combat_disabled')
  if flag('combat_block_byte',0x561f70):return finish('combat_blocked')
  if read('general_mode_dword',0x561f5c)==0:
   call('general_probe','004645e4')
   if _signed(value('general_probe_eax'),32)>0:call('general_positive','004cb9b4',(0x569584,))
   if flag('genie_active_byte',0x561f6c):call('genie_worker','0045a05c',(0x562194,))
   call('general_a','0040f274',(0x561f34,));call('general_b','0040fc1c',(0x561f34,))
  call('common_genie','00458df8',(0x562194,))
  for label,helper in (('common_a','0040f204'),('common_b','0040f458'),('common_c','0040f53c')):call(label,helper,(0x561f34,))
  if read('idle_mode_dword',0x561f5c)==0 and flag('idle_flag_byte',0x56224c):
   call('idle_genie','004631c8')
   if value('idle_genie_eax')&255==0 and flag('idle_other_byte',0x568d81)==0:return finish('idle_return')
  call('priority_first','004fe3a0',(0x5690b8,))
  if value('priority_first_eax')&255==0:
   call('priority_second','0046fe90',(0x5690e0,))
   if value('priority_second_eax')&255==0:
    if read('target_mode_zero_dword',0x561f5c)==0:
     call('general_target','0040d224',(0x561f34,));call('general_attack','0040e2c0',(0x561f34,))
    elif read('target_mode_one_dword',0x561f5c)==1:
     for i,area in enumerate((0x51,0x52,0x53),1):
      label='target_area%d'%i;call(label,'0046209c')
      if value(label+'_eax')==area:
       call('ms_target','004c5468',(0x56216c,));break
    else:read('target_mode_two_dword',0x561f5c) #Source comparison has no effect before shared tail.
  call('common_tail','0040d554',(0x561f34,))
  return finish('tail_return')
 except _Missing as error:return result('needs_observation',error)

class MainWorkerFrame:
 def __init__(self,queue=None,*,owned_byte_compare=False):
  self.observation=MainWorkerObservation();self.frames={};self.final=None
  self.queue=QueueState() if queue is None else queue
  if not isinstance(self.queue,QueueState):raise ValueError('Own queue required')
  self.owned_byte_compare=owned_byte_compare
 def advance(self,o):
  if not isinstance(o,MainWorkerObservation):raise ValueError('Typed main-worker observation required')
  if self.final is not None:return self.final
  def child(label):
   if label not in self.frames:
    if label in self.observation.normal_returns:
     if label in o.children:raise ValueError('Cannot retroactively bind a consumed opaque main-worker call')
     return None
    if label not in o.children:return None
    if label=='genie_worker':self.frames[label]=GenieWorkerFrame(self.queue)
    elif label=='common_genie':self.frames[label]=AutoAllocationFrame()
    else:self.frames[label]=MSUseFrame(self.queue,owned_byte_compare=self.owned_byte_compare) if label=='ms_use' else MSCombatFrame('movement' if label=='ms_movement' else 'target_entry')
   frame=self.frames[label];inputs=o.children.get(label,CHILD_TYPES[label]())
   p=frame.advance(inputs.prefix,inputs.notice) if label=='genie_worker' else frame.advance(inputs)
   if label in ('ms_use','genie_worker'):self.queue=frame.queue
   return p
  for _ in range(160):
   p=plan_main_worker(self.observation,_child=child)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind=='child':return p
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('Main-worker source observation budget exceeded')
