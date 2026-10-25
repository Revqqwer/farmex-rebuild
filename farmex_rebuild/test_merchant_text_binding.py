import sys,unittest
from dataclasses import replace
from merchant_text_normalization import WindowsMerchantText
from merchant_results_session import OwnedMerchantResults
from merchant_result_filter import MerchantResultRecord as F,MerchantFilterSelection as S
from merchant_result_rows import MerchantDisplayRecord as D
from merchant_scan_results import MerchantItemMetadata as M,MerchantActorMetadata as A,format_scanned_item_ansi
from merchant_item_metadata import project_merchant_scan_with_lookups
from test_merchant_item_metadata import observed,packet


@unittest.skipUnless(sys.platform=='win32','Own Windows text/sort binding')
class MerchantTextBindingTests(unittest.TestCase):
    def setUp(self):self.policy=WindowsMerchantText(1254)

    def test_captured_ANSI_survives_decoder_and_suffix_pipeline(self):
        o=replace(observed(),normalized_final_name=None)
        result=project_merchant_scan_with_lookups(packet(),A('seller',1,2),{0:o},
            S('Buying Merchant','Tümü',0xff000011),lambda raw:'OWN DISPLAY TEXT')
        self.assertTrue(result.complete,result.status)
        record=result.results.records[0].display
        self.assertEqual(record.filter_record.original_name_ansi,b'Bow(+7) (Reverse)')
        self.assertEqual(record.item_name,'OWN DISPLAY TEXT(+7) (Reverse)')
        self.assertIsNone(record.filter_record.normalized_name)
        session=OwnedMerchantResults();session.replace_records((record,))
        p=session.rebuild('Buying Merchant','Tümü','bow(+7)',text_policy=self.policy)
        self.assertTrue(p.complete,p.status)
        self.assertEqual(len(p.rows),1)
        self.assertEqual([op for op,index,value in p.text_observations],['query','name'])
        self.assertFalse(result.source_parser_return_verified or p.live_compatibility_verified)

    def test_original_bytes_missing_does_not_encode_display_as_replacement(self):
        s=OwnedMerchantResults();s.replace_records((D(F(0,1,1,1),'seller','sword',1,0,0),))
        p=s.rebuild('Selling Merchant','Tümü','sword',text_policy=self.policy)
        self.assertFalse(p.complete)
        self.assertEqual(p.status,'needs_normalized_name')
        self.assertEqual([o[0] for o in p.text_observations],['query'])

    def test_explicit_normalized_capture_overrides_original_name_policy(self):
        s=OwnedMerchantResults();s.replace_records((D(F(0,1,1,1,b'SWORD',b'other'),'A','display',1,0,0),))
        p=s.rebuild('Selling Merchant','Tümü','ignored',normalized_search=b'SWORD',text_policy=self.policy)
        self.assertTrue(p.complete)
        self.assertEqual(len(p.rows),1)
        self.assertEqual(p.text_observations,())

    def test_category_direction_misses_skip_query_and_name_conversion(self):
        s=OwnedMerchantResults();s.replace_records((D(F(1,1,1,1,None,b'axe'),'A','display',1,0,0),))
        p=s.rebuild('Selling Merchant','Tümü','axe',text_policy=self.policy)
        self.assertTrue(p.complete)
        self.assertEqual((p.rows,p.text_observations),((),()))

    def test_rebuild_uses_fresh_query_and_does_not_mutate_captured_records(self):
        s=OwnedMerchantResults()
        records=tuple(D(F(0,1,1,1,None,name),'A','display',1,0,0) for name in (b'sword',b'axe'))
        s.replace_records(records)
        p=s.rebuild('Selling Merchant','Tümü','sword',text_policy=self.policy)
        q=s.rebuild('Selling Merchant','Tümü','axe',text_policy=self.policy)
        self.assertEqual([r.record_index for r in p.rows],[0])
        self.assertEqual([r.record_index for r in q.rows],[1])
        self.assertTrue(all(r.filter_record.normalized_name is None for r in s.records))
        self.assertEqual(s.sort_column(0).text_observations,q.text_observations)

    def test_gray_placeholder_does_not_require_raw_bytes_or_conversion(self):
        s=OwnedMerchantResults();s.replace_records((D(F(0,1,1,1),'A','display',1,0,0),))
        p=s.rebuild('Selling Merchant','Tümü','placeholder',search_color=0xff000011,text_policy=self.policy)
        self.assertTrue(p.complete)
        self.assertEqual(p.text_observations,())

    def test_missing_earlier_original_name_stops_later_name_consumption(self):
        s=OwnedMerchantResults();s.replace_records((D(F(0,1,1,1),'A','missing',1,0,0),
            D(F(0,1,1,1,None,b'sword'),'B','captured',2,0,0)))
        p=s.rebuild('Selling Merchant','Tümü','sword',text_policy=self.policy)
        self.assertEqual(p.status,'needs_normalized_name')
        self.assertEqual(p.prepared.filter_plan.stopped_index,0)
        self.assertEqual([o[0] for o in p.text_observations],['query'])

    def test_raw_suffix_is_only_pinned_ASCII_and_preserves_nonASCII_bytes(self):
        for category,suffix in ((0,b''),(1,b'(+7)'),(2,b'(+7)'),(5,b'(+7)'),(11,b'(+7) (Reverse)'),(12,b' (Reverse)')):
            m=M('different display',category,12,107,None,b'\xfd\xff')
            self.assertEqual(format_scanned_item_ansi(m),b'\xfd\xff'+suffix)
        self.assertIsNone(format_scanned_item_ansi(M('text',11,12,107)))

    def test_invalid_original_byte_types_and_policy_are_rejected(self):
        with self.assertRaises(ValueError):F(0,1,1,1,None,'Unicode is not original bytes')
        with self.assertRaises(ValueError):M('text',1,1,0,None,'wrong')
        with self.assertRaises(ValueError):OwnedMerchantResults().rebuild('Selling Merchant','Tümü','',text_policy='wrong')


if __name__=='__main__':unittest.main()
