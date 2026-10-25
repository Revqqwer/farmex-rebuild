import struct
import unittest
from dataclasses import replace
from merchant_item_metadata import MerchantItemObservation as O, plan_merchant_item_metadata as metadata, project_merchant_scan_with_lookups as project
from item_lookup import BaseItemLookupObservation as B, ExtensionLookupObservation as E
from item_name import ItemNameObservation as N
from merchant_scan_results import MerchantActorMetadata as A
from merchant_result_filter import MerchantFilterSelection as S


def observed():
    return O(B(first_variant_byte=1,function_target=0x9000,call_returned=True,result_eax=0x1000),
        0x123402,E(0x4000,0x5000,0x9004,True,0x2000),11,107,
        N(metadata_category=2,storage_dword=4,pointer_dword=0,bad_read_result=0,captured=b'Bow\0'+b'x'*251),
        12,b'BOW(+7) (REVERSE)')


def packet(two=False):
    slot=struct.pack('<IHHI',123456,2,99,1000)
    return b'\x68\x23\x01\x34\x12'+slot*(2 if two else 1)+b'\0'*12*(10 if two else 11)


class MerchantItemMetadataTests(unittest.TestCase):
    def test_lookup_name_and_independent_categories_compose(self):
        p=metadata(123456,observed(),lambda b:b.decode('ascii'))
        self.assertTrue(p.complete)
        self.assertEqual((p.base.key,p.extension.key),(123000,456))
        self.assertEqual((p.metadata.base_name,p.metadata.name_category_byte,p.metadata.stored_category_byte),('Bow',11,12))
        self.assertEqual(p.name.family,'lookup')
        self.assertEqual(p.reads,((0x1004,'0045dbdc:resolver_type'),(0x204c,'0045dbdc:name_category'),(0x2000,'0045dc44:extension_id'),(0x204c,'0045dbdc:stored_category')))
        self.assertFalse(p.native_execution_verified or p.native_text_conversion_verified)

    def test_name_helper_receives_supplied_pointers_without_relookup(self):
        p=metadata(123456,observed(),lambda b:b.decode('ascii'))
        self.assertNotIn('00465514',[name for name,args in p.name.calls])
        self.assertNotIn('00465580',[name for name,args in p.name.calls])
        self.assertIn(('0045dbdc:name_category',(0x2044,)),p.name.calls)

    def test_ordered_missing_boundaries(self):
        self.assertEqual(metadata(1).status,'base:needs_first_variant')
        o=observed()
        for field,wanted in [('resolver_type_raw','needs_resolver_type'),('name_category_byte','needs_name_category'),('extension_id_dword','needs_extension_id'),('stored_category_byte','needs_stored_category')]:
            p=metadata(123456,replace(o,**{field:None}),lambda b:b.decode('ascii'))
            self.assertEqual(p.status,wanted)
            self.assertIsNone(p.metadata)

    def test_no_decoder_or_failed_conversion_does_not_create_text(self):
        self.assertEqual(metadata(1,observed()).status,'needs_explicit_own_name_decoder')
        def fail(data):raise OSError('local codec unavailable')
        p=metadata(1,observed(),fail)
        self.assertFalse(p.complete)
        self.assertIsNotNone(p.name.ansi_bytes)

    def test_name_capture_gap_is_not_empty_name(self):
        o=observed();o=replace(o,name=replace(o.name,captured=None))
        p=metadata(1,o,lambda b:b.decode('ascii'))
        self.assertEqual(p.status,'name:needs_observation')
        self.assertIsNone(p.metadata)

    def test_full_owned_reply_to_lookup_to_display_chain(self):
        p=project(packet(),A('seller',825,520),{0:observed()},S('Buying Merchant','Rebirth Unique Item',1),lambda b:b.decode('ascii'))
        self.assertTrue(p.complete)
        self.assertEqual(p.results.rows.rows[0].subitems[0],'Bow(+7) (Reverse)')
        self.assertEqual(p.results.rows.rows[0].subitems[2],'1.000')
        self.assertFalse(p.source_parser_return_verified or p.native_execution_verified)

    def test_missing_second_item_keeps_first_record_without_success_receipt(self):
        p=project(packet(True),A('seller',0,0),{0:observed()},S('Buying Merchant','all',1),lambda b:b.decode('ascii'))
        self.assertFalse(p.complete)
        self.assertEqual(p.status,'item_metadata:base:needs_first_variant')
        self.assertEqual((len(p.results.records),p.results.stopped_slot),(1,1))

    def test_unreached_actor_and_rejected_length_skip_item_production(self):
        for payload,actor in [(b'',A('seller',0,0)),(packet(),None)]:
            p=project(payload,actor,{},S('Buying Merchant','all'))
            self.assertEqual(p.item_plans,())

    def test_contracts(self):
        with self.assertRaises(ValueError):O(name_category_byte=256)
        with self.assertRaises(ValueError):metadata(1,'invalid')
        with self.assertRaises(ValueError):project(packet(),None,{12:observed()},S('Buying Merchant','all'))


if __name__=='__main__':unittest.main()
