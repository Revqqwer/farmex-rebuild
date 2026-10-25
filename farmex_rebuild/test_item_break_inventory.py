import unittest
from dataclasses import replace
from item_break_inventory import *

def slots(empty=(),last_pointer=0x12345678):
    values={slot:0 if slot in empty else last_pointer for slot in range(14,42)}
    return InventorySpaceObservation(True,{slot:True for slot in values},values)

def guard(empty=(14,),**changes):
    return replace(ItemBreakInventoryObservation(True,slots(empty),True,0,True,True,1,True,True,True,True),**changes)

class ItemBreakInventoryTests(unittest.TestCase):
    def test_scan_full_28_slots_preserves_last_eax_upper_bits(self):
        plan=InventorySpaceFrame().advance(slots())
        self.assertTrue(plan.complete);self.assertEqual(plan.result_eax,0x12345601)
        self.assertEqual(len(plan.calls),28);self.assertEqual(plan.empty_count,0)
        self.assertEqual(plan.calls[0],('004634a4',(14,)))
        self.assertEqual(plan.calls[-1],('004634a4',(41,)))

    def test_scan_first_empty_returns_zero_without_later_slot_needs(self):
        plan=InventorySpaceFrame().advance(InventorySpaceObservation(True,{14:True},{14:0}))
        self.assertEqual((plan.result_eax,plan.empty_count,len(plan.calls)),(0,1,1))

    def test_scan_threshold_is_signed_and_count_must_exceed_it(self):
        plan=InventorySpaceFrame(1).advance(slots((14,15)))
        self.assertEqual((plan.result_eax,plan.empty_count,len(plan.calls)),(0,2,2))
        plan=InventorySpaceFrame(1).advance(slots((41,)))
        self.assertEqual(plan.result_eax,1);self.assertEqual(plan.empty_count,1)
        plan=InventorySpaceFrame(0xffffffff).advance(InventorySpaceObservation(True,{14:True},{14:5}))
        self.assertEqual((plan.result_eax,plan.empty_count,len(plan.calls)),(0,0,1))

    def test_scan_getter_normal_and_pointer_are_separate_and_cached(self):
        frame=InventorySpaceFrame();plan=frame.advance(InventorySpaceObservation(True,pointers={14:0}))
        self.assertEqual(plan.needed,('normal',14))
        plan=frame.advance(InventorySpaceObservation(returned={14:True}))
        self.assertEqual(plan.needed,('pointer',14))
        plan=frame.advance(InventorySpaceObservation(pointers={14:0x100}))
        self.assertEqual(plan.needed,('normal',15))
        plan=frame.advance(InventorySpaceObservation(returned={15:True},pointers={14:0,15:0}))
        self.assertEqual(plan.result_eax,0);self.assertEqual(len(plan.calls),2)
        self.assertIs(frame.advance(slots()),plan)

    def test_full_branch_skips_mode_and_gem_and_stops_before_notice(self):
        frame=ItemBreakInventoryFrame();plan=frame.advance(guard(empty=(),mode_dword=None,stop_returned=False))
        self.assertEqual(plan.needed,'stop_returned')
        self.assertEqual([c[0] for c in plan.calls],['00463ac0','0040ae0c'])
        plan=frame.advance(ItemBreakInventoryObservation(stop_returned=True))
        self.assertEqual(plan.needed,'full_notice_returned')
        plan=frame.advance(ItemBreakInventoryObservation(full_notice_returned=True))
        self.assertEqual(plan.status,'inventory_full_stop_notice_returned');self.assertEqual(plan.next_address,0x4710d0)

    def test_scan_child_cannot_be_bypassed_by_inventory_parent_normal(self):
        frame=ItemBreakInventoryFrame();plan=frame.advance(guard(inventory_inputs=None))
        self.assertEqual(plan.needed,'inventory_inputs');self.assertEqual(plan.inventory.needed,('entry',None))
        plan=frame.advance(ItemBreakInventoryObservation(inventory_inputs=slots((14,))))
        self.assertEqual(plan.needed,'inventory_returned')

    def test_nonzero_mode_skips_gem_lookup(self):
        plan=ItemBreakInventoryFrame().advance(guard(mode_dword=0xffffffff,gem_lookup_eax=None))
        self.assertTrue(plan.complete);self.assertEqual(plan.status,'nonzero_mode_skips_gem')
        self.assertEqual(len(plan.calls),1)

    def test_any_nonzero_gem_al_is_present_even_when_upper_bits_vary(self):
        for low in range(1,256):
            plan=ItemBreakInventoryFrame().advance(guard(gem_lookup_eax=0xabcd0000|low))
            self.assertEqual(plan.status,'gem_present')
        missing=ItemBreakInventoryFrame().advance(guard(gem_lookup_eax=0xabcd0000))
        self.assertEqual(missing.status,'gem_missing_stop_notice_returned')

    def test_gem_cleanup_blocks_stop_and_consumed_lookup_is_retained(self):
        frame=ItemBreakInventoryFrame();plan=frame.advance(guard(gem_lookup_eax=0,gem_text_cleanup_returned=False))
        self.assertEqual(plan.needed,'gem_text_cleanup_returned');self.assertNotIn('0040ae0c',[c[0] for c in plan.calls])
        plan=frame.advance(ItemBreakInventoryObservation(gem_lookup_eax=1,gem_text_cleanup_returned=True))
        self.assertEqual(plan.needed,'stop_returned')
        plan=frame.advance(ItemBreakInventoryObservation(stop_returned=True,gem_notice_returned=True))
        self.assertEqual(plan.status,'gem_missing_stop_notice_returned')

    def test_gem_getter_return_and_raw_eax_are_separate(self):
        frame=ItemBreakInventoryFrame();plan=frame.advance(guard(gem_lookup_returned=False))
        self.assertEqual(plan.needed,'gem_lookup_returned')
        plan=frame.advance(ItemBreakInventoryObservation(gem_lookup_returned=True))
        self.assertEqual(plan.needed,'gem_lookup_eax')

    def test_guard_has_no_store_or_automatic_work_flag_mutation(self):
        frame=ItemBreakInventoryFrame();plan=frame.advance(guard(gem_lookup_eax=0))
        self.assertTrue(plan.complete);self.assertFalse(plan.native_execution_verified)
        self.assertFalse(plan.live_compatibility_verified)
        self.assertIs(frame.advance(ItemBreakInventoryObservation()),plan)

    def test_bound_caller_requires_guard_and_parent_before_second_work_read(self):
        frame=ItemBreakInventoryCycleFrame();caller=ItemBreakCycleObservation(True,1,1,1,second_work_byte=0)
        plan=frame.advance(caller,guard_parent_returned=True)
        self.assertEqual(plan.needed,('inventory_guard','entry_reached'))
        plan=frame.advance(ItemBreakCycleObservation(),guard())
        self.assertEqual(plan.needed,'guard_parent_returned')
        plan=frame.advance(ItemBreakCycleObservation(),guard_parent_returned=True)
        self.assertEqual(plan.needed,'second_work_byte')
        plan=frame.advance(ItemBreakCycleObservation(second_work_byte=0))
        self.assertTrue(plan.complete);self.assertEqual(plan.caller.status,'second_work_gate_zero')

    def test_guard_stop_does_not_invent_second_work_byte(self):
        frame=ItemBreakInventoryCycleFrame()
        plan=frame.advance(ItemBreakCycleObservation(True,1,1,1),guard(empty=()),guard_parent_returned=True)
        self.assertEqual(plan.inventory_guard.status,'inventory_full_stop_notice_returned')
        self.assertEqual(plan.needed,'second_work_byte')
        plan=frame.advance(ItemBreakCycleObservation(second_work_byte=1,npc_returned=True,npc_eax=0))
        self.assertEqual(plan.needed,'stop_returned')

    def test_first_work_zero_skips_typed_guard_without_forcing_inputs(self):
        plan=ItemBreakInventoryCycleFrame().advance(ItemBreakCycleObservation(True,1,1,0,second_work_byte=0))
        self.assertTrue(plan.complete);self.assertIsNone(plan.inventory_guard)

    def test_raw_guard_parent_override_is_rejected(self):
        with self.assertRaises(ValueError):
            ItemBreakInventoryCycleFrame().advance(ItemBreakCycleObservation(inventory_guard_returned=True))

    def test_types_and_slot_bounds(self):
        for args in ({'pointers':{13:0}},{'returned':{14:1}},{'pointers':{14:True}}):
            with self.assertRaises(ValueError):InventorySpaceObservation(**args)
        with self.assertRaises(ValueError):ItemBreakInventoryObservation(inventory_inputs={})
        with self.assertRaises(ValueError):ItemBreakInventoryObservation(gem_lookup_eax=-1)

if __name__=='__main__':unittest.main()
