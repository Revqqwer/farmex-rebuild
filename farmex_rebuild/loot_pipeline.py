"""00416c10 lifecycle ->00415198 LIST/cache composition. No game IO or ACK.

Incomplete results expose prospective known prefixes, including the retry clock;
they do not prove the invocation returned. A real adapter must retain/resume the
pending invocation rather than dispatch a new pass from an incomplete result.
"""
from dataclasses import dataclass,replace
from typing import Optional,Tuple
from collections.abc import Mapping
from loot_configuration import LootPanelConfiguration
from loot_classifier import LootListObservation,LootListState
from loot_name_cache import LootCacheState,classify_loot_with_name_cache
from operation_engine import LootDecision,LootSnapshot,OperationIntent,loot_step

@dataclass(frozen=True)
class LootRecordProducer:
    metadata:LootListObservation
    names:Optional[Tuple[str,...]]=None
    input_nonempty:Optional[Tuple[bool,...]]=None

    def __post_init__(self):
        if not isinstance(self.metadata,LootListObservation):raise ValueError('Typed metadata observations required')

@dataclass(frozen=True)
class LootPipelineDecision:
    status:str
    lifecycle:LootDecision
    classification:object
    cache_state:LootCacheState
    complete:bool
    independently_verified:bool=False

def replay_loot_pipeline(configuration,snapshot,producers,cache_rows,*,cache_state=LootCacheState()):
    if not isinstance(configuration,LootPanelConfiguration) or not isinstance(snapshot,LootSnapshot) or not isinstance(producers,Mapping) or not isinstance(cache_state,LootCacheState):
        raise ValueError('Typed loot config/snapshot/producers/cache required')
    if configuration.settings is None:
        lifecycle=LootDecision(configuration.status,snapshot.records,reason=configuration.reason)
        return LootPipelineDecision(configuration.status,lifecycle,None,cache_state,False)
    lifecycle=loot_step(configuration.settings,snapshot)
    reference=lifecycle.classifier_reference
    if reference is None:return LootPipelineDecision(lifecycle.status,lifecycle,None,cache_state,lifecycle.status!='needs_clock_observation')
    record=next(r for r in lifecycle.records if r.reference==reference)
    state=record.list_state or LootListState()
    # Done bytes come from the current source record snapshot; attempts do not
    # fabricate completion or server receipt. Nonzero source bytes are bool here.
    state=replace(state,done=tuple(int(v) for v in record.slot_done))
    producer=producers.get(reference)
    if producer is None and not state.classified and all(item==0 or (i==0 and item==900000000) for i,item in enumerate(record.item_ids)):
        # Source first-slot coins/empty slots build no item name/metadata.
        producer=LootRecordProducer(LootListObservation(),('',)*8,(False,)*8)
    if producer is None and not state.classified:
        return LootPipelineDecision('needs_loot_producer',lifecycle,None,cache_state,False)
    if producer is None:producer=LootRecordProducer(LootListObservation())
    if not isinstance(producer,LootRecordProducer):raise ValueError('Typed per-record producer required')
    result=classify_loot_with_name_cache(record.item_ids,configuration.fields,producer.metadata,
        producer.names,cache_rows,record_state=state,cache_state=cache_state,input_nonempty=producer.input_nonempty)
    classification=result.classification
    records=tuple(replace(r,list_state=classification.state) if r.reference==reference else r for r in lifecycle.records)
    complete=classification.complete and (result.cache is None or result.cache.complete)
    intents=lifecycle.intents
    if complete:
        intents+=tuple(OperationIntent('loot_item',reference,item_id=record.item_ids[i],slot=i)
                       for i in classification.attempt_slots)
    combined=replace(lifecycle,status='list_item_attempt' if complete else result.status,records=records,intents=intents,
        reason=classification.reason,classifier_reference=reference)
    return LootPipelineDecision(combined.status,combined,result,result.cache_state,complete)
