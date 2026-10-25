import unittest
from dataclasses import replace
from monster_stone import *
from test_bot_switch import fixture as start

def settings(boss=1,all_mobs=1,alarm=1):
 return MSObservation({'boss_eax':boss,'all_mobs_eax':all_mobs,'alarm_eax':alarm},
  {k:True for k in ('boss','all_mobs','alarm','settings_return')})
def activation(enabled=1,child=None):
 return MSObservation({'enabled_eax':enabled},{k:True for k in ('enabled','wallhack_setter','bot_start','activation_return')},child)

class MonsterStoneTests(unittest.TestCase):
 def test_boss_priority_does_not_read_second_radio_even_when_both_true(self):
  p=plan_ms_settings(settings());self.assertTrue(p.complete)
  self.assertEqual(p.stores,((0x56216c,4,0),(0x562170,1,1)))
  self.assertFalse(any(c[2]=='all_mobs' for c in p.calls))

 def test_neither_radio_preserves_prior_mode_without_inventing_zero(self):
  p=plan_ms_settings(settings(0,0),previous_mode=0xffffffff)
  self.assertTrue(p.complete);self.assertEqual(p.mode_after,0xffffffff)
  self.assertEqual(p.stores,((0x562170,1,1),))
  self.assertIsNone(plan_ms_settings(settings(0,0)).mode_after)

 def test_checked_conditions_consume_AL_and_alarm_is_rawBYTE(self):
  p=plan_ms_settings(settings(0x100,0x101,0x12ff));self.assertTrue(p.complete)
  self.assertEqual(p.stores,((0x56216c,4,1),(0x562170,1,255)))

 def test_settings_prefix_and_mode_store_retained_across_alarm_gap(self):
  f=MSFrame();o=settings();r=dict(o.normal_returns);r['alarm']=False
  p=f.advance(replace(o,normal_returns=r));self.assertFalse(p.complete)
  self.assertEqual(p.stores,((0x56216c,4,0),))
  p=f.advance(MSObservation({'boss_eax':0,'all_mobs_eax':1,'alarm_eax':0},{'alarm':True,'settings_return':True}))
  self.assertTrue(p.complete);self.assertEqual(p.stores,((0x56216c,4,0),(0x562170,1,0)))

 def test_panel_compile_uses_real_paths_and_does_not_consume_unreached_radio(self):
  p=compile_ms_settings({MS_SETTING_INPUTS[0]:True,MS_SETTING_INPUTS[1]:object(),MS_SETTING_INPUTS[2]:False})
  self.assertTrue(p.complete);self.assertEqual(p.stores[-1],(0x562170,1,0))
  p=compile_ms_settings(dict(zip(MS_SETTING_INPUTS,(False,True,True))))
  self.assertEqual(p.mode_after,1)

 def test_enable_setter_precedes_flag_then_start_and_physical_push_order(self):
  o=activation();r=dict(o.normal_returns);r['wallhack_setter']=False
  p=plan_ms_activation(replace(o,normal_returns=r));self.assertFalse(p.complete)
  self.assertEqual(p.stores,());self.assertEqual(p.ui_updates,())
  r['wallhack_setter']=True;r['bot_start']=False
  p=plan_ms_activation(replace(o,normal_returns=r));self.assertFalse(p.complete)
  self.assertEqual(p.stores,((0x561f5c,4,1),));self.assertEqual(p.ui_updates,((WALLHACK_INPUT,True),))
  self.assertEqual(p.calls[-1],('0040ae0c',(1,0x561f34),'bot_start'))

 def test_uncheck_only_clears_MS_flag_and_does_not_stop_or_uncheck_wallhack(self):
  o=MSObservation({'enabled_eax':0x100},{'enabled':True,'activation_return':True},BotSwitchObservation())
  f=MSFrame(activation=True);p=f.advance(o);self.assertTrue(p.complete)
  self.assertEqual(p.stores,((0x561f5c,4,0),));self.assertEqual(p.ui_updates,())
  self.assertIsNone(f.child);self.assertFalse(any(c[0]=='0040ae0c' for c in p.calls))

 def test_typed_bot_start_gap_cannot_be_bypassed_by_parent_normal(self):
  p=plan_ms_activation(activation(child=BotSwitchObservation()))
  self.assertFalse(p.complete);self.assertEqual(p.needed,('child','bot_start'))
  self.assertEqual(p.stores,((0x561f5c,4,1),));self.assertFalse(p.bot_start.complete)

 def test_generated_child_retained_while_outer_start_return_is_missing(self):
  f=MSFrame(activation=True);o=activation(child=start(5));r=dict(o.normal_returns);r['bot_start']=False
  p=f.advance(replace(o,normal_returns=r));self.assertFalse(p.complete);self.assertTrue(p.bot_start.complete)
  self.assertEqual(p.bot_start.push_order,(1,0x561f34))
  p=f.advance(MSObservation(normal_returns={'bot_start':True,'activation_return':True}))
  self.assertTrue(p.complete);self.assertTrue(p.bot_start.complete);self.assertFalse(p.MonsterStone_effect_verified)
  self.assertIs(f.advance(MSObservation()),p)

if __name__=='__main__':unittest.main()
