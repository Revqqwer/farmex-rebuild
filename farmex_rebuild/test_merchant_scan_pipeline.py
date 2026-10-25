import unittest
from action_queue import QueueState,QueueRecord
from direct_chat_packets import QueueAttempt
from merchant_scan import ScanSnapshot,ScanState
from merchant_scan_collection import MerchantCollectionState,MerchantProbe,MerchantRecord
from merchant_scan_pipeline import (
    MerchantScanPipeline,MerchantConsumeFrame,ScanConsumeObservation,
)


NORMALS=dict.fromkeys(('head_capture','target_write','packet_copy','erase_iterator',
    'erase_move','erase_tail','iterator_cleanup'),True)


def observation(**kw):
    args=dict(normal_enabled=True,buy_enabled=True,client_variant=2,
        normal_returns=NORMALS,attempt=QueueAttempt(1,65,True))
    args.update(kw)
    return ScanConsumeObservation(**args)


def merchant_state(buy=0,busy=False):
    return MerchantCollectionState((MerchantRecord(0x1234,100,buy),MerchantRecord(7,200,0)),(0x1234,7),busy)


def probes():return {i:MerchantProbe(0) for i in range(5001)}


class ConsumeFrameTests(unittest.TestCase):
    def test_target_and_copy_receipts_precede_any_enqueue(self):
        f=MerchantConsumeFrame(merchant_state())
        d=f.advance(observation(normal_returns={'head_capture':True}))
        self.assertEqual(d.needed,('normal','target_write'))
        self.assertEqual(d.queue,QueueState())
        self.assertEqual(d.state,merchant_state())
        d=f.advance(observation(normal_returns={'target_write':True}))
        self.assertEqual(d.needed,('normal','packet_copy'))
        self.assertEqual(d.queue.records,())

    def test_enqueue_partial_receipt_never_duplicates_and_busy_after_return(self):
        f=MerchantConsumeFrame(merchant_state())
        d=f.advance(observation(attempt=QueueAttempt(1,65,None)))
        self.assertEqual(len(d.queue.records),1)
        self.assertFalse(d.state.awaiting_merchant_reply)
        self.assertEqual(d.queue.records[0].payload,bytes.fromhex('68113412'))
        for _ in range(3):
            d=f.advance();self.assertEqual(len(d.queue.records),1)
        d=f.advance(ScanConsumeObservation(normal_returns=NORMALS,attempt=QueueAttempt(normal_returned=True)))
        self.assertTrue(d.complete)
        self.assertEqual(d.state.queue,merchant_state().queue[1:])
        self.assertTrue(d.state.awaiting_merchant_reply)
        self.assertEqual(len(d.queue.records),1)
        self.assertIs(f.advance(observation()),d)

    def test_busy_set_before_erase_and_pop_before_final_cleanup(self):
        f=MerchantConsumeFrame(merchant_state())
        n={k:v for k,v in NORMALS.items() if not k.startswith('erase') and k!='iterator_cleanup'}
        d=f.advance(observation(normal_returns=n))
        self.assertEqual(d.needed,('normal','erase_iterator'))
        self.assertTrue(d.state.awaiting_merchant_reply)
        self.assertEqual(len(d.state.queue),2)
        d=f.advance(observation(normal_returns={'erase_iterator':True,'erase_move':True,'erase_tail':True}))
        self.assertEqual(d.needed,('normal','iterator_cleanup'))
        self.assertEqual(len(d.state.queue),1)
        self.assertFalse(d.complete)
        d=f.advance(observation(normal_returns={'iterator_cleanup':True}))
        self.assertTrue(d.complete)

    def test_disconnected_enqueue_still_sets_busy_and_pops_after_normal_return(self):
        d=MerchantConsumeFrame(merchant_state(1)).advance(observation(attempt=QueueAttempt(0,None,True)))
        self.assertTrue(d.complete)
        self.assertEqual(d.queue.records,())
        self.assertTrue(d.state.awaiting_merchant_reply)
        self.assertEqual(d.plan.request_bytes,bytes.fromhex('68513412'))

    def test_disabled_kind_requires_only_erase_receipts(self):
        st=merchant_state(busy=True)
        n={k:v for k,v in NORMALS.items() if k not in ('target_write','packet_copy')}
        d=MerchantConsumeFrame(st).advance(observation(normal_enabled=False,client_variant=None,normal_returns=n))
        self.assertTrue(d.complete);self.assertIsNone(d.plan.request_bytes)
        self.assertTrue(d.state.awaiting_merchant_reply)
        self.assertEqual(d.queue.records,())

    def test_missing_variant_keeps_consumed_kind_choice(self):
        f=MerchantConsumeFrame(merchant_state())
        d=f.advance(observation(client_variant=None))
        self.assertEqual(d.needed,('value','client_variant'))
        d=f.advance(observation(normal_enabled=False,client_variant=1))
        self.assertTrue(d.complete)
        self.assertEqual(d.plan.target_pointer_offsets,(0x6ac,0x178))
        self.assertEqual(len(d.queue.records),1)

    def test_empty_and_source_bounds_are_terminal_without_effects(self):
        self.assertTrue(MerchantConsumeFrame().advance().complete)
        d=MerchantConsumeFrame(merchant_state()).advance(observation(queue_count_recheck=0))
        self.assertTrue(d.terminal);self.assertFalse(d.complete)
        self.assertEqual(d.status,'source_bounds_exception')
        self.assertEqual(d.state,merchant_state());self.assertEqual(d.queue.records,())


