import unittest
from dataclasses import replace
from allocation_producer import *
from source_integer import SourceIntegerObservation

def number(q):return SourceIntegerObservation(True,'normal',True,q,cleanup_returned=True)

def sample(**updates):
 values=dict(stat_enabled_eax=0,skill_enabled_eax=0)
 normals={k:True for k in ('stat_enabled','skill_enabled','stat_clear','skill_clear')};texts={};names={};integers={}
 for domain,name,identifier in (('stat','STR',3),('skill','Attack',1)):
  pre=domain+'0.'
  values.update({pre+'count_eax':1,domain+'1.count_eax':0,pre+'size_eax':0,pre+'capacity_eax':2,
   pre+'end_dword':0x1000,pre+'new_end_eax':0x100c})
  for label in ('count','row_init','name_get','name_conversion_cleanup','caption_get','action_integer',
   'caption_cleanup','threshold_get','threshold_integer','threshold_cleanup','size','capacity','fast_append','reallocate','row_cleanup'):
   normals[pre+label]=True
  normals[domain+'1.count']=True
  texts.update({pre+'name':name,pre+'caption':str(identifier),pre+'threshold':'100'})
  names[pre+'name']=name.encode('ascii')
  integers.update({pre+'action_integer':number(identifier),pre+'threshold_integer':number(100)})
 values.update(updates)
 return AllocationProducerObservation(True,values,normals,texts,names,integers)

class AllocationProducerTests(unittest.TestCase):
 def test_entry_receipt_precedes_all_getters_and_clears(self):
  p=plan_allocation_producer(AllocationProducerObservation());self.assertFalse(p.complete)
  self.assertEqual(p.needed,('entry','00457700'));self.assertEqual(p.calls,());self.assertEqual(p.cleared_vectors,())

 def test_flags_off_do_not_skip_lists_and_three_fields_preserve_source_layout(self):
  p=AllocationProducerFrame().advance(sample());self.assertTrue(p.complete)
  self.assertEqual(p.stat_rows,(AllocationRow(b'STR',3,100,0),));self.assertEqual(p.skill_rows,(AllocationRow(b'Attack',1,100,0),))
  self.assertEqual(p.cleared_vectors,('stat','skill'));self.assertEqual(p.stores[:2],((0x5621b4,1,0),(0x5621b5,1,0)))
  self.assertEqual(p.stores[2:],((0x5621d0,4,0x100c),(0x5621f0,4,0x100c)))

 def test_exact_caption_and_subitem_column_calls(self):
  p=AllocationProducerFrame().advance(sample())
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='stat0.name_get'),('form_field',0xf40,0,0))
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='stat0.caption_get'),('form_field',0xf40,0))
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='stat0.threshold_get'),('form_field',0xf40,0,1))

 def test_caption_and_threshold_are_independent_generated64bit_conversions_with_minus_one_default(self):
  o=sample();children=dict(o.integer_inputs)
  children['stat0.action_integer']=number(0x100000003)
  children['stat0.threshold_integer']=SourceIntegerObservation(True,'catch_landing',catch_landing_returned=True,cleanup_returned=True)
  p=AllocationProducerFrame().advance(replace(o,integer_inputs=children));self.assertTrue(p.complete)
  self.assertEqual((p.stat_rows[0].action_dword,p.stat_rows[0].threshold_dword),(3,0xffffffff))
  self.assertTrue(all(c.default_qword==0xffffffffffffffff for label,c in p.conversions))

 def test_outer_integer_normal_cannot_bypass_missing_child_and_empty_text_is_not_automatic_default(self):
  o=sample();children=dict(o.integer_inputs);children['stat0.action_integer']=SourceIntegerObservation(True)
  texts={**o.texts,'stat0.caption':''}
  p=AllocationProducerFrame().advance(replace(o,texts=texts,integer_inputs=children))
  self.assertFalse(p.complete);self.assertEqual(p.needed,('integer','stat0.action_integer'));self.assertEqual(p.stat_rows,())
  self.assertEqual(p.cleared_vectors,('stat',))

 def test_missing_subitem_text_is_explicit_gap_not_empty_string(self):
  o=sample();texts=dict(o.texts);del texts['stat0.threshold']
  p=AllocationProducerFrame().advance(replace(o,texts=texts));self.assertFalse(p.complete)
  self.assertEqual(p.needed,('text','stat0.threshold'));self.assertEqual(p.stat_rows,())

 def test_signed_UI_count_and_reallocation_equality_have_distinct_source_effects(self):
  p=AllocationProducerFrame().advance(sample(**{'stat0.count_eax':0xffffffff,'skill0.count_eax':0}))
  self.assertTrue(p.complete);self.assertEqual(p.stat_rows,());self.assertEqual(p.skill_rows,())
  p=AllocationProducerFrame().advance(sample(**{'stat0.size_eax':2,'stat0.capacity_eax':2}))
  self.assertTrue(p.complete);self.assertEqual(len(p.stat_rows),1)
  self.assertNotIn((0x5621d0,4,0x100c),p.stores)
  self.assertIn('stat0.reallocate',[c[2] for c in p.calls])

 def test_appended_row_and_consumed_text_survive_row_cleanup_gap(self):
  f=AllocationProducerFrame();o=sample();n=dict(o.normal_returns);n['stat0.row_cleanup']=False
  p=f.advance(replace(o,normal_returns=n));self.assertFalse(p.complete);self.assertEqual(len(p.stat_rows),1)
  p=f.advance(replace(o,texts={**o.texts,'stat0.caption':'99'},names={**o.names,'stat0.name':b'changed'}))
  self.assertTrue(p.complete);self.assertEqual(p.stat_rows,(AllocationRow(b'STR',3,100,0),))
  self.assertFalse(p.codec_verified);self.assertFalse(p.whole_producer_verified)

 def test_budget_does_not_skip_fresh_count_or_enter_next_list(self):
  f=AllocationProducerFrame(row_budget=1);p=f.advance(sample());self.assertFalse(p.complete)
  self.assertEqual(p.needed,('budget','stat_UI_count_still_open'));self.assertEqual(p.cleared_vectors,('stat',))
  f.extend_budget(2);p=f.advance(sample());self.assertTrue(p.complete);self.assertEqual(len(p.stat_rows),1)

 def test_fast_append_end_math_wraps_and_conflicting_direct_capture_rejects(self):
  o=sample(**{'stat0.end_dword':0xfffffff8,'stat0.new_end_eax':4})
  p=plan_allocation_producer(o);self.assertTrue(p.complete)
  self.assertIn((0x5621d0,4,4),p.stores)
  with self.assertRaisesRegex(ValueError,'end\\+12'):
   plan_allocation_producer(sample(**{'stat0.new_end_eax':0x9999}))
  with self.assertRaisesRegex(ValueError,'end\\+12'):
   AllocationProducerFrame().advance(sample(**{'stat0.new_end_eax':0x9999}))

if __name__=='__main__':unittest.main()
