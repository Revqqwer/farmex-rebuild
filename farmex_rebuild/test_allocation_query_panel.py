import json,unittest
from dataclasses import replace
from auto_allocation import AutoAllocationFrame,AutoAllocationObservation
from allocation_queries import AllocationQueryObservation
from allocation_panel_trial import AllocationPanelTrial
from allocation_consumer_trial import describe_allocation_consumer
from test_auto_allocation import sample
from test_allocation_queries import stat_sample,skill_sample
from test_allocation_consumer_trial import trial_data,observation_json

class AllocationQueryPanelTests(unittest.TestCase):
 def test_unsupported_skill_first_row_derives_zero_from_caller_not_independent_capture(self):
  o=sample(stat_enabled_byte=0,**{'skill0.query_argument':5,'skill0.query_eax':0})
  f=AutoAllocationFrame();p=f.advance(replace(o,query_children={'skill0.query':AllocationQueryObservation(normal_returns={'return':True})}))
  self.assertTrue(p.complete);self.assertEqual(p.children[0][1].return_eax,0)
 def test_unsupported_skill_second_row_derives_three_from_caller(self):
  o=sample(stat_enabled_byte=0,**{'skill0.threshold':5,'skill1.begin_check':0x1000,'skill1.end':0x1018,'skill1.query_argument':0,'skill1.query_eax':3})
  p=AutoAllocationFrame().advance(replace(o,query_children={'skill1.query':AllocationQueryObservation(normal_returns={'return':True})}))
  self.assertTrue(p.complete);self.assertEqual(p.children[0][1].return_eax,3)
 def test_contradictory_unconsumed_incoming_rejected_but_later_capture_does_not_rewrite_prefix(self):
  o=sample(stat_enabled_byte=0,**{'skill0.query_argument':5,'skill0.query_eax':0})
  bad=AllocationQueryObservation({'incoming_eax':99},{'return':True})
  with self.assertRaisesRegex(ValueError,'row index'):AutoAllocationFrame().advance(replace(o,query_children={'skill0.query':bad}))
  f=AutoAllocationFrame();n=dict(o.normal_returns);n['skill0.query']=False
  p=f.advance(replace(o,normal_returns=n,query_children={'skill0.query':AllocationQueryObservation(normal_returns={'return':True})}))
  self.assertEqual(p.needed,('normal','skill0.query'))
  p=f.advance(replace(o,query_children={'skill0.query':bad}));self.assertTrue(p.complete)
  self.assertEqual(p.children[0][1].return_eax,0)
 def test_panel_chains_stat_query_and_action_with_separate_counts(self):
  v,l,data=trial_data();data['consumer']['query_children']={'stat0.query':observation_json(stat_sample())}
  t=AllocationPanelTrial(lambda:(v,l));t.step(json.dumps(data));p=t.consumer_last
  self.assertTrue(p.complete);self.assertEqual([label for label,child in p.children],['stat0.query','stat0.action'])
  description=describe_allocation_consumer(p)
  self.assertEqual(description['Ayrıntılı sorgu modeli sayısı'],1);self.assertEqual(description['Ayrıntılı eylem modeli sayısı'],1)
 def test_panel_skill_query_argument_must_match_panel_even_before_action(self):
  v,l,data=trial_data('skill');data['consumer']['values']['skill0.query_argument']=2
  t=AllocationPanelTrial(lambda:(v,l))
  with self.assertRaisesRegex(ValueError,'differs'):t.step(json.dumps(data))
  self.assertIsNone(t.consumer_last)
 def test_panel_partial_query_cleanup_resumes_and_outer_return_still_required(self):
  v,l,data=trial_data();q=observation_json(stat_sample());q['normal_returns']['argument_cleanup']=False
  data['consumer']['query_children']={'stat0.query':q};t=AllocationPanelTrial(lambda:(v,l));t.step(json.dumps(data))
  self.assertEqual(t.consumer_last.needed,('child','stat0.query'));self.assertEqual(t.consumer_last.actions,())
  q['normal_returns']['argument_cleanup']=True;data['consumer']['normal_returns']['stat0.query']=False
  t.step(json.dumps(data));self.assertEqual(t.consumer_last.needed,('normal','stat0.query'))
  data['consumer']['normal_returns']['stat0.query']=True;t.step(json.dumps(data));self.assertTrue(t.consumer_last.complete)
 def test_panel_query_EAX_disagreement_rejected_before_action(self):
  v,l,data=trial_data();data['consumer']['query_children']={'stat0.query':observation_json(stat_sample(result=6))}
  t=AllocationPanelTrial(lambda:(v,l))
  with self.assertRaisesRegex(ValueError,'full EAX'):t.step(json.dumps(data))
  self.assertIsNone(t.consumer_last)
 def test_unreached_bad_query_fields_are_ignored_and_reached_types_checked(self):
  v,l,data=trial_data();data['consumer']['values']['initial_tick_eax']=499;data['consumer']['query_children']='future'
  t=AllocationPanelTrial(lambda:(v,l));t.step(json.dumps(data));self.assertEqual(t.consumer_last.status,'cooldown_wait')
  v,l,data=trial_data();q=observation_json(stat_sample());q['values']['future']='ignored'
  q['normal_returns']['entry_setup']=1;data['consumer']['query_children']={'stat0.query':q}
  t=AllocationPanelTrial(lambda:(v,l))
  with self.assertRaises(ValueError):t.step(json.dumps(data))
  q['normal_returns']['entry_setup']=True;t.step(json.dumps(data));self.assertTrue(t.consumer_last.complete)

if __name__=='__main__':unittest.main()
