import unittest
from dataclasses import replace
from chat_handler_segments import ChatHandlerSegmentsFrame
from chat_commands import SPECS,CommandSetting,ChatCommandsConfiguration,ChatCommandsObservation
from chat_party_invite import ChatPartyConfiguration,ChatPartyObservation
from chat_skill_requests import ChatSkillObservation
from action_queue import QueueState,enqueue
from test_chat_prelude import sample as prelude_sample,command_sample
from test_chat_skill_requests import config as skill_config,sample as skill_sample
from test_chat_cleanup import ARGS,done as cleanup_done
from chat_skills_trial import EXAMPLE_SKILL_HEX

def config(enabled=False):return ChatCommandsConfiguration(tuple(CommandSetting(s[0],int(enabled and s[0]=='disconnect'),b'go') for s in SPECS))
def frame(command=False,party=False,channel=2,queue=None):
 data=bytearray.fromhex(EXAMPLE_SKILL_HEX);data[1]=channel
 return ChatHandlerSegmentsFrame(config(command),ChatPartyConfiguration(int(party),0,b'go'),skill_config(('mage_tp',)),bytes(data),0,queue)
def samples():return dict(prelude=prelude_sample(2),commands=command_sample(),skills=skill_sample(),cleanup_args=ARGS,cleanup=cleanup_done())

class ChatHandlerSegmentsTests(unittest.TestCase):
 def test_normal_pm_path_preserves_request_and_cleanup_without_whole_native_claim(self):
  f=frame();p=f.advance(**samples())
  self.assertTrue(p.complete);self.assertEqual(p.skills.queued_request.key,'mage_tp');self.assertEqual(p.skills.queued_request.sender_dword,7)
  self.assertTrue(p.cleanup.complete);self.assertFalse(p.full_handler_verified);self.assertFalse(p.returned_EAX_verified)
  self.assertIs(f.advance(prelude=object()),p)

 def test_earlier_gaps_do_not_consume_later_invalid_inputs(self):
  f=frame();p=f.advance(commands=object(),party=object(),skills=object(),cleanup_args=object())
  self.assertEqual(p.status,'needs_prelude');self.assertIsNone(f.command_frame);self.assertIsNone(f.cleanup_frame)
  p=f.advance(prelude=prelude_sample(2),party=object(),skills=object())
  self.assertEqual(p.status,'needs_commands');self.assertIsNone(f.party_frame)
  p=f.advance(commands=command_sample(),skills=ChatSkillObservation(),cleanup_args=object())
  self.assertEqual(p.status,'needs_skills');self.assertIsNone(f.cleanup_frame)

 def test_no_request_still_reaches_cleanup_when_runtime_gate_is_closed(self):
  f=frame();o=skill_sample(runtime_ready_byte=0);s=samples();s['skills']=o
  p=f.advance(**s);self.assertTrue(p.complete);self.assertIsNone(p.skills.queued_request)

 def test_unmodeled_tail_cannot_be_bypassed_by_cleanup_receipts(self):
  f=frame(channel=7);s=samples();s['skills']=skill_sample(channel_first=7,channel_second=7)
  p=f.advance(**s);self.assertFalse(p.complete);self.assertEqual(p.status,'unmodeled_notice_tail');self.assertIsNone(f.cleanup_frame)

 def test_post_command_queue_snapshot_required_and_prior_records_preserved(self):
  q=enqueue(QueueState(),b'old',3,0,1,1).state;f=frame(command=True,queue=q)
  p=f.advance(**samples());self.assertEqual(p.status,'needs_post_command_queue');self.assertIsNone(f.party_frame)
  with self.assertRaises(ValueError):f.advance(after_commands_queue=QueueState())
  q2=enqueue(q,b'\0',1,0,1,2).state
  p=f.advance(after_commands_queue=q2,skills=skill_sample(),cleanup_args=ARGS,cleanup=cleanup_done())
  self.assertTrue(p.complete);self.assertEqual(p.queue,q2)

 def test_party_two_records_survive_late_skill_gap_and_do_not_repeat(self):
  f=frame(party=True);o=ChatPartyObservation(actor_dword=9,helper_returns={k:True for k in ('command_compare','actor','invite_arguments','invite')})
  p=f.advance(prelude=prelude_sample(2),commands=command_sample(),party=o,
   party_enqueue=dict(gates=(1,1),ticks=(100,101),returned=(True,True),cleanup_returned=True))
  self.assertEqual(p.status,'needs_skills');self.assertEqual(len(p.queue.records),2)
  p=f.advance(skills=skill_sample(),cleanup_args=ARGS,cleanup=cleanup_done(),party=object(),party_enqueue=object())
  self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),2)

 def test_partial_cleanup_resumes_without_repeating_source_segments(self):
  f=frame();s=samples();s.pop('cleanup');p=f.advance(**s)
  self.assertEqual(p.status,'needs_cleanup');pre=p.prelude;skills=p.skills
  p=f.advance(cleanup=cleanup_done(),commands=object(),skills=object())
  self.assertTrue(p.complete);self.assertIs(p.prelude,pre);self.assertIs(p.skills,skills)

 def test_short_or_nonchat_packet_does_not_instantiate_later_frames(self):
  for packet,status in ((b'\x10','needs_bytes'),(b'\x08','outside_opcode10_scope')):
   f=ChatHandlerSegmentsFrame(None,None,None,packet,0);p=f.advance(skills=object())
   self.assertFalse(p.complete);self.assertEqual(p.status,status);self.assertIsNone(f.skill_frame)

if __name__=='__main__':unittest.main()
