import unittest
from dataclasses import replace
from storage_items import StorageSelection,StorageItemObservation,StorageItemCall,plan_storage_item
from storage_workers import VIP_BASE,StorageObservation,storage_worker_step

class VipRemainingTests(unittest.TestCase):
    def selection(self,**changes):
        return replace(StorageSelection(0,excluded_4e7c60=False,excluded_index_4e7be8=0,
                       list_index_41a5cc=1,row_e1_byte=0,row_e2_byte=1,mode2_index_47677c=0,
                       mode2_checked4=True,mode2_checked=False,ore_gold_match=True,ore_match=False),**changes)
    def obs(self,kind='vip_deposit',**changes):
        return replace(StorageItemObservation(kind,0,self.selection(),0x100000,1,11,10,4,(1,1,0),0),**changes)
    def plan(self,obs=None):return plan_storage_item(VIP_BASE,self.obs() if obs is None else obs)

    def test_vip_deposit_fresh_capacity_test_precedes_pointer(self):
        r=self.plan(self.obs(capacity_full_byte=2,item_pointer=None))
        self.assertEqual(r.status,'skip');self.assertEqual(r.returned_value,0)
        self.assertEqual(r.calls,(StorageItemCall('004fe3c4',(VIP_BASE,)),))

    def test_vip_deposit_does_not_require_open_byte(self):
        r=self.plan(self.obs(open_byte=None))
        self.assertEqual(r.returned_value,1);self.assertIn(StorageItemCall('004fe2fc',(VIP_BASE,0)),r.calls)

    def test_vip_deposit_unchecked_existing_row_returns1_without_operation(self):
        s=self.selection(row_e2_byte=0,row_e1_byte=0)
        r=self.plan(self.obs(selection=s,available_quantity=None,dialog_bytes=(None,None,None)))
        self.assertEqual(r.status,'no_native_call');self.assertEqual(r.returned_value,1)
        self.assertNotIn('004fe2fc',[c.address for c in r.calls])

    def test_vip_deposit_checked_bytes_require_exact1_and_short_circuit(self):
        for e2,e1,status in ((1,None,'native_calls_planned'),(0,1,'native_calls_planned'),
                            (2,2,'no_native_call'),(255,0,'no_native_call')):
            r=self.plan(self.obs(selection=self.selection(row_e2_byte=e2,row_e1_byte=e1)))
            self.assertEqual(r.status,status)

    def test_vip_deposit_exclusion_or_nonpositive_index_return0(self):
        for s in (self.selection(excluded_4e7c60=True),self.selection(list_index_41a5cc=0),
                  self.selection(list_index_41a5cc=-2)):
            self.assertEqual(self.plan(self.obs(selection=s)).returned_value,0)

    def test_vip_deposit_grade_and_stock_lookup_are_unused(self):
        s=self.selection(protect_grade_5622cf=None,excluded_index_4e7be8=None)
        r=self.plan(self.obs(selection=s))
        self.assertEqual(r.returned_value,1);self.assertNotIn(StorageItemCall('004e7be8'),r.calls)

    def test_vip_deposit_unsigned_half_and_final_dialog_still_return1(self):
        r=self.plan(self.obs(available_quantity=0xffffffff,dialog_bytes=(1,1,1)))
        self.assertIn(StorageItemCall('004653a8',(0x7fffffff,)),r.calls)
        self.assertEqual(r.calls[-1],StorageItemCall('00465334',(0,)));self.assertEqual(r.returned_value,1)

    def test_vip_ore_calls_only_matching_name_and_native_helper_no_dialogs(self):
        for kind,address in (('vip_ore_deposit','004fe2fc'),('vip_ore_withdraw','004fe274')):
            r=self.plan(self.obs(kind,available_quantity=None,dialog_bytes=(None,None,None),
                                 selection=self.selection(ore_gold_match=True,ore_match=None)))
            self.assertEqual(r.calls,(StorageItemCall('00505d20:Mysterious gold mine'),StorageItemCall(address,(VIP_BASE,0))))
            self.assertEqual(r.returned_value,1);self.assertIsNone(r.quantity)

    def test_ore_second_match_or_neither(self):
        for matched,returned in ((True,1),(False,0)):
            r=self.plan(self.obs('vip_ore_withdraw',selection=self.selection(ore_gold_match=False,ore_match=matched)))
            self.assertIn(StorageItemCall('00505d20:Mysterious Ore'),r.calls)
            self.assertEqual(r.returned_value,returned)

    def test_ore_pointer_null_precedes_open_byte(self):
        r=self.plan(self.obs('vip_ore_deposit',item_pointer=0,open_byte=None))
        self.assertEqual(r.returned_value,0);self.assertEqual(r.calls,())
        self.assertEqual(self.plan(self.obs('vip_ore_deposit',open_byte=0)).returned_value,0)

    def test_ore_open_nonzero_byte2_is_allowed(self):
        self.assertEqual(self.plan(self.obs('vip_ore_deposit',open_byte=2)).returned_value,1)

    def test_vip_list_deposit_exact_minus1_other_negative_index_accepted(self):
        for index,returned in ((-1,0),(-2,1),(0,1)):
            r=self.plan(self.obs('vip_list_deposit',selection=self.selection(mode2_index_47677c=index)))
            self.assertEqual(r.returned_value,returned)

    def test_vip_list_deposit_row4_or_row6_short_circuit(self):
        for checked4,checked6,returned in ((True,None,1),(False,True,1),(False,False,0)):
            r=self.plan(self.obs('vip_list_deposit',selection=self.selection(mode2_checked4=checked4,mode2_checked=checked6)))
            self.assertEqual(r.returned_value,returned)

    def test_vip_list_deposit_no_exclusion_or_grade_and_third_dialog_return0(self):
        s=self.selection(excluded_4e7c60=None,protect_grade_5622cf=None)
        r=self.plan(self.obs('vip_list_deposit',selection=s,dialog_bytes=(1,1,1)))
        self.assertEqual(r.returned_value,0);self.assertEqual(r.status,'dialog_remaining')
        self.assertIn(StorageItemCall('004fe2fc',(VIP_BASE,0)),r.calls)

    def test_vip_stock_withdraw_uses_fe4a0_and_caps_deficit(self):
        r=self.plan(self.obs('vip_stock_withdraw',available_quantity=3))
        self.assertEqual(r.quantity,3);self.assertEqual(r.returned_value,1)
        self.assertIn(StorageItemCall('004fe4a0'),r.calls)
        self.assertNotIn(StorageItemCall('0046ffa4'),r.calls)
        self.assertIn(StorageItemCall('004653a8',(1,)),r.calls)

    def test_vip_stock_withdraw_lookup_exact_minus1_and_signed_deficit(self):
        for index,returned in ((-1,0),(-2,1),(0,1)):
            r=self.plan(self.obs('vip_stock_withdraw',selection=self.selection(excluded_index_4e7be8=index)))
            self.assertEqual(r.returned_value,returned)
        for desired,existing in ((4,4),(3,4),(0x80000000,0)):
            r=self.plan(self.obs('vip_stock_withdraw',desired_quantity=desired,existing_quantity=existing))
            self.assertEqual(r.returned_value,0)

    def test_vip_stock_withdraw_available0_still_calls_and_third_dialog_return0(self):
        r=self.plan(self.obs('vip_stock_withdraw',available_quantity=0,dialog_bytes=(1,1,1)))
        self.assertEqual(r.quantity,0);self.assertEqual(r.returned_value,0)
        self.assertIn(StorageItemCall('004fe274',(VIP_BASE,0)),r.calls)

    def test_inn_withdraw_empty_pointer_does_not_require_open_observation(self):
        r=self.plan(self.obs('inn_withdraw',item_pointer=0,open_byte=None))
        self.assertEqual(r.returned_value,0);self.assertEqual(r.calls,())

    def test_unknown_capacity_raw_check_or_ore_name_is_unresolved(self):
        for obs in (self.obs(capacity_full_byte=None),self.obs(selection=self.selection(row_e2_byte=None)),
                    self.obs('vip_ore_deposit',selection=self.selection(ore_gold_match=None)),
                    self.obs('vip_stock_withdraw',existing_quantity=None)):
            self.assertEqual(self.plan(obs).status,'needs_observation')

    def test_outer_vip_all_five_helper_bindings_and_counter_progress(self):
        rows=((1,'004ff600','vip_deposit'),(3,'004fed78','vip_stock_withdraw'),
              (4,'004fe5d8','vip_ore_deposit'),(5,'004fe828','vip_ore_withdraw'),(6,'004fea78','vip_list_deposit'))
        for mode,address,kind in rows:
            state={VIP_BASE:1,VIP_BASE+4:mode,VIP_BASE+0xc:0,VIP_BASE+0x10:0,
                   0x561f60:1,0x561f6f:0}
            obs=StorageObservation(0,1,0,helpers={'004611a0':1,'004fe3c4':0,'004fe420':0},
                                   item_observations={address:self.obs(kind)})
            r=storage_worker_step(VIP_BASE,state,obs)
            self.assertEqual(r.item_plans[0].returned_value,1)
            self.assertEqual(r.globals[VIP_BASE+(0x10 if mode in (3,5) else 0xc)],1)
            # These helpers do not read the global class/mode value.
            self.assertEqual(r.status,'slot_planned')

    def test_new_raw_byte_boundaries(self):
        with self.assertRaises(ValueError):self.selection(row_e1_byte=256)
        with self.assertRaises(ValueError):self.obs(capacity_full_byte=256)
