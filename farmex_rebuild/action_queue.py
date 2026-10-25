"""004c7710/004c79a0 local queue replay. No native calls or acknowledgements.

Queue time is zero-extended GetTickCount minus the stored QWORD timestamp,
compared against sign-extended DWORD delay. It does not wrap modulo DWORD.
Missing observations produce an uncommitted plan, not a guessed state.
"""
from dataclasses import dataclass,replace
from typing import Optional, Tuple
from types import MappingProxyType
from native_sender import SenderObservation,plan_source_sender


def _dword(value, optional=False):
    if optional and value is None:return
    if type(value) is not int or not 0 <= value <= 0xffffffff:
        raise ValueError('Raw DWORD required')


@dataclass(frozen=True)
class QueueRecord:
    record_id: int
    payload: bytes
    created_tick: int
    delay_dword: int

    def __post_init__(self):
        if type(self.record_id) is not int or self.record_id <= 0:raise ValueError('Positive local record ID required')
        if type(self.payload) is not bytes:raise ValueError('Immutable payload required')
        _dword(self.created_tick);_dword(self.delay_dword)


@dataclass(frozen=True)
class QueueState:
    records: Tuple[QueueRecord, ...] = ()
    next_id: int = 1

    def __post_init__(self):
        object.__setattr__(self,'records',tuple(self.records))
        if any(not isinstance(r,QueueRecord) for r in self.records):raise ValueError('Typed records required')
        ids=[r.record_id for r in self.records]
        if len(ids)!=len(set(ids)) or type(self.next_id) is not int or self.next_id <= max(ids,default=0):
            raise ValueError('Unique IDs and fresh local next ID required')


@dataclass(frozen=True)
class QueueSample:
    tick: Optional[int] = None
    connection_gate: Optional[int] = None
    sender_returned: Optional[bool] = None
    sender_inputs: Optional[SenderObservation] = None

    def __post_init__(self):
        _dword(self.tick,True);_dword(self.connection_gate,True)
        if self.sender_returned is not None and type(self.sender_returned) is not bool:
            raise ValueError('Explicit sender return observation required')
        if self.sender_inputs is not None and not isinstance(self.sender_inputs,SenderObservation):
            raise ValueError('Typed bound sender observations required')


@dataclass(frozen=True)
class QueueEvent:
    kind: str
    record_id: int
    payload: bytes
    acknowledged: bool = False
    sender_plan: object = None


@dataclass(frozen=True)
class QueueDecision:
    status: str
    state: Optional[QueueState]
    events: Tuple[QueueEvent, ...] = ()
    missing: str = ''


def publish_appended_records(shared,staged_records,published_count):
    """Publish a child append prefix once into the latest own shared queue.

    IDs are fresh local bookkeeping. Existing/interleaved records are retained;
    no packet delivery, native handle or acknowledgement is implied. The child
    must be append-only and the caller retains its published-count cursor.
    """
    if not isinstance(shared,QueueState):raise ValueError('Own shared queue required')
    if type(staged_records) is not tuple or any(not isinstance(r,QueueRecord) for r in staged_records):raise ValueError('Immutable staged records required')
    if type(published_count) is not int or published_count<0:raise ValueError('Own publication cursor required')
    if len(staged_records)<published_count:raise AssertionError('Owned child queue prefix retracted')
    delta=staged_records[published_count:]
    ids=tuple(range(shared.next_id,shared.next_id+len(delta)))
    if delta:
        appended=tuple(replace(record,record_id=record_id) for record,record_id in zip(delta,ids))
        shared=QueueState(shared.records+appended,shared.next_id+len(appended))
    return shared,ids,len(staged_records)


