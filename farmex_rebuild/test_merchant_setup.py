import unittest
from merchant_setup import (BuyPreparedRow as Row, BuySetupObservation as Obs,
 MerchantInventoryObservation as Inventory,plan_buy_setup,plan_merchant_inventory)
from upgrade_packets import UpgradeItemObservation
from operation_engine import MerchantKind,MerchantSettings,MerchantSnapshot,MerchantRunner


class MerchantSetupTests(unittest.TestCase):
    def setup(self,**changes):
        fields=dict(preparation_returned=True,free_count=2,coins_dword=100,
                    rows=(Row(1,2,30),Row(2,1,50),Row(3,1,40)),stable_rows=True)
        fields.update(changes);return Obs(**fields)

    def test_inventory_all28_and_first_gap(self):
        r=plan_merchant_inventory(Inventory((0,1)*14))
        self.assertTrue(r.complete);self.assertEqual(r.free_count,14)
        self.assertEqual(r.zero_slots,tuple(range(14,42,2)))
        self.assertEqual(r.calls[-1],('004634a4',41))
        gap=plan_merchant_inventory(Inventory((0,1,None,0)))
        self.assertFalse(gap.complete);self.assertIsNone(gap.free_count)
        self.assertEqual(gap.zero_slots,(14,));self.assertIn('slot16',gap.missing)

    def test_bound_item_reads_and_no_missing_to_empty(self):
        item=UpgradeItemObservation(global_root_slot=0x1000,inventory_offset=4,records_offset=8,
                                    root=0x2000,inventory=0x3000,record=0)
        r=plan_merchant_inventory(Inventory((None,)+(1,)*27,(item,)))
        self.assertEqual(r.free_count,1);self.assertEqual(len(r.item_plans[0][1].reads),3)
        with self.assertRaises(ValueError):plan_merchant_inventory(Inventory((0,),(item,)))

    def test_coin_observation_precedes_threshold_return(self):
        r=plan_buy_setup(2,self.setup(coins_dword=None))
        self.assertFalse(r.complete);self.assertEqual(r.calls[-1],('0046258c',))
        r=plan_buy_setup(2,self.setup(rows=(None,),stable_rows=None))
        self.assertEqual(r.result_dword,1);self.assertEqual(r.row_costs,())

    def test_ordered_skip_then_afford_and_stop_at_free_capacity(self):
        r=plan_buy_setup(0,self.setup())
        self.assertEqual((r.result_dword,r.remaining_coins,r.remaining_free),(0,0,0))
        self.assertEqual(r.affordable_indices,(0,2));self.assertEqual(r.row_costs,((0,60),(1,50),(2,40)))
        r=plan_buy_setup(0,self.setup(free_count=1,rows=(Row(0,0,999),None)))
        self.assertTrue(r.complete);self.assertEqual(r.affordable_indices,(0,))

    def test_low_dword_product_and_signed_threshold(self):
        r=plan_buy_setup(0xffffffff,self.setup(free_count=1,coins_dword=0,
                         rows=(Row(0,0x10000,0x10000),)))
        self.assertEqual(r.result_dword,0);self.assertEqual(r.row_costs,((0,0),))
        r=plan_buy_setup(0,self.setup(rows=(Row(1,0xffffffff,2),),coins_dword=0xfffffffd))
        self.assertEqual(r.result_dword,2);self.assertEqual(r.row_costs,((0,0xfffffffe),))
        r=plan_buy_setup(0x80000000,self.setup(free_count=0,rows=()))
        self.assertEqual(r.result_dword,2)

    def test_vector_count_is_fresh_even_after_last_free_slot(self):
        r=plan_buy_setup(0,self.setup(free_count=1,stable_rows=None,vector_counts=(3,)))
        self.assertFalse(r.complete);self.assertEqual(r.affordable_indices,(0,))
        self.assertEqual((r.remaining_coins,r.remaining_free),(40,0))
        self.assertIn('iteration1',r.missing)
        r=plan_buy_setup(0,self.setup(free_count=1,stable_rows=None,vector_counts=(3,3)))
        self.assertTrue(r.complete);self.assertEqual(r.affordable_indices,(0,))

    def test_preparation_gap_and_missing_vector_are_unknown(self):
        r=plan_buy_setup(0,self.setup(preparation_returned=False))
        self.assertEqual(r.calls,(('0041dec8',),));self.assertFalse(r.complete)
        r=plan_buy_setup(0,self.setup(stable_rows=None))
        self.assertFalse(r.complete);self.assertEqual(r.row_costs,())
        r=plan_buy_setup(0,self.setup(rows=(None,)))
        self.assertFalse(r.complete);self.assertIn('row0',r.missing)

    def test_inventory_binding_and_ambiguous_inputs(self):
        r=plan_buy_setup(0,self.setup(free_count=None,inventory_inputs=Inventory((0,)*28)))
        self.assertTrue(r.complete);self.assertEqual(r.inventory_plan.free_count,28)
        with self.assertRaises(ValueError):plan_buy_setup(0,self.setup(inventory_inputs=Inventory((0,)*28)))
        with self.assertRaises(ValueError):self.setup(vector_counts=(3,))
        with self.assertRaises(ValueError):Row(1,True,1)

    def runner(self):
        runner=MerchantRunner(MerchantSettings(kind=MerchantKind.BUY));runner.start()
        runner.tick(MerchantSnapshot(0,currently_open=False))
        runner.tick(MerchantSnapshot(1,close_pending=False));return runner

    def test_bound_runner_waits_then_arms_then_advances(self):
        runner=self.runner()
        r=runner.tick(MerchantSnapshot(61000,buy_setup_inputs=self.setup(preparation_returned=None)))
        self.assertEqual(r.status,'needs_adapter');self.assertEqual(runner.phase,2)
        self.assertFalse(runner.setup_seen)
        r=runner.tick(MerchantSnapshot(61001,buy_setup_inputs=self.setup()))
        self.assertEqual(r.status,'setup_gate_armed')
        r=runner.tick(MerchantSnapshot(61002,buy_setup_inputs=self.setup()))
        self.assertEqual(r.status,'phase_changed');self.assertEqual(runner.phase,3)
        with self.assertRaises(ValueError):
            self.runner().tick(MerchantSnapshot(61000,setup_result=0,buy_setup_inputs=self.setup()))

    def test_bound_monitoring_and_zero_affordability_stop(self):
        runner=self.runner()
        r=runner.tick(MerchantSnapshot(61000,buy_setup_inputs=self.setup(coins_dword=0)))
        self.assertEqual(r.status,'stopped');self.assertFalse(runner.active)
        runner=self.runner();runner.phase=5
        r=runner.tick(MerchantSnapshot(61000,buy_inventory_inputs=Inventory((1,)*28)))
        self.assertEqual(r.reason,'buy_free_threshold');self.assertEqual(runner.phase,0)
        runner=self.runner();runner.phase=5
        r=runner.tick(MerchantSnapshot(61000,buy_inventory_inputs=Inventory((1,))))
        self.assertEqual(r.status,'needs_adapter');self.assertEqual(runner.phase,5)
        runner=MerchantRunner(MerchantSettings(kind=MerchantKind.BUY,buy_free_threshold=0xffffffff))
        runner.start();runner.phase=5
        r=runner.tick(MerchantSnapshot(61000,buy_inventory_inputs=Inventory((1,)*28)))
        self.assertEqual(r.status,'monitoring');self.assertEqual(runner.phase,5)


if __name__=='__main__':unittest.main()
