import unittest
from merchant_scan_collection import (
    MerchantCollectionFrame, MerchantCollectionState, MerchantProbe, MerchantRecord,
    collect_merchants,
)


def actor(entity=42, **changes):
    values=dict(pointer=123,active_byte=1,x_float=1.9,y_float=-1.9,
                buy_byte=0,distance_after_truncation=9.5,entity_id_dword=entity)
    values.update(changes)
    return MerchantProbe(**values)


def empty():return {i:MerchantProbe(0) for i in range(5001)}


class CollectionFrameTests(unittest.TestCase):
    def test_resume_missing_lookup_preserves_queue_and_visited_once(self):
        initial=MerchantCollectionState((MerchantRecord(9,7,0),),(9,),True)
        frame=MerchantCollectionFrame(initial)
        first=frame.advance({0:actor()},True,False)
        self.assertEqual(first.state.queue,(MerchantRecord(42,123,0),))
        self.assertEqual(first.stopped_probe,1)
        for _ in range(3):self.assertEqual(frame.advance(),first)
        tail=empty();tail.pop(0);tail[1]=actor(43)
        done=frame.advance(tail)
        self.assertEqual(done.status,'collected')
        self.assertEqual(done.state.visited_ids,(9,42,43))
        self.assertEqual(tuple(r.entity_id for r in done.state.queue),(42,43))
        self.assertTrue(done.state.awaiting_merchant_reply)
        self.assertEqual(done.collected_count,2)

    def test_reached_fields_frozen_but_unknown_and_unreached_fields_fresh(self):
        frame=MerchantCollectionFrame()
        first=frame.advance({0:actor(y_float=None,entity_id_dword=10)})
        self.assertIn('554010',first.reason)
        self.assertNotIn((0,'entity_id_dword'),frame.consumed_observations)
        p=empty();p[0]=actor(99,pointer=456,active_byte=0,x_float=1e30)
        done=frame.advance(p,True,False)
        self.assertEqual(done.status,'collected')
        self.assertEqual(done.state.queue,(MerchantRecord(99,123,0),))
        self.assertEqual(frame.consumed_observations[(0,'x_float')],1.9)

    def test_null_and_inactive_do_not_require_later_fields(self):
        p=empty();p[1]=MerchantProbe(8,active_byte=0)
        frame=MerchantCollectionFrame();done=frame.advance(p)
        self.assertEqual(done.status,'collected')
        self.assertNotIn((1,'x_float'),frame.consumed_observations)
        self.assertNotIn((None,'normal_enabled'),frame.consumed_observations)

    def test_missing_flag_can_arrive_after_entity_observation(self):
        frame=MerchantCollectionFrame();p=empty();p[0]=actor()
        self.assertEqual(frame.advance(p).reason,'flag:+c')
        done=frame.advance(p,normal_enabled=True)
        self.assertEqual(done.status,'collected')
        self.assertEqual(done.collected_count,1)

    def test_new_frame_does_not_inherit_other_invocation_cache(self):
        first=MerchantCollectionFrame();p=empty();p[0]=actor()
        done=first.advance(p,True,False)
        second=MerchantCollectionFrame(done.state)
        waiting=second.advance()
        self.assertEqual(waiting.status,'needs_observation')
        self.assertEqual(waiting.state.queue,())
        self.assertEqual(waiting.state.visited_ids,(42,))

    def test_final_lookup_and_terminal_outcome(self):
        p=empty();p.pop(5000);frame=MerchantCollectionFrame()
        self.assertEqual(frame.advance(p).stopped_probe,5000)
        done=frame.advance({5000:actor()},True,False)
        self.assertTrue(frame.terminal)
        self.assertIs(frame.advance({0:actor(7)}),done)
        self.assertIs(frame.abort('late'),done)

    def test_abort_keeps_partial_evidence_without_claiming_return(self):
        frame=MerchantCollectionFrame();frame.advance({0:actor()},True,False)
        done=frame.abort('capture interrupted')
        self.assertEqual(done.status,'aborted')
        self.assertEqual(done.collected_count,1)
        self.assertEqual(frame.advance(empty(),True,True),done)
        self.assertEqual(frame.abort_reason,'capture interrupted')

    def test_observation_view_immutable_and_input_validation(self):
        frame=MerchantCollectionFrame();frame.advance({0:MerchantProbe(0)})
        with self.assertRaises(TypeError):frame.consumed_observations[(0,'pointer')]=3
        with self.assertRaises(ValueError):frame.advance({5001:MerchantProbe(0)})
        with self.assertRaises(ValueError):frame.advance(normal_enabled=1)
        with self.assertRaises(ValueError):frame.abort('')

    def test_full_snapshot_matches_existing_collection_semantics(self):
        p=empty();p[0]=actor(0x1002a);p[1]=actor(42);p[5000]=actor(77,buy_byte=1)
        initial=MerchantCollectionState((MerchantRecord(8,4,0),),(8,))
        expected=collect_merchants(p,True,True,initial)
        self.assertEqual(MerchantCollectionFrame(initial).advance(p,True,True),expected)


if __name__=='__main__':unittest.main()
