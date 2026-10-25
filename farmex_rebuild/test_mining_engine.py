import unittest
from mining_engine import (load_mining_routes, route_records, stop_mining,
                           crash_wait_complete, select_start_coordinate,
                           route_browser, MiningRunner, MiningRunnerConfig,
                           MiningExecutionState, MiningSnapshot,
                           OreSlotState, OreSlotSnapshot, process_ore_slot)


class MiningTests(unittest.TestCase):
    def test_declarations_and_recovery(self):
        routes = load_mining_routes()
        self.assertEqual(len(routes), 20)
        self.assertEqual(sum(r['declared_count'] for r in routes.values()), 435)
        self.assertEqual(sum(r['initialized_count'] for r in routes.values()), 427)
        self.assertEqual(routes['EMCMiningRoute4']['initialized_count'], 8)

    def test_actual_first_coordinate(self):
        r = route_records('EMCMiningRoute1')[0]
        self.assertEqual((r['command'], r['x'], r['y']), ('Koordinat', 1603, 407))
        self.assertEqual(r['provenance'][0]['copy_call_address'], '0047e447')

    def test_npc_and_town_keep_literal_parameters(self):
        records = route_records('EMCMiningRoute1')
        self.assertEqual(records[6]['command'], 'NPC')
        self.assertEqual(records[6]['parameter_1_text'], 'Sundries')
        self.assertIsNone(records[6]['parameter_2_text'])
        self.assertEqual(records[15]['command'], 'Town')

    def test_incomplete_route_is_refused(self):
        with self.assertRaises(ValueError):
            route_records('EMCMiningRoute4')

    def test_unknown_route_is_refused(self):
        with self.assertRaises(ValueError):
            route_records('made_up')

    def test_all_coordinates_numeric_and_provenanced(self):
        routes = load_mining_routes()
        for route in routes.values():
            for r in route['records']:
                if r['command'] == 'Koordinat':
                    self.assertEqual(str(r['x']), r['parameter_1_text'])
                    self.assertEqual(str(r['y']), r['parameter_2_text'])
                    self.assertTrue(all(r['provenance']))

    def test_crash_wait_minutes_strict_boundary(self):
        self.assertFalse(crash_wait_complete(True, 2, 100, 120100))
        self.assertTrue(crash_wait_complete(True, 2, 100, 120101))
        self.assertTrue(crash_wait_complete(False, 2, 100, 100))
        self.assertFalse(crash_wait_complete(False, 2, 100, 100, blocked=True))

    def test_invalid_timeline(self):
        with self.assertRaises(ValueError):
            crash_wait_complete(True, 2, 100, 99)

    def test_reset_has_original_item_index(self):
        state = stop_mining()
        self.assertEqual(state.item_index, 14)
        self.assertEqual(state.phase, 0)
        self.assertFalse(state.route_active)

    def test_current_or_retained_mode_one(self):
        self.assertEqual(select_start_coordinate(1, 0x44, (10, 20)).coordinate, (10, 20))
        self.assertEqual(select_start_coordinate(1, 0, (10, 20), previous=(30, 40)).coordinate,
                         (30, 40))
        self.assertFalse(select_start_coordinate(1, 0, (10, 20), previous=(0, 40)).accepted)

    def test_manual_zero_and_measurement_boundary(self):
        self.assertEqual(select_start_coordinate(2, 0, (10, 20), manual=(1, 2)).coordinate, (1, 2))
        self.assertTrue(select_start_coordinate(2, 0x44, (10, 20)).accepted)
        self.assertFalse(select_start_coordinate(2, 0, (10, 20)).accepted)
        self.assertTrue(select_start_coordinate(2, 0, (10, 20), fallback_measurement=49.9).accepted)
        self.assertFalse(select_start_coordinate(2, 0, (10, 20), fallback_measurement=50).accepted)

    def test_manual_route_state_required(self):
        self.assertTrue(select_start_coordinate(3, 0x44, (10, 20)).accepted)
        self.assertFalse(select_start_coordinate(3, 0, (10, 20)).accepted)
        self.assertFalse(select_start_coordinate(99, 0x44, (10, 20)).accepted)


