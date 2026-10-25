import unittest,copy
from mining_repair_routes import *
from routes import RouteRunner

class MiningRepairRouteTests(unittest.TestCase):
    def test_three_regions_offsets_counts_and_order(self):
        for branch,region,name,offset,count in (
            (1,'EMC','EMCMiningRoute2',0x4c4,15),
            (2,'Luferson','LFCMiningRoute2',0x3df4,23),
            (3,'Moradon','MoradonMiningRoute2',0x2ae4,31)):
            with self.subTest(branch=branch):
                p=load_mining_repair_route(branch)
                self.assertTrue(p.complete);self.assertEqual((p.region,p.name,p.source_offset),(region,name,offset))
                self.assertEqual(len(p.steps),count);self.assertEqual(len(p.rows),count)
                self.assertEqual(sum(s.command=='NPC' for s in p.steps),1)

    def test_npc_unknown_second_preserved_not_reported_as_empty_source(self):
        p=load_mining_repair_route(1)
        self.assertEqual(p.unknown_unused_second_fields,(4,))
        self.assertEqual(p.rows[4],('NPC','Sundries',None))
        self.assertEqual(p.steps[4].parameter1,'Sundries')
        self.assertFalse(p.native_pointer_blob_reconstructed)

    def test_local_runner_uses_recovered_coordinates(self):
        p=load_mining_repair_route(3);runner=RouteRunner();runner.start(p.steps)
        self.assertEqual(runner.tick(0).kind,'selected')
        d=runner.tick(1,distance=10)
        self.assertEqual(d.kind,'move')
        self.assertEqual((d.x,d.y),(float(p.rows[0][1]),float(p.rows[0][2])))
        self.assertEqual(runner.tick(2,distance=0).kind,'step_complete')

    def test_missing_route_is_a_gap(self):
        p=load_mining_repair_route(1,{})
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_route_catalog')

    def test_unrecovered_command_refused(self):
        c=load_mining_routes();c=copy.deepcopy(c);c['EMCMiningRoute2']['records'][0]['literal_recovered']=False
        self.assertFalse(load_mining_repair_route(1,c).complete)

    def test_source_binding_mismatch_refused(self):
        c=copy.deepcopy(load_mining_routes());c['EMCMiningRoute2']['slot_offset']='0x0'
        self.assertEqual(load_mining_repair_route(1,c).status,'route_catalog_binding_mismatch')

    def test_missing_coordinate_not_zero_filled(self):
        c=copy.deepcopy(load_mining_routes());c['EMCMiningRoute2']['records'][0]['parameter_2_text']=None
        p=load_mining_repair_route(1,c)
        self.assertFalse(p.complete);self.assertEqual(p.steps,())
        self.assertIsNone(p.rows[0][2])

    def test_branch_validation(self):
        for value in (True,0,4,'EMC'):
            with self.assertRaises(ValueError):load_mining_repair_route(value)

if __name__=='__main__':unittest.main()
