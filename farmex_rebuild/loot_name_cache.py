"""00414a14 exact post-conversion Unicode cache replay, no game IO.

Input names are already converted source Unicode strings. This does not choose a
Windows codepage or implement00467908 game item naming. Initial BYTEs may remain
unknown when no row matches. Local panel compilation reads TOPLA display values;
it does not emulate original JSON loading, runtime initialization or click gates.
"""
from dataclasses import dataclass,replace
from typing import Optional,Tuple
from collections.abc import Mapping
from loot_classifier import (LootListState,LootListObservation,LootMetadataObservation,plan_loot_list,raw)
from source_unicode import utf16_key as unicode_key

LOOT_LIST_PATH='frmMain/MainTab/SheetItem/lwItemList'

@dataclass(frozen=True)
class LootCacheRow:
    name:str
    take_byte:int

    def __post_init__(self):unicode_key(self.name);raw(self.take_byte,255)

@dataclass(frozen=True)
class LootCacheState:
    values:Tuple[Optional[int],...]=(None,)*8

    def __post_init__(self):
        if type(self.values) is not tuple or len(self.values)!=8:raise ValueError('Eight optional cache BYTEs required')
        for value in self.values:raw(value,255,True)

@dataclass(frozen=True)
class LootCachePlan:
    status:str
    state:LootCacheState
    complete:bool
    # Logical(row index1-based, slot0-based, new BYTE), not native addresses.
    writes:Tuple[Tuple[int,int,int],...]=()
    reason:str=''
    independently_verified:bool=False

def compile_loot_name_cache(lists):
    if not isinstance(lists,Mapping) or not isinstance(lists.get(LOOT_LIST_PATH),list):raise ValueError('Loot panel list required')
    rows=[]
    for row in lists[LOOT_LIST_PATH]:
        if not isinstance(row,dict) or type(row.get('caption')) is not str:raise ValueError('Loot row caption required')
        subitems=row.get('subitems')
        if not isinstance(subitems,list) or not subitems or subitems[0] not in ('EVET','HAYIR'):
            raise ValueError('Source TOPLA value must be EVET or HAYIR')
        rows.append(LootCacheRow(row['caption'],1 if subitems[0]=='EVET' else 0))
    return tuple(rows)

def update_loot_name_cache(names,rows,state=LootCacheState(),*,source_count=None,input_nonempty=None):
    if type(names) is not tuple or len(names)!=8:raise ValueError('Eight Unicode input names required')
    keys=tuple(unicode_key(name) for name in names)
    # Source guard is an ANSI comparison before conversion to Unicode. A local
    # fixture may derive it from text; a runtime adapter can supply separate raw
    # guard observations without assuming an unknown codepage conversion.
    guards=tuple(bool(key) for key in keys) if input_nonempty is None else input_nonempty
    if type(guards) is not tuple or len(guards)!=8 or any(type(v) is not bool for v in guards):
        raise ValueError('Eight pre-conversion nonempty guards required')
    if type(rows) is not tuple or any(not isinstance(row,LootCacheRow) for row in rows) or not isinstance(state,LootCacheState):
        raise ValueError('Typed row tuple and cache state required')
    count=len(rows) if source_count is None else source_count
    raw(count,0xffffffff)
    signed=count-0x100000000 if count & 0x80000000 else count
    values=list(state.values);writes=[]
    # All-empty inputs do not access row names/flags in the source body.
    if not any(guards):return LootCachePlan('unchanged_empty_names',state,True)
    for index in range(max(0,signed)):
        if index>=len(rows):return LootCachePlan('needs_observation',LootCacheState(tuple(values)),False,
            tuple(writes),'source cache row%d'%(index+1))
        row=rows[index];key=unicode_key(row.name)
        for slot,name in enumerate(keys):
            if guards[slot] and name==key:
                value=1 if row.take_byte==1 else 0
                values[slot]=value;writes.append((index+1,slot,value))
    return LootCachePlan('cache_updated',LootCacheState(tuple(values)),True,tuple(writes))

@dataclass(frozen=True)
class LootCachedClassification:
    status:str
    cache:object
    classification:object
    cache_state:LootCacheState
    independently_verified:bool=False

def classify_loot_with_name_cache(item_ids,fields,observation,names,rows,*,
                                  record_state=LootListState(),cache_state=LootCacheState(),source_count=None,input_nonempty=None):
    """Compose pure models; observations remain separate from native helper IO."""
    if not isinstance(fields,Mapping) or not isinstance(record_state,LootListState) or not isinstance(cache_state,LootCacheState) or not isinstance(observation,LootListObservation):
        raise ValueError('Typed record/cache/metadata observations required')
    if record_state.classified or fields.get(4)!=3:
        result=plan_loot_list(item_ids,fields,observation,record_state)
        return LootCachedClassification(result.status,None,result,cache_state)
    # Preserve source ordering: missing metadata stops before cache matching.
    probe=plan_loot_list(item_ids,fields,replace(observation,cache_returned=None),record_state)
    if probe.status!='needs_observation' or probe.reason!='00414a14:completed':
        return LootCachedClassification(probe.status,None,probe,cache_state)
    if names is None:
        pending=replace(probe,reason='post-conversion names')
        return LootCachedClassification('needs_name_observation',None,pending,cache_state)
    if type(names) is not tuple or len(names)!=8:raise ValueError('Eight post-conversion names required')
    effective_names=tuple('' if item==0 or (index==0 and item==900000000)
        or observation.slots.get(index,LootMetadataObservation()).lookup==0 else names[index]
        for index,item in enumerate(item_ids))
    guards=None
    if input_nonempty is not None:
        if type(input_nonempty) is not tuple or len(input_nonempty)!=8:raise ValueError('Eight input guards required')
        guards=tuple(False if item==0 or(index==0 and item==900000000)
            or observation.slots.get(index,LootMetadataObservation()).lookup==0 else input_nonempty[index]
            for index,item in enumerate(item_ids))
    cache=update_loot_name_cache(effective_names,rows,cache_state,source_count=source_count,input_nonempty=guards)
    if not cache.complete:return LootCachedClassification('cache_incomplete',cache,probe,cache_state)
    slots={index:replace(observation.slots.get(index,LootMetadataObservation()),cache_byte=value)
           for index,value in enumerate(cache.state.values)}
    result=plan_loot_list(item_ids,fields,LootListObservation(slots,True),record_state)
    return LootCachedClassification(result.status,cache,result,cache.state)
