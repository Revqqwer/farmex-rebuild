"""422c5a..422c89 BUY phase3 slice: pending -> clock -> helper -> phase++.

Own resumable observations only. No native writes, clocks, sends or ACKs.
Accepted state stays at entry while the ordered prefix is prospective.
"""
from dataclasses import dataclass,replace
from merchant_open import BuyOpenState,BuyOpenObservation,BuyOpenExecution,plan_buy_open
from merchant_setup import MerchantInventoryObservation
from upgrade_packets import UpgradeItemObservation
from action_queue import QueueState,QueueSample,enqueue

def _raw(value,bits):
    if type(value) is not int or not 0<=value<1<<bits:raise ValueError('Raw %dbit value required'%bits)

@dataclass(frozen=True)
class BuyOpenCallerState:
    phase_dword:int=3
    pending_byte:int=0
    pending_stamp_qword:int=0
    accumulated_qword:int=0
    def __post_init__(self):
        for value,bits in ((self.phase_dword,32),(self.pending_byte,8),
                           (self.pending_stamp_qword,64),(self.accumulated_qword,64)):_raw(value,bits)

@dataclass(frozen=True)
class BuyOpenFrameDecision:
    status:str
    complete:bool
    state:BuyOpenCallerState
    prospective_state:BuyOpenCallerState
    queue:QueueState
    prospective_queue:QueueState
    calls:tuple=()
    execution:object=None
    missing:str=''
    independently_verified:bool=False

def _known(before,after,label):
    if before is None:return after
    if after is not None and before!=after:raise ValueError('Changed known observation: '+label)
    return before

def _sequence(before,after,merge,label):
    return tuple(merge(before[i] if i<len(before) else None,after[i] if i<len(after) else None,
                       '%s[%d]'%(label,i)) for i in range(max(len(before),len(after))))

def _item(before,after,label):
    if before is None:return after
    if after is None:return before
    return UpgradeItemObservation(**{key:_known(value,getattr(after,key),label+'.'+key) for key,value in vars(before).items()})

def _inventory(before,after,label):
    if before is None:return after
    if after is None:return before
    return MerchantInventoryObservation(_sequence(before.item_results,after.item_results,_known,label+'.results'),
                                         _sequence(before.item_inputs,after.item_inputs,_item,label+'.reads'))

def _normal(before,after,label):
    # False means normal completion has not been observed; it may later arrive.
    if before is True:
        if after is False:raise ValueError('Changed completed helper: '+label)
        return True
    return after if after is not None else before

def _mapping(before,after,merge,label):
    return {key:merge(before.get(key),after.get(key),label+'.'+str(key)) for key in before.keys()|after.keys()}

def _merge(before,after):
    if before is None:return after
    if after is None:return before
    if before.stable_records!=after.stable_records:raise ValueError('Changed in-flight vector policy')
    if before.stable_records and len(before.records)!=len(after.records):raise ValueError('Changed stable vector length')
    return BuyOpenObservation(
        initial_global_base=_known(before.initial_global_base,after.initial_global_base,'initial base'),
        free_count=_known(before.free_count,after.free_count,'free count'),
        inventory_inputs=_inventory(before.inventory_inputs,after.inventory_inputs,'inventory'),
        coins_dword=_known(before.coins_dword,after.coins_dword,'coins'),
        records=_sequence(before.records,after.records,_known,'records'),stable_records=before.stable_records,
        vector_counts=_sequence(before.vector_counts,after.vector_counts,_known,'counts'),
        fresh_global_bases=_mapping(before.fresh_global_bases,after.fresh_global_bases,_known,'global bases'),
        zero_helper_returns=_mapping(before.zero_helper_returns,after.zero_helper_returns,_normal,'zero returns'),
        memset_returns=_mapping(before.memset_returns,after.memset_returns,_normal,'memset returns'))

