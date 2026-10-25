import unittest
from dataclasses import replace
import test_kurian_attack as source_fixture
from kurian_attack import KurianCycleState,replay_kurian_cycle

class KurianReplayTests(unittest.TestCase):
    def test_phase0_consumes_selected_local_return_instead_of_given_al(self):
        attack=source_fixture.enabled(source_fixture.attack(),0x3a)
        result=replay_kurian_cycle(source_fixture.cycle(attack_return_al=255),attack)
        self.assertEqual((result.selector.source_return,result.cycle.state.attack_return_al),(1,1))
        result=replay_kurian_cycle(source_fixture.cycle(attack_return_al=255),source_fixture.attack())
        self.assertEqual((result.cycle.state.phase,result.cycle.state.attack_return_al),(1,0))
        self.assertFalse(result.independently_verified)
    def test_unknown_send_result_does_not_advance_phase(self):
        attack=source_fixture.enabled(source_fixture.attack(helper_bools={'00464490:23c':False}),0x3a)
        result=replay_kurian_cycle(source_fixture.cycle(),attack)
        self.assertEqual(result.status,'needs_observation');self.assertEqual(result.cycle.state.phase,0)
        self.assertEqual(result.selector.calls[-1][0],'004655e8')
    def test_distinct_outer10_and_nested8_source_caps(self):
        attack=source_fixture.enabled(source_fixture.attack(distance=9,configured_range=50),0x3a)
        result=replay_kurian_cycle(source_fixture.cycle(distance=9,configured_range=50),attack)
        self.assertEqual(result.selector.status,'out_of_range')
        self.assertEqual((result.cycle.state.phase,result.cycle.state.attack_return_al),(1,0))
        result=replay_kurian_cycle(source_fixture.cycle(distance=10.01,configured_range=50),attack)
        self.assertEqual(result.status,'out_of_range');self.assertIsNone(result.selector)
    def test_nonzero_phase_never_calls_selector(self):
        st=KurianCycleState(phase=1,attack_return_al=0)
        result=replay_kurian_cycle(source_fixture.cycle(enabled_561fcc=False),None,st)
        self.assertEqual(result.cycle.state.phase,2);self.assertIsNone(result.selector)
    def test_cycle_guard_order_prevents_nested_selection(self):
        st=KurianCycleState(phase=4)
        result=replay_kurian_cycle(source_fixture.cycle(locked_561f7e=True),None,st)
        self.assertEqual(result.cycle.state.phase,0);self.assertIsNone(result.selector)
        result=replay_kurian_cycle(source_fixture.cycle(locked_561f7e=True,distance=11),None,st)
        self.assertEqual(result.cycle.state,st);self.assertEqual(result.status,'out_of_range')
