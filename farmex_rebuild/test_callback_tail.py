import unittest
from dataclasses import replace
from callback_tail import *
from source_callback import *
from callback_prequeue import CallbackEntryEventObservation
from test_callback_prequeue import sample as pre
from test_event_callback import sample as post
from test_main_worker import sample as main_sample

def sample(**updates):
 v=dict(bot_enabled_byte=0,attack_lock_byte=0,unlock_tick_eax=100,lock_started=0,lock_duration=100,
 interlude_tick_eax=100,initial_session_low=100,initial_session_high=0,initial_interval=10,
 fresh_session_low=0,fresh_session_high=0,session_interval=10,fresh_attempt_low=0,fresh_attempt_high=0,attempt_interval=10,
 predicate_eax=0,predicate_flag_byte=0,replacement_target=0xabc,initial_random_eax=20,final_random_eax=30,
 mode_zero=1,mode_two=1,mode_three=1,mode_four=1,mode_five=1,
 cleanup_root_slot=0x1000,cleanup_root=0xfffffff0,cleanup_offset=0x20,cleanup_ecx=0x2000,cleanup_target=0x3000)
 n={k:True for k in ('control','unlock_tick','interlude_tick','initial_random','predicate','replacement','final_random',
 'main_worker','mode2','mode3','mode4','mode5','cleanup_callback','SEH_restore','epilogue')}
 v.update(updates);return CallbackTailObservation(v,n)

