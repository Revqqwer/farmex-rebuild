import unittest
from dataclasses import replace
from jail_protection import JailObservation
from relog_selection import (RelogSelectionFrame,RelogControllerSelectionsFrame,
                              RelogControllerSelectionsObservation)
import test_relog_controller as controller_fixture


def child(**extra):
    v=dict(guard_slot=0x1000,guard_root_eax=0x2000,guard_base_offset=0x10,
           guard_base_eax=0x3000,guard_item_offset=0x20,guard_stride=4,guard_item_eax=0x4000,
           direct_slot=0x5000,direct_root=0x6000,direct_base_offset=0x30,direct_object=0x7000,
           direct_target=0x8000,direct_item_offset=0x40,direct_item=0x9000,
           dispatch_offset=0x50,dispatch_vtable=0xa000,dispatch_target=0xb000,dispatch_eax=0xdeadbeef)
    v.update(extra)
    return JailObservation(True,v,{n:True for n in ('prologue','guard_root','guard_base',
                                                   'guard_item','dispatch','epilogue')})


class RelogSelectionTests(unittest.TestCase):
    def test_kind_argument_validation_and_entry_gate(self):
        for kind,arg in (('other',None),('first',None),('second',True),('advance',0),('confirm',0)):
            with self.assertRaises(ValueError):RelogSelectionFrame(kind,argument=arg)
        f=RelogSelectionFrame('first',argument=2)
        p=f.advance(replace(child(),entry_reached=False))
        self.assertEqual(p.needed,('entry','0041272c'))
        self.assertEqual(p.reads,())

    def test_first_guarded_list_item_uses_index_stride_then_new_direct_chain(self):
        p=RelogSelectionFrame('first',argument=3).advance(child())
        self.assertTrue(p.complete)
        self.assertIn(('0045dc44',(0x302c,),'guard_item'),p.calls)
        self.assertEqual(p.calls[-2],('captured_game_dispatch',
             (('ECX',0x7000),('target',0xb000),('physical_pushes',(0x10000000,0x4000))),'dispatch'))
        self.assertIn((0x553f3c,4,'guard_slot'),p.reads)
        self.assertIn((0x553f3c,4,'direct_slot'),p.reads)

    def test_first_imul_low32_and_pointer_add_wrap_without_index_clamp(self):
        p=RelogSelectionFrame('first',argument=0xffffffff).advance(child(guard_base_eax=2,
              guard_item_offset=1,guard_stride=8))
        self.assertIn(('0045dc44',(0xfffffffb,),'guard_item'),p.calls)

    def test_first_index_and_guard_root_gap_do_not_consume_direct_values_early(self):
        f=RelogSelectionFrame('first',argument=0)
        p=f.advance(replace(child(),normal_returns={'prologue':True}))
        self.assertEqual(p.needed,('normal','guard_root'))
        self.assertNotIn('direct_slot',[r[2] for r in p.reads])

    def test_second_uses_global_function_pointer_one_argument_and_no_guard_chain(self):
        p=RelogSelectionFrame('second',argument=0xffffffff).advance(child())
        self.assertTrue(p.complete)
        self.assertEqual([c[2] for c in p.calls],['prologue','dispatch','epilogue'])
        self.assertIn((0x553f40,4,'direct_target'),p.reads)
        self.assertEqual(p.calls[-2][1],(('ECX',0x7000),('target',0x8000),('physical_pushes',(0xffffffff,))))
        self.assertNotIn('dispatch_vtable',[r[2] for r in p.reads])

    def test_confirm_guard_item_offset_has_no_stride_or_index(self):
        p=RelogSelectionFrame('confirm').advance(child())
        self.assertIn((0x5541bc,4,'guard_item_offset'),p.reads)
        self.assertNotIn('guard_stride',[r[2] for r in p.reads])
        self.assertEqual(p.calls[-2][1][-1],('physical_pushes',(1,0x4000)))

    def test_advance_reads_direct_item_before_virtual_dispatch_without_guard_helpers(self):
        p=RelogSelectionFrame('advance').advance(child())
        self.assertIn((0x7040,4,'direct_item'),p.reads)
        self.assertEqual(p.calls[-2][1][-1],('physical_pushes',(1,0x9000)))
        self.assertNotIn('0045dc44',[c[0] for c in p.calls])

    def test_dispatch_offset_is_vtable_offset_not_callable_absolute_address(self):
        p=RelogSelectionFrame('confirm').advance(child(dispatch_vtable=0xfffffffe,dispatch_offset=5))
        self.assertIn((3,4,'dispatch_target'),p.reads)
        self.assertEqual(p.calls[-2][1][1],('target',0xb000))

    def test_zero_values_do_not_create_source_absent_pointer_or_target_skip(self):
        p=RelogSelectionFrame('second',argument=0).advance(child(direct_slot=0,direct_root=0,
             direct_base_offset=0,direct_object=0,direct_target=0))
        self.assertTrue(p.complete)
        self.assertEqual(p.calls[-2][1],(('ECX',0),('target',0),('physical_pushes',(0,))))

    def test_dispatch_return_eax_and_frame_exit_remain_separate(self):
        f=RelogSelectionFrame('second',argument=2);o=child();v=dict(o.values);del v['dispatch_eax']
        p=f.advance(replace(o,values=v));self.assertEqual(p.needed,('value','dispatch_eax'))
        p=f.advance(JailObservation(values={'dispatch_eax':0xffffffff}))
        self.assertEqual(p.needed,('normal','epilogue'))
        self.assertEqual(p.return_eax,0xffffffff)
        p=f.advance(JailObservation(normal_returns={'epilogue':True}))
        self.assertTrue(p.complete)
        self.assertIs(f.advance(JailObservation()),p)
        self.assertFalse(p.whole_function_verified or p.native_execution_verified or p.live_compatibility_verified)


