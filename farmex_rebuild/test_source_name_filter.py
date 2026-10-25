import unittest
from dataclasses import replace
from source_name_filter import NameFilterIteration as Row,NameFilterObservation as Obs,plan_name_filter as plan,source_vector_count
from source_unicode import UnicodeEqualityObservation as Eq
import test_route_query as query_fixture
from route_query import plan_route_query

class NameFilterTests(unittest.TestCase):
    def row(self,index=0,match=False,**kw):
        values=dict(count_begin_dword=0x1000,count_end_dword=0x1004,slot_base_dword=0x2000,
                    conversion_returned=True,converted_text='abc' if match else 'other',
                    equality=Eq(True,match),temporary_cleanup_returned=True)
        values.update(kw);return Row(index,**values)
    def obs(self,*rows,**kw):
        values=dict(input_copy_returned=True,input_text='abc',iterations=rows,input_cleanup_returned=True)
        values.update(kw);return Obs(**values)
    def empty(self,kind='primary',**kw):return plan(kind,self.obs(Row(0,0),**kw))
    def test_empty_null_begin_does_not_need_end_or_slot(self):
        p=self.empty();self.assertTrue(p.complete);self.assertEqual((p.al,p.eax_dword),(0,0));self.assertEqual(p.equality_plans,())
    def test_begin_nonzero_equal_end_is_empty(self):
        p=plan('primary',self.obs(Row(0,0x1000,0x1000)));self.assertTrue(p.complete);self.assertEqual(p.al,0)
    def test_first_match_skips_next_count_and_full_eax_unknown(self):
        p=plan('primary',self.obs(self.row(match=True)))
        self.assertTrue(p.complete);self.assertEqual((p.al,p.match_index,p.eax_dword),(1,0,None))
    def test_count_is_fresh_can_shrink_after_nonmatch(self):
        p=plan('primary',self.obs(self.row(count_end_dword=0x100c),Row(1,0)))
        self.assertTrue(p.complete);self.assertEqual(p.al,0);self.assertEqual(len(p.equality_plans),1)
    def test_count_can_grow_and_slot_base_is_independent(self):
        p=plan('secondary',self.obs(self.row(),self.row(1,True,count_end_dword=0x1008,slot_base_dword=0xfffffffe)))
        self.assertTrue(p.complete);self.assertEqual(p.match_index,1)
        slots=[s for s in p.steps if s[0]=='slot_conversion']
        self.assertEqual(slots[-1],('slot_conversion',1,0x110,0xfffffffe,2))
    def test_negative_delta_rounds_toward_zero_then_unsigned_comparison(self):
        for delta,count in ((-1,0),(-3,0),(-4,0xffffffff),(-5,0xffffffff),(-8,0xfffffffe),(3,0),(7,1)):
            self.assertEqual(source_vector_count(0x1000,(0x1000+delta)&0xffffffff),count)
        p=plan('primary',self.obs(self.row(count_end_dword=0xffc)))
        self.assertFalse(p.complete);self.assertIn('index1',p.missing)
    def test_subtraction_wrap_and_sign_boundary(self):
        self.assertEqual(source_vector_count(0xfffffffc,4),2)
        self.assertEqual(source_vector_count(1,0x80000001),0xe0000000)
    def test_missing_init_does_not_assume_empty(self):
        p=self.empty(input_copy_returned=None);self.assertFalse(p.complete);self.assertEqual(p.steps[0][0],'normal_return')
    def test_missing_count_or_end_does_not_mean_zero(self):
        for row in (Row(0),Row(0,0x1000)):
            p=plan('primary',self.obs(row));self.assertFalse(p.complete);self.assertIsNone(p.al)
    def test_reached_helpers_need_independent_receipts(self):
        for kw in (dict(slot_base_dword=None),dict(conversion_returned=None),dict(equality=None),dict(temporary_cleanup_returned=None)):
            p=plan('primary',self.obs(self.row(match=True,**kw)));self.assertFalse(p.complete);self.assertIsNone(p.al)
        p=plan('primary',self.obs(self.row(match=True),input_cleanup_returned=None))
        self.assertFalse(p.complete);self.assertEqual(p.match_index,0);self.assertIsNone(p.al)
    def test_empty_still_requires_final_cleanup(self):
        self.assertFalse(self.empty(input_cleanup_returned=False).complete)
    def test_comparison_saved_across_cleanup_and_requires_its_normal_return(self):
        row=self.row(match=True,equality=Eq(True,True,0xaabbcc00))
        p=plan('primary',self.obs(row));self.assertTrue(p.complete);self.assertEqual(p.equality_plans[0][1].eax_dword,0xaabbcc01)
        p=plan('primary',self.obs(replace(row,equality=Eq(None,True))))
        self.assertFalse(p.complete);self.assertNotIn(('saved_comparison_al',0,1),p.steps)
    def test_owned_equality_explicit_utf16_no_lowercase_or_normalization(self):
        def run(left,right):
            eq=Eq(True,use_owned_text_model=True,left_text=left,right_text=right)
            row=self.row(converted_text=right,equality=eq)
            return plan('primary',self.obs(row,Row(1,0),input_text=left))
        self.assertEqual(run('abc','abc').al,1)
        self.assertEqual(run('ABC','abc').al,0)
        self.assertEqual(run('\u00e9','e\u0301').al,0)
        self.assertEqual(run('\U0001f600','\ud83d\ude00').al,1)
    def test_owned_equality_text_mismatch_rejected_only_when_reached(self):
        eq=Eq(True,use_owned_text_model=True,left_text='wrong',right_text='abc')
        row=self.row(converted_text='abc',equality=eq)
        with self.assertRaises(ValueError):plan('primary',self.obs(row))
        self.assertTrue(plan('primary',self.obs(replace(row,count_begin_dword=0))).complete)
    def test_order_types_and_kind(self):
        with self.assertRaises(ValueError):plan('unknown',self.obs())
        with self.assertRaises(ValueError):plan('primary',self.obs(Row(1,0)))
        with self.assertRaises(ValueError):Row(True,0)
        with self.assertRaises(ValueError):Obs(iterations=[])
        with self.assertRaises(ValueError):source_vector_count(1,None)

class NameFilterQueryBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        query_fixture.RouteQueryTests.setUpClass();cls.fixture=query_fixture.RouteQueryTests();cls.n=NameFilterTests()
    def query(self,**kw):return plan_route_query(50,30,self.fixture.obs(self.fixture.row(**kw)))
    def test_complete_bound_filters_feed_query_but_still_require_return(self):
        primary=self.n.empty()
        secondary=plan('secondary',self.n.obs(self.n.row(match=True)))
        kw=dict(primary_name_al=None,secondary_name_al=None,primary_name_execution=primary,secondary_name_execution=secondary,
                primary_name_returned=True,secondary_name_returned=True)
        p=self.query(**kw);self.assertTrue(p.complete);self.assertEqual(p.output_bytes,(1,0,1))
        kw['primary_name_returned']=None
        p=self.query(**kw);self.assertFalse(p.complete);self.assertEqual(p.output_bytes,(0,0,0))
    def test_partial_bound_filter_or_unknown_name_holds_query(self):
        partial=plan('primary',self.n.obs())
        p=self.query(primary_name_al=None,primary_name_execution=partial,primary_name_returned=True)
        self.assertFalse(p.complete);self.assertIn('bound name filter',p.missing)
        p=self.query(name_text=None,primary_name_al=None,primary_name_execution=self.n.empty(),primary_name_returned=True)
        self.assertFalse(p.complete);self.assertIn('query Unicode name',p.missing)
    def test_bound_kind_name_raw_conflicts_and_unreached_ignored(self):
        for kw in (dict(primary_name_execution=self.n.empty()),
                   dict(primary_name_al=None,primary_name_execution=self.n.empty('secondary')),
                   dict(primary_name_al=None,primary_name_execution=self.n.empty(input_text='different'))):
            with self.assertRaises(ValueError):self.query(**kw)
        p=self.query(pointer_dword=0,primary_name_execution=self.n.empty())
        self.assertTrue(p.complete)

if __name__=='__main__':unittest.main()
