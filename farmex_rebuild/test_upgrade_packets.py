import unittest
from dataclasses import replace
from upgrade_packets import (TEMPLATE,UpgradeItemObservation,UpgradePacketObservation,
                             plan_upgrade_item,plan_upgrade_packet)


class UpgradePacketTests(unittest.TestCase):
    def item(self, **kw):
        return replace(UpgradeItemObservation(0x1000,4,8,0x2000,0x3000,0x4000,
                                              0x5000,0x6000,1000,1002),**kw)

    def test_exact_size_offsets_order_and_retained_template(self):
        p=plan_upgrade_packet(0x11223344,0x105,0x1ff,
                             UpgradePacketObservation(0x55667788,0xaabbccdd))
        self.assertTrue(p.complete);self.assertEqual(len(p.payload),57)
        self.assertEqual(p.payload[:17],bytes.fromhex('5b020144332211ddccbbaa0588776655ff'))
        self.assertEqual(p.payload[17:],TEMPLATE[17:])
        self.assertEqual(p.calls,(('004634a4',0x20d),('004634a4',0x113),('004c7710',0x561ef8,57,0)))
        self.assertFalse(p.independently_verified)

    def test_dword_slot_addition_and_low_byte_copy_are_distinct(self):
        p=plan_upgrade_packet(0,0xffffffff,0xfffffff8,UpgradePacketObservation(0,0))
        self.assertEqual(p.calls[:2],(('004634a4',6),('004634a4',13)))
        self.assertEqual((p.payload[11],p.payload[16]),(255,248))

    def test_zero_record_returns_zero_after_three_reads(self):
        p=plan_upgrade_item(14,self.item(record=0,base_pointer=None,variant_pointer=None))
        self.assertTrue(p.complete);self.assertEqual(p.result_dword,0)
        self.assertEqual(p.reads,(('0045dc44',0x1000),('0045dc44',0x2004),('0045dc44',0x3040)))

    def test_unsigned_variant_modulo_and_wrapped_add(self):
        p=plan_upgrade_item(14,self.item(base_item=0xffffffff,variant_item=0xffffffff))
        self.assertEqual(p.result_dword,294)
        self.assertEqual([r[1] for r in p.reads],[0x1000,0x2004,0x3040,0x4060,0x4064,0x5000,0x6000])

    def test_bound_getters_are_fresh_independent_and_name_free(self):
        p=plan_upgrade_packet(7,1,2,UpgradePacketObservation(
            scroll_item_inputs=self.item(base_item=0xaaaa0000),
            target_item_inputs=self.item(base_item=0xbbbb0000,variant_item=1003)))
        self.assertTrue(p.complete)
        self.assertEqual(int.from_bytes(p.payload[7:11],'little'),0xbbbb0003)
        self.assertEqual(int.from_bytes(p.payload[12:16],'little'),0xaaaa0002)
        self.assertEqual(p.item_plans[0][1].reads[2][1],0x3048)
        self.assertEqual(p.item_plans[1][1].reads[2][1],0x3044)

    def test_each_missing_read_remains_a_gap(self):
        fields=('root','inventory','record','base_pointer','variant_pointer','base_item','variant_item')
        for index,name in enumerate(fields):
            p=plan_upgrade_item(14,self.item(**{name:None}))
            self.assertFalse(p.complete);self.assertIsNone(p.result_dword)
            self.assertEqual(len(p.reads),index+1)

    def test_first_getter_gap_does_not_reach_second_conflict(self):
        o=UpgradePacketObservation(target_item_dword=1,target_item_inputs=self.item())
        p=plan_upgrade_packet(1,0,0,o)
        self.assertFalse(p.complete);self.assertEqual(p.calls,(('004634a4',14),))
        self.assertIsNone(p.payload)
        with self.assertRaises(ValueError):
            plan_upgrade_packet(1,0,0,replace(o,scroll_item_dword=1))

    def test_anvil_gap_is_after_both_getters_and_never_enqueues(self):
        p=plan_upgrade_packet(None,1,2,UpgradePacketObservation(3,4))
        self.assertFalse(p.complete);self.assertEqual(len(p.calls),2)
        self.assertIn('anvil',p.missing);self.assertIsNone(p.payload)

    def test_raw_width_and_observation_types(self):
        for bad in (True,-1,1<<32):
            with self.assertRaises(ValueError):
                plan_upgrade_packet(bad,0,0,UpgradePacketObservation())
            with self.assertRaises(ValueError):
                UpgradeItemObservation(root=bad)
        with self.assertRaises(ValueError):
            UpgradePacketObservation(scroll_item_inputs={})
