import unittest
from genie_duration import GenieDurationFrame
from source_integer import SourceIntegerObservation as O

class GenieDurationTests(unittest.TestCase):
    def test_separate_seconds_minutes_addresses_and_fallback_literals(self):
        for key,default,address in (('resume_seconds',60,0x569114),('notice_minutes',30,0x569144)):
            p=GenieDurationFrame(key,'captured').advance(O(True,'catch_landing',catch_landing_returned=True,cleanup_returned=True),helper_returned=True)
            self.assertTrue(p.complete);self.assertEqual(p.stores,((address,4,default),))

    def test_full_parse_is_truncated_at_producer_store_not_rejected(self):
        p=GenieDurationFrame('resume_seconds','4294967297').advance(O(True,'normal',True,0x100000001,cleanup_returned=True),helper_returned=True)
        self.assertEqual(p.stores,((0x569114,4,1),));self.assertEqual(p.conversion.high_dword,1)

    def test_outer_receipt_does_not_bypass_incomplete_child(self):
        p=GenieDurationFrame('notice_minutes','bad').advance(O(),helper_returned=True)
        self.assertFalse(p.complete);self.assertEqual(p.stores,())

    def test_child_result_retained_until_separate_outer_return(self):
        f=GenieDurationFrame('notice_minutes','30');p=f.advance(O(True,'normal',True,30,cleanup_returned=True))
        self.assertFalse(p.complete);self.assertEqual(p.stores,())
        p=f.advance(O(True,'normal',True,999,cleanup_returned=True),helper_returned=True)
        self.assertTrue(p.complete);self.assertEqual(p.stores,((0x569144,4,30),))
        self.assertIs(f.advance(),p)

    def test_negative_qword_stores_raw_lowDWORD(self):
        p=GenieDurationFrame('resume_seconds','-1').advance(O(True,'normal',True,0xffffffffffffffff,cleanup_returned=True),helper_returned=True)
        self.assertEqual(p.stores,((0x569114,4,0xffffffff),))
        self.assertFalse(p.native_execution_verified)

if __name__=='__main__':unittest.main()
