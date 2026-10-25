import unittest
from source_coin import GuardedDwordSample as Sample,SourceCoinObservation as Obs,plan_source_coin,plan_guarded_dword
from merchant_sell_coin_alarm import SellCoinAlarmObservation,plan_sell_coin_alarm

class SourceCoinTests(unittest.TestCase):
    def sample(self):
        return Obs(((0x553e7c,0x1000),(0x553ff0,0x20)),
            (Sample(0x1000,1,0x2000),Sample(0x2020,1,77)))
    def test_two_guarded_calls_use_fresh_offset_after_root(self):
        p=plan_source_coin(self.sample());self.assertTrue(p.complete);self.assertEqual(p.coins_dword,77)
        self.assertEqual(p.helper_calls,(('0045dc44',0x1000),('0045dc44',0x2020)))
    def test_null_helper_returns_zero_without_api(self):
        p=plan_guarded_dword(0);self.assertTrue(p.complete);self.assertEqual((p.value_dword,p.steps),(0,()))
        p=plan_source_coin(Obs(((0x553e7c,0),(0x553ff0,0))))
        self.assertTrue(p.complete);self.assertEqual(p.coins_dword,0);self.assertEqual(len(p.guarded_plans),2)
    def test_null_root_does_not_skip_second_offset_getter(self):
        p=plan_source_coin(Obs(((0x553e7c,0),(0x553ff0,0x20)),(Sample(0x20,1,9),)))
        self.assertTrue(p.complete);self.assertEqual(p.coins_dword,9)
    def test_failed_root_protection_still_reaches_second_getter(self):
        p=plan_source_coin(Obs(((0x553e7c,0x1000),(0x553ff0,0x20)),(Sample(0x1000,0),Sample(0x20,1,5))))
        self.assertTrue(p.complete);self.assertEqual(p.coins_dword,5)
        self.assertEqual(p.guarded_plans[0].status,'protection_failure_returns_zero')
    def test_failed_final_protection_and_real_zero_keep_distinct_provenance(self):
        failed=plan_guarded_dword(7,Sample(7,0));zero=plan_guarded_dword(7,Sample(7,1,0))
        self.assertEqual(failed.value_dword,zero.value_dword)
        self.assertNotEqual(failed.status,zero.status)
    def test_missing_protection_and_value_do_not_become_zero(self):
        self.assertFalse(plan_guarded_dword(7).complete)
        p=plan_guarded_dword(7,Sample(7,2));self.assertFalse(p.complete)
        self.assertEqual(p.steps[-1],('read_plan',7,4))
        self.assertFalse(plan_source_coin(Obs()).complete)
    def test_wrap_can_make_final_helper_null(self):
        p=plan_source_coin(Obs(((0x553e7c,1),(0x553ff0,0x10)),(Sample(1,1,0xfffffff0),)))
        self.assertTrue(p.complete);self.assertEqual(p.coins_dword,0)
        self.assertEqual(p.helper_calls[-1],('0045dc44',0))
    def test_alarm_binding_does_not_bypass_reader_gap(self):
        p=plan_sell_coin_alarm(SellCoinAlarmObservation(1,None,77,coin_inputs=Obs()))
        self.assertFalse(p.complete);self.assertIsNotNone(p.coin_plan);self.assertIsNone(p.mismatch)
        p=plan_sell_coin_alarm(SellCoinAlarmObservation(1,None,77,coin_inputs=self.sample()))
        self.assertTrue(p.complete);self.assertEqual(p.status,'unchanged');self.assertEqual(p.coin_plan.coins_dword,77)
        p=plan_sell_coin_alarm(SellCoinAlarmObservation(0,coin_inputs=Obs()))
        self.assertTrue(p.complete);self.assertIsNone(p.coin_plan)
    def test_types_addresses_and_raw_result_conflict(self):
        with self.assertRaises(ValueError):Sample(1,True)
        with self.assertRaises(ValueError):plan_guarded_dword(1,Sample(2,1,1))
        with self.assertRaises(ValueError):plan_source_coin(Obs(((1,0),)))
        with self.assertRaises(ValueError):SellCoinAlarmObservation(1,7,77,coin_inputs=self.sample())

if __name__=='__main__':unittest.main()
