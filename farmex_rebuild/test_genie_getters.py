import unittest
from dataclasses import replace
from genie_getters import GenieGetterFrame,plan_genie_getter,source_getter_observation,source_getter_globals
from native_profile_versions import LEGACY_SOURCE_SHA256 as OLD,CURRENT_SOURCE_SHA256 as CURRENT
from motion_genie_helpers import MotionGenieObservation as O,GuardedReadReceipt as R

def sample(helper='004631c8',root=0x2000,raw=0xaabbcc01):
 slot=0x554070 if helper=='004631c8' else 0x554074
 return O(((0x553e7c,0x1000),(slot,0x20)),(R(0x1000,4,root,True),R((root+0x20)&0xffffffff,1,raw,True)),normal_returns={'wrapper_return':True})

class GenieGetterTests(unittest.TestCase):
 def test_both_helpers_read_dword_root_then_byte_and_preserve_full_eax(self):
  for helper in ('004631c8','004631e8'):
   p=plan_genie_getter(helper,sample(helper,raw=0xaabbcc00))
   self.assertTrue(p.complete);self.assertEqual(p.raw_eax,0xaabbcc00);self.assertEqual(p.low_al,0)
   self.assertEqual([s[3] for s in p.steps if s[0]=='guarded'],[4,1]);self.assertFalse(p.protection_side_effects_emulated)

 def test_wrong_field_width_or_address_rejected(self):
  o=sample()
  for r in (R(0x2020,4,1,True),R(0x2021,1,1,True)):
   with self.assertRaises(ValueError):plan_genie_getter('004631c8',replace(o,guarded_reads=(o.guarded_reads[0],r)))
  with self.assertRaises(ValueError):plan_genie_getter('004631e8',o)

 def test_null_root_does_not_skip_nonzero_offset_byte_read(self):
  o=sample(root=0);p=plan_genie_getter('004631c8',replace(o,guarded_reads=o.guarded_reads[:1]))
  self.assertFalse(p.complete);self.assertEqual(p.request.address,0x20)
  self.assertTrue(plan_genie_getter('004631c8',o).complete)

 def test_ordered_prefix_and_separate_wrapper_return_are_required(self):
  o=sample();f=GenieGetterFrame('004631c8')
  p=f.advance(replace(o,guarded_reads=o.guarded_reads[:1]));self.assertFalse(p.complete)
  changed=replace(o,global_samples=((0x553e7c,0x9999),(0x554070,0x9999)),normal_returns={})
  p=f.advance(changed);self.assertFalse(p.complete);self.assertEqual(p.missing,'wrapper_return normal return')
  self.assertEqual(p.raw_eax,0xaabbcc01)
  p=f.advance(O(normal_returns={'wrapper_return':True}));self.assertTrue(p.complete);self.assertIs(f.advance(O()),p)

 def test_nonreturned_guarded_receipt_can_be_completed_later(self):
  o=sample();f=GenieGetterFrame('004631c8')
  p=f.advance(replace(o,guarded_reads=(o.guarded_reads[0],replace(o.guarded_reads[1],normal_returned=False))))
  self.assertFalse(p.complete);self.assertTrue(f.advance(o).complete)

 def test_explicit_old_current_profile_literals_and_metadata(self):
  roots={(OLD,'us'):0x1115574,(OLD,'steam'):0x11ea638,(CURRENT,'us'):0x11289c0,(CURRENT,'steam'):0x11e9638}
  for (sha,profile),slot in roots.items():
   for helper,offset in (('004631c8',0x760),('004631e8',0x75c)):
    o=source_getter_observation(sha,profile,helper,(R(slot,4,0x2000,True),R(0x2000+offset,1,0x12345678,True)),{'wrapper_return':True})
    p=plan_genie_getter(helper,o,module_sha256=sha,profile=profile)
    self.assertTrue(p.complete);self.assertEqual((p.module_sha256,p.profile,p.low_al),(sha,profile,0x78))

 def test_profile_conflict_and_implicit_source_defaults_are_rejected_or_missing(self):
  with self.assertRaises(ValueError):source_getter_globals('unknown','us','004631c8')
  with self.assertRaises(ValueError):plan_genie_getter('004631c8',sample(),module_sha256=CURRENT,profile='us')
  p=plan_genie_getter('004631c8',O());self.assertFalse(p.complete);self.assertEqual(p.request.kind,'global')
  self.assertIsNone(p.module_sha256)

if __name__=='__main__':unittest.main()
