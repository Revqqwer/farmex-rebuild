import unittest
from dataclasses import replace
from route_query import RouteQueryCandidate as Row,RouteQueryObservation as Obs,QueryNameCapture,plan_route_query as plan
from source_coin import GuardedDwordSample as Word,GuardedByteSample as Byte
from route_entry import RouteEntryObservation,plan_route_entry
from route_resume import RouteResumeState
from route_progress import RouteProgressObservation

class RouteQueryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.empty=tuple(Row(i,0) for i in range(3001))
    def row(self,index=0,**kw):
        values=dict(pointer_dword=0x1000,
            global_samples=((0x553fec,0x10),(0x554040,0x20),(0x553fdc,0x30),(0x554008,0x40),(0x554010,0x50),(0x553fe8,0x60)),
            dword_samples=(Word(0x1010,1,3),Word(0x1020,1,7),Word(0x1030,1,1)),
            x_read_returned=True,y_read_returned=True,x_float_bits=0x3f800000,y_float_bits=0x40000000,
            metric_ftol_dword=10,context39_byte=0,name_span_returned=True,name_text='abc',reference_4626b0_dword=2,
            anti_radius_ah=0,primary_name_al=0,secondary_name_al=1)
        values.update(kw);return Row(index,**values)
    def obs(self,*rows,**kw):
        values=dict(reference_462650_dword=99,string_init_returned=True,candidates=self.empty,final_cleanup_returned=True)
        if rows:
            candidates=list(self.empty)
            for row in rows:candidates[row.index]=row
            values['candidates']=tuple(candidates)
        values.update(kw);return Obs(**values)
    def group_equal(self,index=0,**kw):
        values=dict(dword_samples=(Word(0x1010,1,3),Word(0x1020,1,7),Word(0x1030,1,2)),
            context8_byte=0,selected_radius_ah=0,anti_radius_ah=1,secondary_name_al=0)
        values.update(kw);return self.row(index,**values)
    def entry(self,q,**kw):
        def G(a,v,b=32):return ('global',a,b,v)
        def F(a,v,b=32):return ('object',a,b,v)
        samples=(G(0x569100,1,8),G(0x569108,0),F(0x5e0,0),F(0x5e4,0),G(0x56ff8c,0),G(0x56ff90,0),
                 G(0x569124,30),G(0x569104,50),G(0x569120,0,8))
        progress=RouteProgressObservation((F(0x566,0,8),F(0x567,0,8),F(0x5f0,2)),step_return_dword=0)
        values=dict(samples=samples,tick_samples=(10000,1001,1100),query_returned=True,query_execution=q,progress=progress)
        values.update(kw);return RouteEntryObservation(**values)
    def test_explicit_empty_scan_covers_all3001_indices(self):
        p=plan(None,None,self.obs());self.assertTrue(p.complete);self.assertEqual(p.output_bytes,(0,0,0));self.assertEqual(p.visited,3001)
        self.assertEqual([s[1] for s in p.steps if s[0]=='00464a10'],list(range(3001)))
    def test_index3000_is_inclusive_and_not_deduplicated(self):
        p=plan(50,30,self.obs(self.row(0),self.row(3000)))
        self.assertTrue(p.complete);self.assertEqual(p.output_bytes,(1,0,1));self.assertEqual(p.visited,3001)
        self.assertEqual(p.writes,((0,0,1),(0,2,1),(3000,0,1),(3000,2,1)))
    def test_missing_tail_even_when_all_outputs1_is_not_complete(self):
        rows=(self.row(0),self.group_equal(1,anti_radius_ah=0))
        p=plan(50,30,self.obs(candidates=rows));self.assertFalse(p.complete);self.assertEqual(p.output_bytes,(1,1,1))
        self.assertIn('index2',p.missing)
    def test_final_cleanup_receipt_is_not_implied_by_exhaustion(self):
        p=plan(50,30,self.obs(self.row(),final_cleanup_returned=None))
        self.assertFalse(p.complete);self.assertEqual(p.visited,3001);self.assertEqual(p.output_bytes,(1,0,1))
    def test_words_truncate_but_cached_full_dword_does_not(self):
        row=self.row(dword_samples=(Word(0x1010,1,0x10003),Word(0x1020,1,0x10007),Word(0x1030,1,0x10001)))
        p=plan(50,30,self.obs(row,reference_462650_dword=0x10007))
        self.assertTrue(p.complete);self.assertEqual(p.output_bytes,(1,0,1));self.assertEqual(p.name_plans[0][1].byte_count,3)
        p=plan(50,30,self.obs(row,reference_462650_dword=7));self.assertTrue(p.complete);self.assertEqual(p.output_bytes,(0,0,0))
    def test_reference_4626b0_full_dword_not_low_word(self):
        p=plan(50,30,self.obs(self.row(reference_4626b0_dword=0x10001,context8_byte=None)))
        self.assertTrue(p.complete);self.assertEqual(p.output_bytes,(1,0,1))
    def test_self_reference_skip_still_requires_prior_name_span(self):
        p=plan(50,30,self.obs(self.row(name_span_returned=None),reference_462650_dword=7))
        self.assertFalse(p.complete);self.assertIn('name copy',p.missing)
        p=plan(50,30,self.obs(self.row(reference_4626b0_dword=None,primary_name_al=None,secondary_name_al=None),reference_462650_dword=7))
        self.assertTrue(p.complete);self.assertEqual(p.output_bytes,(0,0,0))
    def test_opposite_reference_radius_equal_passes_less_unordered_skip(self):
        for ah,outputs in ((0,(1,0,1)),(0x40,(1,0,1)),(1,(0,0,0)),(0x45,(0,0,0))):
            p=plan(50,30,self.obs(self.row(anti_radius_ah=ah)))
            self.assertTrue(p.complete);self.assertEqual(p.output_bytes,outputs)
    def test_equal_reference_enemy_radius_can_set_only_second_output(self):
        p=plan(50,30,self.obs(self.group_equal()))
        self.assertTrue(p.complete);self.assertEqual(p.output_bytes,(0,1,0))
        selected=[s for s in p.steps if s[0]=='radius_vs_metric_float' and s[2]=='selected radius']
        self.assertEqual(selected[0][3],30)
    def test_context8_chooses_anti_radius_and_secondary_independent(self):
        p=plan(50,30,self.obs(self.group_equal(context8_byte=1,anti_radius_ah=0,secondary_name_al=1)))
        self.assertEqual(p.output_bytes,(1,1,1))
        selected=[s for s in p.steps if s[0]=='radius_vs_metric_float' and s[2]=='selected radius']
        self.assertEqual(selected[0][3],50)
        p=plan(50,30,self.obs(self.group_equal(primary_name_al=1,anti_radius_ah=None,secondary_name_al=1)))
        self.assertTrue(p.complete);self.assertEqual(p.output_bytes,(0,0,1))
    def test_state4_skips_second_read_and_name_after_metric(self):
        row=self.row(global_samples=self.row().global_samples[:5]+((0x554034,0x70),),
            context39_byte=1,byte_samples=(Byte(0x1070,1,4),),name_span_returned=None)
        p=plan(50,30,self.obs(row));self.assertTrue(p.complete);self.assertEqual(p.output_bytes,(0,0,0))
        self.assertEqual(len(p.guarded_plans),4);self.assertEqual(p.name_plans,())
        p=plan(50,30,self.obs(replace(row,metric_ftol_dword=None)))
        self.assertFalse(p.complete);self.assertEqual(len(p.guarded_plans),3)
    def test_state_second_read_is_fresh_and5_skips_name(self):
        row=self.row(global_samples=self.row().global_samples[:5]+((0x554034,0x70),(0x554034,0x71)),
            context39_byte=1,byte_samples=(Byte(0x1070,1,3),Byte(0x1071,1,5)),name_span_returned=None)
        p=plan(50,30,self.obs(row));self.assertTrue(p.complete);self.assertEqual(p.output_bytes,(0,0,0))
        self.assertEqual(len(p.guarded_plans),5)
        row=replace(row,global_samples=row.global_samples+((0x553fe8,0x60),),
            byte_samples=(Byte(0x1070,1,3),Byte(0x1071,1,3)),name_span_returned=True)
        p=plan(50,30,self.obs(row));self.assertTrue(p.complete);self.assertEqual(p.output_bytes,(1,0,1))
    def test_inline15_and_indirect16_copy_exact_length_not255(self):
        for length,indirect,address in ((15,False,0x1060),(16,True,0x2000)):
            dwords=(Word(0x1010,1,length),Word(0x1020,1,7),Word(0x1030,1,1))
            if indirect:dwords+=(Word(0x1060,1,0x2000),)
            row=self.row(dword_samples=dwords,name_text=None,name_capture=QueryNameCapture(True,b'abc\0'+b'\0'*(length-4),'cp1254'))
            p=plan(50,30,self.obs(row));self.assertTrue(p.complete)
            request=p.name_plans[0][1];self.assertEqual((request.address,request.byte_count,request.indirect),(address,length,indirect))
            self.assertEqual(p.name_plans[0][2].text,'abc')
    def test_name_codec_gap_and_unsafe_copy_are_not_empty_names(self):
        row=self.row(name_text=None,name_capture=QueryNameCapture(True,b'abc',None))
        p=plan(50,30,self.obs(row));self.assertFalse(p.complete);self.assertIn('needs_codepage',p.missing)
        row=self.row(dword_samples=(Word(0x1010,1,513),Word(0x1020,1,7),Word(0x1030,1,1),Word(0x1060,1,0x2000)),
            name_text=None,name_capture=QueryNameCapture(True,b'x'*513,'cp1254'))
        p=plan(50,30,self.obs(row));self.assertFalse(p.complete);self.assertIn('buffer_overflow',p.missing)
    def test_raw_unicode_and_name_capture_conflict_only_when_reached(self):
        with self.assertRaises(ValueError):plan(50,30,self.obs(self.row(name_capture=QueryNameCapture())))
        row=self.row(pointer_dword=0,name_capture=QueryNameCapture())
        p=plan(50,30,self.obs(row));self.assertTrue(p.complete)
    def test_mapped_reference_helper_preserves_second_fresh_read(self):
        p=plan(50,30,self.obs(self.row(reference_4626b0_dword=None,reference_462690_samples=(1,))))
        self.assertTrue(p.complete);self.assertEqual(p.output_bytes,(1,0,1))
        row=self.row(reference_4626b0_dword=None,reference_462690_samples=(0,2),context8_byte=0,selected_radius_ah=0)
        p=plan(50,30,self.obs(row));self.assertTrue(p.complete);self.assertEqual(p.output_bytes,(1,1,1))
        p=plan(50,30,self.obs(replace(row,reference_462690_samples=(0,))))
        self.assertFalse(p.complete);self.assertIn('fresh second',p.missing)
    def test_gaps_in_initial_reference_or_string_init_hold_outputs(self):
        for kw in (dict(reference_462650_dword=None),dict(string_init_returned=None)):
            p=plan(None,None,self.obs(**kw));self.assertFalse(p.complete);self.assertEqual(p.output_bytes,(0,0,0));self.assertEqual(p.visited,0)
    def test_zero_pointer_does_not_require_candidate_data(self):
        p=plan(None,None,self.obs());self.assertTrue(p.complete);self.assertEqual(p.guarded_plans,())
    def test_bound_query_into_entry_still_requires_independent_return(self):
        q=plan(50,30,self.obs(self.row()));self.assertTrue(q.complete)
        p=plan_route_entry(RouteResumeState(1,0),self.entry(q))
        self.assertTrue(p.complete);self.assertEqual(p.local_bytes,(1,0,1));self.assertIs(p.query_execution,q)
        p=plan_route_entry(RouteResumeState(1,0),self.entry(q,query_returned=None))
        self.assertFalse(p.complete);self.assertEqual(p.local_bytes,(None,None,None))
    def test_bound_partial_outputs_do_not_bypass_entry(self):
        q=plan(50,30,self.obs(candidates=(self.row(),self.group_equal(1,anti_radius_ah=0))))
        self.assertFalse(q.complete);self.assertEqual(q.output_bytes,(1,1,1))
        p=plan_route_entry(RouteResumeState(1,0),self.entry(q))
        self.assertFalse(p.complete);self.assertEqual(p.local_bytes,(None,None,None));self.assertEqual(p.writes,())
    def test_bound_argument_and_raw_output_conflicts(self):
        q=plan(50,30,self.obs())
        with self.assertRaises(ValueError):plan_route_entry(RouteResumeState(1,0),self.entry(q,query_output_bytes=(0,0,0)))
        wrong=replace(q,anti_radius_dword=51)
        with self.assertRaises(ValueError):plan_route_entry(RouteResumeState(1,0),self.entry(wrong))
    def test_unreached_bound_query_ignored_and_unused_args_can_be_unknown(self):
        q=plan(None,None,self.obs());self.assertTrue(q.complete)
        p=plan_route_entry(RouteResumeState(1,0),self.entry(q));self.assertTrue(p.complete)
        skipped=self.entry(q,samples=(('global',0x569100,8,0),('global',0x569120,8,0),('global',0x569120,8,0)),tick_samples=())
        p=plan_route_entry(RouteResumeState(1,0),skipped);self.assertTrue(p.complete);self.assertIsNone(p.query_execution)
    def test_order_width_and_types(self):
        with self.assertRaises(ValueError):plan(50,30,self.obs(candidates=(Row(1,0),)))
        with self.assertRaises(ValueError):Row(3001,0)
        with self.assertRaises(ValueError):self.row(context39_byte=True)
        row=self.row(global_samples=((0x554040,0x20),))
        with self.assertRaises(ValueError):plan(50,30,self.obs(row))

if __name__=='__main__':unittest.main()
