import unittest,json
from chat_skill_requests import SPECS,ROOTS
from chat_skills_trial import ChatSkillsTrial,EXAMPLE_SKILL_HEX,example_chat_skills_sample

def panel(enabled=None):
 enabled={s[0] for s in SPECS} if enabled is None else set(enabled)
 return {ROOTS[s[1]]+n:v for s in SPECS for n,v in ((s[2],s[0] in enabled),(s[3],'go'))}
def trial(enabled=None):
 values=panel(enabled);return ChatSkillsTrial(lambda:(dict(values),{})),values

class ChatSkillsTrialTests(unittest.TestCase):
 def test_all_nine_real_setting_pairs_feed_request(self):
  for spec in SPECS:
   t,v=trial((spec[0],));p=t.step(EXAMPLE_SKILL_HEX,example_chat_skills_sample(spec[1]),1254)
   self.assertTrue(p.complete);self.assertEqual(p.queued_request.key,spec[0]);self.assertEqual(p.queued_request.sender_dword,7)
   self.assertEqual(p.queued_request.kind,spec[-1]);self.assertFalse(p.native_execution_verified)

 def test_fresh_panel_flag_text_and_first_match_restart_invocation(self):
  t,v=trial();sample=example_chat_skills_sample('Rogue');p=t.step(EXAMPLE_SKILL_HEX,sample,1254)
  self.assertEqual(p.queued_request.key,'rogue_sw');first=t.frame
  v[ROOTS['Rogue']+'chChatSW']=False;p=t.step(EXAMPLE_SKILL_HEX,sample,1254)
  self.assertEqual(p.queued_request.key,'rogue_wolf');self.assertIsNot(t.frame,first)
  v[ROOTS['Rogue']+'txtChatWolf']='GO';p=t.step(EXAMPLE_SKILL_HEX,sample,1254)
  self.assertIsNone(p.queued_request)

 def test_same_completed_snapshot_reuses_frame_without_duplicate_request(self):
  t,v=trial();a=t.step(EXAMPLE_SKILL_HEX,example_chat_skills_sample(),1254);frame=t.frame
  b=t.step(EXAMPLE_SKILL_HEX,'{"values":"unreached"}',1254)
  self.assertIs(a,b);self.assertIs(t.frame,frame)

 def test_late_compare_uses_cached_prefix_and_ignores_bad_consumed_values(self):
  t,v=trial();raw=json.loads(example_chat_skills_sample());del raw['normal_returns']['compare:mage_tp']
  p=t.step(EXAMPLE_SKILL_HEX,json.dumps(raw),1254);self.assertFalse(p.complete);self.assertEqual(p.needed,('normal','compare:mage_tp'))
  raw={'values':'already consumed','normal_returns':{'compare:mage_tp':True}}
  p=t.step(EXAMPLE_SKILL_HEX,json.dumps(raw),1254);self.assertTrue(p.complete);self.assertEqual(p.queued_request.key,'mage_tp')

 def test_reached_invalid_observation_clears_stale_frame(self):
  for raw in ('[]','{bad','{"values":{"channel_first":"bad"}}','{"values":7}'):
   t,v=trial()
   with self.assertRaises((ValueError,TypeError)):t.step(EXAMPLE_SKILL_HEX,raw,1254)
   self.assertIsNone(t.last);self.assertIsNone(t.frame);self.assertIsNone(t.configuration)

 def test_short_hex_and_other_opcode_do_not_parse_observation_groups(self):
  t,v=trial();p=t.step('10','{"values":"unreached"}',1254)
  self.assertFalse(p.complete);self.assertIsNone(t.frame)
  p=t.step('08','{"normal_returns":"unreached"}',1254);self.assertTrue(p.complete);self.assertIsNone(t.frame)
  with self.assertRaises(ValueError):t.step('not hex','{}',1254)
  self.assertIsNone(t.captured)

 def test_codepage_and_packet_changes_restart_owned_invocation(self):
  t,v=trial();sample=example_chat_skills_sample();t.step(EXAMPLE_SKILL_HEX,sample,1254);first=t.frame
  t.step(EXAMPLE_SKILL_HEX,sample,65001);self.assertIsNot(t.frame,first);first=t.frame
  p=t.step(EXAMPLE_SKILL_HEX.replace('07000000','08000000'),sample,65001)
  self.assertEqual(p.queued_request.sender_dword,8);self.assertIsNot(t.frame,first)
  t.reset();self.assertIsNone(t.frame)

 def test_no_panel_reader_and_lossy_keyword_are_rejected(self):
  with self.assertRaises(ValueError):ChatSkillsTrial(None).step(EXAMPLE_SKILL_HEX,'{}',1254)
  t,v=trial();v[ROOTS['Mage']+'txtChatTP']='go😀'
  with self.assertRaises(ValueError):t.step(EXAMPLE_SKILL_HEX,'{}',1254)

if __name__=='__main__':unittest.main()
