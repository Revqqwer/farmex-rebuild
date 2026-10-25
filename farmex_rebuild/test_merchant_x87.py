import unittest
from fractions import Fraction
from merchant_x87 import SellX87Sample as Sample,plan_sell_x87 as plan,_round_binary

class SellX87Tests(unittest.TestCase):
    def test_nearest_ties_to_even_without_host_float(self):
        self.assertEqual(_round_binary(Fraction(1)+Fraction(1,1<<24),24,0),1)
        self.assertEqual(_round_binary(Fraction(1)+Fraction(3,1<<24),24,0),Fraction(1)+Fraction(1,1<<22))
    def test_directed_rounds_for_negative_value(self):
        x=-Fraction(1)-Fraction(1,1<<24)
        self.assertEqual(_round_binary(x,24,1),-Fraction(1)-Fraction(1,1<<23))
        self.assertEqual(_round_binary(x,24,2),-1)
        self.assertEqual(_round_binary(x,24,3),-1)
    def test_known_finite_total_and_truncation(self):
        self.assertEqual(plan(100,Sample(0x37f,True)).net_qword,97)
        self.assertEqual(plan((-100)&((1<<64)-1),Sample(0x37f,True)).net_qword,(-97)&((1<<64)-1))
    def test_zero_and_negative_fraction_truncate_to_zero(self):
        self.assertEqual(plan(0,Sample(0x37f,True)).net_qword,0)
        self.assertEqual(plan((1<<64)-1,Sample(0x37f,True)).net_qword,0)
    def test_explicit_precision_and_rounding_fields(self):
        for bits,pc in ((24,0),(53,0x200),(64,0x300)):
            for rc in range(4):
                p=plan(123456789,Sample(0x7f|pc|(rc<<10),True))
                self.assertTrue(p.complete);self.assertEqual((p.precision_bits,p.rounding_code),(bits,rc))
    def test_control_word_never_defaulted(self):
        self.assertFalse(plan(100,Sample(clean_context=True)).complete)
    def test_context_contract_is_required(self):
        for clean in (None,False):self.assertFalse(plan(100,Sample(0x37f,clean)).complete)
    def test_reserved_precision_and_unmasked_exceptions_remain_gaps(self):
        self.assertFalse(plan(100,Sample(0x17f,True)).complete)
        self.assertFalse(plan(100,Sample(0x37e,True)).complete)
        self.assertFalse(plan(100,Sample(0x837f,True)).complete)
    def test_control_word_preserved_and_loaded_game_never_claimed(self):
        p=plan(100,Sample(0x137f,True))
        self.assertTrue(p.complete);self.assertEqual(p.restored_control_word,0x137f)
        self.assertFalse(p.loaded_game_runtime_verified)
    def test_raw_input_widths_and_types(self):
        with self.assertRaises(ValueError):Sample(control_word=True)
        with self.assertRaises(ValueError):plan(-1,Sample(0x37f,True))

if __name__=='__main__':unittest.main()
