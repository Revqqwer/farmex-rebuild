import unittest
from action_queue import QueueState,QueueSample
from operation_engine import UpgradeRunner,UpgradeSnapshot
from upgrade_worker import OwnedUpgradeWorker,UpgradeWorkerInput
from upgrade_parameter_frame import UpgradeParameterState
from armor_worker import ArmorWorkerObservation
from upgrade_armor import ArmorPacketObservation,VENDORS


class NoUiSink:
    def set_enabled(self,*args):raise AssertionError('Mode2 must not call Start/Stop UI helper')


class ArmorWorkerTests(unittest.TestCase):
    def worker(self,counter=0):
        r=UpgradeRunner(source_clock=True);r.state=2;r.queue=(11,);r.armor_attempts=counter
        r.source_start_ui=(True,False)
        r.armor_source_fields={0x54:100,0x50:30,0x4c:9,0x58:100,0x5c:18}
        self.shared=QueueState()
        return OwnedUpgradeWorker(r,UpgradeParameterState(),NoUiSink(),lambda:self.shared,
                                  lambda value:setattr(self,'shared',value))

    def capture(self,now=200,*,initial=0,**changes):
        values=dict(distance_ftol_dword=9,bag_flag_byte=0,preparation_returned=True,
            packet=ArmorPacketObservation(3,vendor_matches={n:n=='Armor' for n,c in VENDORS}),
            queue_samples={0:QueueSample(now+1,1),1:QueueSample(now+2,1)},caller_cleanup_returned=True)
        values.update(changes)
        return UpgradeWorkerInput(UpgradeSnapshot(now,source_helper_returned=True,source_stamp_tick_dword=now+3),
                                  initial_stamp_qword=initial,armor=ArmorWorkerObservation(**values))

    def test_waiting_and_unknown_initial_stamp_do_not_parse_future_packet(self):
        w=self.worker()
        self.assertEqual(w.step(self.capture(initial=None,packet=object())).needed,('initial_armor_stamp_qword',))
        self.assertEqual(w.step(self.capture(199,packet=object())).status,'waiting')
        self.assertEqual((self.shared.records,w.runner.armor_attempts,w.runner.state),((),0,2))

    def test_two_shared_records_use_independent_clocks_delays_and_cached_arguments(self):
        w=self.worker()
        self.assertEqual(w.step(self.capture()).status,'local_armor_frame_complete')
        self.assertEqual([(len(r.payload),r.created_tick,r.delay_dword) for r in self.shared.records],[(20,201,0),(2,202,100)])
        p=self.shared.records[0].payload
        self.assertEqual((int.from_bytes(p[6:10],'little'),int.from_bytes(p[11:15],'little'),p[19]),(9,100,18))
        self.assertEqual((w.runner.queue,w.runner.armor_attempts,w.runner.armor_stamp_qword),((11,),1,203))
        self.assertEqual((w.runner.armor_source_fields[0x40],w.runner.armor_source_fields[0x44]),(203,0))
        self.assertEqual(w.runner.source_start_ui,(True,False))

    def test_distance_is_frozen_while_fresh_bag_is_unknown(self):
        w=self.worker()
        self.assertEqual(w.step(self.capture(bag_flag_byte=None)).needed,('bag_flag_byte',))
        p=w.step(self.capture(999,distance_ftol_dword=10))
        self.assertEqual(p.status,'local_armor_frame_complete')
        self.assertEqual(w.runner.state,2)

    def test_signed_ftol_intmin_is_accepted_and_conflicting_distance_rejected(self):
        w=self.worker()
        self.assertTrue(w.step(self.capture(distance_ftol_dword=0x80000000)).complete)
        with self.assertRaises(ValueError):UpgradeSnapshot(200,armor_distance=9,armor_distance_ftol_dword=9)

    def test_missing_cached_coordinates_are_not_zero_and_reached_y_is_retained(self):
        w=self.worker();del w.runner.armor_source_fields[0x50]
        self.assertEqual(w.step(self.capture()).needed,('cached_field',0x50))
        w.runner.armor_source_fields[0x54]=999;w.runner.armor_source_fields[0x50]=30
        self.assertEqual(w.step(self.capture(distance_ftol_dword=None)).needed,('distance_ftol_dword',))
        self.assertEqual(w.armor_worker.cache[('field',0x54)],100)
        self.assertTrue(w.step(self.capture()).complete)
        self.assertEqual(w.armor_worker.result.status,'local_armor_frame_complete')

    def test_distance_stop_sets_mode0_before_notice_and_ignores_bag(self):
        w=self.worker()
        p=w.step(self.capture(distance_ftol_dword=10,bag_flag_byte=999,packet=object()))
        self.assertEqual((p.needed,w.runner.state),(('message_returned',),0))
        self.assertEqual(self.shared.records,())
        self.assertTrue(w.pending)
        p=w.step(self.capture(message_returned=True,message_cleanup0_returned=True,message_cleanup1_returned=True))
        self.assertEqual((p.status,w.runner.reason,w.pending),('stopped','armor_distance',False))

    def test_bag_stop_has_distinct_reason_and_unchanged_counter(self):
        w=self.worker(7)
        p=w.step(self.capture(bag_flag_byte=255,packet=object()))
        self.assertEqual((p.status,w.runner.state,w.runner.armor_attempts),('needs_armor_observation',0,7))
        w.step(self.capture(message_returned=True,message_cleanup0_returned=True,message_cleanup1_returned=True))
        self.assertEqual(w.runner.reason,'armor_bag')

    def test_limit_stop_mode0_occurs_after_notice_cleanup0_before_cleanup1(self):
        w=self.worker(42)
        p=w.step(self.capture())
        self.assertEqual((p.needed,w.runner.state,w.runner.armor_attempts,len(self.shared.records)),(('message_returned',),2,43,2))
        p=w.step(self.capture(message_returned=True))
        self.assertEqual((p.needed,w.runner.state),(('message_cleanup0_returned',),2))
        p=w.step(self.capture(message_cleanup0_returned=True))
        self.assertEqual((p.needed,w.runner.state),(('message_cleanup1_returned',),0))
        self.assertTrue(w.step(self.capture(message_cleanup1_returned=True)).complete)
        self.assertEqual((w.runner.reason,w.runner.armor_source_fields[0x10]),('armor_attempt_limit',0))

    def test_all_43_attempts_create_86_records_then_wait_for_terminal_returns(self):
        w=self.worker()
        for number in range(1,44):
            p=w.step(self.capture(200+(number-1)*203))
            self.assertEqual((w.runner.armor_attempts,len(self.shared.records)),(number,number*2))
            self.assertEqual(w.runner.state,2)
            self.assertEqual(p.status,'local_armor_frame_complete' if number<43 else 'needs_armor_observation')
        self.assertTrue(w.step(self.capture(message_returned=True,message_cleanup0_returned=True,message_cleanup1_returned=True)).complete)
        self.assertEqual(w.runner.state,0)

    def test_counter_increment_reads_fresh_value_after_helper_cleanup(self):
        w=self.worker()
        p=w.step(self.capture(queue_samples={0:QueueSample(201,1)}))
        self.assertEqual(p.status,'needs_queue_observation')
        w.runner.armor_attempts=42
        p=w.step(self.capture(queue_samples={1:QueueSample(202,1)}))
        self.assertEqual((p.needed,w.runner.armor_attempts,w.runner.state),(('message_returned',),43,2))

    def test_counter_unsigned_wrap_does_not_trigger_signed_limit(self):
        w=self.worker(0xffffffff)
        self.assertTrue(w.step(self.capture()).complete)
        self.assertEqual((w.runner.armor_attempts,w.runner.state),(0,2))

    def test_publish_failure_after_assignment_does_not_duplicate_pair(self):
        w=self.worker()
        def writer(value):self.shared=value;raise OSError('fixture after assignment')
        w.armor_worker.queue_writer=writer
        self.assertEqual(w.step(self.capture()).status,'needs_queue_publish')
        self.assertEqual((len(self.shared.records),w.runner.armor_attempts),(2,1))
        self.assertTrue(w.step(self.capture(packet=object())).complete)
        self.assertEqual((len(self.shared.records),w.runner.armor_attempts),(2,1))

    def test_external_writer_conflict_does_not_overwrite_or_repeat_partial_enqueue(self):
        w=self.worker()
        w.step(self.capture(queue_samples={0:QueueSample(201,1)}))
        self.shared=QueueState(next_id=99)
        self.assertEqual(w.step(self.capture()).status,'queue_conflict')
        self.assertEqual((self.shared.next_id,w.runner.armor_attempts),(99,0))

    def test_cached_arguments_freeze_before_preparation_returns(self):
        w=self.worker()
        self.assertEqual(w.step(self.capture(preparation_returned=None)).needed,('preparation_returned',))
        w.runner.armor_source_fields.update({0x4c:99,0x58:999,0x5c:3})
        self.assertTrue(w.step(self.capture()).complete)
        p=self.shared.records[0].payload
        self.assertEqual((int.from_bytes(p[6:10],'little'),int.from_bytes(p[11:15],'little'),p[19]),(9,100,18))


if __name__=='__main__':unittest.main()
