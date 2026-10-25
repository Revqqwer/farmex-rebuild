import unittest
from dataclasses import replace
from chat_commands import ChatCommandsFrame,ChatCommandsObservation as C,plan_chat_commands
from chat_party_invite import ChatPartyMessage
from bot_switch import BotSwitchFrame,BotSwitchObservation as B,plan_bot_switch
from test_bot_switch import fixture,config,CTX
from test_chat_commands import observations
from test_genie_getter_binding import child
from native_profile_versions import CURRENT_SOURCE_SHA256 as CURRENT,LEGACY_SOURCE_SHA256 as OLD

MSG=ChatPartyMessage(2,7,b'Alice',b'go')
CHAT_CASES=(('genie_start','genie_start_state','004631c8',0),('genie_start','genie_remaining','004631e8',1),('genie_stop','genie_stop_state','004631c8',1))

class ChatBotGetterBindingTests(unittest.TestCase):
 def test_three_chat_sites_and_bot_stop_carry_exact_child(self):
  for action,key,helper,raw in CHAT_CASES:
   c=child(helper,raw);p=plan_chat_commands(config(action),MSG,replace(observations(),getter_executions={key:c}))
   self.assertTrue(p.complete);self.assertIs(dict(p.getter_executions)[key],c);self.assertEqual(p.actions[0].key,action)
  c=child('004631c8',1);p=plan_bot_switch(CTX,0,replace(fixture(stop_genie_state_eax=1),getter_executions={'stop_genie_state':c}))
  self.assertTrue(p.complete);self.assertIs(dict(p.getter_executions)['stop_genie_state'],c)

 def test_incomplete_children_block_positive_outer_returns(self):
  for action,key,helper,raw in CHAT_CASES:
   p=plan_chat_commands(config(action),MSG,replace(observations(),getter_executions={key:child(helper,raw,normal=False)}))
   self.assertFalse(p.complete);self.assertEqual(p.missing,'bound getter:'+key);self.assertEqual(p.actions,())
  p=plan_bot_switch(CTX,0,replace(fixture(),getter_executions={'stop_genie_state':child('004631c8',0,normal=False)}))
  self.assertFalse(p.complete);self.assertEqual(p.request,('getter','stop_genie_state'))
  self.assertFalse(any(s.source=='stop_context_reset' for s in p.stores))

 def test_separate_outer_return_and_full_eax_required(self):
  for action,key,helper,raw in CHAT_CASES:
   o=observations();r=dict(o.helper_returns);r[key]=False
   p=plan_chat_commands(config(action),MSG,replace(o,helper_returns=r,getter_executions={key:child(helper,raw)}))
   self.assertFalse(p.complete);self.assertEqual(p.missing,key+' normal return')
   with self.assertRaises(ValueError):plan_chat_commands(config(action),MSG,replace(o,getter_executions={key:child(helper,raw^0x100)}))
  with self.assertRaises(ValueError):plan_bot_switch(CTX,0,replace(fixture(),getter_executions={'stop_genie_state':child('004631c8',0x100)}))

 def test_chat_frame_resumes_child_then_outer_without_repeating_prefix(self):
  for action,key,helper,raw in CHAT_CASES:
   o=replace(observations(),getter_executions={key:child(helper,raw,normal=False)})
   f=ChatCommandsFrame(config(action),MSG);self.assertFalse(f.advance(o).complete)
   c=child(helper,raw);p=f.advance(replace(observations(),getter_executions={key:c}))
   self.assertTrue(p.complete);self.assertIs(dict(p.getter_executions)[key],c);self.assertIs(f.advance(C()),p)

 def test_bot_frame_resumes_and_keeps_completed_child_at_movement_gap(self):
  o=fixture(stop_genie_state_eax=1);c=child('004631c8',1);r=dict(o.normal_returns);r['stop_movement']=False
  f=BotSwitchFrame(CTX,0);p=f.advance(replace(o,normal_returns=r,getter_executions={'stop_genie_state':c}))
  self.assertFalse(p.complete);self.assertEqual(p.request,('normal','stop_movement'))
  p=f.advance(B(normal_returns={'stop_movement':True},getter_executions={'stop_genie_state':child('004631e8',9)}))
  self.assertTrue(p.complete);self.assertIs(dict(p.getter_executions)['stop_genie_state'],c)

 def test_wrong_helper_ignored_when_unreached_and_rejected_when_reached(self):
  c=child('004631e8',0)
  with self.assertRaises(ValueError):plan_chat_commands(config('genie_start'),MSG,replace(observations(),getter_executions={'genie_start_state':c}))
  p=plan_chat_commands(config('genie_start'),MSG,replace(observations(genie_blocked_byte=1),getter_executions={'genie_start_state':c}))
  self.assertTrue(p.complete);self.assertEqual(p.getter_executions,())
  p=plan_bot_switch(CTX,1,replace(fixture(5),getter_executions={'stop_genie_state':c}))
  self.assertTrue(p.complete);self.assertEqual(p.getter_executions,())

 def test_reached_chat_getters_cannot_mix_source_versions(self):
  o=replace(observations(),getter_executions={'genie_start_state':child('004631c8',0,source=CURRENT),
   'genie_remaining':child('004631e8',1,source=OLD)})
  with self.assertRaises(ValueError):plan_chat_commands(config('genie_start'),MSG,o)
  p=plan_chat_commands(config('genie_start'),MSG,replace(o,genie_start_state_eax=2,
   getter_executions={**o.getter_executions,'genie_start_state':child('004631c8',2,source=CURRENT)}))
  self.assertTrue(p.complete);self.assertEqual(len(p.getter_executions),1)

 def test_wrong_frame_operand_enrichment_cannot_replace_consumed_getter(self):
  c=child('004631c8',0,normal=False);f=ChatCommandsFrame(config('genie_start'),MSG)
  self.assertFalse(f.advance(replace(observations(),getter_executions={'genie_start_state':c})).complete)
  from genie_getters import plan_genie_getter
  from motion_genie_helpers import GuardedReadReceipt as R
  a=c.input_snapshot;changed=replace(a,guarded_reads=(R(0x1000,4,0x3000,True),R(0x3020,1,0,True)),normal_returns={'wrapper_return':True})
  with self.assertRaises(ValueError):f.advance(C(getter_executions={'genie_start_state':plan_genie_getter('004631c8',changed)}))

 def test_bot_child_and_action_still_have_independent_parent_boundaries(self):
  c=child('004631c8',1);b=plan_bot_switch(CTX,0,replace(fixture(stop_genie_state_eax=1),getter_executions={'stop_genie_state':c}))
  o=replace(observations(),action_executions={'bot_stop':b});r=dict(o.helper_returns);r['action:bot_stop']=False
  p=plan_chat_commands(config('bot_stop'),MSG,replace(o,helper_returns=r))
  self.assertFalse(p.complete);self.assertIs(p.actions[0].helper_execution,b)
  p=plan_chat_commands(config('bot_stop'),MSG,o);self.assertTrue(p.complete);self.assertFalse(p.native_execution_verified)

 def test_chat_raw_upper_bits_match_while_source_low_al_decision_is_preserved(self):
  p=plan_chat_commands(config('genie_start'),MSG,replace(observations(genie_start_state_eax=0x100),
   getter_executions={'genie_start_state':child('004631c8',0x100)}))
  self.assertTrue(p.complete);self.assertEqual(p.actions[0].key,'genie_start')
  p=plan_bot_switch(CTX,0,replace(fixture(stop_genie_state_eax=2),getter_executions={'stop_genie_state':child('004631c8',2)}))
  self.assertTrue(p.complete);self.assertFalse(any(s[0]=='opaque_call' and s[1]=='004ca4c4' for s in p.steps))

if __name__=='__main__':unittest.main()
