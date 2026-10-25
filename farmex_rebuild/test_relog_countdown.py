import unittest
from jail_protection import JailObservation
from relog_countdown import (RelogCountdownFrame, DisconnectRecoveryFrame,
                             DisconnectRecoveryObservation)


def timing(**extras):
    values = dict(waiting_byte=1, elapsed_tick_eax=1000,
                  started_low_dword=0, started_high_dword=0, wait_dword=30,
                  notice_tick_eax=1000, notice_stamp_low_dword=0,
                  notice_stamp_high_dword=0)
    values.update(extras)
    return values


def notice(**extras):
    values = timing(number_construct_eax=0x1100, empty_construct_eax=0x1200,
                    queue_size_eax=0, queue_capacity_eax=1,
                    queue_end_dword=0x1300, queue_insert_eax=0x1400,
                    post_tick_eax=1200)
    values.update(extras)
    return values


FORMAT_RETURNS = ('suffix_construct', 'number_construct', 'empty_construct',
                  'concatenate', 'ansi_convert', 'joined_cleanup',
                  'suffix_cleanup', 'number_cleanup', 'queue_size', 'queue_capacity')
ALL_RETURNS = ('elapsed_tick', 'seconds_division', 'notice_tick') + FORMAT_RETURNS + (
    'queue_end', 'queue_insert', 'post_tick', 'notice_cleanup')


