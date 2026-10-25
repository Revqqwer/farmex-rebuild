import unittest
from dataclasses import replace
from allocation_actions import *

def skill():
 return AllocationActionObservation(dict(direct_root_slot=0x1000,direct_root=0x2000,skill_context_offset=0x20,skill_context=0x3000,callback_target=0x12345678),{'callback':True,'return':True})

def stat():
 v=dict(guarded_root_slot=0x1000,guarded_root_eax=0xfffffff0,guarded_first_offset=0x20,
 guarded_first_eax=0x4000,guarded_second_offset=0x30,guarded_second_eax=0xfffffff0,
 stat_table_offset=0x20,guarded_stat_entry_eax=0x76543210,
 direct_root_slot=0x5000,direct_root=0x6000,direct_first_offset=0x40,direct_first=0x7000,
 direct_second_offset=0x50,direct_second=0x8000,callback_offset=0x60,vtable=0x9000,callback_target=0xabcdef12)
 return AllocationActionObservation(v,{k:True for k in ('guarded_root','guarded_first','guarded_second','guarded_stat_entry','callback','return')})

class AllocationActionTests(unittest.TestCase):
 def test_stat_guarded_chain_and_fresh_direct_dispatch_are_distinct(self):
  p=plan_allocation_action('stat',3,stat());self.assertTrue(p.complete)
  self.assertEqual(p.calls[:4],(('0045dc44',(0x1000,),'guarded_root'),('0045dc44',(0x10,),'guarded_first'),('0045dc44',(0x4030,),'guarded_second'),('0045dc44',(0x1c,),'guarded_stat_entry')))
  self.assertEqual(p.invocation,(0xabcdef12,0x8000,(1,0x76543210)))
  self.assertIn((0x6040,4,'direct_first'),p.reads);self.assertIn((0x7050,4,'direct_second'),p.reads)
  self.assertIn((0x9060,4,'callback_target'),p.reads)
  self.assertFalse(p.callback_ABI_verified);self.assertFalse(p.allocation_effect_verified)
 def test_stat_argument_is_raw_wrapped_shift_not_assumed_stat_enum(self):
  p=plan_allocation_action('stat',0x40000001,stat())
  self.assertEqual(p.calls[3][1],(0x14,))
 def test_skill_wraps_argument_plus_four_and_has_no_guarded_chain(self):
  p=plan_allocation_action('skill',0xfffffffe,skill());self.assertTrue(p.complete)
  self.assertEqual(p.invocation,(0x12345678,0x3000,(2,)))
  self.assertEqual(p.reads,((0x553e80,4,'direct_root_slot'),(0x1000,4,'direct_root'),(0x554054,4,'skill_context_offset'),(0x2020,4,'skill_context'),(0x553f0c,4,'callback_target')))
  self.assertEqual(len(p.calls),2)
 def test_callback_and_helper_return_are_separate_gaps(self):
  f=AllocationActionFrame('skill',1);o=skill()
  p=f.advance(replace(o,normal_returns={}));self.assertEqual(p.needed,('normal','callback'))
  p=f.advance(AllocationActionObservation(normal_returns={'callback':True}));self.assertEqual(p.needed,('normal','return'))
  p=f.advance(AllocationActionObservation(normal_returns={'return':True}));self.assertTrue(p.complete)
  self.assertEqual(p.invocation,(0x12345678,0x3000,(5,)))
 def test_frame_caches_only_reached_operands(self):
  f=AllocationActionFrame('stat',3);o=stat();v=dict(o.values);v['direct_root_slot']=1
  p=f.advance(replace(o,values=v,normal_returns={}));self.assertEqual(p.needed,('normal','guarded_root'))
  p=f.advance(o);self.assertTrue(p.complete)
  self.assertIn((0x5000,4,'direct_root'),p.reads)
  self.assertEqual(p.calls[0][1],(0x1000,))
 def test_incomplete_child_blocks_parent_action_and_stamp_even_with_outer_receipt(self):
  from auto_allocation import AutoAllocationFrame
  from test_auto_allocation import sample
  f=AutoAllocationFrame();o=replace(sample(),action_children={'stat0.action':AllocationActionObservation()})
  p=f.advance(o);self.assertEqual(p.needed,('child','stat0.action'));self.assertEqual(p.actions,());self.assertEqual(p.stores,())
  n=dict(o.normal_returns);n['stat0.action']=False
  p=f.advance(replace(o,normal_returns=n,action_children={'stat0.action':stat()}))
  self.assertEqual(p.needed,('normal','stat0.action'));self.assertTrue(p.children[0][1].complete)
  p=f.advance(sample(**{'stat0.action_argument':99}));self.assertTrue(p.complete)
  self.assertEqual(p.actions,(('stat',0,11),));self.assertEqual(p.children[0][1].argument,11)
 def test_skill_child_binds_selected_argument_and_separate_outer_return(self):
  from auto_allocation import AutoAllocationFrame
  from test_auto_allocation import sample
  f=AutoAllocationFrame();o=replace(sample(stat_enabled_byte=0),action_children={'skill0.action':skill()})
  p=f.advance(o);self.assertTrue(p.complete)
  self.assertEqual(p.children[0][1].invocation,(0x12345678,0x3000,(15,)))
 def test_retroactive_binding_rejected_after_opaque_action_before_clock(self):
  from auto_allocation import AutoAllocationFrame
  from test_auto_allocation import sample
  f=AutoAllocationFrame();o=sample();n=dict(o.normal_returns);n['post_tick']=False
  self.assertFalse(f.advance(replace(o,normal_returns=n)).complete)
  with self.assertRaises(ValueError):f.advance(replace(o,action_children={'stat0.action':stat()}))
 def test_bad_types_rejected(self):
  for arg in (True,-1,1<<32):
   with self.assertRaises(ValueError):AllocationActionFrame('stat',arg)
  with self.assertRaises(ValueError):AllocationActionObservation({'root':True})
  with self.assertRaises(ValueError):AllocationActionObservation(normal_returns={'callback':1})
  from auto_allocation import AutoAllocationObservation
  with self.assertRaises(ValueError):AutoAllocationObservation(action_children={'initial_tick':skill()})

if __name__=='__main__':unittest.main()
