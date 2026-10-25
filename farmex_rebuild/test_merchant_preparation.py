import unittest
from dataclasses import replace
from merchant_preparation import (BuyPreparedRecord as Record,BuyPreparationState as State,
 BuyPreparationRow as Row,BuyPreparationObservation as Obs,replay_buy_preparation,plan_merchant_price)
from merchant_setup import BuySetupObservation,plan_buy_setup

class BuyPreparationTests(unittest.TestCase):
    def row(self,**changes):
        fields=dict(item_text='4294967297',quantity_text='2',price_text='1.000',price_ansi=b'1.000',
         item_cleanup_returned=True,quantity_cleanup_returned=True,ansi_returned=True,
         price_ansi_cleanup_returned=True,price_unicode_cleanup_returned=True)
        fields.update(changes);return Row(**fields)
    def obs(self,**changes):
        fields=dict(clear_returned=True,counts=(1,1),rows={0:self.row()},sizes={0:0},capacities={0:12},
                    append_returns={0:True},local_decimal=True)
        fields.update(changes);return Obs(**fields)
    def test_price_length_boundary_and_bad_character_zero(self):
        self.assertEqual(plan_merchant_price(b'1.23',local_decimal=True).qword,123)
        r=plan_merchant_price(b'1.2',local_decimal=True)
        self.assertFalse(r.complete);self.assertEqual(r.parser_bytes,b'1.2')
        for text in (b'-1',b' 1',b'1,000',b'1\x00',b'\xff'):
            r=plan_merchant_price(text);self.assertTrue(r.complete);self.assertEqual(r.qword,0)
    def test_price_empty_dots_overflow_remain_conversion_gap(self):
        for text in (b'',b'...',b'....',b'9223372036854775808'):
            self.assertFalse(plan_merchant_price(text,local_decimal=True).complete)
        self.assertEqual(plan_merchant_price(b'4.294.967.297',local_decimal=True).qword,0x100000001)
    def test_captured_conversion_and_explicit_parser_conflict(self):
        self.assertEqual(plan_merchant_price(b'1.2',parser_qword=123).qword,123)
        with self.assertRaises(ValueError):plan_merchant_price(b'12',parser_qword=12,local_decimal=True)
        r=replay_buy_preparation(State(),self.obs(local_decimal=False,rows={0:self.row(item_qword=5,
             quantity_qword=0xfffffffffffffffe,price_qword=0x100000001)}))
        self.assertEqual(r.state.records,(Record(5,0xfffffffe,0x100000001),))
    def test_low_dwords_and_full_price_are_retained(self):
        r=replay_buy_preparation(State(),self.obs(rows={0:self.row(price_text='4294967297',price_ansi=b'4294967297')}))
        self.assertTrue(r.complete);self.assertEqual(r.state.records,(Record(1,2,0x100000001),))
        self.assertIn(('0041dd9c:inplace_append',0),r.calls)
    def test_clear_and_signed_count_empty_without_parsing_rows(self):
        initial=State((Record(9,9,9),))
        r=replay_buy_preparation(initial,self.obs(clear_returned=None))
        self.assertEqual(r.state,initial);self.assertEqual(r.prospective_state,initial)
        r=replay_buy_preparation(initial,self.obs(counts=(0xffffffff,),rows={0:self.row(item_text='invalid')}))
        self.assertTrue(r.complete);self.assertEqual(r.state.records,())
    def test_missing_item_stops_before_parser_or_quantity(self):
        r=replay_buy_preparation(State(),self.obs(rows={0:self.row(item_text=None)}))
        self.assertFalse(r.complete);self.assertEqual(r.calls[-1],('0045f7f4:caption',0))
        r=replay_buy_preparation(State(),self.obs(rows={0:self.row(item_cleanup_returned=None)}))
        self.assertEqual(r.partial_fields,(('item',1),));self.assertNotIn(('0045f6e0:subitem',0,1),r.calls)
    def test_price_cleanup_precedes_append_and_gap_preserves_accepted_state(self):
        initial=State((Record(9,9,9),))
        r=replay_buy_preparation(initial,self.obs(rows={0:self.row(price_unicode_cleanup_returned=False)}))
        self.assertFalse(r.complete);self.assertEqual(r.state,initial)
        self.assertEqual(r.prospective_state.records,());self.assertEqual(r.partial_fields[-1],('price',1000))
        self.assertNotIn(('0041dd4c:size',),r.calls)
    def test_grow_append_then_missing_next_count_keeps_prefix_prospective(self):
        r=replay_buy_preparation(State(),self.obs(counts=(1,),capacities={0:0}))
        self.assertFalse(r.complete);self.assertEqual(r.state.records,())
        self.assertEqual(r.prospective_state.records,(Record(1,2,1000),))
        self.assertIn(('0041ddfc:grow_append',0),r.calls)
        r=replay_buy_preparation(State(),self.obs(append_returns={0:None}))
        self.assertFalse(r.complete);self.assertEqual(r.prospective_state.records,())
    def test_preparation_binding_reaches_budget_only_after_full_return(self):
        base=BuySetupObservation(preparation_inputs=self.obs(),free_count=2,coins_dword=2000,stable_rows=True)
        p=plan_buy_setup(0,base);self.assertEqual(p.result_dword,0)
        self.assertEqual(p.preparation_plan.state.records,(Record(1,2,1000),))
        p=plan_buy_setup(0,replace(base,preparation_inputs=self.obs(counts=(1,))))
        self.assertFalse(p.complete);self.assertEqual(p.calls,(('0041dec8',),))
        with self.assertRaises(ValueError):plan_buy_setup(0,replace(base,preparation_returned=True))
    def test_raw_qword_price_budget_uses_low_dword_only(self):
        obs=self.obs(rows={0:self.row(price_text='4294967297',price_ansi=b'4294967297')})
        p=plan_buy_setup(0,BuySetupObservation(preparation_inputs=obs,free_count=1,coins_dword=2,stable_rows=True))
        self.assertEqual(p.result_dword,0);self.assertEqual(p.row_costs,((0,2),))
        self.assertEqual(p.preparation_plan.state.records[0].price_qword,0x100000001)

if __name__=='__main__':unittest.main()
