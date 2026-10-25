import unittest
from dataclasses import replace
from jail_protection import JailObservation
from relog_entry import RelogSnapshotFrame, ManualRelogFrame
from disconnect_routine import DisconnectRoutineFrame, DisconnectRoutineObservation
from relog_countdown import DisconnectRecoveryObservation
import test_disconnect_routine as routine_fixture
import test_disconnect_action as action_fixture


def raw(values=None, normals=(), entry=True):
    return JailObservation(entry, values or {}, {n: True for n in normals})


def snapshot():
    return raw(dict(root_slot=0x1000, root_value_eax=0x2000,
                    first_selector_eax=0xffffffff, second_selector_eax=4),
               ('prologue','root_value','first_selector','second_selector','epilogue'))


def manual(connection=1):
    return raw(dict(button_root=0x1000, button_form=0x2000, button_object=0x3000,
                    button_vtable=0x4000, button_target=0x5000, connection_eax=connection),
               ('prologue','button_setter','connection','queue_helper','epilogue'))


class RelogEntryTests(unittest.TestCase):
    def test_snapshot_entry_and_prologue_are_separate(self):
        f = RelogSnapshotFrame()
        p = f.advance(replace(snapshot(),entry_reached=False))
        self.assertEqual(p.needed,('entry','00412ed0'))
        p = f.advance(raw())
        self.assertEqual(p.needed,('normal','prologue'))
        self.assertEqual(p.reads,())

    def test_snapshot_first_store_survives_later_getter_gap(self):
        f = RelogSnapshotFrame()
        p = f.advance(raw(dict(root_slot=1,root_value_eax=0xdeadbeef),('prologue','root_value')))
        self.assertEqual(p.needed,('normal','first_selector'))
        self.assertEqual(p.stores,((0x50b2d4,4,0xdeadbeef),))
        self.assertEqual(p.calls[1],('0045dc44',(1,),'root_value'))

    def test_snapshot_all_three_raw_dwords_preserve_order_and_error_like_values(self):
        p = RelogSnapshotFrame().advance(snapshot())
        self.assertTrue(p.complete)
        self.assertEqual(p.stores,((0x50b2d4,4,0x2000),(0x50b2cc,4,0xffffffff),(0x50b2d0,4,4)))
        self.assertEqual([c[0] for c in p.calls[1:4]],['0045dc44','00461b24','004619b8'])
        self.assertFalse(p.whole_function_verified or p.native_execution_verified or p.live_compatibility_verified)

    def test_snapshot_second_value_and_epilogue_remain_separate(self):
        f = RelogSnapshotFrame()
        o = snapshot()
        v = dict(o.values)
        del v['second_selector_eax']
        p = f.advance(replace(o,values=v))
        self.assertEqual(p.needed,('value','second_selector_eax'))
        self.assertEqual(len(p.stores),2)
        p = f.advance(raw(dict(second_selector_eax=0)))
        self.assertEqual(p.needed,('normal','epilogue'))
        self.assertEqual(p.stores[-1],(0x50b2d0,4,0))
        p = f.advance(raw(normals=('epilogue',)))
        self.assertTrue(p.complete)
        self.assertIs(f.advance(JailObservation()),p)

    def test_manual_flag_precedes_first_ui_root_read(self):
        p = ManualRelogFrame().advance(raw(normals=('prologue',)))
        self.assertEqual(p.needed,('value','button_root'))
        self.assertEqual(p.stores,((0x562202,1,1),))
        self.assertEqual(p.reads,((0x5539f8,4,'button_root'),))

    def test_manual_setter_gap_blocks_counter_resets_and_connection(self):
        f = ManualRelogFrame()
        p = f.advance(replace(manual(),normal_returns={'prologue':True}))
        self.assertEqual(p.needed,('normal','button_setter'))
        self.assertEqual(p.stores,((0x562202,1,1),))
        p = f.advance(raw(normals=('button_setter',)))
        self.assertEqual(p.needed,('normal','connection'))
        self.assertEqual(p.stores[-2:],((0x553c7c,4,0),(0x553c80,4,0)))

    def test_manual_only_full_exact_connection_one_reaches_queue_helper(self):
        for result in (0,1,2,0x101,0xffffffff):
            p = ManualRelogFrame().advance(manual(result))
            self.assertTrue(p.complete)
            self.assertEqual(any(c[2]=='queue_helper' for c in p.calls),result==1)
            self.assertNotIn(0x562208,[s[0] for s in p.stores])

    def test_manual_queue_helper_and_native_return_receipts_are_separate(self):
        f = ManualRelogFrame()
        p = f.advance(replace(manual(),normal_returns={n:True for n in ('prologue','button_setter','connection')}))
        self.assertEqual(p.needed,('normal','queue_helper'))
        self.assertEqual(p.calls[-1],('004c7e0c',(0x561ef8,),'queue_helper'))
        p = f.advance(raw(normals=('queue_helper',)))
        self.assertEqual(p.needed,('normal','epilogue'))
        p = f.advance(raw(normals=('epilogue',)))
        self.assertTrue(p.complete)
        self.assertEqual(p.external_actions_executed,0)

    def test_manual_ui_dereferences_and_register_arguments_use_captured_values(self):
        o = manual(0)
        p = ManualRelogFrame().advance(replace(o,values={**o.values,'button_form':0xfffffffe,
                                                        'button_vtable':0xfffffffe}))
        self.assertIn((0x456,4,'button_object'),p.reads)
        self.assertIn((0x92,4,'button_target'),p.reads)
        self.assertEqual(p.calls[1],('captured_virtual_94',
                         (('target',0x5000),('EAX',0x3000),('EDX',0)),'button_setter'))

    def test_frames_require_typed_raw_observations(self):
        with self.assertRaises(ValueError):
            ManualRelogFrame().advance({})
        with self.assertRaises(ValueError):
            JailObservation(True,{'root_value_eax':-1})


