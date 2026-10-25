import unittest
from merchant_result_compare import MerchantCompareObservation as O, compare_merchant_rows as compare, parse_merchant_price_bytes as parse
from merchant_result_compare import plan_merchant_alpha_sort as alpha
from merchant_result_rows import MerchantResultRow as R


def row(price='0'):
    return R(0,'seller',('item','1',price,'PM','GİT','0','0'))


class MerchantResultCompareTests(unittest.TestCase):
    def test_valid_and_formatted_prices(self):
        for text,value in [(b'0',0),(b'999',999),(b'1.000',1000),(b'4.294.967.295',0xffffffff),(b'0.0.0',0)]:
            p=parse(text)
            self.assertTrue(p.complete)
            self.assertEqual(p.qword,value)

    def test_validator_rejects_whole_input_without_nul_truncation(self):
        for text in (b' 1',b'-1',b'+1',b'1,000',b'1\0',b'\xff',b'0x10'):
            p=parse(text)
            self.assertEqual((p.complete,p.status,p.qword),(True,'validator_rejected_zero',0))

    def test_length_threshold_is_not_global_dot_removal(self):
        for text in (b'',b'.',b'1.0',b'...',b'....'):
            p=parse(text)
            self.assertFalse(p.complete)
            self.assertEqual(p.status,'needs_native_parser_exception_path')
        self.assertEqual(parse(b'1.00').qword,100)
        self.assertEqual(parse(b'.123').qword,123)

    def test_scalar_overflow_is_not_fallback_zero(self):
        p=parse(b'9223372036854775808')
        self.assertFalse(p.complete)
        self.assertIsNone(p.qword)
        self.assertNotEqual(p.parser_code,0)

    def test_price_difference_wrap_and_discarded_high_dword(self):
        p=compare(row('4.294.967.295'),row('0'),3)
        self.assertEqual((p.result_dword,p.signed_result),(0xffffffff,-1))
        self.assertEqual(compare(row('4.294.967.296'),row('0'),3).result_dword,0)
        self.assertEqual(compare(row('0'),row('2.147.483.648'),3).signed_result,-2147483648)

    def test_quantity_observations_separate_from_price_parser(self):
        self.assertEqual(compare(row(),row(),2).status,'needs_first_StrToInt_return')
        self.assertEqual(compare(row(),row(),2,O(first_quantity_eax=4)).status,'needs_second_StrToInt_return')
        p=compare(row(),row(),2,O(first_quantity_eax=0,second_quantity_eax=0xffffffff))
        self.assertEqual(p.result_dword,1)

    def test_text_comparators_are_distinct_explicit_observations(self):
        o=O(compare_text_result=0xfffffffe,ansi_compare_text_result=3)
        self.assertEqual(compare(row(),row(),0,o).signed_result,-2)
        self.assertEqual(compare(row(),row(),1,o).signed_result,3)
        self.assertFalse(compare(row(),row(),0).result_written)

    def test_unsupported_columns_leave_output_untouched(self):
        for column in (4,5,6,7,0xffffffff):
            p=compare(row(),row(),column,previous_result=0x12345678)
            self.assertTrue(p.complete)
            self.assertFalse(p.result_written)
            self.assertEqual(p.result_dword,0x12345678)

    def test_price_failure_preserves_previous_outparam_and_reached_prefix(self):
        p=compare(row('1.0'),row('10'),3,previous_result=99)
        self.assertEqual(p.result_dword,99)
        self.assertFalse(p.result_written)
        self.assertIsNone(p.second_price)
        p=compare(row('10'),row('1.0'),3)
        self.assertEqual(p.first_price.qword,10)
        self.assertFalse(p.complete or p.sorting_verified or p.native_execution_verified)

    def test_non_ascii_conversion_not_guessed(self):
        self.assertEqual(compare(row('１２３'),row(),3).status,'needs_first_native_ANSI_conversion')

    def test_contracts(self):
        with self.assertRaises(ValueError):parse('1000')
        with self.assertRaises(ValueError):O(first_quantity_eax=-1)
        with self.assertRaises(ValueError):compare(row(),row(),True)

    def test_alpha_handle_gate_and_pending_message(self):
        self.assertEqual(alpha().status,'needs_HandleAllocated')
        p=alpha(False)
        self.assertTrue(p.complete)
        self.assertFalse(p.result_bool or p.send_requested)
        self.assertEqual(alpha(True).status,'needs_handle_return')
        p=alpha(True,123)
        self.assertFalse(p.complete)
        self.assertTrue(p.send_requested)
        self.assertEqual((p.hwnd,p.message,p.wparam,p.callback_va),(123,0x1030,0,0x50d8de0c))

    def test_alpha_unsigned_bool_result_is_not_order_proof(self):
        for value,wanted in ((0,False),(1,True),(0xffffffff,True)):
            p=alpha(True,123,value)
            self.assertEqual(p.result_bool,wanted)
            self.assertTrue(p.complete)
            self.assertFalse(p.sorted_order_verified or p.native_execution_verified)

    def test_alpha_does_not_invent_nonzero_handle_guard(self):
        p=alpha(True,0,0)
        self.assertTrue(p.send_requested)
        self.assertFalse(p.result_bool)
        with self.assertRaises(ValueError):alpha('yes')
        with self.assertRaises(ValueError):alpha(True,123,-1)


if __name__=='__main__':unittest.main()
