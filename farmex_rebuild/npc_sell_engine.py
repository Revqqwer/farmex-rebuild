"""Richard004eebf4 slot/batch orchestration. No native calls or memory writes.

Batch commit is deferred until producer observations are complete; native
allocator addresses and mid-call partial vector memory are not emulated.
"""
from dataclasses import dataclass,field
from types import MappingProxyType
from typing import Mapping,Optional,Tuple
from npc_sell_filter import SellFilterObservation,select_sale_item
from npc_sell_packets import NpcSellRecord,plan_npc_sell_packet


@dataclass(frozen=True)
class NpcSaleState:
    fields: Mapping[int,int]
    globals: Mapping[int,int] = field(default_factory=dict)
    batch: Tuple[NpcSellRecord,...] = ()

    def __post_init__(self):
        for mapping in (self.fields,self.globals):
            if any(type(k) is not int or type(v) is not int for k,v in mapping.items()):raise ValueError('Raw state maps required')
        if any(not isinstance(row,NpcSellRecord) for row in self.batch):raise ValueError('Typed batch records required')
        object.__setattr__(self,'fields',MappingProxyType(dict(self.fields)))
        object.__setattr__(self,'globals',MappingProxyType(dict(self.globals)))
        object.__setattr__(self,'batch',tuple(self.batch))


@dataclass(frozen=True)
class NpcSaleObservation:
    now_ms: int
    inventory_pointer: Optional[int] = None
    current_target: Optional[int] = None
    slot_present_4637d8: Optional[bool] = None
    selection: Optional[SellFilterObservation] = None
    record: Optional[NpcSellRecord] = None
    vendor_matches: object = None
    cache_slots: object = None

    def __post_init__(self):
        for value in (self.now_ms,self.inventory_pointer,self.current_target):
            if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):raise ValueError('Observed DWORD required')
        if self.now_ms is None:raise ValueError('DWORD clock required')
        if self.slot_present_4637d8 is not None and type(self.slot_present_4637d8) is not bool:raise ValueError('Slot presence observation required')


@dataclass(frozen=True)
class NpcSaleResult:
    status: str
    state: NpcSaleState
    returned_phase: Optional[int] = None
    calls: Tuple[str,...] = ()
    queue_payloads: Tuple[bytes,...] = ()
    cache_writes: Tuple[Tuple[int,int],...] = ()
    missing: str = ''


class _Missing(Exception):pass


def npc_sale_step(state,observation):
    if not isinstance(state,NpcSaleState) or not isinstance(observation,NpcSaleObservation):raise ValueError('Typed sale state/observation required')
    fields,globals,batch=dict(state.fields),dict(state.globals),list(state.batch)
    calls=[];packets=[];writes=[]
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def f(key):return need(fields.get(key),'field+%x'%key)
    def g(key):return need(globals.get(key),'global%08x'%key)
    def signed(value):
        value &= 0xffffffff
        return value-0x100000000 if value&0x80000000 else value
    def result(status,missing='',returned=None):
        return NpcSaleResult(status,NpcSaleState(fields,globals,tuple(batch)),
                             fields.get(0x654) if returned is None else returned,
                             tuple(calls),tuple(packets),tuple(writes),missing)
    def begin(delay):
        globals[0x56ffb4]=delay
        fields.update({0x658:1,0x660:observation.now_ms,0x664:0})
        return result('waiting')
    def producer(rows):
        matches=need(observation.vendor_matches,'vendor comparisons')
        calls.append('004c9158')
        plan=plan_npc_sell_packet(rows,f(0x604)&0xffffffff,matches,observation.cache_slots)
        writes.extend(plan.cache_writes)
        if plan.status not in ('planned','no_queue'):raise _Missing('producer:'+plan.status+':'+plan.missing)
        if plan.payload is not None:packets.append(plan.payload);calls.append('004c7710')
    try:
        if need(observation.inventory_pointer,'inventory root pointer')==0:
            # Source returns literal43 without changing its own+654 field.
            return result('no_inventory',returned=43)
        phase=f(0x654)&0xffffffff
        if f(0x658)!=0:
            start=((f(0x664)&0xffffffff)<<32)|(f(0x660)&0xffffffff)
            elapsed=(observation.now_ms-start)&0xffffffffffffffff
            if elapsed&0x8000000000000000:elapsed-=0x10000000000000000
            if elapsed<signed(g(0x56ffb4)):return result('waiting')
            fields.update({0x658:0,0x660:0,0x664:0,0x654:(phase+1)&0xffffffff})
            return result('advanced')
        current=need(observation.current_target,'00462630 current target')
        if current!=(f(0x604)&0xffffffff) or phase==13:
            batch.clear();calls.extend(('004ef830','004ef80c','004ef854'))
            f(0x60c);calls.extend(('0046493c','0046fb38'))
            return begin(1000 if g(0x553e44)!=0 else 0xc8f)
        if phase==42:
            if not batch:return begin(1000)
            delay=1000 if g(0x553e44)!=0 else 0x9f9
            producer(batch);batch.clear();calls.extend(('004ef830','004ef80c','004ef854'))
            return begin(delay)
        calls.append('004637d8')
        if not need(observation.slot_present_4637d8,'004637d8 slot presence'):
            fields[0x654]=(phase+1)&0xffffffff;return result('advanced')
        selection=need(observation.selection,'item selection observations')
        if not isinstance(selection,SellFilterObservation):raise ValueError('Typed item selection required')
        if selection.mode!=(g(0x561f58)&0xffffffff):raise ValueError('Selection mode conflicts with raw source mode')
        decision=select_sale_item(selection);calls.extend(decision.calls)
        if decision.status=='needs_observation':raise _Missing(decision.reason)
        if decision.status=='skip':
            fields[0x654]=(phase+1)&0xffffffff;return result('advanced')
        record=need(observation.record,'source record metadata')
        if not isinstance(record,NpcSellRecord) or record.relative_slot!=((phase-14)&255):
            raise ValueError('Record slot must match source phase minus14')
        proposed=batch+[record]
        if len(proposed)>14:raise _Missing('batch outside normal caller limit')
        if len(proposed)==14:
            delay=1000 if g(0x553e44)!=0 else (0xb25 if selection.mode==2 else 0x98b)
            producer(proposed);batch.clear();calls.extend(('004ef830','004ef80c','004ef854'))
            return begin(delay)
        batch.append(record);fields[0x654]=(phase+1)&0xffffffff
        return result('advanced')
    except _Missing as exc:return result('needs_observation',str(exc))
