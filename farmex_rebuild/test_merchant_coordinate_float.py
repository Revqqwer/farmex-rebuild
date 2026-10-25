import unittest
from merchant_coordinate_float import plan_merchant_coordinate_float as plan,merchant_coordinate_float_from_dword as raw


class MerchantCoordinateFloatTests(unittest.TestCase):
    def test_normal_coordinates_and_zero(self):
        for text,bits in (('0',0),('1',0x3f800000),('-1',0xbf800000),('825',0x444e4000),('520',0x44020000)):
            p=plan(text);self.assertTrue(p.complete);self.assertEqual(p.float32_bits,bits)

    def test_halfway_rounds_to_even_without_Python_float(self):
        for value,bits in ((16777217,0x4b800000),(16777219,0x4b800002),
                           (-16777217,0xcb800000),(-16777219,0xcb800002)):
            self.assertEqual(plan(str(value)).float32_bits,bits)

    def test_raw_signed_formatter_limits_and_exponent_carry(self):
        self.assertEqual(raw(0x7fffffff).float32_bits,0x4f000000)
        self.assertEqual(raw(0x80000000).float32_bits,0xcf000000)
        self.assertEqual(raw(0xffffffff).float32_bits,0xbf800000)

    def test_noncanonical_formats_remain_gaps_even_if_RTL_might_accept(self):
        for text in ('','+1','01','-0',' 1','1 ','1.0','1,0','1e0','inf','nan','1\0','١','2147483648','-2147483649'):
            self.assertFalse(plan(text).complete,text)

    def test_other_rounding_mode_is_not_silently_nearest(self):
        p=plan('825',rounding_policy='toward_zero')
        self.assertFalse(p.complete)
        self.assertEqual(p.status,'unsupported_rounding_policy')

    def test_flags_and_contracts(self):
        p=raw(0)
        self.assertFalse(p.native_source_execution_verified or p.live_compatibility_verified)
        with self.assertRaises(ValueError):plan(b'825')
        with self.assertRaises(ValueError):raw(-1)
        with self.assertRaises(ValueError):raw(True)


if __name__=='__main__':unittest.main()
