"""421279..42134b own resumable handoff after setup result0 and gate+58!=0."""
from dataclasses import dataclass,replace
from action_queue import QueueState,QueueSample,enqueue
from merchant_sell_tail import SellSlotState

SEED=bytes.fromhex('6801')

def _raw(value,bits,optional=False):
    if optional and value is None:return
    if type(value) is not int or not 0<=value<1<<bits:raise ValueError('Raw SELL session field required')

@dataclass(frozen=True)
class SellSessionState:
    phase_dword:int=2
    setup_gate_byte:int=1
    ready_byte:int=0
    session_stamp_qword:int=0
    list_index_dword:int=0
    inventory_slot_dword:int=14
    slot:SellSlotState=SellSlotState()
    def __post_init__(self):
        for name,bits in (('phase_dword',32),('setup_gate_byte',8),('ready_byte',8),
                          ('session_stamp_qword',64),('list_index_dword',32),('inventory_slot_dword',32)):
            _raw(getattr(self,name),bits)
        if not isinstance(self.slot,SellSlotState):raise ValueError('Typed own slot state required')

@dataclass(frozen=True)
class SellSessionObservation:
    session_tick_dword:object=None
    queue_sample:object=None
    enqueue_returned:object=None
    def __post_init__(self):
        _raw(self.session_tick_dword,32,True)
        if self.queue_sample is not None and not isinstance(self.queue_sample,QueueSample):raise ValueError('Typed session queue sample required')
        if self.enqueue_returned is not None and type(self.enqueue_returned) is not bool:raise ValueError('Explicit enqueue normal return required')

@dataclass(frozen=True)
class SellSessionDecision:
    complete:bool
    state:SellSessionState
    prospective_state:SellSessionState
    queue:QueueState
    prospective_queue:QueueState
    calls:tuple=()
    writes:tuple=()
    missing:str=''
    independently_verified:bool=False

def _known(before,after,label):
    if before is None:return after
    if after is not None and before!=after:raise ValueError('Changed known SELL session observation: '+label)
    return before

class SellSessionFrame:
    def __init__(self,state,queue):
        if not isinstance(state,SellSessionState) or not isinstance(queue,QueueState):raise ValueError('Typed own SELL session and queue required')
        if state.phase_dword!=2 or not state.setup_gate_byte:raise ValueError('Reached phase2/nonzero setup gate required')
        self.entry=state;self.candidate=state;self.queue=queue;self.prospective_queue=queue
        self.observation=SellSessionObservation();self.stage=0;self.calls=[];self.writes=[];self.done=False
    def _result(self,missing=''):
        return SellSessionDecision(self.done,self.candidate if self.done else self.entry,self.candidate,
            self.prospective_queue if self.done else self.queue,self.prospective_queue,tuple(self.calls),tuple(self.writes),missing)
    def step(self,observation=None):
        if observation is not None and not isinstance(observation,SellSessionObservation):raise ValueError('Typed session observation required')
        if self.done:return self._result()
        a=self.observation;b=observation or SellSessionObservation()
        aq=a.queue_sample or QueueSample();bq=b.queue_sample or QueueSample()
        if a.enqueue_returned is True and b.enqueue_returned is False:raise ValueError('Changed completed enqueue return')
        self.observation=SellSessionObservation(_known(a.session_tick_dword,b.session_tick_dword,'session tick'),
            QueueSample(_known(aq.tick,bq.tick,'queue tick'),_known(aq.connection_gate,bq.connection_gate,'queue gate')),
            True if a.enqueue_returned is True else (b.enqueue_returned if b.enqueue_returned is not None else a.enqueue_returned))
        o=self.observation
        if self.stage==0:
            # Only source-written fields reset; pending+28 and item stamp+30 remain.
            slot=replace(self.candidate.slot,used_bytes=(0,)*28,accumulated_qword=0,net_qword=0,prepared_slots_dword=0)
            self.candidate=replace(self.candidate,slot=slot,list_index_dword=0,inventory_slot_dword=14,ready_byte=0)
            self.writes.extend((0x59+s,1,0) for s in range(14,42))
            self.writes.extend(((0x98,8,0),(0xa0,8,0),(0x84,4,0),(0x88,4,0),(0x8c,4,14),(0x38,1,0)))
            self.calls.append(('GetTickCount',));self.stage=1
        if self.stage==1:
            if o.session_tick_dword is None:return self._result('session GetTickCount')
            self.candidate=replace(self.candidate,session_stamp_qword=o.session_tick_dword)
            self.writes.append((0x40,8,o.session_tick_dword));self.calls.append(('004c7710',2,0));self.stage=2
        if self.stage==2:
            sample=o.queue_sample or QueueSample()
            decision=enqueue(self.queue,SEED,2,0,sample.connection_gate,sample.tick)
            if decision.state is None:return self._result(decision.missing or decision.status)
            self.prospective_queue=decision.state;self.stage=3
        if self.stage==3:
            if o.enqueue_returned is not True:return self._result('session enqueue normal return')
            self.candidate=replace(self.candidate,phase_dword=(self.entry.phase_dword+1)&0xffffffff)
            self.writes.append((4,4,self.candidate.phase_dword));self.done=True
        return self._result()
