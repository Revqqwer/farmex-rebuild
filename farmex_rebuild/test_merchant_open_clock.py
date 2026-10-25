import unittest
from merchant_open_clock import BuyOpenClockSample as Sample,plan_buy_open_wait as plan
from operation_engine import MerchantRunner,MerchantSettings,MerchantKind,MerchantSnapshot

class MerchantOpeningClockTests(unittest.TestCase):
    def test_pending_clear_does_not_need_clock(self):
        p=plan(0);self.assertEqual(p.status,'clear_path');self.assertIsNone(p.elapsed_bits)
    def test_missing_clock_is_not_tick_zero(self):
        self.assertEqual(plan(255).status,'needs_clock')
    def test_exact_10000_boundary(self):
        for elapsed,due in ((0,False),(9999,False),(10000,True),(10001,True)):
            p=plan(1,Sample(77+elapsed,77));self.assertEqual(p.timeout_due,due)
    def test_tick_rollover_is_negative_signed64(self):
        p=plan(1,Sample(10,0xfffffff0))
        self.assertFalse(p.timeout_due);self.assertEqual(p.elapsed_signed,10-0xfffffff0)
        self.assertGreater(p.remaining_ms,1<<32)
    def test_positive_high_dword_reaches_timeout(self):
        # Raw, unusual stamp: subtraction wraps into positive signed64.
        p=plan(1,Sample(0,0xfffffffe00000000))
        self.assertTrue(p.timeout_due);self.assertEqual(p.elapsed_signed,2<<32)
    def test_negative_high_dword_waits(self):
        p=plan(1,Sample(0xffffffff,1<<32))
        self.assertEqual(p.elapsed_signed,-1);self.assertEqual(p.remaining_ms,10001)
    def test_signed64_extremes(self):
        self.assertFalse(plan(1,Sample(0,1<<63)).timeout_due)
        self.assertTrue(plan(1,Sample(0,(1<<63)+1)).timeout_due)
    def test_raw_field_validation(self):
        for args in ((True,0),(1<<32,0),(0,-1),(0,1<<64)):
            with self.assertRaises(ValueError):Sample(*args)
        with self.assertRaises(ValueError):plan(True)
    def runner(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.BUY));r.start();r.phase=4
        return r
    def test_bound_runner_uses_source_sample_not_monotonic_delta(self):
        r=self.runner()
        p=r.tick(MerchantSnapshot(1<<33,opening_pending=True,buy_open_clock=Sample(10,0xfffffff0)))
        self.assertEqual(p.status,'waiting');self.assertTrue(r.active);self.assertEqual(r.phase,4)
    def test_due_uses_existing_local_stop_policy(self):
        r=self.runner()
        p=r.tick(MerchantSnapshot(1,opening_pending=True,buy_open_clock=Sample(10001,1)))
        self.assertEqual(p.status,'stopped');self.assertEqual(r.reason,'open_timeout')
        self.assertEqual(p.intents,()) # Source global/string/UI effects are NOT fabricated.
    def test_clear_pending_takes_priority_over_due_clock(self):
        r=self.runner()
        p=r.tick(MerchantSnapshot(1,opening_pending=False,buy_open_clock=Sample(10001,1)))
        self.assertEqual(r.phase,5);self.assertTrue(r.active)
    def test_bound_input_is_typed(self):
        with self.assertRaises(ValueError):MerchantSnapshot(1,buy_open_clock=0)

if __name__=='__main__':unittest.main()
