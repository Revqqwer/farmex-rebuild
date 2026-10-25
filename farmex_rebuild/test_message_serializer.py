import unittest
from message_serializer import *

def sample(data=b'abc',**values):
    captures=dict(fresh_message_parameter_dword=0x1000,length_word=len(data),
        string_check_length_dword=len(data),copy_length_dword=len(data),string_data_eax=0x2000,add_length_dword=len(data))
    captures.update(values)
    normals={key:True for key in ('argument_copy','string_factory','string_copy','initial_string_cleanup','string_assign',
        'opcode_append','wire_append','word_append','string_data','string_memcpy','string_append_parent',
        'final_string_cleanup','argument_cleanup')}
    return MessageSerializerObservation(True,captures,normals,data,QueueAttempt(1,100,True))

def channel_sample():
    from message_channels import CHANNELS
    return MessageChannelObservation(True,{**{key+'_compare_eax':int(key=='party') for key,_,_ in CHANNELS},'fresh_message_argument_dword':0x5000},
        {key:True for key in ['message_argument_copy','channel_argument_copy','channel_argument_cleanup','message_argument_cleanup']+
         [key+suffix for key,_,_ in CHANNELS for suffix in ('_literal','_compare','_literal_cleanup')]})

def cycle_sample():
    return SourceMessageCycleObservation(True,dict(first_test_begin=0x1000,first_end=0x100c,first_subtract_begin=0x1000,
        first_tick_eax=1000,last_tick_low=0,last_tick_high=0,delay_index=0,delay_begin=0x1000,delay_value=1000,
        argument4_index=0,argument4_begin=0x1000,argument4_value=0x3000,argument0_index=0,argument0_begin=0x1000,
        argument0_value=0x2000,second_tick_eax=1010,increment_index_before=0,tail_test_begin=0x1000,
        tail_end=0x100c,tail_subtract_begin=0x1000,tail_compare_index=1),{'first_tick':True,'second_tick':True})

