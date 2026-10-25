import unittest
from dataclasses import replace
from merchant_reply import (MerchantReplyState as State,MerchantReplyObservation as ReplyObs,
    plan_merchant_reply,merchant_snapshot_from_reply,sell_setup_delay_from_reply)
from merchant_sell_setup_delay import SellSetupDelayObservation,plan_sell_setup_delay
from operation_engine import MerchantRunner,MerchantSettings,MerchantKind

class SellSetupReplyTests(unittest.TestCase):
    def close(self,state=State(close_pending_byte=1),actor=7,tick=123):
        return plan_merchant_reply(state,b'\x68\x02'+(7).to_bytes(4,'little'),ReplyObs(0,actor,tick))
    def test_matching_close_produces_delay_stamp(self):
        p=self.close();o=sell_setup_delay_from_reply(p.state,0,61123,ready_span_returns=(True,True))
        self.assertEqual(o.started_stamp_qword,123);self.assertEqual(p.state.close_pending_byte,0)
        self.assertTrue(plan_sell_setup_delay(o).delay_due)
    def test_wrong_actor_and_scan_priority_do_not_reset_stamp(self):
        state=State(close_pending_byte=1,setup_stamp_qword=99)
        self.assertEqual(self.close(state,actor=8).state,state)
        p=plan_merchant_reply(state,b'\x68\x02'+(7).to_bytes(4,'little'),ReplyObs(1,7,123))
        self.assertEqual(p.state.setup_stamp_qword,99)
        self.assertEqual(sell_setup_delay_from_reply(p.state,0).started_stamp_qword,99)
    def test_clock_gap_cannot_make_an_accepted_close_state(self):
        p=self.close(tick=None)
        self.assertFalse(p.complete);self.assertEqual(p.state.setup_stamp_qword,0)
        self.assertEqual(p.state.close_pending_byte,1)
    def test_projection_never_supplies_fresh_tick_or_ui_returns(self):
        o=sell_setup_delay_from_reply(State(setup_stamp_qword=123),0)
        self.assertIsNone(o.tick_dword);self.assertEqual(o.ready_span_returns,())
        self.assertFalse(plan_sell_setup_delay(o).complete)
    def test_source_rollover_not_rejected_by_outer_future_guard(self):
        state=self.close(tick=0xfffffff0).state
        o=sell_setup_delay_from_reply(state,0,10,waiting_span_returned=True)
        s=merchant_snapshot_from_reply(state,10,sell_setup_delay_inputs=o)
        self.assertIsNone(s.setup_started_ms)
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=2
        self.assertEqual(r.tick(s).status,'waiting')
        self.assertEqual(r.last_sell_setup_delay_plan.elapsed_signed,-4294967270)
        with self.assertRaises(ValueError):merchant_snapshot_from_reply(state,10)
    def test_binding_rejects_conflicting_raw_stamp_and_legacy_override(self):
        state=State(setup_stamp_qword=123)
        with self.assertRaises(ValueError):merchant_snapshot_from_reply(state,200,
            sell_setup_delay_inputs=SellSetupDelayObservation(0,124,1))
        with self.assertRaises(ValueError):merchant_snapshot_from_reply(state,200,
            setup_started_ms=None,sell_setup_delay_inputs=sell_setup_delay_from_reply(state,0))
    def test_explicit_unknown_stamp_remains_missing(self):
        o=SellSetupDelayObservation(extra_wait_dword=0,tick_dword=100000)
        s=merchant_snapshot_from_reply(State(setup_stamp_qword=999),1,sell_setup_delay_inputs=o)
        self.assertIsNone(s.sell_setup_delay_inputs.started_stamp_qword)
        self.assertFalse(plan_sell_setup_delay(s.sell_setup_delay_inputs).complete)
    def test_types(self):
        with self.assertRaises(ValueError):sell_setup_delay_from_reply(None,0)
        with self.assertRaises(ValueError):sell_setup_delay_from_reply(State(),True)
        with self.assertRaises(ValueError):merchant_snapshot_from_reply(State(),1,sell_setup_delay_inputs=0)

if __name__=='__main__':unittest.main()
