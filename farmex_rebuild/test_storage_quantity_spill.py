import unittest
from dataclasses import replace
from storage_quantity_operands import StorageQuantitySamples as Samples,plan_storage_quantity
from storage_native_plans import NativeHelperObservation as Native,plan_native_helper
from storage_items import StorageItemObservation,StorageSelection,plan_storage_item

def samples(argument=1000000000,reads=((0x12345639,0x58),)):
    signed=argument-(1<<32) if argument&0x80000000 else argument
    return Samples(global_samples=((0x553d20,1),(0x553d20,0x2000),(0x553d20,0x3000),
                    (0x553d20,0x4000),(0x553d20,0x5000)),
                   format_span_returned=True,formatted_ansi=str(signed).encode('ascii'),
                   memset_returned=True,copy_returns=(True,True,True),cleanup_returned=True,
                   source_pointer_dword=0x12345678,spilled_read_samples=reads)

class QuantitySpillTests(unittest.TestCase):
    def test_tenth_byte_comes_from_modified_pointer_not_original_decimal(self):
        p=plan_storage_quantity(1000000000,samples())
        self.assertTrue(p.complete);self.assertEqual(p.text,'1000000000')
        self.assertEqual(p.stack_copy_bytes,b'100000000X')
        self.assertEqual(p.memory_writes[1],(0x3000,b'100000000X'))
        self.assertEqual(p.memory_writes[2],(0x4010,b'\x0a'))
        self.assertEqual(p.source_pointer_writes,((8,0x12345630),(9,0x12345830)))
        self.assertFalse(p.independently_verified)

    def test_eleven_bytes_preserve_nul_and_non_ascii_observed_bytes(self):
        o=samples(0x80000000,((0x1234563f,0),(0x12340040,255)))
        p=plan_storage_quantity(0x80000000,o)
        self.assertTrue(p.complete);self.assertEqual(p.text,'-2147483648')
        self.assertEqual(p.stack_copy_bytes,b'-21474836\x00\xff')
        self.assertEqual(p.source_pointer_writes,((8,0x12345636),(9,0x12340036),(10,0x12ff0036)))
        self.assertEqual(p.memory_writes[1][1],p.stack_copy_bytes)
        self.assertEqual(p.memory_writes[2][1],b'\x0b')

    def test_second_spill_read_address_depends_on_first_observed_byte(self):
        for byte,address in ((0,0x12340040),(255,0x1234ff40),(0x39,0x12343940)):
            p=plan_storage_quantity(0x80000000,samples(0x80000000,((0x1234563f,byte),(address,0x41))))
            self.assertTrue(p.complete);self.assertIn(('spill_source_read',10,address),p.steps)
            self.assertEqual(p.stack_copy_bytes[-2:],bytes((byte,0x41)))

    def test_missing_pointer_and_each_spill_prefix_stop_before_cache_and_writes(self):
        o=samples(0x80000000,((0x1234563f,0),(0x12340040,255)))
        p=plan_storage_quantity(0x80000000,replace(o,source_pointer_dword=None))
        self.assertEqual(p.status,'unresolved_stack_buffer_overwrite')
        for n in (0,1):
            p=plan_storage_quantity(0x80000000,replace(o,spilled_read_samples=o.spilled_read_samples[:n]))
            self.assertFalse(p.complete);self.assertEqual(len(p.stack_copy_bytes),9+n)
            self.assertEqual(p.memory_writes,());self.assertEqual(p.global_writes,())
            self.assertFalse(any(s[0]=='global' for s in p.steps))

    def test_unknown_byte_is_not_replaced_by_formatted_byte_or_zero(self):
        for reads,prefix in ((((0x1234563f,None),),b'-21474836'),
                             (((0x1234563f,0),(0x12340040,None)),b'-21474836\0')):
            p=plan_storage_quantity(0x80000000,samples(0x80000000,reads))
            self.assertFalse(p.complete);self.assertEqual(p.stack_copy_bytes,prefix)
            self.assertEqual(p.memory_writes,())

    def test_each_reached_spill_address_must_match_modified_pointer(self):
        for reads in (((0x12345681,0),),((0x1234563f,0),(0x12345640,255))):
            with self.assertRaises(ValueError):plan_storage_quantity(0x80000000,samples(0x80000000,reads))

    def test_short_path_does_not_consume_irrelevant_spill_addresses(self):
        p=plan_storage_quantity(42,samples(42,((0xdeadbeef,255),)))
        self.assertTrue(p.complete);self.assertEqual(p.stack_copy_bytes,b'42')
        self.assertEqual(p.source_pointer_writes,())

    def test_facade_retains_corrupted_bytes_and_copy_return_gap(self):
        o=replace(samples(),copy_returns=())
        p=plan_native_helper(Native('004653a8',1000000000,operand_samples=o,normal_returned=True))
        self.assertEqual(p.status,'needs_observation');self.assertEqual(len(p.memory_writes),2)
        self.assertEqual(p.memory_writes[-1][1],b'100000000X')
        self.assertEqual(p.ordered_plan.stack_copy_bytes,b'100000000X');self.assertIsNone(p.call)

    def test_complete_spill_operands_do_not_supply_item_outer_normal_return(self):
        n=Native('004653a8',1000000000,operand_samples=samples())
        initial=Native('004fe274',0,{0x553e80:0,0x554128:0,0x55412c:0},{0:0})
        item=StorageItemObservation('vip_stock_withdraw',0,StorageSelection(0,excluded_index_4e7be8=0),
             1,1,1000000000,1000000000,0,(1,0,0),native_observations=(initial,n))
        p=plan_storage_item(0x5690b8,item)
        self.assertEqual(p.status,'needs_observation');self.assertIn('normal return1',p.reason)
        self.assertTrue(p.native_plans[-1].ordered_plan.complete)
        self.assertEqual(p.calls[-1].address,'004653a8')

    def test_spill_sample_types_and_bounds_rejected(self):
        for changes in ({'source_pointer_dword':True},{'source_pointer_dword':-1},
                        {'spilled_read_samples':((1,256),)}, {'spilled_read_samples':((1,True),)},
                        {'spilled_read_samples':((1,1),(2,2),(3,3))}):
            with self.assertRaises(ValueError):replace(samples(),**changes)

if __name__=='__main__':unittest.main()
