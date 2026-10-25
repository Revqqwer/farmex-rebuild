import unittest
from dataclasses import replace
import test_alternate_dispatcher as head_fixture
import test_rogue_combo as combo_fixture
from rogue_chain import RogueChainState,replay_rogue_chain
from rogue_combo import ComboState

class RogueChainTests(unittest.TestCase):
    def setUp(self):
        fixture=head_fixture.AlternateTests()
        self.snapshot=fixture.snapshot(rogue_raw_463fc4=1)
        self.replies=fixture.replies()
        self.combo=combo_fixture.ComboTests();self.combo.setUp()
    def run_chain(self,snapshot=None,state=RogueChainState(),observation=None,**kwargs):
        return replay_rogue_chain(snapshot or self.snapshot,observation or self.combo.o,
            state=state,replies=self.replies,**(kwargs or self.combo.selector))
    def test_head_reaches_combo_and_real_local_selector_model(self):
        p=self.run_chain()
        self.assertEqual(p.head.calls[-1],'004db864');self.assertEqual(p.state.combo.stage,1)
        self.assertEqual(p.combo.selector.skill_number,0x22b);self.assertFalse(p.independently_verified)
    def test_head_route_or_lock_does_not_invoke_nested_consumer(self):
        for changes in ({'locked_561f7e':True},{'attack_enabled_561f6c':False},{'rogue_raw_463fc4':0}):
            p=self.run_chain(replace(self.snapshot,**changes))
            self.assertIsNone(p.combo);self.assertEqual(p.state.combo,ComboState())
    def test_incomplete_nested_prefix_is_reported_without_committing(self):
        p=self.run_chain(observation=replace(self.combo.o,clocks={}))
        self.assertEqual(p.status,'combo_incomplete');self.assertEqual(p.state.combo,ComboState())
        self.assertEqual(p.combo.state.category,1);self.assertIn(('00561f7e',1),p.combo.local_writes)
    def test_stage6_query_composition_and_separate_clocks(self):
        p=self.run_chain(state=RogueChainState(combo=ComboState(stage=6,category=1)),
            observation=replace(self.combo.o,clocks={'wait6':1000,'after6':1005}))
        self.assertEqual((p.state.combo.stage,p.state.combo.end_ms),(7,1005))
        self.assertEqual(p.combo.selector.local_writes,())
