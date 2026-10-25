import unittest
from dataclasses import replace
from chat_pending_session import ChatPendingSession,ChatSessionState
from chat_skill_requests import ChatSkillObservation
from chat_skill_consumers import ChatConsumerObservation as O
from direct_chat_packets import DirectChatPacketFrame
from action_queue import QueueState,enqueue
from attack_lock import AttackLockState
from test_chat_skill_requests import config,MSG,sample as producer_sample
from test_chat_pending_binding import consumer_without_shared_fields
from test_direct_chat_packets import sample as builder_sample

def receive(session,key='mage_tp',family='Mage',sender=MSG.sender_dword):
 session.begin_message(config((key,)),replace(MSG,sender_dword=sender))
 o=producer_sample(family);v=dict(o.values);del v['pending_byte']
 return session.advance_message(ChatSkillObservation(v,o.normal_returns))
def direct_o(session,family='Mage',kind=1):
 o,label=consumer_without_shared_fields(family,kind)
 args=o.direct_execution.build.args
 if args.target_argument_dword is not None:
  target=session.state.sender_dword if family=='Mage' or family=='Priest' and kind==4 else 0xbeef0000|(session.state.sender_dword&0xffff)
  args=replace(args,target_argument_dword=target)
 v=dict(o.values);v['direct_sender_push_dword']=0xbeef0000|(session.state.sender_dword&0xffff)
 child=DirectChatPacketFrame(args,session.state.queue).advance(builder_sample())
 return replace(o,values=v,direct_execution=child),label

class ChatPendingSessionTests(unittest.TestCase):
 def test_new_message_cannot_overwrite_existing_pending_request(self):
  s=ChatPendingSession();receive(s,sender=0xaaaa1234);before=s.state
  p=receive(s,sender=0xbbbb5678)
  self.assertTrue(p.complete);self.assertEqual(p.status,'pending_request_preserved');self.assertEqual(s.state,before)

 def test_two_messages_lock_wait_unlock_and_queue_append(self):
  s=ChatPendingSession();receive(s);o,label=direct_o(s);s.begin_consumer('Mage',0x5000)
  p=s.advance_consumer(o);self.assertTrue(p.complete);self.assertEqual(s.state.pending_byte,0)
  self.assertEqual(s.state.lock,AttackLockState(1,1500,100));self.assertEqual(len(s.state.queue.records),2)
  self.assertEqual(s.state.sender_dword,MSG.sender_dword)
  receive(s,sender=0xbbbb5678) #Producer has no attack-lock gate.
  self.assertEqual(s.state.pending_byte,1);s.begin_consumer('Mage',0x5000)
  self.assertEqual(s.advance_consumer(O()).return_low_al,0);self.assertEqual(s.state.pending_byte,1)
  self.assertEqual(s.apply_reached_unlock_timer(1599).status,'wait_lock_duration')
  self.assertEqual(s.apply_reached_unlock_timer(1600).status,'lock_cleared')
  o,label=direct_o(s);s.begin_consumer('Mage',0x5000);s.advance_consumer(o)
  self.assertEqual([r.record_id for r in s.state.queue.records],[1,2,3,4]);self.assertEqual(s.state.pending_byte,0)

 def test_partial_priest_preclear_is_prospective_until_own_transaction_finishes(self):
  s=ChatPendingSession();receive(s,'priest_cure','Priest');before=s.state
  o,label=direct_o(s,'Priest',5);r=dict(o.normal_returns);r[label]=False
  s.begin_consumer('Priest',0x5000);p=s.advance_consumer(replace(o,normal_returns=r))
  self.assertFalse(p.complete);self.assertIn((0x5693a0,1,0),p.stores);self.assertEqual(s.state,before)
  with self.assertRaises(ValueError):s.begin_message(config(),MSG)
  with self.assertRaises(ValueError):s.apply_reached_unlock_timer(999)
  self.assertTrue(s.advance_consumer(O(normal_returns={label:True})).complete)
  self.assertEqual(s.state.pending_byte,0);self.assertEqual(len(s.state.queue.records),2)

 def test_child_queue_cannot_discard_prior_messages(self):
  q=enqueue(QueueState(),b'prior',5,0,1,1).state
  s=ChatPendingSession(ChatSessionState(queue=q));receive(s);before=s.state
  o,label=consumer_without_shared_fields('Mage',1);s.begin_consumer('Mage',0x5000)
  with self.assertRaises(ValueError):s.advance_consumer(o)
  self.assertEqual(s.state,before)

 def test_generic_failure_retains_request_and_leaves_queue_lock_unchanged(self):
  s=ChatPendingSession();receive(s);before=s.state;o,label=direct_o(s)
  v=dict(o.values);v.update(alternate_byte=1,generic_skill_eax=0)
  s.begin_consumer('Mage',0x5000);p=s.advance_consumer(replace(o,values=v,direct_execution=None))
  self.assertTrue(p.complete);self.assertEqual(p.return_low_al,0);self.assertEqual(s.state,before)

 def test_mage_failure_retains_while_rogue_failure_clears(self):
  for family,key,pending in (('Mage','mage_tp',1),('Rogue','rogue_sw',0)):
   s=ChatPendingSession();receive(s,key,family);o,label=direct_o(s,family)
   v=dict(o.values);v['level_eax']=9;s.begin_consumer(family,0x5000)
   p=s.advance_consumer(replace(o,values=v));self.assertEqual(p.return_low_al,0)
   self.assertEqual(s.state.pending_byte,pending);self.assertEqual(s.state.queue.records,())

 def test_reached_timer_wrap_equality_and_missing_clock(self):
  s=ChatPendingSession(ChatSessionState(lock=AttackLockState(1,32,0xfffffff0)));before=s.state
  self.assertFalse(s.apply_reached_unlock_timer().complete);self.assertEqual(s.state,before)
  self.assertEqual(s.apply_reached_unlock_timer(0xf).status,'wait_lock_duration')
  self.assertEqual(s.apply_reached_unlock_timer(0x10).status,'lock_cleared')
  self.assertEqual(s.state.lock,AttackLockState(0,32,0xfffffff0))

 def test_incomplete_message_blocks_other_events_and_resumes_once(self):
  s=ChatPendingSession();s.begin_message(config(('mage_tp',)),MSG)
  self.assertFalse(s.advance_message(ChatSkillObservation()).complete);self.assertEqual(s.state.pending_byte,0)
  with self.assertRaises(ValueError):s.begin_consumer('Mage',0x5000)
  o=producer_sample();self.assertTrue(s.advance_message(o).complete);self.assertEqual(s.state.pending_byte,1)
  with self.assertRaises(ValueError):s.advance_message(o)

if __name__=='__main__':unittest.main()
