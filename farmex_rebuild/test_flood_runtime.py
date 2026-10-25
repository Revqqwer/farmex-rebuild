import unittest
from flood_runtime import *

class Clock:
    def __init__(self,*ticks):self.values=iter(ticks);self.calls=0
    def __call__(self):self.calls+=1;return next(self.values)
def row(channel=b'Party',message=b'hello',delay=5000,index=0):return MessageListRow(channel,message,delay,index)

class FloodRuntimeTests(unittest.TestCase):
    def test_toggle_caption_resets_timestamp_index_even_stop_without_list_gate(self):
        s=OwnedFloodSession();s.state=FloodRuntimeState(False,9,123)
        self.assertEqual(s.toggle(),FloodRuntimeState(True,0,0,STOP_TEXT))
        self.assertEqual(s.toggle(),FloodRuntimeState())
        self.assertFalse(s.toggle('unmatched caption').enabled)

    def test_inactive_and_empty_skip_all_clocks_and_gates(self):
        c=Clock();s=OwnedFloodSession()
        self.assertEqual(s.advance((row(),),c,lambda:1).status,'inactive')
        s.toggle();self.assertEqual(s.advance((),c,lambda:1).status,'empty');self.assertEqual(c.calls,0)

    def test_single_record_per_tick_three_independent_clock_reads_and_wire_mode(self):
        s=OwnedFloodSession();s.toggle();c=Clock(6000,6010,6020)
        p=s.advance((row(),row(b'Clan',b'two')),c,lambda:1)
        self.assertTrue(p.complete);self.assertEqual(p.payload,b'\x10\x03\x05\x00hello')
        self.assertEqual(p.ticks,(6000,6010,6020));self.assertEqual(p.state.index,1);self.assertEqual(p.state.timestamp,6020)
        self.assertEqual(p.queue.records[0].created_tick,6010);self.assertEqual(len(p.queue.records),1)

    def test_wait_has_one_clock_no_gate_and_equality_is_due(self):
        s=OwnedFloodSession();s.toggle();c=Clock(4999)
        def forbidden():raise AssertionError('gate read before due')
        self.assertEqual(s.advance((row(),),c,forbidden).status,'waiting')
        self.assertEqual(s.advance((row(),),Clock(5000,5001,5002),lambda:1).state.index,0)

    def test_signed_qword_elapsed_does_not_wrap_at_dword_clock_rollover(self):
        s=OwnedFloodSession();s.state=FloodRuntimeState(True,0,0xfffffffe,STOP_TEXT)
        p=s.advance((row(delay=1),),Clock(1),lambda:1)
        self.assertEqual(p.status,'waiting');self.assertEqual(p.elapsed,-4294967293)

    def test_negative_delay_is_signed_and_can_be_due_at_zero(self):
        s=OwnedFloodSession();s.toggle();p=s.advance((row(delay=0xffffffff),),Clock(0,1,2),lambda:1)
        self.assertTrue(p.complete);self.assertEqual(p.status,'locally_enqueued')

    def test_admission_gate_zero_skips_enqueue_clock_but_updates_cycle(self):
        s=OwnedFloodSession();s.toggle();p=s.advance((row(),),Clock(6000,6001),lambda:0)
        self.assertEqual(p.status,'not_enqueued');self.assertEqual(p.queue.records,())
        self.assertEqual(p.ticks,(6000,6001));self.assertEqual(p.state.timestamp,6001)

    def test_unknown_channel_skips_gate_and_serializer_but_advances(self):
        s=OwnedFloodSession();s.toggle()
        def forbidden():raise AssertionError('unknown channel should skip gate')
        p=s.advance((row(b'party'),row()),Clock(6000,6010),forbidden)
        self.assertEqual(p.status,'unknown_channel');self.assertEqual(p.state.index,1);self.assertIsNone(p.payload)

    def test_cstring_nul_and_512_copy_boundary_then_alias_remains_open(self):
        s=OwnedFloodSession();s.toggle()
        p=s.advance((row(message=b'a\0tail'),),Clock(6000,6010,6020),lambda:1)
        self.assertEqual(p.payload,b'\x10\x03\x01\x00a')
        s.toggle();s.toggle();p=s.advance((row(message=b'a'*512),),Clock(6000,6010,6020),lambda:1)
        self.assertEqual(len(p.payload),516)
        p=s.advance((row(message=b'a'*513,delay=0),),Clock(7000),lambda:1)
        self.assertFalse(p.complete);self.assertEqual(p.status,'unresolved_source_stack_alias');self.assertEqual(len(p.queue.records),2)

    def test_queue_prefix_survives_missing_post_clock_without_duplicate(self):
        s=OwnedFloodSession();s.toggle();rows=(row(),)
        p=s.advance(rows,Clock(6000,6010),lambda:1)
        self.assertFalse(p.complete);self.assertEqual(len(p.queue.records),1);self.assertEqual(p.state.timestamp,0)
        p=s.advance(rows,Clock(6020),lambda:1)
        self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1);self.assertEqual(p.state.timestamp,6020)

    def test_pending_snapshot_and_out_of_range_source_index_not_clamped(self):
        s=OwnedFloodSession();s.toggle();s.advance((row(),),Clock(6000,6010),lambda:1)
        self.assertEqual(s.advance((row(message=b'changed'),),Clock(6020),lambda:1).status,'changed_during_tick')
        s.toggle();s.toggle();s.state=replace(s.state,index=3)
        p=s.advance((row(),),Clock(6000),lambda:1)
        self.assertEqual(p.status,'unresolved_source_index');self.assertEqual(p.state.index,3)

    def test_stop_retains_queue_and_does_not_forge_delivery(self):
        s=OwnedFloodSession();s.toggle();p=s.advance((row(),),Clock(6000,6010,6020),lambda:1)
        s.toggle();self.assertEqual(s.queue,p.queue)
        self.assertFalse(p.delivery_verified);self.assertFalse(p.native_execution_verified);self.assertFalse(p.live_compatibility_verified)

if __name__=='__main__':unittest.main()
