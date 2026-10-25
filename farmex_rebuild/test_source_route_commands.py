import unittest
from dataclasses import replace,fields
from source_route_commands import SourceRouteCommandsObservation as Obs,plan_source_route_commands as plan
from source_route_step import SourceRouteStepObservation,plan_source_route_step
from source_route_coordinate import RouteCoordinateObservation
from route_resume import RouteResumeObservation
from route_start_state import RouteStartState
from source_coin import GuardedDwordSample as Word,GuardedByteSample as Byte
from special_routes import SpecialRouteSnapshot

def actor(value=0,ret=1):
    return RouteResumeObservation(((0x553e7c,1),(0x554020,0x20)),Word(1,1,0x100),Byte(0x120,ret,value))

class SourceRouteCommandsTests(unittest.TestCase):
    def wait(self,started=0,**kw):
        values=dict(samples=((0x5f4,8,started),),wait_comparison_returned=True,wait_comparison_al=1,tick_dword=100)
        values.update(kw);return Obs(**values)
    def posture(self,**kw):
        values=dict(samples=((0x5f4,8,0),),wait_comparison_returned=True,wait_comparison_al=0,
            posture_predicate_returned=True,posture_match_byte=1,actor=actor(),
            sit_comparison_returned=True,sit_comparison_al=0,
            stand_comparison_returned=True,stand_comparison_al=0,tick_dword=100)
        values.update(kw);return Obs(**values)
    def bound(self,o,return_index=True):
        samples=((0x5e8,8,1),(0x5ec,32,0)) if return_index else ((0x5e8,8,1),)
        return SourceRouteStepObservation(samples,True,0,coordinate=RouteCoordinateObservation(True,0),commands=o)
    def test_wait_start_does_not_parse_duration_yet(self):
        p=plan(self.wait())
        self.assertTrue(p.complete);self.assertEqual(p.status,'command_started')
        self.assertEqual(p.writes,(('object',0x5f8,4,100),('object',0x5fc,4,0),('object',0x5f4,1,1)))
        self.assertIsNone(p.threshold_signed)
    def test_initial_clock_gap_does_not_start(self):
        p=plan(self.wait(tick_dword=None));self.assertFalse(p.complete);self.assertEqual(p.writes,())
    def test_wait_due_equality_and_below_threshold(self):
        for tick,done in ((2099,False),(2100,True)):
            p=plan(self.wait(1,samples=((0x5f4,8,1),(0x5f8,32,100),(0x5fc,32,0)),
                seconds_parse_returned=True,seconds_dword=2,tick_dword=tick))
            self.assertTrue(p.complete);self.assertEqual(len(p.writes),2 if done else 0)
            self.assertEqual(p.threshold_signed,2000)
    def test_negative_and_overflow_duration_uses_low32_signed_product(self):
        for seconds,threshold in ((0xffffffff,-1000),(2147484,-2147483296),(0,0)):
            p=plan(self.wait(1,samples=((0x5f4,8,1),(0x5f8,32,100),(0x5fc,32,0)),
                seconds_parse_returned=True,seconds_dword=seconds))
            self.assertTrue(p.complete);self.assertEqual(p.threshold_signed,threshold);self.assertEqual(p.status,'command_step_cleared')
    def test_full_qword_stamp_not_low_dword_only(self):
        p=plan(self.wait(1,samples=((0x5f4,8,1),(0x5f8,32,0),(0x5fc,32,1)),seconds_parse_returned=True,seconds_dword=0))
        self.assertTrue(p.complete);self.assertLess(p.elapsed_signed,0);self.assertEqual(p.writes,())
    def test_wait_parser_and_result_are_independent(self):
        for kw in (dict(seconds_parse_returned=None,seconds_dword=2),dict(seconds_parse_returned=True,seconds_dword=None)):
            p=plan(self.wait(1,**kw));self.assertFalse(p.complete);self.assertEqual(p.writes,())
    def test_next_command_not_prematurely_completed(self):
        p=plan(self.posture(posture_match_byte=0,samples=()))
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_command_body');self.assertEqual(p.reads,())
    def test_posture_wait_skips_actor_and_fresh_action_comparisons(self):
        p=plan(self.posture(samples=((0x5f4,8,2),(0x5f8,32,100),(0x5fc,32,0)),
            actor=RouteResumeObservation(),sit_comparison_returned=None,stand_comparison_returned=None,tick_dword=2100))
        self.assertTrue(p.complete);self.assertEqual(p.status,'command_step_cleared');self.assertIsNone(p.actor_plan)
    def test_actor_nonzero_blocks_without_calls_or_clock(self):
        p=plan(self.posture(actor=actor(1),sit_comparison_returned=None,stand_comparison_returned=None,tick_dword=None))
        self.assertTrue(p.complete);self.assertEqual(p.status,'posture_actor_blocked');self.assertEqual(p.writes,())
    def test_actor_tests_al_and_keeps_guarded_provenance(self):
        p=plan(self.posture(actor=actor(0,0x100)))
        self.assertTrue(p.complete);self.assertEqual(p.actor_plan.byte_plan.eax_dword,0x100)
        self.assertEqual(p.status,'command_started')
    def test_both_fresh_comparisons_can_be_false_after_predicate_match(self):
        p=plan(self.posture());self.assertTrue(p.complete);self.assertEqual(p.status,'command_started')
        self.assertFalse(any(s[1] in ('00465de0 normal return','00465e50 normal return') for s in p.steps if len(s)>1))
    def test_both_fresh_comparisons_can_trigger_separate_actions(self):
        p=plan(self.posture(sit_comparison_al=1,sit_returned=True,stand_comparison_al=2,stand_returned=True))
        self.assertTrue(p.complete)
        actions=[s[1] for s in p.steps if s[0]=='normal_return' and s[1].startswith(('00465de0','00465e50'))]
        self.assertEqual(actions,['00465de0 normal return','00465e50 normal return'])
    def test_separate_action_receipts_do_not_get_substituted(self):
        for kw in (dict(sit_comparison_al=1),dict(stand_comparison_al=1)):
            p=plan(self.posture(**kw));self.assertFalse(p.complete);self.assertEqual(p.writes,())
    def test_missing_actor_does_not_become_clear(self):
        p=plan(self.posture(actor=RouteResumeObservation()));self.assertFalse(p.complete);self.assertEqual(p.writes,())
    def test_bound_wait_clear_applies_flags_before_fresh_return(self):
        o=self.wait(1,samples=((0x5f4,8,1),(0x5f8,32,100),(0x5fc,32,0)),seconds_parse_returned=True,seconds_dword=0)
        p=plan_source_route_step(RouteStartState({0x5e8:1,0x5f4:1}),self.bound(o))
        self.assertTrue(p.complete);self.assertEqual(p.state.fields[0x5e8],0);self.assertEqual(p.return_dword,0)
        p=plan_source_route_step(RouteStartState({0x5e8:1,0x5f4:1}),self.bound(o,False))
        self.assertFalse(p.complete);self.assertEqual(p.state.fields[0x5e8],1);self.assertEqual(p.prospective_state.fields[0x5e8],0)
    def test_coordinate_parser_gap_does_not_skip_to_other_commands(self):
        o=self.bound(self.wait());o=replace(o,coordinate=RouteCoordinateObservation(True,1))
        p=plan_source_route_step(RouteStartState(),o)
        self.assertFalse(p.complete);self.assertIsNone(p.command_plan)
    def test_generic_route_snapshot_uses_verified_offset_identifier(self):
        names={f.name for f in fields(SpecialRouteSnapshot)}
        self.assertIn('actor_raw_byte_554020',names);self.assertNotIn('actor_raw_byte_55402c',names)
    def test_normalized_predicate_widths_and_read_order(self):
        for kw in (dict(posture_match_byte=2),dict(seconds_dword=-1),dict(sit_returned=1)):
            with self.assertRaises(ValueError):Obs(**kw)
        with self.assertRaises(ValueError):plan(self.wait(samples=((0x5f4,32,0),)))

if __name__=='__main__':unittest.main()
