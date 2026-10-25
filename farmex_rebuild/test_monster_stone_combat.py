import unittest
from dataclasses import replace
from monster_stone_combat import *
from test_motion_genie_helpers import motion

def sample(**updates):
 values=dict(active_byte=1,no_attack_byte=0,area1_eax=0x51,area2_eax=0,area3_eax=0,
  state_root_slot=0x1000,state_root_eax=0x2000,state_offset=0x20,state_eax=0x100,
  float_root_slot=0x1100,float_root_eax=0x2100,float_offset=0x24,status_compare_ax=0x4000,
  stance_root_slot=0x1200,stance_root_eax=0x2200,stance_offset=0x28,stance_eax=0,
  other_block_byte=0,mode_dword=1,follow_byte=1,target_available_byte=1,target_pointer=0x3000,
  first_coordinate_offset=0x10,second_coordinate_offset=0x18,first_coordinate_bits=0x41200000,
  second_coordinate_bits=0x41a00000,first_distance_float_bits=0x42480000,
  second_distance_compare_ax=0,first_distance_compare_ax=0x4000,boss_compare_ax=0,
  current_target_dword=0x10001,target_guard_eax=1,selected_target_eax=123)
 values.update(updates)
 labels=('area1','area2','area3','state_root','state','float_root','status_float','stance_root','stance',
  'boss_distance','boss_move','first_coordinate','second_coordinate','first_distance','second_distance','target_move',
  'movement_return','prepare_target','target_guard','select_target','target_entry_return')
 return MSCombatObservation(values,{k:True for k in labels})

class MSCombatTests(unittest.TestCase):
 def test_inactive_and_outside_areas_do_not_reach_roots_or_motion(self):
  p=plan_ms_movement(MSCombatObservation({'active_byte':0},{'movement_return':True}))
  self.assertTrue(p.complete);self.assertEqual(p.calls,(('source_normal_return',(),'movement_return'),))
  p=plan_ms_movement(sample(area1_eax=0,area2_eax=0,area3_eax=0))
  self.assertEqual(p.status,'outside_area');self.assertFalse(any(c[0]=='0045dc44' for c in p.calls))

 def test_fresh_roots_and_null_root_do_not_invent_early_return(self):
  p=plan_ms_movement(sample(state_root_eax=0));self.assertTrue(p.complete)
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='state'),(0x20,))
  self.assertEqual([c[1] for c in p.calls if c[2] in ('state_root','float_root','stance_root')],[(0x1000,),(0x1100,),(0x1200,)])

 def test_status_mask_retains_source_unordered_behavior(self):
  p=plan_ms_movement(sample(status_compare_ax=0));self.assertEqual(p.status,'float_gate_blocked')
  p=plan_ms_movement(sample(status_compare_ax=0x4500));self.assertTrue(p.complete)
  self.assertEqual(p.status,'target_move_returned') #Raw AH45 is nonzero for TEST45; no Python <= rewrite.

 def test_boss_greater49_moves_early_while_equality_falls_through(self):
  p=plan_ms_movement(sample(mode_dword=0,boss_compare_ax=0));self.assertEqual(p.status,'boss_move_returned')
  self.assertEqual(p.moves,((0x425c0000,0x425c0000),));self.assertFalse(any(r[2]=='follow_byte' for r in p.reads if len(r)==3))
  p=plan_ms_movement(sample(mode_dword=0,boss_compare_ax=0x4000,follow_byte=0))
  self.assertEqual(p.status,'follow_disabled');self.assertEqual(p.moves,())

 def test_final_TEST41_parity_accepts_equal50_and_rejects_greater_or_unordered(self):
  for ax,bits,moves in ((0x4000,0x42480000,True),(0x100,0x42440000,True),(0,0x424c0000,False),(0x4500,0x7fc00001,False)):
   p=plan_ms_movement(sample(first_distance_compare_ax=ax,first_distance_float_bits=bits));self.assertTrue(p.complete)
   self.assertEqual(bool(p.moves),moves)

 def test_distance_invocations_are_separate_and_second_equality_blocks_before_last_compare(self):
  p=plan_ms_movement(sample());distances=[c for c in p.calls if c[0]=='00460548']
  self.assertEqual([c[2] for c in distances],['first_distance','second_distance'])
  self.assertEqual([c[1] for c in distances],[(0x41a00000,0x41200000)]*2)
  o=sample(second_distance_compare_ax=0x4000);v=dict(o.values);del v['first_distance_compare_ax']
  p=plan_ms_movement(replace(o,values=v));self.assertTrue(p.complete);self.assertEqual(p.status,'second_distance_blocked')

 def test_consumed_target_pointer_retained_but_later_offset_can_be_fresh(self):
  f=MSCombatFrame('movement');o=sample();r=dict(o.normal_returns);r['first_coordinate']=False
  self.assertFalse(f.advance(replace(o,normal_returns=r)).complete)
  p=f.advance(sample(target_pointer=0x9000,second_coordinate_offset=0x30));self.assertTrue(p.complete)
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='first_coordinate'),(0x3010,))
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='second_coordinate'),(0x3030,))

 def test_generated_motion_child_and_outer_normal_are_independent(self):
  f=MSCombatFrame('movement');o=replace(sample(),motion_inputs=MotionGenieObservation())
  p=f.advance(o);self.assertFalse(p.complete);self.assertEqual(p.needed,('motion','target_move'))
  r=dict(o.normal_returns);r['target_move']=False
  p=f.advance(replace(o,normal_returns=r,motion_inputs=motion()));self.assertFalse(p.complete)
  self.assertTrue(p.motion_child.complete);self.assertEqual(p.needed,('normal','target_move'))
  p=f.advance(MSCombatObservation(normal_returns={'target_move':True,'movement_return':True}))
  self.assertTrue(p.complete);self.assertEqual(p.motion_child.push_order,(0x41a00000,0x41200000))
  self.assertEqual([w.value for w in p.motion_child.writes],[1,0x41200000,0x41a00000])

 def test_target_entry_uses_fresh_target_after_prepare_and_mode_local_does_not_filter(self):
  for mode,local in ((0,1),(1,0),(99,0)):
   p=plan_ms_target_entry(sample(mode_dword=mode,selected_target_eax=0));self.assertTrue(p.complete)
   self.assertEqual(p.unused_local_byte,local);self.assertEqual(p.stores,((0x562040,4,0),))
   self.assertEqual(next(c[1] for c in p.calls if c[2]=='target_guard'),(0x10001,0x561f34))
   self.assertFalse(p.attack_verified)

 def test_target_guard_only_lowAL_and_false_skips_selector_result(self):
  o=sample(target_guard_eax=0x100);v=dict(o.values);del v['selected_target_eax']
  p=plan_ms_target_entry(replace(o,values=v));self.assertTrue(p.complete);self.assertEqual(p.status,'target_guard_false')
  self.assertEqual(p.stores,());self.assertFalse(any(c[2]=='select_target' for c in p.calls))

 def test_target_selection_return_gap_retains_prepared_target_snapshot(self):
  f=MSCombatFrame('target_entry');o=sample();v=dict(o.values);del v['selected_target_eax']
  p=f.advance(replace(o,values=v));self.assertFalse(p.complete)
  p=f.advance(MSCombatObservation({'selected_target_eax':0xffffffff,'current_target_dword':99},{'target_entry_return':True}))
  self.assertTrue(p.complete);self.assertEqual(p.stores,((0x562040,4,0xffffffff),))
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='target_guard'),(0x10001,0x561f34))

if __name__=='__main__':unittest.main()
