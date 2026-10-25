import unittest
from dataclasses import replace
from source_route_gates import SourceRouteGatesObservation as Obs,plan_source_route_gates as plan
from source_route_step import SourceRouteStepObservation,plan_source_route_step
from source_route_commands import SourceRouteCommandsObservation
from source_route_coordinate import RouteCoordinateObservation
from route_start_state import RouteStartState
from route_resume import RouteResumeState,RouteResumeObservation
from route_progress import RouteProgressObservation,plan_route_progress
from source_coin import GuardedDwordSample as Word,GuardedByteSample as Byte
from action_queue import QueueState,QueueRecord
from special_routes import SpecialCommand,SpecialRouteSnapshot,SpecialRouteState,special_route_step

def actor(value=0):return RouteResumeObservation(((0x553e7c,1),(0x554020,0x20)),Word(1,1,0x100),Byte(0x120,1,value))

class SourceRouteGatesTests(unittest.TestCase):
    def sample(self,kind='Gate Open',**kw):
        comparisons=[]
        for name in ('Gate Skill','Gate Open','Gate'):
            comparisons.append((name,True,1 if name==kind else 0))
            if name==kind:break
        values=dict(comparisons=tuple(comparisons),samples=((0x5f4,8,0),),actor=actor(),helper_returned=True,
            parse_returned=True,parameter_dword=0x12345678,copy_returned=True,queue_gate_dword=1,
            queue_tick_dword=10,queue_returned=True,caller_tick_dword=20)
        values.update(kw);return Obs(**values)
    def bound(self,o,return_index=True):
        commands=SourceRouteCommandsObservation(wait_comparison_returned=True,wait_comparison_al=0,
            posture_predicate_returned=True,posture_match_byte=0,gates=o)
        samples=((0x5e8,8,1),(0x5ec,32,0)) if return_index else ((0x5e8,8,1),)
        return SourceRouteStepObservation(samples,True,0,coordinate=RouteCoordinateObservation(True,0),commands=commands)
    def test_correct_skill_helper_has_no_packet_or_parameter_dependency(self):
        p=plan(self.sample('Gate Skill',parse_returned=None,parameter_dword=None,copy_returned=None,queue_gate_dword=None,queue_tick_dword=None))
        self.assertTrue(p.complete);self.assertEqual(p.kind,'Gate Skill');self.assertIsNone(p.payload)
        self.assertEqual(p.queue.records,());self.assertIn(('normal_return','004c8d84(00561ef8) normal return'),p.steps)
    def test_open_and_gate_payloads_and_independent_queue_caller_clocks(self):
        for kind,payload in (('Gate Open',bytes.fromhex('3378563412')),('Gate',bytes.fromhex('4b78563412'))):
            p=plan(self.sample(kind));self.assertTrue(p.complete);self.assertEqual(p.payload,payload)
            self.assertEqual(len(p.queue.records),1);self.assertEqual(p.queue.records[0].payload,payload)
            self.assertEqual(p.queue.records[0].created_tick,10);self.assertEqual(p.queue.records[0].delay_dword,0)
            self.assertEqual(p.writes,(('object',0x5f8,4,20),('object',0x5fc,4,0),('object',0x5f4,1,1)))
    def test_gate_parameter_low_dword_is_not_range_limited(self):
        p=plan(self.sample('Gate',parameter_dword=0xffffffff));self.assertEqual(p.payload,bytes.fromhex('4bffffffff'))
    def test_skill_open_gate_wait_boundaries_match_source_not_old_names(self):
        for kind,wait in (('Gate Skill',3000),('Gate Open',1500),('Gate',3000)):
            for tick,done in ((100+wait-1,False),(100+wait,True)):
                p=plan(self.sample(kind,samples=((0x5f4,8,1),(0x5f8,32,100),(0x5fc,32,0)),
                    caller_tick_dword=tick,actor=RouteResumeObservation(),helper_returned=None,parse_returned=None))
                self.assertTrue(p.complete);self.assertEqual(len(p.writes),2 if done else 0)
                self.assertIsNone(p.actor_plan);self.assertEqual(p.queue.records,())
    def test_wait_uses_full_qword_signed_delta(self):
        p=plan(self.sample(samples=((0x5f4,8,1),(0x5f8,32,0),(0x5fc,32,1)),caller_tick_dword=0))
        self.assertTrue(p.complete);self.assertEqual(p.status,'gate_wait');self.assertEqual(p.writes,())
    def test_actor_nonzero_skips_parse_queue_and_clock(self):
        p=plan(self.sample(actor=actor(2),parse_returned=None,caller_tick_dword=None))
        self.assertTrue(p.complete);self.assertEqual(p.status,'gate_actor_blocked');self.assertIsNone(p.payload)
        self.assertEqual(p.writes,())
    def test_comparison_order_and_normal_return_gaps(self):
        with self.assertRaises(ValueError):plan(self.sample(comparisons=(('Gate Open',True,1),)))
        for rows in ((),(('Gate Skill',None,1),),(('Gate Skill',True,None),)):
            p=plan(self.sample(comparisons=rows));self.assertFalse(p.complete);self.assertEqual(p.writes,())
    def test_all_false_defers_delos_body_instead_of_clearing(self):
        p=plan(self.sample(comparisons=tuple((k,True,0) for k in ('Gate Skill','Gate Open','Gate'))))
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_command_body');self.assertEqual(p.writes,())
    def test_parse_copy_and_queue_return_are_independent(self):
        for kw in (dict(parse_returned=None),dict(parameter_dword=None),dict(copy_returned=None),dict(queue_returned=None)):
            p=plan(self.sample(**kw));self.assertFalse(p.complete);self.assertEqual(p.queue.records,());self.assertEqual(p.writes,())
    def test_queue_gate_zero_still_arms_caller_without_queue_clock(self):
        p=plan(self.sample(queue_gate_dword=0,queue_tick_dword=None))
        self.assertTrue(p.complete);self.assertEqual(p.queue_decision.status,'not_enqueued');self.assertEqual(p.queue.records,())
        self.assertEqual(p.writes[-1],('object',0x5f4,1,1))
    def test_missing_queue_gate_or_reached_queue_clock_holds(self):
        for kw in (dict(queue_gate_dword=None),dict(queue_tick_dword=None)):
            p=plan(self.sample(**kw));self.assertFalse(p.complete);self.assertEqual(p.queue.records,())
    def test_missing_post_queue_clock_preserves_one_prospective_record(self):
        seed=QueueState((QueueRecord(1,b'old',1,0),),2)
        o=self.sample(queue_state=seed,caller_tick_dword=None)
        p=plan(o);self.assertFalse(p.complete);self.assertEqual(p.queue,seed);self.assertEqual(len(p.prospective_queue.records),2)
        q=plan(replace(o,caller_tick_dword=20));self.assertTrue(q.complete)
        self.assertEqual(len(q.queue.records),2);self.assertEqual(q.queue.records[-1].record_id,2)
    def test_bound_parent_missing_return_index_does_not_commit_queue(self):
        p=plan_source_route_step(RouteStartState(),self.bound(self.sample(),False))
        self.assertFalse(p.complete);self.assertEqual(p.queue.records,());self.assertEqual(len(p.prospective_queue.records),1)
        self.assertEqual(len(p.writes),3)
        q=plan_source_route_step(RouteStartState(),self.bound(self.sample()))
        self.assertTrue(q.complete);self.assertEqual(len(q.queue.records),1);self.assertEqual(q.state.fields[0x5f4],1)
    def test_bound_progress_gap_keeps_queue_prospective_until_caller_complete(self):
        step=plan_source_route_step(RouteStartState(),self.bound(self.sample()))
        samples=(('object',0x566,8,0),('object',0x567,8,0))
        p=plan_route_progress(RouteResumeState(1,0),RouteProgressObservation(samples,step_execution=step))
        self.assertFalse(p.complete);self.assertEqual(p.queue.records,());self.assertEqual(len(p.prospective_queue.records),1)
        samples+=(('object',0x5f0,32,1),('object',0x5e8,8,1))
        p=plan_route_progress(RouteResumeState(1,0),RouteProgressObservation(samples,step_execution=step))
        self.assertTrue(p.complete);self.assertEqual(p.status,'step_processing_no_motion');self.assertEqual(len(p.queue.records),1)
    def test_unreached_step_does_not_expose_bound_queue(self):
        step=plan_source_route_step(RouteStartState(),self.bound(self.sample()))
        p=plan_route_progress(RouteResumeState(1,0),RouteProgressObservation(step_execution=step))
        self.assertFalse(p.complete);self.assertIsNone(p.step_execution);self.assertIsNone(p.queue)
    def test_generic_gate_semantics_match_raw_source_mapping(self):
        s=SpecialRouteSnapshot(20,actor_raw_byte_554020=0)
        for kind,wait,payload in (('Gate Skill',3000,None),('Gate Open',1500,b'\x33\x05\0\0\0'),('Gate',3000,b'\x4b\x05\0\0\0')):
            c=SpecialCommand(kind,5);r=special_route_step(c,s)
            self.assertEqual(r.queue_payloads,() if payload is None else (payload,))
            if kind=='Gate Skill':self.assertEqual(r.calls,('004c8d84',))
            before=special_route_step(c,replace(s,now_ms=wait-1),SpecialRouteState(started=True,started_qword=0))
            self.assertEqual(before.status,'waiting')
    def test_types_and_missing_actor(self):
        for kw in (dict(parameter_dword=-1),dict(queue_returned=1),dict(caller_tick_dword=True)):
            with self.assertRaises(ValueError):Obs(**kw)
        p=plan(self.sample(actor=RouteResumeObservation()));self.assertFalse(p.complete);self.assertEqual(p.writes,())

if __name__=='__main__':unittest.main()
