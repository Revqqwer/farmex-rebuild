import unittest
from dataclasses import replace
from chat_pending_binding import PendingConsumerFrame,FULL_SENDER_LABELS
from chat_skill_requests import SPECS,ChatSkillObservation,plan_chat_skill_requests
from chat_skill_consumers import ChatConsumerObservation as O
from direct_chat_packets import DirectChatArgs as A,DirectChatPacketFrame
from test_chat_skill_requests import config,MSG,sample as producer_sample
from test_direct_chat_packets import sample as builder_sample
from test_direct_consumer_binding import fixture

def producer(key):
 family=next(s[1] for s in SPECS if s[0]==key)
 return plan_chat_skill_requests(config((key,)),MSG,producer_sample(family))
def consumer_without_shared_fields(family,kind):
 o,args,label=fixture(family,kind)
 shared=set(FULL_SENDER_LABELS)|{'pending_byte','kind_dword','kind_second_dword','direct_sender_word'}|{'kind_%d_dword'%i for i in range(1,7)}
 v={k:x for k,x in o.values.items() if k not in shared}
 # Full push upper bits remain a separate native register observation.
 v['direct_sender_push_dword']=0xbeef0000|(MSG.sender_dword&0xffff)
 target=None if args.helper=='004e103c' else MSG.sender_dword if family=='Mage' or family=='Priest' and kind==4 else v['direct_sender_push_dword']
 args=A(args.helper,0x5000,target,args.relative_skill)
 c=DirectChatPacketFrame(args).advance(builder_sample())
 return O(v,o.normal_returns,direct_execution=c),label

class PendingBindingTests(unittest.TestCase):
 def test_all_nine_producer_requests_reach_direct_consumer_without_duplicate_sender_inputs(self):
  for spec in SPECS:
   key,family,*_=spec;kind=spec[-1];o,label=consumer_without_shared_fields(family,kind)
   p=PendingConsumerFrame(producer(key),family,0x5000).advance(o)
   self.assertTrue(p.complete,(key,p.missing));self.assertEqual(p.consumer.return_low_al,1)
   self.assertEqual(p.pending_stores,((0x5693a0,1,1),(0x5693a4,4,kind),(0x5693a8,4,MSG.sender_dword)))
   self.assertEqual(len(p.consumer.direct_execution.queue.records),2)
   self.assertFalse(p.live_compatibility_verified)

 def test_pending_identity_does_not_replace_separate_actor_context(self):
  o,label=consumer_without_shared_fields('Mage',1)
  with self.assertRaises(ValueError):PendingConsumerFrame(producer('mage_tp'),'Mage',0x6000).advance(o)
  with self.assertRaises(ValueError):PendingConsumerFrame(producer('mage_tp'),'Mage',0x5000,message_context_base=0x6000)

 def test_incomplete_producer_does_not_consume_consumer_or_return_receipts(self):
  p=plan_chat_skill_requests(config(),MSG,ChatSkillObservation())
  result=PendingConsumerFrame(p,'Mage',0x5000).advance(O())
  self.assertFalse(result.complete);self.assertEqual(result.status,'producer_incomplete');self.assertIsNone(result.consumer)

 def test_no_new_request_does_not_run_existing_pending_state(self):
  p=plan_chat_skill_requests(config(),MSG,producer_sample(pending_byte=1))
  result=PendingConsumerFrame(p,'Mage',0x5000).advance(O({'pending_byte':255}))
  self.assertTrue(result.complete);self.assertEqual(result.status,'no_new_request');self.assertIsNone(result.consumer)

 def test_wrong_family_kind_or_store_triplet_rejected(self):
  p=producer('mage_tp')
  with self.assertRaises(ValueError):PendingConsumerFrame(p,'Rogue',0x5000)
  for request in (replace(p.queued_request,kind=2),replace(p.queued_request,context_stores=())):
   with self.assertRaises(ValueError):PendingConsumerFrame(replace(p,queued_request=request),'Mage',0x5000)

 def test_conflicting_explicit_stable_fields_rejected(self):
  for label,value in (('pending_byte',0),('kind_dword',2),('generic_sender_dword',1),('direct_sender_word',7)):
   f=PendingConsumerFrame(producer('mage_tp'),'Mage',0x5000)
   with self.assertRaises(ValueError):f.advance(O({label:value}))

 def test_frame_resumes_outer_return_without_prior_observations(self):
  o,label=consumer_without_shared_fields('Mage',1);r=dict(o.normal_returns);r[label]=False
  f=PendingConsumerFrame(producer('mage_tp'),'Mage',0x5000)
  p=f.advance(replace(o,normal_returns=r));self.assertFalse(p.complete)
  p=f.advance(O(normal_returns={label:True}));self.assertTrue(p.complete)
  self.assertIs(f.advance(O()),p);self.assertEqual(len(p.consumer.direct_execution.queue.records),2)

 def test_runtime_lock_and_gate_still_need_independent_observations(self):
  f=PendingConsumerFrame(producer('mage_tp'),'Mage',0x5000)
  p=f.advance(O());self.assertFalse(p.complete);self.assertEqual(p.missing,'lock_byte value')
  p=f.advance(O({'lock_byte':1}));self.assertTrue(p.complete)
  self.assertEqual(p.consumer.return_low_al,0);self.assertEqual(p.consumer.stores,())

if __name__=='__main__':unittest.main()
