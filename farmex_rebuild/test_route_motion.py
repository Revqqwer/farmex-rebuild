import unittest
from dataclasses import replace
from route_motion import RouteMotionObservation as Obs,plan_route_motion as plan
from route_resume import RouteResumeState as State,RouteResumeObservation as Read
from route_resume_paths import RouteResumePathObservation as Exit
from source_coin import GuardedDwordSample as Word,GuardedByteSample as Byte
from merchant_callback import MerchantCallbackObservation,tick_merchant_callback
from operation_engine import MerchantRunner,MerchantSettings,MerchantSnapshot

def condition(v):
    return Read(((0x553e7c,1),(0x554020,0x20)),Word(1,1,0x100),Byte(0x120,1,v))

class RouteMotionTests(unittest.TestCase):
    def mode0(self,metric=2,**kw):
        values=dict(global_samples=((0x561f58,0),(0x562004,20),(0x562000,10)),
                    route_flag574_byte=0,metric_ftol_dword=metric,tick_dword=1500,stamp_qword=0)
        values.update(kw);return Obs(**values)
    def mode2(self,metric=2,**kw):
        values=dict(global_samples=((0x561f58,1),(0x561f58,2),(0x56fa88,10),(0x56fa8c,20),
                                    (0x56fa8c,21),(0x56fa88,11)),metric_ftol_dword=metric)
        values.update(kw);return Obs(**values)
    def exit(self):return Exit(condition(1),condition(0))
    def move_globals(self):return ((0x561f7e,0),(0x553e7c,1),(0x554034,0x34))
    def test_mode0_integer_boundaries_delegate_timed(self):
        for metric in (0,1,71,0x7fffffff,0x80000000,0xffffffff):
            with self.subTest(metric=metric):
                d=plan(State(1,0),self.mode0(metric,resume=self.exit(),tick_dword=None,stamp_qword=None))
                self.assertTrue(d.complete);self.assertEqual(d.status,'exit_timed');self.assertEqual(d.state,State(0,1))
                self.assertIsNone(d.elapsed_signed)
    def test_mode0_inclusive_2_and_70_wait_without_exit(self):
        for metric in (2,70):
            d=plan(State(1,0),self.mode0(metric,tick_dword=1499))
            self.assertTrue(d.complete);self.assertEqual(d.status,'movement_wait_no_tail');self.assertIsNone(d.exit_plan)
    def test_clock_uses_full_signed_qword_not_low_dword(self):
        d=plan(State(1,0),self.mode0(tick_dword=0,stamp_qword=1<<32))
        self.assertTrue(d.complete);self.assertEqual(d.elapsed_signed,-(1<<32))
        self.assertEqual(d.status,'movement_wait_no_tail')
    def test_label_guard_skips_negative_index_and_requires_span_at_nonnegative(self):
        o=self.mode0(tick_dword=0,route_flag574_byte=1,route_index548_dword=0xffffffff)
        self.assertTrue(plan(State(1,0),o).complete)
        o=replace(o,route_index548_dword=0)
        d=plan(State(1,0),o);self.assertFalse(d.complete);self.assertIn('index/string/UI',d.missing)
        self.assertTrue(plan(State(1,0),replace(o,label_span_returned=True)).complete)
    def test_missing_flag_or_index_is_not_false(self):
        for kw in (dict(route_flag574_byte=None),dict(route_flag574_byte=1)):
            d=plan(State(1,0),self.mode0(**kw));self.assertFalse(d.complete)
    def test_mode_is_reread_before_second_comparison(self):
        d=plan(State(1,0),Obs(((0x561f58,2),(0x561f58,1)),resume=Exit(tail=condition(1))))
        self.assertTrue(d.complete);self.assertEqual(d.status,'exit_common');self.assertEqual(d.state,State(1,0))
        d=plan(State(1,0),Obs(((0x561f58,2),),resume=self.exit()))
        self.assertFalse(d.complete);self.assertIn('00561f58',d.missing)
    def test_mode2_zero_x_skips_y_and_geometry(self):
        d=plan(State(1,0),Obs(((0x561f58,1),(0x561f58,2),(0x56fa88,0)),resume=self.exit()))
        self.assertTrue(d.complete);self.assertEqual(d.status,'exit_optional');self.assertIsNone(d.metric_signed)
    def test_mode2_zero_y_skips_geometry(self):
        d=plan(State(1,0),Obs(((0x561f58,1),(0x561f58,2),(0x56fa88,1),(0x56fa8c,0)),resume=self.exit()))
        self.assertTrue(d.complete);self.assertEqual(d.status,'exit_optional')
    def test_mode2_metric_below_two_skips_lock_and_movement(self):
        d=plan(State(1,0),self.mode2(1,resume=self.exit()))
        self.assertTrue(d.complete);self.assertEqual(d.status,'exit_optional')
        self.assertEqual(d.global_reads[-2:],((0x56fa8c,21),(0x56fa88,11)))
    def test_coordinate_guard_values_do_not_replace_fresh_metric_reads(self):
        o=self.mode2();d=plan(State(1,0),replace(o,global_samples=o.global_samples[:4]))
        self.assertFalse(d.complete);self.assertIn('0056fa8c',d.missing)
    def test_lock_nonzero_skips_protected_reads_and_tail(self):
        for o in (self.mode0(),self.mode2()):
            o=replace(o,global_samples=o.global_samples+((0x561f7e,2),))
            d=plan(State(1,0),o);self.assertTrue(d.complete);self.assertEqual(d.status,'movement_locked')
            self.assertEqual(d.guarded_plans,());self.assertIsNone(d.exit_plan)
    def test_exact6_suppresses_move_but_other_values_do_not(self):
        for value in (0,6,7):
            o=self.mode0();o=replace(o,global_samples=o.global_samples+self.move_globals(),
                guarded_root=Word(1,1,0x100),guarded_value=Word(0x134,1,value))
            d=plan(State(1,0),o)
            self.assertEqual(d.complete,value==6)
            if value==6:self.assertEqual(d.status,'movement_field_exact6')
            else:self.assertIn('00562004',d.missing)
    def test_mode0_move_reloads_coordinates_and_returns_without_common_tail(self):
        o=self.mode0();o=replace(o,global_samples=o.global_samples+self.move_globals()+((0x562004,30),(0x562000,40)),
            guarded_root=Word(1,1,0x100),guarded_value=Word(0x134,1,0),move_helper_returned=True)
        d=plan(State(1,0),o);self.assertTrue(d.complete);self.assertEqual(d.status,'movement_return_no_tail')
        self.assertIsNone(d.exit_plan);self.assertEqual(d.state,State(1,0));self.assertEqual(d.writes,())
        self.assertIn(('004646b4','physical_push_y_x_signed_dwords',30,40),d.steps)
    def test_mode2_move_is_followed_by_optional_exit(self):
        o=self.mode2();o=replace(o,global_samples=o.global_samples+self.move_globals()+((0x56fa8c,30),(0x56fa88,40)),
            guarded_root=Word(1,1,0x100),guarded_value=Word(0x134,1,0),move_helper_returned=True,resume=self.exit())
        d=plan(State(1,0),o);self.assertTrue(d.complete);self.assertEqual(d.status,'exit_optional')
        self.assertEqual(d.state,State(0,1))
        d=plan(State(1,0),replace(o,move_helper_returned=None))
        self.assertFalse(d.complete);self.assertIsNone(d.exit_plan)
    def test_missing_exit_preserves_prospective_prefix_but_not_accepted_state(self):
        e=Exit(condition=condition(0),tick_dword=0,stamp_qword=0,limit_dword=0,
               compare_span_returned=True,comparison_al=0)
        d=plan(State(1,0),self.mode0(1,resume=e))
        self.assertFalse(d.complete);self.assertEqual(d.state,State(1,0));self.assertEqual(d.prospective_state,State(0,1))
        self.assertEqual(len(d.writes),2)
    def test_null_root_does_not_skip_second_guard(self):
        o=self.mode0();o=replace(o,global_samples=o.global_samples+((0x561f7e,0),(0x553e7c,0),(0x554034,0x34)),
            guarded_value=Word(0x34,1,6))
        d=plan(State(1,0),o);self.assertTrue(d.complete);self.assertEqual(d.status,'movement_field_exact6')
        self.assertEqual(len(d.guarded_plans),2)
    def test_missing_metric_and_mismatched_sample_addresses_do_not_advance(self):
        d=plan(State(1,0),self.mode0(metric_ftol_dword=None));self.assertFalse(d.complete)
        with self.assertRaises(ValueError):plan(State(1,0),Obs(((0x561f58,0),(0x562000,1)),route_flag574_byte=0))
    def test_own_exit_then_separately_observed_callback_can_advance_merchant(self):
        d=plan(State(1,0),self.mode0(1,resume=self.exit()));self.assertTrue(d.complete)
        r=MerchantRunner(MerchantSettings());r.start()
        # Callback entry pending was1 before the separately supplied route
        # helper normal return; post-enable is an explicit own fixture.
        callback=MerchantCallbackObservation(1,0,1,True,1,d.state.enable_byte,(1,))
        result=tick_merchant_callback(r,callback,MerchantSnapshot(101,currently_open=False))
        self.assertEqual(result.status,'callback_modeled');self.assertEqual(r.phase,1)
    def test_types_and_known_byte_width(self):
        for kw in (dict(metric_ftol_dword=True),dict(route_flag574_byte=256),dict(stamp_qword=-1),dict(label_span_returned=1)):
            with self.assertRaises(ValueError):Obs(**kw)
        o=self.mode0();o=replace(o,global_samples=o.global_samples+((0x561f7e,256),))
        with self.assertRaises(ValueError):plan(State(1,0),o)

if __name__=='__main__':unittest.main()
