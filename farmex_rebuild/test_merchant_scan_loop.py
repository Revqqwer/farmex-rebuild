import unittest
from dataclasses import replace
from action_queue import QueueState,enqueue
from direct_chat_packets import QueueAttempt
from merchant_scan import ScanSnapshot
from merchant_scan_control import ScanControlState,MerchantScanOptions
from merchant_scan_collection import MerchantRecord,MerchantProbe
from merchant_scan_pipeline import ScanConsumeObservation
from merchant_scan_loop import OwnedMerchantScanLoop,ScanLoopInput


NORMALS=dict.fromkeys(('head_capture','target_write','packet_copy','erase_iterator',
    'erase_move','erase_tail','iterator_cleanup'),True)


def control(**kw):
    args=dict(active_byte=1,options=MerchantScanOptions(sell_byte=1),
        vector_58=(MerchantRecord(42,123,0),),vector_78=(42,))
    args.update(kw);return ScanControlState(**args)


def captures(*,normal=True,post=None,attempt=None):
    return ScanLoopInput(ScanSnapshot(consume_returned=normal,post_consume_now_ms=post),
        consume=ScanConsumeObservation(True,False,2,normal_returns=NORMALS,
            attempt=QueueAttempt(1,63,True) if attempt is None else attempt))


def no_clock():raise AssertionError('Unreached clock was read')


