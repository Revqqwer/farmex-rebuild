import unittest
from dataclasses import replace
from native_sender import *
from action_queue import QueueState,QueueSample,enqueue,drain

def sample(**kw):
    return replace(SenderObservation(0x3000,b'abc',((0x553e84,0x1000),(0x553e90,0x70b360)),
                                     ((0x1000,0x2000),),True),**kw)

class SenderOperandTests(unittest.TestCase):
    def test_source_call_shape_preserves_caller_registers_not_callee_eax(self):
        p=plan_source_sender(3,sample(),expected_payload=b'abc')
        self.assertTrue(p.complete)
        self.assertEqual((p.call.target,p.call.ecx,p.call.push_order),(0x70b360,0x2000,(3,0x3000)))
        self.assertEqual(p.call.assumed_callee_cleanup_bytes,8)
        self.assertTrue(p.call.source_preserves_caller_registers and p.call.source_preserves_caller_flags)
        self.assertFalse(p.call.abi_verified or p.native_execution_verified or p.acknowledgement_verified)

    def test_exact_observation_order_and_fresh_target(self):
        p=plan_source_sender(3,sample(global_samples=((0x553e84,0x1000),(0x553e90,0x76543210))))
        self.assertEqual(p.steps,(('global',0x553e84),('direct',0x1000),('push_length_then_pointer',3,0x3000),('global',0x553e90)))
        self.assertEqual(p.call.target,0x76543210)
        with self.assertRaises(ValueError):plan_source_sender(3,sample(global_samples=((0x553e90,0x70b360),(0x553e84,0x1000))))
        with self.assertRaises(ValueError):plan_source_sender(3,sample(direct_samples=((0x9999,0x2000),)))

    def test_missing_reads_do_not_default_to_static_profile_or_context(self):
        p=plan_source_sender(3,SenderObservation())
        self.assertEqual(p.missing,'global DWORD 00553e84');self.assertIsNone(p.call)
        p=plan_source_sender(3,sample(direct_samples=()))
        self.assertEqual(p.missing,'direct DWORD 00001000');self.assertIsNone(p.call)
        p=plan_source_sender(3,sample(global_samples=((0x553e84,0x1000),)))
        self.assertEqual(p.missing,'global DWORD 00553e90');self.assertIsNone(p.call)

    def test_source_null_slot_has_no_invented_success_or_early_return(self):
        p=plan_source_sender(3,sample(global_samples=((0x553e84,0),(0x553e90,123)),direct_samples=()))
        self.assertFalse(p.complete);self.assertEqual(p.missing,'direct DWORD 00000000')
        p=plan_source_sender(3,sample(global_samples=((0x553e84,0),(0x553e90,123)),direct_samples=((0,0),)))
        self.assertEqual(p.call.ecx,0) # Explicit fixture, not a real null dereference.
        self.assertFalse(p.native_execution_verified)

    def test_pointer_and_bound_bytes_are_separate_from_context_and_target(self):
        p=plan_source_sender(3,sample(buffer_pointer_dword=None),expected_payload=b'abc')
        self.assertEqual(p.missing,'sender payload pointer DWORD')
        self.assertEqual(p.steps,(('global',0x553e84),('direct',0x1000)))
        p=plan_source_sender(3,sample(observed_payload=None),expected_payload=b'abc')
        self.assertEqual(p.missing,'bound payload byte snapshot')
        with self.assertRaises(ValueError):plan_source_sender(3,sample(observed_payload=b'abX'),expected_payload=b'abc')
        with self.assertRaises(ValueError):plan_source_sender(2,sample(),expected_payload=b'abc')

    def test_native_normal_return_never_becomes_success_eax(self):
        p=plan_source_sender(3,sample(native_normal_returned=False))
        self.assertFalse(p.complete);self.assertIsNotNone(p.call)
        self.assertIn('target normal return',p.missing)
        self.assertFalse(hasattr(p,'returned_eax'))

    def test_raw_dword_and_ordered_sample_contract(self):
        for kw in ({'buffer_pointer_dword':True},{'global_samples':[(1,2)]},{'direct_samples':((1,-1),)},{'native_normal_returned':1}):
            with self.subTest(kw=kw),self.assertRaises(ValueError):SenderObservation(**kw)
        with self.assertRaises(ValueError):plan_source_sender(1<<32,sample())

class SenderQueueBindingTests(unittest.TestCase):
    def queue(self,delay=0):return enqueue(QueueState(),b'abc',3,delay,1,100).state

    def test_bound_sender_requires_operands_even_with_legacy_outer_return_true(self):
        p=drain(self.queue(),{1:QueueSample(100,1,True,SenderObservation())})
        self.assertIsNone(p.state);self.assertEqual(p.status,'needs_sender_operands')
        self.assertIn('00553e84',p.missing)
        self.assertIsNotNone(p.events[0].sender_plan)

    def test_child_target_return_and_wrapper_return_are_independent(self):
        p=drain(self.queue(),{1:QueueSample(100,1,True,sample(native_normal_returned=None))})
        self.assertEqual(p.status,'needs_sender_operands');self.assertIsNone(p.state)
        p=drain(self.queue(),{1:QueueSample(100,1,None,sample())})
        self.assertEqual(p.status,'needs_sender_return');self.assertIsNone(p.state)
        self.assertTrue(p.events[0].sender_plan.complete)
        p=drain(self.queue(),{1:QueueSample(100,1,True,sample())})
        self.assertEqual(p.status,'locally_drained');self.assertEqual(p.state.records,())
        self.assertEqual([e.kind for e in p.events],['native_send_plan','free_and_mark'])
        self.assertFalse(any(e.acknowledged for e in p.events))

    def test_not_due_disconnected_and_unknown_gate_skip_unreached_binding(self):
        wrong=sample(observed_payload=b'wrong')
        p=drain(self.queue(10),{1:QueueSample(100,1,True,wrong)})
        self.assertEqual(len(p.state.records),1);self.assertEqual(p.events,())
        p=drain(self.queue(),{1:QueueSample(100,0,True,wrong)})
        self.assertEqual(p.state.records,());self.assertEqual(p.events[0].kind,'due_disconnected_drop')
        p=drain(self.queue(),{1:QueueSample(100,None,True,wrong)})
        self.assertIsNone(p.state);self.assertIn('connection gate',p.missing)
        with self.assertRaises(ValueError):drain(self.queue(),{1:QueueSample(100,1,True,wrong)})

    def test_each_record_has_independent_context_target_and_native_receipt(self):
        q=enqueue(self.queue(),b'xyz',3,0,1,100).state
        second=sample(observed_payload=b'xyz',global_samples=((0x553e84,0x4000),(0x553e90,0x5555)),direct_samples=((0x4000,0x6000),))
        p=drain(q,{1:QueueSample(100,1,True,sample()),2:QueueSample(101,1,True,second)})
        self.assertEqual([e.sender_plan.call.ecx for e in p.events if e.sender_plan],[0x2000,0x6000])
        self.assertEqual([e.sender_plan.call.target for e in p.events if e.sender_plan],[0x70b360,0x5555])
        self.assertEqual(p.state.records,())

if __name__=='__main__':unittest.main()
