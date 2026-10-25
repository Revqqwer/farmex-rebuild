import unittest
from source_coin import SourceCoinObservation as Coin,GuardedDwordSample
from merchant_setup import BuySetupObservation as Buy,BuyPreparedRow,plan_buy_setup
from merchant_sell_setup import SellSetupObservation as Sell,plan_sell_setup
from merchant_sell_coin_alarm import SellCoinAlarmObservation,plan_sell_coin_alarm

def reader(value):
    return Coin(((0x553e7c,1),(0x553ff0,0x10)),(GuardedDwordSample(1,1,0x100),GuardedDwordSample(0x110,1,value)))

class SetupCoinBindingTests(unittest.TestCase):
    def test_buy_budget_uses_bound_value(self):
        p=plan_buy_setup(0,Buy(preparation_returned=True,free_count=1,stable_rows=True,
            rows=(BuyPreparedRow(1,2,50),),coin_inputs=reader(100)))
        self.assertTrue(p.complete);self.assertEqual(p.result_dword,0)
        self.assertEqual(p.remaining_coins,0);self.assertEqual(p.coin_plan.coins_dword,100)
    def test_buy_coin_gap_precedes_free_threshold_failure(self):
        p=plan_buy_setup(28,Buy(preparation_returned=True,free_count=0,coin_inputs=Coin()))
        self.assertFalse(p.complete);self.assertIsNotNone(p.coin_plan)
        self.assertIn('coin reader',p.missing)
    def test_buy_preparation_and_inventory_gap_skip_coin_reader(self):
        # Invalid reached global address would raise, but this branch has not been reached.
        for o in (Buy(coin_inputs=Coin(((1,0),))),Buy(preparation_returned=True,coin_inputs=Coin(((1,0),)))):
            p=plan_buy_setup(0,o);self.assertFalse(p.complete);self.assertIsNone(p.coin_plan)
    def test_sell_total_uses_bound_coin(self):
        p=plan_sell_setup(Sell(preparation_returned=True,cost_qword=100,matched_count_dword=1,coin_inputs=reader(1000)))
        self.assertTrue(p.complete);self.assertEqual((p.total_qword,p.result_dword),(1100,0))
        self.assertEqual(p.coin_plan.coins_dword,1000)
    def test_sell_zero_count_still_requires_coin_reader(self):
        p=plan_sell_setup(Sell(preparation_returned=True,cost_qword=0,matched_count_dword=0,coin_inputs=Coin()))
        self.assertFalse(p.complete);self.assertIn('coin reader',p.missing)
    def test_sell_cost_gap_skips_coin_reader(self):
        p=plan_sell_setup(Sell(preparation_returned=True,coin_inputs=Coin(((1,0),))))
        self.assertFalse(p.complete);self.assertIsNone(p.coin_plan)
    def test_alarm_result_not_reused_for_setup(self):
        alarm=plan_sell_coin_alarm(SellCoinAlarmObservation(1,None,77,coin_inputs=reader(77)))
        self.assertTrue(alarm.complete)
        p=plan_sell_setup(Sell(preparation_returned=True,cost_qword=0,matched_count_dword=1,coin_inputs=Coin()))
        self.assertFalse(p.complete);self.assertIsNone(p.coin_plan.coins_dword)
    def test_failure_zero_uses_source_numeric_gate_but_retains_provenance(self):
        c=Coin(((0x553e7c,0),(0x553ff0,1)),(GuardedDwordSample(1,0),))
        p=plan_sell_setup(Sell(preparation_returned=True,cost_qword=0,matched_count_dword=1,coin_inputs=c))
        self.assertTrue(p.complete);self.assertEqual(p.total_qword,0)
        self.assertEqual(p.coin_plan.guarded_plans[-1].status,'protection_failure_returns_zero')
    def test_conflicting_or_untyped_input_rejected(self):
        for typ in (Buy,Sell):
            with self.assertRaises(ValueError):typ(coins_dword=0,coin_inputs=Coin())
            with self.assertRaises(ValueError):typ(coin_inputs=0)

if __name__=='__main__':unittest.main()
