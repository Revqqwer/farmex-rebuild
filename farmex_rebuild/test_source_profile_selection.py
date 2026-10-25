import unittest
from dataclasses import replace
from source_profile_selection import *

def detection(**kw):return replace(ProfileDetectionObservation(0,{'file_exists':True,'candidate_cleanup':True,'detection_cleanup':True}),**kw)
def selection(**kw):return replace(ProfileSelectionObservation(detector_eax=1,use_owned_mode_reads=True,
    helper_returns={'detect_profile':True,'current_steam_initializer':True,'current_us_initializer':True}),**kw)

class ProfileDetectionTests(unittest.TestCase):
    def test_file_exists_low_al_selects_mode_without_path_or_profile_default(self):
        for eax,mode in ((0,1),(0x100,1),(1,2),(0x1234ff,2)):
            p=plan_profile_detection_tail(detection(file_exists_eax=eax))
            self.assertTrue(p.complete);self.assertEqual(p.mode_dword,mode)
            self.assertFalse(p.native_execution_verified)
        p=plan_profile_detection_tail(ProfileDetectionObservation())
        self.assertFalse(p.complete);self.assertIsNone(p.mode_dword)

    def test_file_exists_result_and_both_cleanup_returns_are_separate(self):
        p=plan_profile_detection_tail(detection(file_exists_eax=None))
        self.assertEqual(p.missing,'FileExists EAX')
        for label in ('file_exists','candidate_cleanup','detection_cleanup'):
            p=plan_profile_detection_tail(detection(helper_returns={**detection().helper_returns,label:False}))
            self.assertFalse(p.complete);self.assertEqual(p.missing,label+' normal return')
        with self.assertRaises(ValueError):ProfileDetectionPlan(True,None)

class ProfileSelectionTests(unittest.TestCase):
    def test_us_and_steam_project_current_not_historical_sender_values(self):
        for mode,profile,context,target,version in ((1,'current_us',0x1128a94,0x70b360,0x1009d4),(2,'current_steam',0x11eaa84,0x6241a0,0x10097f)):
            p=plan_profile_sender_selection(selection(detector_eax=mode))
            self.assertTrue(p.complete);self.assertEqual(p.selected_tables,(profile,))
            self.assertEqual(dict(p.projected_sender_globals),{0x553e84:context,0x553e90:target})
            self.assertEqual(p.stores[:2],((0x553e46,1,mode),(0x553e48,4,version)))
            self.assertFalse(p.full_initializer_verified or p.native_execution_verified)

    def test_parent_stores_only_low_byte_then_requires_two_fresh_mode_reads(self):
        p=plan_profile_sender_selection(selection(detector_eax=0x10001,use_owned_mode_reads=False))
        self.assertFalse(p.complete);self.assertEqual(p.stores,((0x553e46,1,1),))
        self.assertEqual(p.missing,'current_steam mode BYTE')
        p=plan_profile_sender_selection(selection(use_owned_mode_reads=False,mode_read_steam=0))
        self.assertEqual(p.missing,'current_us mode BYTE')

    def test_observed_mode_can_change_between_tests_and_both_tables_run_in_order(self):
        p=plan_profile_sender_selection(selection(use_owned_mode_reads=False,mode_read_steam=2,mode_read_us=1))
        self.assertTrue(p.complete);self.assertEqual(p.selected_tables,('current_steam','current_us'))
        self.assertEqual(dict(p.projected_sender_globals)[0x553e90],0x70b360)
        self.assertEqual([s[2] for s in p.stores if s[0]==0x553e48],[0x10097f,0x1009d4])

    def test_other_mode_does_not_guess_prior_sender_globals(self):
        p=plan_profile_sender_selection(selection(detector_eax=255))
        self.assertTrue(p.complete);self.assertEqual(p.selected_tables,());self.assertEqual(p.projected_sender_globals,())
        self.assertEqual(p.stores,((0x553e46,1,255),))

    def test_constructor_normal_return_does_not_follow_from_projected_stores(self):
        p=plan_profile_sender_selection(selection(helper_returns={'detect_profile':True}))
        self.assertFalse(p.complete);self.assertEqual(p.missing,'current_us_initializer normal return')
        self.assertEqual(dict(p.projected_sender_globals)[0x553e90],0x70b360)
        # Prospective projection is retained as evidence, not a complete initializer.
        self.assertFalse(p.full_initializer_verified)

    def test_bound_detector_and_parent_return_cannot_bypass_missing_child_cleanup(self):
        child=plan_profile_detection_tail(detection(helper_returns={'file_exists':True,'candidate_cleanup':True}))
        p=plan_profile_sender_selection(selection(detector_eax=None,detection=child))
        self.assertFalse(p.complete);self.assertIn('bound detection',p.missing);self.assertEqual(p.stores,())
        child=plan_profile_detection_tail(detection(file_exists_eax=1))
        p=plan_profile_sender_selection(selection(detector_eax=None,detection=child,helper_returns={}))
        self.assertEqual(p.missing,'detect_profile normal return');self.assertEqual(p.stores,())
        p=plan_profile_sender_selection(selection(detector_eax=None,detection=child))
        self.assertTrue(p.complete);self.assertEqual(p.selected_tables,('current_steam',))

    def test_conflicting_modes_and_raw_values_are_not_silently_preferred(self):
        with self.assertRaises(ValueError):plan_profile_sender_selection(selection(mode_read_steam=2))
        with self.assertRaises(ValueError):plan_profile_sender_selection(selection(detection=plan_profile_detection_tail(detection())))
        with self.assertRaises(ValueError):ProfileSelectionObservation(mode_read_us=256)
        with self.assertRaises(ValueError):ProfileDetectionObservation(file_exists_eax=True)

if __name__=='__main__':unittest.main()
