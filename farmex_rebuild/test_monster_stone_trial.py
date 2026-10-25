import json,unittest
from monster_stone_trial import *
from monster_stone import WALLHACK_INPUT

def values(enabled=False):
 return dict(zip(MS_PANEL_INPUTS,(True,False,False,enabled)))

class MonsterStoneTrialTests(unittest.TestCase):
 def test_panel_checkbox_and_alarm_compile_while_missing_returns_stay_missing(self):
  v=values(True);v[MS_SETTING_INPUTS[2]]=True;t=MonsterStoneTrial(lambda:(v,{}))
  p=t.step('{}');self.assertEqual(p.settings.mode_after,0)
  self.assertIn((0x562170,1,1),p.settings.stores)
  self.assertFalse(p.activation.complete);self.assertEqual(p.activation.needed,('normal','wallhack_setter'))
  self.assertEqual(p.activation.ui_updates,());self.assertFalse(p.main_worker_executed)

 def test_partial_return_samples_continue_and_apply_own_UI_prefix_once(self):
  v=values(True);writes=[];t=MonsterStoneTrial(lambda:(v,{}),lambda x:writes.append(dict(x)))
  p=t.step(json.dumps({'normal_returns':{'wallhack_setter':True}}));self.assertFalse(p.activation.complete)
  self.assertEqual(writes,[{WALLHACK_INPUT:True}])
  p=t.step(json.dumps({'normal_returns':{'bot_start':True}}));self.assertFalse(p.activation.complete)
  self.assertEqual(p.activation.needed,('normal','activation_return'))
  self.assertTrue(t.step(json.dumps({'normal_returns':{'activation_return':True}})).activation.complete)
  self.assertEqual(len(writes),1)

 def test_disable_clears_only_MS_flag_and_does_not_uncheck_WallHack(self):
  v=values(False);writes=[];t=MonsterStoneTrial(lambda:(v,{}),writes.append)
  p=t.step(json.dumps({'normal_returns':{'activation_return':True},'bot_start':'unreached malformed'}))
  self.assertTrue(p.activation.complete);self.assertEqual(p.activation.stores,((0x561f5c,4,0),))
  self.assertEqual(writes,[])

 def test_mode_retains_when_neither_radio_and_panel_change_starts_fresh_activation(self):
  v=values();v[MS_SETTING_INPUTS[0]]=False;v[MS_SETTING_INPUTS[1]]=True
  t=MonsterStoneTrial(lambda:(v,{}));self.assertEqual(t.step('{}').settings.mode_after,1)
  v[MS_SETTING_INPUTS[1]]=False;self.assertEqual(t.step('{}').settings.mode_after,1)
  v[MS_ENABLE_INPUT]=True;p=t.step('{}');self.assertEqual(p.activation.needed,('normal','wallhack_setter'))
  t.reset();self.assertEqual(t.step('{}').settings.mode_after,0)

 def test_generated_bot_start_incomplete_blocks_opaque_parent_normal(self):
  t=MonsterStoneTrial(lambda:(values(True),{}))
  s=json.loads(example_ms_activation());s['bot_start']={}
  p=t.step(json.dumps(s));self.assertFalse(p.activation.complete)
  self.assertEqual(p.activation.needed,('child','bot_start'));self.assertIsNotNone(p.activation.bot_start)

 def test_bad_sample_clears_last_without_losing_consumed_setter_or_UI_prefix(self):
  writes=[];t=MonsterStoneTrial(lambda:(values(True),{}),writes.append)
  t.step(json.dumps({'normal_returns':{'wallhack_setter':True}}))
  with self.assertRaises(ValueError):t.step('{bad')
  self.assertIsNone(t.last)
  self.assertTrue(t.step(json.dumps({'normal_returns':{'bot_start':True,'activation_return':True}})).activation.complete)
  self.assertEqual(len(writes),1)

 def test_bad_unreached_child_is_ignored_but_reached_child_is_rejected(self):
  t=MonsterStoneTrial(lambda:(values(True),{}))
  self.assertFalse(t.step(json.dumps({'bot_start':'not yet reached'})).activation.complete)
  with self.assertRaises(ValueError):t.step(json.dumps({'normal_returns':{'wallhack_setter':True},'bot_start':'reached malformed'}))

if __name__=='__main__':unittest.main()
