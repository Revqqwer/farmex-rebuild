import unittest
from dataclasses import replace
from merchant_reply import MerchantReplyState as State,MerchantReplyObservation as Obs,plan_merchant_reply,merchant_snapshot_from_reply
from operation_engine import MerchantKind,MerchantSettings,MerchantRunner

class MerchantReplyTests(unittest.TestCase):
    def test_nonmerchant_and_unknown_scan_gate(self):
        initial=State(opening_pending_byte=255)
        p=plan_merchant_reply(initial,b'\x67',Obs())
        self.assertEqual(p.status,'not_applicable');self.assertIsNone(p.return_al)
        p=plan_merchant_reply(initial,b'\x68\x03',Obs())
        self.assertFalse(p.complete);self.assertEqual(p.state,initial)
    def test_close_id_at2_clock_before_pending_clear(self):
        initial=State(close_pending_byte=1)
        packet=b'\x68\x02'+(0x12345678).to_bytes(4,'little')
        p=plan_merchant_reply(initial,packet,Obs(0,0x12345678))
        self.assertFalse(p.complete);self.assertEqual(p.prospective_state.close_pending_byte,1)
        p=plan_merchant_reply(initial,packet,Obs(0,0x12345678,0xffffffff))
        self.assertEqual(p.state.setup_stamp_qword,0xffffffff);self.assertEqual(p.state.close_pending_byte,0)
        self.assertEqual(p.return_al,1);self.assertEqual([w[1] for w in p.writes],[8,0x18])
    def test_open7_id_at6_not2_and_pending_clear_before_clock(self):
        initial=State(opening_pending_byte=1,established_stamp_qword=99)
        packet=b'\x68\x07'+(77).to_bytes(4,'little')+(5).to_bytes(4,'little')
        p=plan_merchant_reply(initial,packet,Obs(0,5))
        self.assertFalse(p.complete);self.assertEqual(p.state,initial)
        self.assertEqual(p.prospective_state.opening_pending_byte,0)
        self.assertEqual(p.prospective_state.established_stamp_qword,99)
        p=plan_merchant_reply(initial,packet,Obs(0,5,100))
        self.assertEqual([w[1] for w in p.writes],[0x48,0x10]);self.assertEqual(p.state.established_stamp_qword,100)
    def test_open28_id_at2_and_mismatch_does_not_read_clock(self):
        initial=State(opening_pending_byte=1)
        packet=b'\x68\x28'+(5).to_bytes(4,'little')
        p=plan_merchant_reply(initial,packet,Obs(0,6))
        self.assertTrue(p.complete);self.assertEqual(p.state,initial);self.assertNotIn(('GetTickCount',),p.calls)
        p=plan_merchant_reply(initial,packet,Obs(0,5,10));self.assertEqual(p.state.opening_pending_byte,0)
    def test_session_and_item_flags_need_no_actor(self):
        initial=State(item_pending_byte=255)
        p=plan_merchant_reply(initial,b'\x68\x01\x01',Obs(0))
        self.assertEqual(p.state.session_ready_byte,1)
        p=plan_merchant_reply(initial,b'\x68\x01\x00',Obs(0));self.assertEqual(p.state.session_ready_byte,0)
        p=plan_merchant_reply(initial,b'\x68\x03',Obs(0));self.assertEqual(p.state.item_pending_byte,0)
    def test_scanner_consumes_before_merchant_identity_and_flags(self):
        initial=State(close_pending_byte=1,scan_pending_byte=1)
        for subtype in (0x27,2,0x11):
            p=plan_merchant_reply(initial,bytes((0x68,subtype)),Obs(1))
            self.assertTrue(p.complete);self.assertEqual(p.return_al,0)
            self.assertEqual(p.state.scan_pending_byte,0);self.assertEqual(p.state.close_pending_byte,1)
            self.assertEqual(p.calls,())
    def test_scanner_parse_finish_are_separate_normal_return_gates(self):
        initial=State(scan_pending_byte=1)
        p=plan_merchant_reply(initial,b'\x68\x23\x01',Obs(1))
        self.assertFalse(p.complete);self.assertEqual(p.calls,(('004bc650','scan_object','payload','payload_length'),))
        p=plan_merchant_reply(initial,b'\x68\x23\x01',Obs(1,scan_parse_returned=True))
        self.assertFalse(p.complete);self.assertEqual(p.calls[-1],('004bf57c',2))
        p=plan_merchant_reply(initial,b'\x68\x05\x00',Obs(1,scan_finish_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.calls,(('004bf57c',1),));self.assertEqual(p.return_al,0)
    def test_truncation_is_not_zero_actor_or_response(self):
        initial=State(opening_pending_byte=1)
        for packet in (b'',b'\x68',b'\x68\x01',b'\x68\x28\x01',b'\x68\x07'+b'\0'*7):
            p=plan_merchant_reply(initial,packet,Obs(0,1,5))
            self.assertEqual(p.status,'truncated');self.assertEqual(p.state,initial)
    def test_session_negative_status_preserves_previous_ready(self):
        initial=State(session_ready_byte=255)
        for status in (0,2,255):
            p=plan_merchant_reply(initial,bytes((0x68,1,status)),Obs(0))
            self.assertEqual(p.state,initial);self.assertEqual(p.writes,())
    def test_active_scanner_unhandled_subtype_reaches_merchant_branch(self):
        initial=State(opening_pending_byte=255,scan_pending_byte=255)
        p=plan_merchant_reply(initial,b'\x68\x28'+(0xffffffff).to_bytes(4,'little'),Obs(255,0xffffffff,10))
        self.assertEqual(p.return_al,1);self.assertEqual(p.state.opening_pending_byte,0)
        self.assertEqual(p.state.scan_pending_byte,255)
    def test_reply_binding_clears_wait_but_never_confirms_trade(self):
        runner=MerchantRunner(MerchantSettings(kind=MerchantKind.BUY));runner.start();runner.phase=4;runner.phase_ms=1
        state=State(opening_pending_byte=1)
        p=runner.tick(merchant_snapshot_from_reply(state,100));self.assertEqual(p.status,'waiting')
        reply=plan_merchant_reply(state,b'\x68\x28'+(1).to_bytes(4,'little'),Obs(0,1,101))
        self.assertFalse(reply.independently_verified)
        p=runner.tick(merchant_snapshot_from_reply(reply.state,102));self.assertEqual(runner.phase,5)
        self.assertEqual(p.intents,())
    def test_bind_rejects_conflicts_and_unsupported_future_clock(self):
        with self.assertRaises(ValueError):merchant_snapshot_from_reply(State(),1,opening_pending=False)
        with self.assertRaises(ValueError):merchant_snapshot_from_reply(State(established_stamp_qword=10),1)
        with self.assertRaises(ValueError):Obs(scan_active_byte=True)

if __name__=='__main__':unittest.main()
