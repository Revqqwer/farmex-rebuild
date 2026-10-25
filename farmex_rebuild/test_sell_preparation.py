import unittest
from dataclasses import replace
from merchant_sell_preparation import (SELL_LIST_PATH,SellPreparationState as State,SellPreparationRow as Row,
    SellPreparationObservation as Obs,replay_sell_preparation as replay)
from merchant_sell_selection import SellPreparedRow as Record,plan_sell_selection,SellSelectionObservation
from merchant_sell_setup import SellSetupObservation as Setup,plan_sell_setup
from operation_engine import MerchantRunner,MerchantSettings,MerchantKind,MerchantSnapshot

class SellPreparationTests(unittest.TestCase):
    def observation(self):
        row=Row(item_text='4294967297',quantity_text='2',price_text='4.294.967.297',price_ansi=b'4.294.967.297',
            item_cleanup_returned=True,quantity_cleanup_returned=True,ansi_returned=True,
            price_ansi_cleanup_returned=True,price_unicode_cleanup_returned=True)
        return Obs(clear_returned=True,counts=(1,1),rows={0:row},sizes={0:0},capacities={0:12},append_returns={0:True},local_decimal=True)
    def test_sell_path_and_raw_widths(self):
        p=replay(State(),self.observation())
        self.assertTrue(p.complete);self.assertEqual(p.state.records,(Record(1,2,0x100000001),))
        self.assertIn(('TListItems.GetCount',SELL_LIST_PATH),p.calls)
    def test_empty_list_clears_previous_vector(self):
        p=replay(State((Record(9,1,2),)),Obs(clear_returned=True,counts=(0,)))
        self.assertTrue(p.complete);self.assertEqual(p.state.records,())
    def test_clear_gap_does_not_synthesize_empty_list(self):
        original=State((Record(9,1,2),));p=replay(original,Obs(counts=(0,)))
        self.assertFalse(p.complete);self.assertEqual(p.state,original)
    def test_missing_final_fresh_count_is_not_implicit_completion(self):
        p=replay(State(),replace(self.observation(),counts=(1,)))
        self.assertFalse(p.complete);self.assertEqual(len(p.prospective_state.records),1)
    def test_append_gap_preserves_accepted_state_and_partial_fields(self):
        old=State((Record(9,1,2),));p=replay(old,replace(self.observation(),append_returns={}))
        self.assertEqual(p.state,old);self.assertEqual(p.prospective_state.records,())
        self.assertIn(('quantity',2),p.partial_fields)
    def test_grow_branch_and_signed_count(self):
        p=replay(State(),replace(self.observation(),capacities={0:0}))
        self.assertIn(('0041ddfc:grow_append',0),p.calls)
        p=replay(State(),Obs(clear_returned=True,counts=(0xffffffff,)))
        self.assertTrue(p.complete);self.assertEqual(p.state.records,())
    def test_records_feed_sell_selection_without_reparsing_text(self):
        p=replay(State(),self.observation())
        s=plan_sell_selection(True,SellSelectionObservation(rows=p.state.records,stable_rows=True,
            item_results=(1,),used_bytes=(0,),quantity_results=(3,)))
        self.assertTrue(s.complete);self.assertEqual((s.item_dword,s.quantity_dword,s.price_dword),(1,2,1))

class SellSetupTests(unittest.TestCase):
    def observation(self,**changes):
        return replace(Setup(preparation_returned=True,cost_qword=200,matched_count_dword=1,coins_dword=1000),**changes)
    def test_byref_count_is_not_assumed_zero_from_decompiler(self):
        self.assertEqual(plan_sell_setup(self.observation()).result_dword,0)
        self.assertEqual(plan_sell_setup(self.observation(matched_count_dword=0)).result_dword,1)
    def test_coins_are_still_read_before_zero_count_result(self):
        p=plan_sell_setup(self.observation(matched_count_dword=0,coins_dword=None))
        self.assertFalse(p.complete);self.assertEqual(p.calls[-1],('0046258c',))
    def test_exact_limit_requires_notification_span_normal_return(self):
        o=self.observation(cost_qword=0x7d2b74ff,coins_dword=0)
        self.assertFalse(plan_sell_setup(o).complete)
        self.assertEqual(plan_sell_setup(replace(o,over_limit_span_returned=True)).result_dword,2)
        self.assertEqual(plan_sell_setup(replace(o,cost_qword=0x7d2b74fe)).result_dword,0)
    def test_qword_add_wrap_and_signed_high_word(self):
        p=plan_sell_setup(self.observation(cost_qword=0xffffffffffffffff,coins_dword=1))
        self.assertEqual(p.total_qword,0);self.assertEqual(p.result_dword,0)
        p=plan_sell_setup(self.observation(cost_qword=1<<63,coins_dword=0))
        self.assertLess(p.signed_total,0);self.assertEqual(p.result_dword,0)
    def test_bound_preparation_gap_blocks_cost_and_coin(self):
        p=plan_sell_setup(Setup(preparation_inputs=Obs()))
        self.assertFalse(p.complete);self.assertEqual(p.calls,(('0041da48',),))
    def test_empty_preparation_does_not_fabricate_cost_observation(self):
        p=plan_sell_setup(Setup(preparation_inputs=Obs(clear_returned=True,counts=(0,))))
        self.assertTrue(p.preparation_plan.complete);self.assertFalse(p.complete)
    def test_runner_uses_bound_result_and_rejects_legacy_conflict(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=2
        snapshot=MerchantSnapshot(61000,sell_setup_inputs=self.observation())
        self.assertEqual(r.tick(snapshot).status,'setup_gate_armed')
        self.assertEqual(r.tick(replace(snapshot,now_ms=61001)).status,'prepare_attempt')
        r.phase=2
        with self.assertRaises(ValueError):r.tick(replace(snapshot,now_ms=61002,setup_result=0))
    def test_typed_observations(self):
        with self.assertRaises(ValueError):Setup(cost_qword=True)
        with self.assertRaises(ValueError):Setup(preparation_inputs=Obs(),preparation_returned=True)

if __name__=='__main__':unittest.main()
