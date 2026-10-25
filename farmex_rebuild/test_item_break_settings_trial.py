import json,unittest
from item_break_settings_trial import *

PATHS=dict(ITEM_BREAK_FIELDS)
def fixture():
    values={PATHS[0xec0]:True,PATHS[0xec8]:'1',PATHS[0xa28]:True}
    trial=ItemBreakSettingsTrial(lambda:(values,{}))
    return values,trial,json.loads(example_item_break_settings_sample(trial.current_snapshot()))

class ItemBreakSettingsTrialTests(unittest.TestCase):
    def test_three_inputs_use_source_context_and_ignore_unrelated_hp(self):
        values,trial,data=fixture();values['hp']='invalid'
        plan=trial.step(json.dumps(data));self.assertTrue(plan.complete)
        self.assertEqual(plan.stores,((0x569a20,1,1),(0x569a24,4,1),(0x569a2c,4,0)))
        self.assertEqual(plan.toggle_argument,1);self.assertEqual(len(ITEM_BREAK_SETTING_INPUTS),3)

    def test_snapshot_change_requires_new_example(self):
        values,trial,data=fixture();values[PATHS[0xec8]]='-1'
        with self.assertRaises(ValueError):trial.step(json.dumps(data))
        trial.step(example_item_break_settings_sample(trial.current_snapshot()))
        self.assertEqual(trial.scalar_state[0x569a24],(4,0xffffffff))

    def test_outer_and_cleanup_gaps_keep_prefix_before_radio_read(self):
        _,trial,data=fixture();data['normal_returns']['parser_outer_ec8']=False
        plan=trial.step(json.dumps(data));self.assertEqual(plan.needed,('settings',('normal','parser_outer_ec8')))
        self.assertEqual(len(trial.scalar_state),1)
        data['normal_returns']['parser_outer_ec8']=True;data['normal_returns']['text_cleanup_ec8']=False
        plan=trial.step(json.dumps(data));self.assertEqual(len(trial.scalar_state),2)
        data['normal_returns']['text_cleanup_ec8']=True;data['normal_returns']['reset_checked_a28']=False
        plan=trial.step(json.dumps(data));self.assertEqual(plan.needed,'reset_checked_returned')

    def test_toggle_gap_keeps_reset_store_and_applies_once(self):
        _,trial,data=fixture();data['normal_returns']['toggle']=False
        plan=trial.step(json.dumps(data));self.assertEqual(plan.needed,'toggle_returned')
        self.assertEqual(trial.scalar_state[0x569a2c],(4,0))
        data['normal_returns']['toggle']=True;plan=trial.step(json.dumps(data));before=dict(trial.scalar_state)
        self.assertIs(trial.step(json.dumps(data)),plan);self.assertEqual(trial.scalar_state,before)

    def test_panel_flags_and_own_fresh_read_cannot_be_overridden(self):
        for key,value in (('checked_ec0',0),('checked_a28',0),('fresh_enabled_byte',0)):
            _,trial,data=fixture();data['values']={key:value}
            with self.assertRaises(ValueError):trial.step(json.dumps(data))
            self.assertIsNone(trial.last)

    def test_unchecked_radio_does_not_clear_previous_mode_shadow(self):
        values,trial,data=fixture();trial.scalar_state[0x569a2c]=(4,0x12345678)
        values[PATHS[0xa28]]=False;values[PATHS[0xec0]]=False
        plan=trial.step(example_item_break_settings_sample(trial.current_snapshot()))
        self.assertTrue(plan.complete);self.assertEqual(plan.toggle_argument,0)
        self.assertEqual(trial.scalar_state[0x569a2c],(4,0x12345678))
        self.assertEqual(len(plan.stores),2)

    def test_invalid_late_numeric_capture_keeps_accepted_enable_store(self):
        _,trial,data=fixture();data['integer_children']['ec8']['parser_qword']='bad'
        with self.assertRaises(ValueError):trial.step(json.dumps(data))
        self.assertEqual(trial.scalar_state,{0x569a20:(1,1)})

    def test_explicit_catch_default_one_without_synthetic_lexical_guess(self):
        values,trial,data=fixture();values[PATHS[0xec8]]='invalid'
        with self.assertRaises(ValueError):example_item_break_settings_sample(trial.current_snapshot())
        data.pop('panel_snapshot_sha256');data['integer_children']['ec8']=dict(text_copy_returned=True,
            route='catch_landing',catch_landing_returned=True,cleanup_returned=True)
        self.assertTrue(trial.step(json.dumps(data)).complete)
        self.assertEqual(trial.scalar_state[0x569a24],(4,1))

    def test_reset_and_snapshot_type_validation(self):
        values,trial,data=fixture();trial.step(json.dumps(data));trial.reset()
        self.assertEqual(trial.scalar_state,{});self.assertIsNone(trial.frame)
        values[PATHS[0xa28]]=1
        with self.assertRaises(ValueError):trial.current_snapshot()

if __name__=='__main__':unittest.main()
