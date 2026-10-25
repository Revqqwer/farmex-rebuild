import json,unittest
from pathlib import Path
from dataclasses import replace
from profiles import Profiles
from loot_configuration import GENERAL,FILTER,MODE_PATHS,compile_loot_panel
from loot_pipeline import LootRecordProducer,replay_loot_pipeline
from loot_classifier import LootListObservation,LootMetadataObservation
from loot_name_cache import LootCacheRow
from operation_engine import LootRecord,LootSnapshot

class LootPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.defaults=Profiles(json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf-8'))).defaults
    def setUp(self):
        self.values=dict(self.defaults)
        self.values[GENERAL+'chAutoLoot']=True;self.values[GENERAL+'chLootBeforeWait']=False
        for i,path in enumerate(MODE_PATHS):self.values[path]=i==2
        self.values[FILTER+'chLootUpgrade']=True;self.values[FILTER+'txtLootUpgrade']='7'
        self.config=compile_loot_panel(self.values)
        self.record=LootRecord('bundle',0,item_phase=True,item_ids=(123,0,0,0,0,0,0,0))
        self.source=LootRecordProducer(LootListObservation({0:LootMetadataObservation(1,1,2,7,0)}),
            ('Fork','','','','','','',''))
        self.rows=(LootCacheRow('Fork',1),)
    def run_pass(self,records=None,now=1000,producers=None,rows=None,config=None,**kw):
        return replay_loot_pipeline(config or self.config,LootSnapshot(now,records or (self.record,),**kw),
            {'bundle':self.source} if producers is None else producers,self.rows if rows is None else rows)
    def test_lifecycle_classifier_cache_mask_and_intents_compose(self):
        p=self.run_pass();r=p.lifecycle.records[0]
        self.assertTrue(p.complete);self.assertEqual(p.status,'list_item_attempt')
        self.assertEqual((r.item_attempt_ms,r.list_state.classified,r.list_state.selected[0]),(1000,1,1))
        self.assertEqual([(i.item_id,i.slot) for i in p.lifecycle.intents],[(123,0)])
        self.assertFalse(r.slot_done[0]);self.assertEqual(p.cache_state.values[0],1)
    def test_missing_producer_retains_known_timer_prefix(self):
        p=self.run_pass(producers={})
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_loot_producer')
        self.assertEqual(p.lifecycle.records[0].item_attempt_ms,1000);self.assertEqual(p.lifecycle.intents,())
    def test_disabled_and_retry_gates_do_not_require_producer(self):
        disabled=replace(self.config,settings=replace(self.config.settings,enabled=False))
        self.assertEqual(self.run_pass(producers={},config=disabled).status,'blocked')
        self.assertEqual(self.run_pass(producers={},now=999).status,'scanned')
        self.assertEqual(self.run_pass(records=(replace(self.record,distance=16),),producers={}).status,'scanned')
    def test_unknown_metadata_does_not_advance_cache_or_mask(self):
        p=self.run_pass(producers={'bundle':LootRecordProducer(LootListObservation())})
        self.assertFalse(p.complete);self.assertIsNone(p.classification.cache)
        self.assertEqual(p.lifecycle.records[0].list_state.classified,0)
        self.assertEqual(p.lifecycle.records[0].item_attempt_ms,1000)
    def test_unknown_name_is_observation_gap_not_default_empty(self):
        p=self.run_pass(producers={'bundle':replace(self.source,names=None)})
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_name_observation')
        self.assertEqual(p.lifecycle.reason,'post-conversion names')
    def test_rejected_mask_is_removed_next_pass_not_same_invocation(self):
        p=self.run_pass(rows=(LootCacheRow('Fork',0),))
        self.assertEqual(len(p.lifecycle.records),1);self.assertEqual(p.lifecycle.records[0].list_state.discarded,1)
        p=self.run_pass(records=p.lifecycle.records,now=1001,producers={})
        self.assertEqual(p.status,'removed');self.assertEqual(p.lifecycle.records,())
    def test_cached_record_requires_no_new_producer_and_done_snapshot_controls_attempt(self):
        first=self.run_pass();record=first.lifecycle.records[0]
        p=self.run_pass(records=(record,),now=2000,producers={},rows=())
        self.assertTrue(p.complete);self.assertIsNone(p.classification.cache)
        self.assertEqual(len(p.lifecycle.intents),1)
        record=replace(record,slot_done=(True,False,False,False,False,False,False,False))
        p=self.run_pass(records=(record,),now=2000,producers={},rows=())
        self.assertEqual(p.lifecycle.intents,());self.assertTrue(p.lifecycle.records[0].list_state.selected[0])
    def test_earlier_open_intents_are_not_lost_before_item_helper(self):
        open_record=LootRecord('open',0,item_phase=False)
        p=self.run_pass(records=(open_record,self.record),open_state_allowed=True)
        self.assertEqual([i.kind for i in p.lifecycle.intents],['loot_open','loot_item'])
        self.assertEqual(p.lifecycle.classifier_reference,'bundle')
        self.assertEqual(p.lifecycle.records[0].open_attempt_ms,1000)
    def test_no_match_unknown_cache_does_not_fabricate_completion(self):
        p=self.run_pass(rows=())
        self.assertFalse(p.complete);self.assertEqual(p.lifecycle.intents,())
        self.assertEqual(p.lifecycle.reason,'slot0:cache_byte')
    def test_coins_only_path_needs_no_metadata_producer(self):
        record=replace(self.record,item_ids=(900000000,0,0,0,0,0,0,0))
        p=self.run_pass(records=(record,),producers={})
        self.assertTrue(p.complete);self.assertEqual(p.lifecycle.intents[0].item_id,900000000)
        self.assertEqual(p.classification.cache.writes,())
