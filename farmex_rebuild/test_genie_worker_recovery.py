import unittest
from dataclasses import replace
from genie_worker import GeniePrefixFrame,plan_genie_prefix
from genie_recovery import GenieRecoveryObservation,RecoverySlotSample,TARGET_NAME
from direct_chat_packets import QueueAttempt
from test_genie_worker import sample as worker
from test_genie_recovery import sample as recovery

def bound(**changes):
    return replace(worker(initial_ba_byte=1,recovery_ba_byte=1,recovery_probe_eax=1,**changes),recovery_observation=recovery())

class WorkerRecoveryTests(unittest.TestCase):
    def test_success_binds_context_lowAL_queue_and_fresh_parent_timestamp(self):
        p=plan_genie_prefix(bound())
        self.assertTrue(p.complete)
        self.assertEqual(p.recovery_execution.context_dword,0x561ef8)
        self.assertEqual(len(p.recovery_execution.queue.records),1)
        self.assertEqual(p.stores[:3],((0x553cf0,1,1),(0x553cf4,4,5001),(0x553cf8,4,0)))
        self.assertFalse(p.native_execution_verified)

    def test_incomplete_child_blocks_parent_even_with_outer_normal_and_EAX(self):
        p=plan_genie_prefix(replace(bound(),recovery_observation=GenieRecoveryObservation()))
        self.assertFalse(p.complete);self.assertEqual(p.needed,('recovery','recovery_probe'))
        self.assertEqual(p.stores,())

    def test_gate_zero_still_has_AL_one_but_no_record(self):
        p=plan_genie_prefix(replace(bound(),recovery_observation=replace(recovery(),attempt=QueueAttempt(0,None,True))))
        self.assertTrue(p.complete);self.assertEqual(p.recovery_execution.queue.records,())
        self.assertEqual(p.stores[0],(0x553cf0,1,1))

    def test_only_success_AL_is_known_but_false_full_EAX_is_zero(self):
        o=bound();p=plan_genie_prefix(replace(o,values={**o.values,'recovery_probe_eax':0xabcdef01}))
        self.assertTrue(p.complete)
        for eax in (0,2):
            with self.assertRaises(ValueError):plan_genie_prefix(replace(o,values={**o.values,'recovery_probe_eax':eax}))
        empty=replace(o,recovery_observation=recovery(item=0))
        p=plan_genie_prefix(replace(empty,values={**empty.values,'recovery_probe_eax':0}))
        self.assertTrue(p.complete)
        with self.assertRaises(ValueError):plan_genie_prefix(replace(empty,values={**empty.values,'recovery_probe_eax':0x100}))

    def test_cached_child_enqueue_survives_parent_return_and_timestamp_gaps(self):
        f=GeniePrefixFrame();o=bound();r=dict(o.normal_returns);r['recovery_probe']=False
        p=f.advance(replace(o,normal_returns=r));self.assertFalse(p.complete)
        self.assertEqual(len(p.recovery_execution.queue.records),1)
        p=f.advance(type(o)({'recovery_probe_eax':1},{'recovery_probe':True}))
        self.assertFalse(p.complete);self.assertEqual(p.needed,('normal','recovery_probe_post_tick'))
        p=f.advance(o);self.assertTrue(p.complete)
        self.assertEqual(len(p.recovery_execution.queue.records),1)
        self.assertIs(f.advance(type(o)()),p)

    def test_child_prefix_resumes_without_repeating_slot_or_queue_record(self):
        f=GeniePrefixFrame();o=bound();child=recovery()
        child=replace(child,samples={14:RecoverySlotSample(TARGET_NAME,1,None)})
        p=f.advance(replace(o,recovery_observation=child));self.assertFalse(p.complete)
        tail=GenieRecoveryObservation({14:RecoverySlotSample(b'changed',0,123)},recovery().normal_returns,QueueAttempt(1,77,True))
        p=f.advance(replace(o,recovery_observation=tail));self.assertTrue(p.complete)
        self.assertEqual(p.recovery_execution.scan.payload,bytes.fromhex('9701017b000000'))
        self.assertEqual(len(p.recovery_execution.queue.records),1)

    def test_unreached_recovery_child_is_not_evaluated(self):
        o=replace(worker(),recovery_observation=GenieRecoveryObservation({14:object()}))
        self.assertTrue(plan_genie_prefix(o).complete)
        f=GeniePrefixFrame();self.assertTrue(f.advance(o).complete);self.assertIsNone(f.recovery_frame)

if __name__=='__main__':unittest.main()
