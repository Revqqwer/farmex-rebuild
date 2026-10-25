import unittest,struct
from dataclasses import replace
from chat_skill_consumers import ChatConsumerObservation as O,ChatConsumerFrame,plan_chat_consumer
from direct_chat_packets import DirectChatArgs as A,DirectChatObservation as D,QueueAttempt as Q,DirectChatPacketFrame
from test_direct_chat_packets import sample as builder_sample
from test_chat_skill_consumers import sample as mr_sample
from test_priest_chat_consumer import sample as priest_sample

CASES=(('Mage',1),('Rogue',1),('Rogue',2))+tuple(('Priest',k) for k in range(1,7))
def fixture(family,kind=1,**values):
 o=priest_sample(kind,alternate_byte=0,**values) if family=='Priest' else mr_sample(kind_dword=kind,alternate_byte=0,**values)
 if family=='Mage':args=A('0049e8c8',0x5000,o.values['direct_sender_dword']);label='direct_mage'
 elif family=='Rogue':
  args=A('004e08e0',0x5000,o.values['direct_sender_push_dword']) if kind==1 else A('004e103c',0x5000)
  label='direct_sw' if kind==1 else 'direct_wolf'
 else:
  helper='004d3568' if kind<4 else {4:'004d36ac',5:'004d3674',6:'004d3690'}[kind]
  sender=o.values['direct_sender_dword' if kind==4 else 'direct_sender_push_dword']
  args=A(helper,0x5000,sender,{1:700,2:701,3:654}.get(kind));label='direct_skill'
 return o,args,label
def child(args,observation=None):return DirectChatPacketFrame(args).advance(builder_sample() if observation is None else observation)
def plan(family,o):return plan_chat_consumer(family,0x5000,o)

