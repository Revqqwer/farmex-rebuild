import json,unittest
from control_settings_trial import *

PATHS=dict(CONTROL_SETTING_FIELDS)
def fixture():
 values={path:False if op[0]=='flag' else '5' for op,(_,path) in zip(OPS,CONTROL_SETTING_FIELDS)}
 trial=ControlSettingsTrial(lambda:(values,{}))
 return values,trial,json.loads(example_control_settings_sample(trial.current_snapshot()))

class ControlSettingsTrialTests(unittest.TestCase):
 def test_fifteen_inputs_and_no_unrelated_hp_dependency(self):
  values,t,data=fixture();values['unrelated hp']='invalid'
  self.assertEqual(len(CONTROL_SETTING_INPUTS),15)
  p=t.step(json.dumps(data));self.assertTrue(p.complete);self.assertEqual(len(t.scalar_state),16)

 def test_fresh_example_is_bound_to_changed_text(self):
  values,t,data=fixture();values[PATHS[0x8b0]]='4294967297'
  with self.assertRaises(ValueError):t.step(json.dumps(data))
  p=t.step(example_control_settings_sample(t.current_snapshot()))
  self.assertTrue(p.complete);self.assertEqual(describe_control_settings_trial(t)['coin_eşiği'],4294967297)

 def test_negative_coin_is_displayed_signed(self):
  values,t,_=fixture();values[PATHS[0x8b0]]='-1'
  t.step(example_control_settings_sample(t.current_snapshot()))
  self.assertEqual(describe_control_settings_trial(t)['coin_eşiği'],-1)

 def test_parser_catch_is_explicit_and_source_default_54_is_preserved(self):
  values,t,data=fixture();values[PATHS[0x8c8]]='invalid'
  data.pop('panel_snapshot_sha256');data['integer_children']['8c8']={'text_copy_returned':True,'route':'catch_landing','catch_landing_returned':True,'cleanup_returned':True}
  self.assertTrue(t.step(json.dumps(data)).complete)
  self.assertEqual(t.scalar_state[0x562194+0xd4],(4,54))

 def test_disabled_coin_flag_does_not_skip_number_or_outer_return(self):
  _,t,data=fixture();data['normal_returns']['parser_outer_8b0']=False
  p=t.step(json.dumps(data));self.assertEqual(p.needed,('normal','parser_outer_8b0'))
  self.assertEqual(len(t.scalar_state),4)
  data['normal_returns']['parser_outer_8b0']=True;data['normal_returns']['text_cleanup_8b0']=False
  p=t.step(json.dumps(data));self.assertEqual(p.needed,('normal','text_cleanup_8b0'));self.assertEqual(len(t.scalar_state),6)

 def test_bad_later_capture_does_not_retract_accepted_prefix(self):
  _,t,data=fixture();data['integer_children']['8c8']['parser_qword']='bad'
  with self.assertRaises(ValueError):t.step(json.dumps(data))
  self.assertEqual(t.scalar_state[0x562194+0xc8],(4,5));self.assertEqual(len(t.scalar_state),7)
  self.assertIsNone(t.last)

 def test_raw_panel_flag_and_text_cannot_be_overridden(self):
  _,t,data=fixture();data['values']={'checked_8a4':1}
  with self.assertRaises(ValueError):t.step(json.dumps(data))
  _,t,data=fixture();data['texts']={'8b0':'different'}
  with self.assertRaises(ValueError):t.step(json.dumps(data))

 def test_reset_and_widget_value_types(self):
  values,t,data=fixture();t.step(json.dumps(data));t.reset()
  self.assertFalse(t.scalar_state);self.assertIsNone(t.frame)
  values[PATHS[0x8a4]]=1
  with self.assertRaises(ValueError):t.current_snapshot()
  values[PATHS[0x8a4]]=False;values[PATHS[0x8b0]]=12
  with self.assertRaises(ValueError):t.current_snapshot()

 def test_synthetic_example_rejects_unsupported_lexical_form(self):
  values,t,_=fixture();values[PATHS[0x8b0]]='1,000'
  with self.assertRaises(ValueError):example_control_settings_sample(t.current_snapshot())
  self.assertFalse(t.scalar_state)
