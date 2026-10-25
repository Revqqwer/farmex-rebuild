import json,unittest
from event_join_trial import *

def panel(*enabled):return {path:key in enabled for path,(key,name,offset,slot) in zip(EVENT_JOIN_INPUTS,EVENT_FIELDS)}

class EventJoinTrialTests(unittest.TestCase):
 def test_real_flags_cannot_be_overridden_and_defaults_wait(self):
  v=panel('chaos');t=EventJoinTrial(lambda:(v,{}));p=t.step('{"values":{"first_chaos_byte":0}}')
  self.assertEqual(p.needed,('normal','entry_setup'));self.assertTrue(t.settings.complete)
  p=t.step(example_event_sample(event_snapshot(v)));self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1)
 def test_first_group_example_and_unchanged_panel_reuse_one_invocation(self):
  v=panel('chaos','bdw','jr');t=EventJoinTrial(lambda:(v,{}));text=example_event_sample(event_snapshot(v))
  p=t.step(text);self.assertEqual([label for label,child in p.children],['chaos_join']);self.assertEqual(p.status,'second_group_wait')
  self.assertEqual(t.step(text).queue,p.queue);self.assertEqual(len(p.queue.records),1)
 def test_second_group_examples_cover_FT_UTC_and_JR(self):
  for kind,count,length in (('ft',2,17),('utc',2,18),('jr',3,18)):
   v=panel(kind);t=EventJoinTrial(lambda:(v,{}));p=t.step(example_event_sample(event_snapshot(v)))
   self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),count)
   self.assertEqual(len(p.queue.records[0].payload),10)
   self.assertTrue(all(len(r.payload)==length for r in p.queue.records[1:]))
 def test_packet_enqueue_clock_gap_and_helper_outer_returns_resume(self):
  v=panel('bdw');t=EventJoinTrial(lambda:(v,{}));d=json.loads(example_event_sample(event_snapshot(v)))
  child=d['packet_children']['bdw_join'];del child['attempt']['tick']
  p=t.step(json.dumps(d));self.assertEqual(p.needed,('child','bdw_join'));self.assertEqual(p.queue.records,())
  child['attempt']['gate']=0;child['attempt']['tick']=333;child['normal_returns']['return']=False
  p=t.step(json.dumps(d));self.assertEqual(len(p.queue.records),1);self.assertFalse(p.complete)
  child['normal_returns']['return']=True;d['normal_returns']['bdw_join']=False
  p=t.step(json.dumps(d));self.assertEqual(p.needed,('normal','bdw_join'));self.assertEqual(p.stores,())
  d['normal_returns']['bdw_join']=True;self.assertTrue(t.step(json.dumps(d)).complete)
  self.assertEqual(t.last.queue.records[0].created_tick,333)
 def test_changed_panel_rejects_stale_example_and_preserves_committed_own_queue(self):
  v=panel('chaos');t=EventJoinTrial(lambda:(v,{}));text=example_event_sample(event_snapshot(v));t.step(text);frame=t.frame
  v.update(panel('jr'))
  with self.assertRaisesRegex(ValueError,'Panel değişti'):t.step(text)
  self.assertIsNot(t.frame,frame);self.assertIsNone(t.last);self.assertEqual(len(t.frame.queue.records),1)
  p=t.step(example_event_sample(event_snapshot(v)));self.assertEqual(len(p.queue.records),4)
  t.reset();self.assertIsNone(t.frame)
 def test_unreached_bad_capture_ignored_and_reached_bad_type_clears_result(self):
  v=panel('ft');t=EventJoinTrial(lambda:(v,{}))
  self.assertEqual(t.step('{"packet_children":"future"}').needed,('normal','entry_setup'))
  d=json.loads(example_event_sample(event_snapshot(v)));d['enqueue_children']['ft_enqueue']['gate']=True
  with self.assertRaises(ValueError):t.step(json.dumps(d))
  self.assertIsNone(t.last);d['enqueue_children']['ft_enqueue']['gate']=1;self.assertTrue(t.step(json.dumps(d)).complete)
  with self.assertRaises(ValueError):t.step('{bad')
  self.assertIsNone(t.last)
 def test_stable_snapshot_getter_overrides_json_priority_flags(self):
  v=panel('royale');t=EventJoinTrial(lambda:(v,{}));d=json.loads(example_event_sample(event_snapshot(v)))
  d['values'].update(first_chaos_byte=1,priority_chaos_byte=1,priority_royale_byte=0)
  p=t.step(json.dumps(d));self.assertEqual([label for label,child in p.children],['royale_join'])
  self.assertEqual(p.queue.records[0].payload.hex(),'b70701')

if __name__=='__main__':unittest.main()
