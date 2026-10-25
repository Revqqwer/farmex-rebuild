import unittest
from dataclasses import replace
from action_queue import QueueState,QueueSample,CallbackQueueGate,enqueue,drain_on_callback

class QueueCallbackTests(unittest.TestCase):
    def setUp(self):
        self.state=enqueue(QueueState(),b'payload',7,0,1,1000).state
        self.gate=CallbackQueueGate(1,1,0,0,1)
        self.samples={1:QueueSample(1000,1,True)}

    def test_readiness_failure_skips_queue_without_later_observations(self):
        result=drain_on_callback(self.state,CallbackQueueGate(ready_46edb0=0),{})
        self.assertEqual(result.status,'callback_skipped_queue');self.assertIs(result.state,self.state)

    def test_outer_connection_uses_exact_one_unlike_inner_nonzero(self):
        for value in (0,2,256,0xffffffff):
            result=drain_on_callback(self.state,CallbackQueueGate(1,value),{})
            self.assertEqual(result.state,self.state);self.assertEqual(result.events,())

    def test_pause_and_recovery_branches_keep_due_record(self):
        for name in ('byte_562208','byte_56221d'):
            result=drain_on_callback(self.state,replace(self.gate,**{name:255}),self.samples)
            self.assertEqual(result.status,'callback_skipped_queue');self.assertEqual(result.state,self.state)

    def test_initial_reader_nonzero_skips_guard_inputs(self):
        result=drain_on_callback(self.state,self.gate,self.samples)
        self.assertEqual(result.state.records,())

    def test_zero_reader_and_disabled_main_flag_skip_helper_observation(self):
        gate=replace(self.gate,initial_reader_f3c=0,byte_561f55=0)
        self.assertEqual(drain_on_callback(self.state,gate,self.samples).state.records,())

    def test_special_guard_blocks_only_when_reached_and_nonzero(self):
        gate=replace(self.gate,initial_reader_f3c=0,byte_561f55=1,helper_46f33c=1)
        self.assertEqual(drain_on_callback(self.state,gate,self.samples).state,self.state)
        self.assertEqual(drain_on_callback(self.state,replace(gate,helper_46f33c=0),self.samples).state.records,())

    def test_unknown_required_guard_is_not_false(self):
        gate=replace(self.gate,initial_reader_f3c=0)
        result=drain_on_callback(self.state,gate,self.samples)
        self.assertIsNone(result.state);self.assertEqual(result.status,'needs_observation')

    def test_connection_can_change_between_outer_gate_and_consumer(self):
        result=drain_on_callback(self.state,self.gate,{1:QueueSample(1000,0)})
        self.assertEqual(result.state.records,());self.assertEqual(result.events[0].kind,'due_disconnected_drop')

    def test_invalid_byte_gate_and_unknown_ready_rejected_or_uncommitted(self):
        with self.assertRaises(ValueError):CallbackQueueGate(byte_56221d=256)
        with self.assertRaises(ValueError):CallbackQueueGate(ready_46edb0=True)
        self.assertIsNone(drain_on_callback(self.state,CallbackQueueGate(),{}).state)
