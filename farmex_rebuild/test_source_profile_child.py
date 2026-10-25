import unittest
from dataclasses import replace
from source_profile_selection import *
from test_source_profile_selection import detection,selection

class ProfileChildTests(unittest.TestCase):
    def test_changed_mode_cannot_select_opposite_initializer(self):
        child=plan_profile_detection_tail(detection(file_exists_eax=0))
        with self.assertRaises(ValueError):plan_profile_sender_selection(selection(detector_eax=None,detection=replace(child,mode_dword=2)))

    def test_changed_calls_and_verification_claims_reject_before_parent_stores(self):
        child=plan_profile_detection_tail(detection())
        for altered in (replace(child,calls=()),replace(child,native_execution_verified=True)):
            with self.assertRaises(ValueError):plan_profile_sender_selection(selection(detector_eax=None,detection=altered))

    def test_handwritten_complete_child_without_input_is_not_generated_evidence(self):
        child=ProfileDetectionPlan(True,1)
        with self.assertRaises(ValueError):plan_profile_sender_selection(selection(detector_eax=None,detection=child))

    def test_missing_cleanup_cannot_be_relabelled_complete(self):
        child=plan_profile_detection_tail(detection(helper_returns={'file_exists':True,'candidate_cleanup':True}))
        forged=replace(child,complete=True,missing='')
        with self.assertRaises(ValueError):plan_profile_sender_selection(selection(detector_eax=None,detection=forged))

    def test_valid_generated_child_retains_raw_AL_semantics_and_outer_return_boundary(self):
        child=plan_profile_detection_tail(detection(file_exists_eax=0x100))
        p=plan_profile_sender_selection(selection(detector_eax=None,detection=child))
        self.assertTrue(p.complete);self.assertEqual(p.selected_tables,('current_us',))
        p=plan_profile_sender_selection(selection(detector_eax=None,detection=child,helper_returns={}))
        self.assertFalse(p.complete);self.assertEqual(p.stores,())
        self.assertEqual(p.missing,'detect_profile normal return')

if __name__=='__main__':unittest.main()