class MiningRunnerTests(unittest.TestCase):
    def tick(self, phase, snapshot=None, now=10000, config=None, **fields):
        state = MiningExecutionState(phase=phase, route_active=True, **fields)
        return MiningRunner(config).tick(state, snapshot or MiningSnapshot(), now)

    def test_summary_browser_marks_gap(self):
        rows = route_browser()
        self.assertEqual(len(rows), 20)
        self.assertEqual(sum(x['coordinate_count'] for x in rows), 397)
        self.assertEqual(sum(not x['complete_literals'] for x in rows), 1)

    def test_disabled_and_global_block_do_not_progress(self):
        state = MiningExecutionState(phase=6)
        self.assertEqual(MiningRunner().tick(state, MiningSnapshot(), 100).state, state)
        state = MiningExecutionState(phase=6, route_active=True)
        self.assertEqual(MiningRunner().tick(state, MiningSnapshot(blocked_561f7e=True), 100).state, state)

    def test_phase_zero_strict_wait_then_reset(self):
        cfg = MiningRunnerConfig(True, 1)
        self.assertEqual(self.tick(0, now=60000, config=cfg).state.phase, 0)
        result = self.tick(0, now=60001, config=cfg)
        self.assertEqual(result.state.phase, 1)
        self.assertEqual(result.intents[0].name, 'reset_5690cc_5690d8')

    def test_phase_one_requires_real_helper_result(self):
        result = self.tick(1, MiningSnapshot(comparison_505118=True))
        self.assertEqual(result.required_observations, ('helper_479988_result',))
        self.assertEqual(result.state.phase, 1)
        result = self.tick(1, MiningSnapshot(comparison_505118=True, helper_479988_result=True))
        self.assertEqual(result.state.phase, 2)

    def test_phase_one_near_target_resolution(self):
        snap = MiningSnapshot(comparison_505118=False, fallback_coordinate_selected=True,
                              distance_outer=50, distance_inner=2, helper_465960_target_id=123)
        result = self.tick(1, snap)
        self.assertEqual((result.state.phase, result.state.target_id), (2, 123))

    def test_phase_one_move_retry_boundaries(self):
        snap = MiningSnapshot(comparison_505118=False, fallback_coordinate_selected=True,
                              distance_outer=50, distance_inner=2.1)
        self.assertFalse(self.tick(1, snap, now=2999).intents)
        result = self.tick(1, snap, now=3000)
        self.assertEqual(result.intents[0].source_address, '004646b4')
        self.assertEqual(result.state.last_move_ms, 3000)
        self.assertFalse(MiningRunner().tick(result.state, snap, 3999).intents)
        self.assertTrue(MiningRunner().tick(result.state, snap, 4000).intents)

    def test_phase_one_far_control_retry(self):
        snap = MiningSnapshot(comparison_505118=False, fallback_coordinate_selected=True,
                              distance_outer=50.1)
        self.assertFalse(self.tick(1, snap, now=4999).intents)
        self.assertEqual(self.tick(1, snap, now=5000).intents[0].source_address, '00465678')

    def test_phase_two_branch_and_exhaustion(self):
        self.assertEqual(self.tick(2, MiningSnapshot(comparison_505118=False)).state.phase, 3)
        snap = MiningSnapshot(comparison_505118=True, helper_477770_count=0)
        self.assertEqual(self.tick(2, snap).state.phase, 4)
        snap = MiningSnapshot(comparison_505118=True, helper_477770_count=1,
                              helper_464a10_result=True)
        self.assertEqual(self.tick(2, snap, item_index=42).state.phase, 4)

    def test_phase_two_integer_distance_boundary(self):
        snap = MiningSnapshot(comparison_505118=True, helper_477770_count=1,
                              helper_464a10_result=True, distance_ore=7.9)
        self.assertEqual(self.tick(2, snap).intents[0].source_address, '00479698')
        snap = MiningSnapshot(comparison_505118=True, helper_477770_count=1,
                              helper_464a10_result=True, distance_ore=8)
        self.assertEqual(self.tick(2, snap).intents[0].source_address, '004646b4')

    def test_phase_three_distance_and_end(self):
        snap = MiningSnapshot(helper_477770_count=1, distance_ore=10)
        self.assertEqual(self.tick(3, snap).state.phase, 1)
        snap = MiningSnapshot(helper_477770_count=1, distance_ore=9.9)
        self.assertEqual(self.tick(3, snap).intents[0].source_address, '00479698')
        self.assertEqual(self.tick(3, snap, item_index=42).state.phase, 4)

    def test_phase_four_recheck_and_job_start(self):
        result = self.tick(4, MiningSnapshot(helper_477770_count=1), item_index=40)
        self.assertEqual((result.state.phase, result.state.item_index), (2, 14))
        result = self.tick(4, MiningSnapshot(helper_477770_count=0, job_568dbc_active=False))
        self.assertEqual(result.state.phase, 5)
        self.assertEqual(result.intents[0].name, 'begin_job_568dbc')
        self.assertEqual(self.tick(4, MiningSnapshot(helper_477770_count=0,
                                                   job_568dbc_active=True)).state.phase, 4)

    def test_phase_five_storage_start_and_wait(self):
        cfg = MiningRunnerConfig(vip_storage=True)
        result = self.tick(5, config=cfg)
        self.assertTrue(result.state.auxiliary_flag)
        self.assertEqual(result.intents[0].value, 5)
        result = MiningRunner(cfg).tick(result.state, MiningSnapshot(storage_5690b8_active=True), 11000)
        self.assertEqual(result.state.phase, 5)

    def test_phase_five_storage_resume_and_finish(self):
        cfg = MiningRunnerConfig(vip_storage=True)
        snap = MiningSnapshot(storage_5690b8_active=False, storage_5690cc_value=47)
        result = self.tick(5, snap, config=cfg, auxiliary_flag=True)
        self.assertEqual((result.state.phase, result.state.item_index), (2, 0))
        snap = MiningSnapshot(storage_5690b8_active=False, storage_5690cc_value=48,
                              helper_477770_count=0)
        self.assertEqual(self.tick(5, snap, config=cfg, auxiliary_flag=True).state.phase, 6)
        snap = MiningSnapshot(storage_5690b8_active=False, storage_5690cc_value=48,
                              helper_477770_count=1)
        self.assertEqual(self.tick(5, snap, config=cfg, auxiliary_flag=True).state.phase, 2)

    def test_phase_five_without_vip_then_six_and_seven(self):
        self.assertEqual(self.tick(5).state.phase, 6)
        self.assertEqual(self.tick(6).state.phase, 7)
        result = self.tick(7)
        self.assertFalse(result.state.route_active)
        self.assertEqual(result.intents[0].source_address, '00477bd4')

    def test_missing_measurements_never_default_to_success(self):
        for phase in (1, 2, 3, 4):
            result = self.tick(phase)
            self.assertEqual(result.state.phase, phase)
            self.assertTrue(result.required_observations)

    def test_clock_and_phase_validation(self):
        with self.assertRaises(ValueError):
            self.tick(99)
        with self.assertRaises(ValueError):
            self.tick(6, now=100, last_move_ms=101)


