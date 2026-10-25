import unittest
from dataclasses import replace
from callback_prequeue import *

def sample(**updates):
 v=dict(header1_slot=0x1000,header1_root_eax=0x2000,header1_offset=0x30,header1_field_eax=1,
 header2_slot=0x4000,header2_root_eax=0x5000,header2_offset=0x60,header2_field_eax=0,
 ready_eax=1,profile_enabled_byte=0,connection_eax=1,pending_byte=0,pending_tick_eax=100,
 recovery_byte=0,recovery_tick_eax=5001,recovery_low=0,recovery_high=0,recovery_toggle_byte=1,recovery_toggle_push_ecx=0x12340001,
 flag_562202_byte=0,recovery_mode_first=0,recovery_mode_second=2,restore_bot_byte=1,recovery_setup_done_byte=0,
 exclusive_byte=0,exclusive_restore_bot_byte=1,combat_active_byte=1,return_coordinates_byte=1,no_coordinates_restore_bot_byte=1,
 distance_eax=49,compare1_ax=0,compare2_ax=0,actor_slot=0x1000,actor_root_eax=0x2000,actor_state_offset=0x40,
 actor_state_eax=0,arrival_restore_bot_byte=1,notice_string_handle=0xa000,guard_profile_enabled_byte=0,fixed_guard_eax=0)
 for pre,y,x in (('distance_input',1,2),('movement_input',3,4)):
  v.update({pre+'.y_integer':10,pre+'.x_integer':20,pre+'.y_bits':y,pre+'.x_bits':x})
 labels=('entry_setup','header1_root','header1_field','header2_root','header2_field','ready','prelude1','prelude2',
 'profile_refresh','connection','disconnected_worker','pending_tick','pending_ui_setter','direct_SEH_restore',
 'recovery_tick','recovery_toggle','recovery_prepare','recovery_ui_setter','mode2_stop','recovery_setup',
 'exclusive_start','no_coordinates_stop','distance','distance_ftol','compare1','compare2','movement','actor_root',
 'actor_state','recovery_arrival','arrival_stop','distance_start','notice_construct','notice_dispatch','notice_cleanup',
 'fixed_guard','work_queue','queue_consumer')
 n={k:True for k in labels}
 for pre in ('distance_input','movement_input'):
  n.update({pre+'.'+axis+'_fstp':True for axis in ('x','y')})
 v.update(updates);return CallbackPreQueueObservation(v,n)

