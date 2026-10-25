import unittest
from dataclasses import replace
from merchant_sell_close import SellCloseState as State,SellCloseObservation as Obs,SellCloseFrame,plan_sell_close_probe
from action_queue import QueueState,QueueSample
from operation_engine import MerchantRunner,MerchantSettings,MerchantKind,MerchantSnapshot
from merchant_reply import (MerchantReplyState,MerchantReplyObservation,plan_merchant_reply,
    merchant_snapshot_from_reply,sell_setup_delay_from_reply)

def own_close_samples(first=1,second=0):
    return Obs(global_samples=((0x553e7c,0x1000),(0x554148,0x20),(0x553e7c,0x2000),(0x55414c,0x30)),
        protected_samples=((0x1000,0x3000),(0x2000,0x4000)),byte_samples=((0x3020,first),(0x4030,second)))

class SellCloseTests(unittest.TestCase):
    def test_second_root_is_fresh_and_only_al_equals_one(self):
        p=plan_sell_close_probe(own_close_samples(0x101,0x201))
        self.assertTrue(p.complete);self.assertTrue(p.is_open);self.assertTrue(p.buy_mode)
        self.assertEqual([r[1] for r in p.reads if r[0]=='protected'],[0x1000,0x2000])
        for value in (0,2,255,0x100):
            p=plan_sell_close_probe(own_close_samples(value,1))
            self.assertTrue(p.complete);self.assertFalse(p.is_open)
            self.assertEqual(len(p.reads),4);self.assertIsNone(p.buy_mode)
    def test_unknown_and_wrong_address_are_not_closed(self):
        p=plan_sell_close_probe(Obs());self.assertFalse(p.complete);self.assertIsNone(p.is_open)
        with self.assertRaises(ValueError):plan_sell_close_probe(replace(own_close_samples(),protected_samples=((0x1001,0x3000),)))
    def test_wrapped_probe_address(self):
        o=Obs(((0x553e7c,1),(0x554148,0x20)),((1,0xfffffff0),),((0x10,0),))
        self.assertTrue(plan_sell_close_probe(o).complete)
    def test_not_open_preserves_pending_stamp_and_queue(self):
        q=QueueState();f=SellCloseFrame(State(pending_byte=255,close_stamp_qword=123),q)
        d=f.step(own_close_samples(2));self.assertTrue(d.complete)
        self.assertEqual(d.status,'no_close_required');self.assertEqual(d.state,State(1,255,123))
        self.assertEqual(d.writes,((4,4,1),));self.assertEqual(d.queue,q);self.assertEqual(d.payload,b'')
    def test_pending_before_clock_and_queue_return_after_copy(self):
        f=SellCloseFrame(State(),QueueState());d=f.step(own_close_samples())
        self.assertFalse(d.complete);self.assertEqual(d.state.phase_dword,0)
        self.assertEqual(d.prospective_state.pending_byte,1);self.assertEqual(d.writes,((0x18,1,1),))
        d=f.step(Obs(close_tick_dword=0xffffffff))
        self.assertEqual(d.prospective_state.close_stamp_qword,0xffffffff)
        d=f.step(Obs(queue_sample=QueueSample(10,1)))
        self.assertFalse(d.complete);self.assertEqual(len(d.queue.records),0)
        self.assertEqual(len(d.prospective_queue.records),1)
        self.assertEqual(f.step().prospective_queue,d.prospective_queue)
        d=f.step(Obs(enqueue_returned=True));self.assertTrue(d.complete)
        self.assertEqual((d.queue.records[0].payload,d.queue.records[0].delay_dword),(b'\x68\x02',0))
        self.assertEqual(d.writes,((0x18,1,1),(0x20,8,0xffffffff),(4,4,1)))
        self.assertEqual(f.step(),d)
    def test_buy_close_subtype_and_connection_gate_zero(self):
        f=SellCloseFrame(State(),QueueState())
        d=f.step(replace(own_close_samples(1,1),close_tick_dword=50,queue_sample=QueueSample(connection_gate=0)))
        self.assertEqual(d.payload,b'\x68\x27');self.assertFalse(d.complete)
        d=f.step(Obs(enqueue_returned=True));self.assertTrue(d.complete)
        self.assertEqual(d.queue.records,());self.assertEqual(d.state.phase_dword,1)
    def test_partial_probe_can_fill_unknown_but_not_change_known(self):
        o=own_close_samples();f=SellCloseFrame(State(),QueueState())
        f.step(replace(o,byte_samples=((0x3020,None),)))
        self.assertTrue(f.step(Obs(byte_samples=o.byte_samples)).probe.complete)
        with self.assertRaises(ValueError):f.step(Obs(byte_samples=((0x3020,0),)))
        f.step(Obs(close_tick_dword=10))
        with self.assertRaises(ValueError):f.step(Obs(close_tick_dword=11))
    def test_runner_holds_and_validates_probe(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start()
        f=SellCloseFrame(State(),QueueState());partial=f.step(own_close_samples())
        self.assertEqual(r.tick(MerchantSnapshot(1000000,sell_close_execution=partial)).status,'needs_adapter')
        self.assertEqual(r.phase,0)
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(1000001,currently_open=False,sell_close_execution=partial))
        d=f.step(Obs(close_tick_dword=10,queue_sample=QueueSample(11,1),enqueue_returned=True))
        self.assertEqual(r.tick(MerchantSnapshot(1000002,sell_close_execution=d)).status,'close_attempt')
        self.assertEqual((r.phase,r.phase_ms),(1,10))
    def test_own_close_reply_delay_chain(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start()
        f=SellCloseFrame(State(),QueueState())
        d=f.step(replace(own_close_samples(),close_tick_dword=10,queue_sample=QueueSample(11,1),enqueue_returned=True))
        r.tick(MerchantSnapshot(20,sell_close_execution=d))
        reply=MerchantReplyState(close_pending_byte=d.state.pending_byte)
        p=plan_merchant_reply(reply,b'\x68\x02\x01\0\0\0',MerchantReplyObservation(0,1,30))
        r.tick(merchant_snapshot_from_reply(p.state,31));self.assertEqual(r.phase,2)
        delay=sell_setup_delay_from_reply(p.state,0,61030,ready_span_returns=(True,True))
        result=r.tick(merchant_snapshot_from_reply(p.state,61030,setup_result=0,sell_setup_delay_inputs=delay))
        self.assertEqual(result.status,'setup_gate_armed');self.assertEqual(len(d.queue.records),1)
        self.assertFalse(d.independently_verified)
    def test_types(self):
        with self.assertRaises(ValueError):Obs(close_tick_dword=True)
        with self.assertRaises(ValueError):Obs(byte_samples=((1,True),))
        with self.assertRaises(ValueError):SellCloseFrame(State(1),QueueState())
        with self.assertRaises(ValueError):MerchantSnapshot(1,sell_close_execution=0)

if __name__=='__main__':unittest.main()
