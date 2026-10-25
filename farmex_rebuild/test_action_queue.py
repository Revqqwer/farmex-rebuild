import unittest
from action_queue import QueueState,QueueSample,enqueue,drain
from repair_packets import repair_payload
from quest_engine import QuestRecord,QuestSnapshot,plan_take_quest


class ActionQueueTests(unittest.TestCase):
    def queue(self,delays=(0,),tick=1000):
        state=QueueState()
        for delay in delays:
            state=enqueue(state,b'packet',6,delay,1,tick).state
        return state

    def test_disconnected_enqueue_does_not_read_buffer_or_clock(self):
        state=QueueState()
        result=enqueue(state,None,0xffffffff,0,0)
        self.assertEqual(result.status,'not_enqueued');self.assertIs(result.state,state)

    def test_unknown_gate_does_not_claim_enqueued_state(self):
        result=enqueue(QueueState(),b'x',1,0,None,1000)
        self.assertIsNone(result.state);self.assertEqual(result.status,'needs_observation')

    def test_buffer_copy_is_prefix_and_independent_of_caller(self):
        payload=bytearray(b'abcTAIL')
        result=enqueue(QueueState(),payload,3,0,1,1000)
        payload[0]=ord('Z')
        self.assertEqual(result.state.records[0].payload,b'abc')
        self.assertFalse(result.events[0].acknowledged)

    def test_zero_length_has_no_invented_terminator(self):
        result=enqueue(QueueState(),b'',0,0,1,1000)
        self.assertEqual(result.state.records[0].payload,b'')

    def test_wrapped_allocation_and_own_copy_limit_are_distinct(self):
        self.assertEqual(enqueue(QueueState(),None,0xffffffff,0,1).status,'unresolved_allocation_wrap')
        self.assertEqual(enqueue(QueueState(),b'abc',3,0,1,1000,copy_limit=2).status,'local_copy_limit')

    def test_partial_payload_and_missing_clock_are_unresolved(self):
        self.assertIsNone(enqueue(QueueState(),b'x',2,0,1,1000).state)
        self.assertIsNone(enqueue(QueueState(),b'x',1,0,1).state)

    def test_delay_boundary_is_inclusive(self):
        state=self.queue((500,))
        self.assertEqual(drain(state,{1:QueueSample(1499)}).state,state)
        due=drain(state,{1:QueueSample(1500,1,True)})
        self.assertEqual(due.state.records,())
        self.assertEqual([e.kind for e in due.events],['native_send_plan','free_and_mark'])

    def test_zero_delay_can_be_consumed_same_tick(self):
        self.assertEqual(drain(self.queue(),{1:QueueSample(1000,1,True)}).state.records,())

    def test_delay_dword_is_sign_extended(self):
        for delay in (0x80000000,0xffffffff):
            self.assertEqual(drain(self.queue((delay,)),{1:QueueSample(1000,1,True)}).state.records,())

    def test_gettickcount_wrap_does_not_become_positive_elapsed(self):
        state=self.queue((0,),tick=0xfffffff0)
        result=drain(state,{1:QueueSample(32)})
        self.assertEqual(result.state,state);self.assertEqual(result.events,())

    def test_signed_delay_against_negative_elapsed(self):
        state=self.queue((0xffffffff,),tick=1000)
        self.assertEqual(drain(state,{1:QueueSample(998)}).state,state)
        self.assertEqual(drain(state,{1:QueueSample(999,0)}).state.records,())

    def test_disconnected_due_record_is_dropped_without_sender(self):
        result=drain(self.queue(),{1:QueueSample(1000,0)})
        self.assertEqual(result.state.records,())
        self.assertEqual([e.kind for e in result.events],['due_disconnected_drop','free_and_mark'])

    def test_nonzero_connection_gate_is_not_exact_one(self):
        result=drain(self.queue(),{1:QueueSample(1000,256,True)})
        self.assertEqual(result.events[0].kind,'native_send_plan')

    def test_missing_sender_return_cannot_commit_a_removal(self):
        state=self.queue()
        for returned in (None,False):
            result=drain(state,{1:QueueSample(1000,1,returned)})
            self.assertEqual(result.status,'needs_sender_return');self.assertIsNone(result.state)
            self.assertEqual([e.kind for e in result.events],['native_send_plan'])
        self.assertEqual(len(state.records),1)

    def test_not_due_head_does_not_block_later_records(self):
        state=self.queue((1000,0,500))
        result=drain(state,{1:QueueSample(1000),2:QueueSample(1000,0),3:QueueSample(1500,1,True)})
        self.assertEqual([r.record_id for r in result.state.records],[1])
        self.assertEqual([e.record_id for e in result.events if e.kind=='free_and_mark'],[2,3])

    def test_tick_and_gate_are_fresh_per_record(self):
        result=drain(self.queue((500,500)),{1:QueueSample(1499),2:QueueSample(1500,0)})
        self.assertEqual([r.record_id for r in result.state.records],[1])

    def test_missing_later_observation_leaves_prefix_uncommitted(self):
        state=self.queue((0,0))
        result=drain(state,{1:QueueSample(1000,0)})
        self.assertIsNone(result.state);self.assertEqual(len(state.records),2)
        self.assertEqual(len(result.events),2)

    def test_unknown_due_gate_is_not_disconnected(self):
        result=drain(self.queue(),{1:QueueSample(1000)})
        self.assertIsNone(result.state);self.assertIn('connection gate',result.missing)

    def test_repair_payload_survives_queue_without_acknowledgement(self):
        payload=repair_payload(1,12,4,12345)
        state=enqueue(QueueState(),payload,len(payload),0,1,1000).state
        result=drain(state,{1:QueueSample(1000,1,True)})
        self.assertEqual(result.events[0].payload,payload)
        self.assertTrue(all(not event.acknowledged for event in result.events))

    def test_quest_three_plans_keep_distinct_delays(self):
        snapshot=QuestSnapshot(0,0,12,0x123400,10,12,4,0x12345678)
        decision=plan_take_quest([QuestRecord('NPC',b'quest')],snapshot)
        self.assertEqual(decision.status,'local_plan')
        state=QueueState()
        for plan in decision.queue_plans:
            state=enqueue(state,plan.payload,len(plan.payload),plan.delay_ms,1,1000).state
        result=drain(state,{1:QueueSample(1500,1,True),2:QueueSample(1500),3:QueueSample(1500)})
        self.assertEqual([r.delay_dword for r in result.state.records],[1000,1500])
        self.assertEqual(result.events[0].payload,decision.queue_plans[0].payload)

    def test_invalid_raw_values_and_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError):QueueSample(tick=True)
        with self.assertRaises(ValueError):QueueSample(sender_returned=1)
        state=self.queue()
        with self.assertRaises(ValueError):QueueState(state.records+state.records,2)
        with self.assertRaises(ValueError):enqueue(state,b'x',-1,0,1,1000)

    def test_empty_queue_needs_no_observations(self):
        self.assertEqual(drain(QueueState(),{}).state,QueueState())
