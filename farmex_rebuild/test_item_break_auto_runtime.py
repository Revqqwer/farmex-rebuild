import unittest
from dataclasses import replace
from action_queue import QueueState,enqueue
from item_break_auto_runtime import OwnedAutoItemBreak,AutoBreakInput
from item_break_cycle import ItemBreakCycleObservation,ItemBreakClockObservation
from item_break_inventory import ItemBreakInventoryObservation,InventorySpaceObservation
from test_item_break_requests import caller,request,candidate,caller_clock


def sample(**kw):
    args=dict(caller=caller(),request=request(),npc=candidate(),npc_parent_returned=True,
        action_parent_returned=True)
    args.update(kw);return AutoBreakInput(**args)


def runtime():
    r=OwnedAutoItemBreak();r.configure(True);return r


class AutoRuntimeTests(unittest.TestCase):
    def test_own_enable_does_not_supply_source_entry_or_gates(self):
        r=OwnedAutoItemBreak();p=r.advance(QueueState())
        self.assertEqual(p.status,'inactive');self.assertIsNone(r.frame)
        r.configure(True);p=r.advance(QueueState())
        self.assertFalse(p.complete);self.assertEqual(p.plan.needed,'entry_reached')
        self.assertEqual(p.queue.records,());self.assertTrue(p.enabled)

    def test_source_disabled_and_outer_gate_skip_children_with_own_checkbox_on(self):
        for c,status in ((ItemBreakCycleObservation(True,0),'outer_gate_zero'),
                         (ItemBreakCycleObservation(True,1,0),'settings_disabled')):
            r=runtime();p=r.advance(QueueState(),AutoBreakInput(c))
            self.assertTrue(p.complete);self.assertTrue(p.enabled)
            self.assertEqual(p.status,status);self.assertEqual(p.queue.records,())
            self.assertIsNone(p.plan.caller.npc)

    def test_full_chain_publishes_three_records_and_post_clock_shadow(self):
        r=runtime();p=r.advance(QueueState(),sample())
        self.assertTrue(p.complete);self.assertEqual(p.status,'action_returned_clock_updated')
        self.assertEqual([v.delay_dword for v in p.queue.records],[0,200,250])
        self.assertEqual(p.published_record_ids,(1,2,3))
        self.assertEqual(p.scalar_state[0x553d50],(4,1010));self.assertEqual(p.scalar_state[0x553d54],(4,0))
        self.assertEqual(p.scalar_state[0x569a28],(4,5));self.assertIsNone(r.frame)
        self.assertFalse(p.delivery_verified)

    def test_request_parent_and_two_post_clock_gates_preserve_prefix(self):
        r=runtime();c=replace(caller(),clock_inputs=caller_clock(second_tick_returned=None,second_tick_dword=None),clock_returned=None)
        p=r.advance(QueueState(),sample(caller=c,action_parent_returned=None))
        self.assertEqual(p.plan.needed,'action_parent_returned')
        self.assertEqual(len(p.queue.records),3);self.assertNotIn(0x553d50,p.scalar_state)
        for _ in range(2):
            q=r.advance(p.queue);self.assertEqual(q.queue,p.queue);self.assertEqual(q.published_record_ids,())
        p=r.advance(p.queue,AutoBreakInput(action_parent_returned=True))
        self.assertFalse(p.complete);self.assertNotIn(0x553d50,p.scalar_state)
        p=r.advance(p.queue,AutoBreakInput(caller=ItemBreakCycleObservation(clock_inputs=
            ItemBreakClockObservation(second_tick_returned=True,second_tick_dword=1234))))
        self.assertFalse(p.complete);self.assertEqual(p.plan.needed,'clock_returned')
        self.assertEqual(p.scalar_state[0x553d50],(4,1234))
        p=r.advance(p.queue,AutoBreakInput(caller=ItemBreakCycleObservation(clock_returned=True)))
        self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),3)

    def test_interleaved_manual_writer_survives_partial_enqueue(self):
        from direct_chat_packets import QueueAttempt
        r=runtime();req=request();req=replace(req,attempts={0:QueueAttempt(1,101,None)})
        p=r.advance(QueueState(),sample(request=req))
        self.assertFalse(p.complete);self.assertEqual(len(p.queue.records),2)
        shared=enqueue(p.queue,b'manual',6,0,1,105).state
        p=r.advance(shared,sample())
        self.assertTrue(p.complete);self.assertEqual(p.published_record_ids,(4,))
        self.assertEqual(p.queue.records[2].payload,b'manual')
        self.assertEqual([v.record_id for v in p.queue.records],[1,2,3,4])

    def test_committed_stamp_is_reused_for_next_invocation_without_fabricating_zero(self):
        r=runtime();p=r.advance(QueueState(),sample())
        c=replace(caller(),clock_inputs=caller_clock(first_tick_dword=2009,last_tick_low=None,last_tick_high=None))
        p=r.advance(p.queue,sample(caller=c))
        self.assertTrue(p.complete);self.assertEqual(p.status,'waiting')
        self.assertEqual(len(p.queue.records),3);self.assertEqual(p.invocation,2)
        c=replace(c,clock_inputs=replace(c.clock_inputs,first_tick_dword=2010,second_tick_dword=2020))
        p=r.advance(p.queue,sample(caller=c))
        self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),6)
        self.assertEqual(p.scalar_state[0x553d50],(4,2020))

    def test_stale_clock_capture_is_rejected_only_at_reached_read(self):
        r=runtime();p=r.advance(QueueState(),sample())
        p=r.advance(p.queue,sample(caller=ItemBreakCycleObservation(True,0,
            clock_inputs=caller_clock(last_tick_low=999))))
        self.assertEqual(p.status,'outer_gate_zero')
        p=r.advance(p.queue,sample(caller=replace(caller(),clock_inputs=caller_clock(first_tick_dword=2009))))
        self.assertEqual(p.status,'conflicting_clock_observation');self.assertFalse(p.complete)
        self.assertEqual(len(p.queue.records),3)
        p=r.advance(p.queue,sample(caller=replace(caller(),clock_inputs=
            caller_clock(first_tick_dword=9999,last_tick_low=None,last_tick_high=None))))
        self.assertEqual(p.status,'waiting') # Previously consumed pre-clock2009 retained.
        self.assertEqual(len(p.queue.records),3)

    def test_signed_threshold_and_qword_rollover_are_not_reinterpreted(self):
        r=runtime();c=replace(caller(),clock_inputs=caller_clock(first_tick_dword=32,last_tick_low=0xfffffff0,speed_dword=0))
        p=r.advance(QueueState(),sample(caller=c))
        self.assertTrue(p.complete);self.assertEqual(p.status,'waiting');self.assertEqual(p.queue.records,())
        r=runtime();c=replace(caller(),clock_inputs=caller_clock(first_tick_dword=32,speed_dword=0xffffffff))
        p=r.advance(QueueState(),sample(caller=c))
        self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),3)

    def test_guard_parent_does_not_infer_fresh_second_work_byte(self):
        scan=InventorySpaceObservation(True,{slot:True for slot in range(14,42)},
            {slot:0x100 for slot in range(14,42)})
        guard=ItemBreakInventoryObservation(True,inventory_inputs=scan,inventory_returned=True,
            stop_returned=True,full_notice_returned=True)
        r=runtime();p=r.advance(QueueState(),AutoBreakInput(
            caller=ItemBreakCycleObservation(True,1,1,1),guard=guard,guard_parent_returned=True))
        self.assertFalse(p.complete);self.assertEqual(p.plan.needed,'second_work_byte')
        self.assertEqual(p.plan.caller.caller.inventory_guard.status,'inventory_full_stop_notice_returned')
        self.assertTrue(p.enabled);self.assertEqual(p.queue.records,())
        p=r.advance(p.queue,AutoBreakInput(caller=ItemBreakCycleObservation(second_work_byte=0)))
        self.assertTrue(p.complete);self.assertEqual(p.status,'second_work_gate_zero')
        self.assertIsNone(p.plan.caller.npc)

    def test_npc_zero_requires_stop_and_notice_before_invocation_completes(self):
        npc=candidate();npc=replace(npc,values={**npc.values,'npc_id_eax':0},
            normal_returns={**npc.normal_returns,'failure_cleanup':True})
        r=runtime();p=r.advance(QueueState(),sample(npc=npc))
        self.assertEqual(p.plan.needed,'stop_returned');self.assertEqual(p.queue.records,())
        p=r.advance(p.queue,AutoBreakInput(caller=ItemBreakCycleObservation(stop_returned=True)))
        self.assertEqual(p.plan.needed,'npc_notice_span_returned')
        p=r.advance(p.queue,AutoBreakInput(caller=ItemBreakCycleObservation(npc_notice_span_returned=True)))
        self.assertTrue(p.complete);self.assertEqual(p.status,'npc_zero_stop_notice_returned')
        self.assertTrue(p.enabled)

    def test_toggle_preserves_committed_stamp_but_profile_reset_invalidates_it(self):
        r=runtime();p=r.advance(QueueState(),sample());old=r.generation
        r.configure(False);self.assertGreater(r.generation,old)
        q=r.advance(p.queue);self.assertEqual(q.status,'inactive');self.assertEqual(q.queue,p.queue)
        r.configure(True);self.assertEqual(r.scalar_state[0x553d50],(4,1010))
        q=r.advance(p.queue);self.assertFalse(q.complete);self.assertEqual(q.plan.needed,'entry_reached')
        r.reset();self.assertFalse(r.scalar_state);self.assertFalse(r.enabled);self.assertIsNone(r.frame)

    def test_child_bindings_cannot_be_bypassed_and_context_is_immutable(self):
        with self.assertRaises(ValueError):AutoBreakInput(caller=ItemBreakCycleObservation(npc_eax=1))
        with self.assertRaises(ValueError):AutoBreakInput(caller=ItemBreakCycleObservation(
            clock_inputs=ItemBreakClockObservation(action_returned=True)))
        r=runtime();context=r.context(QueueState(),{'speed':'1'})
        with self.assertRaises(TypeError):context.configuration['speed']='0'
        self.assertIsNone(r.frame)

    def test_manual_and_automatic_paths_share_npc_context_without_resetting_clock(self):
        from item_break_manual_runtime import OwnedManualItemBreak,ManualBreakInput
        from test_item_break_manual import sample as manual_sample
        shared={};r=OwnedAutoItemBreak(shared);r.configure(True)
        p=r.advance(QueueState(),sample())
        manual=OwnedManualItemBreak(shared);manual.click();s=manual_sample()
        npc=replace(s.npc_inputs,values={**s.npc_inputs.values,'npc_id_eax':9,'selected_npc_eax':9})
        m=manual.advance(p.queue,ManualBreakInput(replace(s,npc_inputs=npc),True))
        self.assertTrue(m.complete);self.assertEqual(shared[0x569a28],(4,9))
        self.assertEqual(r.context(m.queue,{}).scalar_state[0x569a28],(4,9))
        self.assertEqual(shared[0x553d50],(4,1010))
        r.configure(False);self.assertEqual(shared[0x553d50],(4,1010))
        r.reset();self.assertEqual(manual.scalar_state,{})

    def test_pending_paths_do_not_replay_old_stores_over_other_path(self):
        from item_break_manual_runtime import OwnedManualItemBreak,ManualBreakInput
        from test_item_break_manual import sample as manual_sample
        shared={};r=OwnedAutoItemBreak(shared);r.configure(True)
        p=r.advance(QueueState(),sample(npc_parent_returned=None))
        self.assertFalse(p.complete);self.assertEqual(shared[0x569a28],(4,5))
        manual=OwnedManualItemBreak(shared);manual.click();s=manual_sample()
        npc=replace(s.npc_inputs,values={**s.npc_inputs.values,'npc_id_eax':9,'selected_npc_eax':9})
        m=manual.advance(p.queue,ManualBreakInput(replace(s,npc_inputs=npc)))
        self.assertFalse(m.complete);self.assertEqual(shared[0x569a28],(4,9))
        p=r.advance(m.queue)
        self.assertFalse(p.complete);self.assertEqual(shared[0x569a28],(4,9))
        # A later fresh automatic invocation writes5; resuming the older
        # manual callback must preserve5 rather than replay its earlier9 store.
        r.configure(False);r.configure(True)
        p=r.advance(p.queue,sample())
        self.assertTrue(p.complete);self.assertEqual(shared[0x569a28],(4,5))
        m=manual.advance(p.queue,ManualBreakInput(handler_returned=True))
        self.assertTrue(m.complete);self.assertEqual(shared[0x569a28],(4,5))


if __name__=='__main__':unittest.main()
