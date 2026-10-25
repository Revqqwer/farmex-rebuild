import unittest
from dataclasses import replace
from merchant_result_filter import MerchantResultRecord as R, MerchantFilterSelection as S, filter_merchant_results as run


class MerchantResultFilterTests(unittest.TestCase):
    def test_source_category_codes_and_unmatched_default(self):
        records = tuple(R(0, c, c, 100) for c in (1, 2, 3, 4, 5, 11, 12, 6))
        for caption, wanted in [('Magic Item',1), ('Rare Item',2), ('Craft Item',3), ('Unique Item',4), ('Upgrade Item',5), ('Rebirth Item',11), ('Rebirth Unique Item',12)]:
            p = run(records, S('Selling Merchant', caption, 1))
            self.assertTrue(p.complete)
            self.assertEqual([records[m.record_index].category_1c for m in p.matches], [wanted])
        self.assertEqual(len(run(records, S('Selling Merchant','unmatched',1)).matches), 8)

    def test_only_exact_buying_literal_changes_direction(self):
        rows = (R(0,1,5,6), R(1,1,7,8), R(2,1,9,10))
        for text, expected in [('Buying Merchant',1), ('Selling Merchant',0), ('buying merchant',0), ('',0)]:
            self.assertEqual(run(rows,S(text,'all',1)).matches[0].record_index,expected)

    def test_reached_only_style_and_length(self):
        self.assertTrue(run((R(1,2,0,0),),S('Selling Merchant','all')).complete)
        self.assertEqual(run((R(0,2,0,0),),S('Selling Merchant','all')).status,'needs_search_font_color')
        self.assertTrue(run((R(0,2,0,0),),S('Selling Merchant','all',2)).complete)
        for length in (0,0x80000000,0xffffffff):
            self.assertTrue(run((R(0,2,0,0),),S('Selling Merchant','all',0,length)).complete)

    def test_explicit_normalization_no_python_casefold(self):
        rows = (R(0,1,5,6,b'IRON BOW'),R(0,1,7,8,b'iron bow'))
        p = run(rows,S('Selling Merchant','all',0,3,b'BOW'))
        self.assertEqual(tuple(m.record_index for m in p.matches),(0,))
        self.assertEqual(run(rows,S('Selling Merchant','all',0,3)).status,'needs_normalized_search')

    def test_cstring_termination_and_empty_second_search(self):
        rows = (R(0,1,5,6,b'ABC\0MATCH'),)
        self.assertEqual(run(rows,S('Selling Merchant','all',0,5,b'MATCH')).matches,())
        self.assertEqual(len(run(rows,S('Selling Merchant','all',0,5,b'BC\0junk')).matches),1)
        self.assertEqual(len(run(rows,S('Selling Merchant','all',0,5,b'')).matches),1)

    def test_amount_category_and_unsigned_boundary(self):
        rows = tuple(R(0,c,7,a) for c,a in ((0,0),(0,1),(0,2),(0,0xffffffff),(1,99),(11,100)))
        p = run(rows,S('Selling Merchant','all',1))
        self.assertEqual([m.amount for m in p.matches],[7,7,2,0xffffffff,7,7])
        self.assertEqual([m.amount_field for m in p.matches],['+0x20','+0x20','+0x24','+0x24','+0x20','+0x20'])

    def test_missing_observation_preserves_prefix_without_final_sort(self):
        rows = (R(0,1,5,6,b'ABC'),R(0,1,7,8))
        p = run(rows,S('Selling Merchant','all',0,1,b'A'))
        self.assertFalse(p.complete)
        self.assertEqual((p.stopped_index,len(p.matches)),(1,1))
        self.assertFalse(p.alpha_sort_requested)
        self.assertIsNone(p.final_sort_column)

    def test_empty_finalization_and_no_source_mutation(self):
        p = run((),S('Selling Merchant','all'))
        self.assertTrue(p.clear_requested and p.alpha_sort_requested)
        self.assertEqual(p.final_sort_column,3)
        self.assertFalse(p.native_execution_verified or p.ui_execution_verified or p.live_compatibility_verified)
        rows = (R(0,1,5,6),)
        self.assertEqual(run(rows,S('Selling Merchant','all',1)),run(rows,S('Selling Merchant','all',1)))

    def test_raw_contracts(self):
        for kwargs in ({'direction_0c':True}, {'category_1c':256}, {'amount_20':-1}, {'normalized_name':'ABC'}):
            values = dict(direction_0c=0,category_1c=0,amount_20=0,alternate_amount_24=0)
            values.update(kwargs)
            with self.assertRaises(ValueError):R(**values)
        with self.assertRaises(ValueError):run([],S('Selling Merchant','all'))


if __name__ == '__main__':
    unittest.main()