def enqueue(state,payload,length,delay_dword,connection_gate,tick=None,*,copy_limit=1048576):
    if not isinstance(state,QueueState):raise ValueError('Typed queue required')
    _dword(length);_dword(delay_dword);_dword(connection_gate,True);_dword(tick,True)
    if connection_gate is None:return QueueDecision('needs_observation',None,missing='enqueue connection gate')
    if connection_gate==0:return QueueDecision('not_enqueued',state)
    if length==0xffffffff:return QueueDecision('unresolved_allocation_wrap',None)
    if type(copy_limit) is not int or copy_limit<0:raise ValueError('Explicit local copy limit required')
    # This bounded copy is our policy, not a recovered vendor buffer limit.
    if length>copy_limit:return QueueDecision('local_copy_limit',None)
    if not isinstance(payload,(bytes,bytearray)) or len(payload)<length:
        return QueueDecision('needs_observation',None,missing='complete payload bytes')
    if tick is None:return QueueDecision('needs_observation',None,missing='enqueue GetTickCount')
    record=QueueRecord(state.next_id,bytes(payload[:length]),tick,delay_dword)
    updated=QueueState(state.records+(record,),state.next_id+1)
    return QueueDecision('locally_enqueued',updated,(QueueEvent('copied',record.record_id,record.payload),))


def drain(state,samples):
    if not isinstance(state,QueueState):raise ValueError('Typed queue required')
    samples=MappingProxyType(dict(samples));events=[];retained=[]
    def missing(label):return QueueDecision('needs_observation',None,tuple(events),label)
    for record in state.records:
        sample=samples.get(record.record_id)
        if sample is None:return missing('record %d GetTickCount'%record.record_id)
        if not isinstance(sample,QueueSample):raise ValueError('Typed per-record samples required')
        if sample.tick is None:return missing('record %d GetTickCount'%record.record_id)
        delay=record.delay_dword-(0x100000000 if record.delay_dword&0x80000000 else 0)
        if sample.tick-record.created_tick < delay:
            retained.append(record)
            continue
        if sample.connection_gate is None:return missing('record %d connection gate'%record.record_id)
        if sample.connection_gate:
            sender=None
            if sample.sender_inputs is not None:
                sender=plan_source_sender(len(record.payload),sample.sender_inputs,expected_payload=record.payload)
            events.append(QueueEvent('native_send_plan',record.record_id,record.payload,sender_plan=sender))
            if sender is not None and not sender.complete:
                return QueueDecision('needs_sender_operands',None,tuple(events),'bound sender: '+sender.missing)
            if sample.sender_returned is not True:
                return QueueDecision('needs_sender_return',None,tuple(events),'00464918 return for record %d'%record.record_id)
        else:
            events.append(QueueEvent('due_disconnected_drop',record.record_id,record.payload))
        events.append(QueueEvent('free_and_mark',record.record_id,record.payload))
    return QueueDecision('locally_drained',QueueState(tuple(retained),state.next_id),tuple(events))


@dataclass(frozen=True)
class CallbackQueueGate:
    ready_46edb0: Optional[int] = None
    connection_462738: Optional[int] = None
    byte_562208: Optional[int] = None
    byte_56221d: Optional[int] = None
    initial_reader_f3c: Optional[int] = None
    byte_561f55: Optional[int] = None
    helper_46f33c: Optional[int] = None

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            value=getattr(self,name);_dword(value,True)
            if value is not None and name not in ('connection_462738','initial_reader_f3c') and value>255:
                raise ValueError('Raw BYTE gate required')


def drain_on_callback(state,gate,samples):
    """Queue reachability only, not a replay of callback side effects/hook ABI."""
    if not isinstance(state,QueueState) or not isinstance(gate,CallbackQueueGate):
        raise ValueError('Typed queue and callback observations required')
    def unknown(name):return QueueDecision('needs_observation',None,missing=name)
    def skipped(reason):return QueueDecision('callback_skipped_queue',state,missing=reason)
    if gate.ready_46edb0 is None:return unknown('0046edb0 AL')
    if gate.ready_46edb0==0:return skipped('outer readiness')
    if gate.connection_462738 is None:return unknown('outer00462738 EAX')
    if gate.connection_462738!=1:return skipped('outer connection must equal1')
    for name in ('byte_562208','byte_56221d'):
        value=getattr(gate,name)
        if value is None:return unknown(name)
        if value:return skipped(name+' branch')
    if gate.initial_reader_f3c is None:return unknown('initial reader00553f3c chain')
    if gate.initial_reader_f3c==0:
        if gate.byte_561f55 is None:return unknown('byte_561f55')
        if gate.byte_561f55:
            if gate.helper_46f33c is None:return unknown('0046f33c AL')
            if gate.helper_46f33c:return skipped('0046f33c guard')
    return drain(state,samples)
