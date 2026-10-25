import unittest
from dataclasses import replace
from source_route_finish import SourceRouteFinishObservation as Obs,plan_source_route_finish as plan
from source_route_delos import SourceDelosObservation
from source_route_gates import SourceRouteGatesObservation
from source_route_commands import SourceRouteCommandsObservation
from source_route_coordinate import RouteCoordinateObservation
from source_route_step import SourceRouteStepObservation,plan_source_route_step
from route_start_state import RouteStartState
from route_resume import RouteResumeObservation
from source_coin import GuardedDwordSample as Word,GuardedByteSample as Byte
from npc_route_engine import NpcRouteFrame,NpcRouteObservation
from routes import RouteRunner,RouteStep
from special_routes import SpecialCommand,SpecialRouteSnapshot,SpecialRouteState,special_route_step

def actor(value=0):return RouteResumeObservation(((0x553e7c,1),(0x554020,0x20)),Word(1,1,0x100),Byte(0x120,1,value))

class SourceRouteFinishTests(unittest.TestCase):
    def camp(self,**kw):
        values=dict(comparisons=(('Change Camp',True,1),),samples=((0x5f4,8,0),),reset_returned=True,
            max_hp_dword=100,hp_dword=50,random_comparison_returned=True,random_comparison_al=0,
            number_parse_returned=True,number_dword=0,caller_tick_dword=100)
        values.update(kw);return Obs(**values)
    def npc(self,started=0,**kw):
        values=dict(comparisons=(('Change Camp',True,0),('NPC',True,1)),samples=((0x5f4,8,started),),
            actor=actor(),caller_tick_dword=100)
        values.update(kw);return Obs(**values)
    def bound(self,o,return_index=True):
        delos=SourceDelosObservation(comparisons=tuple((k,True,0) for k in ('Delos Gate Open','Delos Gate')),finish=o)
        gates=SourceRouteGatesObservation(comparisons=tuple((k,True,0) for k in ('Gate Skill','Gate Open','Gate')),delos=delos)
        commands=SourceRouteCommandsObservation(wait_comparison_returned=True,wait_comparison_al=0,
            posture_predicate_returned=True,posture_match_byte=0,gates=gates)
        samples=((0x5e8,8,1),(0x5ec,32,0)) if return_index else ((0x5e8,8,1),)
        return SourceRouteStepObservation(samples,True,0,coordinate=RouteCoordinateObservation(True,0),commands=commands)
    def test_camp_health_gate_skips_parameter_and_clock(self):
        p=plan(self.camp(hp_dword=49,random_comparison_returned=None,caller_tick_dword=None))
        self.assertTrue(p.complete);self.assertEqual(p.status,'camp_health_wait');self.assertEqual(p.health_threshold_signed,50)
        self.assertEqual(p.writes,())
    def test_camp_signed_low32_health_product(self):
        p=plan(self.camp(max_hp_dword=0x40000001,hp_dword=0xffffffff))
        self.assertTrue(p.complete);self.assertEqual(p.health_threshold_signed,-21474835)
    def test_camp_randomize_calls_only_its_helper(self):
        p=plan(self.camp(random_comparison_al=1,random_helper_returned=True,number_parse_returned=None,number_dword=None))
        self.assertTrue(p.complete);self.assertEqual(p.status,'camp_started')
        self.assertIn(('normal_return','004c8a98(00561ef8) normal return'),p.steps)
        self.assertEqual(p.writes,(('object',0x5f8,4,100),('object',0x5fc,4,0),('object',0x5f4,1,1)))
    def test_camp_zero_parser_result_skips_action_but_starts(self):
        p=plan(self.camp());self.assertTrue(p.complete);self.assertEqual(p.status,'camp_started')
        self.assertFalse(any('004c8698' in str(s) for s in p.steps))
    def test_camp_nonzero_parameter_requires_separate_helper_return(self):
        o=self.camp(number_dword=0xffffffff)
        self.assertFalse(plan(o).complete)
        p=plan(replace(o,number_helper_returned=True));self.assertTrue(p.complete)
        self.assertIn(('normal_return','004c8698(00561ef8,4294967295) normal return'),p.steps)
    def test_camp_helper_gaps_and_clock_do_not_start(self):
        for kw in (dict(reset_returned=None),dict(max_hp_dword=None),dict(hp_dword=None),
                   dict(random_comparison_returned=None),dict(random_comparison_al=None),
                   dict(number_parse_returned=None),dict(number_dword=None),dict(caller_tick_dword=None)):
            p=plan(self.camp(**kw));self.assertFalse(p.complete);self.assertEqual(p.writes,())
    def test_camp_wait_2000_and_full_qword_skip_health(self):
        for tick,low,high,done in ((2099,100,0,False),(2100,100,0,True),(0,0,1,False)):
            p=plan(self.camp(samples=((0x5f4,8,1),(0x5f8,32,low),(0x5fc,32,high)),
                reset_returned=None,max_hp_dword=None,hp_dword=None,random_comparison_returned=None,caller_tick_dword=tick))
            self.assertTrue(p.complete);self.assertEqual(len(p.writes),2 if done else 0)
    def test_npc_start_actor_then_clock_started_phase_write_order(self):
        p=plan(self.npc());self.assertTrue(p.complete);self.assertEqual(p.status,'npc_started')
        self.assertEqual(p.writes,(('object',0x5f8,4,100),('object',0x5fc,4,0),('object',0x5f4,1,1),('object',0x600,4,1)))
    def test_npc_start_actor_nonzero_skips_copy_helper_and_clock(self):
        p=plan(self.npc(actor=actor(1),caller_tick_dword=None));self.assertTrue(p.complete)
        self.assertEqual(p.status,'npc_actor_blocked');self.assertEqual(p.writes,())
        p=plan(self.npc(actor=RouteResumeObservation()));self.assertFalse(p.complete)
    def test_npc_started_copy_receipt_before_raw_helper_result(self):
        p=plan(self.npc(1,npc_return_al=1));self.assertFalse(p.complete);self.assertEqual(p.writes,())
        p=plan(self.npc(1,npc_copy_returned=True,npc_return_al=0,caller_tick_dword=None))
        self.assertTrue(p.complete);self.assertEqual(p.status,'npc_pending');self.assertEqual(p.writes,())
        p=plan(self.npc(1,npc_copy_returned=True,npc_return_al=2))
        self.assertTrue(p.complete);self.assertEqual(p.writes,(('object',0x5f4,1,0),('object',0x5e8,1,0)))
    def test_bound_npc_copies_unicode_then_uses_existing_result(self):
        observation=NpcRouteObservation(NpcRouteFrame(10,texts={0x608:'old'}),{})
        p=plan(self.npc(1,npc_copy_returned=True,npc_parameter_text='Potion',npc_observation=observation))
        self.assertTrue(p.complete);self.assertEqual(p.status,'npc_step_cleared');self.assertTrue(p.npc_result.returned_true)
        self.assertEqual(p.npc_result.frame.texts[0x608],'Potion');self.assertEqual(p.npc_result.frame.phase,11)
        self.assertEqual(observation.frame.texts[0x608],'old')
    def test_bound_npc_pending_is_normal_return_not_task_complete(self):
        p=plan(self.npc(1,npc_copy_returned=True,npc_parameter_text='Potion',npc_observation=NpcRouteObservation(NpcRouteFrame(11),{})))
        self.assertTrue(p.complete);self.assertEqual(p.status,'npc_pending');self.assertEqual(p.writes,())
    def test_bound_npc_gap_copy_text_and_conflict_do_not_fake_completion(self):
        entry=NpcRouteObservation(NpcRouteFrame(1),{})
        o=self.npc(1,npc_copy_returned=True,npc_parameter_text='Potion',npc_observation=entry)
        p=plan(o);self.assertFalse(p.complete);self.assertEqual(p.writes,());self.assertIsNotNone(p.npc_result)
        p=plan(replace(o,npc_parameter_text=None));self.assertFalse(p.complete);self.assertIsNone(p.npc_result)
        with self.assertRaises(ValueError):plan(replace(o,npc_return_al=1))
    def test_unknown_final_only_clears_processing(self):
        o=Obs(comparisons=(('Change Camp',True,0),('NPC',True,0)))
        p=plan(o);self.assertTrue(p.complete);self.assertEqual(p.status,'unknown_command_processing_cleared')
        self.assertEqual(p.writes,(('object',0x5e8,1,0),));self.assertEqual(p.reads,())
        bound=plan_source_route_step(RouteStartState({0x5e8:1,0x5f4:1,0x5f8:100}),self.bound(o))
        self.assertTrue(bound.complete);self.assertEqual(bound.state.fields[0x5e8],0)
        self.assertEqual(bound.state.fields[0x5f4],1);self.assertEqual(bound.state.fields[0x5f8],100)
    def test_bound_npc_start_preserves_phase_and_fresh_return_requirement(self):
        p=plan_source_route_step(RouteStartState(),self.bound(self.npc()))
        self.assertTrue(p.complete);self.assertEqual(p.state.fields[0x600],1);self.assertEqual(p.return_dword,0)
        p=plan_source_route_step(RouteStartState(),self.bound(self.npc(),False))
        self.assertFalse(p.complete);self.assertNotIn(0x600,p.state.fields);self.assertEqual(p.prospective_state.fields[0x600],1)
    def test_generic_unknown_preserves_started_state(self):
        state=SpecialRouteState(started=True,started_qword=100)
        p=special_route_step(SpecialCommand('Randomize'),SpecialRouteSnapshot(100),state)
        self.assertEqual(p.status,'step_complete');self.assertFalse(p.state.processing);self.assertTrue(p.state.started)
        self.assertEqual(p.state.started_qword,100)
    def test_generic_camp_parser_deferred_during_health_gap_and_wait(self):
        r=RouteRunner();r.start([RouteStep('Change Camp',parameter1='not numeric')]);r.tick(0)
        self.assertEqual(r.tick(1,special_observation=SpecialRouteSnapshot(1,hp_4611a0=49,max_hp_4611c0=100)).kind,'waiting')
        self.assertEqual(r.tick(2,special_observation=SpecialRouteSnapshot(2)).kind,'needs_observation')
        r.special_state=SpecialRouteState(started=True,started_qword=0)
        self.assertEqual(r.tick(2000,special_observation=SpecialRouteSnapshot(2000)).kind,'step_complete')
    def test_order_and_types(self):
        with self.assertRaises(ValueError):plan(self.camp(comparisons=(('NPC',True,1),)))
        for kw in (dict(npc_return_al=256),dict(number_dword=-1),dict(npc_parameter_text=b'Potion'),dict(reset_returned=1)):
            with self.assertRaises(ValueError):Obs(**kw)

if __name__=='__main__':unittest.main()
