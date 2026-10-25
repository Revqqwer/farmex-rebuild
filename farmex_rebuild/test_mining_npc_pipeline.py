import unittest
from mining_configuration import compile_mining_npc_flags,MiningPanelConfiguration,REPAIR,ORE
from mining_npc_pipeline import *
from routes import RouteRunner,RouteStep
from special_routes import SpecialRouteSnapshot

def cfg(skip=1,vip=0):return MiningPanelConfiguration('fixture',{0x603a:skip,0x604c:vip})

class MiningNpcPipelineTests(unittest.TestCase):
    def test_subset_compiler_ignores_unrelated_bad_number(self):
        c=compile_mining_npc_flags({REPAIR+'chDontRPRWithSell':True,ORE+'chMiningVipStorage':False,ORE+'txtOreCrashSpeed':'bad'})
        self.assertEqual(dict(c.fields),{0x603a:1,0x604c:0})

    def test_unknown_mode_does_not_reuse_stale_frame_mode(self):
        frame=NpcRouteFrame(3,{0x63c:0},{0x561f58:2,0x56fad2:1,0x56fae4:0})
        p=replay_mining_npc(cfg(),NpcRouteObservation(frame,{'Sundries':True}))
        self.assertFalse(p.complete);self.assertEqual(p.frame,frame)
        self.assertNotIn(0x561f58,p.prospective_frame.globals)
        self.assertEqual(p.missing,'global00561f58')

    def test_mode2_source_skip_then_mode1_source_repair_start(self):
        obs=NpcRouteObservation(NpcRouteFrame(3,{0x63c:0}),{'Sundries':True})
        a=replay_mining_npc(cfg(),obs,2);b=replay_mining_npc(cfg(),obs,1)
        self.assertEqual(a.frame.phase,4)
        self.assertEqual(b.frame.phase,3);self.assertEqual(b.frame.fields[0x63c],1)
        self.assertFalse(a.native_execution_verified);self.assertFalse(a.server_acknowledged)

    def test_unused_unknown_globals_do_not_invent_a_source_gate(self):
        c=MiningPanelConfiguration('partial',{})
        p=replay_mining_npc(c,NpcRouteObservation(NpcRouteFrame(9),{'Royal National Enchanter':False}))
        self.assertTrue(p.complete);self.assertFalse(p.projection.complete)
        self.assertTrue(p.result.returned_true);self.assertEqual(p.frame.phase,11)

    def test_incomplete_helper_keeps_accepted_frame_and_reports_prefix(self):
        frame=NpcRouteFrame(3,{0x63c:1},{0x561f58:2,0x56fad2:0,0x56fae4:0})
        p=replay_mining_npc(cfg(0),NpcRouteObservation(frame,{'Sundries':True}),2)
        self.assertFalse(p.complete);self.assertEqual(p.frame,frame)
        self.assertEqual(p.result.calls,('004edf34',));self.assertEqual(p.missing,'004edf34 return')

    def test_vip_path_requires_fresh_worker_observation(self):
        p=replay_mining_npc(cfg(1,1),NpcRouteObservation(NpcRouteFrame(5,{0x556:0,0x688:0},{0x5690cc:0}),{'Sundries':True}),2)
        self.assertTrue(p.complete);self.assertEqual(p.frame.globals[0x5690b8],1)
        q=replay_mining_npc(cfg(1,1),NpcRouteObservation(p.frame,{'Sundries':True}),2)
        self.assertEqual(q.frame.phase,5);self.assertEqual(q.frame.fields[0x688],1)

    def test_route_runner_copies_parameter1_and_uses_profiled_inner_step(self):
        runner=RouteRunner();runner.start([RouteStep('NPC',parameter1='Sundries')])
        runner.tick(0);runner.tick(1,special_observation=SpecialRouteSnapshot(1,actor_raw_byte_554020=0))
        o=NpcRouteObservation(NpcRouteFrame(3,texts={0x608:'old'}),{'Sundries':True})
        result=runner.tick(2,npc_observation=o,npc_profile_configuration=cfg(),npc_runtime_mode=2)
        self.assertEqual(result.kind,'waiting')
        self.assertEqual(runner.npc_profile_result.frame.phase,4)
        self.assertEqual(runner.npc_profile_result.frame.texts[0x608],'Sundries')

    def test_route_runner_rejects_mode_without_profile(self):
        with self.assertRaises(ValueError):RouteRunner().tick(0,npc_runtime_mode=2)

if __name__=='__main__':unittest.main()
