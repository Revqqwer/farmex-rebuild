import unittest
from dataclasses import replace
from allocation_queries import *

def stat_sample(match=0,result=5):
 values={'root_slot':0x1000,'root_eax':0xfffffff0,'field_offset':0x20,'field_eax':result}
 returns={k:True for k in ('entry_setup','argument_copy','root','field','argument_cleanup','return')}
 for i in range(5):
  values['compare%d.eax'%i]=0x100 if i!=match else 0x101
  for suffix in ('literal_init','compare','literal_cleanup'):returns['compare%d.%s'%(i,suffix)]=True
 return AllocationQueryObservation(values,returns)

def skill_sample(result=5):
 return AllocationQueryObservation(dict(root_slot=0x1000,root_eax=0xfffffff0,context_offset=0x20,context_eax=0x4000,field_offset=0x30,field_eax=result),{k:True for k in ('root','context','field','return')})

class AllocationQueryTests(unittest.TestCase):
 def test_five_stat_literals_order_and_nonmonotonic_MP_INT_offsets(self):
  self.assertEqual(STAT_FIELDS,((b'STR',0x5540f4),(b'HP',0x5540f8),(b'DEX',0x5540fc),(b'MP',0x554104),(b'INT',0x554100)))
  for i,(name,offset) in enumerate(STAT_FIELDS):
   with self.subTest(name=name):
    p=plan_allocation_query('stat',0x1234,stat_sample(i));self.assertTrue(p.complete)
    self.assertEqual(p.selected_field,name);self.assertEqual(len(p.comparisons),i+1)
    self.assertIn((offset,4,'field_offset'),p.reads);self.assertEqual(p.return_eax,5)
    self.assertEqual(next(c for c in p.calls if c[2]=='field')[1],(0x10,))
    self.assertFalse(p.name_pointer_identity_verified)
 def test_no_matching_stat_returns_zero_after_argument_cleanup_without_reads(self):
  p=plan_allocation_query('stat',0x1234,stat_sample(-1));self.assertTrue(p.complete)
  self.assertEqual(p.return_eax,0);self.assertEqual(p.reads,());self.assertEqual(len(p.comparisons),5)
  self.assertEqual(p.calls[-2][2],'argument_cleanup')
 def test_comparison_result_retained_across_literal_cleanup_gap(self):
  f=AllocationQueryFrame('stat',0x1234);o=stat_sample();n=dict(o.normal_returns);n['compare0.literal_cleanup']=False
  p=f.advance(replace(o,normal_returns=n));self.assertEqual(p.needed,('normal','compare0.literal_cleanup'))
  v=dict(o.values);v['compare0.eax']=0;p=f.advance(replace(o,values=v))
  self.assertTrue(p.complete);self.assertEqual(p.selected_field,b'STR')
 def test_value_retained_before_argument_cleanup_and_separate_return(self):
  f=AllocationQueryFrame('stat',0x1234);o=stat_sample(result=0x87654321);n=dict(o.normal_returns);n['argument_cleanup']=False
  p=f.advance(replace(o,normal_returns=n));self.assertEqual(p.return_eax,0x87654321);self.assertFalse(p.complete)
  p=f.advance(AllocationQueryObservation(normal_returns={'argument_cleanup':True}));self.assertEqual(p.needed,('normal','return'))
  self.assertTrue(f.advance(AllocationQueryObservation(normal_returns={'return':True})).complete)
 def test_skill_indices_have_three_guarded_reads_and_exact_offset_slots(self):
  for index,address in SKILL_FIELDS.items():
   p=plan_allocation_query('skill',index,skill_sample());self.assertTrue(p.complete)
   self.assertIn((address,4,'field_offset'),p.reads)
   self.assertEqual(p.calls[:3],(('0045dc44',(0x1000,),'root'),('0045dc44',(0x10,),'context'),('0045dc44',(0x4030,),'field')))
 def test_unsupported_skill_preserves_incoming_EAX_and_does_not_guess_zero(self):
  for argument in (0,5,0xffffffff):
   f=AllocationQueryFrame('skill',argument);p=f.advance(AllocationQueryObservation())
   self.assertEqual(p.needed,('value','incoming_eax'))
   p=f.advance(AllocationQueryObservation({'incoming_eax':0x87654321},{'return':True}))
   self.assertTrue(p.complete);self.assertEqual(p.return_eax,0x87654321);self.assertEqual(p.reads,())
 def test_child_blocks_caller_and_requires_separate_outer_normal(self):
  from auto_allocation import AutoAllocationFrame
  from test_auto_allocation import sample
  f=AutoAllocationFrame();o=replace(sample(),query_children={'stat0.query':AllocationQueryObservation()})
  p=f.advance(o);self.assertEqual(p.needed,('child','stat0.query'));self.assertEqual(p.actions,())
  n=dict(o.normal_returns);n['stat0.query']=False
  p=f.advance(replace(o,normal_returns=n,query_children={'stat0.query':stat_sample()}))
  self.assertTrue(p.children[0][1].complete);self.assertEqual(p.needed,('normal','stat0.query'))
  p=f.advance(sample(**{'stat0.key':99}));self.assertTrue(p.complete)
  self.assertEqual(p.children[0][1].argument,9)
 def test_caller_full_EAX_must_agree_with_generated_query(self):
  from auto_allocation import AutoAllocationFrame
  from test_auto_allocation import sample
  f=AutoAllocationFrame()
  with self.assertRaisesRegex(ValueError,'full EAX'):f.advance(replace(sample(),query_children={'stat0.query':stat_sample(result=6)}))
 def test_skill_query_binding_and_retroactive_query_rejection(self):
  from auto_allocation import AutoAllocationFrame
  from test_auto_allocation import sample
  o=sample(stat_enabled_byte=0,**{'skill0.query_argument':2});f=AutoAllocationFrame()
  p=f.advance(replace(o,query_children={'skill0.query':skill_sample()}));self.assertTrue(p.complete)
  self.assertEqual(p.children[0][1].selected_field,2)
  f=AutoAllocationFrame();n=dict(o.normal_returns);n['post_tick']=False;self.assertFalse(f.advance(replace(o,normal_returns=n)).complete)
  with self.assertRaisesRegex(ValueError,'retroactively'):f.advance(replace(o,query_children={'skill0.query':skill_sample()}))
 def test_types_rejected(self):
  with self.assertRaises(ValueError):AllocationQueryFrame('skill',True)
  with self.assertRaises(ValueError):AllocationQueryObservation({'field_eax':False})
  from auto_allocation import AutoAllocationObservation
  with self.assertRaises(ValueError):AutoAllocationObservation(query_children={'free_skill':skill_sample()})

if __name__=='__main__':unittest.main()