class DirectConsumerBindingTests(unittest.TestCase):
 def test_nine_call_sites_bind_exact_child_args_and_keep_queue_metadata(self):
  for family,kind in CASES:
   o,args,label=fixture(family,kind);c=child(args);p=plan(family,replace(o,direct_execution=c))
   self.assertTrue(p.complete,(family,kind,p.missing));self.assertEqual(p.return_low_al,1)
   self.assertIs(p.direct_execution,c);self.assertFalse(p.skill_effect_verified)
   self.assertEqual(next(s[2] for s in p.steps if s[0]=='opaque_helper' and s[3]==label),args.push_order)

 def test_parent_normal_cannot_bypass_incomplete_builder_or_enqueue(self):
  for family,kind in CASES:
   o,args,label=fixture(family,kind)
   for d in (D(),D(builder_sample().values,builder_sample().normal_returns,(Q(1,100,True),))):
    c=child(args,d);p=plan(family,replace(o,direct_execution=c))
    self.assertFalse(p.complete);self.assertTrue(p.missing.startswith('bound direct:'))
    self.assertEqual((0x5693a0,1,0) in p.stores,family=='Priest')

 def test_complete_child_still_requires_parent_helper_return(self):
  for family,kind in CASES:
   o,args,label=fixture(family,kind);r=dict(o.normal_returns);r[label]=False
   p=plan(family,O(o.values,r,direct_execution=child(args)))
   self.assertFalse(p.complete);self.assertEqual(p.missing,label+' normal return')

 def test_wrong_context_full_argument_or_helper_rejected_when_reached(self):
  for family,kind in CASES:
   o,args,label=fixture(family,kind)
   wrong=[replace(args,context_dword=0x6000)]
   if args.target_argument_dword is not None:wrong.append(replace(args,target_argument_dword=args.target_argument_dword^0x10000))
   wrong.append(A('0049e8c8' if family!='Mage' else '004e08e0',0x5000,7))
   for a in wrong:
    c=child(a)
    with self.assertRaises(ValueError):plan(family,replace(o,direct_execution=c))
    v=dict(o.values);v['pending_byte']=0
    p=plan(family,O(v,o.normal_returns,direct_execution=c));self.assertTrue(p.complete);self.assertIsNone(p.direct_execution)

 def test_frame_enriches_partial_child_without_repeating_parent_inputs(self):
  for family,kind in CASES:
   o,args,label=fixture(family,kind);f=ChatConsumerFrame(family,0x5000)
   b=DirectChatPacketFrame(args);d=builder_sample()
   partial=b.advance(D(d.values,d.normal_returns,(Q(1,100,True),)))
   self.assertFalse(f.advance(replace(o,direct_execution=partial)).complete)
   done=b.advance(D(normal_returns={'return_span':True},enqueues=(Q(),Q(1,101,True))))
   p=f.advance(O(normal_returns={label:True},direct_execution=done))
   self.assertTrue(p.complete);self.assertIs(p.direct_execution,done);self.assertIs(f.advance(O()),p)

 def test_changed_consumed_getter_is_rejected_during_child_enrichment(self):
  o,args,label=fixture('Mage');d=builder_sample();v=dict(d.values);del v['z_eax']
  gap=child(args,D(v,d.normal_returns));f=ChatConsumerFrame('Mage',0x5000)
  self.assertFalse(f.advance(replace(o,direct_execution=gap)).complete)
  for altered in (builder_sample(class_eax=999),builder_sample(actor_eax=999),builder_sample(x_eax=999)):
   with self.assertRaises(ValueError):f.advance(O(direct_execution=child(args,altered)))

 def test_existing_record_or_gate_cannot_change_on_resume(self):
  o,args,label=fixture('Rogue');d=builder_sample()
  for first in (Q(1,100,True),Q(1,None,True)):
   partial=child(args,D(d.values,d.normal_returns,(first,)))
   f=ChatConsumerFrame('Rogue',0x5000);self.assertFalse(f.advance(replace(o,direct_execution=partial)).complete)
   altered=child(args,D(d.values,d.normal_returns,(Q(0,None,True),Q(1,101,True))))
   with self.assertRaises(ValueError):f.advance(O(direct_execution=altered))

 def test_completed_child_is_retained_while_parent_return_is_pending(self):
  o,args,label=fixture('Mage');r=dict(o.normal_returns);r[label]=False;c=child(args);f=ChatConsumerFrame('Mage',0x5000)
  self.assertFalse(f.advance(O(o.values,r,direct_execution=c)).complete)
  wrong=child(A('004e103c',0x9999))
  p=f.advance(O(normal_returns={label:True},direct_execution=wrong))
  self.assertTrue(p.complete);self.assertIs(p.direct_execution,c)

 def test_sw_partial_register_bits_remain_call_identity_not_payload(self):
  o,args,label=fixture('Rogue',1);p=plan('Rogue',replace(o,direct_execution=child(args)))
  self.assertEqual(p.direct_execution.build.args.target_argument_dword,0xbeef1234)
  for b,d in p.direct_execution.build.payloads:self.assertEqual(struct.unpack_from('<I',b,10)[0],0x1234)
  bad=dict(o.values);bad['direct_sender_word']=0x1235
  with self.assertRaises(ValueError):plan('Rogue',O(bad,o.normal_returns,direct_execution=child(args)))

 def test_zero_target_skip_is_normal_completion_not_skill_success(self):
  for kind in (1,4,5,6):
   values={'direct_sender_dword':0} if kind==4 else {'direct_sender_word':0,'direct_sender_push_dword':0xbeef0000}
   o,args,label=fixture('Priest',kind,**values);c=child(args);p=plan('Priest',replace(o,direct_execution=c))
   self.assertTrue(p.complete);self.assertEqual(c.queue.records,());self.assertEqual(p.return_low_al,1)
   self.assertFalse(c.helper_EAX_verified);self.assertFalse(p.skill_effect_verified)

 def test_direct_child_is_ignored_on_generic_branch(self):
  for family,kind in CASES:
   o,args,label=fixture(family,kind);v=dict(o.values);v['alternate_byte']=1
   p=plan(family,O(v,o.normal_returns,direct_execution=child(A('004e103c',0x9999))))
   self.assertTrue(p.complete);self.assertIsNone(p.direct_execution)

 def test_wrong_type_rejected_and_legacy_opaque_mode_remains_explicit(self):
  with self.assertRaises(ValueError):O(direct_execution=object())
  o,args,label=fixture('Mage');p=plan('Mage',o)
  self.assertTrue(p.complete);self.assertIsNone(p.direct_execution);self.assertFalse(p.skill_effect_verified)

 def test_bound_direct_queue_survives_all_six_class_head_results(self):
  from test_class_chat_binding import run
  for family in ('Mage','Rogue','Priest'):
   o,args,label=fixture(family);c=child(args);consumer=plan(family,replace(o,direct_execution=c))
   for legal in (False,True):
    p=run(family.lower(),legal,consumer,post_lock=True)
    self.assertEqual(p.status,'complete')
    self.assertIs(p.chat_consumers[0][1].direct_execution,c)
    self.assertFalse(c.packet_delivery_verified)

if __name__=='__main__':unittest.main()