class MessageSerializerTests(unittest.TestCase):
    def test_all_eighteen_modes_build_source_wire_bytes(self):
        for mode,wire in WIRE_MODES.items():
            plan=MessageSerializerFrame(mode,0x1000).advance(sample())
            self.assertTrue(plan.complete);self.assertEqual(plan.payload,bytes([0x10,wire,3,0])+b'abc')
            self.assertEqual(plan.queue.records[0].payload,plan.payload)
            self.assertEqual(plan.queue.records[0].delay_dword,0)

    def test_holes_and_out_of_range_modes_enqueue_header_only(self):
        for mode in (6,18,33,35,0xffffffff):
            plan=MessageSerializerFrame(mode,1).advance(sample())
            self.assertTrue(plan.complete);self.assertEqual(plan.payload,b'\x10');self.assertIsNone(plan.wire_mode)
            self.assertNotIn('004c76cc',[c[0] for c in plan.calls])

    def test_null_postcopy_message_pointer_uses_source_empty_literal(self):
        plan=MessageSerializerFrame(0,0x5555).advance(sample(b'',fresh_message_parameter_dword=0))
        self.assertEqual(plan.c_string_pointer,0x5479b4);self.assertEqual(plan.payload,b'\x10\x01\x00\x00')

    def test_word_check_copy_and_add_lengths_remain_independent(self):
        plan=MessageSerializerFrame(0,1).advance(sample(b'abcd',length_word=7,add_length_dword=2))
        self.assertEqual(plan.payload,b'\x10\x01\x07\x00ab')
        self.assertEqual(plan.initialized_bytes,b'\x10\x01\x07\x00abcd')
        plan=MessageSerializerFrame(0,1).advance(sample(b'abc',string_check_length_dword=0,length_word=9))
        self.assertEqual(plan.payload,b'\x10\x01\x09\x00')

    def test_stack_alias_and_uninitialized_tail_remain_incomplete(self):
        plan=MessageSerializerFrame(0,1).advance(sample(b'x'*513))
        self.assertEqual(plan.needed,('scope','source_stack_alias_copy'));self.assertEqual(plan.queue.records,())
        plan=MessageSerializerFrame(0,1).advance(sample(b'abc',add_length_dword=4))
        self.assertEqual(plan.needed,('scope','uninitialized_enqueue_tail'));self.assertEqual(plan.queue.records,())

    def test_exact_nominal_buffer_limit_and_zero_copy(self):
        plan=MessageSerializerFrame(0,1).advance(sample(b'x'*508))
        self.assertTrue(plan.complete);self.assertEqual(len(plan.payload),512)
        plan=MessageSerializerFrame(0,1).advance(sample(b'x'*512))
        self.assertTrue(plan.complete);self.assertEqual(len(plan.payload),516) #Only the dead pointer local is overwritten.
        plan=MessageSerializerFrame(0,1).advance(sample(b'',string_check_length_dword=1))
        self.assertTrue(plan.complete);self.assertEqual(plan.payload,b'\x10\x01\x00\x00')
        plan=MessageSerializerFrame(0,1).advance(replace(sample(b'',string_check_length_dword=1),data_bytes=None))
        self.assertTrue(plan.complete) #Zero-length memcpy needs no fabricated byte capture.

    def test_missing_copy_data_or_memcpy_normal_does_not_guess_bytes(self):
        frame=MessageSerializerFrame(0,1);s=sample()
        plan=frame.advance(replace(s,data_bytes=b'ab'))
        self.assertEqual(plan.needed,('bytes','string_copy_data'))
        plan=frame.advance(replace(s,normal_returns={**s.normal_returns,'string_memcpy':False}))
        self.assertEqual(plan.needed,('normal','string_memcpy'));self.assertEqual(plan.initialized_bytes,b'\x10\x01\x03\x00')
        plan=frame.advance(s);self.assertEqual(plan.payload,b'\x10\x01\x03\x00abc')

    def test_post_memcpy_length_gap_retains_copied_bytes(self):
        frame=MessageSerializerFrame(0,1);s=sample();values=dict(s.values);del values['add_length_dword']
        plan=frame.advance(replace(s,values=values))
        self.assertEqual(plan.needed,('value','add_length_dword'));self.assertEqual(plan.initialized_bytes[-3:],b'abc')
        plan=frame.advance(sample(b'xyz'));self.assertEqual(plan.payload[-3:],b'abc')

    def test_enqueue_commit_and_final_cleanups_are_not_duplicated(self):
        frame=MessageSerializerFrame(0,1);s=sample()
        plan=frame.advance(replace(s,attempt=QueueAttempt(1,100,False)))
        self.assertEqual(len(plan.queue.records),1)
        plan=frame.advance(replace(s,attempt=QueueAttempt(0,999,True),normal_returns={**s.normal_returns,'final_string_cleanup':False}))
        self.assertEqual(plan.needed,('normal','final_string_cleanup'));self.assertEqual(len(plan.queue.records),1)
        plan=frame.advance(s);self.assertTrue(plan.complete);self.assertEqual(len(plan.queue.records),1)
        self.assertEqual(plan.queue.records[0].created_tick,100);self.assertIs(frame.advance(s),plan)

    def test_disconnected_enqueue_needs_no_tick(self):
        plan=MessageSerializerFrame(0,1).advance(replace(sample(),attempt=QueueAttempt(0,None,True)))
        self.assertTrue(plan.complete);self.assertEqual(plan.queue.records,())

    def test_index_dword_wrap_can_truncate_initialized_prefix(self):
        plan=MessageSerializerFrame(0,1).advance(sample(b'abc',add_length_dword=0xffffffff))
        self.assertTrue(plan.complete);self.assertEqual(plan.enqueue_length,3);self.assertEqual(plan.payload,b'\x10\x01\x03')

    def test_typed_cycle_channel_serializer_and_parent_gates(self):
        frame=SerializedChannelCycleFrame()
        plan=frame.advance(cycle_sample(),channel_sample(),serializer_parent_returned=True)
        self.assertEqual(plan.needed,('serializer',('entry','004c9b87')))
        plan=frame.advance(SourceMessageCycleObservation(),serializer=sample())
        self.assertEqual(plan.needed,'serializer_parent_returned');self.assertEqual(len(plan.queue.records),1)
        plan=frame.advance(SourceMessageCycleObservation(),channel_sample(),serializer_parent_returned=True)
        self.assertEqual(plan.needed,'channel_parent_returned')
        plan=frame.advance(cycle_sample(),channel_parent_returned=True)
        self.assertTrue(plan.complete);self.assertEqual(plan.queue.records[0].payload,b'\x10\x03\x03\x00abc')

    def test_serializer_override_types_and_delivery_flags(self):
        with self.assertRaises(ValueError):MessageSerializerObservation(values={'length_word':65536})
        with self.assertRaises(ValueError):MessageSerializerObservation(data_bytes=bytearray())
        with self.assertRaises(ValueError):SerializedChannelCycleFrame().advance(cycle_sample(),replace(channel_sample(),normal_returns={'serializer':True}))
        plan=MessageSerializerFrame(0,1).advance(sample())
        self.assertFalse(plan.native_execution_verified);self.assertFalse(plan.delivery_verified)
        self.assertFalse(plan.live_compatibility_verified)

if __name__=='__main__':unittest.main()
