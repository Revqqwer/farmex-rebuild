import unittest
from source_name_add import NameAddObservation as Obs,plan_name_add as plan
import test_source_name_lists as refresh_fixture

class NameAddTests(unittest.TestCase):
    def obs(self,**kw):
        values=dict(nonempty_span_returned=True,nonempty_al=1,duplicate_span_returned=True,duplicate_al=0,
            append_getter_returned=True,append_text='third read',append_cleanup_span_returned=True,refresh_returned=True)
        values.update(kw);return Obs(**values)
    def test_empty_and_duplicate_skip_unreached_getters_refresh(self):
        for o in (Obs(True,0),Obs(True,1,True,1)):
            p=plan('white',('old',),o);self.assertTrue(p.complete);self.assertEqual(p.state,('old',));self.assertIsNone(p.refresh_execution)
    def test_append_uses_fresh_third_getter_even_empty_or_duplicate(self):
        for text in ('','old',' ABC '):
            p=plan('black',('old',),self.obs(append_text=text));self.assertTrue(p.complete);self.assertEqual(p.state,('old',text))
    def test_normal_spans_not_implied_by_al_or_text(self):
        for field in ('nonempty_span_returned','nonempty_al','duplicate_span_returned','duplicate_al',
                      'append_getter_returned','append_text','append_cleanup_span_returned','refresh_returned'):
            p=plan('white',('old',),self.obs(**{field:None}));self.assertFalse(p.complete,field);self.assertEqual(p.state,p.entry)
    def test_append_survives_as_prospective_on_refresh_gap(self):
        p=plan('white',(),self.obs(refresh_returned=None));self.assertFalse(p.complete);self.assertEqual(p.prospective,('third read',))
    def test_bound_refresh_needs_complete_and_separate_return(self):
        fixture=refresh_fixture.NameListRefreshTests();full=fixture.runplan();partial=fixture.runplan(final_cleanup_returned=None)
        self.assertTrue(plan('white',(),self.obs(refresh_execution=full)).complete)
        self.assertFalse(plan('white',(),self.obs(refresh_execution=full,refresh_returned=None)).complete)
        self.assertFalse(plan('white',(),self.obs(refresh_execution=partial)).complete)
        p=plan('white',(),self.obs(nonempty_al=0,refresh_execution=partial));self.assertTrue(p.complete);self.assertIsNone(p.refresh_execution)
    def test_source_boolean_and_rows_types(self):
        with self.assertRaises(ValueError):Obs(nonempty_al=True)
        with self.assertRaises(ValueError):Obs(duplicate_al=7)
        with self.assertRaises(ValueError):plan('x',(),self.obs())

if __name__=='__main__':unittest.main()
