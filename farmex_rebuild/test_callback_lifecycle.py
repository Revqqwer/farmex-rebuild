import unittest
from dataclasses import replace
from callback_lifecycle import *
from callback_prequeue import CallbackPreQueueFrame
from test_callback_prequeue import sample as pre

def sample(**updates):
 v=dict(object_check_eax=1,stamp_high=0,stamp_low=0,notice_enabled_byte=1,state_active_byte=1,notice_done_byte=0,
 notice_enabled_fresh_byte=1,special_byte=0,initialized_byte=0,tick_eax=123,profile_done_byte=0,profile_enabled_byte=0,
 mode=0,mode4_skip_byte=0,sleep_enabled_byte=0,sleep_ms=250,predicate_eax=0,target_slot=0x1000,
 saved_original=0,original_eax=0x12345678)
 v.update({'predicate%d_byte'%i:1 for i in range(5)});v['predicate5_byte']=0
 n={k:True for k in ('return','object_check','notice_prepare','tick','initialize','profile_refresh','sleep','switch_predicate','replacement','guarded_original','replacement_copy')}
 v.update(updates);return CallbackLifecycleObservation(v,n)

class CallbackLifecycleTests(unittest.TestCase):
 def test_readiness_failure_returns_full_zero_and_success_defines_only_AL(self):
  p=plan_callback_lifecycle('ready',sample(object_check_eax=0x100));self.assertTrue(p.complete);self.assertEqual((p.return_al,p.return_eax),(0,0))
  self.assertEqual(p.reads,())
  p=plan_callback_lifecycle('ready',sample(object_check_eax=0xabcd0001));self.assertEqual(p.return_al,1);self.assertIsNone(p.return_eax)
 def test_readiness_short_circuit_and_fresh_notice_flag(self):
  p=plan_callback_lifecycle('ready',sample(stamp_high=1,notice_enabled_fresh_byte=0));self.assertEqual(p.stores,())
  self.assertNotIn('stamp_low',[r[2] for r in p.reads])
  p=plan_callback_lifecycle('ready',sample(stamp_high=1));self.assertEqual(p.stores,((0x553d35,1,1),))
 def test_notice_helper_gap_precedes_its_store(self):
  f=CallbackLifecycleFrame('ready');o=sample(stamp_high=1);n=dict(o.normal_returns);n['notice_prepare']=False
  p=f.advance(replace(o,normal_returns=n));self.assertEqual(p.stores,());self.assertEqual(p.needed,('normal','notice_prepare'))
  p=f.advance(sample(notice_enabled_fresh_byte=0));self.assertTrue(p.complete);self.assertEqual(p.stores,((0x553d35,1,1),))
 def test_special_stamp_skips_low_read_when_high_nonzero_and_initializes_zero_pair(self):
  p=plan_callback_lifecycle('stamp',sample(special_byte=1,stamp_high=1));self.assertEqual(p.stores,());self.assertNotIn('stamp_low',[r[2] for r in p.reads])
  p=plan_callback_lifecycle('stamp',sample(special_byte=1));self.assertEqual(p.stores,((0x5620a4,4,123),(0x5620a8,4,0)))
 def test_first_initialize_and_later_profile_refresh_have_distinct_stores(self):
  p=plan_callback_lifecycle('stamp',sample());self.assertEqual(p.stores[-2:],((0x561f54,1,1),(0x553d34,1,0)))
  p=plan_callback_lifecycle('stamp',sample(initialized_byte=1));self.assertEqual(p.stores,((0x553d34,1,1),));self.assertIn('profile_refresh',[c[2] for c in p.calls])
  p=plan_callback_lifecycle('stamp',sample(initialized_byte=1,profile_enabled_byte=1));self.assertNotIn('profile_refresh',[c[2] for c in p.calls])
 def test_switch_predicate_requires_first_five_nonzero_and_last_zero_for_false(self):
  p=plan_callback_lifecycle('predicate',sample());self.assertEqual((p.return_al,p.return_eax),(0,0))
  for i in range(5):
   p=plan_callback_lifecycle('predicate',sample(**{'predicate%d_byte'%i:0}));self.assertEqual(p.return_al,1);self.assertIsNone(p.return_eax)
  self.assertEqual(plan_callback_lifecycle('predicate',sample(predicate5_byte=255)).return_al,1)
 def test_mode4_skip_and_SleepEx_physical_arguments(self):
  p=plan_callback_lifecycle('switch',sample(mode=4,mode4_skip_byte=1));self.assertEqual([c[2] for c in p.calls],['return'])
  p=plan_callback_lifecycle('switch',sample(sleep_enabled_byte=1,sleep_ms=250));self.assertIn(('SleepEx',(0,250),'sleep'),p.calls)
 def test_replace_preserves_old_original_and_gaps_do_not_reinterpret_capture(self):
  f=CallbackLifecycleFrame('replace',target_slot=0x1000);o=sample();n=dict(o.normal_returns);n['replacement_copy']=False
  p=f.advance(replace(o,normal_returns=n));self.assertEqual(p.stores,((0x554228,4,0x12345678),))
  p=f.advance(sample(saved_original=999,original_eax=888));self.assertTrue(p.complete);self.assertEqual(p.stores[0][2],0x12345678)
  p=plan_callback_lifecycle('replace',sample(saved_original=99),target_slot=0x1000)
  self.assertEqual(p.stores,((0x1000,4,0x46eca8),));self.assertNotIn('guarded_original',[c[2] for c in p.calls])
 def test_generated_false_predicate_requires_known_full_zero_in_caller(self):
  o=replace(sample(predicate_eax=0x100),predicate_child=sample())
  with self.assertRaisesRegex(ValueError,'full EAX'):CallbackLifecycleFrame('switch').advance(o)
 def test_nested_replacement_blocks_switch_outer_return(self):
  f=CallbackLifecycleFrame('switch');o=replace(sample(predicate_eax=1),predicate_child=sample(predicate0_byte=0),replacement_child=CallbackLifecycleObservation())
  p=f.advance(o);self.assertEqual(p.needed,('child','replacement'))
  n=dict(o.normal_returns);n['replacement']=False
  p=f.advance(replace(o,normal_returns=n,replacement_child=sample()));self.assertEqual(p.needed,('normal','replacement'))
  p=f.advance(sample(predicate_eax=0));self.assertTrue(p.complete);self.assertEqual(dict(p.children)['replacement'].stores[-1],(0x1000,4,0x46eca8))
 def test_prequeue_ready_child_and_switch_replacement_do_not_abort_current_callback(self):
  ready=sample();switch=replace(sample(predicate_eax=1),replacement_child=sample())
  f=CallbackPreQueueFrame();o=pre();n=dict(o.normal_returns);n['prelude2']=False
  p=f.advance(replace(o,normal_returns=n,lifecycle_children={'ready':ready,'prelude2':switch}))
  self.assertEqual(p.needed,('normal','prelude2'));self.assertNotIn('connection',[c[2] for c in p.calls])
  p=f.advance(o);self.assertTrue(p.complete);self.assertTrue(p.queue_consumer_reached)
  self.assertTrue(dict(p.children)['prelude2'].complete)
 def test_late_generated_binding_rejected_after_opaque_prelude(self):
  f=CallbackPreQueueFrame();o=pre();n=dict(o.normal_returns);n['connection']=False
  self.assertFalse(f.advance(replace(o,normal_returns=n)).complete)
  with self.assertRaisesRegex(ValueError,'retroactively'):f.advance(replace(o,lifecycle_children={'prelude1':sample()}))

if __name__=='__main__':unittest.main()
