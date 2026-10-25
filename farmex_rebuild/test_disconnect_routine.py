import unittest
from dataclasses import replace
from jail_protection import JailObservation
from dc_full_chain import DCFullChainObservation
from relog_countdown import DisconnectRecoveryObservation
from disconnect_routine import (SpecialReconnectInitFrame, SpecialReconnectFrame,
    SpecialReconnectCountdownFrame, DisconnectRoutineFrame, DisconnectRoutineObservation)
import test_relog_countdown as countdown_fixture
import test_disconnect_action as action_fixture
import test_dc_full_chain as sender_fixture


def init_values(**extras):
    v = dict(bot_running_byte=0, initialized_byte=0, connection_mode_byte=1,
             guard_root_slot=0x100, guard_root_eax=0x200, guard_offset=0x10, guard_eax=0,
             clear_root_slot=0x300, clear_root_eax=0x400, clear_offset=0x20,
             tick_eax=0xffffffff, reset_root=0x500, reset_form=0x600,
             reset_object=0x700, reset_vtable=0x800, reset_target=0x900)
    v.update(extras)
    return v


INIT_NORMALS = ('stop_bot', 'guard_root', 'guard_byte', 'clear_root', 'clear_byte',
                'tick', 'reset', 'runtime_snapshot')


def raw(values=None, normals=(), entry=True):
    return JailObservation(entry, values or {}, {k: True for k in normals})


def routine_values(special=False):
    return DisconnectRoutineObservation(
        boundary=raw(dict(saved_fs_dword=0x1234), ('prologue', 'seh_restore', 'return')),
        periodic=DCFullChainObservation(raw(dict(context_6e_byte=int(special), enabled_byte=0))),
        recovery=DisconnectRecoveryObservation(raw(dict(enabled_byte=0))),
        special=DisconnectRecoveryObservation(raw(init_values(), INIT_NORMALS)))


