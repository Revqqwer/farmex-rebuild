import unittest
from dataclasses import replace
from merchant_monitor import BuyMonitorObservation as Obs,plan_buy_monitor as plan
from merchant_setup import MerchantInventoryObservation as Inventory
from operation_engine import MerchantRunner,MerchantKind,MerchantSettings,MerchantSnapshot

class BuyMonitorTests(unittest.TestCase):
    def observation(self,**changes):
        return replace(Obs(1,1,0,59999,0,1,None,True),**changes)
    def test_disabled_timer_needs_no_clock_or_display(self):
        p=plan(Obs(reopen_byte=0,free_count_dword=1,threshold_dword=0))
        self.assertTrue(p.complete);self.assertEqual(p.phase_dword,5);self.assertIsNone(p.timer_due)
        self.assertEqual(p.steps,(('read','+110'),('0042070c',)))
    def test_timer_exact_boundary_still_calls_inventory(self):
        p=plan(self.observation(tick_dword=60000,display_span_returned=None))
        self.assertTrue(p.complete);self.assertEqual(p.phase_dword,0)
        self.assertEqual(p.steps[-1],('0042070c',));self.assertEqual(p.writes,((4,0,'timer'),))
    def test_due_prefix_is_exposed_but_not_committed_on_gap(self):
        p=plan(self.observation(tick_dword=60000,free_count_dword=None))
        self.assertFalse(p.complete);self.assertEqual(p.phase_dword,5);self.assertEqual(p.prospective_phase_dword,0)
        self.assertEqual(p.writes,((4,0,'timer'),))
    def test_display_gap_precedes_inventory_even_when_inventory_known(self):
        p=plan(self.observation(display_span_returned=False))
        self.assertFalse(p.complete);self.assertNotIn(('0042070c',),p.steps)
    def test_countdown_is_difference_of_two_truncated_quotients(self):
        p=plan(self.observation(tick_dword=999))
        self.assertEqual(p.display_seconds_signed,60) # (60000-999)//1000 would be59.
    def test_negative_elapsed_uses_idiv_toward_zero(self):
        p=plan(self.observation(tick_dword=1,established_stamp_qword=1000))
        self.assertEqual(p.elapsed_signed,-999);self.assertEqual(p.display_seconds_signed,60)
    def test_elapsed_wrap_is_signed32_and_stamp_high_is_ignored(self):
        p=plan(self.observation(tick_dword=10,established_stamp_qword=0x1234fffffff0))
        self.assertEqual(p.elapsed_signed,26);self.assertFalse(p.timer_due)
    def test_minutes_multiply_wraps_signed32(self):
        p=plan(self.observation(minutes_dword=35792,tick_dword=0))
        self.assertLess(p.interval_signed,0);self.assertTrue(p.timer_due)
    def test_both_conditions_write_phase_zero_in_order(self):
        p=plan(self.observation(tick_dword=60000,free_count_dword=0))
        self.assertEqual(p.writes,((4,0,'timer'),(4,0,'free_threshold')))
    def test_signed_threshold_negative_does_not_reset_for_positive_count(self):
        p=plan(self.observation(threshold_dword=0xffffffff))
        self.assertFalse(p.free_due);self.assertEqual(p.phase_dword,5)
    def test_bound_inventory_counts_all_28_fresh_results(self):
        p=plan(self.observation(free_count_dword=None,inventory_inputs=Inventory((0,)*28),threshold_dword=28))
        self.assertTrue(p.complete);self.assertTrue(p.free_due);self.assertEqual(len(p.inventory_plan.calls),28)
        p=plan(self.observation(free_count_dword=None,inventory_inputs=Inventory((1,))))
        self.assertFalse(p.complete);self.assertIn('slot15',p.missing)
    def test_typed_input_conflicts_rejected(self):
        with self.assertRaises(ValueError):Obs(reopen_byte=True)
        with self.assertRaises(ValueError):self.observation(inventory_inputs=Inventory())
        with self.assertRaises(ValueError):MerchantSnapshot(1,buy_monitor_inputs=0)
    def test_runner_does_not_skip_missing_inventory_after_timer_due(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.BUY));r.start();r.phase=5
        o=self.observation(tick_dword=60000,free_count_dword=None)
        p=r.tick(MerchantSnapshot(1,buy_monitor_inputs=o))
        self.assertEqual(p.status,'needs_adapter');self.assertEqual(r.phase,5)
        self.assertEqual(r.last_buy_monitor_plan.prospective_phase_dword,0)
        p=r.tick(MerchantSnapshot(2,buy_monitor_inputs=replace(o,free_count_dword=1)))
        self.assertEqual(p.reason,'reopen_timer');self.assertEqual(r.phase,0);self.assertTrue(r.restarting)
    def test_runner_bound_monitor_rejects_legacy_count(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.BUY));r.start();r.phase=5
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(1,buy_monitor_inputs=self.observation(),buy_free_slots=1))

if __name__=='__main__':unittest.main()
