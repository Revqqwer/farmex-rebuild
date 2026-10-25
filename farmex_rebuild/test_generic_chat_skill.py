import unittest
from dataclasses import replace
from generic_chat_skill import GenericSkillObservation as O,plan_generic_chat_skill,versioned_generic_skill
from skill_native_plans import SkillObservation,plan_alternate_skill
from native_profile_versions import CURRENT_SOURCE_SHA256,LEGACY_SOURCE_SHA256

def sample(class_eax=107,relative=4,actor=0xffff1234,mode=1,native=0x100):
 action=(class_eax*1000+relative)&0xffffffff
 inner=SkillObservation(action,actor,{0x553e46:mode,0x553eb8:0x1000,0x553ebc:0x9000,
     0x553e80:0x2000,0x5540a0:0x10,0x553ee4:0xa000},
     {0x1000:0x3000,0x2000:0x4000,0x4010:0x5000},0x6000,native)
 return O(relative,actor,class_eax,True,True,True,inner)

class GenericSkillTests(unittest.TestCase):
 def test_relative_prefix_and_actual_helper_identity(self):
  p=plan_generic_chat_skill(sample());self.assertTrue(p.complete)
  self.assertEqual(p.action_id,107004);self.assertEqual(p.source_helper,'004655e8')
  self.assertEqual(p.operand_plan.calls[-1].helper,'004655e8')
  self.assertEqual(p.operand_plan.calls[-1].push_order,(0x6000,0xffff1234))
  self.assertEqual(p.returned_eax,0x100);self.assertFalse(p.native_execution_verified)

 def test_signed_class_bits_use_low32_overflow(self):
  p=plan_generic_chat_skill(sample(class_eax=0xffffffff,relative=1));self.assertEqual(p.action_id,0xfffffc19)
  self.assertEqual(plan_generic_chat_skill(sample(class_eax=0x80000000)).action_id,4)

 def test_each_helper_return_is_separate_from_raw_eax(self):
  o=sample()
  for name in ('class_helper_returned','lookup_wrapper_returned','native_target_returned'):
   self.assertFalse(plan_generic_chat_skill(replace(o,**{name:False})).complete,name)
  self.assertFalse(plan_generic_chat_skill(replace(o,class_eax=None)).complete)
  self.assertFalse(plan_generic_chat_skill(replace(o,operands=None)).complete)
  self.assertFalse(plan_generic_chat_skill(replace(o,operands=replace(o.operands,native_return=None))).complete)

 def test_bound_action_and_actor_must_match_arithmetic(self):
  o=sample()
  for field,value in (('action_id',999),('actor_id',1)):
   with self.assertRaises(ValueError):plan_generic_chat_skill(replace(o,operands=replace(o.operands,**{field:value})))

 def test_modes_preserve_inherited_ecx_and_zero_lookup_path(self):
  for mode,ecx in ((1,None),(2,0x3000)):
   p=plan_generic_chat_skill(sample(mode=mode));self.assertEqual(p.operand_plan.calls[0].ecx,ecx)
  o=sample(mode=3);p=plan_generic_chat_skill(replace(o,operands=replace(o.operands,lookup_return=None)))
  self.assertTrue(p.complete);self.assertEqual(len(p.operand_plan.calls),1)
  self.assertEqual(p.operand_plan.calls[0].push_order[0],0)

 def test_zero_native_return_is_known_complete_result(self):
  p=plan_generic_chat_skill(sample(native=0));self.assertTrue(p.complete);self.assertEqual(p.returned_eax,0)

 def test_existing_alternate_helper_role_default_is_preserved(self):
  o=sample();self.assertEqual(plan_alternate_skill(o.operands).calls[-1].helper,'00465640')
  with self.assertRaises(ValueError):plan_alternate_skill(o.operands,dispatch_helper='unknown')

 def test_versioned_current_factory_retains_source_identity(self):
  o=versioned_generic_skill(CURRENT_SOURCE_SHA256,'us',4,7,107,
      direct_words={0x1128a7c:0x2000,0x24a8:0x3000},lookup_return=0x4000,native_return=1,
      class_helper_returned=True,lookup_wrapper_returned=True,native_target_returned=True)
  p=plan_generic_chat_skill(o);self.assertTrue(p.complete)
  self.assertEqual((p.module_sha256,p.profile),(CURRENT_SOURCE_SHA256,'us'))
  self.assertEqual(p.operand_plan.calls[-1].target,0x88eb50)
  self.assertEqual(p.operand_plan.calls[-1].helper,'004655e8')

 def test_version_conflicts_and_unknown_metadata_rejected(self):
  with self.assertRaises(ValueError):versioned_generic_skill(CURRENT_SOURCE_SHA256,'us',4,7,107,runtime_globals={0x553ee4:1})
  with self.assertRaises(ValueError):versioned_generic_skill('unknown','us',4,7,107)
  with self.assertRaises(ValueError):replace(sample(),module_sha256=LEGACY_SOURCE_SHA256,profile='us')

 def test_missing_current_pointer_is_gap_not_implicit_old_upgrade(self):
  o=versioned_generic_skill(CURRENT_SOURCE_SHA256,'us',4,7,107,
      direct_words={0x111563c:0x2000,0x2468:0x3000},lookup_return=0x4000,native_return=1,
      class_helper_returned=True,lookup_wrapper_returned=True,native_target_returned=True)
  p=plan_generic_chat_skill(o);self.assertFalse(p.complete);self.assertIn('01128a7c',p.missing)

if __name__=='__main__':unittest.main()
