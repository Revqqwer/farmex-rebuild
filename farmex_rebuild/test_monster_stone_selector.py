import unittest
from dataclasses import replace
from monster_stone_selector import MSSelectorObservation, MSSelectorFrame, plan_ms_selector


def fixture(candidates=1, **changes):
 values=dict(buffer_check=0x1000,tree_root_slot=0x2000,tree_root_eax=0x3000,
  sentinel_eax=0x4000,first_node_eax=0x5000,buffer_initial_write=0x1000)
 normals={k:True for k in ('frame_setup','name_init','tree_root','sentinel','first_node','initialize_iterator','return_cleanup')}
 names={}
 for i in range(candidates):
  p='n%d.'%i
  v=dict(actor_eax=0x6000+i*0x100,state_offset=0x10,state_eax=0,
   first_offset=0x20,first_bits=0x41200000,second_offset=0x24,second_bits=0x41a00000,
   metric1_eax=20,metric2_eax=60,kind_offset=0x30,kind_eax=1,
   name_storage_offset=0x40,name_storage_eax=0,name_data_offset=0x44,
   actor_guard_eax=1,stack_id_for_guard=100+i,target_guard_eax=1,mode_dword=0,
   boss_filter_eax=1,stack_id_for_selection=200+i,iterator_buffer=0x1000,
   iterator_target=0x7000,next_buffer=0x1100,next_node_eax=0x4000 if i==candidates-1 else 0x5004+i*4)
  values.update({p+k:x for k,x in v.items()});names[i]='Captured boss %d'%i
  normals.update({p+k:True for k in ('actor','state','first_coordinate','second_coordinate',
   'metric1','metric1_ftol','metric2','metric2_ftol','kind','name_storage','name_pointer',
   'name_copy','name_convert_cleanup','actor_guard','target_guard','boss_filter','iterator','next_node')})
 values.update(changes)
 return MSSelectorObservation(values,normals,names)


