import unittest
from dataclasses import replace
from zone_names import zone_name_ansi, DEFAULT_ANSI
from enchant_engine import EnchantObservation, enchant_step
from npc_route_engine import NpcRouteFrame, npc_route_step


class ZoneTests(unittest.TestCase):
    def test_known_groups_and_raw_default_bytes(self):
        for number,name in ((21,b'Moradon'),(22,b'Moradon'),(23,b'Moradon'),(6,b'Luferson'),
                  (8,b'EMC'),(14,b'Karus Eslant'),(16,b'Human Eslant'),(30,b'Delos Base'),
                  (32,b'Desp. Abbys'),(33,b'Hell Abbys'),(71,b'Ronark Land'),(72,b'Ardream')):
            self.assertEqual(zone_name_ansi(number),name)
        self.assertEqual(zone_name_ansi(0xffffffff),DEFAULT_ANSI)

    def test_zone_id_enchant_selects_same_script_bytes(self):
        fields={0x6c4:2,0x6c8:0,0x604:8}
        for number,byte7,byte9 in ((21,0x38,0x4e),(1,0x35,0x4b),(2,0x37,0x45),(71,0,0x4b)):
            observation=EnchantObservation(1000,b'0',0,current_target=8,raw_zone_id=number)
            packet=enchant_step(fields,observation).queue_payloads[0]
            self.assertEqual((packet[7],packet[9]),(byte7,byte9))

    def test_inn_zone_id_resolves_moradon_branch_without_zone_string(self):
        comparisons={'Potion':False,'Sundries':False,'Inn Hostess':True}
        for zone,distance,name in ((21,31,'Kronil'),(21,30,'Inn'),(1,None,'Inn')):
            result=npc_route_step(NpcRouteFrame(1),comparisons,{'00465960:'+name:9},
                                  raw_zone_id=zone,inn_distance=distance)
            self.assertEqual(result.frame.phase,2);self.assertIn('00465960:'+name,result.calls)

    def test_rejects_ambiguous_or_invalid_observations(self):
        with self.assertRaises(ValueError):EnchantObservation(1,zone_ansi=b'Moradon',raw_zone_id=21)
        with self.assertRaises(ValueError):npc_route_step(NpcRouteFrame(1),{},raw_zone_id=21,inn_in_moradon=True)
        for value in (True,-1,0x100000000):
            with self.assertRaises(ValueError):zone_name_ansi(value)
