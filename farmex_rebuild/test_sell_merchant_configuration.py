import json,unittest
from pathlib import Path
from profiles import Profiles
from merchant_configuration import *

class SellMerchantConfigurationTests(unittest.TestCase):
    def setUp(self):
        catalog=json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf-8'))
        self.values=dict(Profiles(catalog).defaults)
    def compile(self,**kwargs):return compile_sell_merchant_panel(self.values,**kwargs)
    def test_real_profile_defaults(self):
        c=self.compile()
        self.assertEqual(dict(c.fields),{0:0,0xc8:0,0xc9:0,0xcc:20,0xd0:30,0xd4:0,0xd8:0,0xd9:1,0xe0:0,0xe8:0})
        with self.assertRaises(TypeError):c.fields[0xc8]=1
    def test_sell_start_priority_and_buy_short_circuit(self):
        self.values[SELL_START]=True;self.values[BUY_START]=True
        self.assertEqual(self.compile().fields[0],1)
        del self.values[BUY_START];self.assertEqual(self.compile().fields[0],1)
    def test_bank_last_checked_wins(self):
        self.values[SELL_DC]=True;self.values[SELL_BANK]=True
        self.assertEqual(self.compile().fields[0xd4],2)
        self.values[SELL_BANK]=False;self.assertEqual(self.compile().fields[0xd4],1)
    def test_missing_radio_needs_explicit_previous_policy(self):
        self.values[SELL_STOP]=False;c=self.compile()
        self.assertNotIn(0xd4,c.fields)
        with self.assertRaises(ValueError):sell_merchant_settings_from_panel(c)
        self.assertEqual(self.compile(initial_policy_dword=2).fields[0xd4],2)
    def test_inventory_flag_is_canonical_order_not_sell_all(self):
        self.values[SELL_ORDER]=True
        s=sell_merchant_settings_from_panel(self.compile())
        self.assertTrue(s.sell_inventory_order);self.assertFalse(s.sell_all_inventory)
    def test_core_fields_feed_existing_runner_settings(self):
        self.values[SELL_REOPEN]=True;self.values[SELL_MINUTES]='2';self.values[SELL_EXTRA]='5';self.values[SELL_DC]=True
        s=sell_merchant_settings_from_panel(self.compile())
        self.assertEqual((s.reopen,s.reopen_minutes,s.extra_wait_seconds,s.failure_policy),(True,2,5,'disconnect'))
    def test_coin_keeps_full_qword_and_price_dot_rule(self):
        self.values[SELL_COIN]='4.294.967.297'
        self.assertEqual(self.compile().fields[0xe8],0x100000001)
    def test_coin_predicate_failure_is_distinct_from_parser_gap(self):
        self.values[SELL_COIN]='abc';self.assertEqual(self.compile().fields[0xe8],0)
        self.values[SELL_COIN]='1.2';c=self.compile()
        self.assertNotIn(0xe8,c.fields);self.assertTrue(any(SELL_COIN in m for m in c.missing))
    def test_observed_coin_does_not_require_local_codec(self):
        self.values[SELL_COIN]='native text outside ASCII'
        self.assertEqual(self.compile(coin_qword=(1<<64)-1).fields[0xe8],(1<<64)-1)
    def test_combo_index_does_not_resolve_unicode_text(self):
        self.values[SELL_ROUTE]=7
        self.assertIsNone(self.compile().route_text)
        self.assertEqual(self.compile(route_text='Explicit route').route_text,'Explicit route')
    def test_unsupported_timer_preserved_and_not_clamped(self):
        self.values[SELL_EXTRA]='-1';c=self.compile()
        self.assertEqual(c.fields[0xd0],0xffffffff)
        with self.assertRaises(ValueError):sell_merchant_settings_from_panel(c)
    def test_input_integrity_and_observed_numeric_low_dword(self):
        original=dict(self.values);self.compile();self.assertEqual(original,self.values)
        self.assertEqual(self.compile(numeric_results={SELL_MINUTES:0x100000002}).fields[0xcc],2)
        with self.assertRaises(ValueError):self.compile(coin_qword=True)

if __name__=='__main__':unittest.main()
