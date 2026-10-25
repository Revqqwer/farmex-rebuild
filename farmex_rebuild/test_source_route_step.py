import unittest
from dataclasses import replace
from source_route_step import SourceRouteStepObservation as Obs,plan_source_route_step as plan
from route_start_state import RouteStartState as State,RouteStartFrame,RouteStartObservation
from route_resume import RouteResumeState,RouteResumeObservation
from route_resume_paths import RouteResumePathObservation
from route_motion import RouteMotionObservation
from route_progress import RouteProgressObservation,plan_route_progress
from source_coin import GuardedDwordSample as Word,GuardedByteSample as Byte
from merchant_callback import MerchantCallbackObservation,tick_merchant_callback
from operation_engine import MerchantRunner,MerchantSettings,MerchantSnapshot

def D(a,v):return (a,32,v)
def B(a,v):return (a,8,v)

class SourceRouteStepTests(unittest.TestCase):
    def town(self,**kw):
        values=dict(samples=(B(0x5e8,1),B(0x5f4,0),D(0x5ec,0)),comparison_span_returned=True,
            comparison_al=1,reset_helper_returned=True,max_hp_dword=100,hp_dword=50,
            town_helper_returned=True,tick_dword=100)
        values.update(kw);return Obs(**values)
    def test_cursor_arms_and_resets_without_parsing_command(self):
        s=State({0x5ec:0xffffffff,0x5e8:0,0x5f4:7,0x5f8:999,0x5fc:4})
        o=Obs((B(0x5e8,0),D(0x5f0,1),D(0x5ec,0xffffffff),D(0x5ec,0xffffffff),D(0x5ec,0)))
        p=plan(s,o);self.assertTrue(p.complete);self.assertEqual(p.status,'cursor_armed');self.assertEqual(p.return_dword,0)
        self.assertEqual([r[1:] for r in p.writes],[(0x5ec,4,0),(0x5e8,1,1),(0x5f4,1,0),(0x5f8,4,0),(0x5fc,4,0)])
    def test_cursor_empty_count_wrap_and_fresh_return_are_preserved(self):
        p=plan(State(),Obs((B(0x5e8,0),D(0x5f0,0),D(0x5ec,0xffffffff),D(0x5ec,4))))
        self.assertTrue(p.complete);self.assertEqual(p.status,'cursor_at_last');self.assertEqual(p.return_dword,4)
        self.assertEqual(p.writes,())
    def test_increment_uses_its_own_fresh_index(self):
        p=plan(State(),Obs((B(0x5e8,0),D(0x5f0,2),D(0x5ec,0),D(0x5ec,5),D(0x5ec,6))))
        self.assertEqual(p.state.fields[0x5ec],6);self.assertEqual(p.return_dword,6)
    def test_missing_return_index_does_not_complete_after_known_writes(self):
        p=plan(State(),Obs((B(0x5e8,0),D(0x5f0,1),D(0x5ec,0xffffffff),D(0x5ec,0xffffffff))))
        self.assertFalse(p.complete);self.assertEqual(len(p.writes),5);self.assertEqual(p.state,State())
        self.assertEqual(p.prospective_state.fields[0x5ec],0);self.assertIsNone(p.return_dword)
    def test_comparison_cleanup_receipt_is_separate_from_al(self):
        p=plan(State(),self.town(comparison_span_returned=None))
        self.assertFalse(p.complete);self.assertEqual(p.writes,())
        p=plan(State(),self.town(comparison_al=None));self.assertFalse(p.complete)
    def test_non_town_body_is_not_treated_as_unknown_command_completion(self):
        p=plan(State(),self.town(comparison_al=0))
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_command_body');self.assertIsNone(p.return_dword)
    def test_health_below_threshold_skips_town_and_clock(self):
        p=plan(State(),self.town(hp_dword=49,town_helper_returned=None,tick_dword=None))
        self.assertTrue(p.complete);self.assertEqual(p.status,'town_health_wait');self.assertEqual(p.health_threshold_signed,50)
        self.assertEqual(p.writes,())
    def test_health_equality_starts_with_separate_clock_and_started_write(self):
        p=plan(State(),self.town())
        self.assertTrue(p.complete);self.assertEqual(p.status,'town_started')
        self.assertEqual(p.writes,(('object',0x5f8,4,100),('object',0x5fc,4,0),('object',0x5f4,1,1)))
    def test_health_low32_product_and_signed_truncation(self):
        cases=((0xffffffff,0xffffffff,0),(0x40000001,0xffffffff,-21474835),(3,1,1))
        for maximum,hp,threshold in cases:
            p=plan(State(),self.town(max_hp_dword=maximum,hp_dword=hp))
            self.assertTrue(p.complete);self.assertEqual(p.health_threshold_signed,threshold)
    def test_reset_health_and_town_return_gaps_do_not_become_success(self):
        for kw in (dict(reset_helper_returned=None),dict(max_hp_dword=None),dict(hp_dword=None),dict(town_helper_returned=None)):
            p=plan(State(),self.town(**kw));self.assertFalse(p.complete);self.assertEqual(p.writes,())
        p=plan(State(),self.town(tick_dword=None));self.assertFalse(p.complete);self.assertEqual(p.writes,())
    def test_wait_2000_boundary_and_full_qword_stamp(self):
        for tick,low,high,done in ((2099,100,0,False),(2100,100,0,True),(0,0,1,False)):
            o=self.town(samples=(B(0x5e8,1),B(0x5f4,2),D(0x5f8,low),D(0x5fc,high),D(0x5ec,0)),tick_dword=tick)
            p=plan(State(),o);self.assertTrue(p.complete);self.assertEqual(p.status,'town_step_cleared' if done else 'town_wait')
            self.assertEqual(len(p.writes),2 if done else 0)
    def test_owned_start_cursor_town_progress_motion_callback_chain(self):
        start=RouteStartFrame(State({0x88:1})).step(RouteStartObservation(True,True,1,1))
        arm=plan(start.state,Obs((B(0x5e8,0),D(0x5f0,1),D(0x5ec,0xffffffff),D(0x5ec,0xffffffff),D(0x5ec,0))))
        town=plan(arm.state,self.town())
        done=plan(town.state,self.town(samples=(B(0x5e8,1),B(0x5f4,1),D(0x5f8,100),D(0x5fc,0),D(0x5ec,0)),tick_dword=2100))
        self.assertEqual(done.state.fields[0x5e8],0)
        tail=RouteResumeObservation(((0x553e7c,1),(0x554020,0x20)),Word(1,1,0x100),Byte(0x120,1,0))
        motion=RouteMotionObservation(((0x561f58,1),(0x561f58,1)),resume=RouteResumePathObservation(tail=tail))
        samples=(('object',0x566,8,0),('object',0x567,8,0),('object',0x5f0,32,1),
                 ('object',0x5e8,8,0),('global',0x561f58,32,1))
        progress=plan_route_progress(RouteResumeState(1,0),RouteProgressObservation(samples,step_execution=done,motion=motion))
        self.assertTrue(progress.complete);self.assertEqual(progress.state,RouteResumeState(0,1))
        r=MerchantRunner(MerchantSettings());r.start()
        # Explicit own callback samples and route-helper normal return remain
        # independent of the local route decision's completion.
        d=tick_merchant_callback(r,MerchantCallbackObservation(1,0,1,True,1,1,(1,)),MerchantSnapshot(2200,currently_open=False))
        self.assertEqual(d.status,'callback_modeled');self.assertEqual(r.phase,1)
    def test_bound_incomplete_step_blocks_progress_and_conflict_cannot_bypass_it(self):
        missing=plan(State(),self.town(comparison_al=0))
        samples=(('object',0x566,8,0),('object',0x567,8,0))
        p=plan_route_progress(RouteResumeState(1,0),RouteProgressObservation(samples,step_execution=missing))
        self.assertFalse(p.complete);self.assertIn('non-Town',p.missing)
        with self.assertRaises(ValueError):plan_route_progress(RouteResumeState(1,0),RouteProgressObservation(samples,step_return_dword=0,step_execution=missing))
    def test_bound_cursor_arm_still_requires_fresh_caller_processing_byte(self):
        arm=plan(State(),Obs((B(0x5e8,0),D(0x5f0,1),D(0x5ec,0xffffffff),D(0x5ec,0xffffffff),D(0x5ec,0))))
        samples=(('object',0x566,8,0),('object',0x567,8,0),('object',0x5f0,32,1),('object',0x5e8,8,1))
        p=plan_route_progress(RouteResumeState(1,0),RouteProgressObservation(samples,step_execution=arm))
        self.assertTrue(p.complete);self.assertEqual(p.status,'step_processing_no_motion');self.assertIsNone(p.motion)
        p=plan_route_progress(RouteResumeState(1,0),RouteProgressObservation(samples[:-1],step_execution=arm))
        self.assertFalse(p.complete)
    def test_raw_types_and_read_order(self):
        for kw in (dict(comparison_al=256),dict(hp_dword=-1),dict(town_helper_returned=1)):
            with self.assertRaises(ValueError):Obs(**kw)
        with self.assertRaises(ValueError):plan(State(),Obs((D(0x5e8,0),)))

if __name__=='__main__':unittest.main()
