"""421c2c..421eb3 SELL phase5 normal caller, supplied UI-span observations only."""
from dataclasses import dataclass,replace
from merchant_open_clock import MerchantWaitClockSample,plan_merchant_open_wait

def _raw(value,bits,optional=False):
    if optional and value is None:return
    if type(value) is not int or not 0<=value<1<<bits:raise ValueError('Raw SELL opening-wait field required')

@dataclass(frozen=True)
class SellOpenWaitState:
    phase_dword:int=5
    pending_byte:int=1
    pending_stamp_qword:int=0
    setup_gate_byte:int=1
    status_byte_90:int=0
    def __post_init__(self):
        for value,bits in ((self.phase_dword,32),(self.pending_byte,8),(self.pending_stamp_qword,64),
                           (self.setup_gate_byte,8),(self.status_byte_90,8)):_raw(value,bits)

@dataclass(frozen=True)
class SellOpenWaitObservation:
    tick_dword:object=None
    clear_span_returns:tuple=()
    accumulated_qword:object=None
    net_qword:object=None
    stop_returned:object=None
    timeout_message_returned:object=None
    def __post_init__(self):
        _raw(self.tick_dword,32,True);_raw(self.accumulated_qword,64,True);_raw(self.net_qword,64,True)
        if type(self.clear_span_returns) is not tuple or len(self.clear_span_returns)>4:raise ValueError('Four separate UI span returns maximum')
        for value in self.clear_span_returns+(self.stop_returned,self.timeout_message_returned):
            if value is not None and type(value) is not bool:raise ValueError('Explicit normal span return required')

@dataclass(frozen=True)
class SellOpenWaitDecision:
    complete:bool
    status:str
    state:SellOpenWaitState
    prospective_state:SellOpenWaitState
    clock_plan:object=None
    steps:tuple=()
    writes:tuple=()
    value_reads:tuple=()
    display_plans:tuple=()
    missing:str=''
    independently_verified:bool=False

def _known(before,after,label):
    if before is None:return after
    if after is not None and before!=after:raise ValueError('Changed known opening-wait observation: '+label)
    return before

def _normal(before,after):
    if before is True and after is False:raise ValueError('Changed completed UI/helper span return')
    return True if before is True else (after if after is not None else before)

class SellOpenWaitFrame:
    def __init__(self,state):
        if not isinstance(state,SellOpenWaitState) or state.phase_dword!=5:raise ValueError('Reached phase5 state required')
        self.entry=state;self.candidate=state;self.observation=SellOpenWaitObservation()
        self.stage=0;self.span=0;self.entered=set();self.steps=[];self.writes=[];self.value_reads=[];self.displays=[]
        self.clock_plan=None;self.done=False;self.status='needs_observation'
    def _once(self,key,step):
        if key not in self.entered:self.steps.append(step);self.entered.add(key)
    def _result(self,missing=''):
        return SellOpenWaitDecision(self.done,self.status,self.candidate if self.done else self.entry,self.candidate,
            self.clock_plan,tuple(self.steps),tuple(self.writes),tuple(self.value_reads),tuple(self.displays),missing)
    def step(self,observation=None):
        if observation is not None and not isinstance(observation,SellOpenWaitObservation):raise ValueError('Typed opening-wait observation required')
        if self.done:return self._result() # One caller invocation; a later tick uses a new frame.
        a=self.observation;b=observation or SellOpenWaitObservation()
        returns=tuple(_normal(a.clear_span_returns[i] if i<len(a.clear_span_returns) else None,
                              b.clear_span_returns[i] if i<len(b.clear_span_returns) else None)
                      for i in range(max(len(a.clear_span_returns),len(b.clear_span_returns))))
        self.observation=SellOpenWaitObservation(_known(a.tick_dword,b.tick_dword,'tick'),returns,
            _known(a.accumulated_qword,b.accumulated_qword,'fresh accumulated QWORD'),
            _known(a.net_qword,b.net_qword,'fresh net QWORD'),_normal(a.stop_returned,b.stop_returned),
            _normal(a.timeout_message_returned,b.timeout_message_returned));o=self.observation
        if self.entry.pending_byte:
            self._once('clock',('GetTickCount',))
            sample=MerchantWaitClockSample(o.tick_dword,self.entry.pending_stamp_qword) if o.tick_dword is not None else None
            self.clock_plan=plan_merchant_open_wait(self.entry.pending_byte,sample)
            if self.clock_plan.timeout_due is None:return self._result('pending opening GetTickCount')
            if not self.clock_plan.timeout_due:
                self.done=True;self.status='waiting';return self._result()
            self._once('stop',('0040ae0c',0x561f34,0))
            if o.stop_returned is not True:return self._result('timeout stop helper normal return')
            self._once('timeout_message',('normal_span','00421c7d','00421cef'))
            if o.timeout_message_returned is not True:return self._result('timeout message/cleanup span normal return')
            self.done=True;self.status='timed_out';return self._result()
        if self.stage==0:
            if self.candidate.setup_gate_byte:
                self.candidate=replace(self.candidate,setup_gate_byte=0);self.writes.append((0x58,1,0))
            self.candidate=replace(self.candidate,status_byte_90=0);self.writes.append((0x90,1,0));self.stage=1
        ranges=(('00421d11','00421d5d'),('00421d60','00421dbc'),('00421dbf','00421e33'),('00421e36','00421eaa'))
        while self.span<4:
            i=self.span
            if i in (2,3):
                value=o.accumulated_qword if i==2 else o.net_qword
                if value is None:return self._result('fresh accumulated QWORD+98' if i==2 else 'fresh net QWORD+a0')
                key=('value',i)
                if key not in self.entered:
                    low=0x98 if i==2 else 0xa0
                    self.value_reads.extend(((low+4,4,value>>32),(low,4,value&0xffffffff)))
                    self.displays.append((3 if i==2 else 5,value));self.entered.add(key)
            self._once(('span',i),('normal_span',i,*ranges[i]))
            if i>=len(o.clear_span_returns) or o.clear_span_returns[i] is not True:return self._result('clear UI/string span%d normal return'%i)
            self.span+=1
        self.candidate=replace(self.candidate,phase_dword=6);self.writes.append((4,4,6))
        self.done=True;self.status='pending_cleared';return self._result()
