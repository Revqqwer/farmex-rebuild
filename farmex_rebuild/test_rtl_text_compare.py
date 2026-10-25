import unittest,sys
from rtl_text_compare import compare_text_pinned as compare, ansi_compare_text_local
from merchant_result_compare import compare_merchant_rows, MerchantCompareObservation
from merchant_result_rows import MerchantResultRow as R


class RtlTextCompareTests(unittest.TestCase):
    def test_ascii_fold_preserves_exact_difference(self):
        self.assertEqual(compare('abc','ABC'),0)
        self.assertEqual(compare('abc','abd'),-1)
        self.assertEqual(compare('a','c'),-2)

    def test_odd_prefix_uses_extra_utf16_unit(self):
        self.assertEqual(compare('a','aa'),-65)
        self.assertEqual(compare('ab','abc'),-1)
        self.assertEqual(compare('abc','abcd'),-68)
        self.assertEqual(compare('abc','abc\0x'),-2)

    def test_non_ascii_is_not_unicode_casefold(self):
        self.assertEqual(compare('ö','Ö'),32)
        self.assertEqual(compare('ş','Ş'),1)
        self.assertEqual(compare('İ','i'),231)
        self.assertEqual(compare('I','ı'),-232)

    def test_null_empty_embedded_nul_and_surrogate_units(self):
        self.assertEqual(compare(None,'abc'),-3)
        self.assertEqual(compare('',None),0)
        self.assertEqual(compare('abc\0z','ABC\0a'),25)
        self.assertEqual(compare('🗡','🗡'),0)
        self.assertEqual(compare('\ud800','\ud801'),-1)

    def test_merchant_opt_in_uses_caption_and_preserves_capture_override(self):
        a=R(0,'a',('x',));b=R(1,'aa',('y',))
        p=compare_merchant_rows(a,b,0,use_owned_text_model=True)
        self.assertEqual(p.signed_result,-65)
        self.assertEqual(p.text_policy,'pinned_RTL_ASCII_fold_UTF16_pair')
        p=compare_merchant_rows(a,b,0,MerchantCompareObservation(compare_text_result=3),use_owned_text_model=True)
        self.assertEqual(p.signed_result,3)

    @unittest.skipUnless(sys.platform=='win32','Windows NLS policy')
    def test_local_windows_call_and_merchant_item_name_binding(self):
        p=ansi_compare_text_local('abc','ABC')
        self.assertEqual((p.signed_result,p.win32_result,p.locale,p.flags),(0,2,0x400,1))
        a=R(0,'seller',('abc',));b=R(1,'other',('ABC',))
        q=compare_merchant_rows(a,b,1,use_owned_text_model=True)
        self.assertEqual(q.signed_result,0)
        self.assertFalse(q.native_execution_verified or q.sorting_verified)

    def test_contracts(self):
        with self.assertRaises(ValueError):compare(b'a','a')
        with self.assertRaises(ValueError):compare_merchant_rows(R(0,'a',()),R(1,'b',()),0,use_owned_text_model=1)


if __name__=='__main__':unittest.main()
