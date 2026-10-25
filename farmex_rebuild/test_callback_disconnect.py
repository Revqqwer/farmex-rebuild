import unittest
from dataclasses import replace
from action_queue import QueueState
from callback_prequeue import (CallbackPreQueueObservation, CallbackPreQueueFrame,
    CallbackEntryEventObservation, plan_callback_prequeue)
from disconnect_routine import DisconnectRoutineObservation
from relog_countdown import DisconnectRecoveryObservation
from jail_protection import JailObservation
from source_callback import SourceCallbackObservation, SourceCallbackFrame
import test_callback_prequeue as callback_fixture
import test_callback_tail as tail_fixture
import test_disconnect_routine as routine_fixture
import test_dc_full_chain as sender_fixture


def bound(**values):
    return replace(callback_fixture.sample(connection_eax=0, **values),
                   disconnected=routine_fixture.routine_values())


class CallbackDisconnectTests(unittest.TestCase):
    def test_typed_child_required_and_parent_positional_api_preserved(self):
        for child in ({}, JailObservation(), 1):
            with self.assertRaises(ValueError):
                CallbackPreQueueObservation(disconnected=child)
        o = CallbackPreQueueObservation({}, {}, {})
        self.assertIsNone(o.disconnected)

    def test_standalone_plan_contains_completed_child_and_separate_parent_call(self):
        p = plan_callback_prequeue(bound())
        self.assertTrue(p.complete)
        self.assertEqual(p.status, 'connection_not_one')
        child = dict(p.children)['disconnected_worker']
        self.assertTrue(child.complete)
        self.assertFalse(child.whole_function_verified or child.native_execution_verified)
        self.assertEqual(p.calls[-1], ('00459970', (0x562194,), 'disconnected_worker'))
        self.assertEqual(p.next_source_address, 0x46fb09)
        self.assertFalse(p.queue_consumer_reached)

    def test_standalone_missing_child_prologue_cannot_be_skipped_by_parent_receipt(self):
        p = plan_callback_prequeue(replace(bound(), disconnected=DisconnectRoutineObservation()))
        self.assertEqual(p.needed, ('child', 'disconnected_worker'))
        child = dict(p.children)['disconnected_worker']
        self.assertEqual(child.needed, ('boundary', ('normal', 'prologue')))
        self.assertEqual(len(child.calls), 1)  # Entry came from reached CALL, not user entry flag.

    def test_only_full_connection_one_skips_child_for_all_other_values_it_is_bound(self):
        for connection in (0, 2, 0x101, 0xffffffff, 1):
            f = CallbackPreQueueFrame()
            o = replace(bound(), values={**bound().values, 'connection_eax': connection})
            p = f.advance(o)
            self.assertTrue(p.complete)
            self.assertEqual('disconnected_worker' in f.frames, connection != 1)
            if connection == 1:
                self.assertEqual(p.children, ())
                self.assertTrue(p.queue_consumer_reached)

    def test_not_ready_skips_nested_child_without_consuming_any_of_its_values(self):
        f = CallbackPreQueueFrame()
        p = f.advance(bound(ready_eax=0))
        self.assertTrue(p.complete)
        self.assertEqual(p.status, 'not_ready')
        self.assertEqual(f.frames, {})

    def test_frame_derives_fixed_source_context_and_child_entry_but_not_normal_return(self):
        f = CallbackPreQueueFrame()
        o = replace(bound(), disconnected=DisconnectRoutineObservation())
        p = f.advance(o)
        self.assertEqual(p.needed, ('child', 'disconnected_worker'))
        child = f.frames['disconnected_worker']
        self.assertEqual(child.context, 0x562194)
        self.assertTrue(child.entered)
        self.assertFalse(child.prologue)
        self.assertNotIn('disconnected_worker', f.observation.normal_returns)

    def test_sender_child_gap_blocks_callback_exit_and_later_queue_reads(self):
        f = CallbackPreQueueFrame()
        periodic = sender_fixture.DCFullChainTests().observation()
        periodic = replace(periodic, action=replace(periodic.action, transfers={}))
        child = replace(routine_fixture.routine_values(), periodic=periodic)
        p = f.advance(replace(bound(), disconnected=child))
        self.assertEqual(p.needed, ('child', 'disconnected_worker'))
        cp = dict(p.children)['disconnected_worker']
        self.assertEqual(cp.needed[0], 'periodic')
        self.assertNotIn('pending_byte', f.observation.values)
        self.assertFalse(p.queue_consumer_reached)

    def test_complete_child_still_waits_for_distinct_disconnected_worker_return(self):
        f = CallbackPreQueueFrame()
        o = bound()
        o = replace(o, normal_returns={**o.normal_returns, 'disconnected_worker': False})
        p = f.advance(o)
        self.assertEqual(p.needed, ('normal', 'disconnected_worker'))
        self.assertTrue(dict(p.children)['disconnected_worker'].complete)
        child = f.frames['disconnected_worker']
        p = f.advance(CallbackPreQueueObservation(normal_returns={'disconnected_worker': True}))
        self.assertTrue(p.complete)
        self.assertIs(f.frames['disconnected_worker'], child)

    def test_completed_sender_write_prefix_survives_outer_callback_wait(self):
        f = CallbackPreQueueFrame()
        child = replace(routine_fixture.routine_values(),
                        periodic=sender_fixture.DCFullChainTests().observation())
        o = replace(bound(), disconnected=child,
                    normal_returns={**bound().normal_returns, 'disconnected_worker': False})
        p = f.advance(o)
        cp = dict(p.children)['disconnected_worker']
        self.assertEqual(len(cp.periodic.write_intents), 2)
        self.assertEqual(cp.periodic.parent.stores, ((0x553ce4, 4, 300010),))
        p = f.advance(CallbackPreQueueObservation(normal_returns={'disconnected_worker': True}))
        self.assertTrue(p.complete)
        self.assertIs(dict(p.children)['disconnected_worker'], cp)

    def test_bound_missing_child_cannot_be_replaced_by_opaque_receipt(self):
        f = CallbackPreQueueFrame()
        p = f.advance(replace(bound(), disconnected=DisconnectRoutineObservation()))
        p = f.advance(CallbackPreQueueObservation(normal_returns={'disconnected_worker': True}))
        self.assertFalse(p.complete)
        self.assertEqual(p.needed, ('child', 'disconnected_worker'))

    def test_late_binding_after_opaque_worker_consumption_is_rejected(self):
        f = CallbackPreQueueFrame()
        p = f.advance(callback_fixture.sample(connection_eax=0))
        self.assertTrue(p.complete)
        with self.assertRaisesRegex(ValueError, 'retroactively'):
            f.advance(bound())

    def test_binding_can_begin_while_opaque_worker_return_is_still_missing(self):
        f = CallbackPreQueueFrame()
        o = callback_fixture.sample(connection_eax=0)
        p = f.advance(replace(o, normal_returns={**o.normal_returns, 'disconnected_worker': False}))
        self.assertEqual(p.needed, ('normal', 'disconnected_worker'))
        p = f.advance(bound())
        self.assertTrue(p.complete)
        self.assertIn('disconnected_worker', f.frames)

    def test_special_path_keeps_flags_in_child_without_fabricating_callback_recovery(self):
        child = routine_fixture.routine_values(special=True)
        f = CallbackPreQueueFrame()
        p = f.advance(replace(bound(), disconnected=child))
        self.assertTrue(p.complete)
        cp = dict(p.children)['disconnected_worker']
        self.assertIn((0x562208, 1, 1), cp.special.action.stores)
        self.assertNotIn('pending_byte', f.observation.values)
        self.assertEqual(p.stores, ())

    def test_next_callback_requires_fresh_pending_observation_not_prior_child_flag(self):
        f = CallbackPreQueueFrame()
        p = f.advance(replace(bound(), disconnected=routine_fixture.routine_values(special=True)))
        self.assertTrue(p.complete)
        fresh = CallbackPreQueueFrame()
        o = callback_fixture.sample(connection_eax=1)
        v = dict(o.values)
        del v['pending_byte']
        p = fresh.advance(replace(o, values=v))
        self.assertEqual(p.needed, ('value', 'pending_byte'))

    def test_source_callback_composition_still_requires_fresh_early_exit_queue(self):
        f = SourceCallbackFrame()
        o = SourceCallbackObservation(CallbackEntryEventObservation(pre=bound()), tail_fixture.sample())
        p = f.advance(o)
        self.assertEqual(p.needed, ('queue_state', 'early_tail'))
        self.assertTrue(dict(p.entry_event.pre.children)['disconnected_worker'].complete)
        p = f.advance(replace(o, early_tail_queue=QueueState()))
        self.assertTrue(p.complete)
        self.assertEqual(p.tail.entry, 0x46fb09)
        self.assertTrue(p.normal_return_receipt)
        self.assertFalse(p.whole_callback_verified or p.live_compatibility_verified)

    def test_source_callback_cannot_skip_child_gap_using_tail_receipts(self):
        f = SourceCallbackFrame()
        pre = replace(bound(), disconnected=DisconnectRoutineObservation())
        p = f.advance(SourceCallbackObservation(CallbackEntryEventObservation(pre=pre),
                         tail_fixture.sample(), QueueState()))
        self.assertFalse(p.complete)
        self.assertEqual(p.needed, ('entry_event', ('pre', ('child', 'disconnected_worker'))))
        self.assertIsNone(f.tail)


if __name__ == '__main__':
    unittest.main()
