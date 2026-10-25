import unittest
from message_list_add import *

NORMALS=('message_argument_copy','channel_argument_copy','item_add','channel_to_unicode','caption_set',
 'channel_unicode_cleanup','message_to_unicode','message_subitem_append','message_unicode_cleanup',
 'delay_to_unicode','delay_subitem_append','delay_unicode_cleanup','producer_parent_return',
 'channel_argument_cleanup','message_argument_cleanup')
def sample(delay=5):
    child=MessageListObservation(True,{'row0.count_eax':0},{k:True for k in ('clear_end_iterator','clear_begin_iterator','clear_range','row0.count')})
    return MessageListAddObservation(True,{'post_copy_delay_dword':delay,'created_item_eax':0x1234},
        {k:True for k in NORMALS},{'converted_channel':'Party','converted_message':'captured message','converted_delay':'native formatted'},child)

class MessageListAddTests(unittest.TestCase):
    def test_signed_threshold_rejects_before_ui_and_producer(self):
        for delay in (0,1,4,0x80000000,0xffffffff):
            with self.subTest(delay=delay):
                plan=MessageListAddFrame(11,22).advance(sample(delay))
                self.assertTrue(plan.complete);self.assertEqual(plan.status,'delay_rejected')
                self.assertEqual(plan.ui_intents,());self.assertIsNone(plan.producer)
                self.assertEqual([c[2] for c in plan.calls],['message_argument_copy','channel_argument_copy','channel_argument_cleanup','message_argument_cleanup'])

    def test_five_and_signed_max_accepted_with_captured_format(self):
        for delay in (5,0x7fffffff):
            plan=MessageListAddFrame(11,22).advance(sample(delay))
            self.assertTrue(plan.complete);self.assertEqual(plan.status,'row_added_and_recompiled')
            self.assertEqual(plan.ui_intents,(('add_item',LIST_PATH,0x1234),('caption',0x1234,'Party'),
                ('append_subitem',0x1234,'captured message'),('append_subitem',0x1234,'native formatted')))
            self.assertTrue(plan.producer.complete);self.assertEqual(plan.next_address,0x45cb9c)

    def test_both_argument_copies_precede_threshold_capture(self):
        s=sample(0);frame=MessageListAddFrame(11,22)
        p=frame.advance(replace(s,normal_returns={'message_argument_copy':True}))
        self.assertEqual(p.needed,('normal','channel_argument_copy'));self.assertEqual(dict(frame.observation.values),{})
        self.assertTrue(frame.advance(s).complete)

    def test_caption_intent_retained_before_cleanup_and_no_duplicate(self):
        s=sample();frame=MessageListAddFrame(11,22)
        p=frame.advance(replace(s,normal_returns={**s.normal_returns,'channel_unicode_cleanup':False}))
        self.assertEqual(len(p.ui_intents),2);self.assertEqual(p.needed,('normal','channel_unicode_cleanup'))
        changed=replace(s,texts={**s.texts,'converted_channel':'changed'},values={**s.values,'created_item_eax':77})
        p=frame.advance(changed);self.assertTrue(p.complete)
        self.assertEqual(p.ui_intents[1],('caption',0x1234,'Party'));self.assertEqual(len(p.ui_intents),4)
        self.assertIs(frame.advance(sample(0)),p)

    def test_delay_cleanup_precedes_recompile_child(self):
        s=sample();frame=MessageListAddFrame(11,22)
        p=frame.advance(replace(s,normal_returns={**s.normal_returns,'delay_unicode_cleanup':False}))
        self.assertEqual(len(p.ui_intents),4);self.assertIsNone(p.producer)
        self.assertEqual(p.needed,('normal','delay_unicode_cleanup'))

    def test_typed_child_and_separate_parent_and_two_final_cleanups(self):
        s=sample();frame=MessageListAddFrame(11,22)
        p=frame.advance(replace(s,producer=None))
        self.assertEqual(p.needed,('producer',('entry','0045c499')))
        p=frame.advance(MessageListAddObservation(producer=s.producer))
        self.assertTrue(p.producer.complete);self.assertEqual(p.needed,('normal','producer_parent_return'))
        p=frame.advance(MessageListAddObservation(normal_returns={'producer_parent_return':True}))
        self.assertEqual(p.needed,('normal','channel_argument_cleanup'))
        p=frame.advance(MessageListAddObservation(normal_returns={'channel_argument_cleanup':True}))
        self.assertEqual(p.needed,('normal','message_argument_cleanup'))
        self.assertTrue(frame.advance(MessageListAddObservation(normal_returns={'message_argument_cleanup':True})).complete)

    def test_captured_rebuild_not_inferred_from_ui_intents(self):
        p=MessageListAddFrame(11,22).advance(sample())
        self.assertEqual(len(p.ui_intents),4);self.assertEqual(p.producer.rows,())
        self.assertTrue(p.producer.cleared) # Captured child can observe independent/mutated UI.

    def test_created_zero_pointer_has_no_invented_success_gate(self):
        s=sample();p=MessageListAddFrame(11,22).advance(replace(s,values={**s.values,'created_item_eax':0}))
        self.assertTrue(p.complete);self.assertEqual(p.ui_intents[1],('caption',0,'Party'))

    def test_missing_unicode_capture_does_not_use_argument_or_codec(self):
        s=sample();p=MessageListAddFrame(11,22).advance(replace(s,texts={}))
        self.assertEqual(p.needed,('text','converted_channel'));self.assertEqual(len(p.ui_intents),1)

    def test_types_and_verification_limits(self):
        for kwargs in ({'producer':{}},{'normal_returns':{'producer':True}},{'values':{'x':True}},{'texts':{'x':b'bytes'}}):
            with self.assertRaises(ValueError):MessageListAddObservation(**kwargs)
        with self.assertRaises(ValueError):MessageListAddFrame(-1,0)
        p=MessageListAddFrame(0,0).advance(sample())
        self.assertFalse(p.whole_function_verified);self.assertFalse(p.native_execution_verified);self.assertFalse(p.live_compatibility_verified)

if __name__=='__main__':unittest.main()