class SpecialReconnectTests(unittest.TestCase):
    def test_exact_connection_mode_one_chooses31_other_bytes_choose1(self):
        for mode, seconds in ((0, 1), (1, 31), (2, 1), (255, 1)):
            p = SpecialReconnectInitFrame().advance(raw(init_values(connection_mode_byte=mode), INIT_NORMALS))
            self.assertTrue(p.complete)
            self.assertEqual(p.stores[0], (0x562204, 4, seconds))
            self.assertEqual(p.next_address, 0x459c05)

    def test_al_zero_skips_clear_even_when_upper_eax_nonzero(self):
        p = SpecialReconnectInitFrame().advance(raw(init_values(guard_eax=0x100), INIT_NORMALS))
        self.assertTrue(p.complete)
        self.assertFalse(any(c[2] == 'clear_root' for c in p.calls))
        self.assertEqual(p.intents, ())

    def test_nonzero_al_including_two_uses_fresh_clear_chain_and_wrapping_address(self):
        p = SpecialReconnectInitFrame().advance(raw(init_values(
            guard_eax=2, clear_root_slot=0x1000, clear_root_eax=0xfffffffe, clear_offset=5), INIT_NORMALS))
        self.assertTrue(p.complete)
        self.assertIn(('0045dc44', (0x1000,), 'clear_root'), p.calls)
        self.assertIn(('0045de4c', (0, 3), 'clear_byte'), p.calls)
        self.assertEqual(p.intents, (('source_byte_clear', 3, 0),))
        self.assertEqual([r[0] for r in p.reads if r[2] in ('guard_root_slot', 'clear_root_slot')],
                         [0x553e80, 0x553e80])

    def test_wait_store_survives_guard_gap_before_relog_flags(self):
        f = SpecialReconnectInitFrame()
        p = f.advance(raw(init_values()))
        self.assertEqual(p.needed, ('normal', 'guard_root'))
        self.assertEqual(p.stores, ((0x562204, 4, 31),))
        p = f.advance(raw(init_values(), ('guard_root',)))
        self.assertEqual(p.needed, ('normal', 'guard_byte'))
        self.assertEqual(len(p.stores), 1)

    def test_stop_precedes_initialized_check_and_missing_receipt_does_not_repeat(self):
        f = SpecialReconnectInitFrame()
        p = f.advance(raw(init_values(bot_running_byte=1, initialized_byte=1)))
        self.assertEqual(p.needed, ('normal', 'stop_bot'))
        self.assertEqual(p.reads, ((0x561f60, 1, 'bot_running_byte'),))
        p = f.advance(raw(dict(initialized_byte=1), ('stop_bot',)))
        self.assertTrue(p.complete)
        self.assertEqual(p.next_address, 0x459a6e)
        self.assertEqual(len(p.calls), 1)
        self.assertEqual(p.stores, ())

    def test_initialized_skips_mode_guard_and_tick(self):
        p = SpecialReconnectInitFrame().advance(raw(dict(bot_running_byte=0, initialized_byte=255)))
        self.assertTrue(p.complete)
        self.assertEqual(p.next_address, 0x459a6e)
        self.assertEqual(p.calls, ())
        self.assertEqual(len(p.reads), 2)

    def test_flags_precede_tick_and_extra88_clear_follows_tick_result(self):
        f = SpecialReconnectInitFrame()
        p = f.advance(raw(init_values(), ('guard_root', 'guard_byte')))
        self.assertEqual(p.needed, ('normal', 'tick'))
        self.assertEqual(p.stores, ((0x562204, 4, 31), (0x562208, 1, 1), (0x562209, 1, 1)))
        p = f.advance(raw(dict(tick_eax=25), ('tick',)))
        self.assertEqual(p.needed, ('value', 'reset_root'))
        self.assertEqual(p.stores[-5:], ((0x56220c, 4, 25), (0x562210, 4, 0),
                                      (0x562214, 4, 0), (0x562218, 4, 0), (0x56221c, 1, 0)))

    def test_ui_reset_and_runtime_snapshot_are_separate_no_page_selection(self):
        f = SpecialReconnectInitFrame()
        p = f.advance(raw(init_values(), INIT_NORMALS[:-1]))
        self.assertEqual(p.needed, ('normal', 'runtime_snapshot'))
        self.assertEqual(p.calls[-1], ('00412ed0', (), 'runtime_snapshot'))
        self.assertNotIn('TTabSheet.GetPageIndex', [c[0] for c in p.calls])
        p = f.advance(raw(normals=('runtime_snapshot',)))
        self.assertTrue(p.complete)
        self.assertEqual(p.next_address, 0x459c05)

    def test_special_countdown_uses70_own_stamp_and_special_suffix(self):
        p = SpecialReconnectCountdownFrame().advance(raw(countdown_fixture.notice(),
                                                       countdown_fixture.ALL_RETURNS))
        self.assertTrue(p.complete)
        self.assertIn((0x562204, 4, 'wait_dword'), p.reads)
        self.assertIn((0x553cdc, 4, 'notice_stamp_low_dword'), p.reads)
        self.assertIn((0x553ce0, 4, 'notice_stamp_high_dword'), p.reads)
        self.assertEqual(p.calls[3], ('00505bb8', (0x521435, 'suffix_unicode'), 'suffix_construct'))
        self.assertEqual(p.stores[-2:], ((0x553cdc, 4, 1200), (0x553ce0, 4, 0)))
        self.assertEqual(p.next_address, 0x459c05)

    def test_special_countdown_expiration_clears_only75_and_returns_special_edge(self):
        p = SpecialReconnectCountdownFrame().advance(raw(countdown_fixture.timing(wait_dword=1),
                                                       countdown_fixture.ALL_RETURNS))
        self.assertTrue(p.complete)
        self.assertEqual(p.stores, ((0x562209, 1, 0),))
        self.assertEqual(p.next_address, 0x459c05)

    def test_special_init_does_not_consume_countdown_on_same_poll(self):
        f = SpecialReconnectFrame()
        p = f.advance(DisconnectRecoveryObservation(raw(init_values(), INIT_NORMALS), raw(dict(waiting_byte=0))))
        self.assertTrue(p.complete)
        self.assertIsNone(f.countdown)

    def test_special_initialized_derives_distinct_countdown_entry(self):
        p = SpecialReconnectFrame().advance(DisconnectRecoveryObservation(
            raw(dict(bot_running_byte=0, initialized_byte=1))))
        self.assertEqual(p.needed, ('countdown', ('value', 'waiting_byte')))
        self.assertTrue(p.action.complete)

    def test_custom_context_and_explicit_entry_validation(self):
        f = SpecialReconnectInitFrame(context=0xffffffc0)
        p = f.advance(raw(init_values(), INIT_NORMALS, entry=False))
        self.assertEqual(p.needed, ('entry', '0045998e'))
        p = f.advance(raw(init_values(), INIT_NORMALS))
        self.assertEqual(p.stores[0][0], 0x30)
        for c in (True, -1, 1 << 32):
            with self.assertRaises(ValueError):
                SpecialReconnectInitFrame(context=c)


