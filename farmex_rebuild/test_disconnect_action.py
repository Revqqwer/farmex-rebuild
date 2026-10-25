import unittest
from disconnect_action import DisconnectActionFrame
from jail_protection import JailObservation


def base(**overrides):
    values = dict(enabled_byte=1, bot_running_byte=0, alarm_byte=0,
                  initialized_byte=0, procedure_byte=1, mode_zero_dword=2,
                  mode_one_dword=2, mode_two_dword=2)
    values.update(overrides)
    return values


def relog_values():
    return base(tick_eax=0xffffffff,
                reset_root=0x1000, reset_form=0x2000, reset_object=0x3000,
                reset_vtable=0x4000, reset_target=0x5000,
                page_root=0x6000, page_form=0x7000, page_object=0x8000,
                page_index_eax=0xffffffff,
                select_root=0x9000, select_form=0xa000, select_object=0xb000,
                select_vtable=0xc000, select_target=0xd000)


class DisconnectActionTests(unittest.TestCase):
    def observe(self, frame, values, *normals, entry=True):
        return frame.advance(JailObservation(entry, values, {n: True for n in normals}))

    def test_entry_is_explicit_and_unused_values_do_not_start_frame(self):
        f = DisconnectActionFrame()
        p = self.observe(f, base(), entry=False)
        self.assertEqual(p.needed, ('entry', '00459c5a'))
        self.assertEqual(p.reads, ())

    def test_disabled_skips_stop_alarm_and_all_procedure_reads(self):
        p = self.observe(DisconnectActionFrame(), dict(enabled_byte=0))
        self.assertTrue(p.complete)
        self.assertEqual(p.next_address, 0x459fa0)
        self.assertEqual(p.reads, ((0x56221e, 1, 'enabled_byte'),))
        self.assertEqual((p.calls, p.stores, p.intents), ((), (), ()))

    def test_bot_stop_return_precedes_alarm_read_and_is_not_repeated(self):
        f = DisconnectActionFrame()
        p = self.observe(f, base(bot_running_byte=2))
        self.assertEqual(p.needed, ('normal', 'stop_bot'))
        self.assertEqual(p.calls, (('0040ae0c', (0, 0x561f34), 'stop_bot'),))
        self.assertNotIn('alarm_byte', [r[2] for r in p.reads])
        self.assertEqual(self.observe(f, {}).calls, p.calls)
        p = self.observe(f, dict(alarm_byte=0, initialized_byte=1), 'stop_bot')
        self.assertTrue(p.complete)
        self.assertEqual(p.next_address, 0x459e06)

    def test_alarm_uses_returned_object_indirection_and_separate_cleanup(self):
        f = DisconnectActionFrame()
        v = base(alarm_byte=1, alarm_construct_eax=0xfffffffE, alarm_text_pointer=0x1234)
        p = self.observe(f, v, 'alarm_construct')
        self.assertEqual(p.needed, ('normal', 'alarm'))
        self.assertIn((0xfffffffe, 4, 'alarm_text_pointer'), p.reads)
        self.assertEqual(p.intents, (('alarm', 0x1234, 0x569568),))
        p = self.observe(f, {}, 'alarm')
        self.assertEqual(p.needed, ('normal', 'alarm_cleanup'))
        self.assertNotIn('initialized_byte', [r[2] for r in p.reads])
        p = self.observe(f, dict(initialized_byte=1), 'alarm_cleanup')
        self.assertTrue(p.complete)
        self.assertEqual(p.next_address, 0x459e06)

    def test_initialized_goes_to_unmodeled_countdown_before_proc_read(self):
        p = self.observe(DisconnectActionFrame(), base(initialized_byte=0xff))
        self.assertTrue(p.complete)
        self.assertEqual(p.next_address, 0x459e06)
        self.assertNotIn('procedure_byte', [r[2] for r in p.reads])

    def test_procedure_disabled_does_not_read_mode(self):
        p = self.observe(DisconnectActionFrame(), base(procedure_byte=0))
        self.assertTrue(p.complete)
        self.assertFalse(any('mode_' in r[2] for r in p.reads))

    def test_shutdown_null_local_uses_disk_empty_fallback_and_cleanup(self):
        f = DisconnectActionFrame()
        p = self.observe(f, base(mode_zero_dword=0, command_local_pointer=0), 'command_construct')
        self.assertEqual(p.calls[-1], ('WinExec', (0, 0x521463), 'command'))
        self.assertEqual(p.intents, (('command', 0x521463, 0),))
        p = self.observe(f, {}, 'command')
        self.assertFalse(p.complete)
        self.assertEqual(p.needed, ('normal', 'command_cleanup'))
        p = self.observe(f, {}, 'command_cleanup')
        self.assertTrue(p.complete)
        self.assertEqual(p.next_address, 0x459fa0)
        self.assertEqual(p.external_actions_executed, 0)

    def test_shutdown_nonzero_captured_pointer_not_constructor_eax(self):
        p = self.observe(DisconnectActionFrame(),
                         base(mode_zero_dword=0, command_local_pointer=0x100),
                         'command_construct', 'command', 'command_cleanup')
        self.assertTrue(p.complete)
        self.assertIn(('WinExec', (0, 0x100), 'command'), p.calls)
        self.assertFalse(any(r[2] == 'mode_one_dword' for r in p.reads))

    def test_fresh_mode_change_selects_terminate_and_handle_is_not_pid(self):
        f = DisconnectActionFrame()
        p = self.observe(f, base(mode_zero_dword=9, mode_one_dword=1,
                                current_process_eax=0xffffffff), 'current_process')
        self.assertEqual(p.calls[0], ('GetCurrentProcess', (), 'current_process'))
        self.assertEqual(p.calls[-1], ('TerminateProcess', (0, 0xffffffff), 'terminate'))
        p = self.observe(f, {}, 'terminate')
        self.assertEqual(p.needed, ('value', 'saved_fs_dword'))
        p = self.observe(f, dict(saved_fs_dword=0x444))
        self.assertTrue(p.complete)
        self.assertEqual(p.next_address, 0x459faa)
        self.assertEqual(p.intents[-1], ('restore_FS0', 0x444))
        self.assertFalse(any(r[2] == 'mode_two_dword' for r in p.reads))

    def test_three_fresh_mode_reads_can_all_miss(self):
        p = self.observe(DisconnectActionFrame(), base(mode_zero_dword=1, mode_one_dword=2,
                                                       mode_two_dword=0))
        self.assertTrue(p.complete)
        self.assertEqual(p.calls, ())
        self.assertEqual([r[2] for r in p.reads[-3:]],
                         ['mode_zero_dword', 'mode_one_dword', 'mode_two_dword'])

    def test_relog_two_flags_survive_missing_tick_receipt_and_value(self):
        f = DisconnectActionFrame()
        p = self.observe(f, base())
        prefix = ((0x562208, 1, 1), (0x562209, 1, 1))
        self.assertEqual(p.stores, prefix)
        self.assertEqual(p.needed, ('normal', 'tick'))
        p = self.observe(f, {}, 'tick')
        self.assertEqual(p.needed, ('value', 'tick_eax'))
        self.assertEqual(p.stores, prefix)
        p = self.observe(f, dict(tick_eax=0xffffffff))
        self.assertEqual(p.stores[2:], ((0x56220c, 4, 0xffffffff), (0x562210, 4, 0),
                                      (0x562214, 4, 0), (0x562218, 4, 0)))
        self.assertEqual(p.needed, ('value', 'reset_root'))

    def test_fresh_ui_chains_and_full_page_index_reach_opaque_relog(self):
        f = DisconnectActionFrame()
        p = self.observe(f, relog_values(), 'tick', 'reset', 'page_index', 'select')
        self.assertFalse(p.complete)
        self.assertEqual(p.needed, ('normal', 'relog_start'))
        reads = {r[2]: r[0] for r in p.reads}
        self.assertEqual([reads[k] for k in ('reset_root', 'page_root', 'select_root')],
                         [0x5539f8] * 3)
        self.assertEqual([reads[k] for k in ('reset_form', 'page_form', 'select_form')],
                         [0x1000, 0x6000, 0x9000])
        self.assertEqual(reads['reset_target'], 0x4094)
        self.assertEqual(reads['page_object'], 0x8008)
        self.assertEqual(reads['select_target'], 0xc13c)
        self.assertEqual(p.calls[-2], ('captured_virtual_13c',
                         (('target', 0xd000), ('EAX', 0xb000), ('EDX', 0xffffffff)), 'select'))
        p = self.observe(f, {}, 'relog_start')
        self.assertTrue(p.complete)
        self.assertEqual(p.next_address, 0x459fa0)
        self.assertFalse(p.native_execution_verified or p.live_compatibility_verified
                         or p.whole_function_verified)
        self.assertIs(f.advance(JailObservation()), p)

    def test_no_later_ui_reads_before_reset_normal(self):
        p = self.observe(DisconnectActionFrame(), relog_values(), 'tick')
        self.assertEqual(p.needed, ('normal', 'reset'))
        self.assertFalse(any(r[2] == 'page_root' for r in p.reads))

    def test_context_wrap_and_raw_validation(self):
        p = self.observe(DisconnectActionFrame(context=0xfffffffa), dict(enabled_byte=0))
        self.assertEqual(p.reads[0][0], 0x84)
        for context in (-1, 1 << 32, True):
            with self.assertRaises(ValueError):
                DisconnectActionFrame(context=context)
        with self.assertRaises(ValueError):
            JailObservation(True, {'enabled_byte': 256})


if __name__ == '__main__':
    unittest.main()
