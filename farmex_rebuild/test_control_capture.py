import json,unittest
from control_capture import parse_control_sample
from party_help import ROOT

class ControlCaptureTests(unittest.TestCase):
    def test_empty_json_keeps_every_observation_unknown(self):
        p=parse_control_sample('{}')
        self.assertIsNone(p.initial_state);self.assertIsNone(p.party_help.party_count)
        self.assertIsNone(p.alarms.now_tick);self.assertEqual(dict(p.observed_ansi),{})
        self.assertFalse(p.independently_verified)

    def test_exact_ansi_and_fresh_names_have_no_implicit_encoding(self):
        p=parse_control_sample(json.dumps({'observed_ansi_hex':{ROOT+'txtHelpChatSW':'730077'},
            'alarms':{'name_samples':[[14,0,'5465657468206f6620446576696c'],[14,1,'']]}}))
        self.assertEqual(p.observed_ansi[ROOT+'txtHelpChatSW'],b's\0w')
        self.assertEqual(p.alarms.name_samples[(14,1)],b'')
        self.assertNotIn((14,2),p.alarms.name_samples)

    def test_exact_qword_initial_state_and_normalized_keys(self):
        p=parse_control_sample(json.dumps({'initial_state':{'timers':{'0x553cb4':0xffffffffffffffff},'last_activity_qword':0},
            'party_help':{'feature_ticks':{'0x103':0xffffffff},'request_returns':{'259':True},
                'swift_samples':[['0x1000',0x2000]]}}))
        self.assertEqual(p.initial_state.party_help.timers[0x553cb4],0xffffffffffffffff)
        self.assertEqual(p.initial_state.loot_activity.last_activity_qword,0)
        self.assertEqual(p.party_help.feature_ticks[0x103],0xffffffff)
        self.assertEqual(p.party_help.swift_samples,((0x1000,0x2000),))

    def test_duplicate_or_out_of_range_source_samples_rejected(self):
        for payload in ({'alarms':{'name_samples':[[14,0,''],[14,0,'00']]}},
            {'party_help':{'feature_ticks':{'0x103':1,'259':2}}},
            {'initial_state':{'timers':{'0x553cb4':1<<64}}},
            {'alarms':{'name_samples':[[42,0,'']]}}):
            with self.assertRaises(ValueError):parse_control_sample(json.dumps(payload))

    def test_verification_claims_and_unknown_keys_do_not_become_evidence(self):
        for payload in ({'independently_verified':True},{'party_help':{'native_execution_verified':True}},
            {'observed_ansi_hex':{'unknown':'00'}},[]):
            with self.assertRaises(ValueError):parse_control_sample(json.dumps(payload))

if __name__=='__main__':unittest.main()
