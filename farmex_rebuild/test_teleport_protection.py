import unittest
from teleport_protection import *

class TeleportProtectionTests(unittest.TestCase):
 def observation(self,**extra):
  values=dict(first_area_eax=10,tick_eax=10000,start_low=0,start_high=0,
   second_area_eax=10,tp_enabled_byte=1,action_first=0,action_second=0)
  values.update(extra)
  normals={k:True for k in ('first_area','area_change_stop','tick','second_area','notice_block','tp_stop','tp_disconnect','third_area','jail_all','jail_list')}
  return TPObservation(True,values,normals)
 def event(self,o,packet=b'\x27\x01\x0a'):return TPFrame('event',packet=packet).advance(o)
 def test_settings_stop_radio_only_and_raw_al(self):
  for enabled,stop,dc,action in ((True,True,True,1),(True,False,False,2),(False,False,True,2)):
   result=compile_tp_settings(dict(zip(TP_INPUTS,(enabled,stop,dc))))
   self.assertEqual(dict(result),{0xb0:int(enabled),0xb4:action})
  f=TPFrame('settings');p=f.advance(TPObservation(True,{'enabled_eax':0x102,'stop_eax':0x100},{'enabled_getter':True,'stop_getter':True}))
  self.assertEqual(p.stores,((0x5691a8,1,2),(0x5691ac,4,2)));self.assertEqual(p.next_address,0x46c134)
 def test_entry_and_unrelated_opcode_do_not_touch_flags(self):
  p=TPFrame('event',packet=b'').advance(TPObservation())
  self.assertEqual(p.needed,('entry','004d88e4'));self.assertEqual(p.reads,())
  p=TPFrame('event',packet=b'\x26').advance(TPObservation(True))
  self.assertTrue(p.complete);self.assertEqual(p.calls,());self.assertEqual(p.next_address,0x4d8a98)
 def test_source_time_boundary_inclusive_and_notice_before_enable_gate(self):
  below=self.event(self.observation(tick_eax=9999))
  self.assertTrue(below.complete);self.assertEqual(below.stores,())
  self.assertFalse(any(c[2]=='second_area' for c in below.calls))
  at=self.event(self.observation(tp_enabled_byte=0))
  self.assertTrue(at.complete);self.assertEqual(at.stores,((0x56209c,1,1),))
  self.assertFalse(any(r[0]==0x5691ac for r in at.reads))
 def test_signed_qword_time_is_not_wrapped_dword_elapsed(self):
  for values in ({'tick_eax':1,'start_low':0xfffffff0},{'tick_eax':20000,'start_high':1}):
   p=self.event(self.observation(**values))
   self.assertTrue(p.complete);self.assertFalse(any(c[2]=='notice_block' for c in p.calls))
 def test_area_zero_skips_first_getter_but_second_read_still_reached(self):
  o=TPObservation(True,{'tick_eax':10000,'start_low':0,'start_high':0,'second_area_eax':0,'tp_enabled_byte':0},
                   {'tick':True,'second_area':True,'notice_block':True})
  p=self.event(o,b'\x27\x01\x00')
  self.assertTrue(p.complete);self.assertEqual(p.calls[0][2],'tick');self.assertEqual(p.stores,((0x56209c,1,1),))
 def test_early_stop_and_later_tp_stop_are_distinct_fresh_area_calls(self):
  p=self.event(self.observation(first_area_eax=11,area_change_stop_byte=1,action_first=1,action_second=1))
  labels=[c[2] for c in p.calls]
  self.assertTrue(p.complete);self.assertEqual([x for x in labels if x.endswith('stop')],['area_change_stop','tp_stop'])
  self.assertLess(labels.index('area_change_stop'),labels.index('tick'))
 def test_action_is_reloaded_after_stop_so_both_paths_can_be_reached(self):
  f=TPFrame('event',packet=b'\x27\x01\x0a')
  o=self.observation(action_first=1,action_second=1)
  normals=dict(o.normal_returns);normals['tp_stop']=False
  p=f.advance(TPObservation(True,o.values,normals));self.assertEqual(p.needed,('normal','tp_stop'))
  self.assertNotIn('action_second',f.observation.values)
  p=f.advance(TPObservation(False,{'action_first':0,'action_second':2},{'tp_stop':True,'tp_disconnect':True}))
  self.assertTrue(p.complete);self.assertEqual([c[2] for c in p.calls][-2:],['tp_stop','tp_disconnect'])
  self.assertEqual(p.calls[-1][:2],('004c7e0c',(0x561ef8,)))
 def test_third_area_uses_full_eax_and_sets_two_flags(self):
  p=self.event(self.observation(tick_eax=1,first_area_eax=0x5c,third_area_eax=0x15c),b'\x27\x03\x5c')
  self.assertFalse(p.complete);self.assertEqual(p.needed,('value','jail_enabled_byte'))
  self.assertEqual(p.stores,((0x561f6e,1,1),(0x561f70,1,1)))
 def test_jail_branch_independent_of_ten_second_tp_gate(self):
  for flag,label in ((0,'jail_all'),(255,'jail_list')):
   p=self.event(self.observation(tick_eax=1,first_area_eax=0x5c,third_area_eax=0x5c,jail_enabled_byte=1,jail_list_only_byte=flag),b'\x27\x03\x5c')
   self.assertTrue(p.complete);self.assertEqual(p.calls[-1],('0046d66c' if flag==0 else '0046dc5c',(0x5690f8,),label))
   self.assertFalse(any(c[2]=='second_area' for c in p.calls))
 def test_subtype_two_projects_reset_and_terminal_frame_is_stable(self):
  f=TPFrame('event',packet=b'\x27\x02\x0a');p=f.advance(self.observation(tick_eax=1))
  self.assertEqual(p.stores,((0x561f70,1,0),));self.assertEqual(p.planned_eax,1)
  self.assertIs(f.advance(TPObservation()),p)
 def test_notice_gap_retains_prefix_and_blocks_flag_store(self):
  f=TPFrame('event',packet=b'\x27\x01\x0a');o=self.observation(tp_enabled_byte=0)
  n=dict(o.normal_returns);n['notice_block']=False
  p=f.advance(TPObservation(True,o.values,n));self.assertEqual(p.needed,('normal','notice_block'));self.assertEqual(p.stores,())
  p=f.advance(TPObservation(False,{'tick_eax':0,'tp_enabled_byte':0},{'notice_block':True}))
  self.assertTrue(p.complete);self.assertEqual(p.stores,((0x56209c,1,1),))
 def test_short_packet_and_typed_input_boundaries(self):
  p=TPFrame('event',packet=b'\x27').advance(TPObservation(True))
  self.assertFalse(p.complete);self.assertEqual(p.needed[0],'unsupported')
  with self.assertRaises(ValueError):TPObservation(values={'tp_enabled_byte':256})
  with self.assertRaises(ValueError):TPObservation(values={'tick_eax':True})
  with self.assertRaises(ValueError):compile_tp_settings(dict(zip(TP_INPUTS,(True,False,1))))
  p=self.event(self.observation());self.assertFalse(p.native_execution_verified or p.live_compatibility_verified or p.whole_handler_verified)

if __name__=='__main__':unittest.main()
