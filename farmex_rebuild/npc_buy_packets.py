"""Richard004c95a4: ordered local purchase/cache plan, no game IO.

Helper observations remain explicit. The 1024-byte limit is our serializer
policy, not an inferred native buffer bound. Native overflow is not emulated.
"""
from dataclasses import dataclass,field
from types import MappingProxyType
from typing import Mapping,Optional,Tuple
from npc_sell_packets import SellCacheSlot,CACHE_BASES,raw

BUY_VENDORS=(('Sundries',0x3e418),('Armor',0x31511),('Weapon',0x31129),
             ('Potion',0x3dc48),('DC Sundries',0x412f8),('Amore',0x43df0))

def signed32(value):
    value &= 0xffffffff
    return value-0x100000000 if value&0x80000000 else value

@dataclass(frozen=True)
class NpcBuyRecord:
    item_id: int
    desired_quantity: int
    selector_a: int
    selector_b: int
    unit_weight: int
    unit_cost: int

    def __post_init__(self):
        raw(self.item_id);raw(self.desired_quantity,0xffff)
        raw(self.selector_a,255);raw(self.selector_b,255)
        raw(self.unit_weight);raw(self.unit_cost)

@dataclass(frozen=True)
class NpcBuyPacketObservation:
    current_weight: Optional[int] = None
    maximum_weight: Optional[int] = None
    vendor_matches: Mapping[str,bool] = field(default_factory=dict)
    cache_slots: Mapping[int,SellCacheSlot] = field(default_factory=dict)
    currency_by_record: Mapping[int,int] = field(default_factory=dict)

    def __post_init__(self):
        raw(self.current_weight,optional=True);raw(self.maximum_weight,optional=True)
        for key,value in self.currency_by_record.items():raw(key);raw(value)
        for name in ('vendor_matches','cache_slots','currency_by_record'):
            object.__setattr__(self,name,MappingProxyType(dict(getattr(self,name))))

@dataclass(frozen=True)
class NpcBuyPacketPlan:
    status: str
    payload: Optional[bytes] = None
    cache_writes: Tuple[Tuple[int,int],...] = ()
    accepted: Tuple[Tuple[int,int,int],...] = ()  # record index, relative slot, quantity
    missing: str = ''
    queue_delay_ms: int = 0

class _Missing(Exception):pass

def plan_npc_buy_packet(records,npc_id,observation):
    records=tuple(records);raw(npc_id)
    if any(not isinstance(row,NpcBuyRecord) for row in records):raise ValueError('Typed20-byte source records required')
    if not isinstance(observation,NpcBuyPacketObservation):raise ValueError('Typed purchase observations required')
    writes=[];accepted=[]
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    try:
        weight=need(observation.current_weight,'00461220 current weight')
        maximum=need(observation.maximum_weight,'00461240 maximum weight')
        vendor=0
        for name,value in BUY_VENDORS:
            match=need(observation.vendor_matches.get(name),'00505d20:'+name)
            if type(match) is not bool:raise ValueError('Boolean vendor observations required')
            if match:vendor=value
        cache=[]
        for slot in range(14,42):
            row=need(observation.cache_slots.get(slot),'cache slot%d'%slot)
            if not isinstance(row,SellCacheSlot):raise ValueError('Typed cache observations required')
            values=[]
            for base,label,value in zip(CACHE_BASES,('ID','durability','quantity','zero','zero'),
                                        (row.item_id,row.durability,row.quantity,0,0)):
                value=need(value,'cache slot%d %s'%(slot,label));values.append(value)
                writes.append((base+(slot-14)*4,value))
            cache.append(values)
        payload=bytearray(b'\x21\x01'+vendor.to_bytes(4,'little')+npc_id.to_bytes(4,'little')+b'\0')
        spent=0
        for index,record in enumerate(records):
            empty=-1;existing=-1;quantity=0
            for relative,values in enumerate(cache):
                if empty==-1 and values[0]==0:empty=relative
                if values[0]==record.item_id:
                    existing=relative;quantity=values[2];break
            if existing==-1:
                slot=empty;amount=record.desired_quantity
            else:
                slot=existing
                amount=((record.desired_quantity-quantity)&0xffffffff
                        if record.desired_quantity>signed32(quantity) else 0)
            if signed32(amount)<=0 or slot<0:continue
            extra_weight=(record.unit_weight*amount)&0xffffffff
            extra_cost=(record.unit_cost*amount)&0xffffffff
            next_weight=(weight+extra_weight)&0xffffffff
            if next_weight>=maximum:continue
            currency=need(observation.currency_by_record.get(index),'0046258c currency record%d'%index)
            next_spent=(spent+extra_cost)&0xffffffff
            if next_spent>currency:continue
            if len(payload)+9>1024:
                return NpcBuyPacketPlan('unresolved_serializer_limit',cache_writes=tuple(writes),accepted=tuple(accepted))
            payload.extend(record.item_id.to_bytes(4,'little')+bytes((slot,))+
                           (amount&0xffff).to_bytes(2,'little')+bytes((record.selector_a,record.selector_b)))
            values=[record.item_id,1,(quantity+amount)&0xffffffff,0,0]
            cache[slot]=values
            writes.extend((base+slot*4,value) for base,value in zip(CACHE_BASES,values))
            accepted.append((index,slot,amount));weight=next_weight;spent=next_spent
        payload[10]=len(accepted)&255
        # Source has no zero NPC/vendor guard. Only its accepted BYTE count gates queueing.
        return NpcBuyPacketPlan('planned' if payload[10] else 'no_queue',
                                bytes(payload) if payload[10] else None,tuple(writes),tuple(accepted))
    except _Missing as exc:
        return NpcBuyPacketPlan('needs_observation',cache_writes=tuple(writes),accepted=tuple(accepted),missing=str(exc))
