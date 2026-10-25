import unittest
from dataclasses import replace
from fixed_callback_guard import *
from action_queue import QueueSample
from transformation import TransformationUseSamples

def cast():return TransformationUseSamples(actor_returned=True,actor_dword=0x12345678,
                copy_returns=(True,True,True),queue_gate=1,queue_tick=5500,cast_returned=True)
def ready():return FixedGuardObservation(0,1,5000,True,1,cast(),6000)
def gate(**changes):return replace(CallbackQueueGate(1,1,0,0,0,1),**changes)

class FixedGuardTests(unittest.TestCase):
    def frame(self,last=0):return FixedGuardFrame(FixedGuardState(last))
    def test_disabled_zero_return_and_unknown_other_branch(self):
        p=self.frame(None).advance(FixedGuardObservation(0,0))
        self.assertTrue(p.complete);self.assertEqual((p.al,p.eax_dword),(0,0))
        p=self.frame().advance(FixedGuardObservation(1))
        self.assertFalse(p.complete);self.assertIsNone(p.al);self.assertEqual(p.queue.records,())
        self.assertIn('manual CAPTCHA',p.missing)
    def test_unsigned_dword_5000_threshold_wrap_and_rewind(self):
        p=self.frame().advance(replace(ready(),initial_tick_dword=4999,check_returned=None))
        self.assertEqual(p.status,'waiting_5000')
        for last,tick in ((0,5000),(0xfffffff0,0x1378),(100,5)):
            p=self.frame(last).advance(replace(ready(),initial_tick_dword=tick,check_eax_dword=0))
            self.assertTrue(p.complete);self.assertEqual(p.status,'fixed_skill_unavailable')
            self.assertGreaterEqual(p.elapsed_dword,5000)
    def test_check_uses_al_and_no_plus2000_fallback(self):
        p=self.frame().advance(replace(ready(),check_eax_dword=0x100))
        self.assertEqual(p.al,0);self.assertIsNone(p.cast_plan)
        p=self.frame().advance(replace(ready(),check_eax_dword=0x10001))
        self.assertEqual(p.al,1);self.assertEqual(p.cast_plan.selection.selected_skill,FIXED_SKILL)
        self.assertEqual(p.cast_plan.selection.checks,())
    def test_cast_record_then_independent_post_tick_and_mov_al_preserves_high_bits(self):
        f=self.frame();p=f.advance(replace(ready(),post_cast_tick_dword=None))
        self.assertFalse(p.complete);self.assertIsNone(p.al);self.assertEqual(len(p.queue.records),1)
        self.assertEqual(p.state.last_tick_dword,0)
        p=f.advance(FixedGuardObservation(post_cast_tick_dword=0x12345678))
        self.assertTrue(p.complete);self.assertEqual(p.eax_dword,0x12345601)
        self.assertEqual(p.state.last_tick_dword,0x12345678);self.assertEqual(len(p.queue.records),1)
        self.assertEqual(p.queue.records[0].payload[2:6],FIXED_SKILL.to_bytes(4,'little'))
    def test_missing_clock_checker_actor_and_copy_do_not_invent_return(self):
        for o in (replace(ready(),initial_tick_dword=None),replace(ready(),check_returned=None),
                  replace(ready(),check_eax_dword=None),replace(ready(),cast_inputs=None),
                  replace(ready(),cast_inputs=replace(cast(),actor_returned=None)),
                  replace(ready(),cast_inputs=replace(cast(),copy_returns=()))):
            p=self.frame().advance(o);self.assertFalse(p.complete);self.assertIsNone(p.al)
            self.assertEqual(p.queue.records,())
    def test_check_and_clock_prefix_remain_frozen_across_later_gap(self):
        f=self.frame();p=f.advance(replace(ready(),cast_inputs=None))
        self.assertFalse(p.complete)
        p=f.advance(replace(ready(),initial_tick_dword=1,check_eax_dword=0))
        self.assertTrue(p.complete);self.assertEqual(p.al,1);self.assertEqual(p.elapsed_dword,5000)

