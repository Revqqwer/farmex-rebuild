import unittest
from action_queue import QueueState,QueueSample
from operation_engine import UpgradeRunner,UpgradeSnapshot
from upgrade_parameter_frame import UpgradeParameterState
from upgrade_packets import UpgradePacketObservation
from upgrade_start_frame import UpgradeStartFrameObservation
from upgrade_worker import OwnedUpgradeWorker,UpgradeWorkerInput


class Sink:
    def __init__(self):self.events=[]
    def set_enabled(self,name,value):self.events.append((name,value))


class UpgradeWorkerTests(unittest.TestCase):
    def worker(self,parameters=None):
        r=UpgradeRunner(source_clock=True);r.state=1;r.queue=(11,);r.source_scroll_index=2
        r.source_start_ui=(False,True)
        self.shared=QueueState();self.sink=Sink();self.writes=[]
        def writer(value):self.writes.append(value);self.shared=value
        return OwnedUpgradeWorker(r,parameters or UpgradeParameterState(b'Scroll',1254,42,100),
                                  self.sink,lambda:self.shared,writer)

    def capture(self,now=100,**changes):
        values=dict(snapshot=UpgradeSnapshot(now,True,source_helper_returned=True,source_stamp_tick_dword=102),
                    packet=UpgradePacketObservation(13,21),queue_sample=QueueSample(101,1))
        values.update(changes);return UpgradeWorkerInput(**values)

    def test_unknown_interval_and_stamp_are_not_constructor_defaults(self):
        w=self.worker(UpgradeParameterState())
        self.assertEqual(w.step(self.capture(initial_stamp_qword=0)).status,'needs_interval')
        self.assertIsNone(w.runner.queue_stamp_qword)
        w.parameters.interval_dword=100
        self.assertEqual(w.step(self.capture()).status,'needs_initial_stamp')
        self.assertEqual((self.shared.records,w.runner.queue),((),(11,)))

    def test_late_cached_anvil_and_shared_queue_are_used(self):
        w=self.worker();w.parameters.anvil_dword=None
        p=w.step(self.capture(initial_stamp_qword=0))
        self.assertEqual(p.status,'needs_packet_observation')
        w.parameters.anvil_dword=99
        self.assertTrue(w.step(self.capture(packet=None)).complete)
        self.assertEqual(int.from_bytes(self.shared.records[0].payload[3:7],'little'),99)
        self.assertEqual((w.runner.queue,w.runner.queue_stamp_qword),((),102))

    def test_pending_attempt_does_not_resample_interval_or_seed_stamp(self):
        w=self.worker()
        w.step(self.capture(initial_stamp_qword=0,packet=UpgradePacketObservation(13)))
        w.parameters.interval_dword=None
        self.assertTrue(w.step(self.capture(packet=UpgradePacketObservation(target_item_dword=21),initial_stamp_qword=object())).complete)
        self.assertEqual(w.runner.interval_ms,100)

    def test_external_writer_conflict_holds_pending_attempt(self):
        w=self.worker()
        w.step(self.capture(initial_stamp_qword=0,packet=UpgradePacketObservation(13)))
        self.shared=QueueState(next_id=9)
        self.assertEqual(w.step(self.capture()).status,'queue_conflict')
        self.assertEqual(w.runner.queue,(11,))
        self.assertEqual(self.writes,[])

    def test_next_attempt_adopts_fresh_shared_queue(self):
        w=self.worker();self.shared=QueueState(next_id=9)
        self.assertTrue(w.step(self.capture(initial_stamp_qword=0)).complete)
        self.assertEqual(self.shared.records[0].record_id,9)

    def test_publish_failure_retries_without_rerunning_item_action(self):
        w=self.worker();bad=[True]
        def writer(value):
            if bad[0]:raise OSError('fixture writer gap')
            self.shared=value
        w.queue_writer=writer
        self.assertEqual(w.step(self.capture(initial_stamp_qword=0)).status,'needs_queue_publish')
        self.assertEqual(w.runner.queue,())
        bad[0]=False
        self.assertTrue(w.step(self.capture(packet=object())).complete)
        self.assertEqual(len(self.shared.records),1)

    def test_writer_failure_after_assignment_does_not_duplicate(self):
        w=self.worker()
        def writer(value):self.shared=value;raise OSError('fixture after assignment')
        w.queue_writer=writer
        self.assertEqual(w.step(self.capture(initial_stamp_qword=0)).status,'needs_queue_publish')
        self.assertTrue(w.step(self.capture(packet=object())).complete)
        self.assertEqual(len(self.shared.records),1)

    def test_writer_normal_return_without_assignment_is_not_success(self):
        w=self.worker();w.queue_writer=lambda value:None
        self.assertEqual(w.step(self.capture(initial_stamp_qword=0)).status,'needs_queue_publish')
        self.assertEqual(self.shared.records,())
        w.queue_writer=lambda value:setattr(self,'shared',value)
        self.assertTrue(w.step(self.capture(packet=object())).complete)
        self.assertEqual(len(self.shared.records),1)

    def test_publish_retry_never_overwrites_an_external_writer(self):
        w=self.worker();w.queue_writer=lambda value:None
        w.step(self.capture(initial_stamp_qword=0))
        self.shared=QueueState(next_id=99)
        self.assertEqual(w.step(self.capture()).status,'queue_conflict')
        self.assertEqual(self.shared.next_id,99)
        self.assertTrue(w.pending)

    def test_stop_waits_for_prefix_then_unguarded_helper_and_suffix(self):
        w=self.worker();w.runner.queue=();w.runner.queue_stamp_qword=0
        self.assertEqual(w.step(self.capture()).status,'needs_stop_prefix')
        self.assertEqual((w.runner.state,self.sink.events),(1,[]))
        p=w.step(self.capture(stop_prefix_returned=True))
        self.assertEqual((p.status,w.runner.state,self.sink.events),('needs_stop_effects',0,[('start',True)]))
        # Inner4f7af8 has no callback561f55 gate. Supplied gate0 is unreachable.
        obs=UpgradeStartFrameObservation(gate_byte=0,start_ui_returned=True,stop_ui_returned=True)
        self.assertEqual(w.step(self.capture(stop_observation=obs)).status,'needs_stop_suffix')
        self.assertEqual(self.sink.events,[('start',True),('stop',False)])
        self.assertTrue(w.step(self.capture(stop_suffix_returned=True)).complete)
        self.assertFalse(w.pending)
        self.assertEqual(w.runner.queue_stamp_qword,0)

    def test_scroll_missing_uses_same_stop_effect_frame(self):
        w=self.worker()
        p=w.step(UpgradeWorkerInput(UpgradeSnapshot(100,False,-1),initial_stamp_qword=0))
        self.assertEqual(p.status,'needs_stop_prefix')
        self.assertEqual((w.runner.state,w.runner.source_scroll_index,w.runner.queue),(1,-1,(11,)))

    def test_inactive_and_armor_do_not_consume_future_packet_data(self):
        w=self.worker(UpgradeParameterState());w.runner.state=0
        self.assertEqual(w.step(self.capture(packet=object(),initial_stamp_qword=object())).status,'inactive')
        w.runner.state=2
        self.assertEqual(w.step(self.capture(packet=object())).needed,('initial_armor_stamp_qword',))


if __name__=='__main__':unittest.main()
