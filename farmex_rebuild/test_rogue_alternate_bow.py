import unittest
from dataclasses import replace
from rogue_attack import RogueSnapshot,BOW_ROWS
from rogue_alternate_bow import AlternateBowObservation,plan_alternate_bow
from attack_configuration import RogueAlternateBowRanges,rogue_alternate_bow_ranges
import test_attack_configuration as configuration_fixture

class AlternateBowTests(unittest.TestCase):
    def setUp(self):
        self.flags={r.flag_offset:False for r in BOW_ROWS};self.flags.update({0x89:False,0x91:False})
        self.s=RogueSnapshot(0,5,45,1000,self.flags,{'00462ddc':100,'00462670':100})
        self.r=RogueAlternateBowRanges(5,5,5)
        self.o=AlternateBowObservation(0,0,0,prefix_first=102,helper_returns={r.skill_number:0 for r in BOW_ROWS})
    def plan(self,s=None,r=None,o=None):return plan_alternate_bow(s or self.s,r or self.r,o or self.o)
    def test_combo_equality_and_noncombo_strict_boundary(self):
        self.flags[0x91]=True
        o=replace(self.o,helper_returns={0x22b:0})
        self.assertEqual(self.plan(o=o).source_return,0)
        p=self.plan(o=replace(o,byte_562011=1,byte_562012=None))
        self.assertEqual((p.skill_number,p.category,p.source_return),(0x22b,1,1))
        self.assertEqual(self.plan(r=replace(self.r,quintuple=6),o=o).skill_number,0x22b)
    def test_combo_mp200_noncombo150_and_fallback_to_triple(self):
        self.flags.update({0x91:True,0x89:True})
        o=replace(self.o,helper_returns={0x22b:0,0x203:0})
        r=RogueAlternateBowRanges(6,6,6)
        for mp,combo,skill in ((150,0,0x22b),(199,1,0x203),(200,1,0x22b)):
            with self.subTest(mp=mp,combo=combo):
                self.assertEqual(self.plan(replace(self.s,mp=mp),r,replace(o,byte_562012=combo)).skill_number,skill)
    def test_raw_helper_uses_low_byte_and_priority(self):
        self.flags.update({0x91:True,0x89:True})
        o=replace(self.o,byte_562011=1,helper_returns={0x22b:0x100,0x203:0})
        self.assertEqual(self.plan(o=o).category,1)
        self.assertEqual(self.plan(o=replace(o,helper_returns={0x22b:1,0x203:0})).category,2)
    def test_all_ordinary_rows_thresholds_without_timer(self):
        for index,row in enumerate(BOW_ROWS):
            with self.subTest(flag=row.flag_offset):
                flags=dict(self.flags);flags[row.flag_offset]=True
                s=replace(self.s,flags=flags,mp=row.mp_minimum or 0,raw_stats={row.stat_reader:row.stat_minimum})
                helpers={8 if row.flag_offset==0x85 else row.skill_number:0}
                p=self.plan(s=s,o=replace(self.o,helper_returns=helpers))
                self.assertEqual((p.category,p.skill_number),(3,8 if row.flag_offset==0x85 else row.skill_number))
                low=replace(s,raw_stats={row.stat_reader:row.stat_minimum-1})
                self.assertEqual(self.plan(s=low,o=replace(self.o,helper_returns=helpers)).source_return,0)
                if row.mp_minimum:
                    self.assertEqual(self.plan(s=replace(s,mp=row.mp_minimum-1),o=replace(self.o,helper_returns=helpers)).source_return,0)
    def test_outer_equality_skips_ordinary_but_accepts_combo(self):
        self.flags[0x84]=True
        self.assertEqual(self.plan(s=replace(self.s,distance=45)).source_return,0)
        self.assertEqual(self.plan(s=replace(self.s,distance=45.01)).status,'out_of_range')
        self.flags[0x91]=True
        self.assertEqual(self.plan(replace(self.s,distance=45),replace(self.r,combo=45),replace(self.o,byte_562011=1,helper_returns={0x22b:0})).category,1)
    def test_prefix_is_reread_only_when_first_is_not102(self):
        self.flags[0x85]=True
        for first,second,expected,calls in ((102,None,8,1),(202,0,7,2),(0,202,8,2)):
            o=replace(self.o,prefix_first=first,prefix_second=second,helper_returns={7:0,8:0})
            p=self.plan(o=o)
            self.assertEqual(p.skill_number,expected)
            self.assertEqual(sum(h=='0046256c' for h,args in p.calls),calls)
    def test_send_zero_keeps_prior_lock_plan(self):
        self.flags[0x84]=True
        for returned,wanted in ((0,0),(1,3),(0x100,3)):
            p=self.plan(o=replace(self.o,execute_byte=255,target_id=0,send_return=returned))
            self.assertEqual(p.local_writes,(('00561f7e',1),))
            self.assertEqual(p.calls[-1],('004655e8',(3,0)))
            self.assertEqual(p.source_return,wanted)
            self.assertFalse(p.independently_verified)
    def test_unknown_send_preserves_prefix_without_claimed_return(self):
        self.flags[0x84]=True
        p=self.plan(o=replace(self.o,execute_byte=1))
        self.assertEqual((p.status,p.reason),('needs_observation','target_id'))
        self.assertEqual(p.local_writes,(('00561f7e',1),));self.assertIsNone(p.source_return)
    def test_unknown_first_branch_blocks_lower_candidates(self):
        self.flags.update({0x91:True,0x84:True})
        p=self.plan(o=replace(self.o,byte_562011=1))
        self.assertEqual(p.status,'needs_observation');self.assertIsNone(p.skill_number)
    def test_signed_mp_and_negative_radius_are_not_clamped(self):
        self.flags[0x91]=True
        o=replace(self.o,byte_562011=1,helper_returns={0x22b:0})
        self.assertEqual(self.plan(s=replace(self.s,mp=0xffffffff),o=o).source_return,0)
        self.assertEqual(self.plan(s=replace(self.s,configured_range=-1)).status,'out_of_range')
    def test_invalid_raw_types_rejected(self):
        for values in ({'execute_byte':True},{'byte_562011':256},{'send_return':-1},{'helper_returns':{3:False}}):
            with self.subTest(values=values),self.assertRaises(ValueError):AlternateBowObservation(**values)
    def test_compiled_combo_parameter_reaches_actual_selection(self):
        fixture=configuration_fixture.AttackConfigurationTests();fixture.setUp()
        fixture.set_field('rogue','integers',0x18,'4')
        self.flags[0x91]=True
        o=replace(self.o,byte_562011=1,helper_returns={0x22b:0})
        self.assertEqual(self.plan(r=rogue_alternate_bow_ranges(fixture.config('rogue')),o=o).source_return,0)
        fixture.set_field('rogue','integers',0x18,'5')
        self.assertEqual(self.plan(r=rogue_alternate_bow_ranges(fixture.config('rogue')),o=o).category,1)
