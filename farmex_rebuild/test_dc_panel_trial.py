import json,unittest
import test_dc_full_chain as chain_fixture
from dc_panel_trial import *

class DCPanelTrialTests(unittest.TestCase):
    def setUp(self):
        self.values=dict(zip(DC_PANEL_INPUTS,(True,True)));self.trial=DCPanelTrial(lambda:(self.values,{}))
    def sample(self):return json.loads(example_dc_sample(self.trial.current_snapshot()))
    def source_sample(self):
        o=chain_fixture.DCFullChainTests().observation()
        def raw(v):return dict(entry_reached=v.entry_reached,values=dict(v.values),normal_returns=dict(v.normal_returns))
        return dict(panel_snapshot_sha256=dc_panel_digest(self.trial.current_snapshot()),parent=raw(o.parent),
                    consumer=raw(o.action.consumer),transfers={k:raw(v) for k,v in o.action.transfers.items()})

    def test_default_waits_and_empty_source_example_matches_panel_mode(self):
        p=self.trial.step('{}');self.assertEqual(p.needed,('parent',('entry','00459981')))
        for only,mode in ((True,'list'),(False,'scan')):
            self.values[DC_PANEL_INPUTS[1]]=only;p=self.trial.step(json.dumps(self.sample()))
            self.assertTrue(p.complete);self.assertEqual(p.action.consumer.kind,mode)
            self.assertEqual(p.write_intents,())

    def test_disabled_panel_skips_unreached_malformed_consumer(self):
        self.values[DC_PANEL_INPUTS[0]]=False;d=self.sample();d['consumer']='not used'
        p=self.trial.step(json.dumps(d));self.assertTrue(p.complete);self.assertIsNone(p.action)
        self.assertEqual(self.trial.shadow_stores,{})

    def test_panel_flags_cannot_be_overridden(self):
        for label,value in (('enabled_byte',0),('list_only_byte',0),('enabled_byte',True)):
            self.setUp();d=self.sample();d['parent']['values'][label]=value
            with self.assertRaises(ValueError):self.trial.step(json.dumps(d))
            self.assertIsNone(self.trial.last)

    def test_snapshot_rejection_keeps_past_stamp_but_not_old_prefix(self):
        d=self.sample();self.trial.step(json.dumps(d));past=dict(self.trial.shadow_stores)
        self.values[DC_PANEL_INPUTS[1]]=False
        with self.assertRaises(ValueError):self.trial.step(json.dumps(d))
        self.assertIsNone(self.trial.last);self.assertEqual(self.trial.prefix.write_intents,())
        self.assertEqual(self.trial.shadow_stores,past)

    def test_all_four_layers_continue_after_wait_gap_without_duplicate(self):
        d=self.source_sample();d['transfers']['row0.send']['normal_returns']['stub.wait']=False
        p=self.trial.step(json.dumps(d));self.assertEqual(len(p.write_intents),2)
        self.assertEqual(self.trial.shadow_stores,{})
        frame=self.trial.frame;d['transfers']['row0.send']['normal_returns']['stub.wait']=True
        p=self.trial.step(json.dumps(d));self.assertTrue(p.complete);self.assertIs(self.trial.frame,frame)
        self.assertEqual(self.trial.shadow_stores,{0x553ce4:(4,300010)})
        self.assertIs(self.trial.step(json.dumps(d)),p)

    def test_late_invalid_capture_clears_last_but_retains_write_prefix(self):
        d=self.source_sample();d['transfers']['row0.send']['values']['copied_root_dword']='invalid'
        with self.assertRaises(ValueError):self.trial.step(json.dumps(d))
        self.assertIsNone(self.trial.last);self.assertEqual(len(self.trial.prefix.write_intents),1)
        self.assertEqual(self.trial.shadow_stores,{})

    def test_unrelated_panel_change_does_not_restart_frame(self):
        self.trial.step(json.dumps(self.sample()));frame=self.trial.frame
        self.values['unrelated']=17;self.trial.step(json.dumps(self.sample()))
        self.assertIs(self.trial.frame,frame)
        with self.assertRaises(ValueError):dc_panel_snapshot(dict(zip(DC_PANEL_INPUTS,(1,False))))

if __name__=='__main__':unittest.main()
