import unittest
from dataclasses import replace
from chat_skill_consumers import ChatConsumerObservation as O,ChatConsumerFrame,plan_chat_consumer
from generic_chat_skill import GenericSkillObservation as G,plan_generic_chat_skill,versioned_generic_skill
from skill_native_plans import SkillObservation,plan_alternate_skill
from native_profile_versions import CURRENT_SOURCE_SHA256
from test_chat_skill_consumers import sample as mr_sample
from test_priest_chat_consumer import sample as priest_sample

def child(relative,actor,eax=0x100,**changes):
 cls=107;inner=SkillObservation(cls*1000+relative,actor,
  {0x553e46:1,0x553ebc:0x9000,0x553e80:0x1000,0x5540a0:0x10,0x553ee4:0xa000},
  {0x1000:0x2000,0x2010:0x3000},0x4000,eax)
 return plan_generic_chat_skill(replace(G(relative,actor,cls,True,True,True,inner),**changes))
def fixture(family,kind=1):
 if family=='Priest':return priest_sample(kind),{1:700,2:701,3:0x28e,4:4,5:0x20d,6:0x217}[kind]
 return mr_sample(kind_dword=kind,generic_skill_eax=0x100),4 if family=='Mage' else 10 if kind==1 else 30
def plan(family,o):return plan_chat_consumer(family,0x5000,o)

