import unittest
from dataclasses import replace
from operation_engine import UpgradeRunner,UpgradeSnapshot
from upgrade_execution import UpgradeExecution,ArmorExecutionInputs
from upgrade_armor import ArmorPacketObservation,VENDORS
from action_queue import QueueSample


class ArmorExecutionTests(unittest.TestCase):
    def execution(self,counter=0):
        r=UpgradeRunner(source_clock=True);r.start_armor(initial_stamp_qword=0);r.armor_attempts=counter
        return UpgradeExecution(r)

    def inputs(self,cleanup=True):
        return ArmorExecutionInputs(9,100,0x112,
            ArmorPacketObservation(3,vendor_matches={n:n=='Armor' for n,c in VENDORS}),cleanup)

    def snap(self,returned=True,stamp=203):
        return UpgradeSnapshot(200,armor_distance=9,armor_blocked=False,
                               source_helper_returned=returned,source_stamp_tick_dword=stamp)

    def samples(self):return {0:QueueSample(201,1),1:QueueSample(202,1)}

    def test_two_records_distinct_clocks_delays_and_counter_one(self):
        e=self.execution();p=e.step(self.snap(),armor_inputs=self.inputs(),armor_queue_samples=self.samples())
        self.assertTrue(p.complete);self.assertEqual(p.status,'local_armor_frame_complete')
        self.assertEqual([(len(r.payload),r.created_tick,r.delay_dword) for r in e.queue.records],[(20,201,0),(2,202,100)])
        self.assertEqual((e.runner.armor_attempts,e.runner.armor_stamp_qword),(1,203))
        payload=e.queue.records[0].payload
        self.assertEqual((int.from_bytes(payload[6:10],'little'),int.from_bytes(payload[11:15],'little')),(9,100))
        self.assertEqual((payload[15],payload[16:18],payload[18],payload[19]),(3,b'\x01\x00',0,0x12))

    def test_missing_second_sample_preserves_first_copy_without_duplicate(self):
        e=self.execution()
        p=e.step(self.snap(),armor_inputs=self.inputs(),armor_queue_samples={0:QueueSample(201,1)})
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_queue_observation')
        self.assertEqual((len(e.queue.records),len(p.prospective_queue.records),len(p.queue_decisions)),(0,1,1))
        self.assertEqual((e.runner.armor_attempts,e.runner.armor_stamp_qword),(0,0))
        p=e.step(self.snap(),armor_queue_samples={0:object(),1:QueueSample(202,1)})
        self.assertTrue(p.complete);self.assertEqual([r.record_id for r in e.queue.records],[1,2])

    def test_connection_gates_are_independent_for_both_calls(self):
        for a,b in ((0,0),(0,255),(255,0),(255,255)):
            with self.subTest(gates=(a,b)):
                e=self.execution();p=e.step(self.snap(),armor_inputs=self.inputs(),
                    armor_queue_samples={0:QueueSample(201,a),1:QueueSample(202,b)})
                self.assertTrue(p.complete);self.assertEqual(len(e.queue.records),int(bool(a))+int(bool(b)))
                self.assertEqual(e.runner.armor_attempts,1)
                if not a and b:self.assertEqual(e.queue.records[0].payload,b'\x6a\x02')

    def test_counter43_stop_waits_for_second_enqueue(self):
        e=self.execution(42)
        p=e.step(self.snap(),armor_inputs=self.inputs(),armor_queue_samples={0:QueueSample(201,1)})
        self.assertEqual((e.runner.armor_attempts,e.runner.state),(42,2))
        p=e.step(self.snap(),armor_queue_samples={1:QueueSample(202,1)})
        self.assertTrue(p.complete);self.assertEqual((e.runner.armor_attempts,e.runner.state),(43,0))
        self.assertEqual(e.runner.reason,'armor_attempt_limit')

    def test_helper_return_cannot_be_bypassed_by_completed_buffers(self):
        e=self.execution()
        p=e.step(self.snap(returned=False),armor_inputs=self.inputs(),armor_queue_samples=self.samples())
        self.assertEqual(p.status,'helper_did_not_return');self.assertEqual(e.queue.records,())
        p=e.step(self.snap())
        self.assertTrue(p.complete);self.assertEqual(len(e.queue.records),2)

    def test_caller_temporary_cleanup_is_a_separate_observation(self):
        e=self.execution()
        p=e.step(self.snap(),armor_inputs=self.inputs(cleanup=None),armor_queue_samples=self.samples())
        self.assertEqual(p.status,'needs_armor_caller_cleanup')
        self.assertEqual((e.runner.armor_attempts,len(e.queue.records)),(0,0))
        p=e.step(self.snap(returned=None),armor_inputs=ArmorExecutionInputs(caller_cleanup_returned=True))
        self.assertTrue(p.complete);self.assertEqual(e.runner.armor_attempts,1)

    def test_post_stamp_gap_does_not_reenqueue_either_record(self):
        e=self.execution()
        p=e.step(self.snap(stamp=None),armor_inputs=self.inputs(),armor_queue_samples=self.samples())
        self.assertEqual(p.status,'needs_stamp_tick');self.assertEqual(len(p.prospective_queue.records),2)
        p=e.step(self.snap(returned=None),armor_inputs=ArmorExecutionInputs(npc_dword=999))
        self.assertTrue(p.complete);self.assertEqual([r.created_tick for r in e.queue.records],[201,202])
        self.assertEqual(int.from_bytes(e.queue.records[0].payload[6:10],'little'),9)

    def test_completed_free_word_and_comparisons_are_retained(self):
        e=self.execution();i=self.inputs()
        first=replace(i,packet=ArmorPacketObservation(3,vendor_matches={'Sundries':False,'Armor':True}))
        p=e.step(self.snap(),armor_inputs=first)
        self.assertEqual(p.status,'needs_armor_packet')
        with self.assertRaises(ValueError):
            e.step(self.snap(),armor_inputs=ArmorExecutionInputs(packet=ArmorPacketObservation(4)))
        rest={n:False for n,c in VENDORS if n not in ('Sundries','Armor')}
        p=e.step(self.snap(),armor_inputs=ArmorExecutionInputs(packet=ArmorPacketObservation(vendor_matches=rest)),
                 armor_queue_samples=self.samples())
        self.assertTrue(p.complete);self.assertEqual(e.queue.records[0].payload[15],3)

    def test_helper_arguments_cannot_change_before_serialization_finishes(self):
        e=self.execution();e.step(self.snap(),armor_inputs=ArmorExecutionInputs(npc_dword=9))
        with self.assertRaises(ValueError):
            e.step(self.snap(),armor_inputs=ArmorExecutionInputs(npc_dword=10))
        self.assertEqual(e.queue.records,())

    def test_early_wait_and_full_gate_do_not_parse_future_inputs(self):
        e=self.execution()
        p=e.step(UpgradeSnapshot(199,armor_distance=9,armor_blocked=False),armor_inputs=object(),armor_queue_samples=object())
        self.assertEqual(p.status,'waiting');self.assertTrue(p.complete)
        p=e.step(UpgradeSnapshot(200,armor_distance=9,armor_blocked=True),armor_inputs=object(),armor_queue_samples=object())
        self.assertEqual(p.status,'stopped');self.assertEqual(e.queue.records,())
