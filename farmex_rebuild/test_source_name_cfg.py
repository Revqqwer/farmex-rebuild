import unittest
from source_name_cfg import NameCfgLoadObservation as Obs,plan_name_cfg_load as plan

class NameCfgLoadTests(unittest.TestCase):
    def obs(self,**kw):
        values=dict(path_copy_returned=True,clear_returned=True,fopen_returned=True,fopen_pointer_dword=0x1234,
            fclose_returned=True,probe_helper_returned=True,path_conversion_returned=True,load_returned=True,
            loaded_rows=('ABC','ABC',' İsim '),unicode_cleanup_returned=True,path_cleanup_returned=True)
        values.update(kw);return Obs(**values)
    def test_readable_load_preserves_order_duplicates_and_space(self):
        p=plan(('old',),self.obs());self.assertTrue(p.complete);self.assertEqual(p.state,('ABC','ABC',' İsim '));self.assertEqual(p.probe_al,1)
    def test_fopen_zero_is_unreadable_and_source_clears_first(self):
        p=plan(('old',),Obs(True,True,True,0,probe_helper_returned=True,path_cleanup_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.state,());self.assertEqual(p.probe_al,0)
        self.assertNotIn('_fclose',[s[0] for s in p.steps]);self.assertNotIn(('normal_return','TStrings.LoadFromFile virtual6c'),p.steps)
    def test_clear_precedes_probe_and_is_not_implied_by_it(self):
        p=plan(('old',),self.obs(clear_returned=None));self.assertFalse(p.complete);self.assertIsNone(p.prospective)
        self.assertNotIn(('_fopen','r'),p.steps)
    def test_unknown_open_pointer_is_not_missing_file(self):
        p=plan(('old',),self.obs(fopen_pointer_dword=None));self.assertFalse(p.complete);self.assertEqual(p.prospective,());self.assertIsNone(p.probe_al)
    def test_each_reached_receipt_and_load_contents_remain_explicit(self):
        for field in ('path_copy_returned','fopen_returned','fclose_returned','probe_helper_returned',
                      'path_conversion_returned','load_returned','loaded_rows','unicode_cleanup_returned','path_cleanup_returned'):
            p=plan(('old',),self.obs(**{field:None}));self.assertFalse(p.complete,field);self.assertEqual(p.state,('old',))
    def test_empty_successful_load_distinct_from_failed_probe(self):
        p=plan(('old',),self.obs(loaded_rows=()));self.assertTrue(p.complete);self.assertEqual(p.probe_al,1);self.assertEqual(p.state,())
    def test_load_then_cleanup_gap_keeps_known_prospective_rows(self):
        p=plan(('old',),self.obs(unicode_cleanup_returned=None));self.assertFalse(p.complete);self.assertEqual(p.prospective,('ABC','ABC',' İsim '))
    def test_types(self):
        with self.assertRaises(ValueError):Obs(fopen_pointer_dword=True)
        with self.assertRaises(ValueError):Obs(loaded_rows=[])
        with self.assertRaises(ValueError):plan(None,self.obs())

if __name__=='__main__':unittest.main()
