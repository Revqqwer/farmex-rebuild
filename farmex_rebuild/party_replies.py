"""004ca770/004ca7b4 three-byte local reply plans, never sent."""
from dataclasses import dataclass
from action_queue import QueueState,QueueDecision,enqueue

PAYLOADS={'accept':bytes.fromhex('2f0201'),'reject':bytes.fromhex('2f0200')}

@dataclass(frozen=True)
class PartyReplyPlan:
    complete:bool
    action:str
    payload:bytes
    queue_decision:object=None
    missing:str=''
    native_execution_verified:bool=False
    def __post_init__(self):
        if self.action not in PAYLOADS or type(self.payload) is not bytes or self.payload!=PAYLOADS[self.action]:raise ValueError('Exact source reply kind/payload required')
        if type(self.complete) is not bool:raise ValueError('Known reply plan completion required')
        if self.complete and (not isinstance(self.queue_decision,QueueDecision) or self.queue_decision.state is None):raise ValueError('Known own enqueue outcome required before complete reply plan')

class PartyReplyFrame:
    def __init__(self,action,queue=None):
        if action not in PAYLOADS:raise ValueError('Source accept/reject action required')
        self.action=action;self.queue=QueueState() if queue is None else queue;self.final=None
        if not isinstance(self.queue,QueueState):raise ValueError('Own reply queue required')
    def advance(self,gate=None,tick=None):
        if self.final is not None:return self.final
        data=PAYLOADS[self.action];d=enqueue(self.queue,data,3,0,gate,tick)
        p=PartyReplyPlan(d.state is not None,self.action,data,d,d.missing)
        if d.state is not None:self.queue=d.state;self.final=p
        return p
