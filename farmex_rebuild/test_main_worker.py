import unittest
from dataclasses import replace
from main_worker import *

def sample(**updates):
 values=dict(enabled_byte=1,exclusive_byte=0,notice_first_byte=0,notice_second_byte=0,
  pre_mode_dword=1,pre_flag_byte=0,first_active_byte=0,route_mode_dword=1,route_active_byte=0,
  activity_tick_eax=1000,activity_zero_low=1000,activity_zero_high=0,
  interval_check_dword=100,initial_interval_eax=100,activity_low=0,activity_high=0,
  activity_interval_dword=100,periodic_low=0,periodic_high=0,periodic_interval_dword=100,
  periodic_guard_eax=1,periodic_flag_byte=1,callback_argument_dword=0x1234,next_interval_eax=123,
  ms_mode_dword=1,ms_block_byte=0,ms_use_active_byte=1,ms_movement_active_byte=1,
  combat_enabled_byte=1,combat_block_byte=0,general_mode_dword=1,general_probe_eax=0,
  genie_active_byte=0,idle_mode_dword=1,idle_flag_byte=0,idle_genie_eax=0,idle_other_byte=0,
  priority_first_eax=0,priority_second_eax=0,target_mode_zero_dword=1,target_mode_one_dword=1,
  target_mode_two_dword=2,target_area1_eax=0x51,target_area2_eax=0,target_area3_eax=0,
  notice_tick_eax=1000,notice_low=0,notice_high=0)
 values.update(updates)
 labels=('frame_setup','prelude','exclusive','notice_tick','notice_span','pre_mode_zero','active_prelude','route',
  'activity_tick','initial_interval','periodic_guard','periodic_callback','next_interval','ms_use','ms_movement',
  'general_probe','general_positive','genie_worker','general_a','general_b','common_genie','common_a','common_b','common_c',
  'idle_genie','priority_first','priority_second','general_target','general_attack','target_area1','target_area2','target_area3',
  'ms_target','common_tail','worker_return')
 return MainWorkerObservation(values,{k:True for k in labels})

def labels(p):return [c[2] for c in p.calls]

