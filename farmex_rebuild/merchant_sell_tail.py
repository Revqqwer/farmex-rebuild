"""Resumable own plan for selected SELL slot tail, 420aac/420ca8.

No game IO, memcpy execution, x87 approximation, queue drain or ACK.
"""
from dataclasses import dataclass,replace
from merchant_sell_selection import SellSelectionPlan
from action_queue import QueueState,QueueSample,enqueue
from merchant_x87 import SellX87Sample,plan_sell_x87

SEED=bytes.fromhex('6803000000000000000000000000')
COEFFICIENT_BITS=bytes.fromhex('b81e85eb51b89e3f')

def _raw(value,bits,optional=False):
    if optional and value is None:return
    if type(value) is not int or not 0<=value<1<<bits:raise ValueError('Raw SELL tail field required')

@dataclass(frozen=True)
class SellSlotState:
    used_bytes:tuple=(0,)*28
    item_pending_byte:int=0
    item_stamp_qword:int=0
    accumulated_qword:int=0
    net_qword:int=0
    prepared_slots_dword:int=0
    def __post_init__(self):
        if type(self.used_bytes) is not tuple or len(self.used_bytes)!=28:raise ValueError('Explicit28 used bytes required')
        for value in self.used_bytes:_raw(value,8)
        for name,bits in (('item_pending_byte',8),('item_stamp_qword',64),('accumulated_qword',64),('net_qword',64),('prepared_slots_dword',32)):
            _raw(getattr(self,name),bits)

@dataclass(frozen=True)
class SellSlotObservation:
    item_tick_dword:object=None
    ftol_qword:object=None
    copy_returns:tuple=()
    queue_sample:object=None
    enqueue_returned:object=None
    x87_control_word:object=None
    x87_clean_context:object=None
    disk_crt_replay:object=None
    def __post_init__(self):
        _raw(self.item_tick_dword,32,True);_raw(self.ftol_qword,64,True)
        if type(self.copy_returns) is not tuple or len(self.copy_returns)>5:raise ValueError('Five independent memcpy returns maximum')
        for value in self.copy_returns+(self.enqueue_returned,):
            if value is not None and type(value) is not bool:raise ValueError('Explicit normal-return observation required')
        if self.queue_sample is not None and not isinstance(self.queue_sample,QueueSample):raise ValueError('Typed enqueue sample required')
        _raw(self.x87_control_word,16,True)
        for value in (self.x87_clean_context,self.disk_crt_replay):
            if value is not None and type(value) is not bool:raise ValueError('Explicit x87 context/model choice required')
        if self.disk_crt_replay is True and self.ftol_qword is not None:raise ValueError('Disk CRT replay conflicts with observed ftol result')

@dataclass(frozen=True)
class SellSlotDecision:
    complete:bool
    selection:SellSelectionPlan
    state:SellSlotState
    prospective_state:SellSlotState
    queue:QueueState
    prospective_queue:QueueState
    payload:object=None
    prospective_payload:bytes=SEED
    calls:tuple=()
    writes:tuple=()
    missing:str=''
    return_al:object=None
    independently_verified:bool=False
    ftol_plan:object=None
    ftol_source:object=None

def _known(before,after,label):
    if before is None:return after
    if after is not None and before!=after:raise ValueError('Changed known SELL tail observation: '+label)
    return before

def _normal(before,after,label):
    if before is True and after is False:raise ValueError('Changed completed normal return: '+label)
    return True if before is True else (after if after is not None else before)

