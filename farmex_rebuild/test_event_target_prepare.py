import json,unittest
from dataclasses import replace
from event_packets import EventPacketFrame,EventPacketObservation,TARGET_TEMPLATE
from direct_chat_packets import QueueAttempt
from event_join import EventJoinFrame
from event_join_trial import EventJoinTrial,event_snapshot,example_event_sample
from test_event_join import sample
from test_event_join_trial import panel

def target(gate=1,tick=100):
 return EventPacketObservation(normal_returns={k:True for k in ('frame_setup','template_copy','target_copy','return')},attempt=QueueAttempt(gate,tick,True))

class EventTargetPreparationTests(unittest.TestCase):
 def test_full_target_DWORD_at_offset_two_preserves_template_tail(self):
  self.assertEqual(TARGET_TEMPLATE.hex(),'200100000000ffffffff')
  p=EventPacketFrame('target_prepare',target=0x89abcdef).advance(target())
  self.assertTrue(p.complete);self.assertEqual(p.payload.hex(),'2001efcdab89ffffffff')
  self.assertEqual(p.queue.records[0].payload,p.payload)
 def test_copy_gap_does_not_consume_earlier_supplied_gate(self):
  f=EventPacketFrame('target_prepare',target=0);o=target(gate=0);n=dict(o.normal_returns);n['target_copy']=False
  self.assertFalse(f.advance(replace(o,normal_returns=n)).complete)
  p=f.advance(target(gate=0x100,tick=None));self.assertFalse(p.complete)
  p=f.advance(target(gate=0,tick=200));self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1)
 def test_fresh_third_target_and_target_before_event_record_order(self):
  o=replace(sample(second_ft_byte=1,priority_ft_byte=1,target_third_eax=0x89abcdef),packet_children={'target_prepare':target()},enqueue_children={'ft_enqueue':QueueAttempt(1,101,True)})
  p=EventJoinFrame().advance(o);self.assertTrue(p.complete)
  self.assertEqual([len(r.payload) for r in p.queue.records],[10,17]);self.assertEqual(p.queue.records[0].payload[2:6],bytes.fromhex('efcdab89'))
 def test_inner_helper_and_outer_return_gate_later_request(self):
  f=EventJoinFrame();o=sample(second_utc_byte=1,priority_utc_byte=1);child=target();n=dict(child.normal_returns);n['return']=False
  p=f.advance(replace(o,packet_children={'target_prepare':replace(child,normal_returns=n)},enqueue_children={'utc_enqueue':QueueAttempt(1,101,True)}))
  self.assertEqual(p.needed,('child','target_prepare'));self.assertEqual(len(p.queue.records),1);self.assertEqual(p.enqueue_requests,())
  n=dict(o.normal_returns);n['target_prepare']=False
  p=f.advance(replace(o,normal_returns=n,packet_children={'target_prepare':target()}));self.assertEqual(p.needed,('normal','target_prepare'))
  p=f.advance(replace(o,enqueue_children={'utc_enqueue':QueueAttempt(1,101,True)}));self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),2)
 def test_invalid_target_path_does_not_invoke_target_packet_child(self):
  o=replace(sample(second_ft_byte=1,target_first_eax=3000),packet_children={'target_prepare':target()})
  p=EventJoinFrame().advance(o);self.assertTrue(p.complete);self.assertEqual(p.children,());self.assertEqual(p.queue.records,())
 def test_panel_nested_target_copy_then_direct_event_tick_gaps(self):
  v=panel('jr');t=EventJoinTrial(lambda:(v,{}));d=json.loads(example_event_sample(event_snapshot(v)))
  d['packet_children']['target_prepare']['normal_returns']['target_copy']=False
  p=t.step(json.dumps(d));self.assertEqual(p.needed,('child','target_prepare'));self.assertEqual(p.queue.records,())
  d['packet_children']['target_prepare']['normal_returns']['target_copy']=True;del d['enqueue_children']['jr_enqueue0']['tick']
  p=t.step(json.dumps(d));self.assertEqual(p.needed,('child','jr_enqueue0'));self.assertEqual(len(p.queue.records),1)
  d['enqueue_children']['jr_enqueue0']['tick']=300;p=t.step(json.dumps(d));self.assertTrue(p.complete)
  self.assertEqual([r.delay_dword for r in p.queue.records],[0,0,200])
 def test_retroactive_target_packet_binding_rejected(self):
  f=EventJoinFrame();o=sample(second_ft_byte=1,priority_ft_byte=1);n=dict(o.normal_returns);n['ft_copy']=False
  self.assertFalse(f.advance(replace(o,normal_returns=n)).complete)
  with self.assertRaisesRegex(ValueError,'retroactively'):f.advance(replace(o,packet_children={'target_prepare':target()}))

if __name__=='__main__':unittest.main()
