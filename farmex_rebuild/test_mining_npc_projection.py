import unittest
from mining_configuration import MiningPanelConfiguration,project_mining_npc_globals
from npc_route_engine import NpcRouteFrame,npc_route_step

class MiningNpcProjectionTests(unittest.TestCase):
    def test_missing_runtime_mode_never_inferred(self):
        p=project_mining_npc_globals(MiningPanelConfiguration('fixture',{0x603a:1,0x604c:0}))
        self.assertFalse(p.complete);self.assertEqual(p.missing,('runtime_mode_561f58',))
        self.assertNotIn(0x561f58,p.globals)

    def test_mode2_skips_repair_without_auto_sell_flag(self):
        p=project_mining_npc_globals(MiningPanelConfiguration('fixture',{0x603a:1,0x604c:0}),2)
        r=npc_route_step(NpcRouteFrame(3,globals=p.globals),{'Sundries':True})
        self.assertEqual(r.frame.phase,4);self.assertEqual(r.calls,())

    def test_other_mode_does_not_skip_repair(self):
        p=project_mining_npc_globals(MiningPanelConfiguration('fixture',{0x603a:1,0x604c:0}),1)
        r=npc_route_step(NpcRouteFrame(3,{0x63c:0},p.globals),{'Sundries':True})
        self.assertEqual(r.frame.phase,3);self.assertEqual(r.frame.fields[0x63c],1)

    def test_vip_projection_reaches_existing_npc_storage_path(self):
        p=project_mining_npc_globals(MiningPanelConfiguration('fixture',{0x603a:0,0x604c:1}),2)
        r=npc_route_step(NpcRouteFrame(5,{0x556:0,0x688:0},{**p.globals,0x5690cc:20}),{'Sundries':True})
        self.assertEqual(r.frame.globals[0x5690bc],2)
        self.assertEqual(r.frame.globals[0x5690b8],1)

if __name__=='__main__':unittest.main()
