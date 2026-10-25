import unittest
from dataclasses import replace
from source_route_delos import SourceDelosObservation as Obs,plan_source_delos as plan,TEMPLATE
from source_route_gates import SourceRouteGatesObservation,plan_source_route_gates
from source_route_commands import SourceRouteCommandsObservation
from source_route_step import SourceRouteStepObservation,plan_source_route_step
from source_route_coordinate import RouteCoordinateObservation
from route_start_state import RouteStartState
from route_resume import RouteResumeObservation
from source_coin import GuardedDwordSample as Word,GuardedByteSample as Byte
from npc_lookup import NpcCandidate
from action_queue import QueueState
from routes import RouteRunner,RouteStep
from special_routes import SpecialRouteSnapshot,SpecialRouteState

def actor(value=0):return RouteResumeObservation(((0x553e7c,1),(0x554020,0x20)),Word(1,1,0x100),Byte(0x120,1,value))

class SourceDelosTests(unittest.TestCase):
    def opened(self,**kw):
        values=dict(comparisons=(('Delos Gate Open',True,1),),samples=((0x5f4,8,0),),actor=actor(),
            lookup_span_returned=True,npc_id_dword=0,caller_tick_dword=100)
        values.update(kw);return Obs(**values)
    def npc(self,**kw):
        values=dict(npc_id_dword=7,npc_pointer_dword=0x100,global_samples=((0x554008,8),(0x554010,16)),
            x_float_read_returned=True,y_float_read_returned=True,x_float_bits=0x3f800000,y_float_bits=0x40000000,
            metric_status_ah=0x40,move_returned=True,interaction_actor=actor(),interaction_returned=True)
        values.update(kw);return self.opened(**values)
    def gate(self,**kw):
        values=dict(comparisons=(('Delos Gate Open',True,0),('Delos Gate',True,1)),samples=((0x5f4,8,0),),
            actor=actor(),parse_returned=True,parameter_dword=257,copy_returned=True,origin_x_dword=10,
            origin_y_dword=20,queue_gate_dword=1,queue_tick_dword=30,queue_returned=True,caller_tick_dword=40)
        values.update(kw);return Obs(**values)
    def bound(self,o,return_index=True):
        gates=SourceRouteGatesObservation(comparisons=tuple((k,True,0) for k in ('Gate Skill','Gate Open','Gate')),delos=o)
        commands=SourceRouteCommandsObservation(wait_comparison_returned=True,wait_comparison_al=0,
            posture_predicate_returned=True,posture_match_byte=0,gates=gates)
        samples=((0x5e8,8,1),(0x5ec,32,0)) if return_index else ((0x5e8,8,1),)
        return SourceRouteStepObservation(samples,True,0,coordinate=RouteCoordinateObservation(True,0),commands=commands)
    def test_open_no_npc_still_starts_wait_without_pointer_read(self):
        p=plan(QueueState(),self.opened());self.assertTrue(p.complete);self.assertEqual(p.status,'delos_started')
        self.assertEqual(p.writes[-1],('object',0x5f4,1,1));self.assertIsNone(p.lookup)
    def test_open_zero_pointer_also_starts_without_offsets(self):
        p=plan(QueueState(),self.opened(npc_id_dword=0xffffffff,npc_pointer_dword=0))
        self.assertTrue(p.complete);self.assertIn(('00464a10',0xffffffff),p.steps)
        self.assertFalse(any(s[0]=='global_read' for s in p.steps))
    def test_bound_lookup_uses_existing_selector_and_completion_gate(self):
        o=self.opened(npc_id_dword=None,lookup_candidates=(NpcCandidate(10,7,b'abc[Teleport Gate]xyz'),),
            lookup_complete=True,npc_pointer_dword=0)
        p=plan(QueueState(),o);self.assertTrue(p.complete);self.assertEqual(p.lookup.candidate_id,7)
        p=plan(QueueState(),replace(o,lookup_complete=None));self.assertFalse(p.complete);self.assertEqual(p.writes,())
        with self.assertRaises(ValueError):plan(QueueState(),replace(o,npc_id_dword=7))
    def test_entry_actor_blocked_skips_lookup_queue_and_clock(self):
        p=plan(QueueState(),self.opened(actor=actor(1),lookup_span_returned=None,caller_tick_dword=None))
        self.assertTrue(p.complete);self.assertEqual(p.status,'delos_actor_blocked');self.assertEqual(p.writes,())
    def test_exact9_equal_and_greater_choose_movement(self):
        for ah in (0,0x40):
            p=plan(QueueState(),self.npc(metric_status_ah=ah))
            self.assertTrue(p.complete);self.assertIsNone(p.interaction_actor_plan)
            calls=[s for s in p.steps if s[0] in ('00460548','004646b4')]
            self.assertEqual(calls,[('00460548','physical_push_y_x_float_bits',0x40000000,0x3f800000),
                                    ('004646b4','physical_push_y_x_float_bits',0x40000000,0x3f800000)])
    def test_less_and_unordered_require_fresh_interaction_actor(self):
        for ah in (1,0x45):
            p=plan(QueueState(),self.npc(metric_status_ah=ah,interaction_actor=actor(1),caller_tick_dword=None))
            self.assertTrue(p.complete);self.assertEqual(p.status,'interaction_actor_blocked');self.assertEqual(p.writes,())
            p=plan(QueueState(),self.npc(metric_status_ah=ah));self.assertTrue(p.complete)
            self.assertIn(('normal_return','004c8f7c(00561ef8,NPC7) normal return'),p.steps)
    def test_interaction_actor_gap_does_not_reuse_entry_actor(self):
        p=plan(QueueState(),self.npc(metric_status_ah=1,interaction_actor=RouteResumeObservation()))
        self.assertFalse(p.complete);self.assertIn('fresh interaction actor',p.missing)
    def test_offset_arithmetic_wraps_and_getter_values_remain_explicit(self):
        p=plan(QueueState(),self.npc(npc_pointer_dword=0xfffffff8))
        self.assertTrue(p.complete);self.assertIn(('0045ddb8',0),p.steps);self.assertIn(('0045ddb8',8),p.steps)
    def test_npc_helper_value_receipts_and_metric_gaps_hold(self):
        for kw in (dict(lookup_span_returned=None),dict(npc_pointer_dword=None),dict(x_float_read_returned=None),
                   dict(x_float_bits=None),dict(y_float_read_returned=None),dict(metric_status_ah=None),dict(move_returned=None)):
            p=plan(QueueState(),self.npc(**kw));self.assertFalse(p.complete);self.assertEqual(p.writes,())
    def test_open_wait1000_and_full_qword_without_npc_observations(self):
        for tick,low,high,done in ((1099,100,0,False),(1100,100,0,True),(0,0,1,False)):
            p=plan(QueueState(),self.opened(samples=((0x5f4,8,1),(0x5f8,32,low),(0x5fc,32,high)),
                actor=RouteResumeObservation(),caller_tick_dword=tick,lookup_span_returned=None))
            self.assertTrue(p.complete);self.assertEqual(len(p.writes),2 if done else 0);self.assertIsNone(p.actor_plan)
    def test_gate_low_byte_template_origin_globals_and_queue_delay(self):
        p=plan(QueueState(),self.gate());self.assertTrue(p.complete)
        self.assertEqual(p.payload,TEMPLATE[:1]+b'\x01'+TEMPLATE[2:]);self.assertEqual(len(p.payload),19)
        self.assertEqual(p.writes[:2],(('global',0x56ffb8,4,10),('global',0x56ffbc,4,20)))
        self.assertEqual(p.queue.records[0].delay_dword,1000);self.assertEqual(p.queue.records[0].created_tick,30)
        self.assertEqual(p.writes[2],('object',0x5f8,4,40))
    def test_origin_y_gap_preserves_known_x_write_without_enqueuing(self):
        p=plan(QueueState(),self.gate(origin_y_dword=None));self.assertFalse(p.complete)
        self.assertEqual(p.writes,(('global',0x56ffb8,4,10),));self.assertEqual(p.prospective_queue.records,())
    def test_post_queue_clock_gap_retains_only_prospective_record(self):
        p=plan(QueueState(),self.gate(caller_tick_dword=None));self.assertFalse(p.complete)
        self.assertEqual(p.queue.records,());self.assertEqual(len(p.prospective_queue.records),1);self.assertEqual(len(p.writes),2)
    def test_gate0_still_records_origin_and_starts(self):
        p=plan(QueueState(),self.gate(queue_gate_dword=0,queue_tick_dword=None));self.assertTrue(p.complete)
        self.assertEqual(p.queue.records,());self.assertEqual(len(p.writes),5)
    def test_displacement_parity_exact_less_equal_greater_unordered(self):
        for ah,clock_reached in ((0,True),(1,False),(0x40,False),(0x45,True)):
            o=self.gate(samples=((0x5f4,8,1),(0x5f8,32,0),(0x5fc,32,0)),
                global_samples=((0x56ffbc,0xffffffff),(0x56ffb8,10)),
                displacement_status_ah=ah,caller_tick_dword=3000 if clock_reached else None)
            p=plan(QueueState(),o);self.assertTrue(p.complete)
            self.assertEqual(p.status,'delos_step_cleared' if clock_reached else 'displacement_wait_no_clock')
            self.assertIn(('00460548/FUCOMPP10','signed origin DWORD y/x',-1,10),p.steps)
    def test_displacement_greater_still_waits_for3000(self):
        p=plan(QueueState(),self.gate(samples=((0x5f4,8,1),(0x5f8,32,100),(0x5fc,32,0)),
            global_samples=((0x56ffbc,20),(0x56ffb8,10)),displacement_status_ah=0,caller_tick_dword=3099))
        self.assertTrue(p.complete);self.assertEqual(p.status,'delos_wait');self.assertEqual(p.writes,())
    def test_bound_origin_writes_go_to_globals_not_object_fields(self):
        p=plan_source_route_step(RouteStartState({0x5e8:1}),self.bound(self.gate()))
        self.assertTrue(p.complete);self.assertEqual(p.state.globals[0x56ffb8],10)
        self.assertNotIn(0x56ffb8,p.state.fields);self.assertEqual(p.state.fields[0x5f8],40);self.assertEqual(len(p.queue.records),1)
        p=plan_source_route_step(RouteStartState({0x5e8:1}),self.bound(self.gate(),False))
        self.assertFalse(p.complete);self.assertNotIn(0x56ffb8,p.state.globals)
        self.assertEqual(p.prospective_state.globals[0x56ffb8],10);self.assertEqual(p.queue.records,())
    def test_earlier_gate_match_does_not_consume_delos(self):
        p=plan_source_route_gates(SourceRouteGatesObservation(comparisons=(('Gate Skill',True,1),),
            samples=((0x5f4,8,1),(0x5f8,32,0),(0x5fc,32,0)),caller_tick_dword=100,delos=Obs()))
        self.assertTrue(p.complete);self.assertIsNone(p.delos_plan)
    def test_false_delos_comparisons_defer_change_camp(self):
        p=plan(QueueState(),self.opened(comparisons=tuple((k,True,0) for k in ('Delos Gate Open','Delos Gate'))))
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_command_body');self.assertEqual(p.writes,())
    def test_generic_delos_parser_deferred_when_blocked_or_waiting(self):
        r=RouteRunner();r.start([RouteStep('Delos Gate',parameter1='not numeric')]);r.tick(0)
        self.assertEqual(r.tick(1,special_observation=SpecialRouteSnapshot(1,actor_raw_byte_554020=1)).kind,'blocked')
        r.special_state=SpecialRouteState(started=True,started_qword=0)
        self.assertEqual(r.tick(3000,special_observation=SpecialRouteSnapshot(3000,displacement=11)).kind,'step_complete')
    def test_types_and_read_order(self):
        for kw in (dict(metric_status_ah=256),dict(origin_x_dword=-1),dict(copy_returned=1)):
            with self.assertRaises(ValueError):Obs(**kw)
        with self.assertRaises(ValueError):plan(QueueState(),self.npc(global_samples=((0x554010,16),)))

if __name__=='__main__':unittest.main()
