import unittest
from dataclasses import replace
from operation_engine import LootSettings,LootRecord,LootSnapshot,LootClockSamples,loot_step
import test_loot_pipeline as pipeline_fixture
from loot_pipeline import replay_loot_pipeline

class LootClockTests(unittest.TestCase):
    def record(self,**kwargs):
        values=dict(reference='x',created_ms=0,item_ids=(1,0,0,0,0,0,0,0));values.update(kwargs)
        return LootRecord(**values)
    def step(self,record,now,settings=LootSettings(),**kwargs):
        return loot_step(settings,LootSnapshot(now,(record,),**kwargs))
    def test_open_retry_999_1000_across_dword_wrap(self):
        r=self.record(created_ms=0xfffffc18,open_attempt_ms=0xfffffc18)
        self.assertEqual(self.step(r,0xffffffff,open_state_allowed=True).intents,())
        p=self.step(r,0,open_state_allowed=True)
        self.assertEqual(p.intents[0].kind,'loot_open');self.assertEqual(p.records[0].open_attempt_ms,0)
    def test_wait_strict1000_1001_across_wrap(self):
        r=self.record(created_ms=0xfffffc18,open_attempt_ms=0xfffffc18)
        settings=LootSettings(wait_enabled=True,wait_ms=1000)
        self.assertEqual(self.step(r,0,settings,open_state_allowed=True).intents,())
        self.assertEqual(len(self.step(r,1,settings,open_state_allowed=True).intents),1)
    def test_item_retry_and_stamp_zero_at_wrap(self):
        r=self.record(created_ms=0xfffffc18,item_attempt_ms=0xfffffc18,item_phase=True)
        self.assertEqual(self.step(r,0xffffffff).intents,())
        p=self.step(r,0);self.assertEqual(p.records[0].item_attempt_ms,0)
        self.assertEqual(p.intents[0].item_id,1)
    def test_expiry16999_17000_across_wrap(self):
        r=self.record(created_ms=(-16999)&0xffffffff)
        self.assertEqual(len(self.step(r,0).records),1)
        self.assertEqual(self.step(r,1).reason,'local_expiry')
    def test_numerically_future_timestamp_keeps_source_unsigned_effect(self):
        r=self.record(created_ms=1,open_attempt_ms=1)
        p=self.step(r,0,open_state_allowed=True)
        self.assertEqual(p.reason,'local_expiry');self.assertEqual(len(p.intents),1)
    def test_independent_retry_stamp_and_expiry_samples(self):
        r=self.record()
        p=self.step(r,999,open_state_allowed=True,
            clock_samples={'x':LootClockSamples(retry=1000,stamp=1005,expiry=1006)})
        self.assertEqual(p.records[0].open_attempt_ms,1005);self.assertEqual(len(p.intents),1)
    def test_wait_shortcircuit_skips_unknown_retry_but_fresh_expiry_runs(self):
        p=self.step(self.record(item_phase=True),999,LootSettings(wait_enabled=True,wait_ms=1000),
            clock_samples={'x':LootClockSamples(wait=999,expiry=17000)})
        self.assertEqual(p.reason,'local_expiry');self.assertEqual(p.intents,())
    def test_unknown_open_stamp_keeps_known_call_intent_prefix(self):
        p=self.step(self.record(),1000,open_state_allowed=True,clock_samples={'x':LootClockSamples(retry=1000)})
        self.assertEqual(p.status,'needs_clock_observation');self.assertEqual(p.reason,'x:stamp')
        self.assertEqual(len(p.intents),1);self.assertEqual(p.records[0].open_attempt_ms,0)
    def test_disposal_and_blocked_gates_require_no_clock_samples(self):
        p=self.step(self.record(item_phase=True,disposed_flags=(True,False,False)),0,clock_samples={})
        self.assertEqual(p.reason,'disposal_flag')
        p=self.step(self.record(),0,clock_samples={},global_blocked=True)
        self.assertEqual(p.status,'blocked')
    def test_each_record_has_its_own_clock_and_prefix_is_preserved(self):
        a=self.record(reference='a');b=self.record(reference='b')
        p=loot_step(LootSettings(),LootSnapshot(0,(a,b),open_state_allowed=True,
            clock_samples={'a':LootClockSamples(retry=1000,stamp=1001,expiry=1002)}))
        self.assertEqual(p.status,'needs_clock_observation');self.assertEqual(p.reason,'b:retry')
        self.assertEqual(p.records[0].open_attempt_ms,1001);self.assertEqual(len(p.intents),1)
    def test_pipeline_unknown_clock_is_not_completed_callback(self):
        f=pipeline_fixture.LootPipelineTests();f.setUpClass();f.setUp()
        snapshot=LootSnapshot(0,(f.record,),clock_samples={'bundle':LootClockSamples(retry=1000)})
        p=replay_loot_pipeline(f.config,snapshot,{},())
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_clock_observation')
    def test_raw_dword_clock_and_wait_validation(self):
        for build in (lambda:LootClockSamples(stamp=True),lambda:LootClockSamples(retry=-1),
                      lambda:self.record(created_ms=0x100000000),lambda:LootSettings(wait_ms=0x100000000)):
            with self.assertRaises(ValueError):build()
