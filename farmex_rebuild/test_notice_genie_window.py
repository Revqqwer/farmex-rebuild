import unittest
from notice_genie_window import NoticeGenieObservation as O,NoticeGenieFrame,plan_notice_genie_window as plan

def sample(**updates):
 values=dict(enabled_byte=1,mode_dword=3,presence_stamp_low=100,presence_stamp_high=0,
  window_tick=1000,window_stamp_low=100,window_stamp_high=0,minutes_dword=1,no_attack_byte=1,
  start_state_eax=0,start_cooldown_tick=1000,start_cooldown_stamp_low=0,start_cooldown_stamp_high=0,
  remaining_eax=1,start_post_tick=1001,other_stop_flag_2d=1,stop_state_eax=1,stop_cooldown_tick=1000,
  stop_cooldown_stamp_low=0,stop_cooldown_stamp_high=0,stop_post_tick=1002)
 values.update(updates)
 return O(values,{k:True for k in ('window_tick','start_state','start_cooldown_tick','remaining','genie_start','start_post_tick',
  'stop_state','stop_cooldown_tick','genie_stop','stop_post_tick','epilogue')})

class NoticeGenieTests(unittest.TestCase):
 def test_active_window_starts_with_fresh_post_tick_and_no_attack_store_first(self):
  p=plan(sample());self.assertTrue(p.complete);self.assertEqual(p.notice_done_local_2e,0)
  self.assertIn(('00466cc4',(1,),'genie_start'),p.calls)
  self.assertEqual(p.stores,((0x561fa8,1,1),(0x553cfc,4,1001),(0x553d00,4,0)))
  self.assertFalse(p.Genie_effect_verified)

 def test_expired_equality_and_both_local_flags_gate_stop(self):
  p=plan(sample(window_tick=60100));self.assertEqual(p.notice_done_local_2e,1)
  self.assertIn(('00466cc4',(0,),'genie_stop'),p.calls)
  self.assertEqual(p.stores,((0x553cfc,4,1002),(0x553d00,4,0),(0x561fa8,1,0)))
  p=plan(sample(window_tick=60100,other_stop_flag_2d=0));self.assertEqual(p.stores,())
  self.assertFalse(any(c[2]=='stop_state' for c in p.calls))

 def test_disabled_non3_or_nonpositive_stamp_sets_local_done(self):
  for fields in ({'enabled_byte':0},{'mode_dword':2},{'presence_stamp_low':0},{'presence_stamp_high':0x80000000}):
   p=plan(sample(other_stop_flag_2d=0,**fields));self.assertTrue(p.complete);self.assertEqual(p.notice_done_local_2e,1)
   self.assertEqual([c[2] for c in p.calls],['epilogue'])

 def test_start_low_al_nonzero_and_stop_low_al_exactly_one_differ(self):
  p=plan(sample(start_state_eax=0x100));self.assertTrue(any(c[2]=='genie_start' for c in p.calls))
  p=plan(sample(start_state_eax=2));self.assertFalse(any(c[2]=='genie_start' for c in p.calls))
  self.assertEqual(p.stores,((0x561fa8,1,1),))
  p=plan(sample(enabled_byte=0,stop_state_eax=2));self.assertFalse(any(c[2]=='genie_stop' for c in p.calls))
  self.assertEqual(p.stores,((0x561fa8,1,0),))

 def test_cooldown_equality_and_qword_clock_wrap_are_not_dword_wrap(self):
  p=plan(sample(start_cooldown_tick=999));self.assertFalse(any(c[2]=='genie_start' for c in p.calls))
  p=plan(sample(start_cooldown_tick=1000));self.assertTrue(any(c[2]=='genie_start' for c in p.calls))
  p=plan(sample(start_cooldown_tick=0x100,start_cooldown_stamp_low=0xffffff00))
  self.assertFalse(any(c[2]=='genie_start' for c in p.calls))
  p=plan(sample(enabled_byte=0,stop_cooldown_tick=999));self.assertEqual(p.stores,((0x561fa8,1,0),))

 def test_minutes_product_signed_overflow_and_fresh_stamp_reads(self):
  p=plan(sample(minutes_dword=0x8000,other_stop_flag_2d=0))
  self.assertTrue(p.complete) #0x8000*60000 is still positive.
  p=plan(sample(minutes_dword=40000,other_stop_flag_2d=0));self.assertEqual(p.notice_done_local_2e,1)
  p=plan(sample(presence_stamp_low=1,window_stamp_low=0x7fffffff,minutes_dword=0,no_attack_byte=0))
  self.assertEqual(p.notice_done_local_2e,0) #Negative signedQWORD elapsed remains inside zero threshold.

 def test_partial_start_keeps_no_attack_projection_and_consumed_clock_prefix(self):
  o=sample();r=dict(o.normal_returns);r['genie_start']=False;f=NoticeGenieFrame()
  p=f.advance(O(o.values,r));self.assertFalse(p.complete);self.assertEqual(p.needed,('normal','genie_start'))
  self.assertEqual(p.stores,((0x561fa8,1,1),))
  p=f.advance(O({'window_tick':999999,'start_post_tick':1001},{'genie_start':True,'start_post_tick':True,'epilogue':True}))
  self.assertTrue(p.complete);self.assertEqual(p.stores[1],(0x553cfc,4,1001));self.assertIs(f.advance(O()),p)

 def test_missing_other_general_flag_does_not_default_to_stop(self):
  o=sample(enabled_byte=0);v=dict(o.values);del v['other_stop_flag_2d']
  p=plan(O(v,o.normal_returns));self.assertFalse(p.complete);self.assertEqual(p.needed,('value','other_stop_flag_2d'))
  self.assertEqual(p.calls,());self.assertEqual(p.stores,())

if __name__=='__main__':unittest.main()
