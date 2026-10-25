import json,unittest
from allocation_panel_trial import *
from test_allocation_panel_trial import panel
from test_auto_allocation import sample
from test_allocation_actions import stat,skill

def observation_json(o):return {'values':dict(o.values),'normal_returns':dict(o.normal_returns)}

def trial_data(domain='stat'):
 v,l=panel();v[AUTO_ALLOCATION_FLAGS[0]]=domain=='stat';v[AUTO_ALLOCATION_FLAGS[1]]=True
 snapshot=compile_allocation_panel(v,l);data=json.loads(example_allocation_sample(snapshot))
 o=sample(stat_enabled_byte=int(domain=='stat'),**{'stat0.action_argument':3,'stat0.threshold':100,'skill0.action_argument':1,'skill0.query_argument':1,'skill0.threshold':50})
 data['consumer']=observation_json(o)
 data['consumer']['action_children']={domain+'0.action':observation_json(stat() if domain=='stat' else skill())}
 return v,l,data

class AllocationConsumerTrialTests(unittest.TestCase):
 def test_panel_producer_consumer_and_stat_operand_chain(self):
  v,l,data=trial_data();t=AllocationPanelTrial(lambda:(v,l));p=t.step(json.dumps(data))
  self.assertTrue(p.complete);c=t.consumer_last;self.assertTrue(c.complete)
  self.assertEqual(c.actions,(('stat',0,3),));self.assertEqual(c.children[0][1].argument,3)
  self.assertEqual(c.children[0][1].invocation,(0xabcdef12,0x8000,(1,0x76543210)))
  self.assertFalse(c.allocation_effect_verified)
 def test_skill_panel_argument_reaches_wrapped_call_plan(self):
  v,l,data=trial_data('skill');t=AllocationPanelTrial(lambda:(v,l));t.step(json.dumps(data))
  self.assertTrue(t.consumer_last.complete)
  self.assertEqual(t.consumer_last.children[0][1].invocation,(0x12345678,0x3000,(5,)))
 def test_partial_child_and_separate_outer_return_survive_JSON_messages(self):
  v,l,data=trial_data();child=data['consumer']['action_children']['stat0.action']
  child['normal_returns']['callback']=False;t=AllocationPanelTrial(lambda:(v,l));t.step(json.dumps(data))
  self.assertEqual(t.consumer_last.needed,('child','stat0.action'));self.assertEqual(t.consumer_last.stores,())
  del data['consumer']['normal_returns']['stat0.action'];child['normal_returns']['callback']=True
  t.step(json.dumps(data));self.assertEqual(t.consumer_last.needed,('normal','stat0.action'))
  data['consumer']={'normal_returns':{'stat0.action':True,'post_tick':True,'return':True},'values':{'post_tick_eax':999}}
  t.step(json.dumps(data));self.assertTrue(t.consumer_last.complete)
  self.assertEqual(t.consumer_last.stores[0],(0x553cac,4,999))
 def test_reached_flags_and_row_operands_must_match_producer(self):
  for label,value in (('stat_enabled_byte',0),('stat0.threshold',101),('stat0.action_argument',4)):
   with self.subTest(label=label):
    v,l,data=trial_data();data['consumer']['values'][label]=value;t=AllocationPanelTrial(lambda:(v,l))
    with self.assertRaisesRegex(ValueError,'differs'):t.step(json.dumps(data))
    self.assertIsNone(t.consumer_last)
 def test_unreached_bad_child_fields_are_ignored_until_needed(self):
  v,l,data=trial_data();data['consumer']['values']['initial_tick_eax']=499
  data['consumer']['action_children']='not reached';t=AllocationPanelTrial(lambda:(v,l));t.step(json.dumps(data))
  self.assertEqual(t.consumer_last.status,'cooldown_wait')
  v,l,data=trial_data();data['consumer']['action_children']['stat0.action']['values']['future_unused']='not reached'
  t=AllocationPanelTrial(lambda:(v,l));t.step(json.dumps(data));self.assertTrue(t.consumer_last.complete)
 def test_bad_reached_child_type_rejects_and_prefix_can_resume(self):
  v,l,data=trial_data();data['consumer']['action_children']['stat0.action']['values']['guarded_root_slot']=True
  t=AllocationPanelTrial(lambda:(v,l))
  with self.assertRaises(ValueError):t.step(json.dumps(data))
  self.assertIsNone(t.consumer_last);data['consumer']['action_children']['stat0.action']['values']['guarded_root_slot']=0x1000
  t.step(json.dumps(data));self.assertTrue(t.consumer_last.complete)
 def test_consumer_is_optional_and_not_read_before_producer_completes(self):
  v,l,data=trial_data();data['consumer']='not reached';data['normal_returns']['stat_clear']=False
  t=AllocationPanelTrial(lambda:(v,l));self.assertFalse(t.step(json.dumps(data)).complete);self.assertIsNone(t.consumer_last)
  del data['consumer'];data['normal_returns']['stat_clear']=True
  self.assertTrue(t.step(json.dumps(data)).complete);self.assertIsNone(t.consumer_last)
 def test_changed_panel_invalidates_both_frames_and_stale_sample(self):
  v,l,data=trial_data();t=AllocationPanelTrial(lambda:(v,l));t.step(json.dumps(data));frame=t.consumer_frame
  l[ALLOCATION_LISTS['stat']][0]['caption']='4'
  with self.assertRaisesRegex(ValueError,'Panel değişti'):t.step(json.dumps(data))
  self.assertIsNot(t.consumer_frame,frame);self.assertIsNone(t.consumer_last)
  t.reset();self.assertIsNone(t.consumer_frame)

if __name__=='__main__':unittest.main()
