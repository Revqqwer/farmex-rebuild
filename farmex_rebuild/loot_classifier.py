"""00415198 LIST classification/dispatch plans; no memory or native IO.

Metadata lookups and post00414a14 cache BYTEs are independent observations.
Calls record (helper, logical slot), not recovered native argument ABI. Name
conversion/cache matching and helper side effects remain outside this replay.
"""
from dataclasses import dataclass,field,replace
from typing import Mapping,Optional,Tuple

def raw(value,maximum,unknown=False):
    if unknown and value is None:return
    if type(value) is not int or not 0<=value<=maximum:raise ValueError('Raw unsigned field required')

@dataclass(frozen=True)
class LootListState:
    classified: int = 0              # record+33
    discarded: int = 0               # record+34
    selected: Tuple[int,...] = (0,)*8 # record+35..3c
    done: Tuple[int,...] = (0,)*8     # record+3d..44

    def __post_init__(self):
        raw(self.classified,255);raw(self.discarded,255)
        for values in (self.selected,self.done):
            if type(values) is not tuple or len(values)!=8:raise ValueError('Eight BYTEs required')
            for value in values:raw(value,255)

@dataclass(frozen=True)
class LootMetadataObservation:
    lookup: Optional[int] = None
    metadata: Optional[int] = None
    category: Optional[int] = None
    upgrade_value: Optional[int] = None
    price: Optional[int] = None
    cache_byte: Optional[int] = None

    def __post_init__(self):
        for value in (self.lookup,self.metadata,self.upgrade_value,self.price):raw(value,0xffffffff,True)
        for value in (self.category,self.cache_byte):raw(value,255,True)

@dataclass(frozen=True)
class LootListObservation:
    slots: Mapping[int,LootMetadataObservation] = field(default_factory=dict)
    cache_returned: Optional[bool] = None

    def __post_init__(self):
        if not isinstance(self.slots,Mapping):raise ValueError('Per-slot mapping required')
        for index,value in self.slots.items():
            raw(index,7)
            if not isinstance(value,LootMetadataObservation):raise ValueError('Typed slot observation required')
        if self.cache_returned is not None and type(self.cache_returned) is not bool:raise ValueError('Cache completion bool required')

@dataclass(frozen=True)
class LootListPlan:
    status: str
    state: LootListState
    complete: bool
    calls: Tuple[Tuple[str,int],...] = ()
    writes: Tuple[Tuple[int,int],...] = ()
    attempt_slots: Tuple[int,...] = ()
    reason: str = ''
    independently_verified: bool = False

class _Missing(Exception):pass

def plan_loot_list(item_ids,fields,observation,state=LootListState()):
    if type(item_ids) is not tuple or len(item_ids)!=8:raise ValueError('Eight raw item DWORDs required')
    for item in item_ids:raw(item,0xffffffff)
    if not isinstance(fields,Mapping) or not isinstance(observation,LootListObservation) or not isinstance(state,LootListState):
        raise ValueError('Fields and typed observation/state required')
    calls=[];writes=[];st=state
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def setting(offset,maximum=0xffffffff):
        value=need(fields.get(offset),'field:+%x'%offset);raw(value,maximum);return value
    def finish(status,slots=()):return LootListPlan(status,st,True,tuple(calls),tuple(writes),tuple(slots))
    try:
        if setting(4)!=3:return finish('not_list_mode')
        if st.classified==0:
            qualified=[False]*8;coin_first=False
            for index,item in enumerate(item_ids):
                if item==0:continue
                if index==0 and item==900000000:
                    coin_first=True;continue
                obs=observation.slots.get(index,LootMetadataObservation())
                calls.append(('00465514',index))
                if not need(obs.lookup,'slot%d:lookup'%index):continue
                calls.extend((('0045dbdc:resolver',index),('00465580',index),('00467908:name',index)))
                if not need(obs.metadata,'slot%d:metadata'%index):continue
                calls.extend((('0045dbdc:category',index),('0045dc44:upgrade',index)))
                category=need(obs.category,'slot%d:category'%index)
                upgrade=need(obs.upgrade_value,'slot%d:upgrade'%index)
                q=(setting(0x18,255)==1 and category!=3 and setting(0x1c)<=upgrade%10)
                if index==7 or not q:
                    calls.append(('00467820',index))
                    price=need(obs.price,'slot%d:price'%index)
                    # Raw category numbers are not promoted to game type names.
                    if category==0 and setting(0x21,255)!=0:q=True
                    if category==4 and setting(0x20,255)!=0:q=True
                    if setting(0x11,255)!=0 and setting(0x14)<=price:q=True
                qualified[index]=q
            # Source converts eight names then invokes cache updater even when
            # the first slot is coins. Cache read results may retain old BYTEs.
            calls.append(('00414a14',-1))
            if need(observation.cache_returned,'00414a14:completed') is not True:raise _Missing('00414a14:completed')
            selected=list(st.selected)
            for index,item in enumerate(item_ids):
                if not item:continue
                allowed=index==0 and coin_first
                if not allowed and qualified[index]:
                    obs=observation.slots.get(index,LootMetadataObservation())
                    allowed=need(obs.cache_byte,'slot%d:cache_byte'%index)==1
                if allowed:
                    selected[index]=1;writes.append((0x35+index,1))
                    st=replace(st,selected=tuple(selected))
            st=replace(st,selected=tuple(selected))
            if all(value==0 for value in selected):
                st=replace(st,discarded=1);writes.append((0x34,1))
            st=replace(st,classified=1);writes.append((0x33,1))
        slots=[]
        if st.classified and st.discarded==0:
            for index in range(8):
                if st.selected[index] and st.done[index]==0:
                    calls.append(('00414984',index));slots.append(index)
        return finish('item_attempt_plan' if slots else 'no_item_attempt',slots)
    except _Missing as exc:
        return LootListPlan('needs_observation',st,False,tuple(calls),tuple(writes),reason=str(exc))
