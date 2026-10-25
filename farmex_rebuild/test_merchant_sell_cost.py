import unittest
from merchant_sell_selection import SellPreparedRow as Row
from merchant_sell_cost import SellCostObservation as Obs,plan_sell_cost as plan
from merchant_sell_setup import SellSetupObservation,plan_sell_setup

class SellCostTests(unittest.TestCase):
    def test_empty_list_order_needs_no_inventory(self):
        p=plan((),Obs(0,True));self.assertTrue(p.complete);self.assertEqual(p.cost_qword,0)
        self.assertEqual(len(p.writes),28)
    def test_all_zero_inventory_skips_unknown_vector_contract(self):
        p=plan((),Obs(255,None,(0,)*28))
        self.assertTrue(p.complete);self.assertEqual(p.matched_count_dword,0)
        self.assertNotIn(('vector_count',),p.calls)
    def test_inventory_order_first_duplicate_row_applies_per_slot(self):
        p=plan((Row(77,1,2),Row(77,1,99)),Obs(1,True,(77,77)+(0,)*26,(10,10)))
        self.assertEqual(p.cost_qword,4);self.assertEqual(p.matched_count_dword,2)
        self.assertEqual([m[:2] for m in p.matches],[(0,14),(0,15)])
    def test_list_order_duplicate_rows_do_not_reuse_slot(self):
        p=plan((Row(77,1,2),Row(77,1,3)),Obs(0,True,(77,77,77),(10,10)))
        self.assertEqual(p.cost_qword,5);self.assertEqual([m[:2] for m in p.matches],[(0,14),(1,15)])
    def test_item_values_are_per_fresh_call_not_per_slot(self):
        p=plan((Row(77,1,2),Row(88,1,3)),Obs(0,True,(77,99,88),(1,1)))
        self.assertTrue(p.complete);self.assertEqual(p.cost_qword,5)
        self.assertIn(('004634a4',14,1),p.calls)
    def test_quantity_second_read_is_fresh_and_not_clamped_again(self):
        p=plan((Row(77,10,2),),Obs(1,True,(77,)+(0,)*27,(5,100)))
        self.assertEqual(p.matches[0][2:],(100,200))
    def test_signed_quantity_and_low_product_zero_extension(self):
        p=plan((Row(77,10,2),),Obs(1,True,(77,)+(0,)*27,(0x80000000,0xffffffff)))
        self.assertEqual(p.cost_qword,0xfffffffe)
    def test_each_product_is_low32_before_qword_accumulation(self):
        p=plan((Row(77,2,0xffffffff),),Obs(1,True,(77,)+(0,)*27,(2,)))
        self.assertEqual(p.cost_qword,0xfffffffe)
        p=plan((Row(77,1,0xffffffff),Row(88,1,0xffffffff)),Obs(1,True,(77,88)+(0,)*26,(1,1)))
        self.assertEqual(p.cost_qword,0x1fffffffe)
    def test_price_high_dword_not_used(self):
        p=plan((Row(77,2,0x100000003),),Obs(1,True,(77,)+(0,)*27,(2,)))
        self.assertEqual(p.cost_qword,6)
    def test_partial_prefix_does_not_fabricate_return_values(self):
        p=plan((Row(77,1,2),),Obs(1,True,(77,),(1,)))
        self.assertFalse(p.complete);self.assertIsNone(p.cost_qword)
        self.assertEqual(p.prospective_cost_qword,2);self.assertEqual(p.prospective_used_bytes[0],1)
        self.assertEqual(p.writes[:28],tuple((0x59+s,0) for s in range(14,42)))
    def test_nonzero_item_needs_vector_observation(self):
        p=plan((),Obs(1,None,(77,)))
        self.assertFalse(p.complete);self.assertIn('stable prepared',p.missing)
    def test_zero_id_is_skipped_only_in_inventory_order(self):
        p=plan((Row(0,1,2),),Obs(0,True,(0,),(1,)))
        self.assertEqual(p.cost_qword,2)
        p=plan((Row(0,1,2),),Obs(1,True,(0,)*28,()))
        self.assertEqual(p.cost_qword,0)
    def test_counter_wrap_and_caller_zero_contract(self):
        p=plan((Row(77,1,2),),Obs(1,True,(77,)+(0,)*27,(1,),0xffffffff))
        self.assertEqual(p.matched_count_dword,0)
        with self.assertRaises(ValueError):SellSetupObservation(cost_inputs=Obs(initial_count_dword=1))
    def test_bound_setup_derives_count_and_cost_but_still_needs_coins(self):
        o=Obs(1,True,(77,)+(0,)*27,(2,))
        p=plan_sell_setup(SellSetupObservation(preparation_returned=True,cost_rows=(Row(77,2,3),),cost_inputs=o))
        self.assertFalse(p.complete);self.assertTrue(p.cost_plan.complete);self.assertEqual(p.cost_plan.cost_qword,6)
        p=plan_sell_setup(SellSetupObservation(preparation_returned=True,cost_rows=(Row(77,2,3),),cost_inputs=o,coins_dword=1000))
        self.assertEqual(p.result_dword,0);self.assertEqual(p.total_qword,1006)
    def test_conflicting_raw_cost_and_bound_replay_rejected(self):
        with self.assertRaises(ValueError):SellSetupObservation(cost_inputs=Obs(),cost_qword=0)
        with self.assertRaises(ValueError):Obs(item_results=(True,))

if __name__=='__main__':unittest.main()