class SnapshotBindingTests(unittest.TestCase):
    def regular(self):
        action = raw(action_fixture.relog_values(),('tick','reset','page_index','select','relog_start'))
        return replace(routine_fixture.routine_values(),
                       recovery=DisconnectRecoveryObservation(action),snapshot=snapshot())

    def test_regular_and_special_initialization_bind_same_snapshot_helper(self):
        for o in (self.regular(),replace(routine_fixture.routine_values(special=True),snapshot=snapshot())):
            p = DisconnectRoutineFrame().advance(o)
            self.assertTrue(p.complete)
            self.assertTrue(p.snapshot.complete)
            self.assertEqual(p.snapshot.stores[0],(0x50b2d4,4,0x2000))

    def test_child_entry_is_derived_but_missing_prologue_cannot_be_skipped(self):
        f = DisconnectRoutineFrame()
        p = f.advance(replace(self.regular(),snapshot=JailObservation()))
        self.assertEqual(p.needed,('snapshot',('normal','prologue')))
        self.assertEqual(p.snapshot.stores,())
        self.assertIsNone(p.exit)

    def test_snapshot_complete_does_not_imply_outer_helper_return(self):
        f = DisconnectRoutineFrame()
        o = self.regular()
        action = replace(o.recovery.action,normal_returns={**o.recovery.action.normal_returns,'relog_start':False})
        p = f.advance(replace(o,recovery=replace(o.recovery,action=action)))
        self.assertTrue(p.snapshot.complete)
        self.assertEqual(p.needed,('recovery',('action',('normal','relog_start'))))
        p = f.advance(DisconnectRoutineObservation(recovery=DisconnectRecoveryObservation(raw(normals=('relog_start',)))))
        self.assertEqual(p.needed,('boundary',('value','saved_fs_dword')))

    def test_partial_snapshot_stores_survive_without_duplicate_reads_or_parent_flags(self):
        f = DisconnectRoutineFrame()
        o = replace(self.regular(),snapshot=raw(dict(root_slot=1,root_value_eax=9),('prologue','root_value')))
        p = f.advance(o)
        self.assertEqual(p.needed,('snapshot',('normal','first_selector')))
        self.assertEqual(p.snapshot.stores,((0x50b2d4,4,9),))
        self.assertEqual(len(p.recovery.action.stores),6)
        p = f.advance(DisconnectRoutineObservation(snapshot=raw(
            dict(first_selector_eax=2,second_selector_eax=3),('first_selector','second_selector','epilogue'))))
        self.assertEqual(len(p.snapshot.reads),1)
        self.assertEqual(len(p.snapshot.stores),3)
        self.assertEqual(len(p.recovery.action.stores),6)

    def test_bound_snapshot_cannot_be_abandoned_using_only_outer_receipt(self):
        f = DisconnectRoutineFrame()
        p = f.advance(replace(self.regular(),snapshot=JailObservation()))
        p = f.advance(DisconnectRoutineObservation(recovery=DisconnectRecoveryObservation(raw(normals=('relog_start',)))))
        self.assertEqual(p.needed,('snapshot',('normal','prologue')))
        self.assertFalse(p.complete)

    def test_opaque_consumed_snapshot_cannot_be_bound_retroactively(self):
        f = DisconnectRoutineFrame()
        p = f.advance(replace(self.regular(),snapshot=None))
        self.assertTrue(p.complete)
        with self.assertRaisesRegex(ValueError,'retroactively'):
            f.advance(DisconnectRoutineObservation(snapshot=snapshot()))

    def test_before_opaque_snapshot_return_is_consumed_binding_is_allowed(self):
        f = DisconnectRoutineFrame()
        o = replace(self.regular(),snapshot=None)
        a = replace(o.recovery.action,normal_returns={**o.recovery.action.normal_returns,'relog_start':False})
        p = f.advance(replace(o,recovery=replace(o.recovery,action=a)))
        self.assertEqual(p.needed,('recovery',('action',('normal','relog_start'))))
        p = f.advance(self.regular())
        self.assertTrue(p.complete)
        self.assertTrue(p.snapshot.complete)

    def test_unreached_snapshot_is_not_created_on_disabled_or_countdown_path(self):
        for a in (dict(enabled_byte=0),action_fixture.base(initialized_byte=1)):
            o = routine_fixture.routine_values()
            o = replace(o,snapshot=snapshot(),recovery=DisconnectRecoveryObservation(raw(a),raw(dict(waiting_byte=0))))
            f = DisconnectRoutineFrame()
            p = f.advance(o)
            self.assertTrue(p.complete)
            self.assertIsNone(f.snapshot_frame)
            self.assertIsNone(p.snapshot)

    def test_snapshot_field_requires_raw_typed_observation(self):
        with self.assertRaises(ValueError):
            DisconnectRoutineObservation(snapshot={})


if __name__=='__main__':
    unittest.main()
