import unittest
from dataclasses import replace
from merchant_sell_selection import SellPreparedRow as Row,SellSelectionObservation as Obs,plan_sell_selection as plan
from operation_engine import MerchantSettings,MerchantKind,MerchantRunner,MerchantSnapshot

class SellSelectionTests(unittest.TestCase):
    def observation(self,**changes):
        return replace(Obs((Row(77,10,0x100000003),),True,(77,)+(0,)*27,(0,)*28,(20,)),**changes)
    def test_inventory_order_never_selects_unlisted_item(self):
        p=plan(True,self.observation(item_results=(99,)))
        self.assertTrue(p.complete);self.assertEqual(p.status,'unmatched');self.assertFalse(p.requires_tail_return)
    def test_inventory_zero_short_circuits_used_and_vector(self):
        p=plan(True,Obs(item_results=(0,)))
        self.assertEqual(p.status,'unmatched');self.assertEqual(p.calls,(('004634a4',14),))
    def test_used_inventory_slot_skips_unknown_vector(self):
        p=plan(True,Obs(item_results=(77,),used_bytes=(255,)))
        self.assertEqual(p.status,'unmatched')
    def test_inventory_duplicate_rows_choose_first(self):
        p=plan(True,self.observation(rows=(Row(77,10,3),Row(77,20,8))))
        self.assertEqual((p.row_index,p.quantity_dword,p.price_dword),(0,10,3))
    def test_list_order_skips_nonmatching_ids_without_used_reads(self):
        p=plan(False,self.observation(item_results=(99,77),used_bytes=(None,0)))
        self.assertEqual(p.inventory_slot,15);self.assertEqual(p.price_dword,3)
        self.assertEqual(p.calls,(('004634a4',14),('004634a4',15),('00463538',15)))
    def test_list_order_skips_already_used_matching_slot(self):
        p=plan(False,self.observation(item_results=(77,77),used_bytes=(1,0)))
        self.assertEqual(p.inventory_slot,15)
    def test_quantity_clamp_uses_second_fresh_result_without_reclamping(self):
        p=plan(True,self.observation(quantity_results=(5,100)))
        self.assertEqual(p.quantity_dword,100);self.assertEqual(p.calls[-2:],(('00463538',14),('00463538',14)))
    def test_quantity_comparison_is_signed(self):
        p=plan(True,self.observation(quantity_results=(0x80000000,7)))
        self.assertEqual(p.quantity_dword,7)
    def test_missing_second_quantity_is_not_first_result(self):
        p=plan(True,self.observation(quantity_results=(5,)))
        self.assertFalse(p.complete);self.assertIn('second',p.missing)
    def test_missing_item_and_unknown_vector_stay_unknown(self):
        self.assertFalse(plan(True,self.observation(item_results=())).complete)
        self.assertFalse(plan(False,self.observation(stable_rows=None)).complete)
    def test_list_order_does_not_invent_zero_id_guard(self):
        p=plan(False,self.observation(rows=(Row(0,1,3),),item_results=(0,)))
        self.assertEqual(p.status,'selected');self.assertEqual(p.item_dword,0)
    def test_no_list_match_reads_all_28_items(self):
        p=plan(False,self.observation(item_results=(99,)*28,used_bytes=()))
        self.assertEqual(p.status,'unmatched');self.assertEqual(len(p.calls),28)
    def test_runner_match_requires_distinct_tail_return(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL,sell_inventory_order=True));r.start();r.phase=3
        snapshot=MerchantSnapshot(1,sale_session_ready=True,item_pending=False,prepared_slot_count=0,
            sell_selection_inputs=self.observation())
        self.assertEqual(r.tick(snapshot).status,'needs_adapter');self.assertEqual(r.inventory_slot,14)
        p=r.tick(replace(snapshot,now_ms=2,sell_slot_helper_returned=True))
        self.assertEqual(r.inventory_slot,15);self.assertEqual(p.intents[0].item_id,77)
    def test_runner_unlisted_slot_only_advances_traversal(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL,sell_inventory_order=True));r.start();r.phase=3
        p=r.tick(MerchantSnapshot(1,sale_session_ready=True,item_pending=False,prepared_slot_count=0,
            sell_selection_inputs=self.observation(item_results=(99,))))
        self.assertEqual(p.status,'slot_unmatched');self.assertEqual(p.intents,());self.assertEqual(r.inventory_slot,15)
    def test_unknown_row_count_is_not_empty_list_completion(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=3
        p=r.tick(MerchantSnapshot(1,sale_session_ready=True,item_pending=False,prepared_slot_count=0,sell_selection_inputs=Obs()))
        self.assertEqual(p.status,'needs_adapter');self.assertEqual(r.phase,3)
    def test_legacy_and_canonical_order_conflict_rejected(self):
        with self.assertRaises(ValueError):MerchantSettings(sell_all_inventory=True,sell_inventory_order=False)

if __name__=='__main__':unittest.main()
