import unittest
from dataclasses import replace
from merchant_scan import ScanSnapshot, ScanState, merchant_scan_step


class MerchantScanTests(unittest.TestCase):
    def snapshot(self, **changes):
        values = dict(now_ms=1000, route_enabled=True, busy_0f=False, pending_count=0,
                      route_count=2, selected_point_distance=1.5, actor_raw_byte_554020=0,
                      collect_return_4bf040=0, save_on_finish_0e=True,route_count_after_collect=2,
                      post_consume_now_ms=1007,distance_returned=True,move_returned=True,
                      collect_returned=True,consume_returned=True,export_returned=True,stop_returned=True)
        values.update(changes)
        return ScanSnapshot(**values)

    def test_distance_equality_arrives(self):
        result = merchant_scan_step(self.snapshot())
        self.assertEqual(result.state.route_index, 1)
        result = merchant_scan_step(self.snapshot(selected_point_distance=1.50001))
        self.assertEqual(result.calls, ('004646b4',))
        self.assertEqual(result.state.route_index, 0)

    def test_last_point_save_then_stop(self):
        result = merchant_scan_step(self.snapshot(), ScanState(route_index=1))
        self.assertEqual(result.calls, ('004bf040', '004b99f8', '004be6dc:stop_completed'))
        self.assertFalse(result.state.active)

    def test_finish_without_save(self):
        result = merchant_scan_step(self.snapshot(save_on_finish_0e=False), ScanState(route_index=1))
        self.assertNotIn('004b99f8', result.calls)

    def test_bounds_exception_is_not_route_wrap(self):
        for count in (0, 1):
            result = merchant_scan_step(self.snapshot(route_count=count), ScanState(route_index=1))
            self.assertEqual(result.status, 'source_bounds_exception')
            self.assertEqual(result.state.route_index, 1)

    def test_pending_50ms_equality(self):
        state = ScanState(last_scan_qword=1000)
        before = merchant_scan_step(self.snapshot(now_ms=1049, pending_count=1), state)
        self.assertEqual(before.status, 'waiting')
        after = merchant_scan_step(self.snapshot(now_ms=1050,post_consume_now_ms=1080,pending_count=1), state)
        self.assertEqual(after.calls, ('004bf5d0',))
        self.assertEqual(after.state.last_scan_qword, 1080)

    def test_signed_qword_future_timestamp_waits(self):
        result = merchant_scan_step(self.snapshot(pending_count=1), ScanState(last_scan_qword=2000))
        self.assertEqual(result.status, 'waiting')

    def test_pending_does_not_advance_route(self):
        result = merchant_scan_step(self.snapshot(pending_count=2))
        self.assertEqual(result.state.route_index, 0)

    def test_collect_nonzero_keeps_point(self):
        result = merchant_scan_step(self.snapshot(collect_return_4bf040=1))
        self.assertEqual(result.state.route_index, 0)

    def test_unknown_collect_preserves_call_plan(self):
        result = merchant_scan_step(self.snapshot(collect_return_4bf040=None))
        self.assertEqual(result.status, 'needs_observation')
        self.assertEqual(result.calls, ('004bf040',))

    def test_unknown_save_preserves_source_index_increment(self):
        result = merchant_scan_step(self.snapshot(save_on_finish_0e=None), ScanState(route_index=1))
        self.assertEqual(result.status, 'needs_observation')
        self.assertEqual(result.state.route_index, 2)
        self.assertTrue(result.state.active)

    def test_no_route_idle_collection_does_not_require_return(self):
        result = merchant_scan_step(self.snapshot(route_enabled=False, route_count=None,
                                                  collect_return_4bf040=None))
        self.assertEqual(result.calls, ('004bf040',))
        self.assertEqual(result.status, 'local_step')

    def test_gates_short_circuit(self):
        result = merchant_scan_step(self.snapshot(actor_raw_byte_554020=1, busy_0f=None))
        self.assertEqual(result.status, 'actor_or_busy_gate')
        result = merchant_scan_step(self.snapshot(route_enabled=False, busy_0f=True, pending_count=None))
        self.assertEqual(result.status, 'busy')

    def test_own_stopped_guard(self):
        result = merchant_scan_step(ScanSnapshot(0), ScanState(active=False))
        self.assertEqual(result.status, 'idle')

    def test_nan_and_types_rejected(self):
        for values in ({'selected_point_distance': float('nan')}, {'route_enabled': 1},
                       {'pending_count': -1}, {'now_ms': 1 << 32}):
            with self.assertRaises(ValueError):
                self.snapshot(**values)

    def test_consumer_return_and_post_tick_are_independent(self):
        initial=ScanState(last_scan_qword=10)
        p=merchant_scan_step(self.snapshot(pending_count=1,consume_returned=False,post_consume_now_ms=9999),initial)
        self.assertEqual(p.status,'needs_observation');self.assertEqual(p.state.last_scan_qword,10)
        self.assertEqual(p.reason,'normal_return:004bf5d0')
        q=merchant_scan_step(self.snapshot(pending_count=1,post_consume_now_ms=None),initial)
        self.assertEqual(q.state.last_scan_qword,10);self.assertEqual(q.reason,'post_consume_GetTickCount')

    def test_no_route_consumer_also_stamps_fresh_post_tick(self):
        p=merchant_scan_step(self.snapshot(route_enabled=False,pending_count=1,now_ms=1000,post_consume_now_ms=1200))
        self.assertEqual(p.state.last_scan_qword,1200)

    def test_post_tick_wrap_is_zero_extended(self):
        p=merchant_scan_step(self.snapshot(pending_count=1,now_ms=0xfffffffe,post_consume_now_ms=2))
        self.assertEqual(p.state.last_scan_qword,2)

    def test_missing_clock_is_not_needed_before_consumer_branch(self):
        p=merchant_scan_step(self.snapshot(now_ms=None,route_enabled=False,pending_count=0))
        self.assertEqual(p.status,'local_step')
        q=merchant_scan_step(self.snapshot(now_ms=None,pending_count=1))
        self.assertEqual(q.status,'needs_observation');self.assertEqual(q.calls,())

    def test_collect_EAX_zero_does_not_replace_normal_return(self):
        p=merchant_scan_step(self.snapshot(collect_return_4bf040=0,collect_returned=None))
        self.assertEqual(p.state.route_index,0);self.assertEqual(p.reason,'normal_return:004bf040')
        q=merchant_scan_step(self.snapshot(route_enabled=False,collect_returned=False))
        self.assertEqual(q.status,'needs_observation')

    def test_fresh_route_count_can_grow_or_shrink(self):
        p=merchant_scan_step(self.snapshot(route_count_after_collect=4),ScanState(route_index=1))
        self.assertEqual(p.state.route_index,2);self.assertTrue(p.state.active)
        self.assertEqual(p.calls,('004bf040',))
        q=merchant_scan_step(self.snapshot(route_count=10,route_count_after_collect=0),ScanState(route_index=1))
        self.assertEqual(q.status,'completed');self.assertFalse(q.state.active)

    def test_unknown_fresh_count_keeps_completed_index_increment(self):
        p=merchant_scan_step(self.snapshot(route_count_after_collect=None))
        self.assertEqual(p.state.route_index,1);self.assertEqual(p.reason,'fresh_route_count_after_collect')

    def test_export_return_required_before_stop_is_attempted(self):
        p=merchant_scan_step(self.snapshot(export_returned=False),ScanState(route_index=1))
        self.assertEqual(p.calls,('004bf040','004b99f8'));self.assertEqual(p.status,'needs_observation')
        self.assertEqual(p.state.route_index,2)

    def test_stop_return_required_before_own_lifecycle_completed(self):
        p=merchant_scan_step(self.snapshot(stop_returned=None),ScanState(route_index=1))
        self.assertEqual(p.status,'needs_observation');self.assertTrue(p.state.active)
        self.assertEqual(p.calls[-1],'004be6dc:stop_completed')

    def test_x87_unordered_and_equality_take_arrival_path(self):
        nan=merchant_scan_step(self.snapshot(selected_point_distance=float('nan'),distance_status_word=0x4500))
        self.assertEqual(nan.state.route_index,1)
        for word in (0x4500,0x4000,0x0100):
            p=merchant_scan_step(self.snapshot(selected_point_distance=None,distance_status_word=word))
            self.assertEqual(p.state.route_index,1)
        q=merchant_scan_step(self.snapshot(selected_point_distance=None,distance_status_word=0))
        self.assertEqual(q.calls,('004646b4',))

    def test_distance_and_move_returns_are_not_implicit(self):
        p=merchant_scan_step(self.snapshot(distance_returned=False))
        self.assertEqual(p.status,'needs_observation');self.assertEqual(p.calls,())
        q=merchant_scan_step(self.snapshot(selected_point_distance=2,move_returned=False))
        self.assertEqual(q.status,'needs_observation');self.assertEqual(q.calls,('004646b4',))

    def test_actor_field_name_and_byte_width_match_source(self):
        names=ScanSnapshot.__dataclass_fields__
        self.assertIn('actor_raw_byte_554020',names);self.assertNotIn('actor_raw_byte_55402c',names)
        with self.assertRaises(ValueError):self.snapshot(actor_raw_byte_554020=256)


if __name__ == '__main__':
    unittest.main()
