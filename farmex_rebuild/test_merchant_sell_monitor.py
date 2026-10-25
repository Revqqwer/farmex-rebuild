import unittest
from dataclasses import replace
from merchant_sell_monitor import SellMonitorObservation as Obs,plan_sell_monitor as plan
from operation_engine import MerchantRunner,MerchantKind,MerchantSettings,MerchantSnapshot

class SellMonitorTests(unittest.TestCase):
    def sample(self,**changes):return replace(Obs(1,1,0,59999,True),**changes)
    def test_disabled_does_not_require_time_or_ui(self):
        p=plan(Obs(reopen_byte=0))
        self.assertTrue(p.complete);self.assertEqual(p.phase_dword,6)
        self.assertEqual(p.steps,(('read','+c9'),));self.assertIsNone(p.timer_due)
    def test_each_reached_clock_operand_is_required(self):
        for field in ('reopen_byte','minutes_dword','tick_dword','established_stamp_qword'):
            p=plan(self.sample(**{field:None}))
            self.assertFalse(p.complete);self.assertEqual(p.phase_dword,6)
    def test_nonzero_raw_byte_enables(self):
        self.assertTrue(plan(self.sample(reopen_byte=255)).complete)
    def test_countdown_requires_separate_normal_return(self):
        for value in (None,False):
            p=plan(self.sample(display_span_returned=value))
            self.assertFalse(p.complete);self.assertEqual(p.phase_dword,6)
            self.assertEqual(p.display_seconds_signed,1);self.assertEqual(p.writes,())
        self.assertTrue(plan(self.sample()).complete)
    def test_two_idiv_instructions_not_difference_division(self):
        self.assertEqual(plan(self.sample(tick_dword=999)).display_seconds_signed,60)
        self.assertEqual(plan(self.sample(tick_dword=1,established_stamp_qword=1000)).display_seconds_signed,60)
    def test_boundary_skips_display_and_writes_phase_only(self):
        p=plan(self.sample(tick_dword=60000,display_span_returned=False))
        self.assertTrue(p.complete);self.assertTrue(p.timer_due);self.assertEqual(p.phase_dword,0)
        self.assertEqual(p.writes,((4,0,'timer'),));self.assertIsNone(p.display_seconds_signed)
        self.assertFalse(any(s[0]=='normal_span' for s in p.steps))
    def test_low_stamp_and_signed32_wrap(self):
        p=plan(self.sample(tick_dword=10,established_stamp_qword=0x1234fffffff0))
        self.assertEqual(p.elapsed_signed,26);self.assertFalse(p.timer_due)
        p=plan(self.sample(tick_dword=0x80000000,established_stamp_qword=0))
        self.assertEqual(p.elapsed_signed,-2147483648);self.assertFalse(p.timer_due)
    def test_minute_multiply_wraps_before_signed_comparison(self):
        p=plan(self.sample(minutes_dword=35792,tick_dword=0,display_span_returned=None))
        self.assertEqual(p.interval_signed,-2147447296);self.assertTrue(p.timer_due)
        self.assertEqual(plan(self.sample(minutes_dword=0,tick_dword=0)).phase_dword,0)
    def test_negative_elapsed_idiv_truncates_toward_zero(self):
        p=plan(self.sample(tick_dword=0,established_stamp_qword=1001))
        self.assertEqual(p.display_seconds_signed,61)
    def test_no_inventory_or_sell_slot_call(self):
        p=plan(self.sample())
        self.assertEqual(p.steps[-1],('normal_span','00421f47','0042209d'))
        self.assertFalse(p.independently_verified)
    def test_runner_uses_source_tick_and_holds_on_display_gap(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL,reopen=False));r.start();r.phase=6
        d=r.tick(MerchantSnapshot(9999999,sell_monitor_inputs=self.sample(display_span_returned=False)))
        self.assertEqual(d.status,'needs_adapter');self.assertEqual(r.phase,6)
        d=r.tick(MerchantSnapshot(10000000,sell_monitor_inputs=self.sample(tick_dword=60000)))
        self.assertEqual(d.status,'restart_due');self.assertEqual(r.phase,0);self.assertTrue(r.restarting)
        self.assertEqual(r.last_sell_monitor_plan.elapsed_signed,60000)
    def test_disabled_source_setting_does_not_fall_back_to_legacy(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL,reopen=True));r.start();r.phase=6
        d=r.tick(MerchantSnapshot(9999999,sell_monitor_inputs=Obs(reopen_byte=0)))
        self.assertEqual(d.status,'monitoring');self.assertEqual(r.phase,6)
        r.start();self.assertIsNone(r.last_sell_monitor_plan)
    def test_raw_types_ranges_and_typed_binding(self):
        for field in ('reopen_byte','minutes_dword','tick_dword','established_stamp_qword'):
            for value in (-1,True,1.0):
                with self.assertRaises(ValueError):self.sample(**{field:value})
        with self.assertRaises(ValueError):self.sample(reopen_byte=256)
        with self.assertRaises(ValueError):self.sample(display_span_returned=1)
        with self.assertRaises(ValueError):plan(None)
        with self.assertRaises(ValueError):MerchantSnapshot(1,sell_monitor_inputs=0)

if __name__=='__main__':unittest.main()