class SellSlotFrame:
    def __init__(self,selection,state,queue):
        if not isinstance(selection,SellSelectionPlan) or not selection.complete or selection.status!='selected':
            raise ValueError('Completed selected-slot plan required')
        if not isinstance(state,SellSlotState) or not isinstance(queue,QueueState):raise ValueError('Typed own state/queue required')
        for value,bits in ((selection.item_dword,32),(selection.quantity_dword,32),(selection.price_dword,32)):_raw(value,bits)
        if type(selection.inventory_slot) is not int or not 14<=selection.inventory_slot<42:raise ValueError('Selected slot14..41required')
        self.selection=selection;self.entry=state;self.candidate=state;self.queue=queue;self.prospective_queue=queue
        self.observation=SellSlotObservation();self.stage=0;self.copy_index=0;self.buffer=bytearray(SEED)
        self.calls=[];self.writes=[];self.called=set();self.done=False
        self.ftol_plan=None;self.ftol_source=None
    def _call(self,key,value):
        if key not in self.called:self.calls.append(value);self.called.add(key)
    def _write(self,field,value,offset,width):
        self.candidate=replace(self.candidate,**{field:value});self.writes.append((offset,width,value))
    def _merge(self,after):
        before=self.observation
        copies=tuple(_normal(before.copy_returns[i] if i<len(before.copy_returns) else None,
                             after.copy_returns[i] if i<len(after.copy_returns) else None,'copy%d'%i)
                     for i in range(max(len(before.copy_returns),len(after.copy_returns))))
        a=before.queue_sample or QueueSample();b=after.queue_sample or QueueSample()
        sample=QueueSample(_known(a.tick,b.tick,'enqueue tick'),_known(a.connection_gate,b.connection_gate,'enqueue gate'),
                           _normal(a.sender_returned,b.sender_returned,'unused sender return'))
        self.observation=SellSlotObservation(_known(before.item_tick_dword,after.item_tick_dword,'item clock'),
            _known(before.ftol_qword,after.ftol_qword,'ftol EDX:EAX'),copies,sample,
            _normal(before.enqueue_returned,after.enqueue_returned,'enqueue'),
            _known(before.x87_control_word,after.x87_control_word,'x87 control word'),
            _known(before.x87_clean_context,after.x87_clean_context,'clean x87 context'),
            _known(before.disk_crt_replay,after.disk_crt_replay,'disk CRT replay choice'))
    def _result(self,missing=''):
        return SellSlotDecision(self.done,self.selection,self.candidate if self.done else self.entry,self.candidate,
            self.prospective_queue if self.done else self.queue,self.prospective_queue,
            bytes(self.buffer) if self.copy_index==5 else None,bytes(self.buffer),tuple(self.calls),tuple(self.writes),
            missing,1 if self.done else None,ftol_plan=self.ftol_plan,ftol_source=self.ftol_source)
    def step(self,observation=None):
        if observation is not None and not isinstance(observation,SellSlotObservation):raise ValueError('Typed SELL tail observation required')
        if self.done:return self._result() # No later replay can duplicate the local queue record.
        self._merge(observation or SellSlotObservation());o=self.observation;s=self.selection
        if self.stage==0:
            used=list(self.candidate.used_bytes);used[s.inventory_slot-14]=1
            self.candidate=replace(self.candidate,used_bytes=tuple(used));self.writes.append((0x59+s.inventory_slot,1,1))
            self._write('item_pending_byte',1,0x28,1);self.stage=1
        if self.stage==1:
            self._call('clock',('GetTickCount',))
            if o.item_tick_dword is None:return self._result('item GetTickCount')
            self._write('item_stamp_qword',o.item_tick_dword,0x30,8)
            term=(s.quantity_dword*s.price_dword)&0xffffffff
            self._write('accumulated_qword',(self.candidate.accumulated_qword+term)&0xffffffffffffffff,0x98,8)
            self.stage=2
        if self.stage==2:
            self._call('ftol',('__ftol','signed QWORD total - total * double',COEFFICIENT_BITS.hex()))
            if o.disk_crt_replay is True:
                self.ftol_plan=plan_sell_x87(self.candidate.accumulated_qword,SellX87Sample(o.x87_control_word,o.x87_clean_context))
                if not self.ftol_plan.complete:return self._result('disk CRT x87: '+self.ftol_plan.missing)
                value=self.ftol_plan.net_qword;self.ftol_source='local_disk_crt_replay'
            else:
                if o.ftol_qword is None:return self._result('observed __ftol EDX:EAX or explicit disk CRT replay')
                value=o.ftol_qword;self.ftol_source='observed'
            self._write('net_qword',value,0xa0,8);self.stage=3
        if self.stage==3:
            fields=((2,4,s.item_dword),(6,2,s.quantity_dword&0xffff),(8,4,s.price_dword),
                    (12,1,s.inventory_slot-14),(13,1,self.entry.prepared_slots_dword&0xff))
            while self.copy_index<5:
                i=self.copy_index;offset,width,value=fields[i];self._call(('copy',i),('_memcpy',i,width))
                if i>=len(o.copy_returns) or o.copy_returns[i] is not True:return self._result('memcpy%d normal return'%i)
                self.buffer[offset:offset+width]=value.to_bytes(width,'little');self.copy_index+=1
            self.stage=4
        if self.stage==4:
            self._call('enqueue',('004c7710',14,0))
            sample=o.queue_sample or QueueSample()
            decision=enqueue(self.queue,bytes(self.buffer),14,0,sample.connection_gate,sample.tick)
            if decision.state is None:return self._result(decision.missing or decision.status)
            self.prospective_queue=decision.state;self.stage=5
        if self.stage==5:
            if o.enqueue_returned is not True:return self._result('004c7710 normal return after local queue plan')
            self._write('prepared_slots_dword',(self.entry.prepared_slots_dword+1)&0xffffffff,0x84,4)
            self.done=True
        return self._result()
