import unittest
from message_toggle import *

def sample(eax=1):
    return MessageToggleObservation(True,{'compare_eax':eax},
        {key:True for key in ('comparison_literal_create','current_text_init','current_text_get','caption_compare',
         'comparison_literal_cleanup','current_text_cleanup','new_caption_create','new_caption_set','new_caption_cleanup')})

class MessageToggleTests(unittest.TestCase):
    def test_no_stores_before_entry(self):
        plan=MessageToggleFrame().advance(MessageToggleObservation())
        self.assertEqual(plan.needed,('entry','0045cbbd'));self.assertEqual(plan.stores,())

    def test_three_resets_happen_before_first_managed_helper(self):
        plan=MessageToggleFrame().advance(MessageToggleObservation(True))
        self.assertEqual(plan.needed,('normal','comparison_literal_create'))
        self.assertEqual(plan.stores,((0x569938,4,0),(0x56993c,4,0),(0x569934,4,0)))
        self.assertEqual(plan.ui_updates,());self.assertIsNone(plan.enabled_byte)

    def test_start_caption_match_sets_stop_text_then_enable_one(self):
        plan=MessageToggleFrame().advance(sample())
        self.assertEqual(plan.status,'start_branch_returned')
        self.assertEqual(plan.ui_updates,((BUTTON_PATH,STOP_CAPTION),))
        self.assertEqual(plan.stores[-1],(0x569930,1,1))

    def test_compare_low_byte_zero_always_takes_stop_branch(self):
        for eax in (0,0x12340000,0x100):
            plan=MessageToggleFrame().advance(sample(eax))
            self.assertEqual(plan.status,'stop_branch_returned')
            self.assertEqual(plan.ui_updates,((BUTTON_PATH,START_CAPTION),))
            self.assertEqual(plan.stores[-1],(0x569930,1,0))

    def test_noncanonical_nonzero_compare_low_byte_starts(self):
        plan=MessageToggleFrame().advance(sample(255))
        self.assertEqual(plan.enabled_byte,1)

    def test_comparison_is_retained_across_two_cleanup_gaps(self):
        s=sample();frame=MessageToggleFrame()
        plan=frame.advance(replace(s,normal_returns={**s.normal_returns,'comparison_literal_cleanup':False}))
        self.assertEqual(plan.needed,('normal','comparison_literal_cleanup'))
        plan=frame.advance(MessageToggleObservation(normal_returns={'comparison_literal_cleanup':True}))
        self.assertEqual(plan.needed,('normal','current_text_cleanup'))
        plan=frame.advance(sample(0))
        self.assertEqual(plan.enabled_byte,1)

    def test_setter_return_precedes_ui_projection(self):
        s=sample();frame=MessageToggleFrame()
        plan=frame.advance(replace(s,normal_returns={**s.normal_returns,'new_caption_set':False}))
        self.assertEqual(plan.needed,('normal','new_caption_set'));self.assertEqual(plan.ui_updates,())
        self.assertEqual(len(plan.stores),3)

    def test_new_caption_cleanup_precedes_active_store(self):
        s=sample();frame=MessageToggleFrame()
        plan=frame.advance(replace(s,normal_returns={**s.normal_returns,'new_caption_cleanup':False}))
        self.assertEqual(plan.ui_updates,((BUTTON_PATH,STOP_CAPTION),));self.assertEqual(len(plan.stores),3)
        plan=frame.advance(MessageToggleObservation(normal_returns={'new_caption_cleanup':True}))
        self.assertEqual(plan.stores[-1],(0x569930,1,1))
        self.assertIs(frame.advance(sample(0)),plan)

    def test_no_list_rebuild_or_size_gate_inserted(self):
        for eax in (0,1):
            plan=MessageToggleFrame().advance(sample(eax))
            self.assertNotIn('0045c488',[c[0] for c in plan.calls])
            self.assertNotIn('0045c814',[c[0] for c in plan.calls])
            self.assertEqual(plan.next_address,0x45ccd8)

    def test_context_arithmetic_wraps(self):
        plan=MessageToggleFrame(context=0xfffffff0).advance(sample())
        self.assertEqual(plan.stores,((0x18,4,0),(0x1c,4,0),(0x14,4,0),(0x10,1,1)))

    def test_callback_entry_child_and_normal_return_are_separate(self):
        frame=MessageToggleClickFrame();plan=frame.advance(sample(),handler_returned=True)
        self.assertEqual(plan.needed,'callback_entry')
        plan=frame.advance(entry_reached=True,handler_returned=True)
        self.assertEqual(plan.needed,('toggle',('entry','0045cbbd')))
        plan=frame.advance(sample())
        self.assertEqual(plan.needed,'handler_returned')
        plan=frame.advance(handler_returned=True)
        self.assertTrue(plan.complete);self.assertIs(frame.advance(),plan)

    def test_types_and_verification_limits(self):
        with self.assertRaises(ValueError):MessageToggleObservation(values={'compare_eax':True})
        with self.assertRaises(ValueError):MessageToggleObservation(normal_returns={'caption_compare':1})
        with self.assertRaises(ValueError):MessageToggleFrame(context=-1)
        plan=MessageToggleFrame().advance(sample())
        self.assertFalse(plan.caption_equality_verified);self.assertFalse(plan.native_execution_verified)
        self.assertFalse(plan.live_compatibility_verified)

if __name__=='__main__':unittest.main()
