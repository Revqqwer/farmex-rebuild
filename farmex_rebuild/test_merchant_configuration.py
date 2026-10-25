import json,unittest
from pathlib import Path
from profiles import Profiles
from merchant_configuration import *

class BuyMerchantConfigurationTests(unittest.TestCase):
    def setUp(self):
        catalog=json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf-8'))
        self.values=dict(Profiles(catalog).defaults)
    def compile(self,**options):return compile_buy_merchant_panel(self.values,**options)
    def test_real_defaults_and_immutable_raw_fields(self):
        c=self.compile()
        self.assertEqual(dict(c.fields),{0:0,0x110:0,0x114:20,0x118:30,0x11c:0,0x120:0,0x124:0,0x125:1})
        with self.assertRaises(TypeError):c.fields[0]=2
        self.assertIn(ROUTE+': GetText',c.missing)
    def test_sell_start_short_circuits_buy_read(self):
        self.values[SELL_START]=True;del self.values[BUY_START]
        self.assertEqual(self.compile().fields[0],1)
    def test_buy_start_and_neither(self):
        self.values[BUY_START]=True;self.assertEqual(self.compile().fields[0],2)
        self.values[BUY_START]=False;self.assertEqual(self.compile().fields[0],0)
    def test_policy_last_checked_bank_wins_then_dc(self):
        for p in (STOP,DC,BANK):self.values[p]=True
        self.assertEqual(self.compile().fields[0x11c],2)
        self.values[BANK]=False;self.assertEqual(self.compile().fields[0x11c],1)
    def test_no_radio_needs_previous_policy_not_default_stop(self):
        self.values[STOP]=False
        c=self.compile();self.assertNotIn(0x11c,c.fields)
        with self.assertRaises(ValueError):buy_merchant_settings_from_panel(c)
        self.assertEqual(self.compile(initial_policy_dword=2).fields[0x11c],2)
    def test_low_dword_of_signed64_text(self):
        self.values[MINUTES]='4294967298';self.values[EXTRA]='-1'
        c=self.compile();self.assertEqual(c.fields[0x114],2);self.assertEqual(c.fields[0x118],0xffffffff)
    def test_native_numeric_result_requires_explicit_qword(self):
        self.values[MINUTES]='opaque native text'
        with self.assertRaises(ValueError):self.compile()
        self.assertEqual(self.compile(numeric_results={MINUTES:(1<<64)-1}).fields[0x114],0xffffffff)
    def test_route_text_is_not_derived_from_itemindex(self):
        self.values[ROUTE]=123
        self.assertIsNone(self.compile().route_text)
        self.assertEqual(self.compile(route_text='Explicit route').route_text,'Explicit route')
    def test_bridge_consumes_scalar_settings_but_does_not_auto_start(self):
        self.values[REOPEN]=True;self.values[DC]=True;self.values[THRESHOLD]='3'
        settings=buy_merchant_settings_from_panel(self.compile())
        self.assertTrue(settings.reopen);self.assertEqual(settings.reopen_minutes,20)
        self.assertEqual(settings.extra_wait_seconds,30);self.assertEqual(settings.buy_free_threshold,3)
        self.assertEqual(settings.failure_policy,'disconnect')
    def test_unsupported_monotonic_timer_is_not_clamped(self):
        self.values[EXTRA]='-1';c=self.compile()
        with self.assertRaises(ValueError):buy_merchant_settings_from_panel(c)
        self.assertEqual(c.fields[0x118],0xffffffff)
    def test_no_input_mutation_and_strict_bool(self):
        original=dict(self.values);self.compile();self.assertEqual(self.values,original)
        self.values[ALARM]=1
        with self.assertRaises(ValueError):self.compile()

if __name__=='__main__':unittest.main()
