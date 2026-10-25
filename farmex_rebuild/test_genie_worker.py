import unittest
from genie_worker import GenieWorkerObservation as O,GenieWorkerFrame,GeniePrefixFrame,plan_genie_prefix as plan
from notice_genie_window import NoticeGenieObservation as N

def sample(**updates):
 v=dict(initial_bb_byte=0,initial_bc_byte=0,initial_ba_byte=0,initial_remaining_eax=0,recovery_ba_byte=0,
  recovery_probe_tick=5000,recovery_probe_low=0,recovery_probe_high=0,recovery_probe_eax=0x100,recovery_probe_post_tick=5001,
  cached_probe_byte=0,retry_bc_byte=0,retry_bb_byte=0,empty_bc_byte=0,empty_bb_byte=0,
  always_b8_byte=0,always_state_eax=0,always_cooldown_tick=1000,always_cooldown_low=0,always_cooldown_high=0,
  always_remaining_eax=1,always_post_tick=1001,general_enabled_byte=0,general_mode_dword=2,general_genie_byte=1,
  general_active_byte=0,general_no_attack_byte=1,general_cooldown_tick=1000,general_cooldown_low=0,general_cooldown_high=0,
  general_remaining_eax=1,general_post_tick=1002,general_activity_tick=1003,resume_delay_byte=1,
  resume_delay_tick=1000,resume_delay_low=0,resume_delay_high=0,resume_seconds_dword=1)
 v.update(updates)
 labels=('frame_setup','initial_remaining','recovery_probe_tick','recovery_probe','recovery_probe_post_tick',
  'retry_alarm_span','retry_bot_stop','retry_town','empty_alarm_span','empty_bot_stop','empty_town',
  'always_state','always_cooldown_tick','always_remaining','always_start','always_post_tick',
  'general_cooldown_tick','general_remaining','general_start','general_post_tick','general_activity_tick','resume_delay_tick','epilogue')
 return O(v,{k:True for k in labels})
def called(p,label):return any(c[2]==label for c in p.calls)

