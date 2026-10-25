import json,unittest
from tp_protection_trial import *

class TPProtectionTrialTests(unittest.TestCase):
    def fixture(self):
        values=dict(zip(TP_INPUTS,(True,True,False)));trial=TPProtectionTrial(lambda:(values,{}))
        return values,trial,json.loads(example_tp_sample(tp_snapshot(values),b'\x27\x01\x0a'))
    def test_empty_sample_waits_for_settings_entry(self):
        _,trial,_=self.fixture();p=trial.step('27010a','{}')
        self.assertEqual(p.settings.needed,('entry','0046c0e1'));self.assertIsNone(p.dispatch)
    def test_stop_and_dc_follow_actual_panel_selection(self):
        for stop,label in ((True,'tp_stop'),(False,'tp_disconnect')):
            values,trial,data=self.fixture();values[TP_INPUTS[1]]=stop;values[TP_INPUTS[2]]=not stop
            data=json.loads(example_tp_sample(tp_snapshot(values),b'\x27\x01\x0a'));p=trial.step('27010a',json.dumps(data))
            self.assertTrue(p.dispatch.complete);self.assertIn(label,[c[2] for c in p.dispatch.child.calls])
            self.assertEqual(p.settings.stores[-1][2],1 if stop else 2)
            self.assertFalse(p.native_execution_verified or p.live_compatibility_verified)
    def test_notice_gap_resumes_same_dispatch_and_preserves_getters(self):
        _,trial,data=self.fixture();data['normal_returns']['notice_block']=False
        p=trial.step('27010a',json.dumps(data));self.assertFalse(p.dispatch.complete)
        self.assertEqual(p.dispatch.child.stores,());frame=trial.dispatch
        data['normal_returns']['notice_block']=True;data['values']['tick_eax']=1
        p=trial.step('27010a',json.dumps(data));self.assertTrue(p.dispatch.complete)
        self.assertIs(trial.dispatch,frame);self.assertEqual(p.dispatch.child.stores[0],(0x56209c,1,1))
        self.assertIs(trial.step('27010a',json.dumps(data)).dispatch,p.dispatch)
    def test_panel_and_packet_changes_reject_stale_examples(self):
        values,trial,data=self.fixture();trial.step('27010a',json.dumps(data));old=trial.dispatch
        values[TP_INPUTS[0]]=False
        with self.assertRaises(ValueError):trial.step('27010a',json.dumps(data))
        self.assertIsNone(trial.last);self.assertIsNone(trial.dispatch)
        data=json.loads(example_tp_sample(tp_snapshot(values),b'\x27\x01\x0a'))
        self.assertTrue(trial.step('27010a',json.dumps(data)).dispatch.complete);self.assertIsNot(trial.dispatch,old)
        with self.assertRaises(ValueError):trial.step('27020a',json.dumps(data))
    def test_panel_and_source_values_cannot_disagree_in_stable_fixture(self):
        _,trial,data=self.fixture();data['values']['action_first']=2
        with self.assertRaises(ValueError):trial.step('27010a',json.dumps(data))
        self.assertIsNone(trial.last)
    def test_source_entry_and_earlier_opcode_are_not_bypassed(self):
        values,trial,data=self.fixture();data['dispatcher_setup_returned']=False
        p=trial.step('27010a',json.dumps(data));self.assertEqual(p.dispatch.status,'needs_dispatcher_setup')
        data=json.loads(example_tp_sample(tp_snapshot(values),b'\x10'))
        p=trial.step('10',json.dumps(data));self.assertFalse(p.dispatch.complete)
        self.assertEqual(p.dispatch.status,'earlier_branch_not_bound');self.assertIsNone(p.dispatch.child)
    def test_disabled_tp_skips_action_reads_but_retains_source_notice(self):
        values,trial,data=self.fixture();values[TP_INPUTS[0]]=False
        data=json.loads(example_tp_sample(tp_snapshot(values),b'\x27\x01\x0a'))
        data['values']['action_first']=999 #Unreached input is deliberately not consumed.
        p=trial.step('27010a',json.dumps(data));self.assertTrue(p.dispatch.complete)
        self.assertEqual(p.dispatch.child.stores,((0x56209c,1,1),))
        self.assertFalse(any(c[2] in ('tp_stop','tp_disconnect') for c in p.dispatch.child.calls))
    def test_invalid_inputs_clear_result_and_reset_starts_fresh(self):
        _,trial,data=self.fixture();trial.step('27010a',json.dumps(data))
        for packet,text in (('xx','{}'),('27','[]'),('27','{bad')):
            with self.assertRaises(ValueError):trial.step(packet,text)
            self.assertIsNone(trial.last)
        trial.reset();self.assertIsNone(trial.snapshot);self.assertIsNone(trial.dispatch)

if __name__=='__main__':unittest.main()
