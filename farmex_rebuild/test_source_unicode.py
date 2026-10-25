import unittest
from source_unicode import UnicodeEqualityObservation as Obs,plan_unicode_equality as plan,utf16_key

class SourceUnicodeTests(unittest.TestCase):
    def test_setz_only_changes_al_and_preserves_unknown_upper_bits(self):
        for zf,al in ((True,1),(False,0)):
            p=plan(Obs(True,zf,0xabcdef55));self.assertTrue(p.complete)
            self.assertEqual(p.al,al);self.assertEqual(p.eax_dword,0xabcdef00|al)
            p=plan(Obs(True,zf));self.assertTrue(p.complete);self.assertIsNone(p.eax_dword)
    def test_missing_normal_return_or_flags_is_not_false_comparison(self):
        for o in (Obs(),Obs(zero_flag=True),Obs(True)):
            p=plan(o);self.assertFalse(p.complete);self.assertIsNone(p.al)
    def test_texts_do_not_implicitly_select_owned_model(self):
        p=plan(Obs(True,left_text='Town',right_text='Town'))
        self.assertFalse(p.complete);self.assertIn('zero flag',p.missing)
    def test_owned_model_is_explicit_and_missing_text_is_not_empty(self):
        p=plan(Obs(True,use_owned_text_model=True,left_text='',right_text=''))
        self.assertTrue(p.complete);self.assertEqual(p.al,1);self.assertEqual(p.provenance,'owned_utf16_model')
        p=plan(Obs(True,use_owned_text_model=True,left_text=None,right_text=''))
        self.assertFalse(p.complete);self.assertIsNone(p.al)
        self.assertFalse(p.native_runtime_verified)
    def test_exact_code_units_case_spaces_normalization_and_nuls(self):
        for a,b,equal in (('Town','town',False),('Town','Town ',False),('İ','I',False),
                          ('é','e\u0301',False),('A\0B','A',False),('A\0B','A\0B',True)):
            p=plan(Obs(True,use_owned_text_model=True,left_text=a,right_text=b))
            self.assertEqual(p.al,1 if equal else 0)
    def test_python_scalar_and_surrogate_pair_have_equal_utf16(self):
        p=plan(Obs(True,use_owned_text_model=True,left_text='\U0001f600',right_text='\ud83d\ude00'))
        self.assertEqual(p.al,1);self.assertEqual(utf16_key('\ud800'),b'\0\xd8')
    def test_owned_model_and_observed_flag_conflict(self):
        with self.assertRaises(ValueError):plan(Obs(True,True,use_owned_text_model=True,left_text='x',right_text='x'))
    def test_types(self):
        for kw in (dict(helper_returned=1),dict(zero_flag=0),dict(post_helper_eax_dword=-1),dict(use_owned_text_model=1),dict(left_text=b'Town')):
            with self.assertRaises(ValueError):Obs(**kw)

if __name__=='__main__':unittest.main()
