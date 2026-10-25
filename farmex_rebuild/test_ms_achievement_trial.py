import json,unittest
from ms_achievement_trial import *

class AchievementTrialTests(unittest.TestCase):
 def test_empty_sample_waits_and_explicit_example_finishes_eleven(self):
  t=AchievementTrial();p=t.step('{}');self.assertFalse(p.complete);self.assertEqual(p.queue.records,())
  p=t.step(example_achievement_sample());self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),11)

 def test_reached_only_parser_ignores_bad_later_request_and_unreached_attempt(self):
  t=AchievementTrial();p=t.step(json.dumps({'requests':{'0':{'attempt':'not reached'},'1':'later bad'},'caller_returns':'later bad'}))
  self.assertFalse(p.complete);self.assertEqual(p.missing,'frame_setup normal return')
  with self.assertRaises(ValueError):t.step(json.dumps({'requests':{'0':{'normal_returns':{'frame_setup':True,'copy':True},'attempt':'now reached'}}}))

 def test_only_new_fields_needed_across_gate_tick_and_return_gaps(self):
  t=AchievementTrial()
  t.step(json.dumps({'requests':{'0':{'normal_returns':{'frame_setup':True,'copy':True},'attempt':{'gate':1}}}}))
  p=t.step(json.dumps({'requests':{'0':{'attempt':{'tick':9}}}}));self.assertFalse(p.complete)
  self.assertEqual(len(p.queue.records),1);self.assertEqual(p.missing,'enqueue normal return')
  p=t.step(json.dumps({'requests':{'0':{'attempt':{'normal_returned':True},'normal_returns':{'return':True}}}}))
  self.assertEqual(p.needed,('caller_return',0));self.assertEqual(len(p.queue.records),1)
  p=t.step(json.dumps({'caller_returns':{'0':True}}));self.assertEqual(p.needed,('request',1))
  self.assertEqual(len(p.queue.records),1)

 def test_zero_gate_does_not_parse_unneeded_bad_tick(self):
  r=json.loads(example_achievement_sample())
  for item in r['requests'].values():item['attempt'].update(gate=0,tick='unused invalid')
  p=AchievementTrial().step(json.dumps(r));self.assertTrue(p.complete);self.assertEqual(p.queue.records,())

 def test_bad_JSON_clears_stale_last_and_preserves_committed_prefix(self):
  t=AchievementTrial();r=json.loads(example_achievement_sample());r['requests']['0']['attempt']['normal_returned']=False
  p=t.step(json.dumps(r));self.assertEqual(len(p.queue.records),1)
  with self.assertRaises(ValueError):t.step('{bad')
  self.assertIsNone(t.last);self.assertEqual(len(t.frame.queue.records),1)
  self.assertEqual(len(t.step(example_achievement_sample()).queue.records),11)

 def test_final_event_return_and_new_event_queue_preservation_are_explicit(self):
  t=AchievementTrial();r=json.loads(example_achievement_sample());r['event_returned']=False
  p=t.step(json.dumps(r));self.assertEqual(p.needed,('event_return',None))
  p=t.step('{"event_returned":true}');self.assertTrue(p.complete)
  t.reset(p.queue);p=t.step(example_achievement_sample());self.assertEqual(len(p.queue.records),22)
  t.reset();self.assertEqual(t.frame.queue.records,())

if __name__=='__main__':unittest.main()
