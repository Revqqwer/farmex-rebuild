import unittest
from dataclasses import replace
from storage_items import StorageSelection,StorageItemObservation,StorageItemCall,plan_storage_item
from storage_workers import VIP_BASE,INN_BASE,StorageObservation,storage_worker_step
from npc_sell_filter import SellFilterObservation,select_sale_item

class StorageItemTests(unittest.TestCase):
    def selection(self,**changes):
        return replace(StorageSelection(0,excluded_4e7c60=False,excluded_index_4e7be8=-1,
                       protect_grade_5622cf=False,list_index_41a5cc=1,list_checked_5622e1=True,
                       list_checked_e2=True,mode2_index_47677c=0,mode2_checked=True,mode2_checked4=True,
                       mode4_name_match=True,mode4_index=0),**changes)
    def obs(self,kind='vip_withdraw',**changes):
        return replace(StorageItemObservation(kind,0,self.selection(),0x100000,1,11,10,4,(1,1,0)),**changes)
    def plan(self,obs=None):
        obs=self.obs() if obs is None else obs
        return plan_storage_item(VIP_BASE if obs.kind=='vip_withdraw' else INN_BASE,obs)

    def test_vip_native_call_and_quantity_confirmation_order(self):
        r=self.plan()
        self.assertEqual(r.returned_value,1);self.assertEqual(r.quantity,11)
        self.assertEqual(r.calls[-5:],(StorageItemCall('004fe274',(VIP_BASE,0)),StorageItemCall('004653a8',(11,)),
                          StorageItemCall('00465334',(1,)),StorageItemCall('004653a8',(5,)),StorageItemCall('00465334',(1,))))

    def test_empty_item_early_exit_does_not_need_filter_or_dialogs(self):
        r=self.plan(self.obs(item_pointer=0,selection=StorageSelection(0),available_quantity=None))
        self.assertEqual(r.status,'skip');self.assertEqual(r.calls,())

    def test_vip_exclusion_applies_all_modes_and_selectors(self):
        for mode in (0,2,4,99):
            r=self.plan(self.obs(selection=self.selection(mode=mode,strict_byte=255,excluded_4e7c60=True)))
            self.assertEqual(r.status,'skip');self.assertEqual(r.calls,(StorageItemCall('004e7c60'),))

    def test_vip_nonstrict_protected_grade_bypasses_list(self):
        selection=self.selection(protect_grade_5622cf=True,minimum_grade_5622d0=5,extension_id=107,type_byte=2,
                                 list_index_41a5cc=None,list_checked_e2=None)
        r=self.plan(self.obs(selection=selection))
        self.assertEqual(r.returned_value,1);self.assertNotIn(StorageItemCall('0041a5cc'),r.calls)

    def test_vip_strict_protected_grade_rejects(self):
        selection=self.selection(strict_byte=1,protect_grade_5622cf=True,minimum_grade_5622d0=5,
                                 extension_id=107,type_byte=2)
        self.assertEqual(self.plan(self.obs(selection=selection)).status,'skip')

    def test_grade_type3_and_lower_grade_apply_list(self):
        for extension,type_byte in ((107,3),(104,None)):
            selection=self.selection(protect_grade_5622cf=True,minimum_grade_5622d0=5,extension_id=extension,
                                     type_byte=type_byte,list_checked_e2=False)
            self.assertEqual(self.plan(self.obs(selection=selection)).status,'skip')

    def test_minimum_grade_is_full_dword_in_storage_and_sale(self):
        selection=self.selection(protect_grade_5622cf=True,minimum_grade_5622d0=0xffffffff,extension_id=109,
                                 type_byte=None)
        self.assertEqual(self.plan(self.obs(selection=selection)).returned_value,1)
        sale=SellFilterObservation(0,False,-1,True,0x100,109,None,1,True)
        self.assertEqual(select_sale_item(sale).status,'selected')

    def test_vip_strict_and_nonstrict_use_different_normal_flags(self):
        for strict in (0,1,255):
            selection=self.selection(strict_byte=strict,list_checked_e2=False,list_checked_5622e1=True)
            self.assertEqual(self.plan(self.obs(selection=selection)).returned_value,1 if strict else 0)

    def test_normal_index_zero_skipped_mode2_index_zero_accepted(self):
        self.assertEqual(self.plan(self.obs(selection=self.selection(list_index_41a5cc=0))).status,'skip')
        r=self.plan(self.obs(selection=self.selection(mode=2,mode2_index_47677c=0)))
        self.assertEqual(r.returned_value,1)

    def test_mode2_different_checked4_checked6_and_negative_index(self):
        for strict in (0,1):
            s=self.selection(mode=2,strict_byte=strict,mode2_checked4=False,mode2_checked=True)
            self.assertEqual(self.plan(self.obs(selection=s)).returned_value,1 if strict else 0)
        s=self.selection(mode=2,mode2_index_47677c=-1)
        self.assertEqual(self.plan(self.obs(selection=s)).status,'skip')

    def test_other_vip_modes_only_exclusion_gate(self):
        s=StorageSelection(99,excluded_4e7c60=False)
        self.assertEqual(self.plan(self.obs(selection=s)).returned_value,1)

    def test_inn_deposit_nonzero_open_not_exact1(self):
        self.assertEqual(self.plan(self.obs('inn_deposit',open_byte=2)).returned_value,1)
        self.assertEqual(self.plan(self.obs('inn_deposit',open_byte=0,item_pointer=None)).status,'skip')

    def test_inn_deposit_mode0_exact_minus1_stock_sentinel(self):
        for index in (-2,0,1):
            r=self.plan(self.obs('inn_deposit',selection=self.selection(excluded_index_4e7be8=index)))
            self.assertEqual(r.status,'skip')
        self.assertEqual(self.plan(self.obs('inn_deposit')).returned_value,1)

    def test_inn_deposit_protected_grade_bypasses_row_and_uses_fc78(self):
        s=self.selection(protect_grade_5622cf=True,minimum_grade_5622d0=5,extension_id=106,type_byte=1,
                         list_index_41a5cc=None)
        r=self.plan(self.obs('inn_deposit',selection=s))
        self.assertIn(StorageItemCall('0046fc78',(INN_BASE,0)),r.calls)
        self.assertNotIn(StorageItemCall('0041a5cc'),r.calls)

    def test_inn_deposit_modes2_and4_skip_normal_exclusion(self):
        for s in (StorageSelection(2,mode2_index_47677c=0,mode2_checked4=True),
                  StorageSelection(4,mode4_name_match=True,mode4_index=0)):
            r=self.plan(self.obs('inn_deposit',selection=s))
            self.assertEqual(r.returned_value,1);self.assertNotIn(StorageItemCall('004e7c60'),r.calls)

    def test_inn_deposit_mode4_exact_minus1_lookup_other_negative_retained(self):
        for index,expected in ((-1,0),(-2,1),(0,1)):
            r=self.plan(self.obs('inn_deposit',selection=self.selection(mode=4,mode4_index=index)))
            self.assertEqual(r.returned_value,expected)
        self.assertEqual(self.plan(self.obs('inn_deposit',selection=self.selection(mode=3))).status,'skip')

    def test_withdraw_mode2_exit_precedes_all_memory_observations(self):
        r=self.plan(StorageItemObservation('inn_withdraw',0,StorageSelection(2)))
        self.assertEqual(r.returned_value,0);self.assertEqual(r.calls,())

    def test_inn_withdraw_deficit_and_available_cap(self):
        r=self.plan(self.obs('inn_withdraw',selection=self.selection(excluded_index_4e7be8=0),available_quantity=3))
        self.assertEqual(r.quantity,3);self.assertEqual(r.returned_value,1)
        self.assertIn(StorageItemCall('0046fd04',(INN_BASE,0)),r.calls)
        self.assertIn(StorageItemCall('004653a8',(1,)),r.calls)

    def test_inn_withdraw_exact_minus1_lookup_skips_other_negative_reads_observed_target(self):
        for index,expected in ((-1,0),(-2,1),(0,1)):
            r=self.plan(self.obs('inn_withdraw',selection=self.selection(excluded_index_4e7be8=index)))
            self.assertEqual(r.returned_value,expected)

    def test_inn_withdraw_signed_wrapped_deficit_not_unsigned_math(self):
        for desired,existing in ((4,4),(3,4),(0x80000000,0)):
            r=self.plan(self.obs('inn_withdraw',selection=self.selection(excluded_index_4e7be8=0),
                                 desired_quantity=desired,existing_quantity=existing))
            self.assertEqual(r.returned_value,0);self.assertNotIn('0046fd04',[c.address for c in r.calls])

    def test_inn_withdraw_mode4_name_lookup_and_deficit(self):
        s=StorageSelection(4,mode4_name_match=True,mode4_index=0)
        r=self.plan(self.obs('inn_withdraw',selection=s))
        self.assertEqual(r.quantity,6);self.assertIn(StorageItemCall('0041e0d4'),r.calls)
        s=replace(s,mode4_name_match=False)
        self.assertEqual(self.plan(self.obs('inn_withdraw',selection=s)).returned_value,0)

    def test_inn_withdraw_other_modes_still_plan_zero_quantity_source_behavior(self):
        r=self.plan(self.obs('inn_withdraw',selection=StorageSelection(3),available_quantity=None))
        self.assertEqual(r.quantity,0);self.assertEqual(r.returned_value,1)
        self.assertIn(StorageItemCall('004653a8',(0,)),r.calls)

    def test_available_zero_still_reaches_source_native_helper_after_positive_deficit(self):
        s=self.selection(excluded_index_4e7be8=0)
        r=self.plan(self.obs('inn_withdraw',selection=s,available_quantity=0))
        self.assertEqual(r.quantity,0);self.assertEqual(r.returned_value,1)
        self.assertIn(StorageItemCall('0046fd04',(INN_BASE,0)),r.calls)

    def test_fresh_dialog_three_remains_true_has_different_return(self):
        for kind in ('vip_withdraw','inn_deposit','inn_withdraw'):
            s=self.selection(excluded_index_4e7be8=0) if kind=='inn_withdraw' else self.selection()
            r=self.plan(self.obs(kind,selection=s,dialog_bytes=(1,1,1)))
            self.assertEqual(r.calls[-1],StorageItemCall('00465334',(0,)))
            self.assertEqual(r.returned_value,0 if kind=='inn_withdraw' else 1)

    def test_dialog_byte2_does_not_confirm_and_unknown_is_not_closed(self):
        r=self.plan(self.obs(dialog_bytes=(2,2,2)))
        self.assertEqual(r.returned_value,1);self.assertNotIn('00465334',[c.address for c in r.calls])
        r=self.plan(self.obs(dialog_bytes=(1,None,0)))
        self.assertEqual(r.status,'needs_observation');self.assertIsNone(r.returned_value)
        self.assertIn(StorageItemCall('004653a8',(11,)),r.calls)

    def test_missing_grade_pointer_quantity_or_flags_is_unresolved(self):
        for obs in (self.obs(item_pointer=None),self.obs(available_quantity=None),
                    self.obs(selection=StorageSelection(0,excluded_4e7c60=False)),
                    self.obs(selection=self.selection(list_checked_e2=None))):
            self.assertEqual(self.plan(obs).status,'needs_observation')

    def worker_state(self,base,mode):
        return {base:1,base+4:mode,base+8:0,base+9:1,base+0xc:0,base+0x10:0,base+0x14:0,
                0x561f60:1,0x561f6f:0,0x561f58:0}
    def test_vip_worker_nested_item_helper_advances_even_if_return0(self):
        item=self.obs(selection=self.selection(strict_byte=1),item_pointer=0)
        obs=StorageObservation(0,1,0,0,1,{'004611a0':1,'004fe420':0},{'004ff074':item})
        r=storage_worker_step(VIP_BASE,self.worker_state(VIP_BASE,2),obs)
        self.assertEqual(r.item_plans[0].returned_value,0)
        self.assertEqual(r.globals[VIP_BASE+0x10],1);self.assertEqual(r.globals[VIP_BASE+0x14],1)

    def test_inn_worker_nested_native_plan_and_unknown_defers_counter(self):
        item=self.obs('inn_deposit')
        obs=StorageObservation(0,1,0,item_observations={'00470584':item})
        r=storage_worker_step(INN_BASE,self.worker_state(INN_BASE,1),obs)
        self.assertEqual(r.item_plans[0].returned_value,1);self.assertEqual(r.globals[INN_BASE+0xc],1)
        obs=replace(obs,item_observations={'00470584':replace(item,dialog_bytes=(None,None,None))})
        r=storage_worker_step(INN_BASE,self.worker_state(INN_BASE,1),obs)
        self.assertEqual(r.status,'needs_observation');self.assertEqual(r.globals[INN_BASE+0xc],0)

    def test_worker_nested_observation_binds_slot_mode_and_selector(self):
        good=self.obs(selection=self.selection(strict_byte=1))
        for item in (replace(good,slot_index=1),replace(good,selection=self.selection(strict_byte=0)),
                     replace(good,selection=self.selection(mode=2,strict_byte=1)),replace(good,kind='inn_deposit')):
            obs=StorageObservation(0,1,0,helpers={'004611a0':1,'004fe420':0},item_observations={'004ff074':item})
            with self.assertRaises(ValueError):storage_worker_step(VIP_BASE,self.worker_state(VIP_BASE,2),obs)

    def test_inn_outer_worker_ignores_zero_helper_return_from_remaining_dialog(self):
        item=self.obs('inn_withdraw',selection=self.selection(excluded_index_4e7be8=0),dialog_bytes=(1,1,1))
        obs=StorageObservation(0,1,0,item_observations={'00470124':item})
        r=storage_worker_step(INN_BASE,self.worker_state(INN_BASE,2),obs)
        self.assertEqual(r.item_plans[0].returned_value,0)
        self.assertEqual(r.globals[INN_BASE+0x10],1)

    def test_raw_field_width_validation(self):
        with self.assertRaises(ValueError):StorageSelection(0,minimum_grade_5622d0=0x100000000)
        with self.assertRaises(ValueError):StorageSelection(0,type_byte=256)
        with self.assertRaises(ValueError):replace(self.obs(),dialog_bytes=(0,0))
