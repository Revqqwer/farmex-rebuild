import unittest
from dataclasses import replace
from party_replies import *
from party_invitation import PartyInviteConfiguration,PartyInviteObservation,plan_party_invitation
from party_invitation_frame import PartyInvitationFrame

CAPTURE=b'\x2f\x02\xff\xff\x05\x00Alice'
def config(**kw):return replace(PartyInviteConfiguration(1,1,1,0,(b'Alice',)),**kw)
def samples(**kw):return replace(PartyInviteObservation(0,0,True,helper_returns={k:True for k in
    ('party_state','read_inviter','read_name_length','read_name','name_filter','accept','reject','name_cleanup')}),**kw)

class PartyReplyTests(unittest.TestCase):
    def test_exact_three_byte_reply_no_inviter_or_name_added(self):
        for kind,payload in (('accept',b'\x2f\x02\x01'),('reject',b'\x2f\x02\x00')):
            f=PartyReplyFrame(kind);p=f.advance(1,123)
            self.assertTrue(p.complete);self.assertEqual(p.payload,payload)
            self.assertEqual(f.queue.records[0].payload,payload);self.assertEqual(f.queue.records[0].delay_dword,0)
            self.assertFalse(p.native_execution_verified)
    def test_queue_gate_tick_gaps_and_cached_single_record(self):
        f=PartyReplyFrame('accept')
        self.assertFalse(f.advance().complete);self.assertFalse(f.advance(1).complete)
        p=f.advance(1,123);self.assertEqual(len(f.queue.records),1)
        self.assertIs(f.advance(0,None),p);self.assertEqual(len(f.queue.records),1)
    def test_gate_zero_known_skip_is_not_retried(self):
        f=PartyReplyFrame('reject');p=f.advance(0)
        self.assertTrue(p.complete);self.assertEqual(p.queue_decision.status,'not_enqueued')
        f.advance(1,123);self.assertEqual(f.queue.records,())
    def test_bound_reply_cannot_claim_wrong_payload_or_unknown_queue_complete(self):
        with self.assertRaises(ValueError):PartyReplyPlan(False,'accept',b'wrong')
        with self.assertRaises(ValueError):PartyReplyPlan(True,'accept',b'\x2f\x02\x01')
    def test_parent_kind_match_and_outer_return_remain_separate(self):
        reply=PartyReplyFrame('accept').advance(1,123)
        p=plan_party_invitation(config(),CAPTURE,samples(reply_execution=reply,helper_returns={**samples().helper_returns,'accept':False}))
        self.assertFalse(p.complete);self.assertIn('accept normal return',p.missing)
        with self.assertRaises(ValueError):plan_party_invitation(config(),CAPTURE,samples(reply_execution=PartyReplyFrame('reject').advance(1,123)))
        p=plan_party_invitation(config(enabled_byte=0),CAPTURE,samples(reply_execution=PartyReplyFrame('reject').advance()))
        self.assertTrue(p.complete);self.assertIsNone(p.action)
    def test_incomplete_child_cannot_be_bypassed_by_parent_normal_receipt(self):
        reply=PartyReplyFrame('accept').advance()
        p=plan_party_invitation(config(),CAPTURE,samples(reply_execution=reply))
        self.assertFalse(p.complete);self.assertIn('bound party reply',p.missing)
        self.assertIsNone(p.handler_return_dword)

class InvitationFrameTests(unittest.TestCase):
    def test_only_reached_action_creates_queue_and_reject_is_distinct(self):
        f=PartyInvitationFrame(config(enabled_byte=0),CAPTURE)
        self.assertTrue(f.advance(samples()).complete);self.assertIsNone(f.reply_frame)
        f=PartyInvitationFrame(config(names=()),CAPTURE)
        p=f.advance(samples(),reply_gate=1,reply_tick=123)
        self.assertTrue(p.complete);self.assertEqual(p.action,'reject')
        self.assertEqual(f.queue.records[0].payload,b'\x2f\x02\x00')
    def test_source_prefix_frozen_when_reply_gate_missing(self):
        f=PartyInvitationFrame(config(),CAPTURE)
        p=f.advance(samples());self.assertFalse(p.complete);self.assertEqual(f.queue.records,())
        p=f.advance(PartyInviteObservation(helper_returns={'accept':True,'name_cleanup':True}),reply_gate=1,reply_tick=123)
        self.assertTrue(p.complete);self.assertEqual(p.inviter_word,65535);self.assertEqual(len(f.queue.records),1)
    def test_missing_outer_return_then_cleanup_does_not_duplicate_reply(self):
        f=PartyInvitationFrame(config(),CAPTURE)
        p=f.advance(samples(helper_returns={**samples().helper_returns,'accept':False}),reply_gate=1,reply_tick=123)
        self.assertFalse(p.complete);self.assertEqual(len(f.queue.records),1)
        p=f.advance(PartyInviteObservation(helper_returns={'accept':True}))
        self.assertFalse(p.complete);self.assertIn('name_cleanup',p.missing)
        p=f.advance(PartyInviteObservation(helper_returns={'name_cleanup':True}))
        self.assertTrue(p.complete);self.assertEqual(len(f.queue.records),1)
        self.assertIs(f.advance(PartyInviteObservation()),p)
    def test_unfinished_packet_or_filter_never_preemptively_enqueues(self):
        for captured,o in ((CAPTURE[:6],samples()),(CAPTURE,samples(helper_returns={**samples().helper_returns,'name_filter':False}))):
            f=PartyInvitationFrame(config(),captured)
            self.assertFalse(f.advance(o,reply_gate=1,reply_tick=123).complete)
            self.assertEqual(f.queue.records,());self.assertIsNone(f.reply_frame)
    def test_external_reply_conflicts_only_when_owned_frame_reaches_action(self):
        o=samples(reply_execution=PartyReplyFrame('accept').advance(1,123))
        with self.assertRaises(ValueError):PartyInvitationFrame(config(),CAPTURE).advance(o)
        self.assertTrue(PartyInvitationFrame(config(enabled_byte=0),CAPTURE).advance(o).complete)

if __name__=='__main__':unittest.main()