class SelectorTests(unittest.TestCase):
 def test_later_equal_candidate_replaces_and_stack_reads_remain_distinct(self):
  p=plan_ms_selector(fixture(2))
  self.assertTrue(p.complete);self.assertEqual(p.return_eax,201)
  self.assertEqual(p.selections,((0,200,0x6000,20),(1,201,0x6100,20)))
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='n0.target_guard'),(100,0x561f34))
  self.assertEqual(p.stores,((0x562040,4,201),(0x56203c,4,0x6100),(0x562048,4,0),(0x562044,1,0),(0x56204c,1,1)))
  self.assertFalse(p.stack_ID_source_verified);self.assertFalse(p.iterator_ABI_verified)

 def test_missing_stack_id_is_not_derived_from_actor(self):
  o=fixture();v=dict(o.values);del v['n0.stack_id_for_guard']
  p=plan_ms_selector(replace(o,values=v))
  self.assertFalse(p.complete);self.assertEqual(p.needed,('value','n0.stack_id_for_guard'))
  self.assertEqual(p.reads[-1],('EBP-48',4,'n0.stack_id_for_guard'));self.assertEqual(p.stores,())

 def test_kind_and_state_filter_only_after_both_metrics(self):
  for k,v in (('kind_eax',0x10a),('state_eax',4),('state_eax',5),('state_eax',13)):
   p=plan_ms_selector(fixture(**{'n0.'+k:v}))
   self.assertTrue(p.complete);self.assertEqual(p.return_eax,0)
   labels=[c[2] for c in p.calls]
   self.assertIn('n0.metric2_ftol',labels);self.assertNotIn('n0.name_copy',labels)

 def test_unsigned_metrics_and_secondary_admission_do_not_override_best_gate(self):
  p=plan_ms_selector(fixture(**{'n0.metric1_eax':0xffffffff,'n0.metric2_eax':51}))
  self.assertTrue(p.complete);self.assertNotIn('n0.name_copy',[c[2] for c in p.calls])
  p=plan_ms_selector(fixture(**{'n0.metric1_eax':51,'n0.metric2_eax':50}))
  self.assertTrue(p.complete);self.assertIn('n0.name_copy',[c[2] for c in p.calls])
  self.assertNotIn('n0.boss_filter',[c[2] for c in p.calls]);self.assertEqual(p.return_eax,0)

 def test_mode_one_and_guard_AL_two_do_not_select(self):
  for changes in ({'n0.mode_dword':1},{'n0.target_guard_eax':0x102}):
   p=plan_ms_selector(fixture(**changes));self.assertTrue(p.complete)
   self.assertEqual(p.return_eax,0);self.assertNotIn('n0.boss_filter',[c[2] for c in p.calls])
  self.assertEqual(plan_ms_selector(fixture(**{'n0.target_guard_eax':0x101})).return_eax,200)

 def test_signed_final_ID_and_zero_clear_in_source_order(self):
  for selected in (0,0x80000000,0xffffffff):
   p=plan_ms_selector(fixture(**{'n0.stack_id_for_selection':selected}))
   self.assertTrue(p.complete);self.assertEqual(p.best_id,selected);self.assertEqual(p.return_eax,0)
   self.assertEqual(p.stores,((0x56204c,1,0),(0x56203c,4,0),(0x562040,4,0)))

 def test_empty_sentinel_does_not_invent_pre_loop_guard(self):
  p=plan_ms_selector(fixture(first_node_eax=0x4000))
  self.assertTrue(p.complete)
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='n0.actor'),(0x4014,))

 def test_inline_count_50_heap_count_and_unmodeled_oversize(self):
  p=plan_ms_selector(fixture());self.assertEqual(next(c[1] for c in p.calls if c[2]=='n0.name_copy'),(50,0x6044))
  p=plan_ms_selector(fixture(**{'n0.name_storage_eax':16,'n0.name_pointer_eax':0x9000}))
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='n0.name_copy'),(16,0x9000))
  p=plan_ms_selector(fixture(**{'n0.name_storage_eax':513,'n0.name_pointer_eax':0x9000}))
  self.assertFalse(p.complete);self.assertEqual(p.needed,('unmodeled','source_name_copy_above512'))

 def test_budget_is_local_and_does_not_commit_truncated_selection(self):
  f=MSSelectorFrame(candidate_budget=1);p=f.advance(fixture(2))
  self.assertFalse(p.complete);self.assertEqual(p.needed,('budget','source_iterator_still_open'));self.assertEqual(p.stores,())
  f.extend_budget(2);p=f.advance(fixture(2));self.assertTrue(p.complete);self.assertEqual(p.return_eax,201)

 def test_frame_preserves_consumed_prefix_across_return_gap(self):
  o=fixture();n=dict(o.normal_returns);n['n0.target_guard']=False
  f=MSSelectorFrame();p=f.advance(replace(o,normal_returns=n));self.assertFalse(p.complete)
  p=f.advance(fixture(**{'n0.actor_eax':0x9999,'n0.stack_id_for_guard':999,'n0.stack_id_for_selection':321}))
  self.assertTrue(p.complete);self.assertEqual(p.best_pointer,0x6000);self.assertEqual(p.return_eax,321)
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='n0.target_guard'),(100,0x561f34))

 def test_failed_allocation_is_not_inferred_as_safe_exit(self):
  o=fixture(buffer_check=0,allocation_eax=0,buffer_initial_write=0)
  o=replace(o,normal_returns={**o.normal_returns,'allocate':True})
  p=plan_ms_selector(o);self.assertTrue(p.complete)
  self.assertEqual(p.stores[0],(0x56fb3c,4,0))
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='initialize_iterator'),(0x5000,0))

 def test_generated_child_blocks_parent_normal_until_complete(self):
  from monster_stone_combat import MSCombatFrame,MSCombatObservation
  from test_monster_stone_combat import sample
  f=MSCombatFrame('target_entry')
  p=f.advance(replace(sample(selected_target_eax=200),selector_inputs=MSSelectorObservation()))
  self.assertFalse(p.complete);self.assertEqual(p.needed,('selector','select_target'));self.assertEqual(p.stores,())
  o=sample(selected_target_eax=200);normals=dict(o.normal_returns);normals['select_target']=False
  p=f.advance(replace(o,normal_returns=normals,selector_inputs=fixture()))
  self.assertFalse(p.complete);self.assertTrue(p.selector_child.complete)
  self.assertEqual(p.needed,('normal','select_target'))
  p=f.advance(MSCombatObservation({'selected_target_eax':200},{'select_target':True,'target_entry_return':True}))
  self.assertTrue(p.complete);self.assertEqual(p.stores,((0x562040,4,200),))
  self.assertEqual(p.selector_child.return_eax,200)

 def test_generated_child_rejects_conflicting_parent_EAX(self):
  from monster_stone_combat import plan_ms_target_entry
  from test_monster_stone_combat import sample
  with self.assertRaisesRegex(ValueError,'differs'):
   plan_ms_target_entry(replace(sample(selected_target_eax=123),selector_inputs=fixture()))

if __name__=='__main__':unittest.main()