class BuyOpenFrame:
    def __init__(self,state,queue=None):
        if not isinstance(state,BuyOpenCallerState):raise ValueError('Typed caller state required')
        if queue is not None and not isinstance(queue,QueueState):raise ValueError('Typed queue required')
        self.state=state;self.queue=queue if queue is not None else QueueState()
        self._input=state;self._input_queue=self.queue;self._prefix=state;self._prospective_queue=self.queue
        self._calls=[];self._entered=False;self._clock_requested=False;self._tick=None
        self._observation=None;self._source=None;self._packet_index=0;self._gate=None;self._decisions=[]
        self._done=False

    def _decision(self,status,complete=False,missing=''):
        execution=None
        if self._source is not None:
            accepted=BuyOpenState(self.state.accumulated_qword)
            execution=BuyOpenExecution(complete,accepted,self._source.prospective_state,
                self.queue,self._prospective_queue,self._source,tuple(self._decisions),missing)
        return BuyOpenFrameDecision(status,complete,self.state,self._prefix,self.queue,self._prospective_queue,
                                    tuple(self._calls),execution,missing)

    def step(self,*,entry_tick=None,observation=None,samples=None,helper_returned=None):
        if entry_tick is not None:_raw(entry_tick,32)
        if observation is not None and not isinstance(observation,BuyOpenObservation):raise ValueError('Typed opening observations required')
        if samples is not None and not isinstance(samples,dict):raise ValueError('Per-packet sample dictionary required')
        if helper_returned is not None and type(helper_returned) is not bool:raise ValueError('Explicit helper normal-return observation required')
        if self._done:return self._decision('already_complete',True)
        if self.state!=self._input or self.queue!=self._input_queue:raise ValueError('Changed accepted state during open frame')
        if self.state.phase_dword!=3:return self._decision('not_applicable',True)
        if not self._entered:
            self._prefix=replace(self._prefix,pending_byte=1)
            self._calls.append(('write_byte',0x48,1));self._entered=True
        if self._tick is None:
            if not self._clock_requested:self._calls.append(('GetTickCount',));self._clock_requested=True
            if entry_tick is None:return self._decision('needs_entry_clock',missing='phase3 entry GetTickCount')
            self._tick=entry_tick
            self._prefix=replace(self._prefix,pending_stamp_qword=entry_tick)
            self._calls.extend((('write_qword',0x50,entry_tick),('0042086c',)))
        if self._source is None or not self._source.complete:
            self._observation=_merge(self._observation,observation)
            if self._observation is None:return self._decision('needs_helper_inputs',missing='0042086c observations')
            self._source=plan_buy_open(BuyOpenState(self._input.accumulated_qword),self._observation)
            self._prefix=replace(self._prefix,accumulated_qword=self._source.prospective_state.accumulated_qword)
            if not self._source.complete:return self._decision('needs_helper_inputs',missing=self._source.missing)
        while self._packet_index<len(self._source.packets):
            index=self._packet_index;sample=(samples or {}).get(index)
            if sample is None:return self._decision('needs_enqueue_sample',missing='enqueue%d sample'%index)
            if not isinstance(sample,QueueSample):raise ValueError('Typed enqueue sample required')
            self._gate=_known(self._gate,sample.connection_gate,'enqueue%d gate'%index)
            payload,delay=self._source.packets[index]
            decision=enqueue(self._prospective_queue,payload,len(payload),delay,self._gate,sample.tick)
            if decision.state is None:return self._decision('needs_enqueue_sample',missing=decision.missing or decision.status)
            self._decisions.append(decision);self._prospective_queue=decision.state
            self._packet_index+=1;self._gate=None
        if helper_returned is not True:return self._decision('needs_helper_return',missing='0042086c normal return')
        self._prefix=replace(self._prefix,phase_dword=(self._prefix.phase_dword+1)&0xffffffff)
        self._calls.append(('increment_dword',4,self._prefix.phase_dword))
        self.state=self._prefix;self.queue=self._prospective_queue;self._done=True
        return self._decision('open_frame_returned',True)
