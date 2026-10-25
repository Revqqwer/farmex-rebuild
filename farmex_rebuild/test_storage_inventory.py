import unittest
from dataclasses import replace
from storage_inventory import StorageSlot,StorageScanObservation,scan_storage
from storage_items import StorageSelection,StorageItemObservation,plan_storage_item
from storage_workers import VIP_BASE,INN_BASE,StorageObservation,storage_worker_step

class StorageInventoryTests(unittest.TestCase):
    def full(self,count):return {i:StorageSlot(0x1000+i,100,2001,3,1) for i in range(count)}
    def scan(self,kind,slots=None,**args):
        return scan_storage(StorageScanObservation(kind,self.full(28) if slots is None else slots,**args))

    def test_vip_stock_returns_first_stack_not_sum(self):
        rows=self.full(28);rows[0]=StorageSlot(1,100,2001,7)
        rows[1]=StorageSlot(2,100,2001,9)
        r=self.scan('vip_existing',rows,target_item_id=101)
        self.assertEqual(r.returned_value,7);self.assertEqual(r.read_slots,(0,))

    def test_composed_item_id_mod1000_and_dword_wrap(self):
        row=StorageSlot(1,0xffffffff,1002,12,1)
        r=self.scan('vip_existing',{0:row},target_item_id=1)
        self.assertEqual(r.returned_value,12)

    def test_vip_no_match_returns_zero_with_or_without_empty(self):
        for empty in (False,True):
            rows=self.full(28)
            if empty:rows[27]=StorageSlot(0)
            r=self.scan('vip_existing',rows,target_item_id=999)
            self.assertEqual(r.returned_value,0);self.assertEqual(len(r.read_slots),28)

    def test_inn_matching_type_must_be_exact1_and_first_eligible_stack(self):
        rows=self.full(28);rows[0]=StorageSlot(1,100,1,7,2);rows[1]=StorageSlot(2,100,1,9,1)
        r=self.scan('inn_existing',rows,target_item_id=101)
        self.assertEqual(r.returned_value,9);self.assertEqual(r.read_slots,(0,1))

    def test_inn_matching_quantity_zero_is_valid_return(self):
        r=self.scan('inn_existing',{0:StorageSlot(1,100,1,0,1)},target_item_id=101)
        self.assertEqual(r.returned_value,0);self.assertEqual(r.read_slots,(0,))

    def test_inn_no_match_no_empty_requires_uninitialized_stack_byte(self):
        r=self.scan('inn_existing',target_item_id=999)
        self.assertEqual(r.status,'needs_observation');self.assertIsNone(r.returned_value)
        self.assertIn('uninitialized',r.missing);self.assertEqual(len(r.read_slots),28)

    def test_inn_no_match_no_empty_observed_stack_byte_controls_fallback(self):
        for flag,returned in ((0,0xffffffff),(1,0),(2,0),(255,0)):
            r=self.scan('inn_existing',target_item_id=999,initial_empty_flag_byte=flag)
            self.assertEqual(r.returned_value,returned)

    def test_inn_any_empty_overrides_unknown_or_zero_stack_byte(self):
        rows=self.full(28);rows[27]=StorageSlot(0)
        for flag in (None,0,2):
            r=self.scan('inn_existing',rows,target_item_id=999,initial_empty_flag_byte=flag)
            self.assertEqual(r.returned_value,0)

    def test_stock_nonmatching_slot_metadata_unknown_remains_unknown(self):
        for kind in ('vip_existing','inn_existing'):
            r=self.scan(kind,{0:StorageSlot(1,100,1,None,1)},target_item_id=999)
            self.assertEqual(r.status,'needs_observation');self.assertIn('quantity',r.missing)

    def test_null_slot_needs_no_metadata_and_missing_later_slot_not_zero(self):
        r=self.scan('vip_existing',{0:StorageSlot(0)},target_item_id=999)
        self.assertEqual(r.status,'needs_observation');self.assertIn('slot1',r.missing)
        self.assertEqual(r.read_slots,(0,))

    def test_vip_capacity48_all_nonzero_or_first_empty(self):
        self.assertEqual(self.scan('vip_full',self.full(48)).returned_value,1)
        r=self.scan('vip_full',{0:StorageSlot(0)})
        self.assertEqual(r.returned_value,0);self.assertEqual(r.read_slots,(0,))

    def test_capacity_requires_pointer_observation_not_zero(self):
        r=self.scan('vip_full',{0:StorageSlot()})
        self.assertEqual(r.status,'needs_observation');self.assertEqual(r.read_slots,(0,))

    def test_bag_threshold0_exits_first_empty(self):
        self.assertEqual(self.scan('bag_full',{0:StorageSlot(0)}).returned_value,0)
        self.assertEqual(self.scan('bag_full').returned_value,1)

    def test_bag_threshold2_reads_next_slot_before_count_check(self):
        rows={0:StorageSlot(0),1:StorageSlot(0),2:StorageSlot(1)}
        r=self.scan('bag_full',rows,required_empty_count=2)
        self.assertEqual(r.returned_value,0);self.assertEqual(r.read_slots,(0,1,2))
        del rows[2]
        self.assertEqual(self.scan('bag_full',rows,required_empty_count=2).status,'needs_observation')

    def test_bag_last_slot_reaches_threshold_but_source_returns1(self):
        rows=self.full(28);rows[26]=StorageSlot(0);rows[27]=StorageSlot(0)
        self.assertEqual(self.scan('bag_full',rows,required_empty_count=2).returned_value,1)
        rows[25]=StorageSlot(0)
        self.assertEqual(self.scan('bag_full',rows,required_empty_count=2).returned_value,0)

    def test_bag_negative_signed_threshold_reads_slot0_then_returns0(self):
        r=self.scan('bag_full',{0:StorageSlot(1)},required_empty_count=0xffffffff)
        self.assertEqual(r.returned_value,0);self.assertEqual(r.read_slots,(0,))

    def test_inn192_free_counts_null_and_nonnull_decoded_zero(self):
        rows=self.full(192);rows[0]=StorageSlot(0);rows[191]=StorageSlot(1,0,1000)
        r=self.scan('inn_free',rows)
        self.assertEqual(r.returned_value,2);self.assertEqual(len(r.read_slots),192)

    def test_inn_free_missing_final_slot_is_not_partial_count(self):
        rows={i:StorageSlot(0) for i in range(191)}
        r=self.scan('inn_free',rows)
        self.assertEqual(r.status,'needs_observation');self.assertIsNone(r.returned_value)

    def item(self,kind,inventory):
        s=StorageSelection(0,excluded_index_4e7be8=0)
        return StorageItemObservation(kind,0,s,1,1,100,10,None,(0,0,0),
                                      inventory_observation=inventory,source_item_id=101)

    def test_vip_count_scan_replaces_scalar_stock_in_item_plan(self):
        scan=StorageScanObservation('vip_existing',{0:StorageSlot(1,100,1,4)},target_item_id=101)
        r=plan_storage_item(VIP_BASE,self.item('vip_stock_withdraw',scan))
        self.assertEqual(r.quantity,6);self.assertEqual(r.inventory_results[0].returned_value,4)

    def test_inn_unknown_stack_flag_prevents_quantity_plan(self):
        scan=StorageScanObservation('inn_existing',self.full(28),target_item_id=999)
        obs=replace(self.item('inn_withdraw',scan),source_item_id=999)
        r=plan_storage_item(INN_BASE,obs)
        self.assertEqual(r.status,'needs_observation');self.assertIsNone(r.returned_value)

    def test_inn_full_no_match_zero_stack_byte_sentinel_changes_deficit(self):
        scan=StorageScanObservation('inn_existing',self.full(28),target_item_id=999,initial_empty_flag_byte=0)
        obs=replace(self.item('inn_withdraw',scan),source_item_id=999)
        r=plan_storage_item(INN_BASE,obs)
        self.assertEqual(r.inventory_results[0].returned_value,0xffffffff)
        self.assertEqual(r.quantity,11);self.assertEqual(r.returned_value,1)

    def test_item_target_kind_and_scalar_scan_conflicts_rejected(self):
        scan=StorageScanObservation('vip_existing',{0:StorageSlot(0)},target_item_id=101)
        item=self.item('vip_stock_withdraw',scan)
        for obs in (replace(item,source_item_id=100),replace(item,existing_quantity=0),
                    replace(item,inventory_observation=replace(scan,kind='inn_existing'))):
            with self.assertRaises(ValueError):plan_storage_item(VIP_BASE,obs)

    def test_fresh_capacity_scan_into_vip_deposit(self):
        item=StorageItemObservation('vip_deposit',0,StorageSelection(0),None,
             capacity_observation=StorageScanObservation('vip_full',self.full(48)))
        r=plan_storage_item(VIP_BASE,item)
        self.assertEqual(r.returned_value,0);self.assertEqual(r.inventory_results[0].returned_value,1)

    def test_outer_worker_capacity_scan_and_threshold_binding(self):
        state={VIP_BASE:1,VIP_BASE+4:2,VIP_BASE+9:0,VIP_BASE+0x10:0,0x561f60:1,0x561f6f:0}
        scan=StorageScanObservation('bag_full',{0:StorageSlot(0)})
        obs=StorageObservation(0,1,0,helpers={'004611a0':1},scan_observations={'004fe420':scan})
        r=storage_worker_step(VIP_BASE,state,obs)
        self.assertEqual(r.status,'slot_planned');self.assertEqual(r.scan_results[0].returned_value,0)
        with self.assertRaises(ValueError):storage_worker_step(VIP_BASE,state,replace(obs,scan_observations={'004fe420':replace(scan,required_empty_count=2)}))
        with self.assertRaises(ValueError):storage_worker_step(VIP_BASE,state,replace(obs,helpers={'004611a0':1,'004fe420':0}))

    def test_outer_inn_cleanup_counts192_slots_from_scan(self):
        state={INN_BASE:1,INN_BASE+0x14:0,0x561f60:0,0x561f58:0}
        obs=StorageObservation(0,cleanup_open_byte=0,scan_observations={'0046ff6c':StorageScanObservation('inn_free',{i:StorageSlot(0) for i in range(192)})})
        r=storage_worker_step(INN_BASE,state,obs)
        self.assertEqual(r.globals[INN_BASE+0x14],192);self.assertEqual(r.globals[INN_BASE],0)

    def test_observations_copy_and_validate_raw_slots(self):
        rows={0:StorageSlot(0)};obs=StorageScanObservation('vip_full',rows);rows.clear()
        self.assertEqual(scan_storage(obs).returned_value,0)
        with self.assertRaises(ValueError):StorageSlot(pointer=True)
        with self.assertRaises(ValueError):StorageScanObservation('vip_full',{-1:StorageSlot(0)})
