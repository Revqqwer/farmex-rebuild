import json,unittest
from protection_panel_trial import *

class OwnUTF8Codec:
    def __init__(self,codepage):self.codepage=codepage
    def encode(self,text):return text.encode('utf-8'),False

def fixture():
    values={};route_texts={}
    for slot,path in PROTECTION_FIELDS:
        if KINDS[slot]=='checked':values[path]=False
        elif KINDS[slot]=='number':values[path]='10'
        else:values[path]=0;route_texts[path]='Örnek.R'
    reader=lambda:(values,{})
    route_reader=lambda:(route_texts,1254)
    trial=ProtectionSettingsTrial(reader,route_reader)
    data=json.loads(example_protection_sample(trial.current_snapshot(),OwnUTF8Codec))
    return values,route_texts,trial,data

PATHS=dict(PROTECTION_FIELDS)
class ProtectionPanelTrialTests(unittest.TestCase):
    def test_empty_sample_does_not_initialize_shadow_fields(self):
        _,_,trial,_=fixture();p=trial.step('{}')
        self.assertEqual(p.needed,('entry','0046b928'));self.assertEqual(trial.scalar_state,{})
    def test_fifty_controls_and_actual_route_text_not_index(self):
        values,routes,trial,data=fixture();values[PATHS[0x748]]=True
        data=json.loads(example_protection_sample(trial.current_snapshot(),OwnUTF8Codec));p=trial.step(json.dumps(data))
        self.assertTrue(p.complete);self.assertEqual(trial.scalar_state[0x569100],(1,1))
        self.assertEqual(trial.scalar_state[0x569104],(4,10))
        self.assertEqual(trial.string_state[0x56911c],'Örnek.R'.encode('utf-8'))
        self.assertEqual(trial.frame.observation.texts['760'],'Örnek.R')
        self.assertEqual(len(PROTECTION_INPUTS),50)
    def test_no_radio_match_retains_known_previous_shadow_value(self):
        values,_,trial,_=fixture();values[PATHS[0x770]]=True
        trial.step(example_protection_sample(trial.current_snapshot(),OwnUTF8Codec))
        self.assertEqual(trial.scalar_state[0x569108],(4,2))
        values[PATHS[0x770]]=False
        p=trial.step(example_protection_sample(trial.current_snapshot(),OwnUTF8Codec))
        self.assertIn(0x10,p.unchanged_enum_offsets)
        self.assertEqual(trial.scalar_state[0x569108],(4,2))
    def test_numeric_child_and_parent_cleanup_gap_preserve_partial_shadow(self):
        _,_,trial,data=fixture();del data['integer_children']['74c']['cleanup_returned']
        p=trial.step(json.dumps(data));self.assertEqual(p.needed,('child','74c'))
        self.assertNotIn(0x569104,trial.scalar_state)
        data['integer_children']['74c']['cleanup_returned']=True;data['normal_returns']['text_cleanup_74c']=False
        p=trial.step(json.dumps(data));self.assertEqual(p.needed,('normal','text_cleanup_74c'))
        self.assertEqual(trial.scalar_state[0x569104],(4,10))
        data['normal_returns']['text_cleanup_74c']=True
        self.assertTrue(trial.step(json.dumps(data)).complete)
    def test_string_gap_retains_assignment_and_final_step_does_not_reapply(self):
        _,_,trial,data=fixture();data['normal_returns']['ansi_cleanup_760']=False
        p=trial.step(json.dumps(data));self.assertFalse(p.complete)
        self.assertEqual(trial.string_state[0x56911c],'Örnek.R'.encode('utf-8'))
        data['ansi_hex']['760']='ff';data['normal_returns']['ansi_cleanup_760']=True
        p=trial.step(json.dumps(data));self.assertTrue(p.complete)
        self.assertEqual(trial.string_state[0x56911c],'Örnek.R'.encode('utf-8'))
        old=dict(trial.scalar_state);self.assertIs(trial.step('{}'),p)
        self.assertEqual(trial.scalar_state,old)
    def test_panel_and_route_text_changes_reject_stale_example(self):
        values,routes,trial,data=fixture();trial.step(json.dumps(data));old=dict(trial.scalar_state)
        values[PATHS[0x748]]=True
        with self.assertRaises(ValueError):trial.step(json.dumps(data))
        self.assertIsNone(trial.last);self.assertEqual(trial.scalar_state,old)
        data=json.loads(example_protection_sample(trial.current_snapshot(),OwnUTF8Codec))
        trial.step(json.dumps(data));routes[PATHS[0x760]]='Yeni.R'
        with self.assertRaises(ValueError):trial.step(json.dumps(data))
    def test_panel_getters_cannot_be_overridden_but_unreached_values_ignored(self):
        _,_,trial,data=fixture();data['values']={'checked_b28':1}
        with self.assertRaises(ValueError):trial.step(json.dumps(data))
        self.assertIsNone(trial.last)
    def test_local_example_does_not_infer_native_fallback_for_unsupported_text(self):
        values,_,trial,data=fixture();values[PATHS[0x74c]]='$ff'
        with self.assertRaises(ValueError):example_protection_sample(trial.current_snapshot(),OwnUTF8Codec)
        # A manually supplied, explicit native catch landing still works.
        data.pop('panel_snapshot_sha256');data['integer_children']['74c']={
            'text_copy_returned':True,'route':'catch_landing','catch_landing_returned':True,'cleanup_returned':True}
        p=trial.step(json.dumps(data));self.assertTrue(p.complete)
        self.assertEqual(trial.scalar_state[0x569104],(4,80))
    def test_bad_input_clears_last_and_reset_clears_only_shadow(self):
        values,_,trial,data=fixture();trial.step(json.dumps(data))
        for text in ('{bad','[]'):
            with self.assertRaises(ValueError):trial.step(text)
            self.assertIsNone(trial.last)
        trial.reset();self.assertEqual(trial.scalar_state,{});self.assertEqual(trial.string_state,{})
        self.assertEqual(values[PATHS[0x74c]],'10')
    def test_invalid_late_capture_keeps_valid_new_prefix_in_shadow(self):
        values,_,trial,_=fixture();values[PATHS[0x748]]=True
        trial.step(example_protection_sample(trial.current_snapshot(),OwnUTF8Codec))
        self.assertEqual(trial.scalar_state[0x569100],(1,1))
        values[PATHS[0x748]]=False
        data=json.loads(example_protection_sample(trial.current_snapshot(),OwnUTF8Codec));data['ansi_hex']['760']='xx'
        with self.assertRaises(ValueError):trial.step(json.dumps(data))
        self.assertIsNone(trial.last)
        self.assertEqual(trial.scalar_state[0x569100],(1,0))

if __name__=='__main__':unittest.main()
