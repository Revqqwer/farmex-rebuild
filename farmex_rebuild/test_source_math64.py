import random,unittest
from source_math64 import (MASK64,multiply64_bits,divide64_bits,session_ratio,
                          build_status_from_ratio)
from session_status_wire import FIELDS

def instruction_loop_oracle(n,d):
    # Independent restoring-division replay of SHL/RCL/CMP/SUB/INC/LOOP.
    sign=0
    if n>>63:n=(-n)&MASK64;sign^=1
    if d>>63:d=(-d)&MASK64;sign^=1
    remainder=0
    for _ in range(64):
        carry=n>>63;n=(n<<1)&MASK64
        remainder=((remainder<<1)|carry)&MASK64
        if remainder>=d:remainder-=d;n=(n+1)&MASK64
    return (-n if sign else n)&MASK64

class SourceMath64Tests(unittest.TestCase):
    def test_unsigned_multiply_low64(self):
        self.assertEqual(multiply64_bits(MASK64,100),MASK64-99)
        self.assertEqual(multiply64_bits(1<<63,100),0)
        self.assertEqual(multiply64_bits(0x123456789abcdef0,0),0)

    def test_signed_division_rounds_toward_zero(self):
        for n,d,q in ((7,3,2),(-7,3,-2),(7,-3,-2),(-7,-3,2)):
            p=divide64_bits(n&MASK64,d&MASK64)
            self.assertTrue(p.complete);self.assertEqual(p.qword,q&MASK64)
            self.assertEqual((p.edx<<32)|p.eax,p.qword)

    def test_software_min_over_minus_one_wraps_without_idiv_overflow(self):
        p=divide64_bits(1<<63,MASK64)
        self.assertTrue(p.complete);self.assertFalse(p.cpu_divide_error)
        self.assertEqual(p.qword,1<<63);self.assertEqual(p.path,'source_64_step_loop')

    def test_fast_path_and_high_numerator_path(self):
        self.assertEqual(divide64_bits(0xffffffff,2).eax,0x7fffffff)
        self.assertEqual(divide64_bits(0xffffffff,2).path,'source_DIV_EBX')
        p=divide64_bits(0x100000000,2)
        self.assertEqual(p.qword,0x80000000);self.assertEqual(p.path,'source_64_step_loop')

    def test_zero_divisor_faults_without_fabricated_result(self):
        for n in (0,1,0xffffffff,0x100000000,1<<63,MASK64):
            p=divide64_bits(n,0)
            self.assertFalse(p.complete);self.assertTrue(p.cpu_divide_error)
            self.assertIsNone(p.eax);self.assertIsNone(p.qword)
            self.assertFalse(p.exception_delivery_verified)

    def test_wide_operands_against_instruction_loop(self):
        rng=random.Random(0x503e75)
        for _ in range(400):
            n=rng.getrandbits(64);d=rng.getrandbits(64) or 1
            self.assertEqual(divide64_bits(n,d).qword,instruction_loop_oracle(n,d))

    def test_ratio_uses_wrapped_product_and_division_low_byte(self):
        p=session_ratio(MASK64,50)
        self.assertEqual(p.product_bits,MASK64-99)
        self.assertEqual(p.division.qword,MASK64-1)
        self.assertEqual(p.result_byte,254)
        self.assertEqual(session_ratio(1<<63,3).result_byte,0)
        self.assertEqual(session_ratio(1,3).result_byte,33)

    def test_ratio_composes_with_serialization_and_fault_blocks_it(self):
        values={k:0 for k in FIELDS if k!='ratio_division_eax'}
        ratio,wire=build_status_from_ratio(values,b'',numerator=1,denominator=3,
            entry_observed=True,transform_length_word=42)
        self.assertTrue(ratio.complete and wire.complete)
        self.assertEqual(wire.plain_frame[12],33)
        ratio,wire=build_status_from_ratio(values,b'',numerator=1,denominator=0,
            entry_observed=True,transform_length_word=42)
        self.assertFalse(ratio.complete);self.assertIsNone(wire)
        values['ratio_division_eax']=33
        with self.assertRaises(ValueError):
            build_status_from_ratio(values,b'',numerator=1,denominator=3)

    def test_raw_qword_validation(self):
        for value in (True,-1,1<<64,0.0):
            with self.assertRaises(ValueError):multiply64_bits(value,1)
            with self.assertRaises(ValueError):divide64_bits(1,value)
        self.assertFalse(divide64_bits(1,1).native_execution_verified)

if __name__=='__main__':unittest.main()
