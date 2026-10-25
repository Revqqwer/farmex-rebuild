"""Richard004edc40 candidate count, including duplicate cache matches."""
from dataclasses import dataclass,field
from types import MappingProxyType
from typing import Mapping,Optional,Tuple

STARTUP_SLOTS=(1,3,6,8,10,12,13)


def dword(value):
    if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):
        raise ValueError('Observed DWORD or unknown required')


@dataclass(frozen=True)
class RepairSlot:
    item_id: Optional[int] = None
    durability: Optional[int] = None
    maximum: Optional[int] = None
    cache_slot_rereads: Optional[Tuple[Optional[int],...]] = None
    type_matches: Tuple[Optional[bool],Optional[bool]] = (None,None)

    def __post_init__(self):
        for value in (self.item_id,self.durability,self.maximum):dword(value)
        if self.cache_slot_rereads is not None:
            for value in self.cache_slot_rereads:dword(value)
            object.__setattr__(self,'cache_slot_rereads',tuple(self.cache_slot_rereads))
        if len(self.type_matches)!=2 or any(v is not None and type(v) is not bool for v in self.type_matches):
            raise ValueError('Two source type comparisons required')
        object.__setattr__(self,'type_matches',tuple(self.type_matches))


@dataclass(frozen=True)
class RepairInventoryObservation:
    slots: Mapping[int,RepairSlot]
    bag_enabled: Optional[bool] = None
    mode: Optional[int] = None
    cache_ids: Optional[Tuple[int,...]] = None

    def __post_init__(self):
        if any(type(k) is not int or not isinstance(v,RepairSlot) for k,v in self.slots.items()):
            raise ValueError('Typed source slots required')
        if self.bag_enabled is not None and type(self.bag_enabled) is not bool:raise ValueError('Observed bag gate required')
        dword(self.mode)
        if self.cache_ids is not None:
            for value in self.cache_ids:
                dword(value)
                if value is None:raise ValueError('Observed cache ID required')
            object.__setattr__(self,'cache_ids',tuple(self.cache_ids))
        object.__setattr__(self,'slots',MappingProxyType(dict(self.slots)))


@dataclass(frozen=True)
class RepairCandidateCount:
    status: str
    count: int = 0
    visited: Tuple[int,...] = ()
    missing: str = ''


class _Missing(Exception):pass


def count_repair_candidates(observation):
    if not isinstance(observation,RepairInventoryObservation):raise ValueError('Typed inventory observation required')
    count=0;visited=[]
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def damaged(index):
        visited.append(index)
        slot=need(observation.slots.get(index),'slot%d'%index)
        if need(slot.item_id,'slot%d item ID'%index)==0:return False
        return need(slot.durability,'slot%d durability'%index)<need(slot.maximum,'slot%d maximum'%index)
    try:
        for index in STARTUP_SLOTS:
            if damaged(index):count+=1
        if need(observation.bag_enabled,'bag gate'):
            for index in range(14,42):
                if not damaged(index):continue
                slot=observation.slots[index]
                mode=need(observation.mode,'mode')
                if mode==0:
                    cache=need(observation.cache_ids,'ordered cache')
                    if not cache:continue
                    rereads=need(slot.cache_slot_rereads,'slot%d cache rereads'%index)
                    if len(rereads)!=len(cache):raise ValueError('One slot reread per cache record required')
                    for cached_id,reread in zip(cache,rereads):
                        if need(reread,'slot%d cache item-ID reread'%index)==cached_id:count+=1
                elif mode==2:
                    for match in slot.type_matches:
                        if need(match,'slot%d type comparison'%index):count+=1;break
        return RepairCandidateCount('complete',count,tuple(visited))
    except _Missing as exc:return RepairCandidateCount('needs_observation',count,tuple(visited),str(exc))
