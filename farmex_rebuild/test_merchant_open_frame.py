import unittest
from dataclasses import replace
from merchant_open_frame import BuyOpenCallerState as State,BuyOpenFrame
from merchant_open import BuyOpenObservation as Obs
from merchant_preparation import BuyPreparedRecord as Row
from merchant_setup import MerchantInventoryObservation as Inventory
from action_queue import QueueState,QueueSample

class BuyOpenFrameTests(unittest.TestCase):
    def obs(self,**changes):
        fields=dict(initial_global_base=0x1000,free_count=1,coins_dword=6,records=(Row(1,2,3),),
            stable_records=True,fresh_global_bases={0:0x2000},zero_helper_returns={0:True},memset_returns={0:True})
        fields.update(changes);return Obs(**fields)
    def samples(self):return {0:QueueSample(10,1),1:QueueSample(11,1)}
    def test_pending_precedes_unknown_clock_and_stamp_is_zero_extended(self):
        initial=State(pending_byte=254,pending_stamp_qword=0x1122334455667788)
        frame=BuyOpenFrame(initial)
        p=frame.step();self.assertFalse(p.complete);self.assertEqual(p.state,initial)
        self.assertEqual(p.prospective_state.pending_byte,1)
        self.assertEqual(p.prospective_state.pending_stamp_qword,initial.pending_stamp_qword)
        self.assertEqual(p.calls,(('write_byte',0x48,1),('GetTickCount',)))
        p=frame.step(entry_tick=0xffffffff)
        self.assertEqual(p.prospective_state.pending_stamp_qword,0xffffffff)
        self.assertEqual(p.calls.count(('GetTickCount',)),1)
    def test_entry_tick_is_retained_across_later_helper_gap(self):
        frame=BuyOpenFrame(State());p=frame.step(entry_tick=5,observation=self.obs(zero_helper_returns={}))
        self.assertFalse(p.complete);self.assertEqual(p.prospective_state.accumulated_qword,6)
        p=frame.step(entry_tick=999,observation=self.obs(),samples=self.samples(),helper_returned=True)
        self.assertTrue(p.complete);self.assertEqual(p.state.pending_stamp_qword,5)
        self.assertEqual(p.state.phase_dword,4);self.assertEqual(p.state.pending_byte,1)
        self.assertEqual(p.calls[-1],('increment_dword',4,4))
    def test_queue_prefix_cached_and_only_missing_second_sample_needed(self):
        frame=BuyOpenFrame(State());p=frame.step(entry_tick=1,observation=self.obs(),samples={0:QueueSample(10,1)})
        self.assertEqual(len(p.queue.records),0);self.assertEqual(len(p.prospective_queue.records),1)
        p=frame.step(samples={0:QueueSample(999,0),1:QueueSample(11,1)},helper_returned=True)
        self.assertTrue(p.complete)
        self.assertEqual([(r.created_tick,r.record_id) for r in p.queue.records],[(10,1),(11,2)])
    def test_helper_return_is_separate_and_completed_buffers_are_frozen(self):
        frame=BuyOpenFrame(State());p=frame.step(entry_tick=7,observation=self.obs(),samples=self.samples())
        self.assertEqual(p.status,'needs_helper_return');self.assertEqual(p.state.phase_dword,3)
        self.assertEqual(len(p.prospective_queue.records),2)
        p=frame.step(observation=self.obs(coins_dword=0,records=()),helper_returned=True)
        self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),2)
        again=frame.step(helper_returned=True);self.assertEqual(again.status,'already_complete')
        self.assertEqual(again.queue,p.queue)
    def test_partial_known_scalar_cannot_change(self):
        frame=BuyOpenFrame(State());frame.step(entry_tick=1,observation=self.obs(zero_helper_returns={}))
        with self.assertRaises(ValueError):frame.step(observation=self.obs(coins_dword=7))
        with self.assertRaises(ValueError):frame.step(observation=self.obs(initial_global_base=0x1004))
    def test_partial_inventory_can_fill_gaps_but_not_change_known_results(self):
        frame=BuyOpenFrame(State())
        p=frame.step(entry_tick=1,observation=self.obs(free_count=None,inventory_inputs=Inventory((0,))))
        self.assertFalse(p.complete)
        with self.assertRaises(ValueError):
            frame.step(observation=self.obs(free_count=None,inventory_inputs=Inventory((1,)*28)))
        p=frame.step(observation=self.obs(free_count=None,inventory_inputs=Inventory((0,)+(1,)*27)),
                     samples=self.samples(),helper_returned=True)
        self.assertTrue(p.complete)
    def test_current_enqueue_gate_is_frozen_until_tick_arrives(self):
        frame=BuyOpenFrame(State())
        p=frame.step(entry_tick=1,observation=self.obs(),samples={0:QueueSample(None,1)})
        self.assertFalse(p.complete)
        with self.assertRaises(ValueError):frame.step(samples={0:QueueSample(None,0)})
        p=frame.step(samples={0:QueueSample(10,1),1:QueueSample(None,0)},helper_returned=True)
        self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1)
    def test_zero_selection_still_needs_normal_helper_return(self):
        frame=BuyOpenFrame(State())
        p=frame.step(entry_tick=1,observation=self.obs(records=()))
        self.assertEqual(p.status,'needs_helper_return')
        p=frame.step(helper_returned=True)
        self.assertTrue(p.complete);self.assertEqual(p.queue.records,());self.assertEqual(p.state.phase_dword,4)
    def test_not_phase3_is_only_a_skipped_slice(self):
        frame=BuyOpenFrame(State(phase_dword=5))
        p=frame.step();self.assertEqual(p.status,'not_applicable');self.assertTrue(p.complete)
        self.assertEqual(p.calls,());self.assertEqual(p.state.phase_dword,5)
    def test_external_state_mutation_rejected_and_false_can_be_completed(self):
        frame=BuyOpenFrame(State())
        frame.step(entry_tick=1,observation=self.obs(zero_helper_returns={0:False}))
        p=frame.step(observation=self.obs(),samples=self.samples(),helper_returned=False)
        self.assertEqual(p.status,'needs_helper_return')
        p=frame.step(helper_returned=True);self.assertTrue(p.complete)
        frame=BuyOpenFrame(State());frame.step();frame.state=replace(frame.state,pending_byte=1)
        with self.assertRaises(ValueError):frame.step(entry_tick=1)

if __name__=='__main__':unittest.main()