class GenericConsumerBindingTests(unittest.TestCase):
 def test_all_nine_reached_generic_calls_bind_exact_arguments(self):
  for family,kinds in (('Mage',(1,)),('Rogue',(1,2)),('Priest',range(1,7))):
   for kind in kinds:
    o,relative=fixture(family,kind);v=dict(o.values);v['generic_skill_eax']=0x100
    c=child(relative,v['generic_sender_dword']);p=plan(family,O(v,o.normal_returns,c))
    self.assertTrue(p.complete);self.assertEqual(p.return_low_al,1);self.assertIs(p.generic_execution,c)

 def test_parent_positive_normals_cannot_bypass_any_child_gap(self):
  for family in ('Mage','Rogue','Priest'):
   o,relative=fixture(family)
   for fields in ({'class_helper_returned':False},{'lookup_wrapper_returned':False},{'native_target_returned':False},
                  {'operands':None}):
    c=child(relative,o.values['generic_sender_dword'],**fields)
    p=plan(family,replace(o,generic_execution=c))
    self.assertFalse(p.complete);self.assertTrue(p.missing.startswith('bound generic:'))
    self.assertEqual(p.stores,())

 def test_complete_child_still_requires_separate_parent_normal(self):
  for family in ('Mage','Rogue','Priest'):
   o,relative=fixture(family);c=child(relative,o.values['generic_sender_dword'])
   r=dict(o.normal_returns);r['generic_skill']=False
   p=plan(family,O(o.values,r,c));self.assertFalse(p.complete)
   self.assertEqual(p.missing,'generic_skill normal return');self.assertIs(p.generic_execution,c)

 def test_raw_result_mismatch_is_rejected_for_all_families(self):
  for family in ('Mage','Rogue','Priest'):
   o,relative=fixture(family);v=dict(o.values);v['generic_skill_eax']=0
   with self.assertRaises(ValueError):plan(family,O(v,o.normal_returns,child(relative,v['generic_sender_dword'])))

 def test_known_zero_child_and_parent_preserve_pending(self):
  for family in ('Mage','Rogue','Priest'):
   o,relative=fixture(family);v=dict(o.values);v['generic_skill_eax']=0
   p=plan(family,O(v,o.normal_returns,child(relative,v['generic_sender_dword'],0)))
   self.assertTrue(p.complete);self.assertEqual(p.return_low_al,0);self.assertEqual(p.stores,())

 def test_wrong_skill_or_full_actor_rejected_only_when_reached(self):
  for family in ('Mage','Rogue','Priest'):
   o,relative=fixture(family)
   for c in (child(relative+1,o.values['generic_sender_dword']),child(relative,7)):
    with self.assertRaises(ValueError):plan(family,replace(o,generic_execution=c))
    v=dict(o.values);v['pending_byte']=0
    p=plan(family,O(v,o.normal_returns,c));self.assertTrue(p.complete);self.assertIsNone(p.generic_execution)

 def test_frame_resumes_child_then_parent_without_prior_receipts_again(self):
  for family in ('Mage','Rogue','Priest'):
   o,relative=fixture(family);v=dict(o.values);v['generic_skill_eax']=0x100
   gap=child(relative,v['generic_sender_dword'],native_target_returned=False)
   f=ChatConsumerFrame(family,0x5000);self.assertFalse(f.advance(O(v,o.normal_returns,gap)).complete)
   c=child(relative,v['generic_sender_dword']);p=f.advance(O(v,o.normal_returns,c))
   self.assertTrue(p.complete);self.assertIs(p.generic_execution,c)
   self.assertIs(f.advance(O()),p)

 def test_incomplete_frame_rejects_changed_class_snapshot(self):
  o,relative=fixture('Mage');actor=o.values['generic_sender_dword']
  gap=child(relative,actor,native_target_returned=False);f=ChatConsumerFrame('Mage',0x5000)
  self.assertFalse(f.advance(replace(o,generic_execution=gap)).complete)
  source=gap.input_snapshot;different=replace(source,class_eax=108,operands=replace(source.operands,action_id=108000+relative))
  with self.assertRaises(ValueError):f.advance(O(generic_execution=plan_generic_chat_skill(different)))

 def test_stable_map_may_be_enriched_but_old_values_cannot_change(self):
  o,relative=fixture('Mage');actor=o.values['generic_sender_dword'];done=child(relative,actor)
  src=done.input_snapshot;partial=replace(src,operands=replace(src.operands,direct_words={0x1000:0x2000}))
  f=ChatConsumerFrame('Mage',0x5000);self.assertFalse(f.advance(replace(o,generic_execution=plan_generic_chat_skill(partial))).complete)
  bad=replace(src,operands=replace(src.operands,direct_words={0x1000:0x2222,0x2232:0x3000}))
  with self.assertRaises(ValueError):f.advance(O(generic_execution=plan_generic_chat_skill(bad)))
  v=dict(o.values);v['generic_skill_eax']=0x100
  self.assertTrue(f.advance(O(v,o.normal_returns,done)).complete)

 def test_completed_child_is_retained_across_later_clock_gap(self):
  o,relative=fixture('Mage');v=dict(o.values);del v['post_delay_tick'];v['generic_skill_eax']=0x100
  c=child(relative,v['generic_sender_dword']);f=ChatConsumerFrame('Mage',0x5000)
  p=f.advance(O(v,o.normal_returns,c));self.assertFalse(p.complete)
  wrong=child(relative+1,7)
  p=f.advance(O({'post_delay_tick':999},generic_execution=wrong))
  self.assertTrue(p.complete);self.assertIs(p.generic_execution,c)
  self.assertIn((0x561f84,4,999),p.stores)

 def test_current_profile_metadata_survives_parent_result(self):
  o,relative=fixture('Mage');v=dict(o.values);v['generic_skill_eax']=0x100
  obs=versioned_generic_skill(CURRENT_SOURCE_SHA256,'us',relative,v['generic_sender_dword'],107,
   direct_words={0x1128a7c:0x2000,0x24a8:0x3000},lookup_return=0x4000,native_return=0x100,
   class_helper_returned=True,lookup_wrapper_returned=True,native_target_returned=True)
  p=plan('Mage',O(v,o.normal_returns,plan_generic_chat_skill(obs)))
  self.assertTrue(p.complete);self.assertEqual(p.generic_execution.module_sha256,CURRENT_SOURCE_SHA256)
  self.assertFalse(p.skill_effect_verified)

 def test_old_dispatch_role_cannot_be_relabelled_as_complete_generic(self):
  c=child(4,7)
  with self.assertRaises(ValueError):replace(c,operand_plan=plan_alternate_skill(c.input_snapshot.operands))

if __name__=='__main__':unittest.main()
