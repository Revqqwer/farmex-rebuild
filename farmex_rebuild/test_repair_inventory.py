import unittest
from repair_inventory import RepairSlot,RepairInventoryObservation,count_repair_candidates,STARTUP_SLOTS
from repair_engine import RepairObservation,repair_step


class RepairInventoryTests(unittest.TestCase):
    def slots(self,bag=False):
        return {index:RepairSlot(0) for index in STARTUP_SLOTS+(tuple(range(14,42)) if bag else ())}

    def test_startup_slot3_counted_slot4_not_counted(self):
        slots=self.slots();slots[3]=RepairSlot(1,1,100);slots[4]=RepairSlot(2,1,100)
        r=count_repair_candidates(RepairInventoryObservation(slots,False))
        self.assertEqual(r.count,1);self.assertEqual(r.visited,STARTUP_SLOTS)

    def test_zero_id_short_circuits_unknown_metadata(self):
        self.assertEqual(count_repair_candidates(RepairInventoryObservation(self.slots(),False)).count,0)

    def test_damage_unsigned_equal_does_not_count(self):
        slots=self.slots();slots[1]=RepairSlot(1,0xffffffff,100);slots[3]=RepairSlot(1,100,100)
        self.assertEqual(count_repair_candidates(RepairInventoryObservation(slots,False)).count,0)

    def test_mode0_duplicate_cache_counts_each_record(self):
        slots=self.slots(True);slots[14]=RepairSlot(1,1,100,(7,7))
        r=count_repair_candidates(RepairInventoryObservation(slots,True,0,(7,7)))
        self.assertEqual(r.count,2);self.assertEqual(len(r.visited),35)

    def test_mode0_reread_change_is_observed_per_record(self):
        slots=self.slots(True);slots[14]=RepairSlot(1,1,100,(7,8))
        r=count_repair_candidates(RepairInventoryObservation(slots,True,0,(7,7)))
        self.assertEqual(r.count,1)

    def test_empty_cache_needs_no_reread(self):
        slots=self.slots(True);slots[14]=RepairSlot(1,1,100)
        self.assertEqual(count_repair_candidates(RepairInventoryObservation(slots,True,0,())).status,'complete')

    def test_mode2_short_circuit_true_then_unknown(self):
        slots=self.slots(True);slots[14]=RepairSlot(1,1,100,type_matches=(True,None))
        self.assertEqual(count_repair_candidates(RepairInventoryObservation(slots,True,2)).count,1)

    def test_missing_late_slot_prevents_final_count(self):
        slots=self.slots(True);del slots[41]
        r=count_repair_candidates(RepairInventoryObservation(slots,True))
        self.assertEqual(r.status,'needs_observation');self.assertEqual(r.missing,'slot41')

    def test_repair_phase0_uses_complete_inventory_zero(self):
        r=repair_step({0x640:0,0x644:0,0x604:8},{},RepairObservation(1000,current_target=8,
                       candidate_inventory=RepairInventoryObservation(self.slots(),False)))
        self.assertEqual(r.returned_phase,42)

    def test_repair_unknown_inventory_does_not_false_complete42(self):
        r=repair_step({0x640:0,0x644:0,0x604:8},{},RepairObservation(1000,current_target=8,
                       candidate_inventory=RepairInventoryObservation({},False)))
        self.assertEqual(r.status,'needs_observation');self.assertEqual(r.returned_phase,0)

    def test_candidate_bag_and_mode_come_from_short_circuit_raw_frame(self):
        slots=self.slots(True);slots[14]=RepairSlot(1,1,100,())
        r=repair_step({0x640:0,0x644:0,0x604:8,0x555:1},{0x561f58:0},
                     RepairObservation(1000,current_target=8,
                         candidate_inventory=RepairInventoryObservation(slots,cache_ids=())))
        self.assertEqual(r.returned_phase,42)

    def test_source_snapshot_copies_mutable_cache_lists(self):
        rereads=[7];ids=[7];slot=RepairSlot(1,1,100,rereads)
        obs=RepairInventoryObservation({14:slot},True,0,ids)
        rereads[0]=8;ids[0]=8
        self.assertEqual(obs.slots[14].cache_slot_rereads,(7,));self.assertEqual(obs.cache_ids,(7,))
