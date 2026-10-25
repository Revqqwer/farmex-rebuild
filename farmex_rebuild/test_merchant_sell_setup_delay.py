import unittest
from dataclasses import replace
from merchant_sell_setup_delay import SellSetupDelayObservation as Obs,plan_sell_setup_delay as plan
from operation_engine import MerchantRunner,MerchantKind,MerchantSettings,MerchantSnapshot

class SellSetupDelayTests(unittest.TestCase):
    def test_missing_clock_does_not_reach_display_or_setup(self):
        for o in (Obs(),Obs(0),Obs(0,None,0)):
            p=plan(o);self.assertFalse(p.complete);self.assertNotIn(('0042060c',),p.steps)
    def test_waiting_needs_opaque_countdown_return(self):
        p=plan(Obs(30,0,90999))
        self.assertFalse(p.complete);self.assertEqual(p.remaining_ms,1)
        self.assertEqual(p.steps[-1],('normal_span','004217d7','00421924'))
        p=plan(Obs(30,0,90999,True));self.assertTrue(p.complete);self.assertEqual(p.status,'waiting')
    def test_boundary_requires_two_separate_ready_spans(self):
        for returns in ((),(True,),(True,False)):
            p=plan(Obs(30,0,91000,ready_span_returns=returns))
            self.assertTrue(p.delay_due);self.assertFalse(p.complete);self.assertNotIn(('0042060c',),p.steps)
        p=plan(Obs(30,0,91000,ready_span_returns=(True,True)))
        self.assertTrue(p.complete);self.assertEqual(p.steps[-1],('0042060c',))
        self.assertIsNone(p.remaining_ms)
    def test_add_and_product_wrap_before_sign_extension(self):
        p=plan(Obs(0xffffffc3,0,0,ready_span_returns=(True,True))) # -61+61 ==0
        self.assertEqual(p.interval_signed,0);self.assertTrue(p.delay_due)
        p=plan(Obs(2147423,0,0,ready_span_returns=(True,True)))
        self.assertEqual(p.interval_signed,-2147483296);self.assertTrue(p.delay_due)
    def test_full_stamp_and_signed64_elapsed_not_dword_wrap(self):
        p=plan(Obs(0,0xfffffff0,10,True))
        self.assertEqual(p.elapsed_signed,-4294967270);self.assertFalse(p.delay_due)
        p=plan(Obs(0,1<<32,61000,True))
        self.assertLess(p.elapsed_signed,0);self.assertFalse(p.delay_due)
    def test_signed64_subtraction_wrap_is_preserved(self):
        p=plan(Obs(0,(1<<64)-1,60999,ready_span_returns=(True,True)))
        self.assertEqual(p.elapsed_signed,61000);self.assertTrue(p.delay_due)
    def test_runner_does_not_call_setup_on_missing_ui_return(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=2
        p=r.tick(MerchantSnapshot(9999999,setup_result=0,sell_setup_delay_inputs=Obs(0,0,61000)))
        self.assertEqual(p.status,'needs_adapter');self.assertFalse(r.setup_seen)
        p=r.tick(MerchantSnapshot(10000000,setup_result=0,sell_setup_delay_inputs=Obs(0,0,61000,ready_span_returns=(True,True))))
        self.assertEqual(p.status,'setup_gate_armed');self.assertTrue(r.setup_seen)
    def test_bound_raw_stamp_remains_separate_from_outer_restart_clock(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=2;r.restarting=True
        p=r.tick(MerchantSnapshot(10000000,sell_setup_delay_inputs=Obs(0,1<<32,10,True)))
        self.assertEqual(p.status,'waiting');self.assertEqual(r.phase,2)
    def test_raw_types_and_receipts(self):
        for field in ('extra_wait_dword','started_stamp_qword','tick_dword'):
            with self.assertRaises(ValueError):Obs(**{field:True})
            with self.assertRaises(ValueError):Obs(**{field:-1})
        with self.assertRaises(ValueError):Obs(ready_span_returns=[True,True])
        with self.assertRaises(ValueError):Obs(ready_span_returns=(True,1))
        with self.assertRaises(ValueError):MerchantSnapshot(1,sell_setup_delay_inputs=0)

if __name__=='__main__':unittest.main()
