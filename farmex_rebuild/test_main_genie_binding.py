import unittest
from dataclasses import replace
from main_worker import MainGenieObservation,MainWorkerFrame,MainWorkerObservation,plan_main_worker
from genie_worker import GenieWorkerFrame,GeniePrefixFrame,GenieWorkerObservation
from action_queue import QueueState,enqueue
from direct_chat_packets import QueueAttempt
from test_main_worker import sample as main
from test_genie_worker import sample as genie
from test_genie_recovery import sample as recovery
from test_notice_genie_window import sample as notice

def outer(**changes):
 return main(ms_mode_dword=0,general_mode_dword=0,genie_active_byte=1,priority_first_eax=1,**changes)

def inner(recovery_inputs=None):
 return replace(genie(initial_ba_byte=1,recovery_ba_byte=1,recovery_probe_eax=1,always_b8_byte=1,always_state_eax=2),recovery_observation=recovery_inputs)

class MainGenieBindingTests(unittest.TestCase):
 def test_incomplete_Genie_child_blocks_main_outer_normal(self):
  f=MainWorkerFrame();o=replace(outer(),children={'genie_worker':MainGenieObservation()})
  p=f.advance(o);self.assertFalse(p.complete);self.assertEqual(p.needed,('child','genie_worker'))
  self.assertNotIn('common_genie',[c[2] for c in p.calls])
  p=f.advance(replace(outer(),children={'genie_worker':MainGenieObservation(genie(always_b8_byte=1,always_state_eax=2))}))
  self.assertTrue(p.complete);self.assertTrue(p.children[0][1].complete)

 def test_Notice_tail_only_needed_after_prefix_reaches_it(self):
  f=MainWorkerFrame();p=f.advance(replace(outer(),children={'genie_worker':MainGenieObservation(genie())}))
  self.assertFalse(p.complete);self.assertTrue(p.children[0][1].prefix.complete)
  p=f.advance(replace(outer(),children={'genie_worker':MainGenieObservation(notice=notice())}))
  self.assertTrue(p.complete);self.assertIsNotNone(p.children[0][1].notice)
  self.assertFalse(p.children[0][1].whole_worker_verified)

 def test_prior_MS_item_record_then_Genie_recovery_share_own_queue_across_worker_invocations(self):
  from test_monster_stone_use import sample as use
  first=MainWorkerFrame();p=first.advance(replace(main(combat_enabled_byte=0),children={'ms_use':use()}))
  self.assertTrue(p.complete);self.assertEqual(len(first.queue.records),1)
  second=MainWorkerFrame(first.queue)
  p=second.advance(replace(outer(),children={'genie_worker':MainGenieObservation(inner(recovery()))}))
  self.assertTrue(p.complete);self.assertEqual(len(second.queue.records),2)
  self.assertEqual([r.record_id for r in second.queue.records],[1,2])
  self.assertEqual([r.payload[:2] for r in second.queue.records],[b'\x5f\x06',b'\x97\x01'])
  self.assertEqual(p.children[0][1].queue,second.queue)

 def test_committed_recovery_prefix_survives_inner_and_main_outer_return_gaps(self):
  prior=enqueue(QueueState(),b'prior',5,0,1,1).state;f=MainWorkerFrame(prior)
  r=recovery();r=replace(r,attempt=QueueAttempt(1,123,False))
  p=f.advance(replace(outer(),children={'genie_worker':MainGenieObservation(inner(r))}))
  self.assertFalse(p.complete);self.assertEqual(len(f.queue.records),2)
  o=outer();n=dict(o.normal_returns);n['genie_worker']=False
  p=f.advance(replace(o,normal_returns=n,children={'genie_worker':MainGenieObservation(inner(recovery()))}))
  self.assertFalse(p.complete);self.assertEqual(p.needed,('normal','genie_worker'))
  self.assertTrue(p.children[0][1].complete);self.assertEqual(len(f.queue.records),2)
  p=f.advance(outer());self.assertTrue(p.complete);self.assertEqual(len(f.queue.records),2)
  self.assertEqual(f.queue.records[1].created_tick,123)

 def test_zero_recovery_gate_keeps_prior_shared_queue(self):
  prior=enqueue(QueueState(),b'prior',5,0,1,1).state
  r=replace(recovery(),attempt=QueueAttempt(0,None,True));f=MainWorkerFrame(prior)
  p=f.advance(replace(outer(),children={'genie_worker':MainGenieObservation(inner(r))}))
  self.assertTrue(p.complete);self.assertEqual(f.queue,prior)

 def test_unreached_Genie_child_does_not_create_frame_or_change_queue(self):
  f=MainWorkerFrame();p=f.advance(replace(main(combat_enabled_byte=0),children={'genie_worker':MainGenieObservation()}))
  self.assertTrue(p.complete);self.assertNotIn('genie_worker',f.frames);self.assertEqual(f.queue.records,())

 def test_opaque_recovery_prefix_cannot_later_acquire_generated_queue_effects(self):
  f=GeniePrefixFrame();o=inner();n=dict(o.normal_returns);n['recovery_probe_post_tick']=False
  p=f.advance(replace(o,normal_returns=n));self.assertFalse(p.complete)
  with self.assertRaisesRegex(ValueError,'retroactively'):
   f.advance(inner(recovery()))
  self.assertEqual(f.queue.records,())

 def test_invalid_shared_queue_rejected_and_direct_plan_binding_generates_child(self):
  with self.assertRaises(ValueError):GenieWorkerFrame(queue=object())
  p=plan_main_worker(replace(outer(),children={'genie_worker':MainGenieObservation(genie(always_b8_byte=1,always_state_eax=2))}))
  self.assertTrue(p.complete);self.assertEqual(p.children[0][0],'genie_worker')
  self.assertFalse(p.live_compatibility_verified)

if __name__=='__main__':unittest.main()
