import unittest
from dataclasses import replace
from merchant_sell_close_wait import SellCloseWaitObservation as Obs,plan_sell_close_wait as plan
from operation_engine import MerchantRunner,MerchantKind,MerchantSettings,MerchantSnapshot

class SellCloseWaitTests(unittest.TestCase):
    def test_clear_pending_needs_no_clock_and_only_advances_phase(self):
        p=plan(Obs(0));self.assertTrue(p.complete);self.assertEqual(p.phase_dword,2)
        self.assertEqual(p.writes,((4,4,2),));self.assertIsNone(p.clock_plan)
        self.assertEqual(p.steps,(('read','+18'),))
    def test_missing_pending_tick_and_stamp_never_mean_success(self):
        for o in (Obs(),Obs(1),Obs(1,None,10)):
            p=plan(o);self.assertFalse(p.complete);self.assertEqual(p.phase_dword,1)
    def test_9999_and_10000_have_separate_timeout_receipts(self):
        o=Obs(255,10,10009);p=plan(o)
        self.assertTrue(p.complete);self.assertEqual(p.status,'waiting');self.assertEqual(p.clock_plan.remaining_ms,1)
        o=replace(o,tick_dword=10010);p=plan(o)
        self.assertFalse(p.complete);self.assertEqual(p.steps[-1],('normal_span','00421091','004210fd'))
        p=plan(replace(o,message_span_returned=True));self.assertFalse(p.complete)
        self.assertEqual(p.steps[-1],('0040ae0c',0x561f34,0))
        p=plan(replace(o,message_span_returned=True,stop_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.status,'timed_out');self.assertEqual(p.writes,())
    def test_stop_receipt_does_not_skip_missing_message(self):
        p=plan(Obs(1,0,10000,False,True))
        self.assertFalse(p.complete);self.assertNotIn('0040ae0c',[s[0] for s in p.steps])
    def test_raw_clock_wrap_uses_full_stamp_signed64(self):
        p=plan(Obs(1,0xfffffff0,10));self.assertEqual(p.status,'waiting')
        self.assertEqual(p.clock_plan.elapsed_signed,-4294967270)
        self.assertEqual(plan(Obs(1,1<<32,10000)).status,'waiting')
    def runner(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=1;r.phase_ms=10;return r
    def test_runner_waits_on_source_clock_and_holds_missing_returns(self):
        r=self.runner();p=r.tick(MerchantSnapshot(10000000,close_pending=True,sell_close_wait_inputs=Obs(1,10,11)))
        self.assertEqual(p.status,'waiting');self.assertEqual(p.remaining_ms,9999)
        p=r.tick(MerchantSnapshot(10000001,close_pending=True,sell_close_wait_inputs=Obs(1,10,10010)))
        self.assertEqual(p.status,'needs_adapter');self.assertTrue(r.active)
        p=r.tick(MerchantSnapshot(10000002,close_pending=True,sell_close_wait_inputs=Obs(1,10,10010,True,True)))
        self.assertEqual(p.reason,'close_timeout');self.assertFalse(r.active)
    def test_runner_checks_known_pending_and_reached_stamp(self):
        for o in (Obs(0),Obs(1,11,12)):
            r=self.runner()
            with self.assertRaises(ValueError):r.tick(MerchantSnapshot(20,close_pending=True,sell_close_wait_inputs=o))
        r=self.runner();p=r.tick(MerchantSnapshot(20,close_pending=False,sell_close_wait_inputs=Obs(0,999)))
        self.assertEqual(p.status,'phase_changed');self.assertEqual(r.phase,2)
        r.start();self.assertIsNone(r.last_sell_close_wait_plan)
    def test_types(self):
        for field in ('pending_byte','close_stamp_qword','tick_dword'):
            with self.assertRaises(ValueError):Obs(**{field:True})
            with self.assertRaises(ValueError):Obs(**{field:-1})
        with self.assertRaises(ValueError):Obs(message_span_returned=1)
        with self.assertRaises(ValueError):MerchantSnapshot(1,sell_close_wait_inputs=0)

if __name__=='__main__':unittest.main()
