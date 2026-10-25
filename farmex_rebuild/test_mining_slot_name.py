import unittest
from dataclasses import replace
from mining_slot_name import *
from mining_engine import OreSlotState,OreSlotSnapshot,process_ore_slot

def fixture(name=b'Mysterious Ore',base=123000,variant=456):
    return SlotNameObservation(0x100,0x20,0x30,0x200,0x300,0x400,0x500,0x600,base,variant,
        ItemNameObservation(metadata_category=3,storage_dword=max(16,len(name)),pointer_dword=0x700,
                            bad_read_result=0,captured=name.ljust(16,b'\0')))

class SlotNameTests(unittest.TestCase):
    def test_seven_ordered_read_addresses_and_unsigned_id(self):
        result=plan_slot_name(14,fixture())
        self.assertEqual(result.item_id,123456)
        self.assertEqual([a for _,a in result.reads],[0x100,0x220,0x368,0x460,0x464,0x500,0x600])
        self.assertEqual(result.ansi_bytes,b'Mysterious Ore')
        self.assertEqual(result.name_plan.family,'metadata')

    def test_unsigned_variant_remainder_and_add_wrap(self):
        result=plan_slot_name(14,fixture(base=0xffffffff,variant=0xffffffff))
        self.assertEqual(result.item_id,294)

    def test_address_math_wraps_and_no_slot_range_invented(self):
        result=plan_slot_name(0xffffffff,replace(fixture(),inventory=0xfffffff0,offset_5540ac=0x30))
        self.assertEqual(result.reads[2][1],0x1c)

    def test_zero_record_is_empty_and_no_later_reads(self):
        result=plan_slot_name(14,replace(fixture(),record=0,lookup_pointer=None,metadata_pointer=None))
        self.assertEqual(result.ansi_bytes,b'')
        self.assertEqual(len(result.reads),3)

    def test_missing_record_does_not_mean_empty(self):
        result=plan_slot_name(14,replace(fixture(),record=None))
        self.assertIsNone(result.ansi_bytes)
        self.assertEqual(result.missing,'record')

    def test_zero_pointer_does_not_skip_source_read(self):
        result=plan_slot_name(14,replace(fixture(),lookup_pointer=0,base_item=None))
        self.assertEqual(result.reads[-1],('0045dc44',0))
        self.assertEqual(result.missing,'base_item')

    def test_incomplete_capture_is_not_recognized_name(self):
        obs=fixture();obs=replace(obs,name=replace(obs.name,captured=b'Mysterious'))
        result=plan_slot_name(14,obs)
        self.assertIsNone(result.ansi_bytes)
        self.assertIn('complete_captured_bytes',result.missing)

    def test_child_to_name_to_request(self):
        child=process_ore_slot(OreSlotState(),OreSlotSnapshot(True,None,True),2000,1,False)
        result=plan_slot_name_request(child,fixture())
        self.assertEqual(result.request.status,'locally_serialized')
        self.assertEqual(result.request.packets[1][0][1],0)
        self.assertFalse(result.request.context_preparation_verified)
        self.assertFalse(result.request.server_acknowledged)

    def test_blocked_cadence_performs_no_name_resolution(self):
        child=process_ore_slot(OreSlotState(),OreSlotSnapshot(),500,1,False)
        result=plan_slot_name_request(child)
        self.assertIsNone(result.name)
        self.assertEqual(result.request.status,'request_not_reached')

    def test_missing_post_preparation_capture_remains_explicit(self):
        child=process_ore_slot(OreSlotState(),OreSlotSnapshot(True,None,True),2000,1,False)
        result=plan_slot_name_request(child)
        self.assertEqual(result.name.missing,'global_553e80')
        self.assertFalse(result.request.complete)

if __name__=='__main__':unittest.main()
