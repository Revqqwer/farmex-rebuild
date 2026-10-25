import unittest
from dataclasses import replace
from merchant_sell_failure import SellFailureObservation as Obs,plan_sell_failure as plan
from operation_engine import MerchantRunner,MerchantSettings,MerchantKind,MerchantSnapshot

class SellFailureTests(unittest.TestCase):
    def obs(self,**kw):return replace(Obs(header_span_returns=(True,True),alarm_byte=0),**kw)
    def test_header_and_alarm_precede_policy(self):
        p=plan(Obs(policy_results=(0,)));self.assertFalse(p.complete)
        self.assertNotIn(('read','+d4',0),p.steps)
        p=plan(self.obs(alarm_byte=1,policy_results=(0,)))
        self.assertFalse(p.complete);self.assertNotIn(('read','+d4',0),p.steps)
    def test_stop_message_must_return_before_stop(self):
        o=self.obs(policy_results=(0,),stop_returned=True)
        p=plan(o);self.assertFalse(p.complete);self.assertFalse(any(s[0]=='0040ae0c' for s in p.steps))
        p=plan(replace(o,branch_span_returns=(True,)))
        self.assertTrue(p.complete);self.assertEqual(p.status,'stop_returned');self.assertEqual(p.writes,())
    def test_disconnect_orders_stop_disconnect_then_notification(self):
        o=self.obs(policy_results=(7,1),branch_span_returns=(True,))
        p=plan(o);self.assertFalse(p.complete);self.assertFalse(any(s[0]=='004c7e0c' for s in p.steps))
        p=plan(replace(o,stop_returned=True));self.assertFalse(p.complete);self.assertEqual(p.steps[-1],('004c7e0c',0x561ef8))
        p=plan(replace(o,stop_returned=True,disconnect_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.status,'disconnect_returned')
    def test_policy_field_is_fresh_at_each_comparison(self):
        p=plan(self.obs(policy_results=(1,0,2)))
        self.assertFalse(p.complete);self.assertEqual(p.steps[-1],('read','+90'))
        self.assertEqual([s for s in p.steps if s[:2]==('read','+d4')],[('read','+d4',0),('read','+d4',1),('read','+d4',2)])
        p=plan(self.obs(policy_results=(1,)))
        self.assertFalse(p.complete);self.assertIn('read1',p.missing)
    def test_unknown_final_policy_does_not_stop(self):
        p=plan(self.obs(policy_results=(0xffffffff,0xffffffff,0xffffffff)))
        self.assertTrue(p.complete);self.assertEqual(p.status,'unhandled_policy');self.assertEqual(p.writes,())
    def test_bank_writes_prefix_before_status_and_route_spans(self):
        o=self.obs(policy_results=(2,2,2),status_byte_90=0,setup_gate_byte=0)
        p=plan(o);self.assertFalse(p.complete);self.assertEqual(p.phase_dword,2);self.assertEqual(p.prospective_phase_dword,0)
        self.assertEqual(p.writes,((0x58,1,1),(4,4,0)))
        p=plan(replace(o,branch_span_returns=(True,True)));self.assertFalse(p.complete)
        p=plan(replace(o,branch_span_returns=(True,True),route_span_returned=True))
        self.assertTrue(p.complete);self.assertEqual((p.phase_dword,p.setup_gate_byte),(0,1))
        p=plan(replace(o,setup_gate_byte=255,branch_span_returns=(True,True),route_span_returned=True))
        self.assertEqual(p.writes,((4,4,0),));self.assertEqual(p.setup_gate_byte,255)
    def test_nonzero_status_takes_message_stop_path_and_skips_gate(self):
        p=plan(self.obs(policy_results=(2,2,2),status_byte_90=255,branch_span_returns=(True,),stop_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.status,'bank_unavailable_stop_returned')
        self.assertNotIn(('read','+58'),p.steps);self.assertEqual(p.writes,())
    def runner(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=2;return r
    def test_runner_gaps_cannot_fall_back_to_legacy_policy(self):
        r=self.runner();o=self.obs(policy_results=(0,))
        p=r.tick(MerchantSnapshot(61000,setup_result=1,sell_failure_inputs=o))
        self.assertEqual(p.status,'needs_adapter');self.assertTrue(r.active)
        p=r.tick(MerchantSnapshot(61001,setup_result=1,sell_failure_inputs=replace(o,branch_span_returns=(True,),stop_returned=True)))
        self.assertEqual(p.status,'stopped');self.assertFalse(r.active)
    def test_runner_bank_checks_gate_and_does_not_commit_partial_phase(self):
        r=self.runner();o=self.obs(policy_results=(2,2,2),status_byte_90=0,setup_gate_byte=0)
        p=r.tick(MerchantSnapshot(61000,setup_result=1,sell_failure_inputs=o))
        self.assertEqual(p.status,'needs_adapter');self.assertEqual(r.phase,2)
        p=r.tick(MerchantSnapshot(61001,setup_result=1,sell_failure_inputs=replace(o,branch_span_returns=(True,True),route_span_returned=True)))
        self.assertEqual(p.status,'bank_route');self.assertEqual(r.phase,0);self.assertTrue(r.setup_seen)
        r=self.runner()
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(61000,setup_result=1,sell_failure_inputs=replace(o,setup_gate_byte=1)))
    def test_types_and_legacy_gate_conflict(self):
        with self.assertRaises(ValueError):Obs(policy_results=(True,))
        with self.assertRaises(ValueError):Obs(header_span_returns=(True,1))
        with self.assertRaises(ValueError):MerchantSnapshot(1,sell_failure_inputs=0)
        r=self.runner()
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(61000,setup_result=1,bank_route_allowed=True,sell_failure_inputs=self.obs()))

if __name__=='__main__':unittest.main()