class BoundCallbackTests(unittest.TestCase):
    def test_new_record_skips_current_consumer_then_next_callback_can_drain(self):
        f=FixedGuardQueueFrame(QueueState(),gate(),FixedGuardState(0));p=f.advance(ready())
        self.assertTrue(p.complete);self.assertEqual(p.queue_decision.status,'callback_skipped_queue')
        self.assertEqual(len(p.queue.records),1);self.assertEqual(p.queue_decision.events,())
        next_frame=FixedGuardQueueFrame(p.queue,gate(),p.guard_state)
        o=FixedGuardObservation(0,1,6001)
        q=next_frame.advance(o,{1:QueueSample(6001,1,True)},work_queue_returned=True,post_work_queue=p.queue)
        self.assertTrue(q.complete);self.assertEqual(q.guard_plan.al,0);self.assertEqual(q.queue.records,())
        self.assertTrue(any(e.kind=='native_send_plan' for e in q.queue_decision.events))
        self.assertTrue(all(not e.acknowledged for e in q.queue_decision.events))
        self.assertFalse(q.native_execution_verified)
    def test_missing_post_tick_retains_record_but_does_not_guess_al_or_drain(self):
        f=FixedGuardQueueFrame(QueueState(),gate(),FixedGuardState(0))
        p=f.advance(replace(ready(),post_cast_tick_dword=None))
        self.assertFalse(p.complete);self.assertIsNone(p.queue_decision);self.assertEqual(len(p.queue.records),1)
        p=f.advance(FixedGuardObservation(post_cast_tick_dword=6000))
        self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1)
        self.assertIs(f.advance(None),p)
    def test_outer_skip_and_guard_bypass_do_not_consume_child_observations(self):
        for g in (gate(ready_46edb0=0,helper_46f33c=1),gate(initial_reader_f3c=1),gate(byte_561f55=0)):
            p=FixedGuardQueueFrame(QueueState(),g,FixedGuardState()).advance(None,work_queue_returned=True,post_work_queue=QueueState())
            self.assertTrue(p.complete);self.assertIsNone(p.guard_plan)
    def test_raw_guard_conflicts_only_at_reached_bound_branch(self):
        with self.assertRaises(ValueError):FixedGuardQueueFrame(QueueState(),gate(helper_46f33c=1),FixedGuardState(0)).advance(ready())
    def test_unknown_guard_branch_is_not_zero_fallback(self):
        p=FixedGuardQueueFrame(QueueState(),gate(),FixedGuardState(0)).advance(FixedGuardObservation(1))
        self.assertFalse(p.complete);self.assertIsNone(p.queue_decision);self.assertIsNone(p.guard_plan.al)
    def test_raw_types(self):
        for args in ({'mode_byte_561f7c':256},{'check_eax_dword':True},{'check_returned':1}):
            with self.assertRaises(ValueError):FixedGuardObservation(**args)

    def test_work_helper_return_and_fresh_queue_are_independent(self):
        q=FixedGuardQueueFrame(QueueState(),gate(),FixedGuardState(0)).advance(ready()).queue
        f=FixedGuardQueueFrame(q,gate(initial_reader_f3c=1),FixedGuardState(6000))
        p=f.advance(None);self.assertFalse(p.complete);self.assertIn('work queue normal return',p.missing)
        p=f.advance(None,work_queue_returned=True);self.assertFalse(p.complete);self.assertIn('fresh queue',p.missing)
        # Explicit observed post-helper state may differ; never infer purity.
        changed=QueueState((),q.next_id)
        p=f.advance(None,work_queue_returned=True,post_work_queue=changed)
        self.assertTrue(p.complete);self.assertEqual(p.queue.records,());self.assertEqual(p.queue_decision.events,())

    def test_skipped_callback_does_not_require_work_helper_receipt(self):
        p=FixedGuardQueueFrame(QueueState(),gate(ready_46edb0=0),FixedGuardState()).advance(None)
        self.assertTrue(p.complete);self.assertEqual(p.queue_decision.status,'callback_skipped_queue')

if __name__=='__main__':unittest.main()
