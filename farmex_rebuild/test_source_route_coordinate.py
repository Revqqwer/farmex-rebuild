import unittest
from dataclasses import replace
from source_route_coordinate import RouteCoordinateObservation as Obs,plan_route_coordinate as plan
from source_route_step import SourceRouteStepObservation,plan_source_route_step
from route_start_state import RouteStartState
from route_resume import RouteResumeState
from route_progress import RouteProgressObservation,plan_route_progress
from source_coin import GuardedDwordSample as Word

class RouteCoordinateTests(unittest.TestCase):
    def sample(self,**kw):
        values=dict(comparison_span_returned=True,comparison_al=1,
            global_samples=((0x561f7e,8,0),(0x553e7c,32,1),(0x554034,32,0x34)),
            root_sample=Word(1,1,0x100),value_sample=Word(0x134,1,0),parse_span_returned=True,
            x_float_bits=0x3fc00000,y_float_bits=0xc0200000,metric_status_ah=0x40)
        values.update(kw);return Obs(**values)
    def bound(self,o,return_index=True):
        reads=((0x5e8,8,1),(0x5ec,32,0)) if return_index else ((0x5e8,8,1),)
        return SourceRouteStepObservation(reads,True,0,coordinate=o)
    def test_comparison_and_cleanup_are_independent(self):
        for kw in (dict(comparison_span_returned=None),dict(comparison_al=None)):
            p=plan(self.sample(**kw));self.assertFalse(p.complete);self.assertEqual(p.reads,())
    def test_false_comparison_does_not_finish_other_command(self):
        p=plan(self.sample(comparison_al=0));self.assertFalse(p.complete);self.assertEqual(p.status,'needs_command_body')
        self.assertFalse(p.clear_processing);self.assertEqual(p.reads,())
    def test_nonzero_comparison_and_lock_skip_all_unreached_getters(self):
        p=plan(Obs(True,2,((0x561f7e,8,3),)))
        self.assertTrue(p.complete);self.assertEqual(p.status,'coordinate_locked');self.assertFalse(p.clear_processing)
        self.assertEqual(p.guarded_plans,())
    def test_exact_dword6_blocks_but_other_dwords_reach_parse(self):
        p=plan(self.sample(value_sample=Word(0x134,1,6),parse_span_returned=None))
        self.assertTrue(p.complete);self.assertEqual(p.status,'coordinate_field_exact6')
        for value in (0,7,0x1000006):
            p=plan(self.sample(value_sample=Word(0x134,1,value),parse_span_returned=None))
            self.assertFalse(p.complete);self.assertIn('conversion span',p.missing)
    def test_null_root_and_failed_root_still_read_offset_and_second_getter(self):
        for globals_,root in ((((0x561f7e,8,0),(0x553e7c,32,0),(0x554034,32,0x34)),None),
                              (((0x561f7e,8,0),(0x553e7c,32,1),(0x554034,32,0x34)),Word(1,0))):
            p=plan(self.sample(global_samples=globals_,root_sample=root,value_sample=Word(0x34,1,6)))
            self.assertTrue(p.complete);self.assertEqual(len(p.guarded_plans),2)
            self.assertEqual(p.status,'coordinate_field_exact6')
    def test_wrapped_null_value_is_not_exact6_or_observed_value(self):
        p=plan(self.sample(root_sample=Word(1,1,0xffffffcc),value_sample=None,parse_span_returned=None))
        self.assertFalse(p.complete);self.assertEqual(p.guarded_plans[-1].status,'null_returns_zero')
    def test_less_equal_unordered_clear_without_move_receipt(self):
        for ah in (1,0x40,0x45):
            p=plan(self.sample(metric_status_ah=ah,move_returned=None))
            self.assertTrue(p.complete);self.assertTrue(p.clear_processing);self.assertEqual(p.status,'coordinate_step_clear')
            self.assertFalse(any(s[0]=='004646b4' for s in p.steps))
    def test_greater_uses_same_local_float_bits_for_metric_and_move(self):
        for ah in (0,0x80):
            p=plan(self.sample(metric_status_ah=ah,move_returned=True))
            self.assertTrue(p.complete);self.assertFalse(p.clear_processing)
            calls=[s for s in p.steps if s[0] in ('00460548','004646b4')]
            self.assertEqual(calls,[('00460548','physical_push_y_x_float_bits',0xc0200000,0x3fc00000),
                                    ('004646b4','physical_push_y_x_float_bits',0xc0200000,0x3fc00000)])
    def test_move_return_missing_does_not_clear_or_complete(self):
        p=plan(self.sample(metric_status_ah=0));self.assertFalse(p.complete);self.assertFalse(p.clear_processing)
        self.assertIn('coordinate normal return',p.missing)
    def test_parse_float_or_metric_gap_is_not_arrival(self):
        for kw in (dict(parse_span_returned=None),dict(x_float_bits=None),dict(y_float_bits=None),dict(metric_status_ah=None)):
            p=plan(self.sample(**kw));self.assertFalse(p.complete);self.assertFalse(p.clear_processing)
    def test_raw_nan_float_bits_not_rejected_or_approximated(self):
        p=plan(self.sample(x_float_bits=0x7fc00000,metric_status_ah=0x45))
        self.assertTrue(p.complete);self.assertTrue(p.clear_processing)
    def test_bound_clear_writes_only_processing_then_fresh_return(self):
        s=RouteStartState({0x5e8:1,0x5f4:7,0x5f8:999,0x5fc:4})
        p=plan_source_route_step(s,self.bound(self.sample()))
        self.assertTrue(p.complete);self.assertEqual(p.status,'coordinate_step_clear');self.assertEqual(p.return_dword,0)
        self.assertEqual(p.writes,(('object',0x5e8,1,0),))
        self.assertEqual(p.state.fields[0x5f4],7);self.assertEqual(p.state.fields[0x5f8],999)
    def test_bound_missing_return_retains_clear_only_as_prospective_write(self):
        s=RouteStartState({0x5e8:1})
        p=plan_source_route_step(s,self.bound(self.sample(),False))
        self.assertFalse(p.complete);self.assertEqual(p.state,s);self.assertEqual(p.prospective_state.fields[0x5e8],0)
    def test_bound_move_return_does_not_clear_outer_processing_gate(self):
        p=plan_source_route_step(RouteStartState({0x5e8:1}),self.bound(self.sample(metric_status_ah=0,move_returned=True)))
        samples=(('object',0x566,8,0),('object',0x567,8,0),('object',0x5f0,32,1),('object',0x5e8,8,1))
        outer=plan_route_progress(RouteResumeState(1,0),RouteProgressObservation(samples,step_execution=p))
        self.assertTrue(outer.complete);self.assertEqual(outer.status,'step_processing_no_motion');self.assertEqual(outer.writes,())
    def test_town_match_does_not_consume_incomplete_coordinate_observation(self):
        o=SourceRouteStepObservation(((0x5e8,8,1),(0x5f4,8,1),(0x5f8,32,100),(0x5fc,32,0),(0x5ec,32,0)),
            True,1,tick_dword=100,coordinate=Obs())
        p=plan_source_route_step(RouteStartState(),o)
        self.assertTrue(p.complete);self.assertIsNone(p.coordinate_plan)
    def test_types_order_and_missing_global(self):
        for kw in (dict(x_float_bits=-1),dict(metric_status_ah=True),dict(move_returned=1),dict(global_samples=((0x561f7e,8,256),))):
            with self.assertRaises(ValueError):Obs(**kw)
        with self.assertRaises(ValueError):plan(self.sample(global_samples=((0x553e7c,32,1),)))
        p=plan(self.sample(global_samples=()));self.assertFalse(p.complete);self.assertFalse(p.clear_processing)

if __name__=='__main__':unittest.main()
