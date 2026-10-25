import unittest
from dataclasses import replace
from source_target_add import TargetAddObservation as Obs,plan_target_add as plan
from source_target_name import plan_target_id,plan_name_by_index,NameByIndexObservation
from source_coin import SourceCoinObservation,GuardedDwordSample
from source_ui_name_scan import UiNameScanObservation,UiNameScanRow,plan_ui_name_scan
import test_source_name_lists as refresh_fixture

class TargetAddTests(unittest.TestCase):
    def obs(self,**kw):
        values=dict(target_ids=(1,2,3),name_ansi_bytes=b'ABC',name_returned=True,duplicate_al=0,
            duplicate_returned=True,append_unicode_text='ABC',append_span_returned=True,
            refresh_returned=True,name_cleanup_returned=True)
        values.update(kw);return Obs(**values)
    def runplan(self,**kw):return plan('white',('old',),self.obs(**kw))
    def id_plan(self,value):
        return plan_target_id(SourceCoinObservation(((0x553e7c,0x100),(0x554044,0x44)),
            (GuardedDwordSample(0x100,1,0x1000),GuardedDwordSample(0x1044,1,value))))
    def empty_name(self,index):return plan_name_by_index(index,NameByIndexObservation(string_init_returned=True,fallback_span_returned=True))
    def scan_empty_list(self,ansi=b''):
        return plan_ui_name_scan(UiNameScanObservation(True,ansi,(UiNameScanRow(0,0),),True))
    def test_first_zero_alert_short_circuits_other_samples(self):
        p=plan('white',('old',),Obs(target_ids=(0,),invalid_alert_span_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.target_samples,(0,));self.assertEqual(p.state,('old',));self.assertEqual(p.status,'invalid_target_no_add')
    def test_invalid_notice_requires_normal_span_return(self):
        p=plan('black',(),Obs(target_ids=(0,)));self.assertFalse(p.complete);self.assertIn('notice',p.missing)
    def test_second_unsigned_limit_invalidates3001_and_negative_dword(self):
        for second in (3001,0xffffffff):
            p=self.runplan(target_ids=(1,second),invalid_alert_span_returned=True)
            self.assertTrue(p.complete);self.assertEqual(p.status,'invalid_target_no_add');self.assertEqual(len(p.target_samples),2)
    def test_first_test_is_only_nonzero_not_signed_positive(self):
        p=self.runplan(target_ids=(0xffffffff,0,3));self.assertTrue(p.complete);self.assertEqual(p.target_samples,(0xffffffff,0,3))
    def test_three_target_reads_remain_independent(self):
        p=self.runplan();self.assertTrue(p.complete);self.assertEqual(p.target_samples,(1,2,3))
        self.assertIn(('00466144',3),p.steps);self.assertEqual(p.state,('old','ABC'))
    def test_second3000_allowed_and_third3000_empty_name_can_be_added(self):
        p=self.runplan(target_ids=(1,3000,3000),name_ansi_bytes=None,name_execution=self.empty_name(3000),
            duplicate_al=None,duplicate_execution=self.scan_empty_list(),append_unicode_text='')
        self.assertTrue(p.complete);self.assertEqual(p.state,('old',''));self.assertEqual(p.name_plan.status,'empty_fallback')
    def test_third_negative_can_follow_valid_first_second(self):
        p=self.runplan(target_ids=(1,0,0xffffffff),name_ansi_bytes=None,name_execution=self.empty_name(0xffffffff),append_unicode_text='')
        self.assertTrue(p.complete);self.assertEqual(p.state,('old',''))
    def test_missing_fresh_target_samples_are_not_reused(self):
        for ids in ((),(1,),(1,2)):
            p=self.runplan(target_ids=ids);self.assertFalse(p.complete);self.assertEqual(p.state,p.entry)
    def test_bound_target_readers_need_separate_normal_returns(self):
        bound=tuple(self.id_plan(i) for i in (1,2,3))
        p=self.runplan(target_ids=(),target_id_executions=bound,target_id_returned=(True,True,True))
        self.assertTrue(p.complete);self.assertEqual(len(p.target_plans),3)
        p=self.runplan(target_ids=(),target_id_executions=bound,target_id_returned=(True,))
        self.assertFalse(p.complete);self.assertEqual(p.target_samples,(1,))
    def test_partial_bound_target_reader_does_not_become_zero(self):
        partial=plan_target_id(SourceCoinObservation())
        p=self.runplan(target_ids=(),target_id_executions=(partial,),target_id_returned=(True,))
        self.assertFalse(p.complete);self.assertEqual(p.target_samples,())
    def test_bound_name_metadata_and_raw_conflicts(self):
        with self.assertRaises(ValueError):self.runplan(name_execution=self.empty_name(3000))
        with self.assertRaises(ValueError):self.runplan(name_ansi_bytes=None,name_execution=self.empty_name(3000))
        p=self.runplan(target_ids=(0,),invalid_alert_span_returned=True,name_execution=self.empty_name(3000))
        self.assertTrue(p.complete);self.assertIsNone(p.name_plan)
    def test_bound_duplicate_uses_exact_name_output_and_still_needs_return(self):
        scan=self.scan_empty_list(b'ABC')
        p=self.runplan(duplicate_al=None,duplicate_execution=scan);self.assertTrue(p.complete)
        self.assertFalse(self.runplan(duplicate_al=None,duplicate_execution=scan,duplicate_returned=None).complete)
        with self.assertRaises(ValueError):self.runplan(duplicate_execution=scan)
        with self.assertRaises(ValueError):self.runplan(duplicate_al=None,duplicate_execution=self.scan_empty_list(b'other'))
    def test_duplicate_skips_append_refresh_but_requires_final_name_cleanup(self):
        p=plan('black',(),Obs(target_ids=(1,2,3),name_ansi_bytes=b'ABC',name_returned=True,
            duplicate_al=1,duplicate_returned=True,name_cleanup_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.state,());self.assertIsNone(p.refresh_plan)
        self.assertFalse(self.runplan(duplicate_al=1,name_cleanup_returned=None).complete)
    def test_reached_source_spans_remain_required(self):
        for key in ('name_returned','name_ansi_bytes','duplicate_al','duplicate_returned','append_unicode_text',
                    'append_span_returned','refresh_returned','name_cleanup_returned'):
            p=self.runplan(**{key:None});self.assertFalse(p.complete,key);self.assertEqual(p.state,p.entry)
    def test_append_keeps_own_prospective_on_late_gap(self):
        p=self.runplan(refresh_returned=None);self.assertFalse(p.complete);self.assertEqual(p.prospective,('old','ABC'))
        p=self.runplan(name_cleanup_returned=None);self.assertFalse(p.complete);self.assertEqual(p.prospective,('old','ABC'))
    def test_bound_refresh_complete_not_equal_independent_return(self):
        fixture=refresh_fixture.NameListRefreshTests();full=fixture.runplan();partial=fixture.runplan(final_cleanup_returned=None)
        self.assertTrue(self.runplan(refresh_execution=full).complete)
        self.assertFalse(self.runplan(refresh_execution=full,refresh_returned=None).complete)
        self.assertFalse(self.runplan(refresh_execution=partial).complete)
    def test_white_and_black_rows_and_input_types(self):
        p=plan('black',('B',),self.obs());self.assertEqual(p.state,('B','ABC'));self.assertEqual(p.kind,'black')
        with self.assertRaises(ValueError):Obs(target_ids=[1])
        with self.assertRaises(ValueError):Obs(target_ids=(True,))
        with self.assertRaises(ValueError):self.runplan(target_id_executions=(self.id_plan(1),))
    def test_all_bound_chain_keeps3000_empty_name_through_vector_refresh(self):
        fixture=refresh_fixture.NameListRefreshTests()
        refresh=fixture.runplan(white_rows=(fixture.row(0,unicode_text='',ansi_bytes=b''),refresh_fixture.Row(1,1)))
        readers=tuple(self.id_plan(v) for v in (1,3000,3000))
        p=plan('white',(),self.obs(target_ids=(),target_id_executions=readers,target_id_returned=(True,True,True),
            name_ansi_bytes=None,name_execution=self.empty_name(3000),duplicate_al=None,
            duplicate_execution=self.scan_empty_list(),append_unicode_text='',refresh_execution=refresh))
        self.assertTrue(p.complete);self.assertEqual(p.state,('',));self.assertEqual(p.refresh_plan.state.white,(b'',))
        self.assertFalse(p.native_execution_verified)

if __name__=='__main__':unittest.main()
