import unittest
from merchant_result_filter import MerchantResultRecord as R, MerchantFilterSelection as S
from merchant_result_rows import MerchantDisplayRecord as D, build_merchant_result_rows as build, format_source_price, format_source_coordinate


class MerchantResultRowsTests(unittest.TestCase):
    def test_price_grouping_boundaries(self):
        for value,text in [(0,'0'),(1,'1'),(999,'999'),(1000,'1.000'),(9999,'9.999'),(10000,'10.000'),(999999,'999.999'),(1000000,'1.000.000'),(4294967295,'4.294.967.295')]:
            self.assertEqual(format_source_price(value),text)

    def test_signed_coordinate_is_distinct_from_unsigned_amount(self):
        record = D(R(0,0,0xffffffff,1),'seller','item',1000,0xffffffff,0x80000000)
        p = build((record,),S('Selling Merchant','all',1))
        self.assertEqual(p.rows[0].subitems,('item','4294967295','1.000','PM','GİT','-1','-2147483648'))

    def test_column_order_with_alternate_amount(self):
        record = D(R(0,0,3,50),'seller','item',200,825,520)
        p = build((record,),S('Selling Merchant','all',1))
        self.assertEqual((p.rows[0].caption,p.rows[0].subitems),('seller',('item','50','200','PM','GİT','825','520')))
        self.assertTrue(p.formatting_complete)
        self.assertFalse(p.sorting_verified or p.ui_execution_verified or p.native_execution_verified or p.live_compatibility_verified)

    def test_filter_indexes_and_order_preserved_without_invented_sort(self):
        records = tuple(D(R(direction,1,1,1),seller,'item',price,0,0) for direction,seller,price in [(0,'Z',300),(1,'A',100),(0,'B',200)])
        p = build(records,S('Selling Merchant','all',1))
        self.assertEqual([r.record_index for r in p.rows],[0,2])
        self.assertEqual([r.caption for r in p.rows],['Z','B'])
        self.assertEqual(p.status,'rows_prepared_sort_pending')

    def test_filter_missing_name_retains_completed_row_prefix(self):
        records = (D(R(0,1,1,1,b'ABC'),'seller','item',1,0,0),D(R(0,1,1,1),'other','item',2,0,0))
        p = build(records,S('Selling Merchant','all',0,1,b'A'))
        self.assertFalse(p.formatting_complete)
        self.assertEqual(len(p.rows),1)
        self.assertEqual(p.status,'needs_normalized_name')

    def test_empty_rows_and_unicode_display(self):
        self.assertEqual(build((),S('Selling Merchant','all')).rows,())
        p=build((D(R(0,1,1,1),'İsim','Eşya',1,0,0),),S('Selling Merchant','all',1))
        self.assertEqual((p.rows[0].caption,p.rows[0].subitems[0]),('İsim','Eşya'))

    def test_contracts(self):
        for value in (-1,0x100000000,True):
            with self.assertRaises(ValueError):format_source_price(value)
            with self.assertRaises(ValueError):format_source_coordinate(value)
        with self.assertRaises(ValueError):build([],S('Selling Merchant','all'))


if __name__ == '__main__':
    unittest.main()
