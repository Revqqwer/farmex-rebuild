"""SELL phase0 caller 420f9e..42104a; own samples/queue only, no game IO."""
from dataclasses import dataclass,replace
from action_queue import QueueState,QueueSample,enqueue

def _raw(v,bits,optional=False):
    if optional and v is None:return
    if type(v) is not int or not 0<=v<1<<bits:raise ValueError('Raw SELL close field required')

@dataclass(frozen=True)
class SellCloseObservation:
    global_samples:tuple=()
    protected_samples:tuple=()
    byte_samples:tuple=()
    close_tick_dword:object=None
    queue_sample:object=None
    enqueue_returned:object=None
    def __post_init__(self):
        for rows in (self.global_samples,self.protected_samples,self.byte_samples):
            if type(rows) is not tuple:raise ValueError('Ordered immutable close samples required')
            for row in rows:
                if type(row) is not tuple or len(row)!=2:raise ValueError('Close address/value pair required')
                _raw(row[0],32);_raw(row[1],32,True)
        _raw(self.close_tick_dword,32,True)
        if self.queue_sample is not None and not isinstance(self.queue_sample,QueueSample):raise ValueError('Typed queue sample required')
        if self.enqueue_returned is not None and type(self.enqueue_returned) is not bool:raise ValueError('Explicit enqueue normal return required')

@dataclass(frozen=True)
class SellCloseProbePlan:
    complete:bool
    is_open:object=None
    buy_mode:object=None
    reads:tuple=()
    missing:str=''
    independently_verified:bool=False

def plan_sell_close_probe(o):
    if not isinstance(o,SellCloseObservation):raise ValueError('Typed close observations required')
    positions={'global':0,'protected':0,'byte':0};reads=[];opened=None;buy=None
    class Missing(Exception):pass
    def sample(kind,at):
        at&=0xffffffff;i=positions[kind];rows=getattr(o,kind+'_samples')
        if i>=len(rows):raise Missing('%s sample%d at%08x'%(kind,i,at))
        address,value=rows[i]
        if address!=at:raise ValueError('Close %s sample%d address mismatch'%(kind,i))
        positions[kind]+=1;reads.append((kind,at,value))
        if value is None:raise Missing('%s sample%d value'%(kind,i))
        return value
    def g(at):return sample('global',at)
    try:
        root=sample('protected',g(0x553e7c))
        opened=(sample('byte',root+g(0x554148))&255)==1
        if opened:
            fresh_root=sample('protected',g(0x553e7c))
            buy=(sample('byte',fresh_root+g(0x55414c))&255)==1
        return SellCloseProbePlan(True,opened,buy,tuple(reads))
    except Missing as e:return SellCloseProbePlan(False,opened,buy,tuple(reads),str(e))

@dataclass(frozen=True)
class SellCloseState:
    phase_dword:int=0
    pending_byte:int=0
    close_stamp_qword:int=0
    def __post_init__(self):
        _raw(self.phase_dword,32);_raw(self.pending_byte,8);_raw(self.close_stamp_qword,64)

@dataclass(frozen=True)
class SellCloseDecision:
    complete:bool
    status:str
    state:SellCloseState
    prospective_state:SellCloseState
    queue:QueueState
    prospective_queue:QueueState
    probe:object=None
    payload:bytes=b''
    writes:tuple=()
    steps:tuple=()
    missing:str=''
    independently_verified:bool=False

def _known(before,after):
    if before is None:return after
    if after is not None and after!=before:raise ValueError('Changed known close observation')
    return before

def _merge_samples(a,b):
    out=[]
    for i in range(max(len(a),len(b))):
        if i>=len(a):out.append(b[i]);continue
        if i>=len(b):out.append(a[i]);continue
        if a[i][0]!=b[i][0]:raise ValueError('Changed close observation address')
        out.append((a[i][0],_known(a[i][1],b[i][1])))
    return tuple(out)

class SellCloseFrame:
    def __init__(self,state,queue):
        if not isinstance(state,SellCloseState) or state.phase_dword!=0:raise ValueError('Reached SELL phase0 state required')
        if not isinstance(queue,QueueState):raise ValueError('Typed local queue required')
        self.entry=state;self.candidate=state;self.entry_queue=queue;self.queue=queue
        self.observation=SellCloseObservation();self.probe=None;self.payload=b''
        self.writes=[];self.steps=[];self.stage=0;self.queue_done=False;self.done=False;self.status='needs_observation'
    def result(self,missing=''):
        return SellCloseDecision(self.done,self.status,self.candidate if self.done else self.entry,self.candidate,
            self.queue if self.done else self.entry_queue,self.queue,self.probe,self.payload,
            tuple(self.writes),tuple(self.steps),missing)
    def step(self,o=None):
        if o is not None and not isinstance(o,SellCloseObservation):raise ValueError('Typed close observation required')
        if self.done:return self.result()
        a=self.observation;b=o or SellCloseObservation();q=a.queue_sample;r=b.queue_sample
        if q is not None and r is not None:
            q=QueueSample(_known(q.tick,r.tick),_known(q.connection_gate,r.connection_gate),
                          _known(q.sender_returned,r.sender_returned))
        else:q=q or r
        returned=b.enqueue_returned if b.enqueue_returned is not None else a.enqueue_returned
        if a.enqueue_returned is True and returned is False:raise ValueError('Changed completed enqueue return')
        self.observation=SellCloseObservation(_merge_samples(a.global_samples,b.global_samples),
            _merge_samples(a.protected_samples,b.protected_samples),_merge_samples(a.byte_samples,b.byte_samples),
            _known(a.close_tick_dword,b.close_tick_dword),q,returned);o=self.observation
        if self.stage==0:
            self.probe=plan_sell_close_probe(o)
            if not self.probe.complete:return self.result(self.probe.missing)
            if not self.probe.is_open:
                self.candidate=replace(self.candidate,phase_dword=1);self.writes.append((4,4,1))
                self.done=True;self.status='no_close_required';return self.result()
            self.payload=b'\x68\x27' if self.probe.buy_mode else b'\x68\x02'
            self.candidate=replace(self.candidate,pending_byte=1);self.writes.append((0x18,1,1))
            self.steps.append(('GetTickCount',));self.stage=1
        if self.stage==1:
            if o.close_tick_dword is None:return self.result('close pending GetTickCount')
            self.candidate=replace(self.candidate,close_stamp_qword=o.close_tick_dword)
            self.writes.append((0x20,8,o.close_tick_dword));self.steps.append(('004c7710',self.payload,2,0));self.stage=2
        if not self.queue_done:
            q=o.queue_sample or QueueSample()
            decision=enqueue(self.queue,self.payload,2,0,q.connection_gate,q.tick)
            if decision.state is None:return self.result('close local queue: '+decision.missing)
            self.queue=decision.state;self.queue_done=True
        if o.enqueue_returned is not True:return self.result('close enqueue helper normal return')
        self.candidate=replace(self.candidate,phase_dword=1);self.writes.append((4,4,1))
        self.done=True;self.status='close_prepared';return self.result()
