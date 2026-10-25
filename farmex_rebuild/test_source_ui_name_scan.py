import unittest
from dataclasses import replace
from source_ui_name_scan import UiNameScanRow as Row,UiNameScanObservation as Obs,plan_ui_name_scan as plan
from source_unicode import UnicodeEqualityObservation as Eq
from source_name_add import NameAddObservation as Add,plan_name_add

class UiNameScanTests(unittest.TestCase):
    def row(self,index=0,**kw):
        values=dict(count_dword=1,needle_conversion_returned=True,needle_unicode='ABC',item_getter_returned=True,
            item_unicode='ABC',equality=Eq(True,True,0xaabbcc00),temporary_cleanups_returned=True)
        values.update(kw);return Row(index,**values)
    def obs(self,*rows,**kw):
        values=dict(input_copy_returned=True,input_ansi_bytes=b'ABC',iterations=rows,input_cleanup_returned=True)
        values.update(kw);return Obs(**values)
    def test_empty_or_signed_negative_count_skips_conversion(self):
        for count in (0,0xffffffff,0x80000000):
            p=plan(self.obs(Row(0,count)));self.assertTrue(p.complete);self.assertEqual((p.al,p.eax_dword),(0,0));self.assertEqual(p.equality_plans,())
    def test_first_match_restores_full_eax_across_cleanups(self):
        p=plan(self.obs(self.row()));self.assertTrue(p.complete);self.assertEqual((p.match_index,p.al,p.eax_dword),(0,1,0xaabbcc01))
    def test_match_without_upper_observation_does_not_invent_eax1(self):
        p=plan(self.obs(self.row(equality=Eq(True,True))));self.assertTrue(p.complete);self.assertEqual(p.al,1);self.assertIsNone(p.eax_dword)
    def test_count_shrinks_fresh_after_nonmatch(self):
        p=plan(self.obs(self.row(count_dword=5,equality=Eq(True,False)),Row(1,1)))
        self.assertTrue(p.complete);self.assertEqual(p.al,0);self.assertEqual(len(p.equality_plans),1)
    def test_second_iteration_converts_needle_again(self):
        first=self.row(count_dword=2,item_unicode='other',equality=Eq(True,use_owned_text_model=True,left_text='ABC',right_text='other'))
        second=self.row(1,count_dword=2,needle_unicode='changed',item_unicode='changed',equality=Eq(True,use_owned_text_model=True,left_text='changed',right_text='changed'))
        p=plan(self.obs(first,second));self.assertTrue(p.complete);self.assertEqual(p.match_index,1)
        p=plan(self.obs(first,replace(second,needle_conversion_returned=None)));self.assertFalse(p.complete)
    def test_gaps_are_not_nonmatches(self):
        for field in ('count_dword','needle_conversion_returned','item_getter_returned','equality','temporary_cleanups_returned'):
            p=plan(self.obs(self.row(**{field:None})));self.assertFalse(p.complete,field);self.assertIsNone(p.al)
    def test_input_copy_and_both_exit_cleanups_required(self):
        self.assertFalse(plan(self.obs(Row(0,0),input_copy_returned=None)).complete)
        for row in (Row(0,0),self.row()):
            p=plan(self.obs(row,input_cleanup_returned=None));self.assertFalse(p.complete);self.assertIsNone(p.al)
    def test_prefix_exhaustion_is_not_end_of_ui_list(self):
        p=plan(self.obs(self.row(count_dword=2,equality=Eq(True,False))))
        self.assertFalse(p.complete);self.assertIn('index1',p.missing)
    def test_owned_equality_requires_exact_fresh_texts(self):
        row=self.row(equality=Eq(True,use_owned_text_model=True,left_text='wrong',right_text='ABC'))
        with self.assertRaises(ValueError):plan(self.obs(row))
        p=plan(self.obs(replace(row,count_dword=0)));self.assertTrue(p.complete)
    def test_unvisited_tail_not_consumed(self):
        p=plan(self.obs(self.row(),Row(99,0)));self.assertTrue(p.complete)
    def test_types_and_order(self):
        with self.assertRaises(ValueError):Row(True,0)
        with self.assertRaises(ValueError):Obs(iterations=[])
        with self.assertRaises(ValueError):plan(self.obs(Row(1,0)))

class UiNameScanAddBindingTests(unittest.TestCase):
    def scan(self,match=True):
        fixture=UiNameScanTests()
        rows=(fixture.row(),) if match else (Row(0,0),)
        return plan(fixture.obs(*rows))
    def add(self,p,**kw):
        values=dict(nonempty_span_returned=True,nonempty_al=1,duplicate_span_returned=True,
            duplicate_execution=p,duplicate_input_ansi=b'ABC',append_getter_returned=True,append_text='third',
            append_cleanup_span_returned=True,refresh_returned=True)
        values.update(kw);return plan_name_add('white',(),Add(**values))
    def test_match_skips_append_and_empty_scan_allows_fresh_third_text(self):
        p=self.add(self.scan());self.assertTrue(p.complete);self.assertEqual(p.state,());self.assertEqual(p.status,'duplicate_skipped')
        p=self.add(self.scan(False),append_text='');self.assertTrue(p.complete);self.assertEqual(p.state,('',))
    def test_full_scan_still_requires_independent_caller_span(self):
        p=self.add(self.scan(),duplicate_span_returned=None);self.assertFalse(p.complete);self.assertIsNone(p.duplicate_execution)
    def test_incomplete_scan_or_unknown_second_ansi_holds(self):
        fixture=UiNameScanTests();partial=plan(fixture.obs())
        self.assertFalse(self.add(partial).complete)
        self.assertFalse(self.add(self.scan(),duplicate_input_ansi=None).complete)
    def test_raw_al_and_identity_conflicts_only_reached(self):
        with self.assertRaises(ValueError):self.add(self.scan(),duplicate_al=1)
        with self.assertRaises(ValueError):self.add(self.scan(),duplicate_input_ansi=b'other')
        p=self.add(self.scan(),nonempty_al=0,duplicate_al=1)
        self.assertTrue(p.complete);self.assertIsNone(p.duplicate_execution)

if __name__=='__main__':unittest.main()
