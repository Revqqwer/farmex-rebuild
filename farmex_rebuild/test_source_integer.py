import unittest
from dataclasses import replace
from source_integer import SourceIntegerObservation as O,SourceIntegerFrame,plan_source_integer as plan

def normal(q=60):return O(True,'normal',True,q,cleanup_returned=True)

class SourceIntegerTests(unittest.TestCase):
    def test_full_QWORD_preserved_and_only_lowDWORD_is_time_store_candidate(self):
        p=plan('4294967297',60,normal(0x100000001));self.assertTrue(p.complete)
        self.assertEqual((p.result_qword,p.low_dword,p.high_dword),(0x100000001,1,1))
        self.assertFalse(p.lexical_conversion_verified)

    def test_signed_default_is_CDQ_extended_not_zero_extended(self):
        p=plan('unknown',0x80000001,O(True,'catch_landing',catch_landing_returned=True,cleanup_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.result_qword,0xffffffff80000001)

    def test_invalid_or_empty_text_does_not_implicitly_choose_default(self):
        for text in ('','abc','0x10',' 1 ','9999999999999999999999999'):
            p=plan(text,60,O(True));self.assertFalse(p.complete);self.assertEqual(p.needed,'route')

    def test_catch_landing_does_not_consume_normal_parser_result(self):
        p=plan('captured',30,O(True,'catch_landing',True,123,True,True))
        self.assertTrue(p.complete);self.assertEqual(p.result_qword,30)
        self.assertIn('CC32260MT.DLL:_CatchCleanup',p.calls)

    def test_normal_and_catch_cleanup_have_separate_receipts(self):
        p=plan('60',60,O(True,'normal',False,60,cleanup_returned=True))
        self.assertEqual(p.needed,'parser_returned')
        p=plan('',60,O(True,'catch_landing',cleanup_returned=True));self.assertEqual(p.needed,'catch_landing_returned')

    def test_result_retained_across_outer_argument_cleanup_gap(self):
        f=SourceIntegerFrame('30',30);p=f.advance(replace(normal(0xabcdef0100000002),cleanup_returned=False))
        self.assertFalse(p.complete);self.assertEqual(p.result_qword,0xabcdef0100000002)
        p=f.advance(O(True,'catch_landing',True,999,True,True))
        self.assertTrue(p.complete);self.assertEqual(p.result_qword,0xabcdef0100000002)
        self.assertIs(f.advance(O()),p)

    def test_missing_parser_result_can_arrive_after_return_receipt(self):
        f=SourceIntegerFrame('text',0);p=f.advance(O(True,'normal',True))
        self.assertEqual(p.needed,'parser_qword')
        p=f.advance(O(parser_qword=0xffffffffffffffff,cleanup_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.low_dword,0xffffffff)

    def test_width_and_receipt_validation(self):
        for value in (True,-1,1<<64):
            with self.assertRaises(ValueError):normal(value)
        with self.assertRaises(ValueError):plan('1',1<<32,O())
        with self.assertRaises(ValueError):O(route='invalid_text')

if __name__=='__main__':unittest.main()
