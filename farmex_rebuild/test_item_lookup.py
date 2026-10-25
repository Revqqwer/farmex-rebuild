import unittest
from dataclasses import replace
from item_lookup import BaseItemLookupObservation as B, ExtensionLookupObservation as E, plan_base_item_lookup as base, plan_extension_lookup as extension


class ItemLookupTests(unittest.TestCase):
    def test_base_unsigned_thousand_key_and_variant1_ecx_zero(self):
        o=B(first_variant_byte=1,function_target=0x9000,call_returned=True,result_eax=0x1000)
        for item,key in ((0,0),(999,0),(1000,1000),(0xffffffff,4294967000)):
            p=base(item,o)
            self.assertEqual((p.complete,p.key,p.ecx,p.pushed_args,p.result_eax),(True,key,0,(key,),0x1000))
            self.assertNotIn((0x553e46,'BYTE:second'),p.reads)

    def test_two_variant_reads_can_differ(self):
        o=B(0,2,0x2000,0x3000,0x9000,True,0x4000)
        p=base(12345,o)
        self.assertEqual((p.ecx,p.key,p.result_eax),(0x3000,12000,0x4000))
        self.assertEqual(base(12345,replace(o,first_variant_byte=2,second_variant_byte=1)).result_eax,0)

    def test_unsupported_variant_avoids_context_and_function_reads(self):
        p=base(1,B(0,0))
        self.assertTrue(p.complete)
        self.assertEqual(p.reads,((0x553e46,'BYTE:first'),(0x553e46,'BYTE:second')))
        self.assertIsNone(p.target)

    def test_base_reached_only_missing_fields_and_null_context(self):
        self.assertEqual(base(1).status,'needs_first_variant')
        self.assertEqual(base(1,B(0)).status,'needs_second_variant')
        self.assertEqual(base(1,B(0,2,0)).status,'unresolved_null_context_dereference')
        self.assertEqual(base(1,B(1,function_target=0)).status,'unresolved_null_call_target')

    def test_extension_zero_item_skips_all_external_reads(self):
        p=extension(0,0xffffffff)
        self.assertEqual((p.complete,p.result_eax,p.reads),(True,0,()))

    def test_extension_key_low_type_byte_and_address_wrap(self):
        p=extension(0xffffffff,0xabcdef02,E(0xfffffffc,0x1234,0x9000,True,0x5678))
        self.assertEqual((p.key,p.pushed_args,p.ecx),(295,(295,),0x1234))
        self.assertIn((4,'0045dc44:table_slot'),p.reads)
        self.assertEqual(p.result_eax,0x5678)

    def test_normal_return_is_separate_from_observed_result(self):
        o=E(0x1000,0x2000,0x9000,None,0x3000)
        self.assertEqual(extension(1234,1,o).status,'needs_call_normal_return')
        self.assertEqual(extension(1234,1,replace(o,call_returned=True,result_eax=None)).status,'needs_result_eax')
        p=extension(1234,1,replace(o,call_returned=True,result_eax=0))
        self.assertTrue(p.complete)
        self.assertEqual(p.result_eax,0)
        self.assertFalse(p.native_execution_verified)

    def test_zero_extension_context_is_not_an_invented_guard(self):
        p=extension(1234,0,E(0,0,0x9000,True,99))
        self.assertTrue(p.complete)
        self.assertEqual(p.ecx,0)
        self.assertEqual(p.result_eax,99)

    def test_contracts(self):
        with self.assertRaises(ValueError):base(-1)
        with self.assertRaises(ValueError):B(first_variant_byte=256)
        with self.assertRaises(ValueError):E(call_returned=1)
        with self.assertRaises(ValueError):extension(1,True)


if __name__=='__main__':unittest.main()