def bound():
    parent=controller_fixture.sample(advance_ui_eax=1,select_enabled_byte=1,
        first_selection_eax=0,first_desired=0xffffffff,second_selection_eax=2,
        second_desired_compare=3,second_desired_push=4)
    return RelogControllerSelectionsObservation(parent,{k:child() for k in
        ('advance','select_first','select_second','confirm')})


class RelogControllerSelectionBindingTests(unittest.TestCase):
    def test_all_four_children_complete_with_arguments_derived_from_parent(self):
        f=RelogControllerSelectionsFrame();p=f.advance(bound())
        self.assertTrue(p.complete)
        self.assertEqual(set(p.children),{'advance','select_first','select_second','confirm'})
        self.assertEqual(p.children['select_first'].argument,0xffffffff)
        self.assertEqual(p.children['select_second'].argument,4)
        self.assertIsNone(p.children['confirm'].argument)
        self.assertEqual(p.parent.return_eax,0xdeadbeef)
        self.assertFalse(p.native_execution_verified or p.live_compatibility_verified)

    def test_missing_child_epilogue_blocks_outer_return_and_source_fresh_read(self):
        f=RelogControllerSelectionsFrame();o=bound();c=o.children['select_first']
        n=dict(c.normal_returns);n['epilogue']=False
        p=f.advance(replace(o,children={**o.children,'select_first':replace(c,normal_returns=n)}))
        self.assertEqual(p.needed,('child','select_first',('normal','epilogue')))
        self.assertNotIn('first_selection_fresh_offset',[r[2] for r in p.parent.reads])
        self.assertTrue(p.children['advance'].complete)

    def test_outer_return_is_separate_after_completed_child_and_trace_survives(self):
        f=RelogControllerSelectionsFrame();o=bound();n=dict(o.parent.normal_returns);n['select_first']=False
        p=f.advance(replace(o,parent=replace(o.parent,normal_returns=n)))
        self.assertEqual(p.needed,('parent',('normal','select_first')))
        self.assertTrue(p.children['select_first'].complete)
        first=p.children['select_first']
        p=f.advance(o)
        self.assertTrue(p.complete)
        self.assertIs(p.children['select_first'],first)

    def test_bound_child_cannot_be_abandoned_using_only_parent_receipts(self):
        f=RelogControllerSelectionsFrame();o=bound()
        p=f.advance(replace(o,children={'advance':JailObservation()}))
        self.assertEqual(p.needed,('child','advance',('normal','prologue')))
        p=f.advance(RelogControllerSelectionsObservation(o.parent))
        self.assertEqual(p.needed,('child','advance',('normal','prologue')))

    def test_unreached_children_not_created_and_cannot_invent_successful_selection(self):
        f=RelogControllerSelectionsFrame();o=bound()
        p=f.advance(replace(o,parent=controller_fixture.sample(select_enabled_byte=1,
                             first_selection_eax=0,first_selection_fresh_eax=0)))
        self.assertTrue(p.complete)
        self.assertEqual(set(p.children),{'select_first'})
        self.assertNotIn('confirm_tick',[c[2] for c in p.parent.calls])

    def test_fresh_state_still_required_after_child_dispatch_return(self):
        f=RelogControllerSelectionsFrame();o=bound();v=dict(o.parent.values)
        del v['first_selection_fresh_eax']
        p=f.advance(replace(o,parent=replace(o.parent,values=v)))
        self.assertEqual(p.needed,('parent',('value','first_selection_fresh_eax')))
        self.assertTrue(p.children['select_first'].complete)

    def test_retroactive_binding_after_opaque_consumed_call_is_rejected(self):
        f=RelogControllerSelectionsFrame();o=bound()
        p=f.advance(RelogControllerSelectionsObservation(o.parent));self.assertTrue(p.complete)
        with self.assertRaisesRegex(ValueError,'retroactively'):f.advance(o)

    def test_child_mapping_immutable_and_unknown_or_untyped_children_rejected(self):
        o=bound()
        with self.assertRaises(TypeError):o.children['advance']=JailObservation()
        for children in ({'unknown':child()},{'advance':{}}):
            with self.assertRaises(ValueError):RelogControllerSelectionsObservation(children=children)
        with self.assertRaises(ValueError):RelogControllerSelectionsFrame().advance(JailObservation())


if __name__=='__main__':unittest.main()
