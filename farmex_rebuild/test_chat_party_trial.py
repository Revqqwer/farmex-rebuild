import json
import unittest
from chat_party_trial import *
from chat_party_invite import CHAT_PARTY_INPUTS, PARTY_LIST

class ChatPartyTrialTests(unittest.TestCase):
    def trial(self):
        values = dict(zip(CHAT_PARTY_INPUTS,(True,'add',True)))
        lists = {PARTY_LIST:[{'caption':'Alice','checked':False}]}
        return ChatPartyTrial(lambda:(values,lists)), values, lists

    def test_defaults_wait_without_actor_or_queue_fabrication(self):
        t,_,_=self.trial()
        self.assertFalse(t.step('10','{}',1254).complete)
        p=t.step(EXAMPLE_CHAT_HEX,'{}',1254)
        self.assertFalse(p.complete);self.assertEqual(p.missing,'command_compare normal return')
        self.assertEqual(t.frame.queue.records,());self.assertIsNone(t.frame.emission)

    def test_explicit_example_and_repeated_ticks_do_not_reenqueue(self):
        t,_,_=self.trial();p=t.step(EXAMPLE_CHAT_HEX,example_chat_party_sample(),1254)
        self.assertTrue(p.complete);self.assertEqual(len(t.frame.queue.records),2)
        frame=t.frame
        self.assertIs(t.step(EXAMPLE_CHAT_HEX,'{}',1254),p)
        self.assertIs(t.frame,frame);self.assertEqual(len(frame.queue.records),2)

    def test_same_snapshot_resumes_queue_clock_and_outer_return_gaps(self):
        t,_,_=self.trial();raw=json.loads(example_chat_party_sample())
        del raw['queue_samples']['2'];del raw['helper_returns']['invite']
        p=t.step(EXAMPLE_CHAT_HEX,json.dumps(raw),1254)
        self.assertFalse(p.complete);self.assertEqual(len(t.frame.queue.records),1)
        p=t.step(EXAMPLE_CHAT_HEX,json.dumps(dict(queue_samples={'2':{'gate':1,'tick':200}},enqueue_returns={'2':True},cleanup_returned=True)),1254)
        self.assertEqual(p.missing,'invite normal return')
        self.assertEqual([r.created_tick for r in t.frame.queue.records],[100,200])
        self.assertTrue(t.step(EXAMPLE_CHAT_HEX,'{"helper_returns":{"invite":true}}',1254).complete)

    def test_unvisited_invalid_json_fields_are_not_evaluated(self):
        t,values,_=self.trial();values[CHAT_PARTY_INPUTS[0]]=False
        raw=dict(actor_dword='bad',helper_returns='unused',queue_samples='unused',cleanup_returned='unused')
        self.assertEqual(t.step(EXAMPLE_CHAT_HEX,json.dumps(raw),1254).status,'disabled')
        values[CHAT_PARTY_INPUTS[0]]=True;values[CHAT_PARTY_INPUTS[1]]='other'
        raw['helper_returns']={'command_compare':True,'actor':'unused'}
        self.assertEqual(t.step(EXAMPLE_CHAT_HEX,json.dumps(raw),1254).status,'command_mismatch')

    def test_consumed_gate_is_not_reparsed_and_zero_gate_needs_no_tick(self):
        t,_,_=self.trial();raw=json.loads(example_chat_party_sample());del raw['queue_samples']['1']['tick']
        p=t.step(EXAMPLE_CHAT_HEX,json.dumps(raw),1254)
        self.assertIn('GetTickCount',p.missing)
        raw['queue_samples']['1']={'gate':'already consumed','tick':100}
        raw['queue_samples']['2']={'gate':0,'tick':'unvisited'}
        self.assertTrue(t.step(EXAMPLE_CHAT_HEX,json.dumps(raw),1254).complete)
        self.assertEqual(len(t.frame.queue.records),1)

    def test_panel_text_flags_names_and_codepage_are_fresh_new_invocations(self):
        t,v,lists=self.trial();sample=example_chat_party_sample()
        self.assertTrue(t.step(EXAMPLE_CHAT_HEX,sample,1254).complete)
        old=t.frame;v[CHAT_PARTY_INPUTS[1]]='ADD'
        self.assertEqual(t.step(EXAMPLE_CHAT_HEX,sample,1254).status,'command_mismatch');self.assertIsNot(t.frame,old)
        v[CHAT_PARTY_INPUTS[1]]='add';lists[PARTY_LIST]=[]
        self.assertEqual(t.step(EXAMPLE_CHAT_HEX,sample,1254).status,'unlisted')
        v[CHAT_PARTY_INPUTS[2]]=False
        self.assertEqual(t.step(EXAMPLE_CHAT_HEX,sample,65001).action,'invite')
        self.assertEqual(t.configuration.codepage,65001)

    def test_bad_reached_fields_clear_frame_and_stale_queue(self):
        for change in ('{bad','[]','{"helper_returns":{"command_compare":"bad"}}'):
            t,_,_=self.trial();t.step(EXAMPLE_CHAT_HEX,example_chat_party_sample(),1254)
            # A completed invocation ignores unvisited data; reset opens a new one.
            t.reset()
            with self.assertRaises((ValueError,TypeError)):t.step(EXAMPLE_CHAT_HEX,change,1254)
            self.assertIsNone(t.last);self.assertIsNone(t.frame);self.assertIsNone(t.captured)
        t,_,_=self.trial();t.step(EXAMPLE_CHAT_HEX,example_chat_party_sample(),1254)
        with self.assertRaises(ValueError):t.step('not hex','{}',1254)
        self.assertIsNone(t.frame);self.assertIsNone(t.last)

    def test_reached_invalid_second_enqueue_and_helper_receipts_are_rejected(self):
        for field,value in (('queue_samples',{'2':'bad','1':{'gate':0}}),('enqueue_returns',{'1':'bad'}),('cleanup_returned','bad')):
            t,_,_=self.trial();raw=json.loads(example_chat_party_sample());raw[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):t.step(EXAMPLE_CHAT_HEX,json.dumps(raw),1254)
            self.assertIsNone(t.last);self.assertIsNone(t.frame)

    def test_other_opcode_reset_and_missing_reader(self):
        t,_,_=self.trial()
        self.assertEqual(t.step('2f','{}',1254).status,'other_opcode')
        self.assertIsNone(t.frame)
        t.step(EXAMPLE_CHAT_HEX,example_chat_party_sample(),1254);t.reset()
        self.assertIsNone(t.frame);self.assertIsNone(t.configuration)
        with self.assertRaises(ValueError):ChatPartyTrial(None).step('10','{}',1254)

if __name__ == '__main__':unittest.main()
