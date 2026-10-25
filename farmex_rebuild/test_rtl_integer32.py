import unittest
from rtl_integer32 import parse_rtl_integer32 as parse
from merchant_result_compare import compare_merchant_rows,MerchantCompareObservation as O
from merchant_result_rows import MerchantResultRow as R


class RtlInteger32Tests(unittest.TestCase):
    def test_decimal_boundaries_and_raw_error_result(self):
        for text,value in [('0',0),('2147483647',0x7fffffff),('-2147483648',0x80000000)]:
            p=parse(text);self.assertTrue(p.accepted);self.assertEqual(p.dword,value)
        p=parse('2147483648');self.assertEqual((p.dword,p.code),(0x80000000,11))
        p=parse('-2147483649');self.assertEqual((p.dword,p.code),(0x7fffffff,12))

    def test_hex_full_dword_and_negative_wrap(self):
        for text,value in [('$FFFFFFFF',0xffffffff),('0xFFFFFFFF',0xffffffff),('-$FFFFFFFF',1),('x10',16),('-0x80000000',0x80000000)]:
            p=parse(text);self.assertEqual((p.accepted,p.dword),(True,value))
        self.assertFalse(parse('$100000000').accepted)

    def test_error_does_not_always_apply_negative_sign(self):
        p=parse('-123x');self.assertEqual((p.dword,p.code),(123,5))
        p=parse('-$10z');self.assertEqual((p.dword,p.code),(16,5))

    def test_empty_prefix_code_and_whitespace(self):
        for text,code in [(None,1),('',1),('$',3),('0x',4),('+',2)]:self.assertEqual(parse(text).code,code)
        self.assertEqual(parse('  +5').dword,5)
        self.assertFalse(parse('\t5').accepted)
        self.assertFalse(parse('5 ').accepted)

    def test_nul_ascii_digits_and_long_zero_prefix(self):
        self.assertEqual(parse('5\0x').dword,5)
        self.assertTrue(parse('5\0x').accepted)
        self.assertEqual(parse('0'*200+'5').dword,5)
        self.assertFalse(parse('５').accepted)

    def test_merchant_quantity_opt_in_and_wrapped_subtraction(self):
        a=R(0,'a',('item','$FFFFFFFF'));b=R(1,'b',('item','0'))
        p=compare_merchant_rows(a,b,2,use_owned_integer_model=True)
        self.assertEqual(p.signed_result,-1)
        self.assertEqual(p.integer_policy,'pinned_RTL_ValLong_scalar')
        p=compare_merchant_rows(a,b,2,O(first_quantity_eax=7),use_owned_integer_model=True)
        self.assertEqual(p.result_dword,7)

    def test_quantity_error_does_not_write_or_parse_second(self):
        a=R(0,'a',('item','4294967295'));b=R(1,'b',('item','0'))
        p=compare_merchant_rows(a,b,2,previous_result=99,use_owned_integer_model=True)
        self.assertFalse(p.complete or p.result_written)
        self.assertEqual(p.result_dword,99)
        self.assertIsNone(p.second_quantity)

    def test_contracts(self):
        with self.assertRaises(ValueError):parse(b'1')
        with self.assertRaises(ValueError):compare_merchant_rows(R(0,'a',()),R(1,'b',()),2,use_owned_integer_model=1)


if __name__=='__main__':unittest.main()
