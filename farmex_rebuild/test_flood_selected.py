import unittest
from flood_selected import *

def row(c=b'Party',m=b'hello',delay=999999):return MessageListRow(c,m,delay,0)
class Reader:
    def __init__(self,*values):self.values=iter(values);self.calls=0
    def __call__(self):self.calls+=1;return next(self.values)
def forbidden():raise AssertionError('unreached provider used')

class FloodSelectedTests(unittest.TestCase):
    def test_first_negative_selection_skips_second_and_all_row_gate_clock_reads(self):
        selected=Reader(0xffffffff)
        p=OwnedSelectedMessageFrame().advance(selected,forbidden,forbidden,forbidden)
        self.assertTrue(p.complete);self.assertEqual(p.status,'no_selection');self.assertEqual(selected.calls,1)

    def test_second_fresh_selection_is_used_and_delay_is_not_read(self):
        selected=Reader(0,1);clock=Reader(123)
        p=OwnedSelectedMessageFrame().advance(selected,lambda:(row(),row(b'Clan',b'two',-999)),clock,lambda:1)
        self.assertEqual(p.first_index,0);self.assertEqual(p.selected_index,1)
        self.assertEqual(p.payload,b'\x10\x06\x03\x00two');self.assertEqual(clock.calls,1)
        self.assertEqual(p.queue.records[0].created_tick,123)

    def test_second_negative_is_not_python_last_row_and_is_not_clamped(self):
        p=OwnedSelectedMessageFrame().advance(Reader(0,0xffffffff),lambda:(row(),),forbidden,forbidden)
        self.assertFalse(p.complete);self.assertEqual(p.status,'unresolved_source_index');self.assertEqual(p.queue.records,())

    def test_unknown_channel_has_no_clock_or_gate(self):
        p=OwnedSelectedMessageFrame().advance(Reader(0,0),lambda:(row(b'Party\0'),),forbidden,forbidden)
        self.assertTrue(p.complete);self.assertEqual(p.status,'unknown_channel');self.assertIsNone(p.payload)

    def test_gate_zero_copies_no_record_and_reads_no_clock(self):
        p=OwnedSelectedMessageFrame().advance(Reader(0,0),lambda:(row(),),forbidden,lambda:0)
        self.assertEqual(p.status,'not_enqueued');self.assertEqual(p.queue.records,())

    def test_missing_enqueue_clock_resumes_without_repeating_reads(self):
        selected=Reader(0,0);rows=Reader((row(),));gate=Reader(1);frame=OwnedSelectedMessageFrame()
        self.assertFalse(frame.advance(selected,rows,Reader(),gate).complete)
        p=frame.advance(forbidden,forbidden,Reader(500),forbidden)
        self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1)
        self.assertEqual((selected.calls,rows.calls,gate.calls),(2,1,1))
        self.assertIs(frame.advance(forbidden,forbidden,forbidden,forbidden),p)

    def test_cstring_empty_and_partial_nul_use_shared_packet_shape(self):
        for message,expected in ((b'',b'\x10\x03\x00\x00'),(b'a\0tail',b'\x10\x03\x01\x00a')):
            p=OwnedSelectedMessageFrame().advance(Reader(0,0),lambda:(row(m=message),),Reader(1),lambda:1)
            self.assertEqual(p.payload,expected)

    def test_stack_alias_scope_not_guessed_and_queue_prefix_preserved(self):
        first=OwnedSelectedMessageFrame().advance(Reader(0,0),lambda:(row(),),Reader(1),lambda:1)
        p=OwnedSelectedMessageFrame(first.queue).advance(Reader(0,0),lambda:(row(m=b'x'*513),),forbidden,forbidden)
        self.assertFalse(p.complete);self.assertEqual(p.status,'unresolved_source_stack_alias');self.assertEqual(p.queue,first.queue)

    def test_existing_queue_gets_a_new_distinct_record(self):
        first=OwnedSelectedMessageFrame().advance(Reader(0,0),lambda:(row(),),Reader(1),lambda:1)
        second=OwnedSelectedMessageFrame(first.queue).advance(Reader(0,0),lambda:(row(),),Reader(2),lambda:1)
        self.assertEqual([r.record_id for r in second.queue.records],[1,2])
        self.assertFalse(second.delivery_verified);self.assertFalse(second.native_execution_verified);self.assertFalse(second.live_compatibility_verified)

    def test_reader_contracts_do_not_fabricate_selected_row(self):
        p=OwnedSelectedMessageFrame().advance(lambda:True,forbidden,forbidden,forbidden)
        self.assertFalse(p.complete);self.assertEqual(p.queue.records,())
        p=OwnedSelectedMessageFrame().advance(Reader(0,0),lambda:[row()],forbidden,forbidden)
        self.assertFalse(p.complete)

if __name__=='__main__':unittest.main()
