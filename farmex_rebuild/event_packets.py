"""Event helper serializers and inert queue prefixes; no native or network IO."""
from dataclasses import dataclass,field
from types import MappingProxyType
from action_queue import QueueState,enqueue
from direct_chat_packets import QueueAttempt

FIRST_TEMPLATES={'chaos':bytes.fromhex('5f081800'),'bdw_nation2':bytes.fromhex('5f080200'),
 'bdw_other':bytes.fromhex('5f080100'),'royale':bytes.fromhex('b70701')}
DIRECT_TEMPLATES={0x5212e0:bytes.fromhex('55000e31333031355f497269732e6c7561'),
 0x5212f1:bytes.fromhex('55000f32393139305f45726579612e6c7561'),
 0x521303:bytes.fromhex('55000f32343433385f4c756775722e6c7561'),
 0x521315:bytes.fromhex('55001031343433385f42656c64616e2e6c7561')}
TARGET_TEMPLATE=bytes.fromhex('200100000000ffffffff')

@dataclass(frozen=True)
class EventEnqueuePlan:
 complete:bool
 payload:bytes
 delay:int
 queue:QueueState
 missing:str=''
 needed:object=None
 native_execution_verified:bool=False
 delivery_verified:bool=False

class EventEnqueueFrame:
 def __init__(self,payload,delay,queue=None):
  if type(payload) is not bytes or type(delay) is not int or not 0<=delay<=0xffffffff:raise ValueError('Immutable payload/raw delay required')
  self.payload=payload;self.delay=delay;self.queue=QueueState() if queue is None else queue
  if not isinstance(self.queue,QueueState):raise ValueError('Own event queue required')
  self.gate=None;self.decision=None;self.final=None
 def advance(self,o):
  if not isinstance(o,QueueAttempt):raise ValueError('Typed event enqueue attempt required')
  if self.final is not None:return self.final
  def result(kind=None,label=''):return EventEnqueuePlan(kind is None,self.payload,self.delay,self.queue,label,None if kind is None else (kind,label))
  if self.decision is None:
   if self.gate is None:self.gate=o.gate
   if self.gate is None:return result('gate','connection gate')
   if self.gate and o.tick is None:return result('tick','GetTickCount')
   d=enqueue(self.queue,self.payload,len(self.payload),self.delay,self.gate,o.tick if self.gate else None)
   if d.state is None:raise ValueError('Bounded event enqueue unexpectedly unresolved')
   self.decision=d;self.queue=d.state
  if o.normal_returned is not True:return result('normal','enqueue normal return')
  self.final=result();return self.final

@dataclass(frozen=True)
class EventPacketObservation:
 values:object=field(default_factory=dict)
 normal_returns:object=field(default_factory=dict)
 attempt:QueueAttempt=field(default_factory=QueueAttempt)
 def __post_init__(self):
  v=dict(self.values);n=dict(self.normal_returns)
  if any(type(x) is not int or not 0<=x<=0xffffffff for x in v.values()):raise ValueError('Raw event packet DWORD required')
  if any(type(x) is not bool for x in n.values()) or not isinstance(self.attempt,QueueAttempt):raise ValueError('Separate packet returns and typed attempt required')
  object.__setattr__(self,'values',MappingProxyType(v));object.__setattr__(self,'normal_returns',MappingProxyType(n))

@dataclass(frozen=True)
class EventPacketPlan:
 complete:bool
 kind:str
 payload:object
 queue:QueueState
 missing:str=''
 needed:object=None
 native_execution_verified:bool=False
 event_admission_verified:bool=False

class EventPacketFrame:
 def __init__(self,kind,queue=None,*,target=None):
  if kind not in ('chaos','bdw','royale','target_prepare'):raise ValueError('Known event packet helper required')
  if kind=='target_prepare' and (type(target) is not int or not 0<=target<=0xffffffff):raise ValueError('Raw target preparation DWORD required')
  self.target=target
  self.kind=kind;self.queue=QueueState() if queue is None else queue
  if not isinstance(self.queue,QueueState):raise ValueError('Own event queue required')
  self.normals=set();self.nation=None;self.payload=None;self.enqueue_frame=None;self.final=None
 def advance(self,o):
  if not isinstance(o,EventPacketObservation):raise ValueError('Typed event packet observations required')
  if self.final is not None:return self.final
  def result(kind=None,label=''):return EventPacketPlan(kind is None,self.kind,self.payload,self.queue,label,None if kind is None else (kind,label))
  def normal(label):
   if label not in self.normals:
    if o.normal_returns.get(label) is not True:return False
    self.normals.add(label)
   return True
  if not normal('frame_setup'):return result('normal','frame_setup')
  if self.kind=='bdw' and self.nation is None:
   if not normal('nation'):return result('normal','nation')
   if 'nation_eax' not in o.values:return result('value','nation_eax')
   self.nation=o.values['nation_eax']
  if self.payload is None:
   if self.kind=='target_prepare':
    if not normal('template_copy'):return result('normal','template_copy')
    self.payload=TARGET_TEMPLATE[:2]+self.target.to_bytes(4,'little')+TARGET_TEMPLATE[6:]
   else:
    key=('bdw_nation2' if self.nation==2 else 'bdw_other') if self.kind=='bdw' else self.kind
    self.payload=FIRST_TEMPLATES[key]
  copy_label='target_copy' if self.kind=='target_prepare' else 'copy'
  if not normal(copy_label):return result('normal',copy_label)
  if self.enqueue_frame is None:self.enqueue_frame=EventEnqueueFrame(self.payload,0,self.queue)
  child=self.enqueue_frame.advance(o.attempt);self.queue=child.queue
  if not child.complete:return result('enqueue',child.missing)
  if not normal('return'):return result('normal','return')
  self.final=result();return self.final
