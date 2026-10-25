import unittest
from rtl_integer import parse_rtl_integer,rtl_integer_or_default

class RtlIntegerTests(unittest.TestCase):
    def test_null_empty_sign_and_prefix_only_error_positions(self):
        for text,position in ((None,1),('',1),('+',2),('-',2),('$',2),('x',2),('0x',3),('  ',3)):
            p=parse_rtl_integer(text);self.assertFalse(p.accepted);self.assertEqual((p.qword,p.code),(0,position))

    def test_only_leading_ascii_spaces_are_skipped(self):
        self.assertEqual(parse_rtl_integer('  +5').qword,5)
        for text,code in (('5 ',2),('\t5',1),('\n5',1),('\u00a05',1),('5\t',2)):
            p=parse_rtl_integer(text);self.assertEqual(p.code,code);self.assertFalse(p.accepted)

    def test_five_hex_prefix_forms_and_signed_hex(self):
        for prefix in ('$','x','X','0x','0X'):
            p=parse_rtl_integer(prefix+'fF');self.assertTrue(p.accepted);self.assertEqual((p.radix,p.qword),(16,255))
            self.assertEqual(parse_rtl_integer('-'+prefix+'10').signed,-16)
        self.assertFalse(parse_rtl_integer('0b101').accepted)

    def test_signed_decimal_boundaries_and_failure_position(self):
        self.assertEqual(parse_rtl_integer('9223372036854775807').signed,(1<<63)-1)
        p=parse_rtl_integer('-9223372036854775808');self.assertTrue(p.accepted);self.assertEqual(p.signed,-(1<<63))
        p=parse_rtl_integer('9223372036854775808');self.assertFalse(p.accepted);self.assertEqual((p.code,p.qword),(19,1<<63))
        p=parse_rtl_integer('-9223372036854775809');self.assertFalse(p.accepted);self.assertEqual(p.code,20)

    def test_unsigned_hex_range_and_negation_modulo(self):
        p=parse_rtl_integer('$ffffffffffffffff');self.assertTrue(p.accepted);self.assertEqual(p.signed,-1)
        p=parse_rtl_integer('-0xFFFFFFFFFFFFFFFF');self.assertTrue(p.accepted);self.assertEqual(p.qword,1)
        p=parse_rtl_integer('0x10000000000000000');self.assertFalse(p.accepted);self.assertEqual(p.qword,0x1000000000000000)

    def test_invalid_input_retains_partial_result_without_success(self):
        p=parse_rtl_integer('-123z');self.assertEqual((p.signed,p.code),(-123,5));self.assertFalse(p.accepted)
        p=parse_rtl_integer('18446744073709551615');self.assertFalse(p.accepted);self.assertEqual(p.qword,0x1999999999999999)

    def test_embedded_nul_stops_even_with_longer_metadata(self):
        p=parse_rtl_integer('5\0not read');self.assertTrue(p.accepted);self.assertEqual(p.qword,5)
        p=parse_rtl_integer('0\0x10');self.assertTrue(p.accepted);self.assertEqual(p.qword,0)
        self.assertEqual(parse_rtl_integer('\0x5').code,1)

    def test_long_leading_zero_has_no_invented_decimal_length_limit(self):
        self.assertEqual(parse_rtl_integer('0'*2000+'5').qword,5)
        self.assertTrue(parse_rtl_integer('$'+'0'*2000+'5').accepted)

    def test_unicode_digit_and_surrogate_are_not_ascii_digits(self):
        for text in ('\uff15','\u0665','\ud800','\U0001f600','x\uff15'):
            self.assertFalse(parse_rtl_integer(text).accepted)
        self.assertEqual(parse_rtl_integer('12\ud800').code,3)

    def test_sign_after_prefix_and_gap_after_sign_are_invalid(self):
        for text in ('0x-10','$+10','++5','- 5','+ 5'):
            self.assertFalse(parse_rtl_integer(text).accepted)
        p=parse_rtl_integer('-0');self.assertTrue(p.accepted);self.assertEqual(p.qword,0)

    def test_type_contract_is_explicit(self):
        for text in (True,5,b'5',[]):
            with self.assertRaises(ValueError):parse_rtl_integer(text)

    def test_default_wrapper_discards_partial_value_and_preserves_parser_code(self):
        p=rtl_integer_or_default('123z',10)
        self.assertTrue(p.used_default);self.assertEqual((p.parser.qword,p.parser.code,p.result_qword),(123,4,10))
        self.assertFalse(p.native_bot_catch_verified)

    def test_raw_default_sign_extension_and_success_passthrough(self):
        p=rtl_integer_or_default('',0xffffffff)
        self.assertEqual(p.result_qword,0xffffffffffffffff)
        p=rtl_integer_or_default('$FFFFFFFFFFFFFFFF',10)
        self.assertFalse(p.used_default);self.assertEqual(p.result_qword,0xffffffffffffffff)

    def test_default_wrapper_raw_operand_contract(self):
        for default in (-1,1<<32,True,None):
            with self.assertRaises(ValueError):rtl_integer_or_default('5',default)

if __name__=='__main__':unittest.main()
