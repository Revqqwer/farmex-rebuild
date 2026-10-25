"""Richard004c9158 batch builder from explicit metadata, without memory writes.

Ordinary004eebf4 caller flushes at14 records. Larger nonzero-byte-count batches
remain unresolved here; native stack-buffer corruption is not reproduced.
"""
from dataclasses import dataclass
from typing import Optional,Tuple

VENDORS=(('Sundries',0x3e418),('Armor',0x31511),('Weapon',0x31129),
         ('Potion',0x3dc48),('Amore',0x43df0))
CACHE_BASES=(0x568e84,0x568ef4,0x568f64,0x568fd4,0x569044)


def raw(value,maximum=0xffffffff,optional=False):
    if value is None and optional:return
    if type(value) is not int or not 0<=value<=maximum:raise ValueError('Observed raw unsigned field required')


@dataclass(frozen=True)
class NpcSellRecord:
    item_id: int
    relative_slot: int
    quantity: int

    def __post_init__(self):
        raw(self.item_id);raw(self.relative_slot,255);raw(self.quantity,0xffff)


@dataclass(frozen=True)
class SellCacheSlot:
    item_id: Optional[int] = None
    durability: Optional[int] = None
    quantity: Optional[int] = None

    def __post_init__(self):
        for value in (self.item_id,self.durability,self.quantity):raw(value,optional=True)


@dataclass(frozen=True)
class NpcSellPacketPlan:
    status: str
    payload: Optional[bytes] = None
    cache_writes: Tuple[Tuple[int,int],...] = ()
    missing: str = ''
    queue_delay_ms: int = 0


class _Missing(Exception):pass


def plan_npc_sell_packet(records,npc_id,vendor_matches,cache_slots=None):
    records=tuple(records);raw(npc_id)
    if any(not isinstance(row,NpcSellRecord) for row in records):raise ValueError('Typed12-byte source records required')
    cache_slots={} if cache_slots is None else cache_slots
    writes=[]
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    try:
        script=0
        for name,value in VENDORS:
            match=need(vendor_matches.get(name),'00505d20:'+name)
            if type(match) is not bool:raise ValueError('Observed vendor comparison required')
            if match:script=value
        if npc_id==0 or script==0 or len(records)&255==0:return NpcSellPacketPlan('no_queue')
        if len(records)>14:return NpcSellPacketPlan('unresolved_outside_observed_batch_limit')
        for slot in range(14,42):
            row=need(cache_slots.get(slot),'cache slot%d'%slot)
            if not isinstance(row,SellCacheSlot):raise ValueError('Typed cache observation required')
            for base,label,value in zip(CACHE_BASES,('ID','durability','quantity','zero','zero'),
                                        (row.item_id,row.durability,row.quantity,0,0)):
                writes.append((base+(slot-14)*4,need(value,'cache slot%d %s'%(slot,label))))
        payload=bytearray(b'\x21\x02'+script.to_bytes(4,'little')+npc_id.to_bytes(4,'little')+bytes((len(records)&255,)))
        for row in records:
            payload.extend(row.item_id.to_bytes(4,'little')+bytes((row.relative_slot,))+row.quantity.to_bytes(2,'little'))
            # Assembly proves DWORD stores and stride4; decompiler types are incomplete.
            writes.extend((base+row.relative_slot*4,0) for base in CACHE_BASES)
        return NpcSellPacketPlan('planned',bytes(payload),tuple(writes))
    except _Missing as exc:return NpcSellPacketPlan('needs_observation',cache_writes=tuple(writes),missing=str(exc))
