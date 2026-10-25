import unittest
from dataclasses import replace
from quest_name_compare import AnsiCompareSample as Sample,QuestNameCompareObservation as Observation,QuestNameCompareFrame


def capture(greater=None,less=None):
    return Observation(greater,less,{role:True for role in ('greater_compare','greater_return','less_compare','less_return','compare_return','equal_return')})


def owned(left,right):return Sample(use_owned_bytes=True,left_bytes=left,right_bytes=right)


class QuestNameCompareTests(unittest.TestCase):
    def test_seta_path_skips_the_second_comparison(self):
        p=QuestNameCompareFrame().advance(capture(Sample(False,False),object()))
        self.assertEqual((p.complete,p.eax,p.compare_eax),(True,0,1))
        self.assertNotIn('less_compare',[label for label,_ in p.calls])

    def test_carry_in_first_comparison_does_not_require_zf(self):
        p=QuestNameCompareFrame().advance(capture(Sample(True),Sample(True)))
        self.assertEqual((p.eax,p.compare_eax),(0,0xffffffff))

    def test_equal_result_is_clean_dword_one(self):
        p=QuestNameCompareFrame().advance(capture(Sample(False,True),Sample(False)))
        self.assertEqual((p.eax,p.compare_eax),(1,0))

    def test_second_comparison_is_fresh_not_reused_first_flags(self):
        p=QuestNameCompareFrame().advance(capture(Sample(True),Sample(False)))
        self.assertEqual((p.eax,p.compare_eax),(1,0))
        p=QuestNameCompareFrame().advance(capture(Sample(False,True),Sample(True)))
        self.assertEqual((p.eax,p.compare_eax),(0,0xffffffff))

    def test_missing_first_flags_does_not_become_false(self):
        f=QuestNameCompareFrame();p=f.advance(capture(Sample()))
        self.assertEqual(p.needed,('flag','greater_CF'));self.assertIsNone(p.eax)
        p=f.advance(capture(Sample(False)))
        self.assertEqual(p.needed,('flag','greater_ZF'))

    def test_less_does_not_consume_unused_zf(self):
        p=QuestNameCompareFrame().advance(capture(Sample(True),Sample(False,object())))
        self.assertEqual(p.eax,1)

    def test_missing_less_sample_is_not_assumed_equal(self):
        p=QuestNameCompareFrame().advance(capture(Sample(True)))
        self.assertEqual(p.needed,('sample','less'));self.assertIsNone(p.eax)

    def test_helper_return_gap_precedes_flag_use(self):
        f=QuestNameCompareFrame();o=capture(Sample(False,False));normal=dict(o.normal_returns)
        normal['greater_compare']=False
        p=f.advance(replace(o,normal_returns=normal,greater=Sample(object(),object())))
        self.assertEqual(p.needed,('normal','greater_compare'))
        self.assertEqual(f.advance(o).eax,0)

    def test_wrapper_return_gap_freezes_consumed_flags(self):
        f=QuestNameCompareFrame();o=capture(Sample(False,False));normal=dict(o.normal_returns)
        normal['greater_return']=False
        p=f.advance(replace(o,normal_returns=normal));self.assertIsNone(p.eax)
        p=f.advance(capture(Sample(True),Sample(False)))
        self.assertEqual((p.eax,p.compare_eax),(0,1))
        self.assertEqual(len(p.comparisons),1)

    def test_final_wrappers_require_separate_returns(self):
        for role in ('compare_return','equal_return'):
            f=QuestNameCompareFrame();o=capture(Sample(False,True),Sample(False));normal=dict(o.normal_returns);del normal[role]
            p=f.advance(replace(o,normal_returns=normal))
            self.assertIsNone(p.eax);self.assertEqual(p.needed,('normal',role))
            p=f.advance(o);self.assertEqual(p.eax,1)
            self.assertEqual(len(p.calls),len({label for label,_ in p.calls}))
            self.assertIs(f.advance(),p)

    def test_owned_unsigned_bytes_handle_prefix_empty_and_high_bytes(self):
        for left,right,expected in ((b'',b'',1),(b'',b'a',0),(b'ab',b'abc',0),(b'\xff',b'\x80',0),(b'\x80',b'\x80',1)):
            p=QuestNameCompareFrame().advance(capture(owned(left,right),owned(left,right)))
            self.assertEqual(p.eax,expected)
            self.assertFalse(p.native_execution_verified)

    def test_owned_ansi_data_preserves_embedded_nul_and_exact_case(self):
        for left,right,expected in ((b'a\0b',b'a\0c',0),(b'A',b'a',0),(b'\xdd',b'I',0),(b'a\0b',b'a\0b',1)):
            p=QuestNameCompareFrame().advance(capture(owned(left,right),owned(left,right)))
            self.assertEqual(p.eax,expected)

    def test_owned_second_call_uses_its_own_operand_snapshot(self):
        p=QuestNameCompareFrame().advance(capture(owned(b'a',b'b'),owned(b'c',b'b')))
        self.assertEqual(p.eax,1)
        self.assertEqual(p.comparisons[0][-2:],(b'a',b'b'))
        self.assertEqual(p.comparisons[1][-2:],(b'c',b'b'))

    def test_owned_model_cannot_mix_captured_flags(self):
        with self.assertRaises(ValueError):QuestNameCompareFrame().advance(capture(Sample(False,use_owned_bytes=True,left_bytes=b'a',right_bytes=b'a')))

    def test_owned_bytes_must_be_explicit_immutable_and_complete(self):
        p=QuestNameCompareFrame().advance(capture(Sample(use_owned_bytes=True,left_bytes=b'a')))
        self.assertEqual(p.needed,('bytes','greater'))
        with self.assertRaises(ValueError):QuestNameCompareFrame().advance(capture(Sample(use_owned_bytes=True,left_bytes=bytearray(b'a'),right_bytes=b'a')))

    def test_partial_flags_and_policy_are_frozen_for_the_same_compare_call(self):
        f=QuestNameCompareFrame();p=f.advance(capture(Sample(False)))
        self.assertEqual(p.needed,('flag','greater_ZF'))
        with self.assertRaises(ValueError):f.advance(capture(owned(b'z',b'a')))
        p=f.advance(capture(Sample(True,False)))
        self.assertEqual((p.eax,p.compare_eax),(0,1))

    def test_partial_owned_operands_preserve_the_consumed_left_side(self):
        f=QuestNameCompareFrame();p=f.advance(capture(Sample(use_owned_bytes=True,left_bytes=b'z')))
        self.assertEqual(p.needed,('bytes','greater'))
        p=f.advance(capture(owned(b'a',b'b')))
        self.assertEqual((p.eax,p.compare_eax),(0,1))
        self.assertEqual(p.comparisons[0][-2:],(b'z',b'b'))


if __name__=='__main__':unittest.main()
