import unittest
from dataclasses import replace
from loot_classifier import *

class LootClassifierTests(unittest.TestCase):
    def setUp(self):
        self.fields={4:3,0x18:0,0x1c:7,0x21:0,0x20:0,0x11:0,0x14:10000}
        self.meta=LootMetadataObservation(1,1,2,100007,10000,1)
    def plan(self,items=None,fields=None,slots=None,state=LootListState(),cache=True):
        return plan_loot_list(items or (123,0,0,0,0,0,0,0),fields or self.fields,
            LootListObservation({0:self.meta} if slots is None else slots,cache),state)
    def test_each_slot_upgrade_inclusive_modulo10(self):
        fields={**self.fields,0x18:1}
        for index in range(8):
            items=tuple(123 if i==index else 0 for i in range(8))
            p=self.plan(items,fields,{index:self.meta})
            self.assertEqual(p.attempt_slots,(index,));self.assertEqual(p.state.selected[index],1)
            low=replace(self.meta,upgrade_value=100006)
            self.assertEqual(self.plan(items,fields,{index:low}).attempt_slots,())
    def test_eighth_slot_price_read_is_not_skipped_by_upgrade_match(self):
        fields={**self.fields,0x18:1};meta=replace(self.meta,price=None)
        p=self.plan(fields=fields,slots={0:meta})
        self.assertEqual(p.attempt_slots,(0,));self.assertNotIn(('00467820',0),p.calls)
        p=self.plan((0,0,0,0,0,0,0,123),fields,{7:meta})
        self.assertFalse(p.complete);self.assertEqual(p.reason,'slot7:price')
    def test_upgrade_flag_exact1_and_category3_exclusion(self):
        for flag,category,wanted in ((1,2,True),(2,2,False),(1,3,False)):
            p=self.plan(fields={**self.fields,0x18:flag},slots={0:replace(self.meta,category=category)})
            self.assertEqual(bool(p.attempt_slots),wanted)
    def test_category0_and4_flags_and_unsigned_price_equality(self):
        for category,offset in ((0,0x21),(4,0x20)):
            self.assertEqual(self.plan(fields={**self.fields,offset:255},slots={0:replace(self.meta,category=category)}).attempt_slots,(0,))
        for price,wanted in ((9999,()),(10000,(0,))):
            self.assertEqual(self.plan(fields={**self.fields,0x11:1},slots={0:replace(self.meta,price=price)}).attempt_slots,wanted)
        self.assertEqual(self.plan(fields={**self.fields,0x11:1,0x14:0xffffffff}).attempt_slots,())
    def test_cache_byte_requires_exact1(self):
        for byte,wanted in ((0,()),(1,(0,)),(255,())):
            p=self.plan(fields={**self.fields,0x18:1},slots={0:replace(self.meta,cache_byte=byte)})
            self.assertEqual(p.attempt_slots,wanted)
    def test_first_coins_bypasses_metadata_and_cache_but_other_slots_do_not(self):
        p=self.plan((900000000,0,0,0,0,0,0,0),slots={})
        self.assertEqual(p.attempt_slots,(0,));self.assertNotIn(('00465514',0),p.calls)
        p=self.plan((0,900000000,0,0,0,0,0,0),slots={1:replace(self.meta,lookup=0)})
        self.assertEqual(p.attempt_slots,());self.assertEqual(p.state.discarded,1)
    def test_null_lookup_and_metadata_skip_qualification(self):
        for meta in (LootMetadataObservation(lookup=0),LootMetadataObservation(lookup=1,metadata=0)):
            p=self.plan(slots={0:meta});self.assertTrue(p.complete)
            self.assertEqual((p.state.classified,p.state.discarded),(1,1))
    def test_price_helper_required_even_when_all_flags_off(self):
        p=self.plan(slots={0:replace(self.meta,price=None)})
        self.assertFalse(p.complete);self.assertEqual(p.reason,'slot0:price')
        self.assertEqual(p.writes,())
    def test_cache_completion_is_required_before_record_mask_writes(self):
        p=self.plan((900000000,0,0,0,0,0,0,0),slots={},cache=None)
        self.assertFalse(p.complete);self.assertEqual(p.writes,());self.assertEqual(p.state.classified,0)
    def test_cached_record_skips_all_metadata_and_uses_old_mask(self):
        st=LootListState(2,0,(0,255,0,0,0,0,0,0))
        p=self.plan(state=st,slots={},cache=None)
        self.assertTrue(p.complete);self.assertEqual(p.calls,(('00414984',1),))
        self.assertEqual(p.attempt_slots,(1,));self.assertEqual(p.writes,())
    def test_discard_and_done_flags_prevent_attempt_without_clearing_selection(self):
        selected=(1,0,0,0,0,0,0,0)
        for st in (LootListState(1,1,selected),LootListState(1,0,selected,(1,0,0,0,0,0,0,0))):
            p=self.plan(state=st,slots={},cache=None);self.assertEqual(p.attempt_slots,())
            self.assertEqual(p.state,st)
    def test_existing_selection_is_not_cleared_when_new_filters_reject(self):
        st=LootListState(selected=(0,1,0,0,0,0,0,0))
        p=self.plan(state=st)
        self.assertEqual(p.attempt_slots,(1,));self.assertEqual(p.state.discarded,0)
    def test_unknown_late_cache_preserves_known_earlier_write_prefix(self):
        p=self.plan((123,456,0,0,0,0,0,0),{**self.fields,0x18:1},
            {0:self.meta,1:replace(self.meta,cache_byte=None)})
        self.assertFalse(p.complete);self.assertEqual(p.writes,((0x35,1),))
        self.assertEqual(p.state.selected[0],1);self.assertEqual(p.state.classified,0)
    def test_mode_guard_and_raw_validation(self):
        self.assertEqual(self.plan(fields={4:2},slots={},cache=None).status,'not_list_mode')
        with self.assertRaises(ValueError):LootMetadataObservation(category=True)
        with self.assertRaises(ValueError):LootListState(selected=(0,)*7)
        with self.assertRaises(ValueError):LootListObservation({8:self.meta},True)