class CallbackPreQueueTests(unittest.TestCase):
 def test_all_header_reads_precede_readiness_and_ready_uses_low_AL(self):
  p=plan_callback_prequeue(sample(ready_eax=0x100));self.assertEqual(p.status,'not_ready');self.assertEqual(p.next_source_address,0x46fb09)
  self.assertEqual([c[2] for c in p.calls][-1],'ready');self.assertEqual(len(p.calls),6)
  o=sample(ready_eax=0);n=dict(o.normal_returns);n['header1_field']=False
  p=plan_callback_prequeue(replace(o,normal_returns=n));self.assertEqual(p.needed,('normal','header1_field'))
 def test_connection_requires_full_exact_one_and_runs_disconnected_helper(self):
  for connection in (0,2,0x101,0xffffffff):
   p=plan_callback_prequeue(sample(connection_eax=connection));self.assertEqual(p.status,'connection_not_one')
   self.assertEqual(p.calls[-1],('00459970',(0x562194,),'disconnected_worker'));self.assertFalse(p.queue_consumer_reached)
 def test_pending_local_fields_control_clear_and_direct_exit_skips_cleanup(self):
  p=plan_callback_prequeue(sample(pending_byte=1,header1_field_eax=0,header2_field_eax=0))
  self.assertEqual(p.next_source_address,0x46fb2f)
  self.assertEqual(p.stores,((0x562208,1,0),(0x562214,4,100),(0x562218,4,0),(0x56221d,1,1)))
  p=plan_callback_prequeue(sample(pending_byte=1));self.assertEqual(p.stores,());self.assertFalse(p.queue_consumer_reached)
 def test_pending_setter_gap_preserves_prior_stores_and_captured_header(self):
  f=CallbackPreQueueFrame();o=sample(pending_byte=1,header1_field_eax=0);n=dict(o.normal_returns);n['pending_ui_setter']=False
  p=f.advance(replace(o,normal_returns=n));self.assertEqual(len(p.stores),3)
  p=f.advance(sample(pending_byte=0,header1_field_eax=99,pending_tick_eax=999));self.assertTrue(p.complete)
  self.assertEqual(p.stores[1],(0x562214,4,100));self.assertEqual(p.stores[-1],(0x56221d,1,1))
 def test_recovery_signed_QWORD_wait_is_strict5000_without_DWORD_wrap(self):
  for now,lo in ((5000,0),(0x100,0xffffff00)):
   p=plan_callback_prequeue(sample(recovery_byte=1,recovery_tick_eax=now,recovery_low=lo));self.assertEqual(p.status,'recovery_wait')
  p=plan_callback_prequeue(sample(recovery_byte=1,flag_562202_byte=1));self.assertEqual(p.status,'recovery_UI_exit')
  self.assertIn(('00464678',(0x12340001,),'recovery_toggle'),p.calls)
  with self.assertRaisesRegex(ValueError,'MOV CL'):plan_callback_prequeue(sample(recovery_byte=1,recovery_toggle_push_ecx=0x12340000))
 def test_recovery_mode_second_read_is_fresh(self):
  p=plan_callback_prequeue(sample(recovery_byte=1,recovery_mode_first=1,recovery_mode_second=2))
  self.assertEqual(p.stores,((0x56221d,1,0),));self.assertEqual(p.calls[-1][0],'0040ae0c')
  p=plan_callback_prequeue(sample(recovery_byte=1,recovery_mode_first=1,recovery_mode_second=0))
  self.assertEqual(p.stores,());self.assertEqual(p.status,'recovery_other_mode')
 def test_exclusive_combat_disabled_and_no_coordinate_branches_differ(self):
  p=plan_callback_prequeue(sample(recovery_byte=1,exclusive_byte=1));self.assertEqual(p.status,'recovery_exclusive')
  self.assertEqual(p.calls[-1],('0040ac18',(1,0x561f34),'exclusive_start'))
  p=plan_callback_prequeue(sample(recovery_byte=1,combat_active_byte=0));self.assertEqual(p.status,'recovery_combat_disabled')
  self.assertNotIn((0x56221d,1,0),p.stores)
  p=plan_callback_prequeue(sample(recovery_byte=1,return_coordinates_byte=0));self.assertEqual(p.status,'recovery_no_coordinates')
  self.assertEqual(p.calls[-1][0],'0040ae0c')
 def test_movement_uses_fresh_coordinate_push_bits_and_signed50_boundary(self):
  p=plan_callback_prequeue(sample(recovery_byte=1));self.assertEqual(p.status,'recovery_move')
  self.assertIn(('00460548',(1,2),'distance'),p.calls);self.assertEqual(p.calls[-1],('004646b4',(3,4),'movement'))
  p=plan_callback_prequeue(sample(recovery_byte=1,distance_eax=50,compare2_ax=0x100));self.assertEqual(p.status,'recovery_arrival')
  self.assertFalse(p.FPU_semantics_verified)
 def test_second_FPU_TEST_parity_and_actor_low_AL_are_preserved(self):
  p=plan_callback_prequeue(sample(recovery_byte=1,distance_eax=50,compare2_ax=0x100,actor_state_eax=0x101))
  self.assertEqual(p.status,'recovery_actor_busy');self.assertNotIn((0x56221d,1,0),p.stores)
  p=plan_callback_prequeue(sample(recovery_byte=1,distance_eax=50,compare2_ax=0x500))
  self.assertEqual(p.status,'recovery_notice');self.assertEqual(p.calls[-1][2],'notice_cleanup');self.assertEqual(p.stores[-1],(0x56221d,1,0))
 def test_fixed_guard_and_consumer_returns_are_distinct(self):
  p=plan_callback_prequeue(sample(header1_field_eax=0,guard_profile_enabled_byte=1,fixed_guard_eax=0x101));self.assertEqual(p.status,'fixed_guard_exit')
  f=CallbackPreQueueFrame();o=sample();n=dict(o.normal_returns);n['queue_consumer']=False
  p=f.advance(replace(o,normal_returns=n));self.assertFalse(p.complete);self.assertTrue(p.queue_consumer_reached)
  p=f.advance(CallbackPreQueueObservation(normal_returns={'queue_consumer':True}));self.assertTrue(p.complete)
  self.assertEqual(p.next_source_address,0x46f8be);self.assertFalse(p.queue_effect_verified);self.assertFalse(p.callback_return_verified)
 def test_entry_event_chain_requires_fresh_queue_then_derives_post_entry(self):
  from test_event_callback import sample as post
  f=CallbackEntryEventFrame();p=f.advance(CallbackEntryEventObservation(pre=sample(),post=post()))
  self.assertEqual(p.needed,('queue_state','post_drain'));self.assertIsNone(f.post)
  p=f.advance(CallbackEntryEventObservation(post=replace(post(),entry_reached=False),post_drain_queue=QueueState()))
  self.assertTrue(p.complete);self.assertTrue(p.post.event_reached);self.assertEqual(p.next_source_address,0x46f97d)
 def test_entry_early_exit_needs_neither_queue_nor_event_observations(self):
  p=CallbackEntryEventFrame().advance(CallbackEntryEventObservation(pre=sample(ready_eax=0)))
  self.assertTrue(p.complete);self.assertIsNone(p.post);self.assertIsNone(p.queue);self.assertEqual(p.next_source_address,0x46fb09)
 def test_queue_return_gap_cannot_enter_event_even_with_post_queue_supplied(self):
  o=sample();n=dict(o.normal_returns);n['queue_consumer']=False;f=CallbackEntryEventFrame()
  p=f.advance(CallbackEntryEventObservation(pre=replace(o,normal_returns=n),post_drain_queue=QueueState()))
  self.assertFalse(p.complete);self.assertIsNone(f.post);self.assertEqual(p.needed[0],'pre')

if __name__=='__main__':unittest.main()
