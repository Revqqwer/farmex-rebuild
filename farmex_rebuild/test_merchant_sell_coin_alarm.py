import unittest
from merchant_sell_coin_alarm import SellCoinAlarmObservation as Obs,plan_sell_coin_alarm as plan
from merchant_configuration import compile_sell_merchant_panel,sell_coin_alarm_from_panel,SELL_COIN_ALARM,SELL_COIN
from operation_engine import MerchantRunner,MerchantKind,MerchantSettings,MerchantSnapshot
from profiles import Profiles
from pathlib import Path
import json

class SellCoinAlarmTests(unittest.TestCase):
    def test_disabled_skips_helper_and_reference(self):
        p=plan(Obs(0));self.assertTrue(p.complete);self.assertEqual(p.status,'disabled')
        self.assertEqual(p.steps,(('read','+e0'),))
    def test_coin_eax_and_reference_are_not_guessed(self):
        for o in (Obs(),Obs(1),Obs(1,100)):
            self.assertFalse(plan(o).complete)
    def test_equal_zero_extended_dword_does_not_need_alarm_return(self):
        p=plan(Obs(255,0xffffffff,0xffffffff))
        self.assertTrue(p.complete);self.assertFalse(p.mismatch);self.assertEqual(p.status,'unchanged')
    def test_reference_high_nonzero_skips_low_compare(self):
        p=plan(Obs(1,7,(1<<32)|7,True));self.assertTrue(p.mismatch)
        self.assertNotIn(('read','+e8','lowDWORD'),p.steps)
    def test_both_increase_and_decrease_require_normal_return(self):
        for coin in (99,101):
            p=plan(Obs(1,coin,100));self.assertFalse(p.complete);self.assertTrue(p.mismatch)
            p=plan(Obs(1,coin,100,True));self.assertTrue(p.complete)
            self.assertEqual(p.status,'alarm_span_returned');self.assertFalse(p.independently_verified)
    def test_runner_header_holds_every_phase_without_modifying_reference(self):
        for phase in range(7):
            r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=phase
            for now in (100000,100001):
                p=r.tick(MerchantSnapshot(now,sell_coin_alarm_inputs=Obs(1,101,100)))
                self.assertEqual(p.status,'needs_adapter');self.assertEqual(r.phase,phase)
            r.tick(MerchantSnapshot(100002,sell_coin_alarm_inputs=Obs(1,101,100,True)))
            self.assertEqual(r.last_sell_coin_alarm_plan.status,'alarm_span_returned')
            r.tick(MerchantSnapshot(100003,sell_coin_alarm_inputs=Obs(1,101,100)))
            self.assertFalse(r.last_sell_coin_alarm_plan.complete)
    def test_panel_projection_preserves_qword_and_uses_no_default_coin(self):
        p=Profiles(json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf-8')))
        values=dict(p.defaults);values[SELL_COIN_ALARM]=True;values[SELL_COIN]='4.294.967.303'
        compiled=compile_sell_merchant_panel(values)
        o=sell_coin_alarm_from_panel(compiled)
        self.assertEqual(o.reference_qword,(1<<32)|7);self.assertIsNone(o.coins_dword)
        self.assertFalse(plan(o).complete)
    def test_types_and_reset(self):
        with self.assertRaises(ValueError):Obs(True)
        with self.assertRaises(ValueError):Obs(1,1<<32,0)
        with self.assertRaises(ValueError):Obs(1,0,0,1)
        with self.assertRaises(ValueError):MerchantSnapshot(1,sell_coin_alarm_inputs=0)
        r=MerchantRunner(MerchantSettings());r.start();r.tick(MerchantSnapshot(1,sell_coin_alarm_inputs=Obs(1)))
        r.start();self.assertIsNone(r.last_sell_coin_alarm_plan)

if __name__=='__main__':unittest.main()