class CallbackTailTests(unittest.TestCase):
 def test_cleanup_and_direct_epilogue_entries_have_distinct_requirements(self):
  p=plan_callback_tail(sample(),entry=0x46fb09);self.assertTrue(p.complete)
  self.assertEqual(p.calls,(('opaque_indirect_callback',(0x3000,0x2000,()),'cleanup_callback'),('captured_SEH_restore',(),'SEH_restore'),('captured_callback_epilogue_return',(),'epilogue')))
  self.assertIn((0x10,4,'cleanup_ecx'),p.reads)
  p=plan_callback_tail(CallbackTailObservation(normal_returns={'epilogue':True}),entry=0x46fb2f)
  self.assertTrue(p.complete);self.assertEqual(p.reads,());self.assertEqual(len(p.calls),1)
 def test_control_return_precedes_lock_and_wrapped_inclusive_unlock(self):
  f=CallbackTailFrame();o=sample(bot_enabled_byte=1,attack_lock_byte=1,unlock_tick_eax=5,lock_started=0xfffffff0,lock_duration=21)
  n=dict(o.normal_returns);n['control']=False;p=f.advance(replace(o,normal_returns=n));self.assertEqual(p.needed,('normal','control'))
  self.assertNotIn('attack_lock_byte',[r[2] for r in p.reads]);p=f.advance(o);self.assertIn((0x561f7e,1,0),p.stores)
 def test_session_zero_skips_interlude_inputs_and_session_threshold_is_strict(self):
  p=plan_callback_tail(sample());self.assertTrue(p.complete);self.assertEqual(p.stores,())
  p=plan_callback_tail(sample(initial_session_low=0,fresh_session_low=90,session_interval=10))
  self.assertNotIn('predicate',[c[2] for c in p.calls]);self.assertEqual(p.stores,())
 def test_attempt_threshold_inclusive_and_signed_interval_preserved(self):
  p=plan_callback_tail(sample(initial_session_low=0,fresh_attempt_low=90,attempt_interval=10));self.assertTrue(p.complete)
  self.assertIn((0x5620d4,4,100),p.stores);self.assertIn(('0046b8fc',(0x46eca8,0xabc,0x554228),'replacement'),p.calls)
  p=plan_callback_tail(sample(initial_session_low=0,fresh_attempt_low=91,attempt_interval=10));self.assertEqual(p.stores,())
  p=plan_callback_tail(sample(initial_session_low=0,session_interval=0xffffffff,attempt_interval=0xffffffff));self.assertTrue(p.complete)
  self.assertIn((0x5620cc,4,30),p.stores)
 def test_initial_random_store_does_not_replace_later_fresh_interval_read(self):
  p=plan_callback_tail(sample(initial_session_low=0,initial_interval=0,initial_random_eax=1,session_interval=1000))
  self.assertEqual(p.stores,((0x5620cc,4,1),));self.assertNotIn('predicate',[c[2] for c in p.calls])
 def test_predicate_low_AL_and_flag_short_circuit(self):
  p=plan_callback_tail(sample(initial_session_low=0,predicate_eax=0x100));self.assertIn('replacement',[c[2] for c in p.calls])
  self.assertNotIn('predicate_flag_byte',[r[2] for r in p.reads])
  p=plan_callback_tail(sample(initial_session_low=0,predicate_eax=0x101,predicate_flag_byte=1));self.assertNotIn('replacement',[c[2] for c in p.calls])
 def test_random_return_gap_preserves_timestamp_and_original_tick(self):
  f=CallbackTailFrame();o=sample(initial_session_low=0);n=dict(o.normal_returns);n['final_random']=False
  p=f.advance(replace(o,normal_returns=n));self.assertIn((0x5620d4,4,100),p.stores)
  p=f.advance(sample(interlude_tick_eax=999));self.assertTrue(p.complete);self.assertIn((0x5620d4,4,100),p.stores)
 def test_dispatch_reads_same_mode_fresh_for_each_comparison(self):
  p=plan_callback_tail(sample(mode_zero=1,mode_two=7,mode_three=3));self.assertIn(('004f82e8',(0x569a30,),'mode3'),p.calls)
  self.assertNotIn('mode_four',[r[2] for r in p.reads]);self.assertFalse(p.whole_callback_verified)
 def test_generated_main_worker_blocks_outer_return_and_cleanup(self):
  f=CallbackTailFrame();o=replace(sample(mode_zero=0),main_child=MainWorkerObservation())
  p=f.advance(o);self.assertEqual(p.needed,('child','main_worker'));self.assertNotIn('cleanup_callback',[c[2] for c in p.calls])
  n=dict(o.normal_returns);n['main_worker']=False;p=f.advance(replace(o,normal_returns=n,main_child=main_sample()))
  self.assertTrue(p.main_plan.complete);self.assertEqual(p.needed,('normal','main_worker'))
  p=f.advance(sample());self.assertTrue(p.complete);self.assertTrue(p.normal_return_receipt)
 def test_native_return_receipt_is_not_assumed_from_cleanup_callback(self):
  f=CallbackTailFrame(entry=0x46fb09);o=sample();n=dict(o.normal_returns);n['epilogue']=False
  p=f.advance(replace(o,normal_returns=n));self.assertFalse(p.complete);self.assertFalse(p.normal_return_receipt)
  p=f.advance(CallbackTailObservation(normal_returns={'epilogue':True}));self.assertTrue(p.complete);self.assertFalse(p.native_execution_verified)
 def test_whole_control_composition_requires_fresh_queue_on_early_exit(self):
  f=SourceCallbackFrame();o=SourceCallbackObservation(entry_event=CallbackEntryEventObservation(pre=pre(ready_eax=0)),tail=sample())
  p=f.advance(o);self.assertEqual(p.needed,('queue_state','early_tail'));self.assertIsNone(f.tail)
  p=f.advance(replace(o,early_tail_queue=QueueState()));self.assertTrue(p.complete);self.assertTrue(p.normal_return_receipt)
  self.assertEqual(p.tail.entry,0x46fb09);self.assertFalse(p.whole_callback_verified)
 def test_composition_direct_epilogue_does_not_add_cleanup_callback(self):
  o=SourceCallbackObservation(entry_event=CallbackEntryEventObservation(pre=pre(pending_byte=1)),
   tail=CallbackTailObservation(normal_returns={'epilogue':True}),early_tail_queue=QueueState())
  p=SourceCallbackFrame().advance(o);self.assertTrue(p.complete);self.assertEqual(p.tail.entry,0x46fb2f);self.assertEqual(len(p.tail.calls),1)
 def test_composition_normal_event_path_reaches_tail_and_keeps_queue(self):
  chain=CallbackEntryEventObservation(pre=pre(),post=post(),post_drain_queue=QueueState())
  p=SourceCallbackFrame().advance(SourceCallbackObservation(chain,sample()))
  self.assertTrue(p.complete);self.assertTrue(p.entry_event.post.event_reached);self.assertEqual(p.tail.entry,0x46f97d)
  self.assertIsNotNone(p.queue);self.assertFalse(p.live_compatibility_verified)

if __name__=='__main__':unittest.main()