class OreSlotTests(unittest.TestCase):
    def test_cadence_is_seconds_and_equality_runs(self):
        state = OreSlotState(last_attempt_ms=100)
        snap = OreSlotSnapshot(True, request_helper_45dc44_zero=True)
        self.assertFalse(process_ore_slot(state, snap, 5099, 5).intents)
        result = process_ore_slot(state, snap, 5100, 5)
        self.assertEqual((result.state.item_index, result.state.last_attempt_ms), (15, 5100))
        self.assertEqual(result.intents[0].source_address, '004c80e4')

    def test_non_ore_skips_slot_without_timestamp(self):
        state = OreSlotState(last_attempt_ms=100)
        result = process_ore_slot(state, OreSlotSnapshot(False), 5100, 5)
        self.assertEqual(result.state.item_index, 15)
        self.assertEqual(result.state.last_attempt_ms, 100)
        self.assertFalse(result.intents)

    def test_unknown_gate_cannot_be_success(self):
        result = process_ore_slot(OreSlotState(), OreSlotSnapshot(True), 5100, 5)
        self.assertEqual(result.required_observations, ('request_helper_45dc44_zero',))
        self.assertEqual(result.state.item_index, 14)

    def test_ws_first_phase_counter_and_request_pending(self):
        result = process_ore_slot(OreSlotState(), OreSlotSnapshot(True, True, False), 5100, 5, True)
        self.assertEqual(result.state.ws_counter, 1)
        self.assertEqual(result.state.ws_first_ms, 5100)
        self.assertEqual(result.intents[0].name, 'ws_action_465f30_first')
        self.assertEqual(result.state.item_index, 14)

    def test_ws_second_strict_delay20_and50(self):
        snap = OreSlotSnapshot(True, False, False)
        state = OreSlotState(ws_first_ms=100)
        self.assertFalse(process_ore_slot(state, snap, 120, 0, True).intents)
        self.assertTrue(process_ore_slot(state, snap, 121, 0, True).state.ws_active)
        state = OreSlotState(ws_first_ms=100, ws_counter=1)
        self.assertFalse(process_ore_slot(state, snap, 150, 0, True).intents)
        self.assertTrue(process_ore_slot(state, snap, 151, 0, True).state.ws_active)

    def test_request_resets_ws_without_claiming_acceptance(self):
        state = OreSlotState(ws_active=True)
        result = process_ore_slot(state, OreSlotSnapshot(True, request_helper_45dc44_zero=True), 100, 0, True)
        self.assertFalse(result.state.ws_active)
        self.assertEqual(result.intents[0].name, 'ore_crash_request_attempt')


if __name__ == '__main__':
    unittest.main()
