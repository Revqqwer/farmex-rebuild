import unittest
from dataclasses import replace
from action_queue import QueueState,enqueue
from direct_chat_packets import QueueAttempt
from item_break_manual import ItemBreakManualObservation
from item_break_manual_runtime import OwnedManualItemBreak,ManualBreakInput
from test_item_break_manual import sample,candidate


class ManualRuntimeTests(unittest.TestCase):
    def test_click_without_provider_waits_without_implicit_helper_entry(self):
        runtime=OwnedManualItemBreak();ticket=runtime.click()
        p=runtime.advance(QueueState())
        self.assertEqual(p.ticket,ticket);self.assertFalse(p.complete)
        self.assertEqual(p.plan.manual.needed,('entry','00471144'))
        self.assertEqual(p.queue.records,());self.assertTrue(runtime.pending)

    def test_manual_child_and_callback_returns_are_independent(self):
        runtime=OwnedManualItemBreak();runtime.click()
        p=runtime.advance(QueueState(),ManualBreakInput(sample()))
        self.assertEqual(p.plan.needed,'handler_returned')
        self.assertEqual(len(p.queue.records),3);self.assertEqual(p.published_record_ids,(1,2,3))
        for _ in range(3):
            q=runtime.advance(p.queue)
            self.assertFalse(q.complete);self.assertEqual(q.queue,p.queue)
            self.assertEqual(q.published_record_ids,())
        q=runtime.advance(p.queue,ManualBreakInput(handler_returned=True))
        self.assertTrue(q.complete);self.assertFalse(runtime.pending)
        self.assertEqual(q.queue,p.queue);self.assertEqual(q.status,'request_child_returned')

    def test_partial_enqueue_preserves_interleaved_writer_and_fresh_ids(self):
        runtime=OwnedManualItemBreak();runtime.click();s=sample()
        target=replace(s.request_inputs.target_child,attempt=QueueAttempt(1,10,None))
        partial=replace(s,request_inputs=replace(s.request_inputs,target_child=target))
        p=runtime.advance(QueueState(),ManualBreakInput(partial,True))
        self.assertEqual(len(p.queue.records),1);self.assertFalse(p.complete)
        shared=enqueue(p.queue,b'other writer',12,0,1,11).state
        q=runtime.advance(shared,ManualBreakInput(s,True))
        self.assertTrue(q.complete);self.assertEqual(q.published_record_ids,(3,4))
        self.assertEqual([r.record_id for r in q.queue.records],[1,2,3,4])
        self.assertEqual(q.queue.records[1].payload,b'other writer')
        self.assertEqual([r.delay_dword for r in q.queue.records],[0,0,200,250])

    def test_each_click_is_fifo_and_needs_fresh_invocation_observations(self):
        runtime=OwnedManualItemBreak();first=runtime.click();second=runtime.click()
        self.assertNotEqual(first,second)
        p=runtime.advance(QueueState(),ManualBreakInput(sample(),True))
        self.assertTrue(p.complete);self.assertEqual(p.ticket,first);self.assertEqual(p.queued_invocations,1)
        context=runtime.context(p.queue)
        self.assertEqual(context.ticket,second);self.assertIsNone(context.pending)
        q=runtime.advance(p.queue)
        self.assertFalse(q.complete);self.assertEqual(q.ticket,second)
        self.assertEqual(q.queue,p.queue)
        q=runtime.advance(q.queue,ManualBreakInput(sample(),True))
        self.assertTrue(q.complete);self.assertEqual(len(q.queue.records),6)

    def test_existing_queue_is_captured_when_head_invocation_starts(self):
        runtime=OwnedManualItemBreak();runtime.click()
        shared=enqueue(QueueState(),b'existing',8,0,1,1).state
        p=runtime.advance(shared,ManualBreakInput(sample(),True))
        self.assertEqual(p.queue.records[0],shared.records[0])
        self.assertEqual(p.published_record_ids,(2,3,4))

    def test_npc_prefix_store_survives_missing_select_return_bits(self):
        runtime=OwnedManualItemBreak();runtime.click();s=sample();npc=candidate()
        npc=replace(npc,values={**npc.values,'selected_npc_eax':6},
            normal_returns={**npc.normal_returns,'select_npc':True})
        p=runtime.advance(QueueState(),ManualBreakInput(replace(s,npc_inputs=npc)))
        self.assertFalse(p.complete);self.assertEqual(p.scalar_state[0x569a28],(4,5))
        self.assertEqual(p.queue.records,())
        self.assertFalse(p.native_execution_verified)

    def test_manual_path_does_not_require_automatic_enable_work_or_clock_inputs(self):
        runtime=OwnedManualItemBreak();runtime.click()
        p=runtime.advance(QueueState(),ManualBreakInput(sample(),True))
        self.assertTrue(p.complete)
        self.assertFalse(any(c[0] in ('00470f6c','004710d4','GetTickCount','0040ae0c') for c in p.plan.manual.calls))
        self.assertEqual([r.delay_dword for r in p.queue.records],[0,200,250])

    def test_notice_and_nonzero_mode_paths_do_not_enqueue(self):
        for s,status in ((replace(sample(),npc_inputs=candidate(True)),'npc_zero_notice_returned'),
            (replace(sample(),values={'fresh_mode_dword':0,'gem_lookup_eax':0}),'gem_zero_notice_returned'),
            (replace(sample(),values={'fresh_mode_dword':1}),'nonzero_mode_skips_manual_action')):
            runtime=OwnedManualItemBreak();runtime.click()
            p=runtime.advance(QueueState(),ManualBreakInput(s,True))
            self.assertTrue(p.complete);self.assertEqual(p.status,status);self.assertEqual(p.queue.records,())

    def test_reset_invalidates_pending_tickets_and_keeps_published_queue_external(self):
        runtime=OwnedManualItemBreak();ticket=runtime.click()
        p=runtime.advance(QueueState(),ManualBreakInput(sample()))
        runtime.reset();self.assertFalse(runtime.pending);self.assertFalse(runtime.scalar_state)
        q=runtime.advance(p.queue)
        self.assertEqual(q.status,'idle');self.assertEqual(q.queue,p.queue)
        self.assertIsNone(runtime.context(p.queue));self.assertNotEqual(runtime.click(),ticket)

    def test_bad_input_does_not_mutate_current_ticket_or_queue(self):
        runtime=OwnedManualItemBreak();ticket=runtime.click()
        with self.assertRaises(ValueError):runtime.advance(QueueState(),'not typed')
        self.assertEqual(runtime.context(QueueState()).ticket,ticket)
        self.assertIsNone(runtime.frame)
        with self.assertRaises(ValueError):ManualBreakInput(handler_returned=1)


if __name__=='__main__':unittest.main()