class DisconnectRoutineTests(unittest.TestCase):
    def test_explicit_entry_and_separate_prologue_gate_every_child(self):
        f = DisconnectRoutineFrame()
        p = f.advance(DisconnectRoutineObservation())
        self.assertEqual(p.needed, ('boundary', ('entry', '00459970')))
        self.assertEqual(p.calls, ())
        p = f.advance(DisconnectRoutineObservation(boundary=raw()))
        self.assertEqual(p.needed, ('boundary', ('normal', 'prologue')))
        self.assertIsNone(p.periodic)
        p = f.advance(DisconnectRoutineObservation(boundary=raw()))
        self.assertEqual(len(p.calls), 1)

    def test_regular_disabled_path_reaches_return_with_one_context_gate(self):
        f = DisconnectRoutineFrame()
        p = f.advance(routine_values())
        self.assertTrue(p.complete)
        self.assertIsNone(f.special)
        self.assertEqual(p.periodic.parent.reads[0][2], 'context_6e_byte')
        self.assertTrue(p.recovery.complete)
        self.assertEqual(p.exit.intents, (('restore_FS0', 0x1234),))
        self.assertFalse(p.whole_function_verified or p.native_execution_verified or p.live_compatibility_verified)
        self.assertIs(f.advance(DisconnectRoutineObservation()), p)

    def test_special_nonzero_context_skips_all_periodic_and_regular_options(self):
        p = DisconnectRoutineFrame().advance(routine_values(special=True))
        self.assertTrue(p.complete)
        self.assertEqual(len(p.periodic.parent.reads), 1)
        self.assertIsNone(p.recovery)
        self.assertEqual(p.special.action.stores[0], (0x562204, 4, 31))
        self.assertEqual(p.special.action.next_address, 0x459c05)

    def test_missing_exit_value_then_fs_receipt_then_return_are_distinct(self):
        f = DisconnectRoutineFrame()
        o = replace(routine_values(), boundary=raw(normals=('prologue',)))
        p = f.advance(o)
        self.assertEqual(p.needed, ('boundary', ('value', 'saved_fs_dword')))
        p = f.advance(DisconnectRoutineObservation(boundary=raw(dict(saved_fs_dword=0x900))))
        self.assertEqual(p.needed, ('boundary', ('normal', 'seh_restore')))
        self.assertEqual(p.exit.intents, (('restore_FS0', 0x900),))
        p = f.advance(DisconnectRoutineObservation(boundary=raw(normals=('seh_restore',))))
        self.assertEqual(p.needed, ('boundary', ('normal', 'return')))
        p = f.advance(DisconnectRoutineObservation(boundary=raw(normals=('return',))))
        self.assertTrue(p.complete)

    def test_regular_mode_one_has_already_restored_fs_and_must_not_do_it_twice(self):
        o = routine_values()
        a = raw(action_fixture.base(mode_zero_dword=9, mode_one_dword=1,
                     current_process_eax=0xffffffff, saved_fs_dword=0x777), ('current_process', 'terminate'))
        o = replace(o, boundary=raw(normals=('prologue', 'return')),
                    recovery=DisconnectRecoveryObservation(a))
        p = DisconnectRoutineFrame().advance(o)
        self.assertTrue(p.complete)
        self.assertEqual(p.recovery.action.intents[-1], ('restore_FS0', 0x777))
        self.assertEqual(p.exit.intents, ())
        self.assertEqual(p.exit.calls, (('source_stack_restore_return_span', (), 'return'),))

    def test_regular_initialized_countdown_and_special_countdown_are_distinct(self):
        for special, expected in ((False, 0x459fa0), (True, 0x459c05)):
            o = routine_values(special=special)
            if special:
                a = raw(dict(bot_running_byte=0, initialized_byte=1))
                o = replace(o, special=DisconnectRecoveryObservation(a, raw(dict(waiting_byte=0))))
            else:
                a = raw(action_fixture.base(initialized_byte=1))
                o = replace(o, recovery=DisconnectRecoveryObservation(a, raw(dict(waiting_byte=0))))
            p = DisconnectRoutineFrame().advance(o)
            self.assertTrue(p.complete)
            child = p.special if special else p.recovery
            self.assertEqual(child.countdown.next_address, expected)

    def test_four_layer_sender_trace_retained_while_later_action_waits(self):
        f = DisconnectRoutineFrame()
        periodic = sender_fixture.DCFullChainTests().observation()
        o = replace(routine_values(), periodic=periodic, recovery=DisconnectRecoveryObservation())
        p = f.advance(o)
        self.assertEqual(p.needed, ('recovery', ('action', ('value', 'enabled_byte'))))
        self.assertEqual(len(p.periodic.write_intents), 2)
        self.assertEqual(p.periodic.parent.stores, ((0x553ce4, 4, 300010),))
        p = f.advance(DisconnectRoutineObservation(recovery=DisconnectRecoveryObservation(raw(dict(enabled_byte=0)))))
        self.assertEqual(p.needed, ('boundary', ('value', 'saved_fs_dword')))
        self.assertEqual(len(p.periodic.write_intents), 2)

    def test_consumer_or_sender_gap_prevents_recovery_even_with_early_receipts(self):
        f = DisconnectRoutineFrame()
        periodic = sender_fixture.DCFullChainTests().observation()
        periodic = replace(periodic, action=replace(periodic.action, transfers={}))
        p = f.advance(replace(routine_values(), periodic=periodic))
        self.assertEqual(p.needed[0], 'periodic')
        self.assertIsNone(f.recovery)
        self.assertIsNone(p.recovery)

    def test_special_snapshot_gap_preserves_init_prefix_and_blocks_return(self):
        f = DisconnectRoutineFrame()
        o = routine_values(special=True)
        o = replace(o, special=DisconnectRecoveryObservation(raw(init_values(), INIT_NORMALS[:-1])))
        p = f.advance(o)
        self.assertEqual(p.needed, ('special', ('action', ('normal', 'runtime_snapshot'))))
        self.assertEqual(len(p.special.action.stores), 8)
        self.assertIsNone(p.exit)
        p = f.advance(DisconnectRoutineObservation(special=DisconnectRecoveryObservation(
            raw(normals=('runtime_snapshot',)))))
        self.assertEqual(p.needed, ('boundary', ('value', 'saved_fs_dword')))

    def test_typed_observations_reject_mixed_children(self):
        for name in ('boundary', 'periodic', 'recovery', 'special'):
            with self.assertRaises(ValueError):
                DisconnectRoutineObservation(**{name: {}})
        with self.assertRaises(ValueError):
            DisconnectRoutineFrame().advance(DisconnectRecoveryObservation())


if __name__ == '__main__':
    unittest.main()
