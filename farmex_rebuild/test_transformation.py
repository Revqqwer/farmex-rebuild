import unittest
from dataclasses import replace
from transformation import *

def panel(index=0,wait='10',enabled=True,route=True):
    return {TRANSFORMATION_INPUTS[0]:enabled,TRANSFORMATION_INPUTS[1]:wait,
            TRANSFORMATION_INPUTS[2]:route,TRANSFORMATION_INPUTS[3]:index}
def ready():return TransformationUseSamples(TransformationSelectionSamples((True,),(1,)),True,0x89abcdef,(True,True,True),1,123,True)

class TransformationTests(unittest.TestCase):
    def test_all18_index_ids_and_source_default(self):
        expected=(470310,470020,470040,470050,470070,470080,470090,470150,470130,
                  470132,472160,470200,470202,470250,470260,470290,470276,470280)
        self.assertEqual(SKILLS,expected)
        for i,skill in enumerate(expected):self.assertEqual(compile_transformation(panel(i)).fields[0x24],skill)
        for i in (-1,18,100):self.assertEqual(compile_transformation(panel(i)).fields[0x24],SKILLS[0])
    def test_rearm_and_route_flags_even_disabled_and_imul_wrap(self):
        c=compile_transformation(panel(wait='-1',enabled=False,route=False))
        self.assertEqual(dict(c.fields),{0x20:0,0x21:1,0x28:0xfffffc18,0x22:0,0x24:SKILLS[0]})
        self.assertEqual(compile_transformation(panel(wait='2147483647')).fields[0x28],0xfffffc18)
    def test_strict_parser_and_types(self):
        for v in ('0x10','1.5','2147483648',''):
            with self.assertRaises(ValueError):compile_transformation(panel(wait=v))
        with self.assertRaises(ValueError):compile_transformation(panel(index=True))
        with self.assertRaises(ValueError):compile_transformation(panel(enabled=1))
    def test_selector_masks_al_and_fallback_wraps(self):
        p=select_transformation(0xfffffff0,TransformationSelectionSamples((True,True),(0x100,0xff)))
        self.assertEqual(p.selected_skill,1984);self.assertEqual(p.checks,(('00464268',0xfffffff0),('00464268',1984)))
        p=select_transformation(99,TransformationSelectionSamples((True,),(0x10001,)))
        self.assertEqual(p.selected_skill,99);self.assertEqual(len(p.checks),1)
    def test_selector_missing_return_eax_and_both_false(self):
        for o in (TransformationSelectionSamples(),TransformationSelectionSamples((True,),()),TransformationSelectionSamples((True,),(0,))):
            self.assertFalse(select_transformation(1,o).complete)
        self.assertIsNone(select_transformation(1,TransformationSelectionSamples((True,True),(0,0))).selected_skill)
    def test_template_and_actor_are_full_dwords_not_potion_words(self):
        f=TransformationFrame(0x12345678);p=f.advance(ready())
        self.assertTrue(p.complete);self.assertEqual(len(p.payload),38)
        self.assertEqual(p.payload[:14],bytes.fromhex('310678563412efcdab89efcdab89'))
        self.assertEqual(p.payload[14:],bytes(24));self.assertEqual(len(f.queue.records),1)
        self.assertEqual(f.queue.records[0].delay_dword,0);self.assertFalse(p.native_execution_verified)
    def test_unselected_path_needs_no_actor_copy_or_queue(self):
        f=TransformationFrame(1);p=f.advance(TransformationUseSamples(TransformationSelectionSamples((True,True),(0,0))))
        self.assertTrue(p.complete);self.assertEqual(p.status,'no_skill_selected');self.assertEqual(f.queue.records,())
    def test_known_check_prefix_is_frozen_when_second_result_arrives(self):
        f=TransformationFrame(99)
        p=f.advance(replace(ready(),selection=TransformationSelectionSamples((True,),(0,))))
        self.assertFalse(p.complete)
        p=f.advance(replace(ready(),selection=TransformationSelectionSamples((True,True),(1,1))))
        self.assertTrue(p.complete);self.assertEqual(p.selection.selected_skill,2099)
    def test_actor_and_copy_prefix_are_frozen_across_gaps(self):
        f=TransformationFrame(99);o=replace(ready(),copy_returns=(True,))
        self.assertFalse(f.advance(o).complete);self.assertEqual(f.copies,1)
        p=f.advance(replace(ready(),actor_dword=1,copy_returns=(None,True,True)))
        self.assertTrue(p.complete);self.assertEqual(p.payload[6:10],bytes.fromhex('efcdab89'))
    def test_missing_gate_tick_and_cast_return_do_not_duplicate_queue(self):
        f=TransformationFrame(99)
        self.assertFalse(f.advance(replace(ready(),queue_gate=None)).complete)
        self.assertFalse(f.advance(replace(ready(),queue_tick=None)).complete)
        self.assertEqual(len(f.queue.records),0)
        p=f.advance(replace(ready(),cast_returned=None));self.assertFalse(p.complete);self.assertEqual(len(f.queue.records),1)
        self.assertTrue(f.advance(ready()).complete);self.assertEqual(len(f.queue.records),1)
        self.assertEqual(f.advance(ready()).status,'already_finished')
    def test_zero_queue_gate_is_known_skip_and_not_retried(self):
        f=TransformationFrame(99)
        self.assertFalse(f.advance(replace(ready(),queue_gate=0,queue_tick=None,cast_returned=None)).complete)
        self.assertTrue(f.advance(ready()).complete);self.assertEqual(len(f.queue.records),0)
    def test_consumed_full_dword_gate_survives_missing_tick_for_both_entries(self):
        for frame_type in (TransformationFrame,DirectSkillFrame):
            for gate in (1,0x100,0x80000000):
                with self.subTest(entry=frame_type.__name__,gate=gate):
                    f=frame_type(99)
                    p=f.advance(replace(ready(),queue_gate=gate,queue_tick=None))
                    self.assertFalse(p.complete);self.assertEqual(f.queue.records,())
                    p=f.advance(replace(ready(),queue_gate=0,queue_tick=456,cast_returned=None))
                    self.assertFalse(p.complete);self.assertEqual(len(f.queue.records),1)
                    self.assertEqual(f.queue.records[0].created_tick,456)
                    self.assertTrue(f.advance(ready()).complete)
                    self.assertEqual(len(f.queue.records),1)
    def test_gate_is_not_consumed_before_copy_prefix_or_when_unknown(self):
        for frame_type in (TransformationFrame,DirectSkillFrame):
            with self.subTest(entry=frame_type.__name__):
                f=frame_type(99)
                self.assertFalse(f.advance(replace(ready(),copy_returns=(True,),queue_gate=0)).complete)
                self.assertFalse(f.advance(replace(ready(),queue_gate=None)).complete)
                self.assertTrue(f.advance(replace(ready(),queue_gate=0x100)).complete)
                self.assertEqual(len(f.queue.records),1)
    def test_consumed_gate_is_retained_across_multiple_missing_ticks(self):
        f=TransformationFrame(99)
        for gate in (0xffffffff,None,0,1):
            self.assertFalse(f.advance(replace(ready(),queue_gate=gate,queue_tick=None)).complete)
            self.assertEqual(f.queue.records,())
        self.assertTrue(f.advance(replace(ready(),queue_gate=0)).complete)
        self.assertEqual(len(f.queue.records),1)
    def test_actor_return_is_separate_and_samples_validate(self):
        f=TransformationFrame(99);p=f.advance(replace(ready(),actor_returned=None))
        self.assertFalse(p.complete);self.assertIsNone(f.actor)
        with self.assertRaises(ValueError):TransformationSelectionSamples((1,),())
        with self.assertRaises(ValueError):TransformationUseSamples(copy_returns=(1,))

if __name__=='__main__':unittest.main()
