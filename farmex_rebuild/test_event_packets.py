import unittest
from dataclasses import replace
from action_queue import QueueState,enqueue
from direct_chat_packets import QueueAttempt
from event_packets import *
from event_join import EventJoinFrame,plan_event_join
from test_event_join import sample

def packet(nation=2,gate=1,tick=123):
 return EventPacketObservation({'nation_eax':nation},{k:True for k in ('frame_setup','nation','copy','return')},QueueAttempt(gate,tick,True))

class EventPacketTests(unittest.TestCase):
 def test_first_templates_and_direct_template_lengths_are_exact(self):
  for kind,expected in (('chaos','5f081800'),('royale','b70701')):
   p=EventPacketFrame(kind).advance(packet());self.assertTrue(p.complete)
   self.assertEqual(p.payload.hex(),expected);self.assertEqual(p.queue.records[0].payload,p.payload)
  self.assertEqual([len(p) for p in DIRECT_TEMPLATES.values()],[17,18,18,19])
 def test_BDW_exact_nation2_else_branch(self):
  for nation,expected in ((2,'5f080200'),(1,'5f080100'),(0,'5f080100'),(0xffffffff,'5f080100')):
   p=EventPacketFrame('bdw').advance(packet(nation));self.assertTrue(p.complete);self.assertEqual(p.payload.hex(),expected)
 def test_consumed_full_DWORD_gate_survives_clock_gap(self):
  f=EventEnqueueFrame(b'abc',200)
  self.assertFalse(f.advance(QueueAttempt(0x100,None,True)).complete)
  p=f.advance(QueueAttempt(0,999,None));self.assertFalse(p.complete);self.assertEqual(len(p.queue.records),1)
  self.assertEqual(p.queue.records[0].created_tick,999);self.assertEqual(p.queue.records[0].delay_dword,200)
  self.assertTrue(f.advance(QueueAttempt(None,None,True)).complete);self.assertEqual(len(f.queue.records),1)
 def test_gate_zero_is_known_skip_and_enqueue_return_still_required(self):
  f=EventEnqueueFrame(b'abc',0);p=f.advance(QueueAttempt(0,None,None));self.assertFalse(p.complete)
  p=f.advance(QueueAttempt(1,1,True));self.assertTrue(p.complete);self.assertEqual(p.queue.records,())
 def test_nation_and_copy_prefix_are_retained_before_helper_return(self):
  f=EventPacketFrame('bdw');o=packet();n=dict(o.normal_returns);n['copy']=False
  self.assertFalse(f.advance(replace(o,normal_returns=n)).complete)
  n['copy']=True;n['return']=False;p=f.advance(replace(packet(1),normal_returns=n))
  self.assertFalse(p.complete);self.assertEqual(p.payload,FIRST_TEMPLATES['bdw_nation2']);self.assertEqual(len(p.queue.records),1)
  self.assertTrue(f.advance(EventPacketObservation(normal_returns={'return':True})).complete)
 def test_typed_helper_blocks_opaque_outer_return_and_stamp(self):
  f=EventJoinFrame();o=sample(first_chaos_byte=1,priority_chaos_byte=1)
  p=f.advance(replace(o,packet_children={'chaos_join':EventPacketObservation()}))
  self.assertEqual(p.needed,('child','chaos_join'));self.assertEqual(p.stores,())
  n=dict(o.normal_returns);n['chaos_join']=False
  p=f.advance(replace(o,normal_returns=n,packet_children={'chaos_join':packet()}))
  self.assertEqual(p.needed,('normal','chaos_join'));self.assertEqual(len(p.queue.records),1);self.assertEqual(p.stores,())
  p=f.advance(o);self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1)
 def test_JR_double_enqueue_prefix_and_independent_clock_observations(self):
  f=EventJoinFrame();o=sample(second_jr_byte=1,priority_jr_byte=1)
  p=f.advance(replace(o,enqueue_children={'jr_enqueue0':QueueAttempt(1,100,True),'jr_enqueue200':QueueAttempt(1,None,True)}))
  self.assertEqual(p.needed,('child','jr_enqueue200'));self.assertEqual(len(p.queue.records),1);self.assertEqual(p.stores,())
  p=f.advance(replace(o,enqueue_children={'jr_enqueue0':QueueAttempt(0,999,True),'jr_enqueue200':QueueAttempt(0,222,True)}))
  self.assertTrue(p.complete);self.assertEqual([r.created_tick for r in p.queue.records],[100,222])
  self.assertEqual([r.delay_dword for r in p.queue.records],[0,200]);self.assertEqual(p.queue.records[0].payload,p.queue.records[1].payload)
 def test_shared_queue_across_first_and_second_groups_preserves_seed(self):
  seed=enqueue(QueueState(),b'seed',4,0,1,1).state
  o=replace(sample(first_chaos_byte=1,priority_chaos_byte=1,second_ft_byte=1,priority_ft_byte=1),
   packet_children={'chaos_join':packet(tick=10)},enqueue_children={'ft_enqueue':QueueAttempt(1,20,True)})
  p=EventJoinFrame(queue=seed).advance(o);self.assertTrue(p.complete)
  self.assertEqual([r.record_id for r in p.queue.records],[1,2,3]);self.assertEqual(p.queue.records[0].payload,b'seed')
  self.assertEqual(p.queue.records[1].payload,FIRST_TEMPLATES['chaos']);self.assertEqual(p.queue.records[2].payload,DIRECT_TEMPLATES[0x5212e0])
 def test_opaque_return_cannot_be_retroactively_replaced_by_child(self):
  f=EventJoinFrame();o=sample(first_chaos_byte=1,priority_chaos_byte=1);n=dict(o.normal_returns);n['first_post_tick']=False
  self.assertFalse(f.advance(replace(o,normal_returns=n)).complete)
  with self.assertRaisesRegex(ValueError,'retroactively'):f.advance(replace(o,packet_children={'chaos_join':packet()}))
 def test_unreached_children_do_not_create_queue_records(self):
  o=replace(sample(second_ft_byte=1,target_first_eax=3000),enqueue_children={'ft_enqueue':QueueAttempt(1,1,True)})
  p=EventJoinFrame().advance(o);self.assertTrue(p.complete);self.assertEqual(p.queue.records,());self.assertEqual(p.children,())
 def test_single_plan_and_stateful_frame_share_same_owned_result(self):
  o=replace(sample(second_utc_byte=1,priority_utc_byte=1),enqueue_children={'utc_enqueue':QueueAttempt(1,333,True)})
  p=plan_event_join(o);f=EventJoinFrame();q=f.advance(o)
  self.assertEqual(p.queue,q.queue);self.assertTrue(p.complete);self.assertFalse(p.queue_effect_verified)
  self.assertIs(f.advance(o),q)

if __name__=='__main__':unittest.main()
