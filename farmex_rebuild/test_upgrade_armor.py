import unittest
from dataclasses import replace
from upgrade_armor import (VENDORS,TEMPLATE,FOLLOWUP,ArmorFreeSlotObservation,ArmorPacketObservation,
                           plan_armor_free_slot,plan_armor_packet)
from upgrade_packets import UpgradeItemObservation


class ArmorPacketTests(unittest.TestCase):
    def observation(self,**kw):
        return replace(ArmorPacketObservation(0x1234,vendor_matches={name:name=='Armor' for name,code in VENDORS}),**kw)

    def packet(self,o=None):
        return plan_armor_packet(0xaabbccdd,0xffff0003,0x11223344,0x1234,0xff,o or self.observation())

    def test_exact_twenty_byte_fields_and_followup_pair(self):
        p=self.packet()
        self.assertTrue(p.complete);self.assertFalse(p.independently_verified)
        self.assertEqual(p.packets,((bytes.fromhex('210111150300ddccbbaa014433221134030034ff'),0),(b'\x6a\x02',100)))
        self.assertEqual((len(TEMPLATE),FOLLOWUP),(20,b'\x6a\x02'))
        self.assertEqual(p.calls[-3:],(('004c7710',0x561ef8,20,0),('004c911c',0x561ef8),('004c7710',0x561ef8,2,100)))

    def test_vendor_last_match_wins_and_all_six_are_evaluated(self):
        p=self.packet(self.observation(vendor_matches={n:True for n,c in VENDORS}))
        self.assertEqual(p.vendor_dword,0x43df0)
        self.assertEqual([c[1] for c in p.calls if c[0]=='00505d20'],[n for n,c in VENDORS])

    def test_no_match_has_no_invented_vendor_zero(self):
        o=self.observation(vendor_matches={n:False for n,c in VENDORS})
        p=self.packet(o)
        self.assertFalse(p.complete);self.assertIn('uninitialized vendor',p.missing)
        self.assertEqual(p.packets,())
        p=self.packet(replace(o,initial_vendor_dword=0xdeadbeef))
        self.assertEqual(p.packets[0][0][2:6],bytes.fromhex('efbeadde'))

    def test_missing_later_vendor_does_not_accept_an_earlier_match(self):
        o=self.observation(vendor_matches={'Sundries':False,'Armor':True})
        p=self.packet(o)
        self.assertFalse(p.complete);self.assertEqual(p.vendor_dword,0x31511)
        self.assertIn('Weapon',p.missing);self.assertEqual(p.packets,())

    def test_first_zero_scan_early_return_last_slot_and_full_sentinel(self):
        p=plan_armor_free_slot(ArmorFreeSlotObservation({14:0,15:object()}))
        self.assertEqual((p.result_word,p.visited_slots),(0,(14,)))
        samples={s:1 for s in range(14,42)};samples[41]=0
        self.assertEqual(plan_armor_free_slot(ArmorFreeSlotObservation(samples)).result_word,27)
        samples[41]=1
        p=plan_armor_free_slot(ArmorFreeSlotObservation(samples))
        self.assertEqual((p.result_word,len(p.visited_slots)),(255,28))

    def test_missing_getter_does_not_mean_zero_or_full(self):
        p=plan_armor_free_slot(ArmorFreeSlotObservation({14:1}))
        self.assertFalse(p.complete);self.assertIsNone(p.result_word)
        self.assertEqual(p.visited_slots,(14,15))

    def test_bound_getter_zero_is_a_helper_observation_not_a_name_query(self):
        item=UpgradeItemObservation(0x1000,4,8,0x2000,0x3000,0)
        scan=ArmorFreeSlotObservation({14:item})
        p=self.packet(self.observation(free_slot_word=None,free_scan=scan))
        self.assertTrue(p.complete);self.assertEqual(p.packets[0][0][15],0)
        self.assertEqual(len(p.free_plan.item_plans[0][1].reads),3)

    def test_full_sentinel_is_serialized_without_an_invented_guard(self):
        scan=ArmorFreeSlotObservation({s:1 for s in range(14,42)})
        p=self.packet(self.observation(free_slot_word=None,free_scan=scan))
        self.assertTrue(p.complete);self.assertEqual(p.packets[0][0][15],255)

    def test_quantity_unknown_prevents_later_scan_and_conflict_is_reached_only_later(self):
        o=self.observation(free_scan=ArmorFreeSlotObservation())
        p=plan_armor_packet(1,None,2,0,0,o)
        self.assertFalse(p.complete);self.assertEqual(p.calls,())
        with self.assertRaises(ValueError):self.packet(o)

    def test_parameter_widths_and_normalized_vendor_types(self):
        for bad in (True,-1,1<<32):
            with self.assertRaises(ValueError):plan_armor_packet(bad,1,1,0,0,self.observation())
        with self.assertRaises(ValueError):ArmorPacketObservation(free_slot_word=1<<16)
        with self.assertRaises(ValueError):ArmorFreeSlotObservation({42:0})
        with self.assertRaises(ValueError):
            self.packet(self.observation(vendor_matches={'Sundries':1}))
