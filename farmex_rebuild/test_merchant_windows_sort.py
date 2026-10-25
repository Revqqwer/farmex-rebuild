import sys,unittest
from merchant_windows_sort import sort_merchant_rows_windows as sort,sort_prepared_merchant_rows
from merchant_result_rows import MerchantResultRow as R


def row(index,caption='Seller',item='Item',quantity='1',price='0'):
    return R(index,caption,(item,quantity,price,'PM','GİT','0','0'))


@unittest.skipUnless(sys.platform=='win32','Own Windows list control')
class MerchantWindowsSortTests(unittest.TestCase):
    def check(self,rows,column):
        p=sort(rows,column)
        self.assertTrue(p.complete,p.status)
        self.assertTrue(p.local_order_observed and p.native_control_executed and p.cleanup_verified)
        self.assertEqual((p.created_windows,p.destroyed_windows),(2,2))
        self.assertFalse(p.source_VCL_callback_executed or p.live_compatibility_verified)
        return p

    def test_seller_item_quantity_price(self):
        rows=(row(0,'Z','Z','30','300'),row(1,'A','A','10','100'),row(2,'M','M','20','200'))
        for column in range(4):self.assertEqual(self.check(rows,column).order,(1,2,0))

    def test_numeric_sort_does_not_use_lexical_order(self):
        rows=(row(0,quantity='2',price='2'),row(1,quantity='10',price='10'),row(2,quantity='1',price='1'))
        for column in (2,3):self.assertEqual(self.check(rows,column).order,(2,0,1))

    def test_duplicates_are_not_deduplicated(self):
        rows=(row(0),row(0),row(0))
        p=self.check(rows,3)
        self.assertEqual(sorted(p.order),[0,1,2])
        self.assertEqual(len(p.rows),3)

    def test_empty_and_singleton_skip_unreached_parse_errors(self):
        self.assertEqual(self.check((),3).order,())
        self.assertEqual(self.check((row(0,quantity='bad'),),2).order,(0,))

    def test_error_does_not_publish_order(self):
        p=sort((row(0,quantity='bad'),row(1,quantity='2')),2)
        self.assertFalse(p.complete or p.local_order_observed)
        self.assertEqual(p.order,())
        self.assertTrue(p.cleanup_verified)
        self.assertTrue(p.comparisons)

    def test_unsupported_column_is_only_a_gap_when_callback_reached(self):
        self.assertEqual(self.check((row(0),),4).order,(0,))
        p=sort((row(0),row(1)),4)
        self.assertFalse(p.complete)
        self.assertTrue(p.cleanup_verified)
        self.assertIn('result_unchanged',p.status)

    def test_contracts(self):
        with self.assertRaises(ValueError):sort([],0)
        with self.assertRaises(ValueError):sort((),True)

    def test_rebuild_intent_consumes_source_price_column(self):
        from merchant_result_filter import MerchantResultRecord as F,MerchantFilterSelection as S
        from merchant_result_rows import MerchantDisplayRecord as D,build_merchant_result_rows
        prepared=build_merchant_result_rows((D(F(0,1,1,1),'A','Item',300,0,0),D(F(0,1,1,1),'Z','Item',100,0,0)),S('Selling Merchant','all',1))
        p=sort_prepared_merchant_rows(prepared)
        self.assertTrue(p.complete,p.status)
        self.assertEqual(p.order,(1,0))

    def test_inline_reply_does_not_implicitly_sort_but_explicit_click_can(self):
        from merchant_result_filter import MerchantResultRecord as F,MerchantFilterSelection as S
        from merchant_result_rows import MerchantDisplayRecord as D,build_merchant_result_rows
        prepared=build_merchant_result_rows((D(F(0,1,1,1),'Z','Item',300,0,0),D(F(0,1,1,1),'A','Item',100,0,0)),S('Selling Merchant','all',1),finalize_rebuild=False)
        p=sort_prepared_merchant_rows(prepared)
        self.assertTrue(p.complete)
        self.assertFalse(p.native_control_executed)
        self.assertEqual((p.order,p.status),((0,1),'sort_not_requested'))
        q=sort_prepared_merchant_rows(prepared,0)
        self.assertTrue(q.complete,q.status)
        self.assertEqual(q.order,(1,0))


if __name__=='__main__':unittest.main()
