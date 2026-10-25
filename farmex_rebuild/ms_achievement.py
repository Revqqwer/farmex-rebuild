"""004b0380 ->11 sequential004ca958 request attempts, own queue only."""
from dataclasses import dataclass,field
from types import MappingProxyType
from action_queue import QueueState,enqueue
from direct_chat_packets import QueueAttempt

BUTTON_PATH='frmMain/MainTab/sheetMSDraki/GroupBox60/btnAchieveGetMS'
ACHIEVEMENT_IDS=(0x182,0x183,0x184,0x185,0x186,0x187,0x56,0x58,0x65,0x74,0x5f)
TEMPLATE=bytes.fromhex('990200000000')

@dataclass(frozen=True)
class AchievementRequestObservation:
 attempt:QueueAttempt=field(default_factory=QueueAttempt)
 normal_returns:object=field(default_factory=dict)
 def __post_init__(self):
  if not isinstance(self.attempt,QueueAttempt):raise ValueError('Typed achievement queue attempt required')
  returns=dict(self.normal_returns)
  if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate achievement helper normal receipts required')
  object.__setattr__(self,'normal_returns',MappingProxyType(returns))

@dataclass(frozen=True)
class AchievementRequestPlan:
 complete:bool
 identifier:int
 payload:bytes
 queue:QueueState
 missing:str=''
 context:int=0x561ef8
 native_execution_verified:bool=False
 delivery_verified:bool=False
 reward_verified:bool=False

class AchievementRequestFrame:
 def __init__(self,identifier,queue=None):
  if type(identifier) is not int or not 0<=identifier<=0xffffffff:raise ValueError('Raw achievement DWORD required')
  self.identifier=identifier;self.payload=TEMPLATE[:2]+identifier.to_bytes(4,'little')
  self.queue=QueueState() if queue is None else queue
  if not isinstance(self.queue,QueueState):raise ValueError('Own queue required')
  self.normals=set();self.gate=None;self.decision=None;self.final=None
 def advance(self,o):
  if not isinstance(o,AchievementRequestObservation):raise ValueError('Typed achievement request observation required')
  if self.final is not None:return self.final
  def result(missing=''):return AchievementRequestPlan(not missing,self.identifier,self.payload,self.queue,missing)
  for label in ('frame_setup','copy'):
   if label not in self.normals:
    if o.normal_returns.get(label) is not True:return result(label+' normal return')
    self.normals.add(label)
  if self.decision is None:
   if self.gate is None and o.attempt.gate is not None:self.gate=o.attempt.gate
   decision=enqueue(self.queue,self.payload,6,0,self.gate,o.attempt.tick if self.gate else None)
   if decision.state is None:return result(decision.missing)
   self.queue=decision.state;self.decision=decision
  if 'enqueue' not in self.normals:
   if o.attempt.normal_returned is not True:return result('enqueue normal return')
   self.normals.add('enqueue')
  if o.normal_returns.get('return') is not True:return result('helper return span')
  self.final=result();return self.final

@dataclass(frozen=True)
class MSAchievementObservation:
 requests:object=field(default_factory=dict)
 caller_returns:object=field(default_factory=dict)
 event_returned:bool=False
 def __post_init__(self):
  requests=dict(self.requests);returns=dict(self.caller_returns)
  if any(type(k) is not int or not 0<=k<11 or not isinstance(v,AchievementRequestObservation) for k,v in requests.items()):raise ValueError('Typed per-invocation achievement requests required')
  if any(type(k) is not int or not 0<=k<11 or type(v) is not bool for k,v in returns.items()):raise ValueError('Separate per-invocation outer returns required')
  if type(self.event_returned) is not bool:raise ValueError('Separate event return required')
  object.__setattr__(self,'requests',MappingProxyType(requests));object.__setattr__(self,'caller_returns',MappingProxyType(returns))

@dataclass(frozen=True)
class MSAchievementPlan:
 complete:bool
 queue:QueueState
 completed_invocations:tuple=()
 calls:tuple=()
 children:tuple=()
 missing:str=''
 needed:object=None
 native_execution_verified:bool=False
 delivery_verified:bool=False
 reward_verified:bool=False

class MSAchievementFrame:
 def __init__(self,queue=None):
  self.queue=QueueState() if queue is None else queue
  if not isinstance(self.queue,QueueState):raise ValueError('Own queue required')
  self.index=0;self.frames={};self.completed=[];self.calls=[];self.children={};self.final=None
 def result(self,needed=None,missing=''):
  return MSAchievementPlan(needed is None,self.queue,tuple(self.completed),tuple(self.calls),tuple(sorted(self.children.items())),missing,needed)
 def advance(self,o):
  if not isinstance(o,MSAchievementObservation):raise ValueError('Typed MS achievement observations required')
  if self.final is not None:return self.final
  while self.index<len(ACHIEVEMENT_IDS):
   i=self.index;identifier=ACHIEVEMENT_IDS[i]
   if i not in self.frames:
    self.frames[i]=AchievementRequestFrame(identifier,self.queue)
    self.calls.append(('004ca958',(identifier,0x561ef8),i))
   p=self.frames[i].advance(o.requests.get(i,AchievementRequestObservation()))
   self.children[i]=p;self.queue=p.queue
   if not p.complete:return self.result(('request',i),p.missing)
   if o.caller_returns.get(i) is not True:return self.result(('caller_return',i),'request outer normal return')
   self.completed.append(i);self.index+=1
  if o.event_returned is not True:return self.result(('event_return',None),'event epilogue normal return')
  self.final=self.result();return self.final
