import unittest
from dataclasses import replace
from source_name_lists import (NameListsState as State,NameListRefreshRow as Row,NameListRefreshObservation as Obs,
    plan_name_list_refresh as plan,filter_refreshed_names)
from source_name_filter import NameFilterIteration as FilterRow,NameFilterObservation as FilterObs
from source_unicode import UnicodeEqualityObservation as Eq

class NameListRefreshTests(unittest.TestCase):
    def row(self,index=0,**kw):
        values=dict(ui_count_dword=1,text_get_returned=True,unicode_text='ABC',ansi_conversion_returned=True,
            ansi_bytes=b'ABC',assignment_cleanup_returned=True,vector_size_dword=0,vector_capacity_dword=4,
            insertion_returned=True,fast_end_dword=0x2004)
        values.update(kw);return Row(index,**values)
    def obs(self,**kw):
        values=dict(scratch_init_returned=True,black_reset_returned=True,white_reset_returned=True,
            black_after_reset=(),white_after_reset=(),black_rows=(Row(0,0),),white_rows=(Row(0,0),),final_cleanup_returned=True)
        values.update(kw);return Obs(**values)
    def runplan(self,**kw):return plan(State((b'oldW',),(b'oldB',)),self.obs(**kw))
    def test_empty_ui_lists_still_reset_both_before_count(self):
        p=self.runplan();self.assertTrue(p.complete);self.assertEqual(p.state,State())
        self.assertEqual([s[1] for s in p.steps[:3]],['00404148 ANSI scratch initialization','context100 end/begin/erase span','contexte0 end/begin/erase span'])
    def test_reset_return_does_not_prove_empty_contents(self):
        p=self.runplan(black_after_reset=None);self.assertFalse(p.complete);self.assertIsNone(p.prospective_black)
        self.assertEqual(p.state,p.entry)
        p=self.runplan(black_after_reset=(b'residual',));self.assertTrue(p.complete);self.assertEqual(p.state.black,(b'residual',))
    def test_black_then_white_order_duplicates_and_ansi_bytes_preserved(self):
        rows=(self.row(0,ui_count_dword=2),self.row(1,ui_count_dword=2,ansi_bytes=b'ABC\0x'),Row(2,2))
        p=self.runplan(black_rows=rows,white_rows=(self.row(0,ansi_bytes=b'ABC'),Row(1,1)))
        self.assertTrue(p.complete);self.assertEqual(p.state.black,(b'ABC',b'ABC\0x'));self.assertEqual(p.state.white,(b'ABC',))
        self.assertEqual([s[1] for s in p.steps if s[0]=='vector_insert'],['black','black','white'])
    def test_signed_negative_ui_count_skips_body(self):
        p=self.runplan(black_rows=(Row(0,0xffffffff),));self.assertTrue(p.complete);self.assertEqual(p.state.black,())
    def test_ui_count_is_fresh_not_initial_bound(self):
        p=self.runplan(black_rows=(self.row(ui_count_dword=9),Row(1,1)))
        self.assertTrue(p.complete);self.assertEqual(p.state.black,(b'ABC',))
    def test_fast_vs_slow_uses_unsigned_size_capacity(self):
        p=self.runplan(black_rows=(self.row(vector_size_dword=0xffffffff,vector_capacity_dword=0,fast_end_dword=None),Row(1,1)))
        self.assertTrue(p.complete);self.assertEqual(p.writes,());self.assertIn('0040a01c',[s[4] for s in p.steps if s[0]=='vector_insert'])
        p=self.runplan(black_rows=(self.row(),Row(1,1)))
        self.assertEqual(p.writes,(('black',0x114,0x2004),))
    def test_reached_row_gaps_do_not_become_empty_string_or_insert(self):
        for field in ('ui_count_dword','text_get_returned','ansi_conversion_returned','ansi_bytes',
                      'assignment_cleanup_returned','vector_size_dword','vector_capacity_dword','insertion_returned','fast_end_dword'):
            p=self.runplan(black_rows=(self.row(**{field:None}),Row(1,1)))
            self.assertFalse(p.complete,field);self.assertEqual(p.state,p.entry);self.assertEqual(p.prospective_black,())
    def test_final_cleanup_missing_keeps_own_trial_only(self):
        p=self.runplan(black_rows=(self.row(),Row(1,1)),final_cleanup_returned=None)
        self.assertFalse(p.complete);self.assertEqual(p.prospective_black,(b'ABC',));self.assertEqual(p.state,p.entry)
    def test_black_gap_prevents_white_reads(self):
        p=self.runplan(black_rows=(),white_rows=(self.row(),))
        self.assertFalse(p.complete);self.assertFalse(any(s[0]=='UI_count' and s[1]=='white' for s in p.steps))
    def test_order_and_types(self):
        with self.assertRaises(ValueError):self.runplan(black_rows=(Row(1,0),))
        with self.assertRaises(ValueError):Row(0,True)
        with self.assertRaises(ValueError):State(['abc'],())
        with self.assertRaises(ValueError):Obs(black_after_reset=(None,))

