import unittest,struct
from direct_chat_packets import (DirectChatArgs as A,DirectChatObservation as O,QueueAttempt as Q,
    DirectChatPacketFrame,FIRST_TEMPLATE,plan_direct_chat_packets)
from action_queue import QueueState,enqueue

def sample(**values):
 v=dict(class_eax=100,actor_eax=0x11223344,x_eax=0xfffffff6,y_eax=20,z_eax=30);v.update(values)
 return O(v,{k:True for k in ('frame_setup','class_getter','actor_getter','x_getter','y_getter','z_getter','return_span')},
          (Q(1,100,True),Q(1,101,True)))

class DirectChatPacketTests(unittest.TestCase):
 def test_tp_two_exact_lengths_delays_and_dword_fields(self):
  p=plan_direct_chat_packets(A('0049e8c8',0x5000,0x55667788),sample())
  self.assertTrue(p.complete);self.assertEqual([(len(b),d) for b,d in p.payloads],[(48,0),(34,1500)])
  first,second=[b for b,d in p.payloads]
  self.assertEqual(first[:14].hex(),'3101a48601004433221188776655')
  self.assertEqual(second[:14].hex(),'3103a48601004433221188776655')
  self.assertEqual(struct.unpack_from('<III',second,14),(0xfffffff6,20,30))
  self.assertEqual(first[14:],FIRST_TEMPLATE[14:])

 def test_priest_word_copy_and_fixed_cure_disease_relatives(self):
  for helper,relative in (('004d3568',700),('004d3674',525),('004d3690',535)):
   args=A(helper,0x5000,0xdead1234,relative if helper=='004d3568' else None)
   p=plan_direct_chat_packets(args,sample());self.assertTrue(p.complete)
   self.assertEqual([(len(b),d) for b,d in p.payloads],[(48,0),(26,1500)])
   for b,d in p.payloads:
    self.assertEqual(struct.unpack_from('<IIH',b,2),(100000+relative,0x11223344,0x1234))
    self.assertEqual(b[12:14],b'\0\0')

 def test_priest_zero_low_word_skips_after_class_and_actor_getters(self):
  args=A('004d3568',0x5000,0xbeef0000,700)
  p=plan_direct_chat_packets(args,O())
  self.assertFalse(p.complete);self.assertEqual(p.missing,'frame_setup normal return')
  p=plan_direct_chat_packets(args,sample());self.assertTrue(p.complete);self.assertEqual(p.payloads,())
  self.assertEqual(p.status,'source_zero_target_WORD_skip')
  self.assertEqual(len(plan_direct_chat_packets(A('0049e8c8',0x5000,0),sample()).payloads),2)

 def test_class_arithmetic_wrap_and_argument_identity(self):
  a=A('0049e8c8',0x5000,7);p=plan_direct_chat_packets(a,sample(class_eax=0xffffffff))
  self.assertEqual(p.action_id,0xfffffc1c);self.assertEqual(a.push_order,(7,0x5000))
  self.assertEqual(A('004d3568',0x5000,0xbeef1234,700).push_order,(0xbeef1234,700,0x5000))
  with self.assertRaises(ValueError):A('004d3674',0x5000,7,535)

 def test_every_reached_getter_value_and_normal_is_required(self):
  o=sample();args=A('0049e8c8',0x5000,7)
  for label in ('frame_setup','class_getter','actor_getter','x_getter','y_getter','z_getter'):
   r=dict(o.normal_returns);r[label]=False
   self.assertFalse(plan_direct_chat_packets(args,O(o.values,r)).complete,label)
  for label in o.values:
   v=dict(o.values);del v[label]
   self.assertFalse(plan_direct_chat_packets(args,O(v,o.normal_returns)).complete,label)

 def test_first_record_survives_second_enqueue_gap(self):
  f=DirectChatPacketFrame(A('0049e8c8',0x5000,7));o=sample()
  p=f.advance(O(o.values,o.normal_returns,(Q(1,100,True),Q())))
  self.assertFalse(p.complete);self.assertEqual(len(p.queue.records),1)
  final=f.advance(O(normal_returns={'return_span':True},enqueues=(Q(),Q(1,101,True))))
  self.assertTrue(final.complete);self.assertEqual([r.record_id for r in final.queue.records],[1,2])
  self.assertEqual([r.delay_dword for r in final.queue.records],[0,1500])
  self.assertIs(f.advance(O()),final)

 def test_enqueue_committed_once_before_separate_helper_return(self):
  f=DirectChatPacketFrame(A('004d3568',0x5000,7,700));o=sample()
  p=f.advance(O(o.values,o.normal_returns,(Q(1,100,False),)))
  self.assertFalse(p.complete);self.assertEqual(len(p.queue.records),1)
  p=f.advance(O(enqueues=(Q(0,999,False),)))
  self.assertFalse(p.complete);self.assertEqual(p.queue.records[0].created_tick,100)
  p=f.advance(O(normal_returns={'return_span':True},enqueues=(Q(0,999,True),Q(1,101,True))))
  self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),2)

 def test_independent_gates_can_skip_first_copy_but_queue_second(self):
  f=DirectChatPacketFrame(A('004d3674',0x5000,7));o=sample()
  p=f.advance(O(o.values,o.normal_returns,(Q(0,None,True),Q(1,100,True))))
  self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1)
  self.assertEqual(p.queue.records[0].payload[:2],b'\x31\x03')
  self.assertFalse(p.packet_delivery_verified)

 def test_known_gate_is_not_changed_while_waiting_for_tick(self):
  f=DirectChatPacketFrame(A('004d3690',0x5000,7));o=sample()
  p=f.advance(O(o.values,o.normal_returns,(Q(1,None,True),)))
  self.assertIn('GetTickCount',p.missing)
  p=f.advance(O(normal_returns={'return_span':True},enqueues=(Q(0,200,True),Q(0,None,True))))
  self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1)
  self.assertEqual(p.queue.records[0].created_tick,200)

 def test_builder_prefix_is_cached_when_last_coordinate_arrives(self):
  f=DirectChatPacketFrame(A('0049e8c8',0x5000,7));o=sample();v=dict(o.values);del v['z_eax']
  self.assertFalse(f.advance(O(v,o.normal_returns)).complete)
  p=f.advance(sample(class_eax=999,actor_eax=999,x_eax=999,y_eax=999))
  self.assertTrue(p.complete);self.assertEqual(p.build.action_id,100004)
  self.assertEqual(struct.unpack_from('<II',p.queue.records[1].payload,6),(0x11223344,7))
  self.assertEqual(struct.unpack_from('<III',p.queue.records[1].payload,14),(0xfffffff6,20,30))

 def test_return_span_gap_keeps_both_records_without_duplicate(self):
  f=DirectChatPacketFrame(A('004d3568',0x5000,7,700));o=sample();r=dict(o.normal_returns);r['return_span']=False
  p=f.advance(O(o.values,r,o.enqueues));self.assertFalse(p.complete);self.assertEqual(len(p.queue.records),2)
  p=f.advance(O(normal_returns={'return_span':True}));self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),2)

 def test_zero_word_skip_preserves_preexisting_queue_and_unknown_eax(self):
  q=enqueue(QueueState(),b'old',3,0,1,1).state
  f=DirectChatPacketFrame(A('004d3674',0x5000,0xbeef0000),q)
  p=f.advance(sample());self.assertTrue(p.complete);self.assertEqual(p.queue,q);self.assertEqual(p.enqueue_decisions,())
  self.assertFalse(p.helper_EAX_verified)

 def test_str_guard_and_copy_use_full_dword(self):
  for target in (0xbeef0000,0xdead1234):
   p=plan_direct_chat_packets(A('004d36ac',0x5000,target),sample())
   self.assertEqual([(len(b),d) for b,d in p.payloads],[(48,0),(26,1500)])
   for b,d in p.payloads:self.assertEqual(struct.unpack_from('<III',b,2),(100004,0x11223344,target))
  p=plan_direct_chat_packets(A('004d36ac',0x5000,0),sample())
  self.assertEqual(p.status,'source_zero_target_DWORD_skip');self.assertEqual(p.payloads,())
  self.assertEqual(p.steps[-1],('source_value','actor_eax'))

 def test_sw_zero_word_still_builds_and_only_word_is_copied(self):
  for target in (0,0xbeef0000,0xdead1234):
   a=A('004e08e0',0x5000,target);p=plan_direct_chat_packets(a,sample())
   self.assertEqual(a.push_order,(target,0x5000))
   self.assertEqual([(len(b),d) for b,d in p.payloads],[(48,0),(38,1500)])
   for b,d in p.payloads:
    self.assertEqual(struct.unpack_from('<IIH',b,2),(100010,0x11223344,target&0xffff))
    self.assertEqual(b[12:14],b'\0\0')

 def test_wolf_has_no_target_and_both_records_have_xzy(self):
  a=A('004e103c',0x5000);p=plan_direct_chat_packets(a,sample())
  self.assertEqual(a.push_order,(0x5000,));self.assertEqual(a.relative_skill,30)
  self.assertEqual([(len(b),d) for b,d in p.payloads],[(48,0),(38,1700)])
  for b,d in p.payloads:
   self.assertEqual(struct.unpack_from('<III',b,2),(100030,0x11223344,0xffffffff))
   self.assertEqual(struct.unpack_from('<III',b,14),(0xfffffff6,30,20))
  self.assertEqual(p.payloads[0][0][42],0x11)
  self.assertEqual([v for k,v,*rest in p.steps if k=='source_value'],['class_eax','actor_eax','x_eax','y_eax','z_eax'])
  with self.assertRaises(ValueError):A('004e103c',0x5000,0)
  with self.assertRaises(ValueError):A('004e103c',0x5000,relative_skill=10)

 def test_wolf_reached_coordinate_gaps_keep_consumed_prefix(self):
  f=DirectChatPacketFrame(A('004e103c',0x5000));o=sample();v=dict(o.values);del v['z_eax']
  p=f.advance(O(v,o.normal_returns));self.assertFalse(p.complete);self.assertEqual(p.queue.records,())
  p=f.advance(sample(class_eax=999,actor_eax=999,x_eax=999,y_eax=999))
  self.assertTrue(p.complete)
  for record in p.queue.records:
   self.assertEqual(struct.unpack_from('<III',record.payload,14),(0xfffffff6,30,20))
   self.assertEqual(struct.unpack_from('<I',record.payload,2)[0],100030)

 def test_wolf_second_gap_and_late_return_do_not_duplicate_records(self):
  f=DirectChatPacketFrame(A('004e103c',0x5000));o=sample()
  p=f.advance(O(o.values,o.normal_returns,(Q(1,100,True),Q(1,None,True))))
  self.assertFalse(p.complete);self.assertEqual(len(p.queue.records),1)
  p=f.advance(O(enqueues=(Q(),Q(0,200,False))))
  self.assertFalse(p.complete);self.assertEqual([r.delay_dword for r in p.queue.records],[0,1700])
  p=f.advance(O(normal_returns={'return_span':True},enqueues=(Q(),Q(0,300,True))))
  self.assertTrue(p.complete);self.assertEqual([r.created_tick for r in p.queue.records],[100,200])
  self.assertIs(f.advance(sample()),p);self.assertFalse(p.packet_delivery_verified)

 def test_new_fixed_relatives_and_str_sw_skip_unreached_coordinate_inputs(self):
  for helper,relative in (('004d36ac',4),('004e08e0',10)):
   p=plan_direct_chat_packets(A(helper,0x5000,1),O({'class_eax':0xffffffff,'actor_eax':1},
    {'frame_setup':True,'class_getter':True,'actor_getter':True}))
   self.assertTrue(p.complete);self.assertEqual(p.action_id,(0xffffffff*1000+relative)&0xffffffff)
   with self.assertRaises(ValueError):A(helper,0x5000,1,relative+1)

if __name__=='__main__':unittest.main()
