import unittest
from dataclasses import replace
from owned_route_texts import owned_stable_route_texts,bind_owned_route_texts
from source_route_step import SourceRouteStepObservation as Step,plan_source_route_step
from route_start_state import RouteStartState
from source_route_commands import SourceRouteCommandsObservation as Commands
from source_route_gates import SourceRouteGatesObservation as Gates
from source_route_delos import SourceDelosObservation as Delos
from source_route_finish import SourceRouteFinishObservation as Finish
from source_route_coordinate import RouteCoordinateObservation as Coordinate
from route_resume import RouteResumeObservation
from source_coin import GuardedDwordSample as Word,GuardedByteSample as Byte

def actor(value=0):return RouteResumeObservation(((0x553e7c,1),(0x554020,0x20)),Word(1,1,0x100),Byte(0x120,1,value))

class OwnedRouteTextsTests(unittest.TestCase):
    def names(self,name,parameter=None):return owned_stable_route_texts(name,parameter,stable_same_invocation=True)
    def template(self,**kw):
        values=dict(samples=((0x5e8,8,1),(0x5ec,32,0)),comparison_span_returned=True,
            coordinate=Coordinate(comparison_span_returned=True),
            commands=Commands(wait_comparison_returned=True,posture_predicate_returned=True))
        values.update(kw);return Step(**values)
    def gate_templates(self,kind):
        finish=Finish(comparisons=tuple((k,True,None) for k in ('Change Camp','NPC')))
        delos=Delos(comparisons=tuple((k,True,None) for k in ('Delos Gate Open','Delos Gate')),finish=finish)
        gates=Gates(comparisons=tuple((k,True,None) for k in ('Gate Skill','Gate Open','Gate')),
            samples=((0x5f4,8,0),),actor=actor(1),delos=delos)
        return self.template(commands=Commands(wait_comparison_returned=True,posture_predicate_returned=True,gates=gates))
    def test_town_from_name_does_not_need_later_texts(self):
        template=Step(samples=((0x5e8,8,1),(0x5f4,8,0),(0x5ec,32,0)),comparison_span_returned=True,
            reset_helper_returned=True,max_hp_dword=100,hp_dword=49)
        bound=bind_owned_route_texts(template,{'Town':'Town'})
        p=plan_source_route_step(RouteStartState(),bound.observation)
        self.assertTrue(p.complete);self.assertEqual(p.status,'town_health_wait')
        self.assertFalse(bound.equality_plans['Koordinat'].complete)
    def test_builder_never_fills_string_construct_cleanup_receipts(self):
        bound=bind_owned_route_texts(Step(samples=((0x5e8,8,1),)),self.names('Town'))
        self.assertEqual(bound.observation.comparison_al,1)
        self.assertIsNone(bound.observation.comparison_span_returned)
        p=plan_source_route_step(RouteStartState(),bound.observation)
        self.assertFalse(p.complete);self.assertIn('string/comparison',p.missing)
    def test_processing_zero_cursor_works_without_any_text(self):
        template=Step(samples=((0x5e8,8,0),(0x5f0,32,0),(0x5ec,32,0xffffffff),(0x5ec,32,0xffffffff)))
        p=plan_source_route_step(RouteStartState(),bind_owned_route_texts(template,{}).observation)
        self.assertTrue(p.complete);self.assertEqual(p.status,'cursor_at_last')
    def test_coordinate_selection_from_owned_name_holds_on_its_own_missing_gate(self):
        p=plan_source_route_step(RouteStartState(),bind_owned_route_texts(self.template(),self.names('Koordinat')).observation)
        self.assertFalse(p.complete);self.assertIsNotNone(p.coordinate_plan)
        self.assertIn('global sample',p.missing)
    def test_wait_selected_without_manual_al(self):
        template=self.template(commands=Commands(samples=((0x5f4,8,0),),wait_comparison_returned=True,tick_dword=100))
        p=plan_source_route_step(RouteStartState(),bind_owned_route_texts(template,self.names('Bekle')).observation)
        self.assertTrue(p.complete);self.assertEqual(p.status,'command_started');self.assertEqual(p.state.fields[0x5f8],100)
    def test_posture_or_short_circuits_unknown_kalk_text(self):
        texts={'Town':'Otur','Koordinat':'Otur','Bekle':'Otur','Otur_predicate':'Otur'}
        template=self.template(commands=Commands(samples=((0x5f4,8,0),),wait_comparison_returned=True,
            posture_predicate_returned=True,actor=actor(1)))
        bound=bind_owned_route_texts(template,texts);self.assertEqual(bound.posture_match_byte,1)
        self.assertFalse(bound.equality_plans['Kalk_predicate'].complete)
        p=plan_source_route_step(RouteStartState(),bound.observation)
        self.assertTrue(p.complete);self.assertEqual(p.status,'posture_actor_blocked')
    def test_unknown_first_posture_does_not_use_second_to_guess_or(self):
        bound=bind_owned_route_texts(self.template(),{'Kalk_predicate':'Kalk'})
        self.assertIsNone(bound.posture_match_byte)
    def test_fresh_posture_rechecks_can_disagree_with_group(self):
        texts=self.names('Otur');texts['Otur_action']='Kalk';texts['Kalk_action']='Kalk'
        template=self.template(commands=Commands(samples=((0x5f4,8,0),),wait_comparison_returned=True,
            posture_predicate_returned=True,actor=actor(),sit_comparison_returned=True,
            stand_comparison_returned=True,stand_returned=True,tick_dword=100))
        bound=bind_owned_route_texts(template,texts)
        self.assertEqual(bound.observation.commands.sit_comparison_al,0)
        self.assertEqual(bound.observation.commands.stand_comparison_al,1)
        p=plan_source_route_step(RouteStartState(),bound.observation)
        self.assertTrue(p.complete);self.assertEqual(p.status,'command_started')
    def test_gate_comparison_tuples_from_names_preserve_returns(self):
        for name in ('Gate Skill','Gate Open','Gate'):
            bound=bind_owned_route_texts(self.gate_templates(name),self.names(name))
            p=plan_source_route_step(RouteStartState(),bound.observation)
            self.assertTrue(p.complete);self.assertEqual(p.status,'gate_actor_blocked')
            self.assertEqual(p.command_plan.gate_plan.kind,name)
    def test_randomize_uses_parameter_text_not_command_name(self):
        names=self.names('Change Camp','Randomize')
        bound=bind_owned_route_texts(self.gate_templates('Change Camp'),names)
        self.assertEqual(bound.observation.commands.gates.delos.finish.random_comparison_al,1)
        names=self.names('Randomize','1')
        bound=bind_owned_route_texts(self.gate_templates('Randomize'),names)
        self.assertEqual(bound.observation.commands.gates.delos.finish.random_comparison_al,0)
        self.assertEqual(bound.observation.commands.gates.delos.finish.comparisons[0][2],0)
    def test_unknown_name_flows_to_final_processing_clear(self):
        p=plan_source_route_step(RouteStartState({0x5e8:1,0x5f4:1}),
            bind_owned_route_texts(self.gate_templates('unknown'),self.names('unknown')).observation)
        self.assertTrue(p.complete);self.assertEqual(p.status,'unknown_command_processing_cleared')
        self.assertEqual(p.state.fields[0x5f4],1)
    def test_case_and_whitespace_not_normalized(self):
        for name in ('Town ','town'):
            b=bind_owned_route_texts(self.template(),self.names(name))
            self.assertEqual(b.observation.comparison_al,0)
    def test_unknown_names_missing_text_not_empty(self):
        bound=bind_owned_route_texts(self.template(),{})
        self.assertIsNone(bound.observation.comparison_al)
        p=plan_source_route_step(RouteStartState(),bound.observation);self.assertFalse(p.complete)
    def test_compiler_rejects_mixed_raw_results_as_own_input_contract(self):
        with self.assertRaises(ValueError):bind_owned_route_texts(replace(self.template(),comparison_al=1),self.names('Town'))
        with self.assertRaises(ValueError):bind_owned_route_texts(self.template(commands=Commands(wait_comparison_al=0)),self.names('Town'))
        with self.assertRaises(ValueError):bind_owned_route_texts(self.template(),{'typo':'Town'})
    def test_stable_row_contract_is_explicit_and_inputs_not_mutated(self):
        with self.assertRaises(ValueError):owned_stable_route_texts('Town')
        template=self.template();bound=bind_owned_route_texts(template,self.names('Town'))
        self.assertIsNone(template.comparison_al);self.assertEqual(bound.observation.comparison_al,1)
        with self.assertRaises(TypeError):bound.equality_plans['Town']=None
        self.assertFalse(bound.native_runtime_verified)

if __name__=='__main__':unittest.main()
