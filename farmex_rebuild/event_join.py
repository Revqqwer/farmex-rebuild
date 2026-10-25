"""45a4dc event replay with optional generated own packet/queue children."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState
from direct_chat_packets import QueueAttempt
from event_packets import EventPacketObservation,EventPacketFrame,EventEnqueueFrame,DIRECT_TEMPLATES
from event_target_fallback import EventFallbackObservation,EventFallbackFrame

ROOT='frmMain/MainTab/SheetGenel/GroupBox40/'
# Source read/store order, deliberately not visual form order.
EVENT_FIELDS=(('chaos','chChaosJoin',0x68,0x540),('ft','chFTJoin',0x69,0x544),
 ('utc','chUTCJoin',0x6a,0x54c),('royale','chKnightRoyaleJoin',0x6b,0x550),
 ('jr','chJRJoin',0x6c,0x548),('bdw','chBDWJoin',0x6d,0x53c))
EVENT_JOIN_INPUTS=tuple(ROOT+name for key,name,offset,slot in EVENT_FIELDS)

def compile_event_join(values):
 result={}
 for path,(_,name,offset,slot) in zip(EVENT_JOIN_INPUTS,EVENT_FIELDS):
  v=values.get(path)
  if type(v) is not bool:raise ValueError('Known event checkbox boolean required: '+path)
  result[offset]=int(v)
 return MappingProxyType(result)

@dataclass(frozen=True)
class EventSettingsObservation:
 entry_reached:bool=False
 getter_returns:tuple=()
 getter_eax:tuple=()
 def __post_init__(self):
  if type(self.entry_reached) is not bool:raise ValueError('Explicit bounded event settings entry required')
  if type(self.getter_returns) is not tuple or type(self.getter_eax) is not tuple or max(len(self.getter_returns),len(self.getter_eax))>6:raise ValueError('Six ordered event getters required')
  if any(v is not None and type(v) is not bool for v in self.getter_returns):raise ValueError('Separate event getter returns required')
  if any(v is not None and (type(v) is not int or not 0<=v<=0xffffffff) for v in self.getter_eax):raise ValueError('Raw event getter EAX required')

@dataclass(frozen=True)
class EventSettingsPlan:
 complete:bool
 stores:tuple=()
 missing:str=''
 next_source_address:int=0x457d02
 whole_producer_verified:bool=False
 native_execution_verified:bool=False

class EventSettingsFrame:
 def __init__(self,*,context=0x562194):
  if type(context) is not int or not 0<=context<=0xffffffff:raise ValueError('Raw event settings context required')
  self.context=context;self.entry=False;self.index=0;self.returned=False;self.stores=[]
 def advance(self,o):
  if not isinstance(o,EventSettingsObservation):raise ValueError('Typed event settings observations required')
  if not self.entry:
   if not o.entry_reached:return EventSettingsPlan(False,tuple(self.stores),'bounded settings entry')
   self.entry=True
  while self.index<6:
   i=self.index
   if not self.returned:
    if i>=len(o.getter_returns) or o.getter_returns[i] is not True:return EventSettingsPlan(False,tuple(self.stores),'getter%d normal return'%i)
    self.returned=True
   if i>=len(o.getter_eax) or o.getter_eax[i] is None:return EventSettingsPlan(False,tuple(self.stores),'getter%d EAX'%i)
   self.stores.append(((self.context+EVENT_FIELDS[i][2])&0xffffffff,1,o.getter_eax[i]&255))
   self.index+=1;self.returned=False
  return EventSettingsPlan(True,tuple(self.stores))

@dataclass(frozen=True)
class EventJoinObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 packet_children:object=field(default_factory=dict)
 enqueue_children:object=field(default_factory=dict)
 fallback_child:object=None
 def __post_init__(self):
  v=dict(self.values);n=dict(self.normal_returns)
  if any(type(x) is not int or not 0<=x<1<<(8 if k.endswith('_byte') else 32) for k,x in v.items()):raise ValueError('Raw event BYTE/DWORD required')
  if any(type(x) is not bool for x in n.values()):raise ValueError('Separate event normal receipts required')
  object.__setattr__(self,'values',MappingProxyType(v));object.__setattr__(self,'normal_returns',MappingProxyType(n))
  packets=dict(self.packet_children);enqueues=dict(self.enqueue_children)
  if any(k not in ('chaos_join','bdw_join','royale_join','target_prepare') or not isinstance(v,EventPacketObservation) for k,v in packets.items()):raise ValueError('Typed reached event packet children required')
  if any(k not in ('ft_enqueue','utc_enqueue','jr_enqueue0','jr_enqueue200') or not isinstance(v,QueueAttempt) for k,v in enqueues.items()):raise ValueError('Typed reached direct event enqueue children required')
  object.__setattr__(self,'packet_children',MappingProxyType(packets));object.__setattr__(self,'enqueue_children',MappingProxyType(enqueues))
  if self.fallback_child is not None and not isinstance(self.fallback_child,EventFallbackObservation):raise ValueError('Typed event fallback child required')

@dataclass(frozen=True)
class EventJoinPlan:
 complete:bool
 status:str
 reads:tuple=()
 calls:tuple=()
 enqueue_requests:tuple=()
 stores:tuple=()
 missing:str=''
 needed:object=None
 native_execution_verified:bool=False
 event_admission_verified:bool=False
 queue_effect_verified:bool=False
 children:tuple=()
 queue:object=None

class _Missing(Exception):
 def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def event_child_frame(label,helper,args,queue):
 if label=='target_fallback':
  if helper!='00464a20' or args:raise ValueError('Target fallback source binding differs')
  return EventFallbackFrame(queue)
 if label=='target_prepare':
  if helper!='004c8f7c' or len(args)!=2 or args[1]!=0x561ef8:raise ValueError('Target preparation source binding differs')
  return EventPacketFrame('target_prepare',queue,target=args[0])
 if label in ('chaos_join','bdw_join','royale_join'):
  expected={'chaos_join':'004c7e48','bdw_join':'004c7e84','royale_join':'004c7ee8'}[label]
  if helper!=expected or args!=(0x561ef8,):raise ValueError('Event packet child source binding differs')
  return EventPacketFrame(label.split('_')[0],queue)
 if helper!='004c7710' or len(args)!=4 or args[3]!=0x561ef8:raise ValueError('Event enqueue source binding differs')
 delay,length,descriptor,context=args
 if type(descriptor) is not tuple or descriptor[0]!='copied_template' or descriptor[2]!=length:raise ValueError('Copied event template binding required')
 payload=DIRECT_TEMPLATES[descriptor[1]]
 if len(payload)!=length:raise ValueError('Event template length differs')
 return EventEnqueueFrame(payload,delay,queue)

def plan_event_join(o,*,context=0x562194,queue=None,_child=None):
 if not isinstance(o,EventJoinObservation):raise ValueError('Typed event observations required')
 if type(context) is not int or not 0<=context<=0xffffffff:raise ValueError('Raw event context required')
 queue=QueueState() if queue is None else queue
 if not isinstance(queue,QueueState):raise ValueError('Own event queue required')
 reads=[];calls=[];requests=[];stores=[];children=[]
 def result(status,error=None):return EventJoinPlan(error is None,status,tuple(reads),tuple(calls),tuple(requests),tuple(stores),'' if error is None else str(error),None if error is None else error.needed,children=tuple(children),queue=queue)
 def value(label):
  if label not in o.values:raise _Missing('value',label)
  return o.values[label]
 def read(label,address,width=4):reads.append((address&0xffffffff,width,label));return value(label)
 def flag(label,offset):return read(label+'_byte',context+offset,1)!=0
 def normal(label,helper,args=()):
  nonlocal queue
  calls.append((helper,args,label))
  child=None
  if _child is not None:child=_child(label,helper,args)
  elif label=='target_fallback' and o.fallback_child is not None:
   child=event_child_frame(label,helper,args,queue).advance(o.fallback_child)
  elif label in o.packet_children or label in o.enqueue_children:
   frame=event_child_frame(label,helper,args,queue)
   child=frame.advance(o.packet_children[label] if label in o.packet_children else o.enqueue_children[label])
  if child is not None:
   children.append((label,child));queue=child.queue
   if not child.complete:raise _Missing('child',label)
  if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
 def tick(label):normal(label,'GetTickCount');return value(label+'_eax')
 def elapsed(prefix):
  now=tick(prefix+'_tick');lo=read(prefix+'_low',0x553d04);hi=read(prefix+'_high',0x553d08)
  difference=(now-((hi<<32)|lo))&0xffffffffffffffff
  return difference if difference<1<<63 else difference-(1<<64)
 def stamp(prefix):
  now=tick(prefix+'_post_tick');stores.extend(((0x553d04,4,now),(0x553d08,4,0)))
 def enqueue(label,template,length,delay):
  requests.append((label,template,length,delay))
  # The source pushes a local copied buffer, not the template's disk VA.
  normal(label,'004c7710',(delay,length,('copied_template',template,length),0x561ef8))
 def finish(status):normal('return','source_normal_return');return result(status)
 try:
  normal('entry_setup','opaque_SEH_setup')
  first=flag('first_chaos',0x68) or flag('first_bdw',0x6d) or flag('first_royale',0x6b)
  if first and elapsed('first')<=200:
   if flag('priority_chaos',0x68):normal('chaos_join','004c7e48',(0x561ef8,))
   elif flag('priority_bdw',0x6d):normal('bdw_join','004c7e84',(0x561ef8,))
   elif flag('priority_royale',0x6b):normal('royale_join','004c7ee8',(0x561ef8,))
   stamp('first')
  second=flag('second_ft',0x69) or flag('second_utc',0x6a) or flag('second_jr',0x6c)
  if not second:return finish('second_group_disabled')
  if elapsed('second')<=200:return finish('second_group_wait')
  normal('target_first','00462630');target=value('target_first_eax')
  invalid=target<=3000
  if not invalid:
   normal('target_second','00462630');invalid=value('target_second_eax')==0
  if invalid:normal('target_fallback','00464a20')
  else:
   normal('target_third','00462630');target=value('target_third_eax')
   normal('target_prepare','004c8f7c',(target,0x561ef8)) #Physical PUSH order.
   if flag('priority_ft',0x69):
    normal('ft_copy','captured_template_copy');enqueue('ft_enqueue',0x5212e0,17,0)
   elif flag('priority_utc',0x6a):
    normal('utc_copy','captured_template_copy');enqueue('utc_enqueue',0x5212f1,18,0)
   elif flag('priority_jr',0x6c):
    normal('nation','00462690');nation=value('nation_eax')
    template,length=(0x521303,18) if nation==1 else (0x521315,19)
    normal('jr_copy','captured_template_copy')
    enqueue('jr_enqueue0',template,length,0);enqueue('jr_enqueue200',template,length,200)
  stamp('second')
  return finish('second_group_returned')
 except _Missing as error:return result('needs_observation',error)

class EventJoinFrame:
 def __init__(self,*,context=0x562194,queue=None):
  self.context=context;self.observation=EventJoinObservation();self.final=None
  self.queue=QueueState() if queue is None else queue;self.frames={}
  plan_event_join(self.observation,context=context,queue=self.queue)
 def advance(self,o):
  if not isinstance(o,EventJoinObservation):raise ValueError('Typed event observations required')
  for label in set(o.packet_children)|set(o.enqueue_children)|({'target_fallback'} if o.fallback_child is not None else set()):
   if self.observation.normal_returns.get(label) is True and label not in self.frames:raise ValueError('Cannot retroactively bind completed opaque event helper')
  if self.final is not None:return self.final
  def child(label,helper,args):
   if label not in self.frames:
    if label not in o.packet_children and label not in o.enqueue_children and not (label=='target_fallback' and o.fallback_child is not None):return None
    self.frames[label]=event_child_frame(label,helper,args,self.queue)
   frame=self.frames[label]
   if isinstance(frame,EventFallbackFrame):observation=o.fallback_child or EventFallbackObservation()
   else:observation=o.packet_children.get(label,EventPacketObservation()) if isinstance(frame,EventPacketFrame) else o.enqueue_children.get(label,QueueAttempt())
   p=frame.advance(observation);self.queue=p.queue;return p
  for _ in range(512):
   p=plan_event_join(self.observation,context=self.context,queue=self.queue,_child=child)
   if p.complete:self.final=p;return p
   kind,label=p.needed
   if kind=='child':return p
   if kind=='normal':
    if o.normal_returns.get(label) is not True:return p
    self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
   else:
    if label not in o.values:return p
    self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
  raise ValueError('Own event observation budget exceeded')
