import unittest
from dataclasses import replace
from auto_allocation import *

def sample(**updates):
 v=dict(initial_tick_eax=500,cooldown_low=0,cooldown_high=0,stat_enabled_byte=1,free_stat_eax=1,
  skill_enabled_byte=1,free_skill_eax=1,post_tick_eax=501)
 n={k:True for k in ('initial_tick','free_stat','free_skill','post_tick','return')}
 for domain in ('stat','skill'):
  for i in range(2):
   pre='%s%d.'%(domain,i)
   v.update({pre+'begin_check':0x1000 if i==0 else 0,pre+'end':0x100c,pre+'begin_subtract':0x1000,
    pre+'query_begin':0x2000,pre+'key':9,pre+'query_argument':10,pre+'query_eax':5,
    pre+'threshold_begin':0x3000,pre+'threshold':6,pre+'action_begin':0x4000,pre+'action_argument':11,
    pre+'level_eax':6})
   n.update({pre+k:True for k in ('query','action','level')})
 v.update(updates);return AutoAllocationObservation(v,n)

class AutoAllocationTests(unittest.TestCase):
 def test_signed_QWORD_cooldown_is_inclusive500_and_not_DWORD_wrap(self):
  self.assertEqual(plan_auto_allocation(sample(initial_tick_eax=499)).status,'cooldown_wait')
  self.assertEqual(plan_auto_allocation(sample()).status,'stat_action_returned')
  p=plan_auto_allocation(sample(initial_tick_eax=0x100,cooldown_low=0xffffff00))
  self.assertEqual(p.status,'cooldown_wait');self.assertEqual(p.actions,())

 def test_stat_has_priority_and_fresh_begins_are_not_collapsed(self):
  p=plan_auto_allocation(sample());self.assertTrue(p.complete)
  self.assertEqual(p.actions,(('stat',0,11),));self.assertEqual(p.stores,((0x553cac,4,501),(0x553cb0,4,0)))
  self.assertNotIn('skill_enabled_byte',[r[2] for r in p.reads])
  self.assertIn((0x2000,4,'stat0.key'),p.reads);self.assertIn((0x3008,4,'stat0.threshold'),p.reads)
  self.assertIn((0x4004,4,'stat0.action_argument'),p.reads)

 def test_stat_equality_advances_then_skill_can_run(self):
  p=plan_auto_allocation(sample(**{'stat0.threshold':5}));self.assertTrue(p.complete)
  self.assertEqual(p.actions,(('skill',0,11),));self.assertEqual(p.counts,(('stat',0,1),('stat',1,0),('skill',0,1)))

 def test_free_point_queries_are_signed_and_zero_does_not_stamp(self):
  p=plan_auto_allocation(sample(free_stat_eax=0xffffffff,free_skill_eax=0))
  self.assertTrue(p.complete);self.assertEqual(p.status,'no_action');self.assertEqual(p.counts,());self.assertEqual(p.stores,())

 def test_skill_threshold_needs_actor_level_strictly_greater_than_current(self):
  for level in (4,5):
   p=plan_auto_allocation(sample(stat_enabled_byte=0,**{'skill0.level_eax':level}))
   self.assertEqual(p.status,'skill_level_blocked');self.assertEqual(p.actions,());self.assertEqual(p.stores,())
   self.assertNotIn('skill1.begin_check',[r[2] for r in p.reads])
  p=plan_auto_allocation(sample(stat_enabled_byte=0,**{'skill0.level_eax':6}))
  self.assertEqual(p.status,'skill_action_returned')

 def test_signed_row_threshold_and_current_comparisons(self):
  p=plan_auto_allocation(sample(**{'stat0.query_eax':0xfffffffe,'stat0.threshold':0xffffffff}))
  self.assertTrue(p.complete);self.assertEqual(p.actions,(('stat',0,11),))

 def test_IDIV12_negative_and_wrapped_differences_are_preserved(self):
  p=plan_auto_allocation(sample(**{'stat0.end':0x0ff4}))
  self.assertEqual(p.counts,(('stat',0,0xffffffff),));self.assertTrue(p.complete)
  p=plan_auto_allocation(sample(**{'stat0.end':0,'stat0.begin_subtract':0xfffffff4}))
  self.assertEqual(p.counts,(('stat',0,1),));self.assertTrue(p.complete)
  p=plan_auto_allocation(sample(skill_enabled_byte=0,**{'stat0.end':0x0ff5}))
  self.assertEqual(p.counts,(('stat',0,0),));self.assertEqual(p.actions,())

 def test_action_and_fresh_post_tick_are_independent_prefixes(self):
  f=AutoAllocationFrame();o=sample();n=dict(o.normal_returns);n['post_tick']=False
  p=f.advance(replace(o,normal_returns=n));self.assertFalse(p.complete);self.assertEqual(p.actions,(('stat',0,11),))
  self.assertEqual(p.stores,())
  p=f.advance(sample(post_tick_eax=999,**{'stat0.action_argument':99,'stat0.query_eax':99}))
  self.assertTrue(p.complete);self.assertEqual(p.actions,(('stat',0,11),));self.assertEqual(p.stores[0],(0x553cac,4,999))
  self.assertFalse(p.allocation_effect_verified)

 def test_local_budget_is_not_vector_end_or_permission_to_enter_skill(self):
  f=AutoAllocationFrame(row_budget=1);o=sample(**{'stat0.threshold':5})
  p=f.advance(o);self.assertFalse(p.complete);self.assertEqual(p.needed,('budget','stat_vector_still_open'))
  self.assertNotIn('skill_enabled_byte',[r[2] for r in p.reads])
  f.extend_budget(2);p=f.advance(o);self.assertTrue(p.complete);self.assertEqual(p.actions[0][0],'skill')

 def test_main_legacy_common_genie_label_now_binds_only_actual_allocation_helper(self):
  from main_worker import MainWorkerFrame
  from test_main_worker import sample as main
  f=MainWorkerFrame();o=replace(main(),children={'common_genie':AutoAllocationObservation()})
  p=f.advance(o);self.assertFalse(p.complete);self.assertEqual(p.needed,('child','common_genie'))
  o=replace(main(),children={'common_genie':sample()});n=dict(o.normal_returns);n['common_genie']=False
  p=f.advance(replace(o,normal_returns=n));self.assertFalse(p.complete);self.assertTrue(p.children[0][1].complete)
  self.assertEqual(p.needed,('normal','common_genie'))
  p=f.advance(main());self.assertTrue(p.complete);self.assertEqual(p.children[0][1].actions,(('stat',0,11),))
  self.assertEqual(f.queue.records,())

if __name__=='__main__':unittest.main()