class ScanLoopTests(unittest.TestCase):
    def test_pre_and_post_clocks_are_distinct_reached_reads(self):
        f=OwnedMerchantScanLoop();c=control();f.restart(c)
        ticks=iter((60,89));calls=[]
        def clock():
            v=next(ticks);calls.append(v);return v
        d=f.advance(c,QueueState(),captures(),clock=clock)
        self.assertEqual(calls,[60,89]);self.assertEqual(f.state.last_scan_qword,89)
        self.assertEqual(d.status,'local_step');self.assertIsNone(f.pipeline)
        self.assertTrue(d.control.busy_byte_0f);self.assertEqual(d.control.vector_58,())
        self.assertEqual(d.published_record_ids,(1,));self.assertEqual(len(d.queue.records),1)

    def test_waiting_clock_does_not_start_child_or_read_post(self):
        f=OwnedMerchantScanLoop();c=control();f.restart(c)
        d=f.advance(c,QueueState(),clock=lambda:49)
        self.assertEqual(d.status,'waiting');self.assertEqual(d.queue.records,())
        self.assertEqual(f.state.last_scan_qword,0)
        self.assertIsNone(f.pipeline)

    def test_busy_and_no_data_do_not_call_clock(self):
        f=OwnedMerchantScanLoop();c=control(busy_byte_0f=1);f.restart(c)
        d=f.advance(c,QueueState(),clock=no_clock)
        self.assertEqual(d.status,'busy');self.assertTrue(d.active)
        c=control(vector_58=());f.restart(c)
        d=f.advance(c,QueueState(),clock=no_clock)
        self.assertEqual(d.status,'needs_child_observation')
        self.assertEqual(d.control.vector_78,(42,));self.assertIsNotNone(f.pipeline)

    def test_missing_parent_return_retains_one_child_across_ticks(self):
        f=OwnedMerchantScanLoop();c=control();f.restart(c)
        d=f.advance(c,QueueState(),captures(normal=None),clock=lambda:60)
        pipeline=f.pipeline
        self.assertEqual(d.status,'needs_parent_return')
        self.assertEqual(len(d.queue.records),1)
        d2=f.advance(d.control,d.queue,clock=no_clock)
        self.assertIs(f.pipeline,pipeline)
        self.assertEqual(d2.published_record_ids,());self.assertEqual(d2.queue,d.queue)
        d3=f.advance(d2.control,d2.queue,ScanLoopInput(ScanSnapshot(consume_returned=True)),clock=lambda:90)
        self.assertEqual(d3.status,'local_step');self.assertEqual(len(d3.queue.records),1)
        self.assertEqual(f.state.last_scan_qword,90)

    def test_interleaved_shared_append_is_preserved_with_fresh_ids(self):
        f=OwnedMerchantScanLoop();c=control();f.restart(c)
        d=f.advance(c,QueueState(),clock=lambda:60)
        self.assertEqual(d.status,'needs_child_observation')
        shared=enqueue(d.queue,b'other feature',13,0,1,61).state
        d=f.advance(d.control,shared,captures(post=80),clock=no_clock)
        self.assertEqual([r.record_id for r in d.queue.records],[1,2])
        self.assertEqual(d.queue.records[0].payload,b'other feature')
        self.assertEqual(d.queue.records[1].payload,bytes.fromhex('68112a00'))
        self.assertEqual(d.published_record_ids,(2,));self.assertEqual(d.queue.next_id,3)

    def test_already_published_partial_enqueue_not_republished_after_other_writer(self):
        f=OwnedMerchantScanLoop();c=control();f.restart(c)
        d=f.advance(c,QueueState(),captures(attempt=QueueAttempt(1,63,None)),clock=lambda:60)
        self.assertEqual(len(d.queue.records),1)
        shared=enqueue(d.queue,b'pm',2,0,1,64).state
        d2=f.advance(d.control,shared,captures(attempt=QueueAttempt(normal_returned=True),post=80),clock=no_clock)
        self.assertEqual(len(d2.queue.records),2);self.assertEqual(d2.published_record_ids,())
        self.assertEqual(d2.queue,shared)

    def test_post_clock_failure_publishes_prefix_and_resume_does_not_duplicate(self):
        f=OwnedMerchantScanLoop();c=control();f.restart(c)
        calls=[]
        def clock():
            calls.append(1)
            if len(calls)==1:return 60
            raise OSError('clock unavailable')
        d=f.advance(c,QueueState(),captures(),clock=clock)
        self.assertEqual(d.status,'own_clock_error');self.assertIn('clock unavailable',d.error)
        self.assertTrue(d.control.busy_byte_0f);self.assertEqual(len(d.queue.records),1)
        d2=f.advance(d.control,d.queue,clock=lambda:95)
        self.assertEqual(d2.status,'local_step');self.assertEqual(d2.queue,d.queue)
        self.assertEqual(f.state.last_scan_qword,95)

    def test_collection_commits_to_control_without_fabricating_normal_receipt(self):
        f=OwnedMerchantScanLoop();c=control(vector_58=(),vector_78=());f.restart(c)
        p={i:MerchantProbe(0) for i in range(5001)}
        p[5000]=MerchantProbe(444,1,3,4,0,9.5,17)
        d=f.advance(c,QueueState(),ScanLoopInput(probes=p),clock=no_clock)
        self.assertEqual(d.status,'needs_parent_return');self.assertEqual(d.control.vector_78,(17,))
        self.assertEqual(d.control.vector_58,(MerchantRecord(17,444,0),))
        d=f.advance(d.control,d.queue,ScanLoopInput(ScanSnapshot(collect_returned=True)),clock=no_clock)
        self.assertEqual(d.status,'local_step');self.assertIsNone(f.pipeline)

    def test_route_completion_keeps_explicit_stop_receipt(self):
        f=OwnedMerchantScanLoop()
        c=control(options=MerchantScanOptions(sell_byte=1,route_byte=1),vector_58=(),
            route_points=((1,2),))
        f.restart(c);p={i:MerchantProbe(0) for i in range(5001)}
        o=ScanLoopInput(ScanSnapshot(distance_returned=True,selected_point_distance=0,
            actor_raw_byte_554020=0,collect_returned=True),p)
        d=f.advance(c,QueueState(),o,clock=no_clock)
        self.assertEqual(d.control.route_index_dword,1);self.assertTrue(d.active)
        self.assertEqual(d.invocation.scheduler.pending_return.target,'004be6dc')
        d=f.advance(d.control,d.queue,ScanLoopInput(ScanSnapshot(stop_returned=True)),clock=no_clock)
        self.assertEqual(d.status,'completed');self.assertFalse(d.active)

    def test_stop_invalidates_generation_and_preserves_clock_and_queue_prefix(self):
        f=OwnedMerchantScanLoop();c=control();f.restart(c)
        d=f.advance(c,QueueState(),captures(),clock=iter((60,90)).__next__)
        old=f.generation;f.stop();self.assertGreater(f.generation,old)
        self.assertEqual(f.state.last_scan_qword,90);self.assertFalse(f.state.active)
        self.assertFalse(f.collection.awaiting_merchant_reply)
        f.restart(control(vector_58=()))
        self.assertEqual(f.state.last_scan_qword,90)
        d2=f.advance(control(vector_58=()),d.queue,clock=no_clock)
        self.assertEqual(d2.queue,d.queue)

    def test_bounds_failure_stops_own_loop_without_completing_source(self):
        f=OwnedMerchantScanLoop();c=control(options=MerchantScanOptions(route_byte=1));f.restart(c)
        d=f.advance(c,QueueState(),clock=no_clock)
        self.assertEqual(d.status,'source_bounds_exception');self.assertFalse(d.active)
        self.assertFalse(d.invocation.complete)

    def test_own_control_conflict_does_not_consume_provider_data(self):
        f=OwnedMerchantScanLoop();c=control();f.restart(c)
        with self.assertRaises(ValueError):f.advance(c,QueueState(),
            ScanLoopInput(ScanSnapshot(route_enabled=True)),clock=no_clock)
        self.assertIsNone(f.pipeline.last)
        self.assertEqual(f.collection.queue,c.vector_58)


if __name__=='__main__':unittest.main()
