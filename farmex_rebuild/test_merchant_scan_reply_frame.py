import struct
import unittest
from action_queue import QueueState,enqueue
from direct_chat_packets import QueueAttempt
from merchant_reply import MerchantReplyState
from merchant_scan import ScanSnapshot
from merchant_scan_collection import MerchantProbe
from merchant_scan_control import ScanControlState,MerchantScanOptions
from merchant_scan_results import MerchantActorMetadata as Actor,MerchantItemMetadata as Item
from merchant_scan_reply_frame import MerchantScanReplyFrame,ScanReplyObservation
from merchant_scan_loop import OwnedMerchantScanLoop,ScanLoopInput


def packet(slots=()):
    return b'\x68\x23\x01\x34\x12'+b''.join(struct.pack('<IHHI',*s) for s in slots)+b'\0'*12*(12-len(slots))


def obs(**kw):
    args=dict(parse_returned=True,finish_setup_returned=True,finish_returned=True,
        attempt=QueueAttempt(1,123,True))
    args.update(kw);return ScanReplyObservation(**args)


def no_clock():raise AssertionError('Reply processing must not read scan clocks')


class ReplyFrameTests(unittest.TestCase):
    def test_direct_scan_responses_clear_busy_without_finish_or_actor(self):
        for subtype in (0x27,2,0x11):
            initial=MerchantReplyState(scan_pending_byte=255,close_pending_byte=1)
            f=MerchantScanReplyFrame(bytes((0x68,subtype)),initial)
            p=f.advance()
            self.assertTrue(p.complete);self.assertEqual(p.state.scan_pending_byte,0)
            self.assertEqual(p.state.close_pending_byte,1)
            self.assertEqual(p.queue.records,());self.assertIsNone(p.finish_payload)
            self.assertEqual(p.dispatcher.return_al,0)
            self.assertIs(f.advance(),p)

    def test_negative_status_skips_parser_but_finishes_correct_mode(self):
        for subtype,expected in ((5,b'\x68\x08'),(0x23,b'\x68\x27')):
            p=MerchantScanReplyFrame(bytes((0x68,subtype,0)),MerchantReplyState(scan_pending_byte=1)).advance(obs())
            self.assertTrue(p.complete);self.assertIsNone(p.parser)
            self.assertEqual(p.queue.records[0].payload,expected)
            self.assertEqual(p.queue.records[0].delay_dword,0)
            self.assertEqual(p.state.scan_pending_byte,0)

    def test_metadata_projection_does_not_supply_parser_normal_return(self):
        f=MerchantScanReplyFrame(packet(((1,2,3,4),)),MerchantReplyState(scan_pending_byte=1))
        p=f.advance(obs(actor=Actor('seller',5,6),items={0:Item('Bow',5,5,7)},parse_returned=None))
        self.assertEqual(p.status,'needs_parser_return');self.assertEqual(len(p.records),1)
        self.assertEqual(p.state.scan_pending_byte,1);self.assertEqual(p.queue.records,())
        p=f.advance(obs())
        self.assertTrue(p.complete);self.assertEqual(p.records[0].display.item_name,'Bow(+7)')

    def test_missing_actor_and_item_preserve_completed_prefix_and_consumed_values(self):
        f=MerchantScanReplyFrame(packet(((1,2,3,4),(5,6,7,8))),MerchantReplyState(scan_pending_byte=1))
        p=f.advance(obs());self.assertEqual(p.status,'needs_metadata')
        p=f.advance(obs(actor=Actor('first',1,2),items={0:Item('A',0,0,0)}))
        self.assertEqual(p.status,'needs_metadata');self.assertEqual(len(p.records),1)
        p=f.advance(obs(actor=Actor('changed',7,8),items={0:Item('changed',0,0,0),1:Item('B',0,0,0)}))
        self.assertTrue(p.complete)
        self.assertEqual([r.display.item_name for r in p.records],['A','B'])
        self.assertEqual([r.display.seller for r in p.records],['first','first'])

    def test_actor_is_consumed_even_when_first_item_is_missing(self):
        f=MerchantScanReplyFrame(packet(((1,2,3,4),)),MerchantReplyState(scan_pending_byte=1))
        f.advance(obs(actor=Actor('first',1,2)))
        p=f.advance(obs(actor=Actor('changed',3,4),items={0:Item('A',0,0,0)}))
        self.assertEqual(p.records[0].display.seller,'first')

    def test_finish_setup_enqueue_and_parent_returns_remain_separate(self):
        f=MerchantScanReplyFrame(b'\x68\x05\x00',MerchantReplyState(scan_pending_byte=1))
        p=f.advance();self.assertEqual(p.status,'needs_finish_setup')
        p=f.advance(obs(attempt=QueueAttempt(1,123,None)))
        self.assertEqual(p.status,'needs_finish_enqueue');self.assertEqual(len(p.queue.records),1)
        for _ in range(3):self.assertEqual(len(f.advance().queue.records),1)
        p=f.advance(obs(attempt=QueueAttempt(normal_returned=True),finish_returned=None))
        self.assertEqual(p.status,'needs_finish_return');self.assertEqual(p.state.scan_pending_byte,1)
        p=f.advance(obs());self.assertTrue(p.complete)
        self.assertEqual(len(p.queue.records),1);self.assertEqual(p.state.scan_pending_byte,0)

    def test_disconnected_finish_return_still_clears_busy_without_delivery(self):
        p=MerchantScanReplyFrame(b'\x68\x23\x00',MerchantReplyState(scan_pending_byte=1)).advance(
            obs(attempt=QueueAttempt(0,None,True)))
        self.assertTrue(p.complete);self.assertEqual(p.queue.records,())
        self.assertEqual(p.state.scan_pending_byte,0);self.assertFalse(p.delivery_verified)

    def test_parser_length_rejection_still_requires_independent_parse_return(self):
        f=MerchantScanReplyFrame(b'\x68\x23\x01',MerchantReplyState(scan_pending_byte=1))
        p=f.advance();self.assertEqual(p.status,'needs_parser_return')
        self.assertEqual(p.parser.status,'source_length_rejected')
        p=f.advance(obs());self.assertTrue(p.complete);self.assertEqual(p.records,())

    def test_truncation_and_outside_scope_never_clear_busy(self):
        initial=MerchantReplyState(scan_pending_byte=1)
        for data in (b'',b'\x68',b'\x68\x05'):
            p=MerchantScanReplyFrame(data,initial).advance(obs())
            self.assertTrue(p.terminal);self.assertFalse(p.complete);self.assertEqual(p.state,initial)
        for data in (b'\x67',b'\x68\x28'):
            p=MerchantScanReplyFrame(data,initial).advance(obs())
            self.assertEqual(p.status,'outside_active_scan_scope');self.assertEqual(p.state,initial)

    def test_abort_preserves_finish_queue_without_clearing_busy(self):
        f=MerchantScanReplyFrame(b'\x68\x23\x00',MerchantReplyState(scan_pending_byte=1))
        f.advance(obs(attempt=QueueAttempt(1,123,None)))
        p=f.abort('stop');self.assertEqual(len(p.queue.records),1)
        self.assertEqual(p.state.scan_pending_byte,1);self.assertFalse(p.complete)
        self.assertIs(f.advance(obs()),p)


