import unittest
from dataclasses import replace
from party_invitation import *

def packet(name=b'Alice',inviter=65535):return b'\x2f\x02'+inviter.to_bytes(2,'little')+len(name).to_bytes(2,'little')+name
def config(**kw):return replace(PartyInviteConfiguration(1,1,1,0,(b'Alice',)),**kw)
def observation(**kw):return replace(PartyInviteObservation(0,0,True,helper_returns={k:True for k in
    ('party_state','read_inviter','read_name_length','read_name','name_filter','accept','reject','name_cleanup')}),**kw)

class InvitationTests(unittest.TestCase):
    def test_panel_flags_leader_only_choice_and_rows_ignore_checked(self):
        v={PARTY_INVITE_INPUTS[0]:True,PARTY_INVITE_INPUTS[1]:False,PARTY_INVITE_INPUTS[2]:True,PARTY_INVITE_INPUTS[3]:True}
        v[ROOT+'rdListPartyAccept']=False
        rows=[{'caption':'Alice\0suffix','checked':False},{'caption':'Şule','checked':False}]
        c=compile_party_invitation(v,{PARTY_LIST:rows},WindowsNameCodec(1254))
        self.assertEqual((c.enabled_byte,c.list_only_byte,c.reject_unlisted_byte,c.party_bug_byte),(1,1,1,1))
        self.assertEqual(c.names,(b'Alice','Şule'.encode('cp1254')))
    def test_lossy_name_and_unknown_rows_not_silently_empty(self):
        v={p:True for p in PARTY_INVITE_INPUTS[:4]}
        with self.assertRaises(ValueError):compile_party_invitation(v,{PARTY_LIST:[{'caption':'\U0001f600'}]},WindowsNameCodec(1254))
        with self.assertRaises(ValueError):compile_party_invitation(v,{},WindowsNameCodec(1254))
    def test_other_opcode_and_subtype_do_not_consume_later_gates(self):
        p=plan_party_invitation(config(),b'\x01',PartyInviteObservation())
        self.assertTrue(p.complete);self.assertIsNone(p.handler_return_dword)
        p=plan_party_invitation(config(),b'\x2f\x03',PartyInviteObservation())
        self.assertEqual(p.handler_return_dword,1);self.assertEqual(p.calls,())
    def test_early_block_exact_party_state_one_and_disabled_skip_parse(self):
        for c,o,status in ((config(),observation(blocked_byte_56228d=2),'blocked'),
            (config(),observation(party_state_eax=0xabcd0001),'party_state_one'),
            (config(enabled_byte=0),observation(party_state_eax=2),'auto_accept_disabled')):
            p=plan_party_invitation(c,b'\x2f\x02',o)
            self.assertTrue(p.complete);self.assertEqual(p.status,status);self.assertIsNone(p.inviter_word)
    def test_matching_accept_and_suppression_change_return_not_action(self):
        for suppress,returned in ((0,1),(1,0),(2,0)):
            p=plan_party_invitation(config(party_bug_byte=suppress),packet(),observation())
            self.assertTrue(p.complete);self.assertEqual(p.action,'accept');self.assertEqual(p.handler_return_dword,returned)
            self.assertEqual(p.inviter_word,65535);self.assertEqual(p.name_bytes,b'Alice')
            self.assertFalse(p.native_execution_verified)
    def test_accept_all_still_requires_filter_and_ignores_nonmatch(self):
        c=config(list_only_byte=0,names=())
        o=observation(helper_returns={**observation().helper_returns,'name_filter':False})
        p=plan_party_invitation(c,packet(),o);self.assertFalse(p.complete);self.assertIsNone(p.action)
        p=plan_party_invitation(c,packet(),observation());self.assertTrue(p.complete);self.assertFalse(p.matched);self.assertEqual(p.action,'accept')
    def test_unmatched_reject_or_unchanged_and_case_sensitive_names(self):
        p=plan_party_invitation(config(),packet(b'alice'),observation())
        self.assertEqual(p.action,'reject');self.assertEqual(p.handler_return_dword,0)
        p=plan_party_invitation(config(reject_unlisted_byte=0),packet(b'Bob'),observation())
        self.assertEqual(p.status,'unlisted_unchanged');self.assertIsNone(p.action);self.assertEqual(p.handler_return_dword,1)
    def test_declared_length_bounds_and_embedded_nul_constructor(self):
        for n in (0,1,2,3,4,5,6,10):
            p=plan_party_invitation(config(),packet()[:n],observation())
            self.assertFalse(p.complete);self.assertIsNone(p.handler_return_dword)
        p=plan_party_invitation(config(),packet(b'Alice\0Bob')+b'trailing',observation())
        self.assertTrue(p.complete);self.assertEqual(p.name_bytes,b'Alice');self.assertTrue(p.matched)
        p=plan_party_invitation(config(names=(b'',)),packet(b''),observation())
        self.assertTrue(p.complete);self.assertTrue(p.matched)
    def test_each_normal_return_gap_does_not_invent_completed_handler(self):
        for key in observation().helper_returns:
            if key=='reject':continue
            p=plan_party_invitation(config(),packet(),observation(helper_returns={**observation().helper_returns,key:False}))
            self.assertFalse(p.complete);self.assertIsNone(p.handler_return_dword)
        p=plan_party_invitation(config(),packet(b'Bob'),observation(helper_returns={**observation().helper_returns,'reject':False}))
        self.assertFalse(p.complete);self.assertEqual(p.action,'reject')
    def test_own_filter_and_raw_result_conflict_only_when_reached(self):
        with self.assertRaises(ValueError):plan_party_invitation(config(),packet(),observation(filter_eax=1))
        p=plan_party_invitation(config(enabled_byte=0),b'\x2f\x02',observation(filter_eax=1))
        self.assertTrue(p.complete)
        p=plan_party_invitation(config(names=None),packet(),observation(use_owned_filter=False,filter_eax=1))
        self.assertTrue(p.complete);self.assertEqual(p.action,'accept')
    def test_missing_flag_or_filter_value_stays_unknown(self):
        p=plan_party_invitation(config(),packet(),PartyInviteObservation())
        self.assertFalse(p.complete);self.assertIn('0056228d',p.missing)
        p=plan_party_invitation(config(names=None),packet(),observation())
        self.assertFalse(p.complete);self.assertIn('stable name vector',p.missing)
        p=plan_party_invitation(config(),packet(),observation(use_owned_filter=False))
        self.assertFalse(p.complete);self.assertIn('filter EAX',p.missing)

if __name__=='__main__':unittest.main()
