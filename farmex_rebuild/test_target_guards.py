import unittest
from dataclasses import replace
from target_guards import *

def actor(**changes):
 v=dict(guarded_root_slot=0x1000,guarded_root_eax=0x2000,first_profile_byte=1,second_profile_byte=2,
  direct_root_slot=0x1100,direct_root=0x2100,callback_target=0x3000,callback_eax=0x123401)
 v.update(changes);return TargetGuardObservation(v,{'guarded_root':True,'callback':True,'return':True})

def ids(entries=(5,6),**changes):
 v={}
 for pre in ('initial.',)+tuple('e%d.'%i for i in range(len(entries)+1)):
  v.update({pre+'begin_check':0x1000,pre+'end':0x1000+len(entries)*4,pre+'begin_subtract':0x1000,pre+'begin_entry':0x2000})
 for i,x in enumerate(entries):v['e%d.id'%i]=x
 v.update(changes);return TargetGuardObservation(v,{'frame_setup':True,'return':True})

class TargetGuardTests(unittest.TestCase):
 def test_null_actor_skips_all_global_and_guarded_reads(self):
  p=plan_target_guard('actor',0,TargetGuardObservation(normal_returns={'return':True}))
  self.assertTrue(p.complete);self.assertEqual(p.return_eax,0);self.assertEqual(p.reads,())

 def test_actor_profile_one_uses_guarded_root_argument_and_distinct_direct_ECX(self):
  p=plan_target_guard('actor',77,actor());self.assertTrue(p.complete)
  self.assertEqual(p.callback_invocation,(0x3000,0x2100,(77,0x2000)))
  self.assertEqual(p.return_eax,0x123401);self.assertFalse(p.callback_ABI_verified)
  self.assertNotIn('second_profile_byte',[r[2] for r in p.reads])

 def test_actor_second_profile_read_is_fresh_and_callback_AL_exact_one(self):
  p=plan_target_guard('actor',77,actor(first_profile_byte=2));self.assertTrue(p.complete)
  self.assertEqual(p.callback_invocation,(0x3000,0x2100,(77,)))
  for callback in (0,2,0x100):self.assertEqual(plan_target_guard('actor',77,actor(callback_eax=callback)).return_eax,0)
  p=plan_target_guard('actor',77,actor(first_profile_byte=2,second_profile_byte=1))
  self.assertEqual(p.return_eax,0);self.assertIsNone(p.callback_invocation)
  self.assertIn('guarded_root',[c[2] for c in p.calls])

 def test_actor_return_gap_retains_callback_result_and_does_not_reinvoke(self):
  f=TargetGuardFrame('actor',77);o=actor();n=dict(o.normal_returns);n['return']=False
  p=f.advance(replace(o,normal_returns=n));self.assertFalse(p.complete)
  p=f.advance(actor(callback_eax=0));self.assertTrue(p.complete);self.assertEqual(p.return_eax,0x123401)

 def test_ID_list_matches_full_DWORD_including_zero_and_rejects(self):
  for arg,entries in ((5,(5,)),(0,(0,)),(0x10005,(5,0x10005))):
   p=plan_target_guard('id_list',arg,ids(entries));self.assertTrue(p.complete);self.assertEqual(p.return_eax,0)
   self.assertEqual(p.status,'listed');self.assertFalse(p.ID_origin_verified)

 def test_empty_list_accepts_without_comparing_ID_and_nonempty_success_preserves_high_EAX(self):
  p=plan_target_guard('id_list',99,ids(()));self.assertTrue(p.complete);self.assertEqual(p.return_eax,1)
  p=plan_target_guard('id_list',99,ids());self.assertTrue(p.complete)
  self.assertEqual((p.return_al,p.return_eax),(1,0x562101));self.assertEqual(p.status,'not_listed')
  self.assertNotEqual(p.return_eax,1)

 def test_initial_count_and_loop_count_are_separate_fresh_snapshots(self):
  p=plan_target_guard('id_list',5,ids(**{'e0.begin_check':0}))
  self.assertTrue(p.complete);self.assertEqual(p.counts,(2,0));self.assertEqual(p.status,'not_listed')
  self.assertNotIn('e0.id',[r[2] for r in p.reads])

 def test_negative_count_and_wrapped_pointer_difference_are_not_sanitized(self):
  p=plan_target_guard('id_list',5,ids((5,),**{'initial.end':0x0ffc,'e0.end':0x0ffc}))
  self.assertTrue(p.complete);self.assertEqual(p.counts,(0xffffffff,0xffffffff));self.assertEqual(p.return_al,0)
  p=plan_target_guard('id_list',5,ids((5,),**{'initial.end':0,'initial.begin_subtract':0xfffffffc}))
  self.assertEqual(p.counts[0],1)

 def test_guard_budget_cannot_produce_success_on_truncated_list(self):
  f=TargetGuardFrame('id_list',6,entry_budget=1);p=f.advance(ids())
  self.assertFalse(p.complete);self.assertEqual(p.needed,('budget','source_ID_vector_still_open'))
  self.assertIsNone(p.return_al);f.extend_budget(2);self.assertEqual(f.advance(ids()).return_al,0)

 def test_typed_data_is_immutable_and_invalid_raw_data_rejected(self):
  v={'first_profile_byte':1};o=TargetGuardObservation(v);v['first_profile_byte']=2
  self.assertEqual(o.values['first_profile_byte'],1)
  with self.assertRaises(ValueError):TargetGuardObservation({'x':True})

 def test_selector_guard_child_blocks_parent_and_preserves_separate_ID_reads(self):
  from monster_stone_selector import MSSelectorFrame
  from test_monster_stone_selector import fixture
  f=MSSelectorFrame();o=replace(fixture(**{'n0.actor_guard_eax':0x123401}),actor_guards={0:TargetGuardObservation()})
  p=f.advance(o);self.assertFalse(p.complete);self.assertEqual(p.needed,('guard','n0.actor_guard'))
  n=dict(o.normal_returns);n['n0.actor_guard']=False
  p=f.advance(replace(o,normal_returns=n,actor_guards={0:actor()},id_guards={0:ids(())}))
  self.assertFalse(p.complete);self.assertTrue(p.guard_children[0][2].complete)
  self.assertEqual(p.needed,('normal','n0.actor_guard'))
  p=f.advance(replace(o,id_guards={0:ids(())}));self.assertTrue(p.complete)
  self.assertEqual(p.return_eax,200);self.assertEqual(f.guards[(0,'id_list')].argument,100)
  self.assertFalse(p.stack_ID_source_verified)

 def test_selector_rejects_guard_full_EAX_conflict_and_listed_ID_skips_boss_filter(self):
  from monster_stone_selector import plan_ms_selector
  from test_monster_stone_selector import fixture
  with self.assertRaisesRegex(ValueError,'full EAX differs'):
   plan_ms_selector(replace(fixture(),actor_guards={0:actor()}))
  p=plan_ms_selector(replace(fixture(**{'n0.target_guard_eax':0}),id_guards={0:ids((100,))}))
  self.assertTrue(p.complete);self.assertEqual(p.return_eax,0)
  self.assertNotIn('n0.boss_filter',[c[2] for c in p.calls])

 def test_selector_cannot_retroactively_bind_guard_after_consumed_normal(self):
  from monster_stone_selector import MSSelectorFrame
  from test_monster_stone_selector import fixture
  f=MSSelectorFrame();o=fixture();n=dict(o.normal_returns);n['n0.iterator']=False
  self.assertFalse(f.advance(replace(o,normal_returns=n)).complete)
  with self.assertRaisesRegex(ValueError,'retroactively'):
   f.advance(replace(o,actor_guards={0:actor()}))

if __name__=='__main__':unittest.main()
