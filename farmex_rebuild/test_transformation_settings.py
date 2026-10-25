import unittest
from dataclasses import replace
from transformation_settings import *

def sample(**values):
 v=dict(enabled_eax=0x102,parser_eax=1,route_eax=0x101,combo_eax=0);v.update(values)
 return TransformationSettingsObservation(True,v,{k:True for k in ('enabled','text_init','wait_text','parser','wait_cleanup','route','combo')},'$1','normal')

class TransformationSettingsTests(unittest.TestCase):
 def test_no_bounded_entry_receipt_prevents_any_call_or_store(self):
  p=plan_transformation_settings(TransformationSettingsObservation())
  self.assertFalse(p.complete);self.assertEqual(p.needed,('entry','0040929a'));self.assertEqual(p.stores,())

 def test_enabled_raw_AL_and_rearm_written_before_text_or_parser_failure(self):
  o=sample();n=dict(o.normal_returns);n['text_init']=False
  p=plan_transformation_settings(replace(o,normal_returns=n))
  self.assertEqual(p.stores,((0x562070,1,2),(0x562071,1,1)));self.assertFalse(p.complete)

 def test_exception_does_not_invent_default_or_rollback_prefix(self):
  p=plan_transformation_settings(replace(sample(),parser_route='exception_unresolved'))
  self.assertFalse(p.complete);self.assertEqual(p.needed,('unmodeled','StrToInt_exception_unwind'))
  self.assertEqual(len(p.stores),2);self.assertNotIn('wait_cleanup',[c[2] for c in p.calls])

 def test_captured_parser_allows_nondecimal_text_without_claiming_lexical_conversion(self):
  p=plan_transformation_settings(sample());self.assertTrue(p.complete)
  self.assertEqual(next(c[1] for c in p.calls if c[2]=='parser'),('$1',))
  self.assertEqual(p.milliseconds_dword,1000);self.assertFalse(p.lexical_conversion_verified)

 def test_low32_IMUL_and_all_eighteen_combo_mappings(self):
  for index,skill in enumerate(SKILLS):
   p=plan_transformation_settings(sample(parser_eax=0xffffffff,combo_eax=index))
   self.assertTrue(p.complete);self.assertEqual(p.selected_skill,skill);self.assertEqual(p.milliseconds_dword,0xfffffc18)
  for index in (18,0xffffffff,0x80000000):self.assertEqual(plan_transformation_settings(sample(combo_eax=index)).selected_skill,SKILLS[0])

 def test_wait_store_precedes_cleanup_and_route_reads_are_not_reached_early(self):
  o=sample();n=dict(o.normal_returns);n['wait_cleanup']=False
  p=plan_transformation_settings(replace(o,normal_returns=n));self.assertFalse(p.complete)
  self.assertEqual(p.stores[-1],(0x562078,4,1000));self.assertNotIn('route',[c[2] for c in p.calls])

 def test_frame_preserves_parser_and_enabled_prefix_but_reads_route_and_combo_later(self):
  f=TransformationSettingsFrame();o=sample();n=dict(o.normal_returns);n['wait_cleanup']=False
  self.assertFalse(f.advance(replace(o,normal_returns=n)).complete)
  p=f.advance(sample(enabled_eax=0,parser_eax=99,route_eax=0,combo_eax=17))
  self.assertTrue(p.complete);self.assertEqual(p.stores,((0x562070,1,2),(0x562071,1,1),(0x562078,4,1000),(0x562072,1,0),(0x562074,4,SKILLS[17])))
  self.assertFalse(p.whole_producer_verified);self.assertFalse(p.periodic_consumer_verified)

if __name__=='__main__':unittest.main()
