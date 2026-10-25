import struct
import unittest
from merchant_scan_results import MerchantActorMetadata as A, MerchantItemMetadata as I, project_merchant_scan_results as project, format_scanned_item_name
from merchant_result_filter import MerchantFilterSelection as S


def packet(slots=()):
    return b'\x68\x23\x01\x34\x12'+b''.join(struct.pack('<IHHI',*slot) for slot in slots)+b'\0'*12*(12-len(slots))


class MerchantScanResultsTests(unittest.TestCase):
    def test_raw_reply_to_metadata_to_filtered_columns(self):
        p=project(packet(((123456,2,99,1000000),)),A('seller',825,0xffffffff),{0:I('Bow',11,11,107,b'BOW(+7) (REVERSE)')},S('Buying Merchant','Rebirth Item',1))
        self.assertTrue(p.complete)
        self.assertEqual(p.records[0].extension_digit,7)
        self.assertEqual(p.records[0].final_flag,0)
        self.assertEqual(p.rows.rows[0].subitems,('Bow(+7) (Reverse)','2','1.000.000','PM','GİT','825','-1'))
        self.assertFalse(p.source_parser_return_verified or p.native_execution_verified or p.rows.sorting_verified)

    def test_name_categories_and_zero_digit(self):
        for category,wanted in [(0,'Item'),(1,'Item(+0)'),(2,'Item(+0)'),(3,'Item'),(4,'Item'),(5,'Item(+0)'),(11,'Item(+0) (Reverse)'),(12,'Item (Reverse)'),(255,'Item')]:
            self.assertEqual(format_scanned_item_name(I('Item',category,category,10)),wanted)

    def test_name_category_and_stored_category_are_fresh_independent_values(self):
        p=project(packet(((1,4,5,6),)),A('seller',0,0),{0:I('Item',5,12,33)},S('Buying Merchant','Rebirth Unique Item',1))
        self.assertEqual(p.rows.rows[0].subitems[0],'Item(+3)')
        self.assertEqual(p.records[0].display.filter_record.category_1c,12)

    def test_empty_reply_needs_no_fabricated_actor_or_items(self):
        p=project(packet(),None,{},S('Buying Merchant','all'))
        self.assertTrue(p.complete)
        self.assertEqual(p.records,())
        self.assertEqual(p.rows.rows,())

    def test_missing_metadata_preserves_completed_append_prefix(self):
        data=packet(((1,2,3,4),(5,6,7,8)))
        self.assertEqual(project(data,None,{},S('Buying Merchant','all',1)).status,'needs_actor_metadata')
        p=project(data,A('seller',0,0),{0:I('First',1,1,0)},S('Buying Merchant','all',1))
        self.assertFalse(p.complete)
        self.assertEqual((p.added_count,len(p.records),p.stopped_slot),(1,1,1))
        self.assertIsNone(p.rows)

    def test_search_gap_does_not_rollback_record_append(self):
        p=project(packet(((1,2,3,4),)),A('seller',0,0),{0:I('Item',1,1,0)},S('Buying Merchant','all',0,1,b'I'))
        self.assertFalse(p.complete)
        self.assertEqual(p.status,'rows:needs_normalized_name')
        self.assertEqual(len(p.records),1)

    def test_existing_records_preserved_and_duplicates_not_deduplicated(self):
        args=(packet(((1,2,3,4),)),A('seller',0,0),{0:I('Item',1,1,0)},S('Buying Merchant','all',1))
        a=project(*args)
        b=project(*args,prior_records=a.records)
        self.assertEqual((b.added_count,len(b.records),len(b.rows.rows)),(1,2,2))
        self.assertEqual(b.records[0],b.records[1])

    def test_guard_rejection_does_not_clear_prior_records(self):
        p=project(packet(((1,2,3,4),)),A('seller',0,0),{0:I('Item',1,1,0)},S('Buying Merchant','all',1))
        q=project(b'',None,{},S('Buying Merchant','all'),p.records)
        self.assertEqual(q.records,p.records)
        self.assertIsNone(q.rows)

    def test_reply_composition_does_not_invent_rebuild_clear_or_sort(self):
        p=project(packet(((1,2,3,4),)),A('seller',0,0),{0:I('Item',1,1,0)},S('Buying Merchant','all',1))
        self.assertFalse(p.rows.filter_plan.clear_requested)
        self.assertFalse(p.rows.filter_plan.alpha_sort_requested)
        self.assertIsNone(p.rows.filter_plan.final_sort_column)
        self.assertEqual(p.rows.status,'rows_prepared')

    def test_contracts(self):
        with self.assertRaises(ValueError):A('seller',-1,0)
        with self.assertRaises(ValueError):I('item',256,1,0)
        with self.assertRaises(ValueError):project(packet(),None,{12:I('Item',0,0,0)},S('Buying Merchant','all'))


if __name__=='__main__':unittest.main()
