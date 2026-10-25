import unittest
from dataclasses import replace
from action_queue import QueueState,QueueSample
from merchant_sell_tail import SellSlotState
from merchant_sell_session import SellSessionState as State,SellSessionObservation as Obs,SellSessionFrame as Frame
from merchant_sell_setup import SellSetupObservation
from operation_engine import MerchantRunner,MerchantSettings,MerchantKind,MerchantSnapshot

class SellSessionTests(unittest.TestCase):
    def dirty(self):
        return State(ready_byte=255,list_index_dword=7,inventory_slot_dword=30,
            slot=SellSlotState((1,)*28,1,99,123,124,11))
    def ready(self):return Obs(100,QueueSample(101,1),True)
    def test_resets_source_fields_but_preserves_item_pending_and_stamp(self):
        p=Frame(self.dirty(),QueueState()).step(self.ready())
        self.assertTrue(p.complete);self.assertEqual(p.state.phase_dword,3)
        self.assertEqual(p.state.slot.used_bytes,(0,)*28)
        self.assertEqual((p.state.slot.accumulated_qword,p.state.slot.net_qword,p.state.slot.prepared_slots_dword),(0,0,0))
        self.assertEqual((p.state.slot.item_pending_byte,p.state.slot.item_stamp_qword),(1,99))
        self.assertEqual((p.state.list_index_dword,p.state.inventory_slot_dword,p.state.ready_byte),(0,14,0))
    def test_reset_prefix_waits_for_explicit_clock(self):
        initial=self.dirty();p=Frame(initial,QueueState()).step()
        self.assertFalse(p.complete);self.assertEqual(p.state,initial)
        self.assertEqual(p.prospective_state.slot.used_bytes,(0,)*28)
        self.assertEqual(p.calls,(('GetTickCount',),))
    def test_seed_and_independent_enqueue_clock(self):
        p=Frame(State(),QueueState()).step(self.ready())
        self.assertEqual(p.queue.records[0].payload,b'\x68\x01')
        self.assertEqual(p.state.session_stamp_qword,100);self.assertEqual(p.queue.records[0].created_tick,101)
        self.assertEqual(p.queue.records[0].delay_dword,0)
    def test_ready_not_inferred_from_successful_local_enqueue(self):
        p=Frame(State(ready_byte=1),QueueState()).step(self.ready())
        self.assertEqual(p.state.ready_byte,0);self.assertFalse(p.independently_verified)
    def test_local_queue_cache_does_not_duplicate_on_missing_return(self):
        f=Frame(State(),QueueState());p=f.step(Obs(100,QueueSample(101,1),False))
        self.assertFalse(p.complete);self.assertEqual(len(p.prospective_queue.records),1);self.assertEqual(p.state.phase_dword,2)
        p=f.step(Obs(enqueue_returned=True))
        self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1)
        self.assertEqual(f.step().queue,p.queue);self.assertEqual(p.calls.count(('GetTickCount',)),1)
    def test_unknown_gate_and_tick_remain_gaps(self):
        for sample in (QueueSample(),QueueSample(connection_gate=1)):
            p=Frame(State(),QueueState()).step(Obs(100,sample,True))
            self.assertFalse(p.complete);self.assertEqual(p.prospective_state.phase_dword,2)
    def test_gate_zero_no_tick_still_has_normal_caller_phase_increment(self):
        p=Frame(State(),QueueState()).step(Obs(0,QueueSample(connection_gate=0),True))
        self.assertTrue(p.complete);self.assertEqual(p.queue.records,());self.assertEqual(p.state.session_stamp_qword,0)
    def test_changed_clock_and_unreached_entry_rejected(self):
        f=Frame(State(),QueueState());f.step(Obs(100))
        with self.assertRaises(ValueError):f.step(Obs(101))
        with self.assertRaises(ValueError):Frame(State(setup_gate_byte=0),QueueState())
        with self.assertRaises(ValueError):Frame(State(phase_dword=3),QueueState())
    def test_runner_gate_arms_before_handoff_and_missing_handoff_waits(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=2
        setup=SellSetupObservation(preparation_returned=True,cost_qword=1,matched_count_dword=1,coins_dword=1)
        f=Frame(State(),QueueState())
        snapshot=MerchantSnapshot(61000,sell_setup_inputs=setup,sell_session_execution=f.step())
        self.assertEqual(r.tick(snapshot).status,'setup_gate_armed')
        self.assertEqual(r.tick(replace(snapshot,now_ms=61001)).status,'needs_adapter');self.assertEqual(r.phase,2)
        p=r.tick(replace(snapshot,now_ms=61002,sell_session_execution=f.step(self.ready())))
        self.assertEqual(p.status,'prepare_attempt');self.assertEqual((r.phase,r.entry_index,r.inventory_slot),(3,0,14))
    def test_snapshot_type_is_explicit(self):
        with self.assertRaises(ValueError):MerchantSnapshot(1,sell_session_execution=True)

if __name__=='__main__':unittest.main()
