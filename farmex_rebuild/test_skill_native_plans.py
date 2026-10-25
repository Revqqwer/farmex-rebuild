import unittest
from skill_native_plans import SOURCE_GLOBALS,SkillObservation,plan_alternate_skill

class SkillNativeTests(unittest.TestCase):
    def observation(self,profile='us',**changes):
        globals=dict(SOURCE_GLOBALS[profile])
        words={globals[0x553e80]:0x100000,0x100000+globals[0x5540a0]:0x200000}
        if profile=='steam':words[globals[0x553eb8]]=0x300000
        values=dict(action_id=0x77a20,actor_id=0x12345678,globals=globals,direct_words=words,lookup_return=0x400000)
        values.update(changes);return SkillObservation(**values)

    def test_us_lookup_does_not_invent_ecx(self):
        result=plan_alternate_skill(self.observation())
        self.assertIsNone(result.calls[0].ecx)
        self.assertEqual(result.calls[0].push_order,(0x77a20,))
        self.assertEqual(result.reads,(0x111563c,0x100468))

    def test_steam_lookup_reads_context_before_ui_root(self):
        result=plan_alternate_skill(self.observation('steam'))
        self.assertEqual(result.calls[0].ecx,0x300000)
        self.assertEqual(result.reads,(0x11ea50c,0x11ebab0,0x1004a8))

    def test_actor_stays_full_dword_and_push_order_is_preserved(self):
        result=plan_alternate_skill(self.observation())
        self.assertEqual(result.calls[1].push_order,(0x400000,0x12345678))
        self.assertEqual(result.calls[1].ecx,0x200000)
        self.assertEqual([c.assumed_callee_cleanup_bytes for c in result.calls],[4,8])
        self.assertTrue(all(not c.abi_verified for c in result.calls))

    def test_zero_lookup_is_not_an_early_return(self):
        result=plan_alternate_skill(self.observation(lookup_return=0))
        self.assertEqual(len(result.calls),2);self.assertEqual(result.calls[1].push_order[0],0)

    def test_modes_other_than_one_and_two_skip_lookup_only(self):
        for mode in (0,3,255):
            obs=self.observation();globals=dict(obs.globals);globals[0x553e46]=mode
            result=plan_alternate_skill(self.observation(globals=globals,lookup_return=None))
            self.assertEqual(len(result.calls),1);self.assertEqual(result.calls[0].push_order[0],0)

    def test_missing_lookup_return_does_not_invent_pointer(self):
        result=plan_alternate_skill(self.observation(lookup_return=None))
        self.assertEqual(result.status,'needs_observation');self.assertEqual(len(result.calls),1)
        self.assertEqual(result.reads,())

    def test_missing_context_does_not_turn_into_zero(self):
        result=plan_alternate_skill(self.observation(direct_words={0x111563c:0x100000}))
        self.assertEqual(result.status,'needs_observation');self.assertEqual(len(result.calls),1)

    def test_native_zero_and_nonzero_results_are_only_local_observations(self):
        for value in (0,1,256,0xffffffff):
            result=plan_alternate_skill(self.observation(native_return=value))
            self.assertEqual(result.returned_nonzero,value!=0)
            self.assertFalse(result.independently_verified)

    def test_unknown_native_return_does_not_become_success(self):
        self.assertIsNone(plan_alternate_skill(self.observation()).returned_nonzero)

    def test_zero_targets_remain_unverified_operand_plans(self):
        obs=self.observation();globals=dict(obs.globals);globals[0x553ebc]=globals[0x553ee4]=0
        result=plan_alternate_skill(self.observation(globals=globals))
        self.assertEqual([c.target for c in result.calls],[0,0])
        self.assertTrue(all(not c.abi_verified for c in result.calls))

    def test_context_address_addition_wraps_as_dword(self):
        obs=self.observation();globals=dict(obs.globals);globals[0x5540a0]=0x30
        result=plan_alternate_skill(self.observation(globals=globals,direct_words={0x111563c:0xfffffff0,0x20:0x200000}))
        self.assertEqual(result.reads[-1],0x20)

    def test_mode_byte_and_raw_types_are_checked(self):
        obs=self.observation();globals=dict(obs.globals);globals[0x553e46]=256
        with self.assertRaises(ValueError):self.observation(globals=globals)
        with self.assertRaises(ValueError):self.observation(actor_id=True)
        with self.assertRaises(ValueError):self.observation(lookup_return=-1)
