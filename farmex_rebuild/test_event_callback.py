import unittest
from dataclasses import replace
from action_queue import QueueState,QueueSample,enqueue,drain
from event_callback import *
from test_event_join import sample as worker
from test_event_packets import packet

def sample(**updates):
 v=dict(vip_active_byte=0,inn_active_byte=0,worker_active_byte=0,vip_probe_eax=0,inn_probe_eax=0,exclusive_byte=0,health_eax=1,worker_step_eax=12,worker_step_compare=12)
 n={k:True for k in ('vip_storage','inn_storage','vip_probe','inn_probe','health_probe','worker_step','event_worker')}
 v.update(updates);return EventCallbackObservation(True,v,n)

class EventCallbackTests(unittest.TestCase):
 def test_explicit_post_drain_entry_precedes_all_flag_reads(self):
  p=EventCallbackFrame().advance(EventCallbackObservation());self.assertEqual(p.needed,('entry','after004c79a0_return'));self.assertEqual(p.reads,())
 def test_VIP_priority_blocks_before_event_until_helper_returns(self):
  f=EventCallbackFrame();o=sample(vip_active_byte=1);n=dict(o.normal_returns);n['vip_storage']=False
  p=f.advance(replace(o,normal_returns=n));self.assertEqual(p.needed,('normal','vip_storage'));self.assertFalse(p.event_reached)
  self.assertNotIn('inn_active_byte',[r[2] for r in p.reads])
  p=f.advance(o);self.assertTrue(p.complete);self.assertTrue(p.event_reached);self.assertEqual(p.next_source_address,0x46f97d)
 def test_Inn_branch_goes_to_event_without_worker_or_bot_enabled_read(self):
  p=plan_event_callback(sample(inn_active_byte=2));self.assertTrue(p.complete);self.assertTrue(p.event_reached)
  self.assertNotIn('worker_active_byte',[r[2] for r in p.reads]);self.assertFalse(any(r[0]==0x561f60 for r in p.reads))
  self.assertFalse(p.whole_callback_verified);self.assertFalse(p.callback_return_verified)
 def test_worker_probe_nonzero_AL_resets_and_exits_before_event(self):
  p=plan_event_callback(replace(sample(worker_active_byte=1,vip_probe_eax=0x101),event_child=EventJoinObservation()))
  self.assertTrue(p.complete);self.assertFalse(p.event_reached);self.assertEqual(p.next_source_address,0x46fb09)
  self.assertEqual(p.stores,((0x568dc0,4,14),(0x568dbc,1,0)))
 def test_worker_phase_exact43_and_raw_AL_probes(self):
  for result,reset in ((43,True),(12,False),(0x100002b,False)):
   p=plan_event_callback(sample(worker_active_byte=1,vip_probe_eax=0x100,inn_probe_eax=0x100,worker_step_eax=result,worker_step_compare=result))
   self.assertTrue(p.complete);self.assertFalse(p.event_reached);self.assertEqual(p.stores[0],(0x568dc0,4,result))
   self.assertEqual(len(p.stores),3 if reset else 1)
 def test_worker_health_signed_nonpositive_skips_step(self):
  for health in (0,0xffffffff,0x80000000):
   p=plan_event_callback(sample(worker_active_byte=1,health_eax=health));self.assertEqual(p.status,'worker_reset_health')
   self.assertNotIn('worker_step',[c[2] for c in p.calls]);self.assertFalse(p.event_reached)
 def test_worker_comparison_is_a_fresh_global_read_after_return_store(self):
  p=plan_event_callback(sample(worker_active_byte=1,worker_step_eax=12,worker_step_compare=43))
  self.assertEqual(p.stores,((0x568dc0,4,12),(0x568dc0,4,14),(0x568dbc,1,0)))
  p=plan_event_callback(sample(worker_active_byte=1,worker_step_eax=43,worker_step_compare=12))
  self.assertEqual(p.stores,((0x568dc0,4,43),));self.assertIn((0x568dc0,4,'worker_step_compare'),p.reads)
 def test_generated_event_child_requires_inner_and_outer_returns(self):
  f=EventCallbackFrame();child=replace(worker(first_chaos_byte=1,priority_chaos_byte=1),packet_children={'chaos_join':packet()})
  o=replace(sample(),event_child=EventJoinObservation());p=f.advance(o);self.assertEqual(p.needed,('child','event_worker'))
  n=dict(o.normal_returns);n['event_worker']=False;p=f.advance(replace(o,normal_returns=n,event_child=child))
  self.assertEqual(p.needed,('normal','event_worker'));self.assertEqual(len(p.queue.records),1)
  p=f.advance(sample());self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1)
 def test_consumed_storage_flag_does_not_change_during_return_gap(self):
  f=EventCallbackFrame();o=sample(vip_active_byte=1);n=dict(o.normal_returns);n['vip_storage']=False
  self.assertFalse(f.advance(replace(o,normal_returns=n)).complete)
  p=f.advance(sample(vip_active_byte=0,inn_active_byte=1));self.assertTrue(p.complete)
  self.assertEqual([c[2] for c in p.calls],['vip_storage','event_worker'])
 def test_opaque_event_cannot_be_retroactively_replaced(self):
  f=EventCallbackFrame();self.assertTrue(f.advance(sample()).complete)
  with self.assertRaisesRegex(ValueError,'retroactively'):f.advance(replace(sample(),event_child=EventJoinObservation()))
 def test_event_records_are_created_after_explicit_drain_and_not_drained_again(self):
  before=enqueue(QueueState(),b'old',3,0,1,1).state;after=drain(before,{1:QueueSample(100,0)}).state
  self.assertEqual(after.records,())
  child=replace(worker(first_chaos_byte=1,priority_chaos_byte=1),packet_children={'chaos_join':packet(tick=101)})
  p=EventCallbackFrame(queue=after).advance(replace(sample(),event_child=child))
  self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1);self.assertEqual(p.queue.records[0].record_id,2)
  self.assertFalse(any(c[0]=='004c79a0' for c in p.calls))

if __name__=='__main__':unittest.main()
