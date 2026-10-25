import unittest
from repair_packets import repair_payload
from repair_engine import RepairObservation, repair_step
from npc_route_engine import NpcRouteFrame,NpcRouteObservation
from routes import RouteRunner,RouteStep
from special_routes import SpecialRouteSnapshot


class RepairPacketTests(unittest.TestCase):
    def test_equipment_exact_layout_and_little_endian_full_ids(self):
        self.assertEqual(repair_payload(1,0x12345678,12,0x90abcdef).hex(),'3b010c78563412efcdab90')

    def test_inventory_slot14_zero_slot41_27_and_wrap(self):
        for slot,expected in ((14,0),(41,27),(13,255),(0x1234,0x26)):
            self.assertEqual(repair_payload(2,8,slot,1)[2],expected)
            self.assertEqual(len(repair_payload(2,8,slot,1)),11)

    def test_zero_item_id_is_not_fabricated_into_another_id(self):
        self.assertEqual(repair_payload(1,8,1,0)[7:],b'\0'*4)

    def observation(self,item=None):
        return RepairObservation(1000,current_target=8,item_id_4634a4=100,
                                 durability_46358c=1,maximum_4635e0=100,
                                 producer_item_id_4634a4=item)

    def fields(self):return {0x640:1,0x644:0,0x604:8,0x63c:1}

    def test_missing_second_read_stops_before_wait_and_packet(self):
        r=repair_step(self.fields(),{},self.observation())
        self.assertEqual(r.status,'needs_observation');self.assertEqual(r.queue_payloads,())
        self.assertEqual(r.fields[0x644],0);self.assertEqual(r.globals[0x561fb0],0xffffffff)

    def test_changed_item_uses_producer_reread(self):
        r=repair_step(self.fields(),{},self.observation(200))
        self.assertEqual(int.from_bytes(r.queue_payloads[0][7:],'little'),200)
        self.assertEqual(r.fields[0x644],1)

    def test_packet_survives_npc_and_route_integration(self):
        runner=RouteRunner();runner.start([RouteStep('NPC',parameter1='Sundries')])
        runner.tick(0);runner.tick(1,special_observation=SpecialRouteSnapshot(1,actor_raw_byte_554020=0))
        observation=NpcRouteObservation(NpcRouteFrame(3,self.fields(),{0x561f58:0}),
                                       {'Sundries':True},repair_observation=self.observation(200))
        result=runner.tick(1000,special_observation=SpecialRouteSnapshot(1000),npc_observation=observation)
        self.assertEqual(result.queue_payloads,(repair_payload(1,8,1,200),))
        self.assertEqual(result.kind,'waiting');self.assertTrue(runner.processing)