class RefreshedFilterBridgeTests(unittest.TestCase):
    def refresh(self,white=(b'ABC',),black=(b'other',)):
        return NameListRefreshTests().runplan(white_after_reset=white,black_after_reset=black)
    def observation(self,text='ABC',**kw):
        eq=Eq(True,use_owned_text_model=True)
        row=FilterRow(0,0x1000,0x1004,0x2000,True,equality=eq,temporary_cleanup_returned=True)
        values=dict(input_copy_returned=True,input_text=text,iterations=(row,FilterRow(1,0x1000,0x1004)),input_cleanup_returned=True)
        values.update(kw);return FilterObs(**values)
    def bridge(self,refresh=None,kind='primary',o=None,**kw):
        values=dict(stable_same_invocation=True,codec='cp1254');values.update(kw)
        return filter_refreshed_names(refresh or self.refresh(),kind,o or self.observation(),**values)
    def test_white_primary_black_secondary_and_case_preserved(self):
        self.assertEqual(self.bridge().al,1)
        self.assertEqual(self.bridge(kind='secondary').al,0)
        self.assertEqual(self.bridge(o=self.observation('abc')).al,0)
    def test_explicit_stability_codec_and_complete_refresh_required(self):
        with self.assertRaises(ValueError):self.bridge(stable_same_invocation=False)
        with self.assertRaises(ValueError):self.bridge(codec=None)
        with self.assertRaises(ValueError):self.bridge(refresh=NameListRefreshTests().runplan(final_cleanup_returned=None))
    def test_count_conversion_and_owned_text_conflicts_rejected(self):
        o=self.observation();row=o.iterations[0]
        for modified in (replace(row,count_end_dword=0x1008),replace(row,converted_text='wrong'),
                         replace(row,equality=Eq(True,use_owned_text_model=True,left_text='wrong'))):
            with self.assertRaises(ValueError):self.bridge(o=replace(o,iterations=(modified,)))
    def test_bridge_does_not_fill_source_helper_receipts(self):
        o=self.observation();row=o.iterations[0]
        for row in (replace(row,conversion_returned=None),replace(row,equality=Eq(None,use_owned_text_model=True)),
                    replace(row,temporary_cleanup_returned=None)):
            self.assertFalse(self.bridge(o=replace(o,iterations=(row,))).complete)
        self.assertFalse(self.bridge(o=replace(o,input_copy_returned=None)).complete)
    def test_unvisited_tail_conflicts_and_invalid_codec_bytes_ignored(self):
        o=self.observation();bad=replace(o.iterations[1],count_end_dword=0x9999,converted_text='bad')
        self.assertTrue(self.bridge(o=replace(o,iterations=(o.iterations[0],bad))).complete)
        r=self.refresh(white=(b'\xff',));row=replace(o.iterations[0],conversion_returned=None)
        self.assertFalse(self.bridge(refresh=r,o=replace(o,iterations=(row,)),codec='ascii').complete)
    def test_embedded_nul_preserved_not_pchar_truncated(self):
        r=self.refresh(white=(b'A\0B',));self.assertEqual(self.bridge(refresh=r,o=self.observation('A\0B')).al,1)

if __name__=='__main__':unittest.main()
