import unittest
from dataclasses import replace
from target_branches import LeaderTargetObservation as O,plan_target_branch

class LeaderTargetTests(unittest.TestCase):
    def observation(self,**changes):return replace(O(1,0,2,7,0x110000,11,0x120000,0,100,50),**changes)
    def plan(self,**changes):return plan_target_branch(4,self.observation(**changes))
    def test_outer_guard_skips_all_helper_reads(self):
        self.assertEqual(plan_target_branch(4,O(enabled_38=0)).calls,())
    def test_party_count_is_signed_and_less_than_two_does_not_clear(self):
        for count in (0,1,0xffffffff):
            result=self.plan(party_count_dword=count)
            self.assertEqual(result.status,'local_no_write');self.assertEqual(result.writes,())
    def test_missing_leader_or_target_pointer_clears_three_fields(self):
        for changes in ({'leader_pointer':0},{'target_pointer':0}):
            self.assertEqual(dict(self.plan(**changes).writes),{0x118:0,0x108:0,0x10c:0})
    def test_zero_leader_target_id_is_not_early_rejected(self):
        result=self.plan(leader_target_id=0)
        self.assertIn(('00464a10',(0,)),result.calls)
        self.assertEqual(dict(result.writes)[0x10c],0)
    def test_within_or_equal_radius_does_not_use_hp_values(self):
        for ah in (0,0x40):
            result=self.plan(comparison_ah=ah,maximum_hp_dword=None,current_hp_dword=None)
            self.assertEqual(result.status,'local_write_plan')
            self.assertEqual(dict(result.writes),{0x108:0x120000,0x10c:11,0x118:1})
    def test_outside_radius_dead_low_words_clear(self):
        self.assertEqual(self.plan(comparison_ah=1,maximum_hp_dword=0x10001,current_hp_dword=0x10000).status,'local_clear_plan')
    def test_outside_radius_other_hp_combinations_do_not_clear(self):
        for maximum,current in ((0,0),(0x10000,0),(100,1)):
            self.assertEqual(self.plan(comparison_ah=1,maximum_hp_dword=maximum,current_hp_dword=current).writes,())
    def test_unordered_fcom_takes_outside_path(self):
        self.assertEqual(self.plan(comparison_ah=0x45,maximum_hp_dword=100,current_hp_dword=0).status,'local_clear_plan')
    def test_unknown_status_is_not_guessed_from_health(self):
        result=self.plan(comparison_ah=None,current_hp_dword=0)
        self.assertEqual(result.status,'needs_observation');self.assertEqual(result.writes,())
    def test_missing_ignored_current_word_is_not_required(self):
        self.assertEqual(self.plan(comparison_ah=1,maximum_hp_dword=0,current_hp_dword=None).status,'local_no_write')
