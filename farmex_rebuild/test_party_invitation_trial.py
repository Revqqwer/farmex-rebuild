import json,unittest
from party_invitation_trial import *
from party_invitation import ROOT,PARTY_LIST

class InvitationTrialTests(unittest.TestCase):
    def trial(self):
        v={ROOT+'chotoparty':True,ROOT+'rdAllPartyAccept':False,ROOT+'chpartyred':True,ROOT+'chDisablePtBug':False}
        lists={PARTY_LIST:[{'caption':'Alice','checked':False}]}
        return PartyInvitationTrial(lambda:(v,lists)),v,lists
    def test_empty_observation_default_remains_unknown(self):
        t,_,_=self.trial();p=t.step('2f02','{}',1254)
        self.assertFalse(p.complete);self.assertIsNone(p.action)
    def test_fresh_panel_all_list_flags_and_rows(self):
        t,v,lists=self.trial();s=example_invitation_sample();hexdata='2f02ffff0300426f62'
        self.assertEqual(t.step(hexdata,s,1254).action,'reject')
        v[ROOT+'rdAllPartyAccept']=True
        self.assertEqual(t.step(hexdata,s,1254).action,'accept')
        v[ROOT+'rdAllPartyAccept']=False;lists[PARTY_LIST].append({'caption':'Bob','checked':False})
        self.assertEqual(t.step(hexdata,s,1254).action,'accept')
    def test_unreached_bad_filter_or_helper_fields_are_ignored(self):
        t,v,_=self.trial();v[ROOT+'chotoparty']=False
        r=json.loads(example_invitation_sample());r['filter_eax']='bad';r['use_owned_filter']='bad'
        self.assertEqual(t.step('2f02',json.dumps(r),1254).status,'auto_accept_disabled')
        self.assertEqual(t.step('2f02',json.dumps({'blocked_byte_56228d':1,'helper_returns':'unused'}),1254).status,'blocked')
    def test_all_accept_does_not_bypass_filter_return(self):
        t,v,_=self.trial();v[ROOT+'rdAllPartyAccept']=True
        r=json.loads(example_invitation_sample());r['helper_returns']['name_filter']=False
        p=t.step('2f02ffff0500416c696365',json.dumps(r),1254)
        self.assertFalse(p.complete);self.assertIsNone(p.action)
    def test_own_filter_conflict_and_missing_cleanup(self):
        t,_,_=self.trial();r=json.loads(example_invitation_sample());r['filter_eax']=1
        with self.assertRaises(ValueError):t.step('2f02ffff0500416c696365',json.dumps(r),1254)
        r.pop('filter_eax');del r['helper_returns']['name_cleanup']
        p=t.step('2f02ffff0500416c696365',json.dumps(r),1254)
        self.assertFalse(p.complete);self.assertEqual(p.action,'accept');self.assertIsNone(p.handler_return_dword)
    def test_bad_new_capture_or_json_clears_stale_success(self):
        t,_,_=self.trial();t.step('2f02ffff0500416c696365',example_invitation_sample(),1254)
        for h,s in (('not hex','{}'),('2f02','{bad')):
            with self.assertRaises(ValueError):t.step(h,s,1254)
            self.assertIsNone(t.last);self.assertIsNone(t.captured)
    def test_bounds_unknown_packet_and_explicit_codec(self):
        t,_,_=self.trial()
        p=t.step('2f02ffff050041',example_invitation_sample(),1254)
        self.assertFalse(p.complete);self.assertIn('bounded name',p.missing)
        self.assertEqual(t.step('01','{}',1254).status,'other_opcode')
        with self.assertRaises(ValueError):t.step('01','{}',0)
    def test_reader_required_and_reset(self):
        with self.assertRaises(ValueError):PartyInvitationTrial(None).step('2f02','{}',1254)
        t,_,_=self.trial();t.step('01','{}',1254);t.reset();self.assertIsNone(t.last)

if __name__=='__main__':unittest.main()
