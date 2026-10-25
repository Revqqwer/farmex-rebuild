import unittest
from target_branches import TargetBranchObservation as O,plan_target_branch

class TargetBranchTests(unittest.TestCase):
    def test_outer_gate_skips_without_helper_reads(self):
        self.assertEqual(plan_target_branch(1,O(enabled_38=0)).calls,())
        self.assertEqual(plan_target_branch(5,O(1,1)).status,'outer_skipped')
    def test_manual_repeated_ids_are_not_forced_equal(self):
        result=plan_target_branch(1,O(1,0,(11,12,13),0x100000,1))
        self.assertEqual(result.calls,(('00462630',()),('00462630',()),('00464a10',(12,)),('00464c2c',(0x100000,)),('00462630',())))
        self.assertEqual(result.writes,((0x108,0x100000),(0x10c,13),(0x118,1)))
    def test_manual_zero_pointer_or_visibility_clears(self):
        for observation in (O(1,0,(11,12),0),O(1,0,(11,12),0x100000,0)):
            result=plan_target_branch(1,observation)
            self.assertEqual(dict(result.writes),{0x118:0,0x108:0,0x10c:0})
    def test_initial_zero_does_not_need_later_reads(self):
        self.assertEqual(plan_target_branch(1,O(1,0,(0,))).status,'local_clear_plan')
        self.assertEqual(plan_target_branch(5,O(1,0,(0,),autoz_state=1)).status,'local_clear_plan')
    def test_unknown_final_manual_id_keeps_only_known_prefix_plan(self):
        result=plan_target_branch(1,O(1,0,(11,12),0x100000,1))
        self.assertEqual(result.status,'needs_observation');self.assertEqual(result.writes,((0x108,0x100000),))
    def test_autoz_zero_lookup_still_plans_source_ready_one(self):
        result=plan_target_branch(5,O(1,0,(11,12),0,autoz_state=1))
        self.assertEqual(result.writes,((0x10c,12),(0x108,0),(0x118,1)))
        self.assertFalse(result.independently_verified)
    def test_autoz_refresh_return_is_not_invented(self):
        result=plan_target_branch(5,O(1,0,autoz_state=0))
        self.assertEqual(result.status,'needs_observation')
        self.assertEqual(result.calls[-1],('00464b2c',()))
        result=plan_target_branch(5,O(1,0,(11,12),0x100000,autoz_state=0,refresh_returned=True))
        self.assertEqual(result.status,'local_write_plan')
    def test_no_unrelated_scratch_field_writes(self):
        result=plan_target_branch(1,O(1,0,(0,)))
        self.assertNotIn(0x110,dict(result.writes));self.assertNotIn(0x114,dict(result.writes))
    def test_last_manual_read_zero_is_not_corrected_to_initial_id(self):
        result=plan_target_branch(1,O(1,0,(11,12,0),0x100000,1))
        self.assertEqual(dict(result.writes),{0x108:0x100000,0x10c:0,0x118:1})
