import unittest
from operation_engine import UpgradeRunner,UpgradeRow,UpgradeSnapshot
from upgrade_packets import UpgradePacketObservation
from upgrade_execution import UpgradeExecution
from action_queue import QueueSample,QueueState


class UpgradeExecutionTests(unittest.TestCase):
    def execution(self):
        runner=UpgradeRunner(100,42,source_clock=True)
        runner.start((UpgradeRow(11),UpgradeRow(22)),initial_stamp_qword=0)
        runner.source_scroll_index=2
        return UpgradeExecution(runner)

    def snap(self,now=100,returned=True,stamp=102):
        return UpgradeSnapshot(now,True,source_helper_returned=returned,source_stamp_tick_dword=stamp)

    def packet(self):return UpgradePacketObservation(13,21)

    def test_completed_frame_commits_one_buffer_and_one_source_row(self):
        e=self.execution()
        p=e.step(self.snap(),self.packet(),QueueSample(101,255))
        self.assertTrue(p.complete);self.assertFalse(p.independently_verified)
        self.assertEqual((e.runner.queue,e.runner.queue_stamp_qword,len(e.queue.records)),((22,),102,1))
        record=e.queue.records[0]
        self.assertEqual((record.created_tick,record.delay_dword,len(record.payload)),(101,0,57))
        self.assertEqual((record.payload[11],record.payload[16]),(11,2))

    def test_marker_cannot_bypass_missing_packet_observations(self):
        e=self.execution()
        p=e.step(self.snap(),queue_sample=QueueSample(101,1))
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_packet_observation')
        self.assertEqual((e.runner.queue,e.runner.queue_stamp_qword,e.queue.records),((11,22),0,()))

    def test_completed_first_getter_is_retained_until_second_is_known(self):
        e=self.execution()
        p=e.step(self.snap(),UpgradePacketObservation(scroll_item_dword=13))
        self.assertEqual(p.packet.observed_items,(('scroll',13),))
        p=e.step(self.snap(),UpgradePacketObservation(target_item_dword=21),QueueSample(101,1))
        self.assertTrue(p.complete)
        self.assertEqual(int.from_bytes(e.queue.records[0].payload[12:16],'little'),13)

    def test_changed_completed_getter_is_rejected(self):
        e=self.execution();e.step(self.snap(),UpgradePacketObservation(scroll_item_dword=13))
        with self.assertRaises(ValueError):
            e.step(self.snap(),UpgradePacketObservation(99,21),QueueSample(101,1))
        self.assertEqual(e.queue.records,())

    def test_post_stamp_gap_has_one_prospective_copy_and_no_duplicate(self):
        e=self.execution()
        p=e.step(self.snap(stamp=None),self.packet(),QueueSample(101,1))
        self.assertEqual(p.status,'needs_stamp_tick')
        self.assertEqual((len(e.queue.records),len(p.prospective_queue.records),e.runner.queue),(0,1,(11,22)))
        p=e.step(UpgradeSnapshot(9999,False,source_stamp_tick_dword=102))
        self.assertTrue(p.complete);self.assertEqual(len(e.queue.records),1)
        self.assertEqual(e.queue.records[0].created_tick,101)
        self.assertEqual(e.runner.queue,(22,))

    def test_closed_enqueue_gate_can_complete_without_a_record(self):
        e=self.execution()
        p=e.step(self.snap(),self.packet(),QueueSample(connection_gate=0))
        self.assertTrue(p.complete);self.assertEqual(p.queue_decision.status,'not_enqueued')
        self.assertEqual((e.queue.records,e.runner.queue,e.runner.queue_stamp_qword),((),(22,),102))

    def test_reached_enqueue_gate_cannot_change_while_tick_is_missing(self):
        e=self.execution()
        p=e.step(self.snap(),self.packet(),QueueSample(connection_gate=1))
        self.assertEqual(p.status,'needs_queue_observation')
        with self.assertRaises(ValueError):e.step(self.snap(),queue_sample=QueueSample(101,0))
        p=e.step(self.snap(),queue_sample=QueueSample(tick=101))
        self.assertTrue(p.complete);self.assertEqual(len(e.queue.records),1)

    def test_non_normal_return_keeps_local_copy_prospective(self):
        e=self.execution()
        p=e.step(self.snap(returned=False),self.packet(),QueueSample(101,1))
        self.assertEqual(p.status,'helper_did_not_return')
        self.assertEqual((e.runner.queue,e.queue.records),((11,22),()))
        self.assertEqual(len(p.prospective_queue.records),1)

    def test_early_clock_gap_and_wait_do_not_parse_future_inputs(self):
        e=self.execution()
        p=e.step(self.snap(99),object(),object())
        self.assertTrue(p.complete);self.assertEqual(p.status,'waiting')
        e.runner.queue_stamp_qword=None
        p=e.step(self.snap(),object(),object())
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_initial_stamp')

    def test_inflight_queue_change_rejected_and_next_attempt_gets_fresh_id(self):
        e=self.execution()
        e.step(self.snap(stamp=None),self.packet(),QueueSample(101,1))
        e.queue=QueueState(next_id=2)
        with self.assertRaises(ValueError):e.step(self.snap())
        e=self.execution()
        e.step(self.snap(),self.packet(),QueueSample(101,1))
        p=e.step(self.snap(202,stamp=204),UpgradePacketObservation(31,41),QueueSample(203,1))
        self.assertTrue(p.complete)
        self.assertEqual([r.record_id for r in e.queue.records],[1,2])
        self.assertEqual(e.queue.records[1].payload[11],22)