class ReplyLoopTests(unittest.TestCase):
    def make_loop(self,busy=1):
        c=ScanControlState(active_byte=1,busy_byte_0f=busy,options=MerchantScanOptions(sell_byte=1))
        f=OwnedMerchantScanLoop();f.restart(c);return f,c

    def test_reply_context_fifo_and_busy_clear_allow_next_scan_tick(self):
        f,c=self.make_loop();first=f.enqueue_reply(b'\x68\x23\x00');second=f.enqueue_reply(b'\x68\x11')
        self.assertEqual(f.context(c,QueueState()).reply.ticket,first)
        p=f.advance(c,QueueState(),ScanLoopInput(reply=obs()),clock=no_clock)
        self.assertEqual(p.status,'reply_scan_consumed');self.assertEqual(p.control.busy_byte_0f,0)
        self.assertEqual(f.context(p.control,p.queue).reply.ticket,second)
        q=f.advance(p.control,p.queue,clock=no_clock)
        self.assertEqual(q.status,'reply_scan_consumed');self.assertIsNone(f.context(q.control,q.queue).reply)
        q=f.advance(q.control,q.queue,clock=no_clock)
        self.assertEqual(q.status,'needs_child_observation')

    def test_partial_records_and_finish_enqueue_are_published_once_with_other_writer(self):
        f,c=self.make_loop();f.enqueue_reply(packet(((1,2,3,4),(5,6,7,8))))
        p=f.advance(c,QueueState(),ScanLoopInput(reply=obs(actor=Actor('seller',1,2),items={0:Item('A',0,0,0)})),clock=no_clock)
        self.assertEqual(len(p.added_records),1);self.assertEqual(len(p.control.result_records),1)
        p=f.advance(p.control,p.queue,clock=no_clock)
        self.assertEqual(p.added_records,());self.assertEqual(len(p.control.result_records),1)
        shared=enqueue(p.queue,b'other',5,0,1,5).state
        p=f.advance(p.control,shared,ScanLoopInput(reply=obs(items={1:Item('B',0,0,0)},finish_returned=None)),clock=no_clock)
        self.assertEqual(len(p.added_records),1);self.assertEqual(len(p.control.result_records),2)
        self.assertEqual([r.record_id for r in p.queue.records],[1,2])
        self.assertEqual(p.queue.records[0].payload,b'other');self.assertEqual(p.control.busy_byte_0f,1)
        q=f.advance(p.control,p.queue,ScanLoopInput(reply=obs()),clock=no_clock)
        self.assertEqual(q.status,'reply_scan_consumed');self.assertEqual(q.added_records,())
        self.assertEqual(q.queue,p.queue);self.assertEqual(q.control.busy_byte_0f,0)

    def test_reply_waits_for_inflight_scheduler_invocation(self):
        f,c=self.make_loop(busy=0)
        p=f.advance(c,QueueState(),clock=no_clock)
        pipeline=f.pipeline;f.enqueue_reply(b'\x68\x11')
        context=f.context(p.control,p.queue)
        self.assertIsNone(context.reply);self.assertIsNotNone(context.pending)
        empty={i:MerchantProbe(0) for i in range(5001)}
        p=f.advance(p.control,p.queue,ScanLoopInput(ScanSnapshot(collect_returned=True),empty),clock=no_clock)
        self.assertEqual(p.status,'local_step');self.assertIsNone(f.pipeline)
        self.assertIsNotNone(f.context(p.control,p.queue).reply)
        q=f.advance(p.control,p.queue,clock=no_clock)
        self.assertEqual(q.status,'reply_scan_consumed')

    def test_stop_restart_invalidates_queued_reply_and_old_ticket(self):
        f,c=self.make_loop();ticket=f.enqueue_reply(b'\x68\x23\x00')
        f.stop();self.assertIsNone(f.enqueue_reply(b'\x68\x11'))
        f.restart(c);self.assertIsNone(f.context(c,QueueState()).reply)
        self.assertNotEqual(ticket,f.enqueue_reply(b'\x68\x11'))

    def test_malformed_reply_does_not_discard_next_valid_reply(self):
        f,c=self.make_loop();f.enqueue_reply(b'\x68');f.enqueue_reply(b'\x68\x11')
        p=f.advance(c,QueueState(),clock=no_clock)
        self.assertEqual(p.status,'reply_truncated');self.assertEqual(p.control.busy_byte_0f,1)
        q=f.advance(p.control,p.queue,clock=no_clock)
        self.assertEqual(q.control.busy_byte_0f,0);self.assertEqual(q.status,'reply_scan_consumed')


if __name__=='__main__':unittest.main()
