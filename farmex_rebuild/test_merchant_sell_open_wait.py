import unittest
from dataclasses import replace
from merchant_sell_open_wait import SellOpenWaitState as State,SellOpenWaitObservation as Obs,SellOpenWaitFrame as Frame
from operation_engine import MerchantRunner,MerchantSettings,MerchantKind,MerchantSnapshot

class SellOpenWaitTests(unittest.TestCase):
    def clear_state(self,**changes):return replace(State(pending_byte=0,status_byte_90=255),**changes)
    def complete(self):return Obs(clear_span_returns=(True,)*4,accumulated_qword=0x100000002,net_qword=97)
    def test_clear_prefix_before_ui_and_no_clock_needed(self):
        initial=self.clear_state();p=Frame(initial).step()
        self.assertFalse(p.complete);self.assertEqual(p.state,initial)
        self.assertEqual((p.prospective_state.setup_gate_byte,p.prospective_state.status_byte_90),(0,0))
        self.assertNotIn(('GetTickCount',),p.steps);self.assertEqual(p.writes,((0x58,1,0),(0x90,1,0)))
    def test_zero_setup_gate_is_not_rewritten(self):
        p=Frame(self.clear_state(setup_gate_byte=0)).step()
        self.assertEqual(p.writes,((0x90,1,0),))
    def test_data_reads_wait_until_reached_span(self):
        f=Frame(self.clear_state());p=f.step(Obs(clear_span_returns=(True,)))
        self.assertEqual(p.value_reads,());self.assertIn('span1',p.missing)
        p=f.step(Obs(clear_span_returns=(True,True)))
        self.assertIn('accumulated',p.missing);self.assertEqual(p.value_reads,())
    def test_raw_qword_high_then_low_and_display_parts(self):
        p=Frame(self.clear_state()).step(self.complete())
        self.assertTrue(p.complete);self.assertEqual(p.state.phase_dword,6)
        self.assertEqual(p.value_reads,((0x9c,4,1),(0x98,4,2),(0xa4,4,0),(0xa0,4,97)))
        self.assertEqual(p.display_plans,((3,0x100000002),(5,97)))
    def test_net_gap_does_not_repeat_completed_total_display(self):
        f=Frame(self.clear_state());p=f.step(Obs(clear_span_returns=(True,)*4,accumulated_qword=100))
        self.assertFalse(p.complete);self.assertIn('net',p.missing);self.assertEqual(p.display_plans,((3,100),))
        p=f.step(Obs(net_qword=97));self.assertTrue(p.complete);self.assertEqual(len(p.display_plans),2)
    def test_known_format_value_cannot_change_while_waiting(self):
        f=Frame(self.clear_state());f.step(Obs(clear_span_returns=(True,True),accumulated_qword=100))
        with self.assertRaises(ValueError):f.step(Obs(accumulated_qword=101))
    def test_pending_9999_waits_but_10000_reaches_stop(self):
        p=Frame(State(pending_stamp_qword=77)).step(Obs(tick_dword=10076))
        self.assertTrue(p.complete);self.assertEqual(p.status,'waiting');self.assertEqual(p.clock_plan.remaining_ms,1)
        p=Frame(State(pending_stamp_qword=77)).step(Obs(tick_dword=10077))
        self.assertFalse(p.complete);self.assertIn('stop helper',p.missing)
    def test_tick_wrap_keeps_negative_signed64_wait(self):
        p=Frame(State(pending_stamp_qword=0xfffffff0)).step(Obs(tick_dword=10))
        self.assertTrue(p.complete);self.assertEqual(p.status,'waiting');self.assertLess(p.clock_plan.elapsed_signed,0)
    def test_timeout_stop_and_message_are_independent(self):
        f=Frame(State());p=f.step(Obs(tick_dword=10000,stop_returned=True))
        self.assertFalse(p.complete);self.assertIn('message',p.missing)
        p=f.step(Obs(timeout_message_returned=True));self.assertTrue(p.complete);self.assertEqual(p.status,'timed_out')
        self.assertEqual(p.writes,());self.assertEqual(p.state.phase_dword,5)
    def test_runner_uses_bound_raw_clock_despite_monotonic_epoch(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=5;r.phase_ms=0xfffffff0
        p=Frame(State(pending_stamp_qword=r.phase_ms)).step(Obs(tick_dword=10))
        result=r.tick(MerchantSnapshot(1<<33,opening_pending=True,sell_open_wait_execution=p))
        self.assertEqual(result.status,'waiting');self.assertTrue(r.active)
    def test_runner_clear_flag_does_not_bypass_ui_gaps(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=5;r.setup_seen=True
        f=Frame(self.clear_state())
        self.assertEqual(r.tick(MerchantSnapshot(1,opening_pending=False,sell_open_wait_execution=f.step())).status,'needs_adapter')
        self.assertEqual(r.phase,5);self.assertTrue(r.setup_seen)
        r.tick(MerchantSnapshot(2,opening_pending=False,sell_open_wait_execution=f.step(self.complete())))
        self.assertEqual(r.phase,6);self.assertFalse(r.setup_seen)
    def test_bound_pending_or_clock_conflict_rejected(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=5
        p=Frame(State(pending_stamp_qword=1)).step(Obs(tick_dword=2))
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(3,opening_pending=True,sell_open_wait_execution=p))
    def test_later_callback_needs_a_new_frame(self):
        f=Frame(State());first=f.step(Obs(tick_dword=1))
        self.assertEqual(f.step(Obs(tick_dword=10000)),first)
        self.assertEqual(Frame(State()).step(Obs(tick_dword=10000)).status,'needs_observation')
    def test_typed_context_and_reached_phase(self):
        with self.assertRaises(ValueError):Obs(accumulated_qword=True)
        with self.assertRaises(ValueError):Frame(State(phase_dword=4))

if __name__=='__main__':unittest.main()