class RelogCountdownTests(unittest.TestCase):
    def run_frame(self, values, normals=ALL_RETURNS, frame=None, entry=True):
        return (frame or RelogCountdownFrame()).advance(
            JailObservation(entry, values, {label: True for label in normals}))

    def test_entry_and_waiting_zero_have_no_timer_or_queue_calls(self):
        f = RelogCountdownFrame()
        p = self.run_frame(notice(), frame=f, entry=False)
        self.assertEqual(p.needed, ('entry', '00459e06'))
        self.assertEqual(p.reads, ())
        p = self.run_frame(dict(waiting_byte=0), frame=f)
        self.assertTrue(p.complete)
        self.assertEqual((p.calls, p.stores, p.intents), ((), (), ()))
        self.assertEqual(p.next_address, 0x459fa0)

    def test_division_normal_receipt_precedes_wait_field_read(self):
        f = RelogCountdownFrame()
        p = self.run_frame(timing(), ('elapsed_tick',), f)
        self.assertEqual(p.needed, ('normal', 'seconds_division'))
        self.assertNotIn('wait_dword', [r[2] for r in p.reads])
        self.assertEqual(p.calls[-1], ('00503e75',
                         (('PUSH', 0), ('PUSH', 1000), ('EDX:EAX', 1000)), 'seconds_division'))
        p = self.run_frame(dict(wait_dword=0), ('seconds_division',), f)
        self.assertTrue(p.complete)
        self.assertEqual(p.remaining_dword, 0xffffffff)

    def test_integer_seconds_truncate_negative_elapsed_toward_zero(self):
        for start, expected in ((999, 30), (1001, 31)):
            with self.subTest(start=start):
                p = self.run_frame(timing(elapsed_tick_eax=0, started_low_dword=start,
                                          notice_tick_eax=0))
                self.assertTrue(p.complete)
                self.assertEqual(p.remaining_dword, expected)

    def test_tick_wrap_is_signed_qword_subtraction_not_dword_elapsed(self):
        p = self.run_frame(timing(elapsed_tick_eax=20, started_low_dword=0xfffffff0,
                                  notice_tick_eax=0))
        self.assertEqual(p.remaining_dword, 4294997)
        self.assertEqual(p.stores, ())

    def test_high_timestamp_dword_is_used_in_elapsed_subtraction(self):
        p = self.run_frame(timing(elapsed_tick_eax=0, started_high_dword=1,
                                  notice_tick_eax=0))
        self.assertEqual(p.remaining_dword, 4294997)

    def test_only_low_division_result_enters_wrapping_dword_remaining(self):
        p = self.run_frame(timing(elapsed_tick_eax=0, started_high_dword=0xf0000000,
                                  wait_dword=1, notice_tick_eax=0))
        self.assertEqual(p.remaining_dword, (1 - ((1 << 60) // 1000)) & 0xffffffff)

    def test_remaining_signed_overflow_takes_finished_path(self):
        p = self.run_frame(timing(elapsed_tick_eax=0, started_low_dword=1000,
                                  wait_dword=0x7fffffff))
        self.assertEqual(p.remaining_dword, 0x80000000)
        self.assertEqual(p.stores, ((0x562209, 1, 0),))
        self.assertFalse(any(c[2] == 'notice_tick' for c in p.calls))

    def test_zero_and_negative_remaining_only_clear_wait_flag(self):
        for wait in (0, 1):
            p = self.run_frame(timing(wait_dword=wait))
            self.assertTrue(p.complete)
            self.assertEqual(p.stores, ((0x562209, 1, 0),))
            self.assertEqual(p.intents, ())
            self.assertNotIn('00412ed0', [c[0] for c in p.calls])
            self.assertFalse(any(r[2] == 'notice_stamp_low_dword' for r in p.reads))

    def test_notice_999_skips_but_exact_1000_reaches_suffix(self):
        p = self.run_frame(timing(notice_tick_eax=999))
        self.assertTrue(p.complete)
        self.assertEqual(p.intents, ())
        p = self.run_frame(timing(), ('elapsed_tick', 'seconds_division', 'notice_tick'))
        self.assertEqual(p.needed, ('normal', 'suffix_construct'))

    def test_notice_signed_high_word_gates_negative_and_positive_delta(self):
        p = self.run_frame(timing(notice_tick_eax=0, notice_stamp_low_dword=1))
        self.assertTrue(p.complete)  # delta=-1, lowDWORD is large but high is negative.
        self.assertEqual(p.intents, ())
        p = self.run_frame(timing(notice_tick_eax=0, notice_stamp_high_dword=0xffffffff),
                           ('elapsed_tick', 'seconds_division', 'notice_tick'))
        self.assertEqual(p.needed, ('normal', 'suffix_construct'))

    def test_notice_tick_value_is_independent_and_never_reuses_elapsed_tick(self):
        f = RelogCountdownFrame()
        v = timing()
        del v['notice_tick_eax']
        p = self.run_frame(v, frame=f)
        self.assertEqual(p.needed, ('value', 'notice_tick_eax'))
        self.assertFalse(any(r[2] == 'notice_stamp_low_dword' for r in p.reads))
        # Earlier, unreached stamp values were deliberately not consumed.
        p = self.run_frame(dict(notice_tick_eax=999, notice_stamp_low_dword=0,
                                notice_stamp_high_dword=0), frame=f)
        self.assertTrue(p.complete)

    def test_number_and_empty_constructor_return_values_are_not_local_guesses(self):
        f = RelogCountdownFrame()
        p = self.run_frame(timing(), ('elapsed_tick', 'seconds_division', 'notice_tick',
                                      'suffix_construct', 'number_construct'), f)
        self.assertEqual(p.needed, ('value', 'number_construct_eax'))
        p = self.run_frame(dict(number_construct_eax=0x987), ('empty_construct',), f)
        self.assertEqual(p.needed, ('value', 'empty_construct_eax'))
        p = self.run_frame(dict(empty_construct_eax=0x654), (), f)
        self.assertEqual(p.calls[-1], ('00505cb8', ('suffix_unicode', 0x987, 0x654), 'concatenate'))

    def test_normal_format_and_cleanup_order_then_unsigned_fast_queue(self):
        p = self.run_frame(notice())
        self.assertTrue(p.complete)
        labels = [c[2] for c in p.calls]
        self.assertEqual(tuple(labels[3:13]), FORMAT_RETURNS)
        self.assertEqual(p.calls[13], ('00409fbc', ('notice_ansi', 1, 0x1300, 0x561f34), 'queue_insert'))
        self.assertEqual(p.intents, (('queue_notice', 29, 'fast'),))
        self.assertEqual(p.stores, ((0x561f48, 4, 0x1400), (0x553ce8, 4, 1200), (0x553cec, 4, 0)))
        self.assertEqual(p.calls[-1], ('004040f8', (2, 'notice_ansi'), 'notice_cleanup'))
        self.assertFalse(p.native_execution_verified or p.live_compatibility_verified)

    def test_fast_insert_return_store_survives_missing_post_tick(self):
        f = RelogCountdownFrame()
        v = notice()
        del v['post_tick_eax']
        p = self.run_frame(v, frame=f)
        self.assertEqual(p.needed, ('value', 'post_tick_eax'))
        self.assertEqual(p.stores, ((0x561f48, 4, 0x1400),))
        p = self.run_frame(dict(post_tick_eax=0xffffffff), (), f)
        self.assertEqual(p.needed, ('normal', 'notice_cleanup'))
        self.assertEqual(p.stores[-2:], ((0x553ce8, 4, 0xffffffff), (0x553cec, 4, 0)))

    def test_unsigned_size_capacity_equal_and_wrapped_size_take_slow_branch(self):
        for size, capacity in ((2, 2), (0xffffffff, 1)):
            p = self.run_frame(notice(queue_size_eax=size, queue_capacity_eax=capacity))
            self.assertTrue(p.complete)
            self.assertEqual(p.intents, (('queue_notice', 29, 'slow'),))
            self.assertNotIn('queue_end_dword', [r[2] for r in p.reads])
            self.assertNotIn(0x561f48, [r[0] for r in p.stores])
            self.assertIn(('00409e98', (0x561f34, 'end_iterator'), 'queue_end'), p.calls)

    def test_slow_insert_waits_for_distinct_iterator_and_insert_returns(self):
        f = RelogCountdownFrame()
        normals = ('elapsed_tick', 'seconds_division', 'notice_tick') + FORMAT_RETURNS
        p = self.run_frame(notice(queue_capacity_eax=0), normals, f)
        self.assertEqual(p.needed, ('normal', 'queue_end'))
        self.assertEqual(p.intents, ())
        p = self.run_frame({}, ('queue_end',), f)
        self.assertEqual(p.needed, ('normal', 'queue_insert'))
        self.assertEqual(p.intents, (('queue_notice', 29, 'slow'),))
        self.assertEqual(p.stores, ())

    def test_cleanup_gap_preserves_stamps_without_invented_queue_success(self):
        f = RelogCountdownFrame()
        p = self.run_frame(notice(), ALL_RETURNS[:-1], f)
        self.assertEqual(p.needed, ('normal', 'notice_cleanup'))
        self.assertEqual(len(p.stores), 3)
        p = self.run_frame({}, ('notice_cleanup',), f)
        self.assertTrue(p.complete)
        self.assertIs(f.advance(JailObservation()), p)

    def test_context_addresses_wrap_and_invalid_inputs_are_rejected(self):
        p = self.run_frame(dict(waiting_byte=0), frame=RelogCountdownFrame(context=0xfffffff0))
        self.assertEqual(p.reads, ((0x65, 1, 'waiting_byte'),))
        for c in (-1, 1 << 32, True):
            with self.assertRaises(ValueError):
                RelogCountdownFrame(context=c)
        with self.assertRaises(ValueError):
            RelogCountdownFrame().advance({})


class DisconnectRecoveryTests(unittest.TestCase):
    def test_disabled_action_does_not_create_countdown(self):
        f = DisconnectRecoveryFrame()
        p = f.advance(DisconnectRecoveryObservation(JailObservation(True, dict(enabled_byte=0))))
        self.assertTrue(p.complete)
        self.assertIsNone(p.countdown)
        self.assertIsNone(f.countdown)

    def test_initialized_edge_derives_countdown_entry_and_retains_action(self):
        f = DisconnectRecoveryFrame(context=0x1000)
        action = JailObservation(True, dict(enabled_byte=1, bot_running_byte=0,
                                            alarm_byte=0, initialized_byte=1))
        p = f.advance(DisconnectRecoveryObservation(action))
        self.assertFalse(p.complete)
        self.assertEqual(p.needed, ('countdown', ('value', 'waiting_byte')))
        self.assertTrue(p.action.complete)
        self.assertEqual(p.countdown.reads, ((0x1075, 1, 'waiting_byte'),))
        p = f.advance(DisconnectRecoveryObservation(countdown=JailObservation(False, dict(waiting_byte=0))))
        self.assertTrue(p.complete)
        self.assertIs(f.advance(DisconnectRecoveryObservation()), p)

    def test_relog_init_jump_exits_without_same_poll_countdown(self):
        # Fixture constants supplied explicitly; no imported TestCase duplication.
        import test_disconnect_action as fixture
        f = DisconnectRecoveryFrame()
        action = JailObservation(True, fixture.relog_values(),
                                 {k: True for k in ('tick', 'reset', 'page_index', 'select', 'relog_start')})
        p = f.advance(DisconnectRecoveryObservation(action, JailObservation(True, dict(waiting_byte=0))))
        self.assertTrue(p.complete)
        self.assertIsNone(p.countdown)
        self.assertEqual(len(p.action.stores), 6)

    def test_action_gap_cannot_be_bypassed_by_countdown_receipts(self):
        f = DisconnectRecoveryFrame()
        p = f.advance(DisconnectRecoveryObservation(
            JailObservation(True, dict(enabled_byte=1, bot_running_byte=1)),
            JailObservation(True, dict(waiting_byte=0))))
        self.assertEqual(p.needed, ('action', ('normal', 'stop_bot')))
        self.assertIsNone(f.countdown)

    def test_observation_requires_two_typed_children(self):
        with self.assertRaises(ValueError):
            DisconnectRecoveryObservation(action={})
        with self.assertRaises(ValueError):
            DisconnectRecoveryFrame().advance(JailObservation())


if __name__ == '__main__':
    unittest.main()
