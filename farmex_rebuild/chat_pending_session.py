"""Serial own pending/lock/queue state; not native shared-memory scheduling."""
from dataclasses import dataclass,field,replace
from chat_skill_requests import ChatSkillFrame,ChatSkillObservation,SPECS
from chat_skill_consumers import ChatConsumerFrame
from chat_pending_binding import bind_stable_pending_observation,PendingConsumerFrame
from attack_lock import AttackLockState,plan_attack_unlock
from action_queue import QueueState

@dataclass(frozen=True)
class ChatSessionState:
    pending_byte:int=0
    kind_dword:int=0
    sender_dword:int=0
    lock:AttackLockState=field(default_factory=AttackLockState)
    queue:QueueState=field(default_factory=QueueState)
    def __post_init__(self):
        for v,width in ((self.pending_byte,1),(self.kind_dword,4),(self.sender_dword,4)):
            if type(v) is not int or not 0<=v<1<<(8*width):raise ValueError('Raw own session pending fields required')
        if not isinstance(self.lock,AttackLockState) or not isinstance(self.queue,QueueState):raise ValueError('Typed own lock and queue required')

class ChatPendingSession:
    def __init__(self,state=None):
        self.state=ChatSessionState() if state is None else state
        if not isinstance(self.state,ChatSessionState):raise ValueError('Typed initial session required')
        self.active=None;self.active_kind=None;self.family=None
    def _idle(self):
        if self.active is not None:raise ValueError('Finish current own serial transaction before another event')
    def begin_message(self,configuration,message):
        self._idle();frame=ChatSkillFrame(configuration,message)
        self.active=frame;self.active_kind='message'
    def advance_message(self,o):
        if self.active_kind!='message':raise ValueError('Active message transaction required')
        if not isinstance(o,ChatSkillObservation):raise ValueError('Typed message observations required')
        pending=self.state.pending_byte
        if 'pending_byte' in o.values and o.values['pending_byte']!=pending:raise ValueError('Message snapshot conflicts with own pending state')
        p=self.active.advance(replace(o,values={**o.values,'pending_byte':pending}))
        if p.complete:
            if p.queued_request is not None:
                request=p.queued_request;family=next(s[1] for s in SPECS if s[0]==request.key)
                # Reuse exact triplet/base validation before committing any own state.
                PendingConsumerFrame(p,family,0)
                self.state=replace(self.state,pending_byte=1,kind_dword=request.kind,sender_dword=request.sender_dword)
            self.active=None;self.active_kind=None
        return p
    def begin_consumer(self,family,actor_context_dword):
        self._idle();frame=ChatConsumerFrame(family,actor_context_dword)
        self.active=frame;self.active_kind='consumer';self.family=family
    def advance_consumer(self,o):
        if self.active_kind!='consumer':raise ValueError('Active consumer transaction required')
        s=self.state
        p=self.active.advance(bind_stable_pending_observation(o,self.family,s.pending_byte,s.kind_dword,s.sender_dword,s.lock.byte))
        if not p.complete:return p
        # Transactional commit is an own scheduling policy. Source helper effects
        # and Priest's intermediate pre-call clear are retained only in p.stores.
        pending=s.pending_byte;lock=s.lock;queue=s.queue
        for address,width,value in p.stores:
            if address==0x5693a0:
                if width!=1:raise ValueError('Pending source store must be BYTE')
                pending=value
            elif address in (0x561f7e,0x561f80,0x561f84):
                name,expected={0x561f7e:('byte',1),0x561f80:('duration_ms',4),0x561f84:('started_ms',4)}[address]
                if width!=expected:raise ValueError('Source lock store width differs')
                lock=replace(lock,**{name:value})
        if p.direct_execution is not None:
            queue=p.direct_execution.queue;n=len(s.queue.records)
            if queue.records[:n]!=s.queue.records or queue.next_id<s.queue.next_id:
                raise ValueError('Direct child must retain session queue prefix')
        updated=replace(s,pending_byte=pending,lock=lock,queue=queue)
        self.state=updated;self.active=None;self.active_kind=None;self.family=None
        return p
    def apply_reached_unlock_timer(self,clock=None):
        """Caller explicitly enters the timer span; no callback reachability proof."""
        self._idle();p=plan_attack_unlock(self.state.lock,clock)
        if p.complete:self.state=replace(self.state,lock=p.state)
        return p
