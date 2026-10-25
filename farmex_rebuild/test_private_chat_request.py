import unittest
from dataclasses import replace
from private_chat_request import PrivateChatObservation as O,PrivateChatRequestFrame as Frame
from direct_chat_packets import QueueAttempt


def sample(data=b'Seller',**overrides):
    values=dict(fresh_name_parameter_dword=0x1000,length_word=len(data),string_check_length_dword=len(data),
        copy_length_dword=len(data),string_data_eax=0x2000,add_length_dword=len(data))
    values.update(overrides)
    normals={k:True for k in ('argument_copy','string_factory','string_copy','initial_string_cleanup','string_assign',
        'opcode_append','subopcode_append','word_append','string_data','string_memcpy','string_append_parent',
        'final_string_cleanup','argument_cleanup')}
    return O(True,values,normals,data,QueueAttempt(1,100,True))


class PrivateChatRequestTests(unittest.TestCase):
    def test_request_wire_and_own_queue_are_not_chat_text_send(self):
        p=Frame(1).advance(sample())
        self.assertTrue(p.complete)
        self.assertEqual(p.payload,b'\x35\x01\x06\x00Seller')
        self.assertEqual(p.queue.records[0].payload,p.payload)
        self.assertEqual(p.queue.records[0].delay_dword,0)
        self.assertFalse(p.native_execution_verified or p.delivery_verified or p.live_compatibility_verified)

    def test_entry_and_argument_copy_are_separate_gaps(self):
        frame=Frame(1)
        self.assertEqual(frame.advance(O()).needed,('entry','004ca233'))
        self.assertEqual(frame.advance(O(True)).needed,('normal','argument_copy'))
        self.assertEqual(frame.queue.records,())

    def test_null_fresh_argument_uses_correct_source_empty_literal(self):
        p=Frame(0x9999).advance(sample(b'',fresh_name_parameter_dword=0))
        self.assertTrue(p.complete)
        self.assertEqual(p.c_string_pointer,0x5479b5)
        self.assertEqual(p.payload,b'\x35\x01\x00\x00')

    def test_independent_word_check_copy_and_add_lengths(self):
        p=Frame(1).advance(sample(b'abcd',length_word=7,add_length_dword=2))
        self.assertEqual(p.payload,b'\x35\x01\x07\x00ab')
        self.assertEqual(p.initialized_bytes,b'\x35\x01\x07\x00abcd')
        p=Frame(1).advance(sample(b'abc',length_word=9,string_check_length_dword=0))
        self.assertEqual(p.payload,b'\x35\x01\x09\x00')

    def test_nominal_and_dead_pointer_limits_then_counter_alias_gap(self):
        for count in (96,100):
            p=Frame(1).advance(sample(b'x'*count))
            self.assertTrue(p.complete)
            self.assertEqual(len(p.payload),4+count)
        p=Frame(1).advance(sample(b'x'*101))
        self.assertEqual(p.needed,('scope','source_stack_alias_copy'))
        self.assertEqual(p.queue.records,())

    def test_uninitialized_enqueue_tail_is_not_zero_padded(self):
        p=Frame(1).advance(sample(b'abc',add_length_dword=4))
        self.assertEqual(p.needed,('scope','uninitialized_enqueue_tail'))
        self.assertEqual(p.queue.records,())

    def test_missing_copy_capture_and_memcpy_return_can_resume(self):
        frame=Frame(1);s=sample()
        self.assertEqual(frame.advance(replace(s,data_bytes=b'Sel')).needed,('bytes','string_copy_data'))
        self.assertEqual(frame.advance(replace(s,normal_returns={**s.normal_returns,'string_memcpy':False})).needed,('normal','string_memcpy'))
        self.assertEqual(frame.advance(s).payload,b'\x35\x01\x06\x00Seller')

    def test_post_copy_gap_preserves_original_copied_bytes(self):
        frame=Frame(1);s=sample(b'abc');values=dict(s.values);del values['add_length_dword']
        p=frame.advance(replace(s,values=values))
        self.assertEqual(p.needed,('value','add_length_dword'))
        self.assertEqual(p.initialized_bytes[-3:],b'abc')
        p=frame.advance(sample(b'xyz'))
        self.assertEqual(p.payload[-3:],b'abc')

    def test_cleanup_gap_never_duplicates_already_admitted_record(self):
        frame=Frame(1);s=sample();p=frame.advance(replace(s,normal_returns={**s.normal_returns,'argument_cleanup':False}))
        self.assertEqual(p.needed,('normal','argument_cleanup'))
        self.assertEqual(len(p.queue.records),1)
        p=frame.advance(s)
        self.assertTrue(p.complete)
        self.assertEqual(len(p.queue.records),1)
        self.assertIs(frame.advance(O()),p)

    def test_admission_gate0_does_not_invent_tick_or_enqueue(self):
        p=Frame(1).advance(replace(sample(),attempt=QueueAttempt(0,None,True)))
        self.assertTrue(p.complete)
        self.assertEqual(p.queue.records,())

    def test_zero_copy_requires_no_fabricated_byte_capture(self):
        p=Frame(1).advance(replace(sample(b'',string_check_length_dword=1),data_bytes=None))
        self.assertTrue(p.complete)
        self.assertEqual(p.payload,b'\x35\x01\x00\x00')

    def test_contracts(self):
        with self.assertRaises(ValueError):Frame(-1)
        with self.assertRaises(ValueError):O(values={'length_word':65536})
        with self.assertRaises(ValueError):O(data_bytes='not ANSI')
        with self.assertRaises(ValueError):O(normal_returns={'argument_copy':1})


if __name__=='__main__':unittest.main()
