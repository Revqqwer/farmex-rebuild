import unittest
from dataclasses import replace
from special_routes import SpecialCommand, SpecialRouteSnapshot, SpecialRouteState, special_route_step


class SpecialRouteTests(unittest.TestCase):
    def snapshot(self, **values):
        defaults = dict(now_ms=1000, actor_raw_byte_554020=0, hp_4611a0=50, max_hp_4611c0=100,
                        npc_found_465960=True, npc_pointer_found_464a10=True, npc_distance=8,
                        npc_interaction_raw_byte=0, displacement=11, npc_helper_return_4f11a0=True)
        defaults.update(values)
        return SpecialRouteSnapshot(**defaults)

    def test_town_half_boundary_and_prepare_call(self):
        c = SpecialCommand('Town')
        r = special_route_step(c, self.snapshot(hp_4611a0=49))
        self.assertEqual(r.calls, ('00464714',))
        self.assertFalse(r.state.started)
        r = special_route_step(c, self.snapshot())
        self.assertEqual(r.calls, ('00464714', '004c8604'))
        self.assertTrue(r.state.started)

    def test_town_integer_truncation(self):
        r = special_route_step(SpecialCommand('Town'), self.snapshot(max_hp_4611c0=101))
        self.assertEqual(r.status, 'started')

    def test_unknown_health_preserves_prepare_plan(self):
        r = special_route_step(SpecialCommand('Town'), self.snapshot(max_hp_4611c0=None))
        self.assertEqual(r.status, 'needs_observation')
        self.assertEqual(r.calls, ('00464714',))

    def test_each_fixed_wait_boundary(self):
        times = {'Town': 2000, 'Otur': 2000, 'Kalk': 2000, 'Gate Skill': 3000,
                 'Gate Open': 1500, 'Gate': 3000, 'Delos Gate Open': 1000,
                 'Delos Gate': 3000, 'Change Camp': 2000}
        for name, wait in times.items():
            with self.subTest(name=name):
                state = SpecialRouteState(started=True, started_qword=1000)
                c = SpecialCommand(name, 5)
                self.assertEqual(special_route_step(c, self.snapshot(now_ms=1000+wait-1), state).status, 'waiting')
                r = special_route_step(c, self.snapshot(now_ms=1000+wait), state)
                self.assertEqual(r.status, 'step_complete')
                self.assertFalse(r.state.started)
                self.assertFalse(r.state.processing)

    def test_sit_stand_first_matching_branch(self):
        for name, helper in (('Otur', '00465de0'), ('Kalk', '00465e50')):
            r = special_route_step(SpecialCommand(name), self.snapshot())
            self.assertEqual(r.calls, (helper,))
            self.assertEqual(r.queue_payloads, ())

    def test_actor_blocks_gate_before_unknown_parameter(self):
        r = special_route_step(SpecialCommand('Gate Skill'), self.snapshot(actor_raw_byte_554020=1))
        self.assertEqual(r.status, 'blocked')
        self.assertEqual(r.calls, ())

    def test_gate_packets_match_template_and_signed_dword(self):
        opened = special_route_step(SpecialCommand('Gate Open', -1), self.snapshot())
        self.assertEqual(opened.queue_payloads, (bytes.fromhex('33ffffffff'),))
        gate = special_route_step(SpecialCommand('Gate', 0x12345678), self.snapshot())
        self.assertEqual(gate.queue_payloads, (bytes.fromhex('4b78563412'),))

    def test_generic_gate_helper(self):
        r = special_route_step(SpecialCommand('Gate Skill'), self.snapshot())
        self.assertEqual(r.calls, ('004c8d84',))

    def test_delos_gate_truncates_parameter_to_byte_and_saves_origin(self):
        r = special_route_step(SpecialCommand('Delos Gate', 257), self.snapshot())
        self.assertEqual(r.queue_payloads[0][1], 1)
        self.assertEqual(len(r.queue_payloads[0]), 19)
        self.assertEqual(r.calls, ('004625ac:save_x', '004625d8:save_y', '004c7710'))

    def test_delos_displacement_must_exceed_ten(self):
        st = SpecialRouteState(started=True, started_qword=0)
        c = SpecialCommand('Delos Gate', 1)
        self.assertEqual(special_route_step(c, self.snapshot(now_ms=3000, displacement=10), st).status, 'waiting')
        self.assertEqual(special_route_step(c, self.snapshot(now_ms=3000, displacement=10.001), st).status, 'step_complete')

    def test_delos_open_npc_distance_strict(self):
        c = SpecialCommand('Delos Gate Open')
        near = special_route_step(c, self.snapshot(npc_distance=8.999))
        self.assertIn('004c8f7c', near.calls)
        equal = special_route_step(c, self.snapshot(npc_distance=9))
        self.assertIn('004646b4', equal.calls)
        self.assertNotIn('004c8f7c', equal.calls)

    def test_delos_open_wait_starts_even_no_npc(self):
        r = special_route_step(SpecialCommand('Delos Gate Open'), self.snapshot(npc_found_465960=False,
                                                                               npc_pointer_found_464a10=None))
        self.assertEqual(r.status, 'started')
        self.assertEqual(r.calls, ('00465960:[Teleport Gate]',))

    def test_delos_open_independent_interaction_byte(self):
        r = special_route_step(SpecialCommand('Delos Gate Open'), self.snapshot(npc_interaction_raw_byte=1))
        self.assertEqual(r.status, 'blocked')
        self.assertFalse(r.state.started)

    def test_change_camp_randomize_is_parameter(self):
        r = special_route_step(SpecialCommand('Change Camp', randomize=True), self.snapshot())
        self.assertEqual(r.calls, ('00464714', '004c8a98'))
        r = special_route_step(SpecialCommand('Randomize'), self.snapshot())
        self.assertEqual(r.status, 'step_complete')
        self.assertEqual(r.calls, ())

    def test_change_camp_zero_still_starts_wait(self):
        r = special_route_step(SpecialCommand('Change Camp', 0), self.snapshot())
        self.assertEqual(r.calls, ('00464714',))
        self.assertTrue(r.state.started)

    def test_change_camp_nonzero_calls_helper(self):
        r = special_route_step(SpecialCommand('Change Camp', 1), self.snapshot())
        self.assertEqual(r.calls[-1], '004c8698')

    def test_npc_aux_phase_and_explicit_helper_polarity(self):
        c = SpecialCommand('NPC')
        start = special_route_step(c, self.snapshot())
        self.assertEqual(start.state.auxiliary_phase, 1)
        waiting = special_route_step(c, self.snapshot(npc_helper_return_4f11a0=False), start.state)
        self.assertEqual(waiting.status, 'waiting')
        done = special_route_step(c, self.snapshot(), start.state)
        self.assertEqual(done.status, 'step_complete')

    def test_npc_unknown_result_is_not_success(self):
        r = special_route_step(SpecialCommand('NPC'), self.snapshot(npc_helper_return_4f11a0=None),
                               SpecialRouteState(started=True))
        self.assertEqual(r.status, 'needs_observation')
        self.assertEqual(r.calls, ('004f11a0',))

    def test_signed_future_timestamp_waits(self):
        r = special_route_step(SpecialCommand('Otur'), self.snapshot(),
                               SpecialRouteState(started=True, started_qword=2000))
        self.assertEqual(r.status, 'waiting')

    def test_unknown_command_source_completion_and_inactive(self):
        r = special_route_step(SpecialCommand('unsupported'), self.snapshot())
        self.assertEqual(r.status, 'step_complete')
        self.assertEqual(special_route_step(SpecialCommand('Town'), SpecialRouteSnapshot(0),
                                            SpecialRouteState(processing=False)).status, 'inactive')

    def test_invalid_input_types(self):
        for values in ({'npc_distance': float('nan')}, {'npc_interaction_raw_byte': 256}, {'now_ms': 1<<32}):
            with self.assertRaises(ValueError):
                self.snapshot(**values)
        with self.assertRaises(ValueError):
            SpecialCommand('Gate Open', 1 << 31)


if __name__ == '__main__':
    unittest.main()
