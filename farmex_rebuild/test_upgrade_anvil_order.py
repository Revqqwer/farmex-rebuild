import unittest
from operation_engine import UpgradeRunner,UpgradeRow,UpgradeSnapshot
from upgrade_execution import UpgradeExecution
from upgrade_packets import UpgradePacketObservation
from action_queue import QueueSample


class UpgradeAnvilOrderTests(unittest.TestCase):
    def execution(self,reader=None):
        r=UpgradeRunner(100,42,source_clock=True)
        r.start((UpgradeRow(11),UpgradeRow(22)),initial_stamp_qword=0)
        r.source_scroll_index=2
        return UpgradeExecution(r,anvil_reader=reader)

    def snapshot(self,now=100,stamp=102):
        return UpgradeSnapshot(now,True,source_helper_returned=True,source_stamp_tick_dword=stamp)

    def test_default_runner_anvil_is_read_after_second_getter(self):
        e=self.execution()
        e.step(self.snapshot(),UpgradePacketObservation(scroll_item_dword=13))
        e.runner.anvil_id=99
        p=e.step(self.snapshot(),UpgradePacketObservation(target_item_dword=21),QueueSample(101,1))
        self.assertTrue(p.complete)
        self.assertEqual(int.from_bytes(e.queue.records[0].payload[3:7],'little'),99)

    def test_reader_unreached_for_wait_or_missing_getters(self):
        calls=[];e=self.execution(lambda:calls.append('read') or 5)
        e.step(self.snapshot(99),object(),object())
        e.step(self.snapshot(),UpgradePacketObservation())
        e.step(self.snapshot(),UpgradePacketObservation(scroll_item_dword=13))
        self.assertEqual(calls,[])
        e.step(self.snapshot(),UpgradePacketObservation(target_item_dword=21),QueueSample(101,1))
        self.assertEqual(calls,['read'])

    def test_unknown_cached_anvil_never_uses_constructor_default(self):
        value=[None];calls=[]
        def reader():calls.append('read');return value[0]
        e=self.execution(reader)
        p=e.step(self.snapshot(),UpgradePacketObservation(13,21),QueueSample(101,1))
        self.assertEqual((p.status,p.missing),('needs_packet_observation','anvil DWORD at object+8'))
        self.assertEqual((e.queue.records,e.runner.queue),((),(11,22)))
        value[0]=0
        p=e.step(self.snapshot(),queue_sample=QueueSample(101,1))
        self.assertTrue(p.complete)
        self.assertEqual(int.from_bytes(e.queue.records[0].payload[3:7],'little'),0)
        self.assertEqual(calls,['read','read'])

    def test_copied_anvil_is_frozen_across_queue_and_stamp_gaps(self):
        value=[7];calls=[]
        e=self.execution(lambda:calls.append(value[0]) or value[0])
        p=e.step(self.snapshot(stamp=None),UpgradePacketObservation(13,21),QueueSample(connection_gate=1))
        self.assertEqual(p.status,'needs_queue_observation')
        value[0]=8
        p=e.step(self.snapshot(stamp=None),queue_sample=QueueSample(tick=101))
        self.assertEqual(p.status,'needs_stamp_tick')
        value[0]=9
        self.assertTrue(e.step(self.snapshot()).complete)
        self.assertEqual(int.from_bytes(e.queue.records[0].payload[3:7],'little'),7)
        self.assertEqual(calls,[7])

    def test_next_attempt_gets_fresh_anvil(self):
        value=[7];e=self.execution(lambda:value[0])
        e.step(self.snapshot(),UpgradePacketObservation(13,21),QueueSample(101,1))
        value[0]=9
        e.step(self.snapshot(202,204),UpgradePacketObservation(31,41),QueueSample(203,1))
        self.assertEqual([int.from_bytes(r.payload[3:7],'little') for r in e.queue.records],[7,9])

    def test_reader_error_preserves_completed_getters_for_retry(self):
        bad=[True]
        def reader():
            if bad[0]:raise OSError('fixture gap')
            return 7
        e=self.execution(reader)
        with self.assertRaises(OSError):e.step(self.snapshot(),UpgradePacketObservation(13,21))
        self.assertEqual(e._frozen,{'scroll':13,'target':21})
        self.assertEqual(e.queue.records,())
        bad[0]=False
        self.assertTrue(e.step(self.snapshot(),queue_sample=QueueSample(101,1)).complete)

    def test_invalid_reader_value_does_not_commit_packet(self):
        for value in (True,-1,0x100000000,'42'):
            with self.subTest(value=value):
                e=self.execution(lambda:value)
                with self.assertRaises(ValueError):e.step(self.snapshot(),UpgradePacketObservation(13,21))
                self.assertEqual(e.queue.records,())
                self.assertEqual(e.runner.queue,(11,22))


if __name__=='__main__':unittest.main()
