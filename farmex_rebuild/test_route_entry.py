import unittest
from dataclasses import replace
from route_entry import RouteEntryObservation as Obs,plan_route_entry as plan
from route_resume import RouteResumeState as State,RouteResumeObservation
from route_progress import RouteProgressObservation as Progress
from route_motion import RouteMotionObservation
from route_resume_paths import RouteResumePathObservation
from source_coin import GuardedDwordSample as Word,GuardedByteSample as Byte
from source_route_step import SourceRouteStepObservation,plan_source_route_step
from source_route_coordinate import RouteCoordinateObservation
from source_route_commands import SourceRouteCommandsObservation
from source_route_gates import SourceRouteGatesObservation
from route_start_state import RouteStartState
from merchant_callback import MerchantCallbackObservation,tick_merchant_callback
from operation_engine import MerchantRunner,MerchantSettings,MerchantSnapshot

def G(a,v,bits=32):return ('global',a,bits,v)
def F(a,v,bits=32):return ('object',a,bits,v)
SKIP=(G(0x569100,0,8),G(0x569120,0,8),G(0x569120,0,8))

class RouteEntryTests(unittest.TestCase):
    def short_progress(self,**kw):
        values=dict(samples=(F(0x566,0,8),F(0x567,0,8),F(0x5f0,2)),step_return_dword=0)
        values.update(kw);return Progress(**values)
    def query(self,post=(G(0x569120,0,8),),**kw):
        samples=(G(0x569100,1,8),G(0x569108,0),F(0x5e0,0),F(0x5e4,0),
            G(0x56ff8c,0),G(0x56ff90,0),G(0x569124,22),G(0x569104,11))+post
        values=dict(samples=samples,tick_samples=(10000,1001,1100),query_returned=True,
            query_output_bytes=(1,0,None),progress=self.short_progress())
        values.update(kw);return Obs(**values)
    def test_disabled_query_initializes_locals_without_clock(self):
        p=plan(State(1,0),Obs(SKIP,query_output_bytes=(1,1,1),progress=self.short_progress()))
        self.assertTrue(p.complete);self.assertFalse(p.query_called);self.assertEqual(p.local_bytes,(0,0,0))
        self.assertEqual(p.writes,())
    def test_anti_eligible_short_circuits_enemy_prechecks(self):
        p=plan(State(1,0),self.query());self.assertTrue(p.complete);self.assertTrue(p.query_called)
        self.assertEqual(p.local_bytes,(1,0,None))
        calls=[s for s in p.steps if s[0]=='0046cfcc']
        self.assertEqual(calls[0][2],('local-33 ref','local-32 ref',22,'local-31 ref',11,0x5690f8))
    def test_start9999_skips_poll_clock_query_and_keeps_initialized_locals(self):
        o=Obs((G(0x569100,1,8),G(0x569108,0),F(0x5e0,0),F(0x5e4,0),G(0x569120,0,8)),
            (9999,),query_output_bytes=(1,1,1),progress=self.short_progress())
        p=plan(State(1,0),o);self.assertTrue(p.complete);self.assertFalse(p.query_called);self.assertEqual(p.local_bytes,(0,0,0))
    def test_poll_equality1000_does_not_query(self):
        o=Obs((G(0x569100,1,8),G(0x569108,0),F(0x5e0,0),F(0x5e4,0),
            G(0x56ff8c,0),G(0x56ff90,0),G(0x569120,0,8)),(10000,1000),progress=self.short_progress())
        p=plan(State(1,0),o);self.assertTrue(p.complete);self.assertFalse(p.query_called);self.assertEqual(p.writes,())
    def test_full_qword_start_and_poll_stamps_not_low_only(self):
        o=Obs((G(0x569100,1,8),G(0x569108,0),F(0x5e0,0),F(0x5e4,1),G(0x569120,0,8)),
            (0,),progress=self.short_progress())
        p=plan(State(1,0),o);self.assertTrue(p.complete);self.assertFalse(p.query_called)
        o=Obs((G(0x569100,1,8),G(0x569108,0),F(0x5e0,0),F(0x5e4,0),
            G(0x56ff8c,0),G(0x56ff90,1),G(0x569120,0,8)),(10000,0),progress=self.short_progress())
        p=plan(State(1,0),o);self.assertTrue(p.complete);self.assertFalse(p.query_called)
    def test_update_clock_after_query_is_separate(self):
        p=plan(State(1,0),self.query());self.assertTrue(p.complete)
        self.assertEqual(p.writes,(('global',0x56ff8c,4,1100),('global',0x56ff90,4,0)))
        p=plan(State(1,0),self.query(tick_samples=(10000,1001)))
        self.assertFalse(p.complete);self.assertTrue(p.query_called);self.assertEqual(p.local_bytes,(1,0,None));self.assertEqual(p.writes,())
    def test_unconfirmed_query_return_does_not_leave_old_zero_outputs(self):
        p=plan(State(1,0),self.query(query_returned=None))
        self.assertFalse(p.complete);self.assertEqual(p.local_bytes,(None,None,None));self.assertEqual(p.writes,())
        self.assertIsNone(p.progress)
    def test_enemy_eligibility_uses_its_own_flag_pair(self):
        o=self.query()
        samples=(G(0x569100,0,8),G(0x569120,1,8),G(0x569130,1,8))+o.samples[2:]
        p=plan(State(1,0),replace(o,samples=samples));self.assertTrue(p.complete);self.assertTrue(p.query_called)
    def test_fresh_enemy_flags_can_skip_previously_eligible_branch(self):
        o=self.query();samples=(G(0x569100,0,8),G(0x569120,1,8),G(0x569130,1,8))+o.samples[2:]
        p=plan(State(1,0),replace(o,samples=samples,query_output_bytes=(None,1,None)))
        self.assertTrue(p.complete);self.assertIsNotNone(p.progress);self.assertEqual(p.local_bytes,(None,1,None))
    def test_enemy_reload_returns_before_any_progress_or_queue(self):
        o=self.query(post=(G(0x569120,1,8),G(0x569130,1,8)),query_output_bytes=(None,1,None),enemy_span_returned=True,
            progress=Progress(anti_result_byte=1))
        p=plan(State(1,0),o);self.assertTrue(p.complete);self.assertEqual(p.status,'enemy_reload_span_returned')
        self.assertIsNone(p.progress);self.assertIsNone(p.queue)
        p=plan(State(1,0),replace(o,enemy_span_returned=None));self.assertFalse(p.complete);self.assertIn('Enemy',p.missing)
    def test_unknown_query_enemy_output_is_not_false(self):
        p=plan(State(1,0),self.query(post=(G(0x569120,1,8),G(0x569130,1,8)),query_output_bytes=(0,None,None)))
        self.assertFalse(p.complete);self.assertIn('local-32',p.missing);self.assertEqual(len(p.writes),2)
    def test_unvisited_unknown_query_outputs_do_not_block_counter_skip(self):
        p=plan(State(1,0),self.query(query_output_bytes=(None,None,None)))
        self.assertTrue(p.complete);self.assertEqual(p.local_bytes,(None,None,None))
    def test_entry_binds_local31_into_reached_anti_cr_branch(self):
        samples=(F(0x566,0,8),F(0x567,0,8),F(0x5f0,1),F(0x5e8,0,8),
            G(0x561f58,0),G(0x569100,1,8),G(0x569108,0))
        progress=Progress(samples,step_return_dword=0,anti_route_span_returned=True)
        p=plan(State(1,0),self.query(progress=progress))
        self.assertTrue(p.complete);self.assertEqual(p.progress.status,'anti_cr_route_returned')
        p=plan(State(1,0),self.query(progress=progress,query_output_bytes=(None,0,None)))
        self.assertFalse(p.complete);self.assertIn('local-31',p.missing)
    def test_no_query_does_not_reuse_previous_outputs_in_anti_cr_branch(self):
        tail=RouteResumeObservation(((0x553e7c,1),(0x554020,0x20)),Word(1,1,0x100),Byte(0x120,1,1))
        motion=RouteMotionObservation(((0x561f58,1),(0x561f58,1)),resume=RouteResumePathObservation(tail=tail))
        samples=(F(0x566,0,8),F(0x567,0,8),F(0x5f0,1),F(0x5e8,0,8),G(0x561f58,0),
            G(0x569100,1,8),G(0x569108,0),F(0x566,0,8),F(0x567,0,8))
        progress=Progress(samples,step_return_dword=0,motion=motion)
        p=plan(State(1,0),Obs(SKIP,query_output_bytes=(1,1,1),progress=progress))
        self.assertTrue(p.complete);self.assertEqual(p.progress.status,'motion_modeled');self.assertEqual(p.local_bytes,(0,0,0))
    def test_raw_progress_local31_cannot_override_entry_producer(self):
        with self.assertRaises(ValueError):plan(State(1,0),Obs(SKIP,progress=self.short_progress(anti_result_byte=0)))
    def test_callback_bound_gap_cannot_be_bypassed_by_raw_return(self):
        root=plan(State(1,0),Obs())
        runner=MerchantRunner(MerchantSettings());runner.start();calls=[]
        o=MerchantCallbackObservation(1,0,1,True,1,1,(1,),route_execution=root)
        d=tick_merchant_callback(runner,o,lambda:calls.append(1))
        self.assertEqual(d.status,'needs_adapter');self.assertEqual(calls,[]);self.assertEqual(runner.phase,0)
        self.assertIs(d.callback.route_execution,root)
    def test_callback_still_needs_separate_return_and_fresh_post_globals(self):
        root=plan(State(1,0),Obs(SKIP,progress=self.short_progress()))
        runner=MerchantRunner(MerchantSettings());runner.start()
        o=MerchantCallbackObservation(1,0,1,None,1,1,(1,),route_execution=root)
        d=tick_merchant_callback(runner,o,MerchantSnapshot(100,currently_open=False))
        self.assertEqual(d.status,'needs_adapter');self.assertIn('helper normal return',d.missing)
        d=tick_merchant_callback(runner,replace(o,route_helper_returned=True,post_enable_byte=None))
        self.assertEqual(d.status,'needs_adapter');self.assertIn('post-route enable',d.missing)
        d=tick_merchant_callback(runner,replace(o,route_helper_returned=True),MerchantSnapshot(100,currently_open=False))
        self.assertEqual(d.status,'callback_modeled');self.assertEqual(runner.phase,1);self.assertFalse(d.native_execution_verified)
    def test_callback_route_pending_zero_ignores_bound_gap(self):
        root=plan(State(1,0),Obs());r=MerchantRunner(MerchantSettings());r.start()
        d=tick_merchant_callback(r,MerchantCallbackObservation(1,0,0,None,1,1,(1,),route_execution=root),MerchantSnapshot(100,currently_open=False))
        self.assertEqual(d.status,'callback_modeled');self.assertIsNone(d.callback.route_execution)
    def test_queue_progress_gap_propagates_prospective_queue_only(self):
        actor=RouteResumeObservation(((0x553e7c,1),(0x554020,0x20)),Word(1,1,0x100),Byte(0x120,1,0))
        gates=SourceRouteGatesObservation(comparisons=(('Gate Skill',True,0),('Gate Open',True,1)),samples=((0x5f4,8,0),),
            actor=actor,parse_returned=True,parameter_dword=5,copy_returned=True,queue_gate_dword=1,
            queue_tick_dword=5,queue_returned=True,caller_tick_dword=10)
        step=plan_source_route_step(RouteStartState(),SourceRouteStepObservation(((0x5e8,8,1),(0x5ec,32,0)),True,0,
            coordinate=RouteCoordinateObservation(True,0),commands=SourceRouteCommandsObservation(wait_comparison_returned=True,
                wait_comparison_al=0,posture_predicate_returned=True,posture_match_byte=0,gates=gates)))
        progress=Progress((F(0x566,0,8),F(0x567,0,8)),step_execution=step)
        p=plan(State(1,0),Obs(SKIP,progress=progress));self.assertFalse(p.complete)
        self.assertEqual(p.queue.records,());self.assertEqual(len(p.prospective_queue.records),1)
    def test_missing_and_mismatched_reads_do_not_become_zero(self):
        p=plan(State(1,0),Obs());self.assertFalse(p.complete)
        with self.assertRaises(ValueError):plan(State(1,0),Obs((G(0x569100,0),)))
        for kw in (dict(tick_samples=(True,)),dict(query_output_bytes=(0,0,256)),dict(query_returned=1)):
            with self.assertRaises(ValueError):Obs(**kw)

if __name__=='__main__':unittest.main()
