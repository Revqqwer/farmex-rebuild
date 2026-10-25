import unittest
from dataclasses import replace
from ms_achievement import *

def request(gate=1,tick=100,normal=True):
 return AchievementRequestObservation(QueueAttempt(gate,tick,normal),{'frame_setup':True,'copy':True,'return':True})

def sample(gate=1):
 return MSAchievementObservation({i:request(gate,100+i) for i in range(11)},{i:True for i in range(11)},True)

class AchievementTests(unittest.TestCase):
 def test_exact_eleven_ID_order_context_payload_and_independent_timestamps(self):
  p=MSAchievementFrame().advance(sample());self.assertTrue(p.complete)
  self.assertEqual([c[1] for c in p.calls],[(x,0x561ef8) for x in ACHIEVEMENT_IDS])
  self.assertEqual([r.payload for r in p.queue.records],[b'\x99\x02'+x.to_bytes(4,'little') for x in ACHIEVEMENT_IDS])
  self.assertEqual([r.created_tick for r in p.queue.records],list(range(100,111)))
  self.assertTrue(all(r.delay_dword==0 and len(r.payload)==6 for r in p.queue.records))
  self.assertFalse(p.reward_verified);self.assertFalse(p.delivery_verified)

 def test_serializer_accepts_zero_and_full_DWORD_without_invented_lookup(self):
  for value in (0,0xffffffff,0x11223344):
   p=AchievementRequestFrame(value).advance(request());self.assertTrue(p.complete)
   self.assertEqual(p.payload[2:],value.to_bytes(4,'little'))

 def test_gate_zero_finishes_all_calls_without_any_queue_records(self):
  p=MSAchievementFrame().advance(sample(0));self.assertTrue(p.complete)
  self.assertEqual(p.completed_invocations,tuple(range(11)));self.assertEqual(p.queue.records,())

 def test_missing_first_helper_stops_before_any_later_calls(self):
  o=sample();r=dict(o.requests);r[0]=AchievementRequestObservation()
  p=MSAchievementFrame().advance(replace(o,requests=r));self.assertFalse(p.complete)
  self.assertEqual(len(p.calls),1);self.assertEqual(p.needed,('request',0));self.assertEqual(p.queue.records,())

 def test_gate_and_copy_prefix_retained_while_waiting_for_tick(self):
  f=AchievementRequestFrame(1);p=f.advance(request(1,None));self.assertFalse(p.complete)
  p=f.advance(AchievementRequestObservation(QueueAttempt(0,99,True),{'return':True}))
  self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1);self.assertEqual(p.queue.records[0].created_tick,99)

 def test_committed_record_not_repeated_when_enqueue_normal_or_outer_return_missing(self):
  f=MSAchievementFrame();o=sample();r=dict(o.requests);r[0]=request(normal=False)
  p=f.advance(replace(o,requests=r));self.assertFalse(p.complete);self.assertEqual(len(p.queue.records),1)
  returns=dict(o.caller_returns);returns[0]=False
  p=f.advance(replace(o,caller_returns=returns));self.assertFalse(p.complete)
  self.assertEqual(p.needed,('caller_return',0));self.assertEqual(len(p.queue.records),1)
  p=f.advance(o);self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),11)

 def test_final_event_return_separate_and_cached_completion_has_no_repeat(self):
  f=MSAchievementFrame();o=sample();p=f.advance(replace(o,event_returned=False))
  self.assertFalse(p.complete);self.assertEqual(len(p.queue.records),11)
  p=f.advance(MSAchievementObservation(event_returned=True));self.assertTrue(p.complete)
  self.assertIs(f.advance(sample()),p);self.assertEqual(len(p.queue.records),11)

 def test_each_invocation_gate_is_independent(self):
  o=sample();r=dict(o.requests);r[4]=request(0,None)
  p=MSAchievementFrame().advance(replace(o,requests=r));self.assertTrue(p.complete)
  self.assertEqual(len(p.queue.records),10)
  self.assertNotIn(b'\x99\x02'+ACHIEVEMENT_IDS[4].to_bytes(4,'little'),[x.payload for x in p.queue.records])

if __name__=='__main__':unittest.main()
