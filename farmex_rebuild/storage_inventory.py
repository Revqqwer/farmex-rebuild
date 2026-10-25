"""Observed-slot replay of Richard storage counts and capacity predicates.

No memory IO. In0046ffa4 the no-empty/no-match fallback uses a stack BYTE
not initialized by the body or00504bec frame setup: it remains explicit.
"""
from dataclasses import dataclass,field
from types import MappingProxyType
from typing import Mapping,Optional,Tuple
from npc_sell_packets import raw
from npc_buy_packets import signed32

KINDS=('vip_existing','inn_existing','vip_full','bag_full','inn_free')

@dataclass(frozen=True)
class StorageSlot:
    pointer: Optional[int] = None
    base_item_id: Optional[int] = None
    extension_id: Optional[int] = None
    quantity: Optional[int] = None
    metadata_byte_6a: Optional[int] = None

    def __post_init__(self):
        for value in (self.pointer,self.base_item_id,self.extension_id,self.quantity):raw(value,optional=True)
        raw(self.metadata_byte_6a,255,optional=True)

@dataclass(frozen=True)
class StorageScanObservation:
    kind: str
    slots: Mapping[int,StorageSlot] = field(default_factory=dict)
    target_item_id: Optional[int] = None
    required_empty_count: int = 0
    initial_empty_flag_byte: Optional[int] = None

    def __post_init__(self):
        if self.kind not in KINDS:raise ValueError('Source storage scan kind required')
        raw(self.target_item_id,optional=True);raw(self.required_empty_count)
        raw(self.initial_empty_flag_byte,255,optional=True)
        if any(type(key) is not int or not 0<=key<192 or not isinstance(value,StorageSlot)
               for key,value in self.slots.items()):raise ValueError('Typed indexed source slot observations required')
        object.__setattr__(self,'slots',MappingProxyType(dict(self.slots)))

@dataclass(frozen=True)
class StorageScanResult:
    status: str
    returned_value: Optional[int] = None
    read_slots: Tuple[int,...] = ()
    missing: str = ''

class _Missing(Exception):pass

def scan_storage(observation):
    if not isinstance(observation,StorageScanObservation):raise ValueError('Typed storage scan required')
    obs=observation;read=[];empty_count=0;empty_flag=obs.initial_empty_flag_byte
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def result(value):return StorageScanResult('complete',value,tuple(read))
    def item_id(row,index):
        base=need(row.base_item_id,'slot%d base item ID'%index)
        extension=need(row.extension_id,'slot%d extension ID'%index)
        return (base+extension%1000)&0xffffffff
    try:
        limit=192 if obs.kind=='inn_free' else 48 if obs.kind=='vip_full' else 28
        target=need(obs.target_item_id,'source target item ID') if obs.kind in ('vip_existing','inn_existing') else None
        for index in range(limit):
            row=need(obs.slots.get(index),'slot%d observation'%index);read.append(index)
            pointer=need(row.pointer,'slot%d pointer'%index)
            if obs.kind=='vip_full':
                if pointer==0:return result(0)
                continue
            if obs.kind=='bag_full':
                if obs.required_empty_count==0:
                    if pointer==0:return result(0)
                else:
                    # Assembly reads this slot before testing the count, and does
                    # not test again after the final slot increments it.
                    if empty_count>=signed32(obs.required_empty_count):return result(0)
                    if pointer==0:empty_count+=1
                continue
            if obs.kind=='inn_free':
                decoded=0 if pointer==0 else item_id(row,index)
                if decoded==0:empty_count+=1
                continue
            if pointer==0:
                if obs.kind=='inn_existing':empty_flag=1
                continue
            quantity=need(row.quantity,'slot%d quantity DWORD'%index)
            decoded=item_id(row,index)
            flag=need(row.metadata_byte_6a,'slot%d metadata+6a BYTE'%index) if obs.kind=='inn_existing' else 1
            if decoded==target and flag==1:return result(quantity)
        if obs.kind in ('vip_full','bag_full'):return result(1)
        if obs.kind=='inn_free':return result(empty_count)
        if obs.kind=='vip_existing':return result(0)
        flag=need(empty_flag,'uninitialized EBP-4a stack BYTE in no-empty/no-match path')
        return result(0 if flag!=0 else 0xffffffff)
    except _Missing as exc:return StorageScanResult('needs_observation',read_slots=tuple(read),missing=str(exc))
