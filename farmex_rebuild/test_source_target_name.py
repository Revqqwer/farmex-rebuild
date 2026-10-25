import unittest
from dataclasses import replace
from source_target_name import NameByIndexObservation as Obs,plan_name_by_index as plan,plan_target_id
from source_coin import SourceCoinObservation as IdObs,GuardedDwordSample as D

class TargetIdTests(unittest.TestCase):
    def test_root_plus_fresh_target_offset_full_dword(self):
        o=IdObs(((0x553e7c,0x100),(0x554044,0x44)),(D(0x100,1,0x1000),D(0x1044,1,0x10001)))
        p=plan_target_id(o);self.assertTrue(p.complete);self.assertEqual(p.target_id_dword,0x10001)
    def test_null_root_argument_still_reads_nonzero_offset_address(self):
        p=plan_target_id(IdObs(((0x553e7c,0),(0x554044,0x44)),(D(0x44,1,5),)))
        self.assertTrue(p.complete);self.assertEqual(p.target_id_dword,5);self.assertEqual(len(p.guarded_plans),2)
    def test_address_addition_wraps_and_null_final_argument_needs_no_api_sample(self):
        p=plan_target_id(IdObs(((0x553e7c,0x100),(0x554044,1)),(D(0x100,1,0xffffffff),)))
        self.assertTrue(p.complete);self.assertEqual(p.target_id_dword,0)
    def test_missing_target_observation_is_not_target0(self):
        p=plan_target_id(IdObs(((0x553e7c,0x100),(0x554044,0x44)),(D(0x100,1,0x1000),)))
        self.assertFalse(p.complete);self.assertIsNone(p.target_id_dword)

class NameByIndexTests(unittest.TestCase):
    def obs(self,length=3,**kw):
        values=dict(string_init_returned=True,lookup_pointer_dword=0x1000,lookup_returned=True,
            global_samples=((0x553fec,0x10),(0x553fe8,0x20)),guarded_samples=(D(0x1010,1,length),),
            name_span_returned=True,unicode_text='abc',ansi_output_span_returned=True,ansi_output_bytes=b'abc',fallback_span_returned=True)
        values.update(kw);return Obs(**values)
    def test_index_range_includes0_excludes3000_and_negative(self):
        for index in (0,2999):self.assertTrue(plan(index,self.obs()).complete)
        for index in (3000,0xffffffff,0x80000000):
            p=plan(index,Obs(string_init_returned=True,fallback_span_returned=True))
            self.assertTrue(p.complete);self.assertEqual(p.ansi_bytes,b'');self.assertIsNone(p.text_request)
    def test_inline_uses255_even_short_or_signed_negative_length(self):
        for length in (0,3,15,0xffffffff):
            p=plan(1,self.obs(length));self.assertTrue(p.complete)
            self.assertEqual((p.text_request.address,p.text_request.byte_count,p.text_request.indirect),(0x1020,255,False))
    def test_length_is_not_truncated_to_word_before_indirect_decision(self):
        p=plan(1,self.obs(0x10003,guarded_samples=(D(0x1010,1,0x10003),D(0x1020,1,0x2000))))
        self.assertTrue(p.complete);self.assertEqual(p.text_request.byte_count,0x10003);self.assertTrue(p.text_request.indirect)
    def test_null_lookup_fallback_but_unknown_lookup_not_empty_name(self):
        p=plan(1,self.obs(lookup_pointer_dword=0));self.assertTrue(p.complete);self.assertEqual(p.ansi_bytes,b'')
        self.assertFalse(plan(1,self.obs(lookup_pointer_dword=None)).complete)
    def test_init_and_fallback_cleanups_required_even_out_of_range(self):
        self.assertFalse(plan(3000,Obs(fallback_span_returned=True)).complete)
        self.assertFalse(plan(3000,Obs(string_init_returned=True)).complete)
    def test_reached_normal_returns_and_output_bytes_required(self):
        for field in ('lookup_returned','name_span_returned','ansi_output_span_returned','ansi_output_bytes'):
            self.assertFalse(plan(1,self.obs(**{field:None})).complete,field)
    def test_captured_inline_copy_and_missing_codec(self):
        kw=dict(use_captured_copy=True,unicode_text=None,readable=True,copied_bytes=b'abc\0'+b'\0'*251,copy_codec='cp1254')
        p=plan(1,self.obs(**kw));self.assertTrue(p.complete);self.assertEqual(p.unicode_text,'abc')
        kw['copy_codec']=None
        self.assertFalse(plan(1,self.obs(**kw)).complete)
    def test_indirect_oversized_copy_is_held_not_executed(self):
        p=plan(1,self.obs(513,guarded_samples=(D(0x1010,1,513),D(0x1020,1,0x2000)),
            use_captured_copy=True,unicode_text=None,readable=True,copied_bytes=b'x'*513,copy_codec='cp1254'))
        self.assertFalse(p.complete);self.assertIn('buffer_overflow',p.missing)
    def test_captured_copy_raw_conflict_only_reached(self):
        o=self.obs(use_captured_copy=True)
        with self.assertRaises(ValueError):plan(1,o)
        self.assertTrue(plan(3000,o).complete)
    def test_global_order_and_raw_types(self):
        with self.assertRaises(ValueError):plan(1,self.obs(global_samples=((0x553fe8,0x20),)))
        with self.assertRaises(ValueError):plan(True,self.obs())

if __name__=='__main__':unittest.main()
