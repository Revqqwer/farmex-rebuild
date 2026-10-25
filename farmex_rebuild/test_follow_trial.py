import json,unittest
from follow_trial import *
from follow_engine import ROOT

class FollowTrialTests(unittest.TestCase):
    def trial(self,leader=False,name='Alice',enabled=True):
        values={ROOT+'chFollow':enabled,ROOT+'rdFollowPartyLeader':leader,ROOT+'txtFollowNick':name}
        return FollowTrial(lambda:(values,{})),values
    def test_empty_default_does_not_infer_entry_or_helpers(self):
        t,_=self.trial();p=t.step('{}')
        self.assertFalse(p.complete);self.assertIn('earlier caller',p.missing);self.assertIsNone(p.movement)
    def test_disabled_and_leader_party_zero_ignore_unreached_bad_fields(self):
        t,_=self.trial(enabled=False)
        self.assertEqual(t.step(json.dumps(dict(entry_reached=True,helper_returns=99,coordinate_bits='bad'))).status,'disabled')
        t,_=self.trial(leader=True);r=json.loads(example_follow_sample());r.update(party_count_dword=0,coordinate_bits=['bad'])
        self.assertEqual(t.step(json.dumps(r)).status,'no_positive_party_count')
    def test_leader_and_manual_use_distinct_y_and_fresh_panel_mode(self):
        t,v=self.trial(leader=True);sample=example_follow_sample()
        self.assertEqual(t.step(sample).movement,(0x41200000,0x41a00000))
        v[ROOT+'rdFollowPartyLeader']=False
        self.assertEqual(t.step(sample).movement,(0x41200000,0x41c00000))
    def test_manual_empty_name_skips_bad_previous_comparison(self):
        t,_=self.trial(name='');r=json.loads(example_follow_sample());r['previous_equal']='bad'
        self.assertEqual(t.step(json.dumps(r)).status,'empty_name')
    def test_cached_lookup_skipped_then_new_name_clears_before_return_gap(self):
        t,v=self.trial();r=json.loads(example_follow_sample());t.step(json.dumps(r))
        r['helper_returns']['name_lookup']=False;r['name_id_dword']='unused'
        self.assertTrue(t.step(json.dumps(r)).complete)
        v[ROOT+'txtFollowNick']='Bob';p=t.step(json.dumps(r))
        self.assertFalse(p.complete);self.assertEqual(t.state.previous_name,'Bob');self.assertEqual(t.state.cached_id_dword,0)
    def test_coordinate_prefix_only_consumes_reached_element(self):
        t,_=self.trial(leader=True);r=json.loads(example_follow_sample())
        r['helper_returns']['coord_x']=False;r['coordinate_offsets'][1]='unused';r['coordinate_bits']=['unused']
        p=t.step(json.dumps(r));self.assertFalse(p.complete);self.assertIn('coord_x normal',p.missing)
        r['helper_returns']['coord_x']=True
        with self.assertRaises(ValueError):t.step(json.dumps(r))
    def test_missing_move_return_keeps_intent_without_success(self):
        t,_=self.trial();r=json.loads(example_follow_sample());del r['helper_returns']['movement']
        p=t.step(json.dumps(r));self.assertFalse(p.complete);self.assertIsNotNone(p.movement);self.assertFalse(p.native_execution_verified)
    def test_invalid_sample_clears_stale_last_but_does_not_reset_cache(self):
        t,_=self.trial();t.step(example_follow_sample());state=t.state
        with self.assertRaises(ValueError):t.step('{bad')
        self.assertIsNone(t.last);self.assertEqual(t.state,state)
    def test_owned_comparison_does_not_invent_normal_return(self):
        t,_=self.trial();r=json.loads(example_follow_sample());del r['empty_equal']['helper_returned']
        p=t.step(json.dumps(r));self.assertFalse(p.complete);self.assertIn('UStrEqual normal',p.missing)
        self.assertEqual(t.state.initialized_byte,1)
    def test_missing_reader_has_no_demo_fallback_and_reset_clears_state(self):
        with self.assertRaises(ValueError):FollowTrial(None).step(example_follow_sample())
        t,_=self.trial();t.step(example_follow_sample());t.reset()
        self.assertEqual(t.state,FollowState());self.assertIsNone(t.last)

if __name__=='__main__':unittest.main()
