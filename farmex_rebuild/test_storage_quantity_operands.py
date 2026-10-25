import unittest
from dataclasses import replace
from source_coin import GuardedDwordSample as D
from storage_quantity_operands import StorageQuantitySamples as Samples,plan_storage_quantity
from storage_native_plans import NativeHelperObservation as Native,plan_native_helper
from storage_items import StorageItemObservation,StorageSelection,plan_storage_item

def cached(argument=42):
    signed=argument-(1<<32) if argument&0x80000000 else argument
    return Samples(((0x553d20,0x1000),(0x553d20,0x2000),(0x553d20,0x3000),
                    (0x553d20,0x4000),(0x553d20,0x5000)),
                   format_span_returned=True,formatted_ansi=str(signed).encode('ascii'),
                   memset_returned=True,copy_returns=(True,True,True),cleanup_returned=True)

class QuantityOperandTests(unittest.TestCase):
    def test_each_native_write_uses_fresh_cache_address(self):
        p=plan_storage_quantity(42,cached())
        self.assertTrue(p.complete);self.assertEqual(p.status,'writes_planned')
        self.assertEqual(p.memory_writes,((0x2000,b'\0'*14),(0x3000,b'42'),(0x4010,b'\x02'),(0x5028,b'\0')))
        self.assertEqual(p.global_writes,());self.assertFalse(p.independently_verified)

    def test_zero_cache_records_root_store_then_fresh_add_operand(self):
        o=replace(cached(),global_samples=((0x553d20,0),(0x553f48,0x1000),(0x554134,0x40),
            (0x553d20,0x7000),(0x553d20,0x8000),(0x553d20,0x9000),(0x553d20,0xa000),(0x553d20,0xb000)),
            guarded_samples=(D(0x1000,1,0x6000),))
        p=plan_storage_quantity(42,o)
        self.assertTrue(p.complete);self.assertEqual(p.global_writes,((0x553d20,0x6000),(0x553d20,0x7040)))
        self.assertEqual(p.memory_writes[0],(0x8000,b'\0'*14))

    def test_null_or_failed_root_still_stores_and_adds_offset(self):
        for address,samples in ((0,()),(0x1000,(D(0x1000,0),))):
            o=replace(cached(),global_samples=((0x553d20,0),(0x553f48,address),(0x554134,4),
                (0x553d20,0),(0x553d20,4),(0x553d20,4),(0x553d20,4),(0x553d20,4)),guarded_samples=samples)
            p=plan_storage_quantity(42,o)
            self.assertTrue(p.complete);self.assertEqual(p.global_writes,((0x553d20,0),(0x553d20,4)))

    def test_cache_and_destination_offsets_wrap_dword(self):
        o=replace(cached(),global_samples=((0x553d20,0),(0x553f48,0),(0x554134,0x20),
            (0x553d20,0xfffffff0),(0x553d20,0),(0x553d20,0),(0x553d20,0xfffffff8),(0x553d20,0xfffffff0)))
        p=plan_storage_quantity(42,o)
        self.assertTrue(p.complete);self.assertEqual(p.global_writes[-1],(0x553d20,0x10))
        self.assertEqual(p.memory_writes,((0,b'\0'*14),(0,b'42'),(8,b'\x02'),(0x18,b'\0')))

    def test_format_receipt_and_bytes_are_separate_before_cache_reads(self):
        for o in (replace(cached(),format_span_returned=None),replace(cached(),format_span_returned=False),
                  replace(cached(),formatted_ansi=None)):
            p=plan_storage_quantity(42,o)
            self.assertFalse(p.complete);self.assertEqual(p.memory_writes,());self.assertEqual(p.global_writes,())
            self.assertFalse(any(s[0]=='global' for s in p.steps))

    def test_signed_decimal_and_observed_copy_limit(self):
        for argument,text in ((0,b'0'),(0xffffffff,b'-1'),(99999999,b'99999999'),((-9999999)&0xffffffff,b'-9999999')):
            p=plan_storage_quantity(argument,cached(argument))
            self.assertTrue(p.complete);self.assertEqual(p.memory_writes[1][1],text)
            self.assertEqual(p.memory_writes[2][1],bytes((len(text),)))
        for argument in (1000000000,0x7fffffff,0x80000000):
            p=plan_storage_quantity(argument,cached(argument))
            self.assertFalse(p.complete);self.assertEqual(p.status,'unresolved_stack_buffer_overwrite')
            self.assertEqual(p.memory_writes,());self.assertEqual(p.global_writes,())

    def test_ninth_byte_spills_saved_pointer_after_its_final_source_read(self):
        for argument in (100000000,(-99999999)&0xffffffff):
            p=plan_storage_quantity(argument,cached(argument))
            self.assertTrue(p.complete);self.assertEqual(len(p.memory_writes[1][1]),9)
            self.assertIn(('stack_pointer_final_byte_spill',p.memory_writes[1][1][-1]),p.steps)
            self.assertEqual(p.memory_writes[2][1],b'\x09')

    def test_each_copy_return_gap_preserves_only_reached_write_intents(self):
        p=plan_storage_quantity(42,replace(cached(),memset_returned=None))
        self.assertFalse(p.complete);self.assertEqual(len(p.memory_writes),1)
        for i in range(3):
            p=plan_storage_quantity(42,replace(cached(),copy_returns=(True,)*i))
            self.assertFalse(p.complete);self.assertEqual(len(p.memory_writes),i+2)
            self.assertIn('memcpy%d'%i,p.missing)
        p=plan_storage_quantity(42,replace(cached(),cleanup_returned=None))
        self.assertFalse(p.complete);self.assertEqual(len(p.memory_writes),4)

    def test_all_fresh_cache_reads_required_and_no_last_address_reuse(self):
        o=cached()
        for n in range(5):
            p=plan_storage_quantity(42,replace(o,global_samples=o.global_samples[:n]))
            self.assertFalse(p.complete);self.assertLess(len(p.memory_writes),4)

    def test_prefix_global_store_survives_later_offset_or_add_gap(self):
        for tail in ((),((0x554134,None),),((0x554134,4),)):
            o=replace(cached(),global_samples=((0x553d20,0),(0x553f48,0))+tail)
            p=plan_storage_quantity(42,o)
            self.assertFalse(p.complete);self.assertEqual(p.global_writes,((0x553d20,0),));self.assertEqual(p.memory_writes,())

    def test_observation_types_reached_mismatches_and_contract(self):
        for o in (replace(cached(),formatted_ansi=b'0042'),
                  replace(cached(),global_samples=((0x553f48,0),))):
            with self.assertRaises(ValueError):plan_storage_quantity(42,o)
        for args in ({'copy_returns':(1,)},{'format_span_returned':1},{'formatted_ansi':'42'}):
            with self.assertRaises(ValueError):Samples(**args)
        with self.assertRaises(ValueError):plan_storage_quantity(True,cached())

