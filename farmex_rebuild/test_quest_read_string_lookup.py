import unittest
from dataclasses import replace
from quest_lookup import QuestLookupFrame
from test_quest_lookup import capture as lookup_capture
from test_quest_read_string import capture as read_capture
from test_quest_name_compare import capture as compare_capture,Sample


def nested(text=b'Quest',**row):
    data=text+b'\0'*(max(0,15-len(text)))
    return replace(lookup_capture([row]),name_reads={0:read_capture(data,constructor=text)})


def derived(text=b'Quest'):
    compare=compare_capture(Sample(use_owned_bytes=True),Sample(use_owned_bytes=True))
    return replace(nested(text),name_compares={0:compare},use_read_name_operands=True)


class QuestReadStringLookupTests(unittest.TestCase):
    def frame(self):return QuestLookupFrame(b'Quest',4,7,7)

    def test_completed_read_value_reaches_owned_name_after_outer_and_assign(self):
        p=self.frame().advance(nested())
        self.assertTrue(p.complete);self.assertEqual(p.owned_name_values,((0,b'Quest'),))
        self.assertTrue(p.name_read_plans[0][1].complete)

    def test_assignment_prefix_is_visible_while_inner_cleanup_waits(self):
        f=self.frame();o=nested();r=o.name_reads[0];normal=dict(r.normal_returns);del normal['cleanup']
        p=f.advance(replace(o,name_reads={0:replace(r,normal_returns=normal)}))
        child=p.name_read_plans[0][1]
        self.assertEqual(child.destination_ansi,b'Quest');self.assertTrue(child.destination_assigned)
        self.assertIsNone(p.eax);self.assertEqual(p.owned_name_values,())
        self.assertTrue(f.advance(o).complete)

    def test_completed_callee_still_requires_outer_read_return(self):
        f=self.frame();o=nested();normal=dict(o.normal_returns);del normal[(0,'name_read')]
        p=f.advance(replace(o,normal_returns=normal))
        self.assertTrue(p.name_read_plans[0][1].complete);self.assertEqual(p.owned_name_values,())
        self.assertEqual(p.needed,('normal',(0,'name_read')))
        self.assertTrue(f.advance(o).complete)

    def test_outer_assignment_gap_preserves_read_snapshot_without_publishing_name(self):
        f=self.frame();o=nested();normal=dict(o.normal_returns);normal[(0,'name_assign')]=False
        p=f.advance(replace(o,normal_returns=normal))
        self.assertTrue(p.name_read_plans[0][1].complete);self.assertEqual(p.owned_name_values,())
        self.assertEqual(f.advance(o).owned_name_values,((0,b'Quest'),))

    def test_pending_composed_reader_cannot_be_bypassed_by_opaque_normal(self):
        f=self.frame();o=nested();r=o.name_reads[0];normal=dict(r.normal_returns);del normal['copy']
        f.advance(replace(o,name_reads={0:replace(r,normal_returns=normal)}))
        p=f.advance(lookup_capture([{}]));self.assertFalse(p.complete)
        self.assertEqual(f.name_read_modes[0],'composed')

    def test_inline_and_indirect_source_arguments_reach_child(self):
        for storage,address,count in ((15,0x2010,15),(16,0x3000,16)):
            f=self.frame();o=nested(storage=storage)
            o=replace(o,name_reads={0:read_capture(b'Quest\0'+b'\0'*20,constructor=b'Quest')})
            self.assertTrue(f.advance(o).complete)
            self.assertEqual((f.name_read_frames[0].address,f.name_read_frames[0].count),(address,count))

    def test_bad_read_empty_destination_can_drive_unequal_comparison(self):
        o=derived();o=replace(o,name_reads={0:read_capture(raw=object(),bad=1,constructor=b'')})
        p=self.frame().advance(o)
        self.assertTrue(p.complete);self.assertEqual(p.mode_comparisons,())
        self.assertEqual(p.name_compare_plans[0][1].eax,0)

    def test_derived_equal_and_unequal_comparison_use_actual_assigned_bytes(self):
        for text,equal in ((b'Quest',1),(b'Other',0)):
            p=self.frame().advance(derived(text))
            self.assertTrue(p.complete);self.assertEqual(p.name_compare_plans[0][1].eax,equal)
            self.assertEqual(len(p.mode_comparisons),equal)

    def test_bridge_requires_opt_in_and_preserves_explicit_second_operands(self):
        o=derived();p=self.frame().advance(replace(o,use_read_name_operands=False))
        self.assertFalse(p.complete)
        cmp=o.name_compares[0]
        cmp=replace(cmp,less=Sample(use_owned_bytes=True,left_bytes=b'z',right_bytes=b'a'))
        # First owned comparison is less, fresh explicit second is greater;
        # compare wrapper consequently reports equality rather than caching CF.
        p=self.frame().advance(replace(derived(b'A'),name_compares={0:cmp}))
        self.assertEqual(p.name_compare_plans[0][1].eax,1)

    def test_opaque_reader_compatibility_and_unreached_invalid_child(self):
        p=self.frame().advance(replace(lookup_capture([dict(record=0)]),name_reads={0:object()}))
        self.assertTrue(p.complete);self.assertEqual(p.name_read_plans,())
        f=self.frame();o=lookup_capture([{}]);normal=dict(o.normal_returns);normal[(0,'name_read')]=False
        f.advance(replace(o,normal_returns=normal));p=f.advance(nested())
        self.assertTrue(p.complete);self.assertEqual(p.name_read_plans,())

    def test_derived_bytes_are_not_invented_for_opaque_reader(self):
        o=derived();p=self.frame().advance(replace(o,name_reads={}))
        self.assertEqual(p.needed,('owned_name_bytes',0));self.assertIsNone(p.eax)

    def test_read_overflow_holds_before_comparison_and_return(self):
        p=self.frame().advance(nested(storage=513))
        self.assertFalse(p.complete);self.assertIsNone(p.eax)
        self.assertEqual(p.name_compare_plans,())
        self.assertEqual(p.name_read_plans[0][1].status,'unresolved_source_stack_overflow')

    def test_owned_operand_bridge_choice_is_frozen_while_compare_waits(self):
        f=self.frame();o=derived();cmp=o.name_compares[0];normal=dict(cmp.normal_returns)
        normal['greater_compare']=False
        p=f.advance(replace(o,name_compares={0:replace(cmp,normal_returns=normal)}))
        self.assertFalse(p.complete)
        p=f.advance(replace(o,use_read_name_operands=False))
        self.assertTrue(p.complete);self.assertEqual(p.name_compare_plans[0][1].eax,1)


if __name__=='__main__':unittest.main()