class PipelineTests(unittest.TestCase):
    def test_existing_shared_queue_record_preserved_and_new_id_fresh(self):
        q=QueueState((QueueRecord(4,b'owned existing request',3,0),),5)
        f=MerchantScanPipeline(collection=merchant_state(),queue=q)
        d=f.advance(ScanSnapshot(route_enabled=False,now_ms=65,post_consume_now_ms=66,
            consume_returned=True),consume=observation())
        self.assertTrue(d.complete)
        self.assertEqual(d.packet_queue.records[0],q.records[0])
        self.assertEqual(d.packet_queue.records[1].record_id,5)
        self.assertEqual(d.packet_queue.next_id,6)

    def test_movement_receipt_never_enters_collection_or_consume(self):
        f=MerchantScanPipeline()
        d=f.advance(ScanSnapshot(route_enabled=True,route_count=1,
            distance_returned=True,selected_point_distance=9))
        self.assertEqual(d.scheduler.pending_return.target,'004646b4')
        self.assertIsNone(d.child)
        d=f.advance(ScanSnapshot(move_returned=True))
        self.assertTrue(d.complete);self.assertIsNone(d.child)
        self.assertEqual(d.packet_queue.records,())

    def test_route_finish_requires_export_then_stop_separately(self):
        f=MerchantScanPipeline()
        s=ScanSnapshot(route_enabled=True,route_count=1,distance_returned=True,
            selected_point_distance=1,actor_raw_byte_554020=0,collect_returned=True,
            route_count_after_collect=1,save_on_finish_0e=True)
        d=f.advance(s,probes=probes())
        self.assertEqual(d.scheduler.pending_return.target,'004b99f8')
        d=f.advance(ScanSnapshot(export_returned=True))
        self.assertEqual(d.scheduler.pending_return.target,'004be6dc')
        self.assertTrue(d.scheduler.state.active)
        d=f.advance(ScanSnapshot(stop_returned=True))
        self.assertTrue(d.complete);self.assertEqual(d.status,'completed')

    def test_collection_cannot_be_bypassed_by_parent_receipt(self):
        f=MerchantScanPipeline()
        d=f.advance(ScanSnapshot(route_enabled=False,collect_returned=True))
        self.assertEqual(d.status,'needs_child_observation')
        self.assertFalse(d.terminal)
        self.assertEqual(d.collection.queue,())
        d=f.advance(ScanSnapshot(collect_returned=True),probes=probes())
        self.assertTrue(d.complete);self.assertEqual(d.status,'local_step')

    def test_complete_collection_still_requires_independent_parent_return(self):
        f=MerchantScanPipeline();p=probes()
        p[0]=MerchantProbe(123,1,1.0,2.0,0,9.5,42)
        d=f.advance(ScanSnapshot(route_enabled=False),probes=p,normal_enabled=True)
        self.assertEqual(d.status,'needs_parent_return')
        self.assertEqual(d.collection.visited_ids,(42,))
        d=f.advance(ScanSnapshot(collect_returned=True))
        self.assertTrue(d.complete)
        self.assertEqual(d.collection.queue,(MerchantRecord(42,123,0),))

    def test_route_zero_collection_increments_once_then_stop_receipt(self):
        f=MerchantScanPipeline()
        s=ScanSnapshot(route_enabled=True,route_count=1,distance_returned=True,
            selected_point_distance=1,actor_raw_byte_554020=0,collect_returned=True)
        d=f.advance(s,probes=probes())
        self.assertEqual(d.scheduler.state.route_index,1)
        self.assertFalse(d.terminal)
        d=f.advance(ScanSnapshot(route_count_after_collect=1,save_on_finish_0e=False))
        self.assertEqual(d.scheduler.pending_return.target,'004be6dc')
        for _ in range(3):self.assertEqual(f.advance().scheduler.state.route_index,1)
        d=f.advance(ScanSnapshot(stop_returned=True))
        self.assertTrue(d.complete);self.assertFalse(d.scheduler.state.active)

    def test_consume_timestamp_waits_for_child_parent_return_and_post_clock(self):
        f=MerchantScanPipeline(ScanState(last_scan_qword=10),merchant_state())
        d=f.advance(ScanSnapshot(route_enabled=False,now_ms=65,consume_returned=True))
        self.assertEqual(d.status,'needs_child_observation')
        self.assertEqual(d.scheduler.state.last_scan_qword,10)
        d=f.advance(consume=observation())
        self.assertEqual(d.status,'needs_parent_return')
        self.assertEqual(len(d.packet_queue.records),1)
        self.assertEqual(len(d.collection.queue),1)
        d=f.advance(ScanSnapshot(consume_returned=True))
        self.assertEqual(d.needed,'post_consume_GetTickCount')
        self.assertEqual(d.scheduler.state.last_scan_qword,10)
        d=f.advance(ScanSnapshot(post_consume_now_ms=88))
        self.assertTrue(d.complete)
        self.assertEqual(d.scheduler.state.last_scan_qword,88)
        self.assertEqual(len(d.packet_queue.records),1)

    def test_waiting_and_busy_do_not_enter_children(self):
        d=MerchantScanPipeline(collection=merchant_state()).advance(ScanSnapshot(route_enabled=False,now_ms=49))
        self.assertEqual(d.status,'waiting');self.assertIsNone(d.child)
        d=MerchantScanPipeline(collection=merchant_state(busy=True)).advance(ScanSnapshot(route_enabled=False))
        self.assertEqual(d.status,'busy');self.assertIsNone(d.child)

    def test_new_tick_uses_committed_own_busy_flag(self):
        f=MerchantScanPipeline(collection=merchant_state())
        d=f.advance(ScanSnapshot(route_enabled=False,now_ms=65,post_consume_now_ms=66,
            consume_returned=True),consume=observation())
        self.assertTrue(d.complete)
        next_tick=MerchantScanPipeline(d.scheduler.state,d.collection,d.packet_queue)
        next_d=next_tick.advance(ScanSnapshot(route_enabled=False))
        self.assertEqual(next_d.status,'busy')
        self.assertEqual(len(next_d.packet_queue.records),1)

    def test_conflicting_entry_state_and_eax_rejected(self):
        f=MerchantScanPipeline()
        with self.assertRaises(ValueError):f.advance(ScanSnapshot(pending_count=1))
        with self.assertRaises(ValueError):f.advance(ScanSnapshot(busy_0f=True))
        with self.assertRaises(ValueError):f.advance(ScanSnapshot(route_enabled=False,
            collect_return_4bf040=7),probes=probes())

    def test_child_bounds_failure_and_abort_preserve_prefix(self):
        f=MerchantScanPipeline(collection=merchant_state())
        d=f.advance(ScanSnapshot(route_enabled=False,now_ms=65),
            consume=observation(queue_count_recheck=0))
        self.assertTrue(d.terminal);self.assertFalse(d.complete)
        self.assertEqual(d.status,'child_failed')
        self.assertIs(f.advance(),d)
        self.assertEqual(d.collection,merchant_state())
        self.assertEqual(d.packet_queue.records,())
        f=MerchantScanPipeline(collection=merchant_state())
        f.advance(ScanSnapshot(route_enabled=False,now_ms=65),
            consume=observation(attempt=QueueAttempt(1,65,None)))
        d=f.abort('capture stopped')
        self.assertEqual(d.status,'aborted');self.assertFalse(d.complete)
        self.assertEqual(len(d.packet_queue.records),1)
        self.assertFalse(d.collection.awaiting_merchant_reply)
        self.assertTrue(f.advance().terminal)


if __name__=='__main__':unittest.main()
