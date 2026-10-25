import unittest
from dataclasses import replace
from merchant_sell_prepare_wait import SellPrepareWaitObservation as Obs,plan_sell_prepare_wait as plan,parse_sell_prepare_wait
from operation_engine import MerchantRunner,MerchantKind,MerchantSettings,MerchantSnapshot

class SellPrepareWaitTests(unittest.TestCase):
    def test_session_gate_precedes_item_and_count(self):
        p=plan(Obs(ready_byte=0,session_stamp_qword=100,tick_dword=10099))
        self.assertTrue(p.complete);self.assertEqual(p.branch,'session');self.assertEqual(p.status,'waiting')
        self.assertNotIn(('read','+28'),p.steps);self.assertEqual(p.clock_plan.remaining_ms,1)
    def test_clear_item_reaches_selection_without_clock(self):
        p=plan(Obs(ready_byte=255,item_pending_byte=0))
        self.assertEqual(p.status,'selection_path');self.assertTrue(p.complete)
        self.assertIsNone(p.clock_plan)
    def test_only_selected_stamp_is_required(self):
        o=Obs(ready_byte=1,item_pending_byte=1,item_stamp_qword=200,tick_dword=201)
        self.assertEqual(plan(o).status,'waiting');self.assertEqual(plan(o).branch,'item')
        self.assertFalse(plan(replace(o,item_stamp_qword=None,session_stamp_qword=200)).complete)
    def test_each_reached_missing_field_holds(self):
        for o in (Obs(),Obs(ready_byte=1),Obs(ready_byte=0),
                  Obs(ready_byte=0,tick_dword=10000),Obs(ready_byte=1,item_pending_byte=1,tick_dword=10000)):
            self.assertFalse(plan(o).complete)
    def test_timeout_message_before_stop_in_both_branches(self):
        for ready,branch,span in ((0,'session',('00421ae2','00421b4e')),(1,'item',('0042197b','004219e7'))):
            o=Obs(ready,1,0,0,10000)
            p=plan(o);self.assertFalse(p.complete);self.assertEqual(p.steps[-1],('normal_span',*span))
            self.assertFalse(any(s[0]=='0040ae0c' for s in p.steps))
            p=plan(replace(o,message_span_returned=True))
            self.assertFalse(p.complete);self.assertEqual(p.steps[-1][0],'0040ae0c')
            p=plan(replace(o,message_span_returned=True,stop_returned=True))
            self.assertTrue(p.complete);self.assertEqual((p.status,p.branch),('timed_out',branch))
            self.assertFalse(p.independently_verified)
    def test_stop_receipt_cannot_skip_message(self):
        self.assertNotIn('0040ae0c',[s[0] for s in plan(Obs(0,None,0,None,10000,False,True)).steps])
    def test_raw_tick_wrap_waits_as_negative_signed64(self):
        p=plan(Obs(1,1,None,0xfffffff0,10))
        self.assertEqual(p.status,'waiting');self.assertEqual(p.clock_plan.elapsed_signed,-4294967270)
    def test_high_stamp_and_signed64_boundary(self):
        self.assertEqual(plan(Obs(0,None,1<<32,None,10000)).status,'waiting')
        p=plan(Obs(0,None,(1<<64)-1,None,10000,True,True))
        self.assertEqual(p.clock_plan.elapsed_signed,10001);self.assertEqual(p.status,'timed_out')
    def runner(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=3;r.phase_ms=100;r.item_ms=200
        return r
    def test_runner_wait_does_not_require_later_prepared_count(self):
        r=self.runner();o=Obs(0,None,100,None,101)
        p=r.tick(MerchantSnapshot(10000000,sale_session_ready=False,sell_prepare_wait_inputs=o))
        self.assertEqual(p.status,'waiting');self.assertEqual(p.remaining_ms,9999);self.assertTrue(r.active)
    def test_runner_requires_both_timeout_returns(self):
        r=self.runner();o=Obs(1,1,None,200,10200)
        for i in range(2):
            p=r.tick(MerchantSnapshot(10000000+i,sale_session_ready=True,item_pending=True,sell_prepare_wait_inputs=o))
            self.assertEqual(p.status,'needs_adapter');self.assertTrue(r.active)
            o=replace(o,message_span_returned=True)
        p=r.tick(MerchantSnapshot(10000002,sale_session_ready=True,item_pending=True,
            sell_prepare_wait_inputs=replace(o,stop_returned=True)))
        self.assertEqual(p.reason,'sale_item_timeout');self.assertFalse(r.active)
    def test_runner_rejects_flag_and_stamp_conflicts(self):
        for o in (Obs(1,0),Obs(0,None,99,None,100),Obs(1,1,None,199,200)):
            r=self.runner()
            with self.assertRaises(ValueError):r.tick(MerchantSnapshot(1000,sale_session_ready=False,sell_prepare_wait_inputs=o))
        r=self.runner()
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(1000,sale_session_ready=True,item_pending=False,
            sell_prepare_wait_inputs=Obs(1,1,None,200,201)))
        r=self.runner()
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(1000,sale_session_ready=True,item_pending=True,
            sell_prepare_wait_inputs=Obs(1,1,None,199,200)))
    def test_runner_session_timeout_and_selection_continuation(self):
        r=self.runner()
        p=r.tick(MerchantSnapshot(10100,sale_session_ready=False,
            sell_prepare_wait_inputs=Obs(0,None,100,None,10100,True,True)))
        self.assertEqual(p.reason,'sale_session_timeout');self.assertFalse(r.active)
        r=self.runner()
        p=r.tick(MerchantSnapshot(10000000,sale_session_ready=True,item_pending=False,
            sell_prepare_wait_inputs=Obs(1,0)))
        self.assertEqual(p.status,'needs_adapter');self.assertEqual(r.phase,3)
        self.assertEqual(r.last_sell_prepare_wait_plan.status,'selection_path')
    def test_types(self):
        for field in ('ready_byte','item_pending_byte','session_stamp_qword','item_stamp_qword','tick_dword'):
            with self.assertRaises(ValueError):Obs(**{field:True})
            with self.assertRaises(ValueError):Obs(**{field:-1})
        with self.assertRaises(ValueError):Obs(message_span_returned=1)
        with self.assertRaises(ValueError):MerchantSnapshot(1,sell_prepare_wait_inputs=0)
    def test_json_only_reads_reached_branch_fields(self):
        p=parse_sell_prepare_wait('{"ready_byte":1,"item_pending_byte":0,"tick_dword":"unreached","stop_returned":1}')
        self.assertEqual(plan(p).status,'selection_path');self.assertIsNone(p.tick_dword)
        p=parse_sell_prepare_wait('{"ready_byte":0,"session_stamp_qword":"unreached"}')
        self.assertIsNone(p.session_stamp_qword);self.assertFalse(plan(p).complete)
    def test_json_timeout_receipts_are_independent_and_lazy(self):
        p=parse_sell_prepare_wait('{"ready_byte":0,"tick_dword":10000,"session_stamp_qword":0,"stop_returned":"unreached"}')
        self.assertIsNone(p.stop_returned);self.assertFalse(plan(p).complete)
        with self.assertRaises(ValueError):parse_sell_prepare_wait('{"ready_byte":0,"tick_dword":10000,"session_stamp_qword":0,"message_span_returned":true,"stop_returned":1}')
    def test_json_rejects_unknown_fields_and_invalid_root(self):
        for text in ('[]','{"tick":1}','{"ready_byte":true}'):
            with self.assertRaises(ValueError):parse_sell_prepare_wait(text)

if __name__=='__main__':unittest.main()
