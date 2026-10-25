import unittest
from dataclasses import replace
from route_progress import RouteProgressObservation as Obs,plan_route_progress as plan
from route_motion import RouteMotionObservation as Motion
from route_resume import RouteResumeState as State,RouteResumeObservation as Read
from route_resume_paths import RouteResumePathObservation as Exit
from source_coin import GuardedDwordSample as Word,GuardedByteSample as Byte
from source_random import SourceRandomObservation as Random

def F(a,v,bits=32):return ('object',a,bits,v)
def B(a,v):return F(a,v,8)
def G(a,v,bits=32):return ('global',a,bits,v)
SKIP=(B(0x566,0),B(0x567,0))
CORE=(F(0x5f0,1),B(0x5e8,0),G(0x561f58,0),G(0x569100,0,8))

def common_motion():
    tail=Read(((0x553e7c,1),(0x554020,0x20)),Word(1,1,0x100),Byte(0x120,1,1))
    return Motion(((0x561f58,1),(0x561f58,1)),resume=Exit(tail=tail))

class RouteProgressTests(unittest.TestCase):
    def arrival(self,**kw):
        values=dict(samples=SKIP+CORE+(B(0x566,1),B(0x6d9,1),B(0x6da,0),G(0x562004,20),G(0x562000,10)),
            tick_samples=(100,),step_return_dword=0,metric_status_ah=0x40,random_return_dword=2000)
        values.update(kw);return Obs(**values)
    def test_mismatched_step_return_does_not_read_processing_or_mode(self):
        d=plan(State(1,0),Obs(SKIP+(F(0x5f0,2),),step_return_dword=0))
        self.assertTrue(d.complete);self.assertEqual(d.status,'step_not_last_no_motion');self.assertIsNone(d.motion)
    def test_count_decrement_wrap_is_not_replaced_by_positive_guard(self):
        d=plan(State(1,0),Obs(SKIP+(F(0x5f0,0),B(0x5e8,1)),step_return_dword=0xffffffff))
        self.assertTrue(d.complete);self.assertEqual(d.status,'step_processing_no_motion')
    def test_processing_nonzero_does_not_advance_mode(self):
        d=plan(State(1,0),Obs(SKIP+(F(0x5f0,1),B(0x5e8,2)),step_return_dword=0))
        self.assertTrue(d.complete);self.assertEqual(d.status,'step_processing_no_motion')
    def test_nonzero_mode_hands_off_before_anti_or_repeated_flags(self):
        d=plan(State(1,0),Obs(SKIP+(F(0x5f0,1),B(0x5e8,0),G(0x561f58,2)),step_return_dword=0,motion=common_motion()))
        self.assertTrue(d.complete);self.assertEqual(d.status,'motion_modeled');self.assertEqual(d.motion.status,'exit_common')
    def test_flag_clear_writes_three_globals_before_motion(self):
        d=plan(State(1,0),Obs(SKIP+CORE+SKIP,step_return_dword=0,motion=common_motion()))
        self.assertTrue(d.complete)
        self.assertEqual(d.writes,(('global',0x56ff9c,4,0),('global',0x56ffa0,4,0),('global',0x56ffa4,4,0)))
    def test_incomplete_motion_retains_known_prefix_writes(self):
        d=plan(State(1,0),Obs(SKIP+CORE+SKIP,step_return_dword=0))
        self.assertFalse(d.complete);self.assertEqual(len(d.writes),3);self.assertEqual(d.state,State(1,0))
    def test_anti_cr_gates_need_separate_earlier_result_and_route_span(self):
        samples=SKIP+(F(0x5f0,1),B(0x5e8,0),G(0x561f58,0),G(0x569100,1,8),G(0x569108,0))
        o=Obs(samples,step_return_dword=0)
        self.assertIn('local-31',plan(State(1,0),o).missing)
        o=replace(o,anti_result_byte=1)
        self.assertIn('AntiCR',plan(State(1,0),o).missing)
        d=plan(State(1,0),replace(o,anti_route_span_returned=True))
        self.assertTrue(d.complete);self.assertEqual(d.status,'anti_cr_route_returned');self.assertIsNone(d.motion)
    def test_index_is_reread_for_signed_compare(self):
        samples=(B(0x566,1),F(0x5ec,1),F(0x5ec,0xffffffff),F(0x544,0),F(0x5f0,2))
        d=plan(State(1,0),Obs(samples,step_return_dword=0))
        self.assertTrue(d.complete);self.assertEqual(d.writes,())
    def test_first_pass_request_at_5000_records_fresh_update_clock(self):
        samples=(B(0x566,1),F(0x5ec,0),F(0x5ec,1),F(0x544,0),B(0x6d9,0),B(0x6da,0),
                 G(0x56ff94,0),G(0x56ff98,0),F(0x5f0,2))
        d=plan(State(1,0),Obs(samples,(5000,6000),(True,),step_return_dword=0))
        self.assertTrue(d.complete)
        self.assertEqual(d.writes,(('object',0x6d9,1,1),('global',0x56ff94,4,6000),('global',0x56ff98,4,0)))
    def test_request_missing_return_stops_before_update_clock_and_step(self):
        samples=(B(0x566,1),F(0x5ec,0),F(0x5ec,1),F(0x544,0),B(0x6d9,0),B(0x6da,0),G(0x56ff94,0),G(0x56ff98,0))
        d=plan(State(1,0),Obs(samples,(5000,6000)))
        self.assertFalse(d.complete);self.assertEqual(len(d.writes),1)
        self.assertFalse(any(step[0]=='004f276c' for step in d.steps))
    def test_request_branch_waits_below_threshold_and_uses_qword(self):
        for tick,low,high in ((4999,0,0),(0,0,1)):
            samples=SKIP+CORE+(B(0x566,1),B(0x6d9,0),B(0x6da,0),G(0x56ff94,low),G(0x56ff98,high))
            d=plan(State(1,0),Obs(samples,(tick,),step_return_dword=0))
            self.assertTrue(d.complete);self.assertEqual(d.status,'request_wait_return');self.assertEqual(len(d.writes),1)
    def test_done_byte_bypasses_metric_and_clock_into_motion(self):
        for working in (0,1):
            samples=SKIP+CORE+(B(0x566,1),B(0x6d9,working),B(0x6da,1))
            d=plan(State(1,0),Obs(samples,step_return_dword=0,motion=common_motion()))
            self.assertTrue(d.complete);self.assertEqual(d.status,'motion_modeled')
    def test_arrival_less_equal_and_unordered_statuses_arm_delay(self):
        for ah in (1,0x40,0x45):
            d=plan(State(1,0),self.arrival(metric_status_ah=ah))
            self.assertTrue(d.complete);self.assertEqual(d.status,'arrival_delay_armed')
            self.assertEqual(d.writes,(('object',0x6d9,1,0),('object',0x6da,1,1),
                ('global',0x56ff9c,4,100),('global',0x56ffa0,4,0),('global',0x56ffa4,4,2000)))
            self.assertIsNone(d.motion)
    def test_greater_status_uses_request_clock_without_arming_delay(self):
        for ah in (0,0x80):
            o=self.arrival(metric_status_ah=ah)
            o=replace(o,samples=o.samples+(G(0x56ff94,0),G(0x56ff98,0)),tick_samples=(4999,))
            d=plan(State(1,0),o);self.assertTrue(d.complete);self.assertEqual(d.status,'metric_greater_wait_return')
            self.assertEqual(d.writes,());self.assertIsNone(d.random_plan)
    def test_bound_rng_uses_existing_helper_and_separate_seed_clock(self):
        d=plan(State(1,0),self.arrival(random_return_dword=None,random_observation=Random(7,True,5000)))
        self.assertTrue(d.complete);self.assertEqual(d.writes[-1],('global',0x56ffa4,4,7000))
        self.assertEqual(d.writes[-3],('global',0x56ff9c,4,100))
        self.assertIsNotNone(d.random_plan)
        d=plan(State(1,0),self.arrival(random_return_dword=None,random_observation=Random(srand_returned=True,rand_eax=0)))
        self.assertFalse(d.complete);self.assertEqual(len(d.writes),4);self.assertIn('GetTickCount',d.missing)
    def test_conflicting_rng_inputs_rejected_only_when_reached(self):
        with self.assertRaises(ValueError):plan(State(1,0),self.arrival(random_observation=Random(7,True,0)))
        d=plan(State(1,0),Obs(SKIP+(F(0x5f0,2),),step_return_dword=0,
            random_return_dword=1,random_observation=Random(7,True,0)))
        self.assertTrue(d.complete)
    def test_missing_rng_does_not_complete_or_hide_prior_writes(self):
        d=plan(State(1,0),self.arrival(random_return_dword=None))
        self.assertFalse(d.complete);self.assertEqual(len(d.writes),4);self.assertEqual(d.state,State(1,0))
    def test_missing_step_result_is_not_zero(self):
        d=plan(State(1,0),Obs(SKIP))
        self.assertFalse(d.complete);self.assertIn('helper normal-return',d.missing)
    def test_read_order_width_and_types(self):
        with self.assertRaises(ValueError):plan(State(1,0),Obs((F(0x566,0),)))
        for kw in (dict(metric_status_ah=256),dict(tick_samples=(True,)),dict(request_returns=(1,)),dict(step_return_dword=-1)):
            with self.assertRaises(ValueError):Obs(**kw)

if __name__=='__main__':unittest.main()
