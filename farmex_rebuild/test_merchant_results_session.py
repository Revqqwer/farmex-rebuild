import sys
import unittest
from merchant_results_session import OwnedMerchantResults
from merchant_result_rows import MerchantDisplayRecord as D
from merchant_result_filter import MerchantResultRecord as F


def item(seller, name, price, direction=0, category=1, amount=1):
    return D(F(direction, category, amount, 1, name.encode('ascii')), seller, name, price, 0, 0)


@unittest.skipUnless(sys.platform=='win32', 'Own Windows control')
class MerchantResultsSessionTests(unittest.TestCase):
    def test_filter_then_numeric_price_order(self):
        s=OwnedMerchantResults()
        s.replace_records((item('Z','A',10), item('A','B',2), item('Buy','B',1,1)))
        p=s.rebuild('Selling Merchant','Tümü','')
        self.assertTrue(p.complete,p.status)
        self.assertEqual([r.caption for r in p.rows],['A','Z'])
        self.assertEqual([r.record_index for r in p.rows],[1,0])
        self.assertTrue(p.sorting.cleanup_verified)

    def test_category_and_direction_are_source_text_values(self):
        s=OwnedMerchantResults()
        s.replace_records((item('Buy','A',2,1,2),item('Sell','A',1),item('Other','A',3,1,1)))
        self.assertEqual([r.caption for r in s.rebuild('Buying Merchant','Rare Item','').rows],['Buy'])
        self.assertEqual([r.caption for r in s.rebuild('unknown','unmatched','').rows],['Sell'])

    def test_search_requires_explicit_conversion_then_recovers(self):
        s=OwnedMerchantResults();s.replace_records((item('A','SWORD',1),item('B','AXE',2)))
        p=s.rebuild('Selling Merchant','Tümü','sword')
        self.assertFalse(p.complete)
        self.assertEqual(p.status,'needs_normalized_search')
        self.assertIsNone(p.sorting)
        q=s.rebuild('Selling Merchant','Tümü','sword',normalized_search=b'SWORD')
        self.assertTrue(q.complete)
        self.assertEqual([r.caption for r in q.rows],['A'])

    def test_click_sorts_current_rows_without_changing_record_identity(self):
        s=OwnedMerchantResults();s.replace_records((item('Z','B',1),item('A','A',2)))
        s.rebuild('Selling Merchant','Tümü','')
        p=s.sort_column(0)
        self.assertEqual([r.record_index for r in p.rows],[1,0])
        self.assertEqual(len(s.records),2)

    def test_replacement_invalidates_old_rows_and_duplicate_records_survive(self):
        s=OwnedMerchantResults();r=item('A','B',2)
        s.replace_records((r,r));p=s.rebuild('Selling Merchant','Tümü','')
        self.assertEqual(sorted(r.record_index for r in p.rows),[0,1])
        s.replace_records(())
        with self.assertRaises(ValueError):s.sort_column(0)
        self.assertEqual(s.rebuild('Selling Merchant','Tümü','').rows,())

    def test_failed_sort_does_not_publish_neutral_callback_order(self):
        s=OwnedMerchantResults();s.replace_records((item('A','B',1),item('B','B',2)))
        s.rebuild('Selling Merchant','Tümü','')
        p=s.sort_column(4)
        self.assertFalse(p.complete)
        self.assertEqual(p.rows,())
        self.assertTrue(p.sorting.cleanup_verified)
        with self.assertRaises(ValueError):s.sort_column(0)
        self.assertTrue(s.rebuild('Selling Merchant','Tümü','').complete)

    def test_contracts_and_utf16_search_length(self):
        s=OwnedMerchantResults()
        with self.assertRaises(ValueError):s.replace_records([])
        with self.assertRaises(ValueError):s.rebuild('Selling Merchant','Tümü',None)
        s.replace_records((item('A','B',1),))
        # Non-BMP text is legal input; it still needs source conversion bytes.
        self.assertEqual(s.rebuild('Selling Merchant','Tümü','\U0001f600').status,'needs_normalized_search')


if __name__=='__main__':unittest.main()
