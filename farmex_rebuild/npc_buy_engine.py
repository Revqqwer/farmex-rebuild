"""Richard004efa84 local row collection and final purchase batch replay.

Native vector allocation addresses are not emulated; the immutable batch is
our logical20-byte record vector. All external observations are explicit.
"""
from dataclasses import dataclass,field
from types import MappingProxyType
from typing import Mapping,Optional,Tuple
from npc_buy_packets import NpcBuyRecord,BUY_VENDORS,plan_npc_buy_packet
from npc_sell_packets import raw

@dataclass(frozen=True)
class NpcBuyRouteRow:
    enabled: int
    vendor_id: Optional[int] = None
    record: Optional[NpcBuyRecord] = None

    def __post_init__(self):
        raw(self.enabled,255);raw(self.vendor_id,optional=True)
        if self.record is not None and not isinstance(self.record,NpcBuyRecord):raise ValueError('Typed purchase record required')

@dataclass(frozen=True)
class NpcBuyState:
    fields: Mapping[int,int]
    batch: Tuple[NpcBuyRecord,...] = ()

    def __post_init__(self):
        for key,value in self.fields.items():
            raw(key)
            if type(value) is not int:raise ValueError('Integer raw fields required')
        if any(not isinstance(row,NpcBuyRecord) for row in self.batch):raise ValueError('Typed purchase batch required')
        object.__setattr__(self,'fields',MappingProxyType(dict(self.fields)))
        object.__setattr__(self,'batch',tuple(self.batch))

@dataclass(frozen=True)
class NpcBuyObservation:
    now_ms: int
    current_target: Optional[int] = None
    row: Optional[NpcBuyRouteRow] = None
    vendor_matches: Mapping[str,bool] = field(default_factory=dict)
    packet_observation: object = None

    def __post_init__(self):
        raw(self.now_ms);raw(self.current_target,optional=True)
        if self.row is not None and not isinstance(self.row,NpcBuyRouteRow):raise ValueError('Typed route row required')
        object.__setattr__(self,'vendor_matches',MappingProxyType(dict(self.vendor_matches)))

@dataclass(frozen=True)
class NpcBuyResult:
    status: str
    state: NpcBuyState
    returned_phase: int
    calls: Tuple[str,...] = ()
    queue_payloads: Tuple[bytes,...] = ()
    cache_writes: Tuple[Tuple[int,int],...] = ()
    missing: str = ''

class _Missing(Exception):pass

def npc_buy_step(state,observation):
    if not isinstance(state,NpcBuyState) or not isinstance(observation,NpcBuyObservation):raise ValueError('Typed purchase inputs required')
    fields=dict(state.fields);batch=list(state.batch);calls=[];packets=[];writes=[]
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def f(key):return need(fields.get(key),'field+%x'%key)&0xffffffff
    def wait():fields.update({0x694:1,0x698:observation.now_ms,0x69c:0})
    def clear():
        calls.extend(('004f0108','004f00e4','004f012c'));batch.clear()
    def result(status,missing=''):
        return NpcBuyResult(status,NpcBuyState(fields,tuple(batch)),fields.get(0x690,0),
                            tuple(calls),tuple(packets),tuple(writes),missing)
    try:
        phase=f(0x690)
        if f(0x694)&255:
            start=(f(0x69c)<<32)|f(0x698)
            if start&0x8000000000000000:start-=0x10000000000000000
            elapsed=(observation.now_ms-start)&0xffffffffffffffff
            if elapsed&0x8000000000000000:elapsed-=0x10000000000000000
            if elapsed<500:return result('waiting')
            fields.update({0x694:0,0x698:0,0x69c:0,0x690:(phase+1)&0xffffffff})
            return result('advanced')
        calls.append('00462630')
        target=need(observation.current_target,'00462630 current target')
        if target!=f(0x604) or phase==0xffffffff:
            pointer=f(0x60c)
            clear();calls.append('0046493c');wait()
            return result('npc_target_planned')
        count=f(0x68c)
        if phase==count:
            if batch:
                calls.append('004c95a4')
                packet_obs=need(observation.packet_observation,'004c95a4 packet observations')
                plan=plan_npc_buy_packet(batch,f(0x604),packet_obs)
                writes.extend(plan.cache_writes)
                if plan.status not in ('planned','no_queue'):return result(plan.status,plan.missing)
                if plan.payload is not None:packets.append(plan.payload)
                clear()
            wait();return result('batch_flushed' if packets else 'final_wait')
        if phase>=count:return result('unresolved_row_index','native row index outside observed vector')
        row=need(observation.row,'route row%d'%phase)
        if row.enabled!=1:
            fields[0x690]=(phase+1)&0xffffffff;return result('row_skipped')
        matched=False
        for name,vendor in BUY_VENDORS:
            calls.append('00505d20:'+name)
            match=need(observation.vendor_matches.get(name),'00505d20:'+name)
            if type(match) is not bool:raise ValueError('Boolean vendor comparison required')
            if match and need(row.vendor_id,'route row vendor ID')==vendor:
                matched=True;break
        if not matched:
            fields[0x690]=(phase+1)&0xffffffff;return result('vendor_skipped')
        record=need(row.record,'route row20-byte record')
        calls.extend(('004f01dc','004f0204','004f022c/004f0290'))
        batch.append(record);wait();return result('row_collected')
    except _Missing as exc:return result('needs_observation',str(exc))
