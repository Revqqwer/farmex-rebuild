import unittest
from dataclasses import replace
from monster_stone_boss_filter import *

def sample(entries=1,match=0,**changes):
 values={'empty_compare_eax':0};normals={k:True for k in ('frame_setup','empty_compare','empty_cleanup','return_cleanup')}
 for i in range(entries+1):
  pre='e%d.'%i
  values.update({pre+'begin_check':0x1000,pre+'end':0x1000+entries*4,pre+'begin_subtract':0x1000,
   pre+'begin_entry':0x2000,pre+'compare_eax':int(i==match)})
  normals.update({pre+k:True for k in ('candidate_convert','compare','temporary_cleanup')})
 values.update(changes);return MSBossFilterObservation(values,normals)

def plan(o,**kw):return plan_ms_boss_filter(o,candidate_name='Captured boss',**kw)

class BossFilterTests(unittest.TestCase):
 def test_empty_comparison_low_byte_returns_zero_after_cleanup(self):
  p=plan(sample(empty_compare_eax=0x102));self.assertTrue(p.complete)
  self.assertEqual(p.return_eax,0);self.assertEqual(p.reads,())
  self.assertEqual([c[2] for c in p.calls],['frame_setup','empty_compare','empty_cleanup','return_cleanup'])

 def test_null_begin_skips_end_and_subtract(self):
  p=plan(MSBossFilterObservation({'empty_compare_eax':0,'e0.begin_check':0},sample().normal_returns))
  self.assertTrue(p.complete);self.assertEqual(p.counts,(0,));self.assertEqual(p.return_al,0)

 def test_each_iteration_reconverts_candidate_and_reads_entry_begin_fresh(self):
  p=plan(sample(entries=3,match=1,**{'e1.begin_entry':0x9000}));self.assertTrue(p.complete)
  self.assertEqual(p.matched_index,1);self.assertEqual(p.return_al,1);self.assertIsNone(p.return_eax)
  self.assertEqual([c[1] for c in p.calls if c[2].endswith('.compare')],
   [('converted_candidate_temporary',0x2000),('converted_candidate_temporary',0x9004)])
  self.assertEqual(len([c for c in p.calls if c[1]==('Captured boss',) and c[0]=='004073a0']),2)

 def test_count_begin_check_and_subtraction_are_distinct_fresh_reads(self):
  p=plan(sample(**{'e0.begin_check':0x1234,'e0.end':0x3004,'e0.begin_subtract':0x3000}))
  self.assertTrue(p.complete);self.assertEqual(p.counts,(1,))
  self.assertEqual([r[2] for r in p.reads],['e0.begin_check','e0.end','e0.begin_subtract','e0.begin_entry'])

 def test_count_rounds_negative_toward_zero_then_compares_unsigned(self):
  for delta,expected,matched in ((-1,0,False),(-3,0,False),(-4,0xffffffff,True),(3,0,False),(4,1,True)):
   p=plan(sample(**{'e0.end':0x1000+delta}));self.assertTrue(p.complete)
   self.assertEqual(p.counts,(expected,));self.assertEqual(p.return_al,int(matched))
  p=plan(sample(**{'e0.end':0,'e0.begin_subtract':0xfffffffc}));self.assertEqual(p.counts,(1,))

 def test_dynamic_count_rechecked_after_first_failed_comparison(self):
  p=plan(sample(entries=2,match=1,**{'e1.begin_check':0}))
  self.assertTrue(p.complete);self.assertEqual(p.counts,(2,0));self.assertEqual(p.return_al,0)
  self.assertNotIn('e1.candidate_convert',[c[2] for c in p.calls])

 def test_no_python_string_equality_inference_and_cleanup_blocks_success(self):
  o=sample(**{'e0.compare_eax':0x100});p=plan(o)
  self.assertTrue(p.complete);self.assertEqual(p.return_al,0)
  n=dict(o.normal_returns);n['e0.temporary_cleanup']=False
  p=plan(replace(sample(),normal_returns=n));self.assertFalse(p.complete);self.assertIsNone(p.return_al)
  self.assertEqual(p.needed,('normal','e0.temporary_cleanup'))

 def test_frame_retains_consumed_comparison_while_cleanup_waits(self):
  o=sample(entries=2,match=1);n=dict(o.normal_returns);n['e0.temporary_cleanup']=False
  f=MSBossFilterFrame(candidate_name='Captured boss');p=f.advance(replace(o,normal_returns=n))
  self.assertFalse(p.complete)
  p=f.advance(sample(entries=2,match=0));self.assertTrue(p.complete)
  self.assertEqual(p.return_al,0) #Consumed first comparison remains false; fresh second is false.

 def test_budget_exhaustion_has_no_invented_false_return(self):
  o=sample(entries=2,match=1);f=MSBossFilterFrame(candidate_name='Captured boss',entry_budget=1)
  p=f.advance(o);self.assertFalse(p.complete);self.assertIsNone(p.return_al)
  self.assertEqual(p.needed,('budget','source_vector_loop_still_open'))
  f.extend_budget(2);self.assertEqual(f.advance(o).return_al,1)

 def test_selector_child_gap_and_outer_AL_agreement(self):
  from monster_stone_selector import MSSelectorFrame,MSSelectorObservation,plan_ms_selector
  from test_monster_stone_selector import fixture
  f=MSSelectorFrame();o=replace(fixture(),boss_filters={0:MSBossFilterObservation()})
  p=f.advance(o);self.assertFalse(p.complete);self.assertEqual(p.needed,('boss_filter','n0.boss_filter'))
  n=dict(o.normal_returns);n['n0.boss_filter']=False
  p=f.advance(replace(o,normal_returns=n,boss_filters={0:sample()}));self.assertFalse(p.complete)
  self.assertTrue(p.boss_filter_children[0][1].complete)
  p=f.advance(MSSelectorObservation(normal_returns={'n0.boss_filter':True},values={k:v for k,v in fixture().values.items()},names=fixture().names))
  #The remaining iterator normals are independent and must still be supplied.
  self.assertFalse(p.complete)
  self.assertTrue(f.advance(fixture()).complete)
  with self.assertRaisesRegex(ValueError,'AL differs'):
   plan_ms_selector(replace(fixture(),boss_filters={0:sample(empty_compare_eax=1)}))

if __name__=='__main__':unittest.main()