class MainWorkerTests(unittest.TestCase):
 def test_prelude_precedes_disabled_gate_and_exclusive_exits(self):
  p=plan_main_worker(sample(enabled_byte=0));self.assertTrue(p.complete)
  self.assertEqual(labels(p),['frame_setup','prelude','worker_return'])
  p=plan_main_worker(sample(exclusive_byte=2));self.assertTrue(p.complete)
  self.assertEqual(labels(p),['frame_setup','prelude','exclusive','worker_return'])

 def test_notice_signed_QWORD_inclusive_threshold_and_early_exit(self):
  for tick,low,high,called in ((999,0,0,False),(1000,0,0,True),(0x100,0xffffff00,0,False),(1000,0,1,False)):
   p=plan_main_worker(sample(notice_first_byte=1,notice_second_byte=1,notice_tick_eax=tick,notice_low=low,notice_high=high))
   self.assertTrue(p.complete);self.assertEqual('notice_span' in labels(p),called)
   self.assertNotIn('ms_use',labels(p));self.assertEqual(p.status,'notice_return')

 def test_normal_MS_sequence_and_tail_are_distinct(self):
  p=plan_main_worker(sample());self.assertTrue(p.complete)
  self.assertLess(labels(p).index('ms_use'),labels(p).index('ms_movement'))
  self.assertLess(labels(p).index('ms_movement'),labels(p).index('ms_target'))
  self.assertEqual([c[1] for c in p.calls if c[2] in ('ms_use','ms_movement','ms_target')],[(0x56216c,)]*3)
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='common_genie'),(0x562194,))
  self.assertEqual(labels(p)[-2:],['common_tail','worker_return']);self.assertFalse(p.whole_worker_verified)

 def test_MS_enable_is_exact_DWORD_one_and_movement_activity_is_fresh(self):
  p=plan_main_worker(sample(ms_mode_dword=0x101));self.assertTrue(p.complete)
  self.assertNotIn('ms_use',labels(p));self.assertNotIn('ms_movement',labels(p))
  p=plan_main_worker(sample(ms_use_active_byte=1,ms_movement_active_byte=0));self.assertTrue(p.complete)
  self.assertIn('ms_use',labels(p));self.assertNotIn('ms_movement',labels(p));self.assertIn('ms_target',labels(p))

 def test_combat_gate_is_after_MS_calls_and_priority_short_circuits_target(self):
  p=plan_main_worker(sample(combat_enabled_byte=0));self.assertEqual(p.status,'combat_disabled')
  self.assertIn('ms_movement',labels(p));self.assertNotIn('common_genie',labels(p))
  p=plan_main_worker(sample(priority_first_eax=0x101));self.assertTrue(p.complete)
  self.assertNotIn('priority_second',labels(p));self.assertNotIn('ms_target',labels(p));self.assertIn('common_tail',labels(p))

 def test_target_areas_are_three_distinct_full_EAX_samples(self):
  p=plan_main_worker(sample(target_area1_eax=0x10051,target_area2_eax=0x52));self.assertTrue(p.complete)
  self.assertIn('target_area2',labels(p));self.assertNotIn('target_area3',labels(p));self.assertIn('ms_target',labels(p))
  p=plan_main_worker(sample(target_area1_eax=0,target_area2_eax=0,target_area3_eax=0x53));self.assertIn('ms_target',labels(p))
  p=plan_main_worker(sample(target_area1_eax=0,target_area2_eax=0,target_area3_eax=0));self.assertNotIn('ms_target',labels(p))

 def test_zero_and_one_mode_checks_are_fresh_and_other_mode_compare_is_retained(self):
  p=plan_main_worker(sample(target_mode_zero_dword=2,target_mode_one_dword=0,target_mode_two_dword=2))
  self.assertTrue(p.complete);self.assertNotIn('ms_target',labels(p));self.assertNotIn('general_attack',labels(p))
  self.assertEqual([r[2] for r in p.reads if r[2].startswith('target_mode')],
   ['target_mode_zero_dword','target_mode_one_dword','target_mode_two_dword'])

 def test_activity_strict_and_periodic_inclusive_thresholds(self):
  for now,activity_low,periodic_low,called in ((1000,900,0,False),(1001,900,901,True),(1001,900,902,False)):
   p=plan_main_worker(sample(activity_tick_eax=now,activity_zero_low=0,activity_low=activity_low,
    periodic_low=periodic_low,periodic_guard_eax=0))
   self.assertTrue(p.complete);self.assertEqual('periodic_callback' in labels(p),called)
   self.assertEqual(bool(p.stores),called)

 def test_interval_creation_then_fresh_threshold_and_callback_short_circuit(self):
  p=plan_main_worker(sample(activity_zero_low=0,interval_check_dword=0,initial_interval_eax=9999,
   activity_interval_dword=100,periodic_guard_eax=0))
  self.assertTrue(p.complete);self.assertIn('periodic_callback',labels(p))
  self.assertNotIn('periodic_flag_byte',[r[2] for r in p.reads])
  self.assertEqual(p.stores,((0x5620cc,4,9999),(0x5620d4,4,1000),(0x5620d8,4,0),(0x5620cc,4,123)))
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='periodic_callback'),(0x46eca8,0x1234,0x554228))

 def test_negative_interval_is_sign_extended_and_tick_is_not_DWORD_wrap_elapsed(self):
  p=plan_main_worker(sample(activity_tick_eax=0x100,activity_zero_low=0xffffff00,
   activity_low=0xffffff00,activity_interval_dword=0xffffffff))
  self.assertTrue(p.complete);self.assertNotIn('periodic_guard',labels(p))
  self.assertIn(('activity_elapsed_gt_signed_interval',-4294966784,-1),p.comparisons)

 def test_general_probe_signed_and_idle_return_before_priority(self):
  p=plan_main_worker(sample(general_mode_dword=0,general_probe_eax=0xffffffff,idle_mode_dword=0,idle_flag_byte=1))
  self.assertTrue(p.complete);self.assertEqual(p.status,'idle_return')
  self.assertNotIn('general_positive',labels(p));self.assertIn('general_a',labels(p));self.assertNotIn('priority_first',labels(p))

 def test_generated_MS_use_blocks_parent_and_enqueues_once_across_outer_gap(self):
  from test_monster_stone_use import sample as use
  f=MainWorkerFrame();o=replace(sample(),children={'ms_use':MSUseObservation()})
  p=f.advance(o);self.assertFalse(p.complete);self.assertEqual(p.needed,('child','ms_use'));self.assertNotIn('ms_movement',labels(p))
  n=dict(o.normal_returns);n['ms_use']=False
  p=f.advance(replace(o,normal_returns=n,children={'ms_use':use()}));self.assertFalse(p.complete)
  self.assertTrue(p.children[0][1].complete);self.assertEqual(p.needed,('normal','ms_use'));self.assertEqual(len(f.queue.records),1)
  p=f.advance(sample(ms_mode_dword=2));self.assertTrue(p.complete);self.assertEqual(len(f.queue.records),1)
  self.assertIn('ms_movement',labels(p)) #Consumed mode1 retained; later samples are independent.

 def test_generated_movement_and_target_children_require_their_own_gates(self):
  from test_monster_stone_combat import sample as combat
  f=MainWorkerFrame();o=replace(sample(),children={'ms_movement':MSCombatObservation(),'ms_target':combat()})
  p=f.advance(o);self.assertFalse(p.complete);self.assertEqual(p.needed,('child','ms_movement'))
  p=f.advance(replace(sample(),children={'ms_movement':combat(),'ms_target':combat()}))
  self.assertTrue(p.complete);self.assertEqual([k for k,v in p.children],['ms_movement','ms_target'])
  self.assertTrue(all(v.complete for k,v in p.children));self.assertFalse(p.live_compatibility_verified)

 def test_consumed_opaque_call_cannot_later_acquire_generated_effects(self):
  from test_monster_stone_use import sample as use
  f=MainWorkerFrame();o=sample();n=dict(o.normal_returns);n['ms_movement']=False
  p=f.advance(replace(o,normal_returns=n));self.assertFalse(p.complete)
  self.assertEqual(p.needed,('normal','ms_movement'))
  with self.assertRaisesRegex(ValueError,'retroactively'):
   f.advance(replace(sample(),children={'ms_use':use()}))
  self.assertEqual(f.queue.records,())

if __name__=='__main__':unittest.main()
