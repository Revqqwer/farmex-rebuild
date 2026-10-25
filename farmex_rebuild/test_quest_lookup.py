import unittest
from dataclasses import replace
from quest_lookup import QuestLookupFrame,QuestLookupObservation as Observation


def capture(rows):
    values={};normal={(-1,s):True for s in ('entry','argument_copy','argument_cleanup')}
    roles=('record','metadata_key','metadata','name_init','storage','name_pointer','temp_init','name_read',
           'name_assign','temp_cleanup','name_compare','nation_gate','nation_value','nation_current',
           'class_gate','class_value','class_current','mode','name_cleanup')
    for ordinal,changes in enumerate(rows):
        row=dict(record=0x1000,metadata_key=77,metadata=0x2000,storage=15,name_pointer=0x3000,
                 name_compare=1,nation_gate=3,nation_value=1,nation_current=1,
                 class_gate=5,class_value=2,class_current=2,mode=4)
        row.update(changes)
        values.update({(ordinal,k):v for k,v in row.items()})
        normal.update({(ordinal,k):True for k in roles})
    return Observation(values,normal)


class QuestLookupTests(unittest.TestCase):
    def frame(self,lower=7,upper=7,mode=4):return QuestLookupFrame(b'Quest',mode,lower,upper)
    def labels(self,plan):return [token[1] for _,_,token in plan.calls]

    def test_matching_candidate_still_returns_minus_one_and_scans_next(self):
        p=self.frame(7,8).advance(capture([{},{}]))
        self.assertTrue(p.complete);self.assertEqual(p.eax,0xffffffff)
        self.assertEqual([row[1] for row in p.mode_comparisons],[7,8])
        self.assertEqual(p.iteration,2)
        self.assertFalse(p.native_execution_verified)

    def test_mode_match_mismatch_and_high_dword_do_not_change_return(self):
        for mode in (3,4,0x10000004):
            p=self.frame(mode=mode).advance(capture([{}]))
            self.assertEqual(p.eax,0xffffffff)
            self.assertEqual(p.mode_comparisons[0][-1],mode==4)

    def test_reversed_signed_range_copies_and_cleans_argument_without_lookup(self):
        p=self.frame(0,0xffffffff).advance(capture([]))
        self.assertEqual(p.eax,0xffffffff)
        self.assertEqual(self.labels(p),['entry','argument_copy','argument_cleanup'])

    def test_signed_negative_lower_includes_zero(self):
        p=self.frame(0xfffffffe,0).advance(capture([dict(record=0)]*3))
        self.assertTrue(p.complete)
        args=[args for helper,args,_ in p.calls if helper=='004d51c4']
        self.assertEqual([a[1] for a in args],[0xfffffffe,0xffffffff,0])

    def test_null_record_and_null_metadata_skip_name_lifetimes(self):
        for row in (dict(record=0,metadata=object()),dict(metadata=0,storage=object())):
            p=self.frame().advance(capture([row]))
            self.assertTrue(p.complete);self.assertNotIn('name_init',self.labels(p))

    def test_inline_storage_uses15_and_indirect_storage_uses_raw_count(self):
        for storage,address,count in ((15,0x2010,15),(16,0x3000,16),(0xffffffff,0x2010,15)):
            p=self.frame().advance(capture([dict(storage=storage)]))
            args=next(args for helper,args,token in p.calls if token==(0,'name_read'))
            self.assertEqual(args,('owned_name_temp',address,count))
            self.assertEqual('name_pointer' in self.labels(p),storage==16)

    def test_pointer_and_read_addresses_wrap_dword(self):
        p=self.frame().advance(capture([dict(record=0xfffffff0,metadata=0xfffffff8)]))
        reads={token[1]:address for address,width,token,raw in p.reads}
        self.assertEqual(reads['metadata_key'],0x40)
        self.assertEqual(reads['storage'],0x18)
        args=next(args for helper,args,token in p.calls if token==(0,'name_read'))
        self.assertEqual(args[1],8)

    def test_false_name_skips_all_filters_but_preserves_cleanup(self):
        p=self.frame().advance(capture([dict(name_compare=0,nation_gate=object())]))
        self.assertTrue(p.complete);self.assertNotIn('nation_gate',self.labels(p))
        self.assertIn('name_cleanup',self.labels(p))

    def test_nonzero_low_byte_name_result_and_special_filter_values_skip_reads(self):
        p=self.frame().advance(capture([dict(name_compare=0x10000002,nation_value=object(),class_value=object())]))
        self.assertTrue(p.complete);self.assertEqual(len(p.mode_comparisons),1)
        self.assertNotIn('nation_current',self.labels(p));self.assertNotIn('class_current',self.labels(p))

    def test_repeated_nation_and_class_reads_are_fresh_and_byte_comparisons_differ(self):
        p=self.frame().advance(capture([dict(nation_gate=1,nation_value=0x102,nation_current=2,
                                               class_gate=1,class_value=0x104,class_current=0xab04)]))
        self.assertEqual(len(p.mode_comparisons),1)
        p=self.frame().advance(capture([dict(nation_gate=1,nation_value=2,nation_current=0x102)]))
        self.assertNotIn('class_gate',self.labels(p))
        p=self.frame().advance(capture([dict(class_gate=1,class_value=2,class_current=3)]))
        self.assertNotIn('mode',self.labels(p))

    def test_cleanup_gap_withholds_eax_and_does_not_reissue_calls(self):
        f=self.frame();o=capture([{}]);normal=dict(o.normal_returns);del normal[(0,'name_cleanup')]
        p=f.advance(replace(o,normal_returns=normal))
        self.assertFalse(p.complete);self.assertIsNone(p.eax)
        p=f.advance(o)
        self.assertTrue(p.complete)
        self.assertEqual(self.labels(p).count('mode'),1)
        self.assertEqual(self.labels(p).count('name_cleanup'),1)

    def test_missing_read_value_is_frozen_after_normal_return(self):
        f=self.frame();o=capture([{}]);values=dict(o.values);del values[(0,'nation_gate')]
        p=f.advance(replace(o,values=values))
        self.assertEqual(p.needed,('value',(0,'nation_gate')))
        normal=dict(o.normal_returns);normal[(0,'nation_gate')]=False
        p=f.advance(replace(o,normal_returns=normal))
        self.assertTrue(p.complete)
        self.assertEqual(self.labels(p).count('nation_gate'),1)

    def test_argument_cleanup_is_required_even_with_no_rows(self):
        f=self.frame(1,0);o=capture([]);normal=dict(o.normal_returns);del normal[(-1,'argument_cleanup')]
        self.assertIsNone(f.advance(replace(o,normal_returns=normal)).eax)
        self.assertEqual(f.advance(o).eax,0xffffffff)

    def test_upper_intmax_wraps_without_fabricated_termination(self):
        f=self.frame(0x7fffffff,0x7fffffff)
        p=f.advance(capture([dict(record=0),dict(record=0)]))
        self.assertFalse(p.complete);self.assertEqual(p.index_dword,0x80000001)
        self.assertEqual(p.needed,('normal',(2,'record')))
        self.assertIsNone(p.eax)

    def test_own_budget_yields_and_keeps_same_source_call_tokens(self):
        f=self.frame(7,8);o=capture([{},{}])
        for _ in range(100):
            p=f.advance(o,step_budget=1)
            if p.complete:break
        self.assertTrue(p.complete)
        self.assertEqual(len(p.calls),len({token for helper,args,token in p.calls}))
        self.assertIs(f.advance(),p)


if __name__=='__main__':unittest.main()
