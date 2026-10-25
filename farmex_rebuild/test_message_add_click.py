import unittest
from message_add_click import *

NORMALS=('delay_text_init','delay_text_get','integer_parent_return','message_text_init','message_text_get',
 'message_ansi_convert','channel_text_init','channel_index_get','channel_item_get','channel_ansi_convert',
 'add_parent_return','channel_ansi_cleanup','channel_unicode_cleanup','message_ansi_cleanup','message_unicode_cleanup','delay_unicode_cleanup')
def sample(qword=4):
    integer=SourceIntegerObservation(True,'normal',True,qword,cleanup_returned=True)
    add=MessageListAddObservation(True,{'post_copy_delay_dword':qword&0xffffffff},
        {k:True for k in ('message_argument_copy','channel_argument_copy','channel_argument_cleanup','message_argument_cleanup')})
    return MessageAddClickObservation(True,{'message_ansi_dword':0x100,'channel_ansi_dword':0x200,
        'channel_index_eax':0xffffffff,'fresh_combo_strings_object_dword':0x300},{k:True for k in NORMALS},
        {'delay':'captured delay','message':'unicode message','channel':'selected item'},integer,add)

class MessageAddClickTests(unittest.TestCase):
    def test_low_dword_and_physical_argument_order(self):
        p=MessageAddClickFrame().advance(sample(0x1234567800000004))
        self.assertTrue(p.complete);self.assertEqual(p.physical_pushes,(4,0x100,0x200,0x569910))
        self.assertEqual(p.add.status,'delay_rejected');self.assertEqual(p.integer.high_dword,0x12345678)
        self.assertEqual(p.next_address,0x4b168d)

    def test_integer_fallback_ten_is_explicit_and_reaches_child(self):
        s=sample();s=replace(s,integer=SourceIntegerObservation(True,'catch_landing',catch_landing_returned=True,cleanup_returned=True),add=None)
        p=MessageAddClickFrame().advance(s)
        self.assertEqual(p.integer.default_qword,10);self.assertEqual(p.physical_pushes[0],10)
        self.assertEqual(p.needed,('add',('entry','0045ca30')))

    def test_missing_parser_result_not_derived_from_text(self):
        s=sample();frame=MessageAddClickFrame()
        p=frame.advance(replace(s,integer=SourceIntegerObservation(True,'normal',True)))
        self.assertEqual(p.needed,('integer','parser_qword'));self.assertIsNone(p.physical_pushes)
        p=frame.advance(s);self.assertTrue(p.complete)

    def test_parent_integer_return_precedes_message_init(self):
        s=sample();frame=MessageAddClickFrame()
        p=frame.advance(replace(s,normal_returns={**s.normal_returns,'integer_parent_return':False}))
        self.assertTrue(p.integer.complete);self.assertEqual(p.needed,('normal','integer_parent_return'))
        self.assertNotIn('message_text_init',[c[2] for c in p.calls])

    def test_raw_negative_selection_not_clamped_or_early_rejected(self):
        p=MessageAddClickFrame().advance(sample())
        self.assertIn(('VCL_Strings_virtual_0c',(0x300,0xffffffff),'channel_item_get'),p.calls)
        self.assertTrue(p.complete)

    def test_fresh_strings_object_is_read_after_index_get(self):
        s=sample();frame=MessageAddClickFrame()
        p=frame.advance(replace(s,normal_returns={**s.normal_returns,'channel_index_get':False}))
        self.assertNotIn('fresh_combo_strings_object_dword',frame.observation.values)
        p=frame.advance(replace(s,values={**s.values,'fresh_combo_strings_object_dword':0x777}))
        self.assertIn(('VCL_Strings_virtual_0c',(0x777,0xffffffff),'channel_item_get'),p.calls)

    def test_typed_add_and_parent_separate_before_five_cleanup_calls(self):
        s=sample();frame=MessageAddClickFrame()
        p=frame.advance(replace(s,add=None));self.assertEqual(p.needed,('add',('entry','0045ca30')))
        p=frame.advance(MessageAddClickObservation(add=s.add))
        self.assertTrue(p.add.complete);self.assertEqual(p.needed,('normal','add_parent_return'))
        p=frame.advance(MessageAddClickObservation(normal_returns={'add_parent_return':True}))
        self.assertEqual(p.needed,('normal','channel_ansi_cleanup'))
        p=frame.advance(s);self.assertTrue(p.complete)
        self.assertEqual([c[2] for c in p.calls][-5:],['channel_ansi_cleanup','channel_unicode_cleanup','message_ansi_cleanup','message_unicode_cleanup','delay_unicode_cleanup'])

    def test_accepted_captures_retained_across_later_wait(self):
        s=sample();frame=MessageAddClickFrame()
        p=frame.advance(replace(s,normal_returns={**s.normal_returns,'channel_text_init':False}))
        p=frame.advance(replace(s,values={**s.values,'message_ansi_dword':0x999},texts={**s.texts,'delay':'changed'}))
        self.assertTrue(p.complete);self.assertEqual(p.physical_pushes[1],0x100)
        self.assertEqual(frame.integer.text,'captured delay');self.assertIs(frame.advance(sample(0)),p)

    def test_empty_message_and_null_ansi_are_not_invented_rejections(self):
        s=sample();p=MessageAddClickFrame().advance(replace(s,texts={**s.texts,'message':''},values={**s.values,'message_ansi_dword':0}))
        self.assertTrue(p.complete);self.assertEqual(p.physical_pushes[1],0)

    def test_types_and_unproven_flags(self):
        for kwargs in ({'integer':{}},{'add':{}},{'normal_returns':{'add':True}},{'values':{'x':True}}):
            with self.assertRaises(ValueError):MessageAddClickObservation(**kwargs)
        p=MessageAddClickFrame().advance(sample())
        self.assertFalse(p.whole_function_verified);self.assertFalse(p.codec_verified);self.assertFalse(p.native_execution_verified);self.assertFalse(p.live_compatibility_verified)

    def test_full_accepted_add_rebuild_and_outer_cleanup_chain(self):
        from message_list_producer import MessageListObservation
        s=sample(5)
        normals=('message_argument_copy','channel_argument_copy','item_add','channel_to_unicode','caption_set',
            'channel_unicode_cleanup','message_to_unicode','message_subitem_append','message_unicode_cleanup',
            'delay_to_unicode','delay_subitem_append','delay_unicode_cleanup','producer_parent_return',
            'channel_argument_cleanup','message_argument_cleanup')
        producer=MessageListObservation(True,{'row0.count_eax':0},
            {k:True for k in ('clear_end_iterator','clear_begin_iterator','clear_range','row0.count')})
        child=MessageListAddObservation(True,{'post_copy_delay_dword':5,'created_item_eax':123},
            {k:True for k in normals},{'converted_channel':'fresh channel','converted_message':'fresh message','converted_delay':'5'},producer)
        p=MessageAddClickFrame().advance(replace(s,add=child))
        self.assertTrue(p.complete);self.assertEqual(p.add.status,'row_added_and_recompiled')
        self.assertEqual(len(p.add.ui_intents),4);self.assertTrue(p.add.producer.complete)
        self.assertEqual(p.physical_pushes,(5,0x100,0x200,0x569910))

if __name__=='__main__':unittest.main()