class QuantityBindingTests(unittest.TestCase):
    def native(self,returned=True,o=None):
        return Native('004653a8',6,operand_samples=cached(6) if o is None else o,normal_returned=returned)
    def item(self,native):
        # Amount6 is the positive stock deficit10-4.
        return StorageItemObservation('vip_stock_withdraw',0,StorageSelection(0,excluded_index_4e7be8=0),
            1,1,100,10,4,(1,0,0),native_observations=(Native('004fe274',0,
                {0x553e80:0,0x554128:0,0x55412c:0},{0:0}),native,Native('00465334',1)))

    def test_native_facade_exposes_partial_write_intents_and_ordered_child(self):
        p=plan_native_helper(self.native(o=replace(cached(6),copy_returns=())))
        self.assertEqual(p.status,'needs_observation');self.assertEqual(len(p.memory_writes),2)
        self.assertFalse(p.ordered_plan.complete);self.assertIsNone(p.call)

    def test_item_quantity_return_gap_blocks_confirm_after_four_intents(self):
        p=plan_storage_item(0x5690b8,self.item(self.native(returned=None)))
        self.assertEqual(p.status,'needs_observation');self.assertIn('normal return1',p.reason)
        self.assertEqual(p.calls[-1].address,'004653a8');self.assertEqual(len(p.native_plans[-1].memory_writes),4)

    def test_quantity_inner_copy_gap_blocks_confirm_even_with_outer_receipt(self):
        p=plan_storage_item(0x5690b8,self.item(self.native(o=replace(cached(6),memset_returned=None))))
        self.assertEqual(p.status,'needs_observation');self.assertIn('memset',p.reason)
        self.assertEqual(p.calls[-1].address,'004653a8')

    def test_legacy_map_and_ordered_quantity_inputs_cannot_mix(self):
        with self.assertRaises(ValueError):Native('004653a8',6,{0x553d20:0},operand_samples=cached(6))
        with self.assertRaises(ValueError):Native('00465334',1,operand_samples=cached(1))

if __name__=='__main__':unittest.main()
