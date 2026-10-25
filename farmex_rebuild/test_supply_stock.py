import unittest
from dataclasses import replace
from supply_stock import *

class SupplyStockTests(unittest.TestCase):
    def compile(self,rows=(),**kw):return compile_supply_list({BUY_LIST_PATH:list(rows)},**kw)
    def row(self,index,desired='200',**kw):return dict(caption='Ignored',checked=False,subitems=[desired,str(index)],**kw)
    def observe(self,index,item_id,matches=(),quantity=0):
        return SupplyStockObservation({(index,s):item_id if s in matches else 0 for s in range(14,42)},
            {(index,s):quantity for s in matches})
    def test_source_catalog22_ids_and_arrow_ordinal(self):
        self.assertEqual(len(SOURCE_CATALOG),22)
        self.assertEqual((SOURCE_CATALOG[0].item_id,SOURCE_CATALOG[9].name,SOURCE_CATALOG[9].item_id),
            (389011000,'Arrow',391010000))
        self.assertTrue(all(not r.enabled and not r.desired for r in SOURCE_CATALOG))
    def test_profile_index_resolves_catalog_id_caption_and_checked_ignored(self):
        p=self.compile((self.row(9),));self.assertTrue(p.complete)
        self.assertEqual((p.rows[9].enabled,p.rows[9].desired,p.rows[9].item_id),(1,200,391010000))
        self.assertEqual(sum(r.enabled!=0 for r in p.rows),1)
    def test_reset_entire_catalog_and_duplicate_index_last_wins(self):
        old=tuple(replace(r,enabled=255,desired=100) for r in SOURCE_CATALOG)
        p=self.compile((self.row(9,'10'),self.row(9,'30')),catalog=old)
        self.assertEqual(p.rows[9].desired,30)
        self.assertTrue(all(not r.enabled and r.desired==0 for i,r in enumerate(p.rows) if i!=9))
    def test_signed32_quantity_preserves_low_dword_and_zero_does_not_disable(self):
        p=self.compile((self.row(9,'-1'),self.row(0,'0')))
        self.assertEqual(p.rows[9].desired,0xffffffff);self.assertEqual(p.rows[0].enabled,1)
    def test_source_out_of_bounds_retains_known_reset_and_overlay_prefix(self):
        for index in (-1,22,2147483647):
            p=self.compile((self.row(9,'20'),self.row(index)))
            self.assertFalse(p.complete);self.assertEqual(p.rows[9].desired,20)
            self.assertEqual(plan_supply_stock(p,SupplyStockObservation({},{})).due,None)
    def test_invalid_profile_and_parser_inputs_are_not_silent_empty(self):
        with self.assertRaises(ValueError):compile_supply_list({})
        for bad in ('2147483648','1.000','0x10',''):
            with self.assertRaises(ValueError):self.compile((self.row(9,bad),))
        with self.assertRaises(ValueError):self.compile(({'subitems':['10']},))
    def test_empty_list_requires_no_inventory_observations(self):
        p=plan_supply_stock(self.compile(),SupplyStockObservation({},{}))
        self.assertFalse(p.due);self.assertEqual(p.calls,())
    def test_absent_item_requires_all28_slots_before_due(self):
        p=self.compile((self.row(9),));item=p.rows[9].item_id
        result=plan_supply_stock(p,self.observe(9,item))
        self.assertTrue(result.due);self.assertEqual(len(result.calls),28)
        self.assertEqual(result.status,'stock_item_absent')
        missing=SupplyStockObservation({(9,s):0 for s in range(14,41)},{})
        result=plan_supply_stock(p,missing)
        self.assertIsNone(result.due);self.assertEqual(result.missing,'row9 slot41 itemID')
    def test_last_matching_stack_wins_without_sum_or_first_match(self):
        p=self.compile((self.row(9),));item=p.rows[9].item_id
        obs=self.observe(9,item,(14,41),100)
        low=SupplyStockObservation(obs.item_ids,{(9,14):100,(9,41):10})
        r=plan_supply_stock(p,low)
        self.assertTrue(r.due);self.assertEqual(r.matched_slot,41)
        self.assertEqual(r.calls[-1],('00463538',9,41));self.assertEqual(len(r.calls),29)
        high=SupplyStockObservation(obs.item_ids,{(9,14):0,(9,41):11})
        self.assertFalse(plan_supply_stock(p,high).due)
    def test_threshold10_11_arrow_and2_3_other_ignore_desired(self):
        for index,limit in ((9,10),(0,2)):
            p=self.compile((self.row(index,'1000'),));item=p.rows[index].item_id
            self.assertTrue(plan_supply_stock(p,self.observe(index,item,(20,),limit)).due)
            self.assertFalse(plan_supply_stock(p,self.observe(index,item,(20,),limit+1)).due)
    def test_signed_quantity_and_exact_case_name(self):
        catalog=(SupplyCatalogRow('arrow',123,enabled=2),)
        p=SupplyListConfiguration('observed_catalog',catalog,True)
        self.assertFalse(plan_supply_stock(p,self.observe(0,123,(20,),3)).due)
        self.assertTrue(plan_supply_stock(p,self.observe(0,123,(20,),0xffffffff)).due)
    def test_each_enabled_row_requires_fresh_id_and_quantity_observations(self):
        p=self.compile((self.row(0),self.row(9)))
        obs=self.observe(0,p.rows[0].item_id,(14,),3)
        r=plan_supply_stock(p,obs)
        self.assertIsNone(r.due);self.assertEqual(r.missing,'row9 slot14 itemID')
        self.assertEqual(r.calls[28],('00463538',0,14))
    def test_quantity_is_read_only_after_all_id_calls_and_can_be_unknown(self):
        p=self.compile((self.row(9),));obs=self.observe(9,p.rows[9].item_id,(14,),100)
        missing=SupplyStockObservation({(9,s):obs.item_ids[(9,s)] for s in range(14,41)},obs.quantities)
        r=plan_supply_stock(p,missing)
        self.assertTrue(all(c[0]=='004634a4' for c in r.calls))
        r=plan_supply_stock(p,SupplyStockObservation(obs.item_ids,{}))
        self.assertEqual(r.missing,'row9 slot14 quantity');self.assertEqual(len(r.calls),29)
    def test_out_of_source_slot_and_nonraw_values_rejected(self):
        for key in ((0,13),(0,42),(-1,14),(True,14)):
            with self.assertRaises(ValueError):SupplyStockObservation({key:0},{})
        for value in (-1,True,0x100000000):
            with self.assertRaises(ValueError):SupplyStockObservation({(0,14):value},{})
    def test_npc_batch_projection_uses_source_widths_and_preserves_disabled_indices(self):
        p=plan_supply_buy_rows(self.compile((self.row(9,'65537'),)))
        self.assertTrue(p.complete);self.assertEqual(len(p.rows),22)
        self.assertEqual(p.rows[9].record.desired_quantity,1)
        self.assertEqual(p.rows[9].record.item_id,391010000)
        self.assertEqual(p.rows[9].vendor_id,0x3e418)
        self.assertEqual(p.rows[9].enabled,1);self.assertEqual(p.rows[8].enabled,0)
    def test_panel_list_to_existing_npc_engine_collects_source_record(self):
        from npc_buy_engine import NpcBuyState,NpcBuyObservation,npc_buy_step
        rows=plan_supply_buy_rows(self.compile((self.row(9,'200'),))).rows
        state=NpcBuyState({0x690:9,0x694:0,0x68c:len(rows),0x604:100})
        p=npc_buy_step(state,NpcBuyObservation(1000,current_target=100,row=rows[9],vendor_matches={'Sundries':True}))
        self.assertEqual(p.status,'row_collected');self.assertEqual(p.state.batch,(rows[9].record,))
        self.assertEqual(p.queue_payloads,()) # Collection alone sends nothing.
    def test_missing_catalog_fields_and_invalid_list_do_not_invent_npc_record(self):
        incomplete=self.compile((self.row(22),))
        self.assertFalse(plan_supply_buy_rows(incomplete).complete)
        custom=SupplyListConfiguration('observed',(SupplyCatalogRow('X',1,1),),True)
        self.assertFalse(plan_supply_buy_rows(custom).complete)

if __name__=='__main__':unittest.main()
