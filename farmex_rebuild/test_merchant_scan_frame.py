import unittest
from merchant_scan import ScanSnapshot as O,ScanState as S,MerchantScanFrame


def arrived(**kw):
    values=dict(route_enabled=True,route_count=2,distance_returned=True,distance_status_word=0x4000,
                actor_raw_byte_554020=0,busy_0f=False,pending_count=0)
    values.update(kw);return O(**values)


class ScanFrameTests(unittest.TestCase):
    def test_consume_request_once_then_post_clock_without_reconsume(self):
        f=MerchantScanFrame();p=f.advance(O(route_enabled=False,busy_0f=False,pending_count=1,now_ms=1000))
        self.assertEqual([r.target for r in p.new_return_requests],['004bf5d0'])
        token=p.pending_return.token;self.assertFalse(p.pending_return.executable_native_command)
        q=f.advance();self.assertEqual(q.new_return_requests,());self.assertEqual(q.pending_return.token,token)
        r=f.advance(O(consume_returned=True));self.assertIsNone(r.pending_return)
        self.assertEqual(r.decision.reason,'post_consume_GetTickCount');self.assertEqual(r.state.last_scan_qword,0)
        done=f.advance(O(now_ms=9999,post_consume_now_ms=1234))
        self.assertTrue(done.complete);self.assertEqual(done.state.last_scan_qword,1234)
        self.assertEqual(done.new_logical_call_intents,());self.assertEqual(done.consumed_observations['now_ms'],1000)

    def test_waiting_is_terminal_for_this_invocation_not_new_tick(self):
        f=MerchantScanFrame(S(last_scan_qword=1000))
        p=f.advance(O(route_enabled=False,busy_0f=False,pending_count=1,now_ms=1049))
        self.assertTrue(p.complete);self.assertTrue(p.terminal);self.assertEqual(p.status,'waiting')
        q=f.advance(O(now_ms=2000,consume_returned=True,post_consume_now_ms=2001))
        self.assertEqual(q.status,'waiting');self.assertEqual(q.state.last_scan_qword,1000)
        self.assertNotIn('consume_returned',q.consumed_observations)

    def test_return_requests_are_scoped_to_distinct_invocations(self):
        o=O(route_enabled=False,busy_0f=False,pending_count=0)
        a=MerchantScanFrame().advance(o);b=MerchantScanFrame().advance(o)
        self.assertNotEqual(a.pending_return.token,b.pending_return.token)

    def test_route_increment_is_not_replayed_as_another_increment(self):
        f=MerchantScanFrame(S(route_index=1));p=f.advance(arrived())
        self.assertEqual(p.pending_return.target,'004bf040')
        q=f.advance(O(collect_returned=True,collect_return_4bf040=0))
        self.assertEqual(q.state.route_index,2);self.assertEqual(q.decision.reason,'fresh_route_count_after_collect')
        r=f.advance(O(route_count=999,route_count_after_collect=2,save_on_finish_0e=False))
        self.assertEqual(r.state.route_index,2);self.assertEqual(r.pending_return.target,'004be6dc')
        end=f.advance(O(stop_returned=True));self.assertTrue(end.complete)
        self.assertEqual(end.state.route_index,2);self.assertFalse(end.state.active)

    def test_save_then_stop_requests_each_once_and_no_parent_return_invention(self):
        f=MerchantScanFrame(S(route_index=1));p=f.advance(arrived(collect_returned=True,collect_return_4bf040=0,
            route_count_after_collect=2,save_on_finish_0e=True))
        self.assertEqual(p.pending_return.target,'004b99f8');self.assertTrue(p.state.active)
        q=f.advance(O(export_returned=False));self.assertEqual(q.new_return_requests,())
        r=f.advance(O(export_returned=True));self.assertEqual(r.pending_return.target,'004be6dc')
        end=f.advance(O(stop_returned=True));self.assertTrue(end.complete)
        self.assertEqual(end.new_return_requests,());self.assertFalse(end.native_execution_verified)

    def test_unused_EAX_not_cached_before_normal_return(self):
        f=MerchantScanFrame();f.advance(arrived(collect_return_4bf040=0))
        p=f.advance(O(collect_returned=True,collect_return_4bf040=1))
        self.assertTrue(p.complete);self.assertEqual(p.state.route_index,0)
        self.assertNotIn('route_count_after_collect',p.consumed_observations)

    def test_unreached_actor_value_not_frozen_during_distance_wait(self):
        f=MerchantScanFrame();p=f.advance(O(route_enabled=True,route_count=2,actor_raw_byte_554020=0))
        self.assertEqual(p.pending_return.target,'00460548')
        q=f.advance(O(distance_returned=True,distance_status_word=0x4000,actor_raw_byte_554020=1))
        self.assertTrue(q.complete);self.assertEqual(q.status,'actor_or_busy_gate')
        self.assertNotIn('busy_0f',q.consumed_observations)

    def test_unknown_status_WORD_may_arrive_before_scalar_choice(self):
        f=MerchantScanFrame();p=f.advance(O(route_enabled=True,route_count=2,distance_returned=True))
        self.assertFalse(p.complete);self.assertNotIn('distance_status_word',p.consumed_observations)
        q=f.advance(O(distance_status_word=0x4500,actor_raw_byte_554020=1))
        self.assertTrue(q.complete);self.assertEqual(q.status,'actor_or_busy_gate')

    def test_scalar_fallback_choice_is_frozen_once_consumed(self):
        f=MerchantScanFrame();p=f.advance(O(route_enabled=True,route_count=2,distance_returned=True,selected_point_distance=2))
        self.assertEqual(p.pending_return.target,'004646b4')
        self.assertIn('distance_status_word',p.consumed_observations)
        q=f.advance(O(distance_status_word=0x4500,selected_point_distance=float('nan'),move_returned=True))
        self.assertTrue(q.complete);self.assertEqual(q.decision.reason,'move_to_route_point')

    def test_captured_completed_calls_do_not_create_return_requests(self):
        f=MerchantScanFrame(S(route_index=1))
        p=f.advance(arrived(collect_returned=True,collect_return_4bf040=0,route_count_after_collect=2,
            save_on_finish_0e=True,export_returned=True,stop_returned=True))
        self.assertTrue(p.complete);self.assertEqual(p.new_return_requests,())
        self.assertEqual(p.new_logical_call_intents,('004bf040','004b99f8','004be6dc:stop_completed'))

    def test_abort_keeps_prefix_and_prevents_reissue(self):
        f=MerchantScanFrame();p=f.advance(arrived(collect_returned=True,collect_return_4bf040=0))
        self.assertEqual(p.state.route_index,1)
        q=f.abort('external child failure');self.assertTrue(q.terminal);self.assertFalse(q.complete)
        self.assertEqual(q.status,'aborted');self.assertEqual(q.state.route_index,1)
        self.assertIsNone(q.pending_return)
        r=f.advance(O(route_count_after_collect=100));self.assertEqual(r.status,'aborted')
        self.assertEqual(r.new_logical_call_intents,())

    def test_bounds_exception_is_terminal_without_normal_completion(self):
        f=MerchantScanFrame(S(route_index=1));p=f.advance(O(route_enabled=True,route_count=1))
        self.assertTrue(p.terminal);self.assertFalse(p.complete)
        self.assertEqual(p.status,'source_bounds_exception')
        self.assertEqual(f.advance(O(route_count=5)).status,'source_bounds_exception')


if __name__=='__main__':unittest.main()