class GenieWorkerTests(unittest.TestCase):
 def test_all_disabled_skips_initial_remaining_and_generates_notice_stop_flag(self):
  p=plan(sample());self.assertTrue(p.complete);self.assertEqual(p.status,'notice_entry_reached')
  self.assertEqual(p.general_stop_flag_2d,1);self.assertFalse(called(p,'initial_remaining'))

 def test_initial_remaining_consumes_only_lowAL_and_flags_are_fresh(self):
  p=plan(sample(initial_bb_byte=1,initial_remaining_eax=0x101))
  self.assertTrue(p.complete);self.assertFalse(called(p,'recovery_probe'));self.assertFalse(called(p,'empty_alarm_span'))
  p=plan(sample(initial_bb_byte=1,initial_remaining_eax=0x100,recovery_ba_byte=0,empty_bc_byte=1,empty_bb_byte=1))
  self.assertEqual(p.status,'early_stop_town');self.assertTrue(called(p,'empty_alarm_span'))
  self.assertEqual([c[2] for c in p.calls][-3:],['empty_bot_stop','empty_town','epilogue'])

 def test_five_second_probe_equality_skips_same_pass_alarm_even_returnAL_zero(self):
  p=plan(sample(initial_ba_byte=1,recovery_ba_byte=1,retry_bc_byte=1,retry_bb_byte=1))
  self.assertEqual(p.status,'notice_entry_reached');self.assertTrue(called(p,'recovery_probe'))
  self.assertFalse(called(p,'retry_alarm_span'))
  self.assertEqual(p.stores[:3],((0x553cf0,1,0),(0x553cf4,4,5001),(0x553cf8,4,0)))
  p=plan(sample(initial_ba_byte=1,recovery_ba_byte=1,recovery_probe_tick=4999,retry_bc_byte=1,retry_bb_byte=1))
  self.assertEqual(p.status,'early_stop_town');self.assertTrue(called(p,'retry_alarm_span'))

 def test_cached_nonzero_recovery_result_does_not_enter_alarm_or_stop(self):
  p=plan(sample(initial_ba_byte=1,recovery_ba_byte=1,recovery_probe_tick=4999,cached_probe_byte=255,retry_bb_byte=1))
  self.assertEqual(p.status,'notice_entry_reached');self.assertFalse(called(p,'retry_bot_stop'))

 def test_always_on_all_paths_return_before_notice(self):
  for changes in ({'always_state_eax':2},{'always_cooldown_tick':999},{'always_remaining_eax':0x100},{}):
   o=sample(always_b8_byte=1,**changes);f=GenieWorkerFrame();p=f.advance(o,notice=object())
   self.assertTrue(p.complete);self.assertEqual(p.prefix.status,'early_always_on');self.assertIsNone(p.notice)
   self.assertFalse(p.whole_worker_verified)
  p=plan(sample(always_b8_byte=1));self.assertTrue(called(p,'always_start'))
  self.assertEqual(p.stores,((0x553cfc,4,1001),(0x553d00,4,0)))

 def test_general_start_separate_activity_tick_and_early_return(self):
  p=plan(sample(general_enabled_byte=1,general_active_byte=1))
  self.assertEqual(p.status,'early_general_start');self.assertEqual(p.stores,
   ((0x561fa8,1,1),(0x553cfc,4,1002),(0x553d00,4,0),(0x561fa4,4,1003)))

 def test_general_cooldown_wait_continues_notice_with_flag_zero(self):
  p=plan(sample(general_enabled_byte=1,general_active_byte=1,general_cooldown_tick=999))
  self.assertEqual(p.status,'notice_entry_reached');self.assertEqual(p.general_stop_flag_2d,0)
  self.assertEqual(p.stores,((0x561fa8,1,1),));self.assertFalse(called(p,'general_remaining'))

 def test_resume_delay_is_strict_while_cooldown_is_inclusive(self):
  for tick,flag in ((999,0),(1000,0),(1001,1)):
   p=plan(sample(general_enabled_byte=1,resume_delay_tick=tick));self.assertEqual(p.general_stop_flag_2d,flag)
  p=plan(sample(general_enabled_byte=1,resume_delay_byte=0));self.assertEqual(p.general_stop_flag_2d,1)
  self.assertFalse(called(p,'resume_delay_tick'))

 def test_signed_qword_wrap_and_low32_seconds_product(self):
  p=plan(sample(general_enabled_byte=1,general_active_byte=1,general_cooldown_tick=0x100,general_cooldown_low=0xffffff00))
  self.assertFalse(called(p,'general_start'));self.assertEqual(p.general_stop_flag_2d,0)
  p=plan(sample(general_enabled_byte=1,resume_seconds_dword=3000000));self.assertEqual(p.general_stop_flag_2d,1)

 def test_prefix_resume_retains_no_attack_projection_and_separate_activity_gap(self):
  o=sample(general_enabled_byte=1,general_active_byte=1);r=dict(o.normal_returns);r['general_start']=False
  f=GeniePrefixFrame();p=f.advance(O(o.values,r));self.assertFalse(p.complete);self.assertEqual(p.stores,((0x561fa8,1,1),))
  p=f.advance(O({'general_post_tick':123,'general_activity_tick':456},{'general_start':True,'general_post_tick':True,'general_activity_tick':True,'epilogue':True}))
  self.assertTrue(p.complete);self.assertEqual(p.stores[-3:],((0x553cfc,4,123),(0x553d00,4,0),(0x561fa4,4,456)))

 def test_worker_binds_derived_general_flag_and_resumes_notice_without_prefix_inputs(self):
  f=GenieWorkerFrame();p=f.advance(sample());self.assertFalse(p.complete);self.assertEqual(p.notice.needed,('value','enabled_byte'))
  with self.assertRaises(ValueError):f.advance(notice=N({'other_stop_flag_2d':0}))
  p=f.advance(notice=N({'enabled_byte':0,'stop_state_eax':2},{'stop_state':True,'epilogue':True}))
  self.assertTrue(p.complete);self.assertEqual(p.stores,((0x561fa8,1,0),));self.assertIs(f.advance(),p)

 def test_short_circuit_and_normal_gaps_do_not_invent_source_reads(self):
  p=plan(O({'initial_bb_byte':1,'initial_remaining_eax':1,'always_b8_byte':0,'general_enabled_byte':0},
   {'frame_setup':True,'initial_remaining':True}))
  self.assertTrue(p.complete);self.assertEqual(p.general_stop_flag_2d,1)
  p=plan(O());self.assertEqual(p.needed,('normal','frame_setup'))
  with self.assertRaises(ValueError):O({'always_b8_byte':True})

if __name__=='__main__':unittest.main()
