import json,unittest
from pathlib import Path
from dataclasses import replace
from profiles import Profiles
from party_help import *

class PartyHelpTests(unittest.TestCase):
    def config(self,*enabled,ansi=True):
        return PartyHelpConfiguration({flag:int(flag in enabled) for flag,_,_,_ in ROWS},
            {text:'text' for _,text,_,_ in ROWS},{text:('text%x'%text).encode('ascii') for _,text,_,_ in ROWS} if ansi else {})
    def state(self):return PartyHelpState({address:0 for address in (0x553cb4,0x553cbc,0x553cc4,0x553ccc,0x553cd4)})
    def obs(self,**kw):return replace(PartyHelpObservation(party_count=2,outer_tick=10000,final_tick=10020),**kw)

    def test_producer_text_binding_and_no_implicit_encoding(self):
        values=dict(Profiles(json.loads(Path(__file__).with_name('ui_model.json').read_text(encoding='utf-8'))).defaults)
        c=compile_party_help(values)
        self.assertEqual(c.unicode_texts[0x110],'sw');self.assertEqual(c.unicode_texts[0x114],'cure')
        self.assertEqual(dict(c.ansi_texts),{})
        c=compile_party_help(values,observed_ansi={ROOT+'txtHelpChatSW':b'sw'})
        self.assertEqual(c.ansi_texts[0x110],b'sw');self.assertNotIn(0x114,c.ansi_texts)

    def test_small_party_does_not_read_time_or_flags(self):
        for count in (0,1,0xffffffff):
            p=plan_party_help(PartyHelpConfiguration({},{}),PartyHelpState(),PartyHelpObservation(party_count=count))
            self.assertTrue(p.complete);self.assertEqual(p.status,'party_too_small')
            self.assertEqual(p.calls,(('004645e4',()),));self.assertEqual(p.next_address,0x459496)

    def test_outer4999_5000_boundary_and_stamp_even_with_all_flags_disabled(self):
        p=plan_party_help(self.config(),self.state(),self.obs(outer_tick=4999,final_tick=None))
        self.assertTrue(p.complete);self.assertEqual(p.status,'outer_timer_wait');self.assertEqual(p.writes,())
        p=plan_party_help(self.config(),self.state(),self.obs(outer_tick=5000,final_tick=5001))
        self.assertTrue(p.complete);self.assertEqual(p.writes,((0x553cb4,5001,0),));self.assertEqual(p.requests,())

    def test_feature9999_10000_boundary_and_fresh_request_stamp(self):
        p=plan_party_help(self.config(0x103),self.state(),self.obs(feature_ticks={0x103:9999}))
        self.assertTrue(p.complete);self.assertEqual(p.requests,())
        o=self.obs(feature_ticks={0x103:10000},predicate_returns={0x103:1},request_returns={0x103:True},post_request_ticks={0x103:10001},final_tick=10002)
        p=plan_party_help(self.config(0x103),self.state(),o)
        self.assertTrue(p.complete);self.assertEqual(p.writes,((0x553cbc,10001,0),(0x553cb4,10002,0)))

    def test_predicate_uses_low_byte_and_no_post_request_read_on_false(self):
        o=self.obs(feature_ticks={0x103:10000},predicate_returns={0x103:0x100})
        p=plan_party_help(self.config(0x103),self.state(),o)
        self.assertTrue(p.complete);self.assertEqual(p.requests,())
        self.assertNotIn('004c9b74',[x[0] for x in p.calls])

    def test_missing_ansi_is_not_guessed_from_unicode_text(self):
        o=self.obs(feature_ticks={0x103:10000},predicate_returns={0x103:1})
        p=plan_party_help(self.config(0x103,ansi=False),self.state(),o)
        self.assertFalse(p.complete);self.assertEqual(p.missing,'observed AnsiString field+108')
        self.assertEqual(p.requests,())

    def test_missing_normal_return_prevents_stamp_and_next_feature(self):
        o=self.obs(feature_ticks={0x103:10000},predicate_returns={0x103:1})
        p=plan_party_help(self.config(0x103,0x104),self.state(),o)
        self.assertFalse(p.complete);self.assertEqual(len(p.requests),1);self.assertEqual(p.writes,())
        self.assertEqual(p.missing,'feature103 004c9b74 normal return')

    def test_missing_post_clock_or_final_clock_does_not_commit_prefix(self):
        state=self.state()
        o=self.obs(feature_ticks={0x103:10000},predicate_returns={0x103:1},request_returns={0x103:True})
        p=plan_party_help(self.config(0x103),state,o)
        self.assertFalse(p.complete);self.assertIs(p.state,state);self.assertEqual(p.writes,())
        p=plan_party_help(self.config(0x103),state,replace(o,post_request_ticks={0x103:10001},final_tick=None))
        self.assertFalse(p.complete);self.assertIs(p.state,state)
        self.assertEqual(p.prospective_state.timers[0x553cbc],10001);self.assertEqual(p.writes,((0x553cbc,10001,0),))

    def test_full_source_order_and_four_independent_request_clocks(self):
        flags=(0x103,0x104,0x105,0x106)
        o=self.obs(feature_ticks={f:10001+i for i,f in enumerate(flags)},predicate_returns={0x103:1,0x104:1,0x106:1},
            request_returns={f:True for f in flags},post_request_ticks={f:10010+i for i,f in enumerate(flags)},final_tick=10014,
            swift_globals={0x553e7c:0x1000,0x553fe4:0x10},swift_samples=((0x1000,0x2000),(0x2010,0x3f80)))
        p=plan_party_help(self.config(*flags),self.state(),o)
        self.assertTrue(p.complete);self.assertEqual([flag for flag,text in p.requests],list(flags))
        self.assertEqual([w[1] for w in p.writes],[10010,10011,10012,10013,10014])
        self.assertEqual([x[0] for x in p.calls].count('005074da'),10)
        self.assertEqual([x[1][1] for x in p.calls if x[0]=='004c9b74'],[2]*4)
        self.assertFalse(p.native_execution_verified);self.assertFalse(p.messages_sent)

    def test_swift_requires_exact_protected_state_and_explicit_addresses(self):
        o=self.obs(feature_ticks={0x105:10000},swift_globals={0x553e7c:0x1000,0x553fe4:0x10})
        p=plan_party_help(self.config(0x105),self.state(),o)
        self.assertFalse(p.complete);self.assertTrue(p.missing.startswith('Swift read0'))
        p=plan_party_help(self.config(0x105),self.state(),replace(o,swift_samples=((0x1000,0x2000),(0x2010,0x3f81))))
        self.assertTrue(p.complete);self.assertEqual(p.requests,())
        with self.assertRaises(ValueError):plan_party_help(self.config(0x105),self.state(),replace(o,swift_samples=((0x9999,0x2000),)))

    def test_outer_wrap_retains_signed_qword_difference(self):
        state=PartyHelpState({0x553cb4:0xfffffff0})
        p=plan_party_help(PartyHelpConfiguration({},{}),state,self.obs(outer_tick=7000,final_tick=None))
        self.assertTrue(p.complete);self.assertEqual(p.status,'outer_timer_wait')

    def test_zero_post_tick_is_preserved_and_observation_maps_are_immutable(self):
        ticks={0x103:0xffffffff};returns={0x103:True}
        o=self.obs(outer_tick=0xffffffff,feature_ticks=ticks,predicate_returns={0x103:1},request_returns=returns,post_request_ticks={0x103:0},final_tick=1)
        ticks.clear();returns.clear()
        p=plan_party_help(self.config(0x103),self.state(),o)
        self.assertTrue(p.complete);self.assertEqual(p.state.timers[0x553cbc],0)

if __name__=='__main__':unittest.main()
