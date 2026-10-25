import unittest
from dataclasses import replace
from quest_lookup import QuestLookupFrame
from test_quest_lookup import capture as lookup_capture
from test_quest_name_compare import capture as compare_capture,Sample,owned


def nested(comparison=None,rows=None):
    o=lookup_capture([{}] if rows is None else rows)
    return replace(o,name_compares={0:compare_capture(Sample(False,True),Sample(False)) if comparison is None else comparison})


class QuestNameCompareLookupTests(unittest.TestCase):
    def frame(self,upper=7):return QuestLookupFrame(b'Quest',4,7,upper)

    def test_composed_equal_flows_to_filters_and_mode(self):
        p=self.frame().advance(nested())
        self.assertTrue(p.complete);self.assertEqual(len(p.mode_comparisons),1)
        self.assertEqual(p.name_compare_plans[0][1].eax,1)

    def test_composed_unequal_skips_filters_but_cleans_name(self):
        p=self.frame().advance(nested(compare_capture(Sample(False,False)),rows=[dict(nation_gate=object())]))
        self.assertTrue(p.complete);self.assertEqual(p.mode_comparisons,())
        self.assertIn('name_cleanup',[token[1] for _,_,token in p.calls])

    def test_missing_second_flags_withholds_lookup_return_and_filter_reads(self):
        f=self.frame();o=nested(compare_capture(Sample(True)))
        p=f.advance(o)
        self.assertEqual(p.needed,('name_compare',0,'less_flags',('sample','less')))
        self.assertIsNone(p.eax)
        self.assertNotIn('nation_gate',[token[1] for _,_,token in p.calls])
        self.assertTrue(f.advance(nested()).complete)

    def test_raw_name_result_cannot_bypass_a_pending_composed_call(self):
        f=self.frame();f.advance(nested(compare_capture(Sample(True))))
        p=f.advance(lookup_capture([{}]))
        self.assertFalse(p.complete);self.assertIsNone(p.eax)
        self.assertEqual(f.name_compare_modes[0],'composed')

    def test_outer_equality_return_is_separate_and_child_is_not_restarted(self):
        f=self.frame();o=nested();normal=dict(o.normal_returns);del normal[(0,'name_compare')]
        p=f.advance(replace(o,normal_returns=normal))
        self.assertTrue(p.name_compare_plans[0][1].complete);self.assertIsNone(p.eax)
        self.assertEqual(p.needed,('normal',(0,'name_compare')))
        calls=p.name_compare_plans[0][1].calls
        p=f.advance(lookup_capture([{}]));self.assertTrue(p.complete)
        self.assertEqual(p.name_compare_plans[0][1].calls,calls)

    def test_each_iteration_can_choose_an_independent_capture_source(self):
        o=nested(compare_capture(Sample(False,False)),rows=[{},{}])
        p=self.frame(8).advance(o)
        self.assertTrue(p.complete)
        self.assertEqual([r[0] for r in p.mode_comparisons],[1])
        self.assertEqual([ordinal for ordinal,_ in p.name_compare_plans],[0])

    def test_owned_post_load_ansi_operands_work_without_unicode_decode(self):
        c=compare_capture(owned(b'\xdd\0x',b'\xdd\0x'),owned(b'\xdd\0x',b'\xdd\0x'))
        p=self.frame().advance(nested(c))
        self.assertTrue(p.complete);self.assertEqual(len(p.mode_comparisons),1)
        self.assertFalse(p.native_execution_verified)

    def test_captured_name_return_mode_stays_captured(self):
        f=self.frame();o=lookup_capture([{}]);normal=dict(o.normal_returns);del normal[(0,'name_compare')]
        f.advance(replace(o,normal_returns=normal))
        p=f.advance(nested(compare_capture(Sample(False,False))))
        self.assertTrue(p.complete);self.assertEqual(p.name_compare_plans,())
        self.assertEqual(len(p.mode_comparisons),1)

    def test_missing_name_input_is_not_assumed_equal(self):
        o=lookup_capture([{}]);values=dict(o.values);del values[(0,'name_compare')]
        p=self.frame().advance(replace(o,values=values))
        self.assertEqual(p.needed,('name_compare_input',0));self.assertIsNone(p.eax)

    def test_null_candidate_does_not_consume_invalid_nested_comparison(self):
        p=self.frame().advance(replace(lookup_capture([dict(record=0)]),name_compares={0:object()}))
        self.assertTrue(p.complete);self.assertEqual(p.name_compare_plans,())


if __name__=='__main__':unittest.main()
