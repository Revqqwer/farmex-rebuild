import unittest
from dataclasses import replace
from alternate_dispatcher import AlternateSnapshot, AlternateState, dispatch_alternate
from job_dispatcher import HelperReply


class AlternateTests(unittest.TestCase):
    def snapshot(self, **changes):
        values = dict(now_ms=1000, locked_561f7e=False, raw_byte_55402c=0,
                      raw_float_554030=0, actor_state_554034=0, attack_enabled_561f6c=True,
                      guard_fe384=False, guard_46fe90=False, target_id_562040=2,
                      current_target_462630=2, target_ready_56204c=True,
                      target_mode_561f64=0, target_raw_byte_554034=0,
                      rogue_flag_0=False, rogue_raw_463fc4=0,
                      rogue_minor_actor_state_554034=0, rogue_attack_actor_state_554034=0,
                      warrior_flag_198=False, priest_final_raw_byte_55402c=0,
                      priest_final_raw_float_554030=0, target_max_hp_positive=True,
                      target_hp_positive=True)
        values.update(changes)
        return AlternateSnapshot(**values)

    def replies(self, success=None, lock=False):
        return {h: HelperReply(h == success, lock) for h in
                ('00499b88', '00499620', '004994bc', '00471c38', '00472b90',
                 '0050269c', '004cf8b8', '004d0c18', '004cfc74', '004cee18',
                 '004d20b0', '004d0434', '004da25c', '004da2d4', '004da568',
                 '004da784', '004dd2e0')}

    def run_head(self, job='mage', state=AlternateState(), replies=None, **changes):
        return dispatch_alternate(job, self.snapshot(**changes), state,
                                  self.replies() if replies is None else replies)

    def test_mage_priority_early_exit(self):
        r = self.run_head(replies=self.replies('00499620'))
        self.assertEqual(r.calls, ('00499b88', '00499620'))
        self.assertEqual(r.state, AlternateState(1000, 650))

    def test_mage_all_support_then_attack(self):
        self.assertEqual(self.run_head().calls, ('00499b88', '00499620', '004994bc', '0049b318'))

    def test_zero_float_passes_both_source_assemblies(self):
        for job in ('mage', 'kurian'):
            self.assertTrue(self.run_head(job).calls)
            self.assertFalse(self.run_head(job, raw_float_554030=0.001).calls)

    def test_actor_state_six_skips_support(self):
        self.assertEqual(self.run_head(actor_state_554034=6).calls, ('0049b318',))
        self.assertEqual(self.run_head('kurian', actor_state_554034=6).calls, ('0047225c',))

    def test_interval_equality(self):
        state = AlternateState(500, 500)
        self.assertTrue(self.run_head(state=state).calls)
        self.assertFalse(self.run_head(state=state, now_ms=999).calls)

    def test_kurian_primary_support_state(self):
        r = self.run_head('kurian', replies=self.replies('00471c38'))
        self.assertEqual(r.calls, ('00471c38',))
        self.assertEqual(r.state, AlternateState(1000, 500))

    def test_kurian_secondary_support_state(self):
        r = self.run_head('kurian', replies=self.replies('00472b90'))
        self.assertEqual(r.calls, ('00471c38', '00472b90'))
        self.assertEqual(r.state, AlternateState(1000, 650))

    def test_kurian_negative_primary_changes_interval_not_timestamp(self):
        r = self.run_head('kurian', state=AlternateState(900, 100))
        self.assertEqual(r.calls, ('00471c38', '00472b90', '0047225c'))
        self.assertEqual(r.state, AlternateState(900, 100))

    def test_kurian_target_state_skips_secondary_only(self):
        self.assertEqual(self.run_head('kurian', target_raw_byte_554034=4).calls,
                         ('00471c38', '0047225c'))

    def test_mage_requires_ready_kurian_final_attack_does_not(self):
        self.assertNotIn('0049b318', self.run_head(target_ready_56204c=False).calls)
        self.assertIn('0047225c', self.run_head('kurian', target_ready_56204c=False).calls)

    def test_retarget_does_not_stop_mage(self):
        r = self.run_head(actor_state_554034=6, current_target_462630=3)
        self.assertEqual(r.calls, ('0046493c', '0049b318'))

    def test_kurian_retargets_in_both_branches_without_fabricating_new_target(self):
        r = self.run_head('kurian', current_target_462630=3)
        self.assertEqual(r.calls, ('00471c38', '0046493c', '00472b90', '0046493c', '0047225c'))

    def test_preserve_modes(self):
        for mode in (1, 5):
            self.assertNotIn('0046493c', self.run_head(current_target_462630=3, target_mode_561f64=mode).calls)

    def test_unknown_helper_stops(self):
        r = self.run_head(replies={})
        self.assertEqual(r.status, 'needs_observation')
        self.assertEqual(r.calls, ('00499b88',))

    def test_unknown_post_support_lock(self):
        self.assertEqual(self.run_head(replies=self.replies(lock=None)).reason, 'post_support_lock')

    def test_support_can_set_lock(self):
        r = self.run_head(replies=self.replies(lock=True))
        self.assertNotIn('0049b318', r.calls)

    def test_route_gate_prevents_final_not_support(self):
        r = self.run_head(guard_fe384=True)
        self.assertEqual(r.calls, ('00499b88', '00499620', '004994bc'))

    def test_lock_and_raw_byte_short_circuit(self):
        self.assertFalse(self.run_head(locked_561f7e=True, raw_float_554030=None).calls)
        self.assertEqual(self.run_head(raw_byte_55402c=1, raw_float_554030=None).reason, 'raw_gate')

    def test_future_time_and_unknown_state(self):
        with self.assertRaises(ValueError):
            self.run_head(state=AlternateState(1001, 0))
        self.assertEqual(self.run_head(actor_state_554034=None).status, 'needs_observation')

    def test_warrior_positive_support(self):
        r = self.run_head('warrior', replies=self.replies('0050269c'))
        self.assertEqual(r.calls, ('0050269c',))
        self.assertEqual(r.state, AlternateState(1000, 500))

    def test_warrior_negative_support_final(self):
        r = self.run_head('warrior')
        self.assertEqual(r.calls, ('0050269c', '00502c4c'))
        self.assertEqual(r.state, AlternateState(0, 100))

    def test_warrior_special_without_target_or_due_timer(self):
        r = self.run_head('warrior', state=AlternateState(900, 500), warrior_flag_198=True,
                          target_id_562040=0)
        self.assertEqual(r.calls, ('0050306c',))

    def test_warrior_unknown_special_flag_prevents_guessing(self):
        self.assertEqual(self.run_head('warrior', actor_state_554034=6,
                                      warrior_flag_198=None).status, 'needs_observation')

    def test_priest_first_heal_precedes_invalid_raw_gate(self):
        r = self.run_head('priest', replies=self.replies('004cf8b8'), raw_byte_55402c=1)
        self.assertEqual(r.calls, ('004cf8b8',))
        self.assertEqual(r.state, AlternateState(1000, 650))

    def test_priest_all_support_then_no_early_attack(self):
        r = self.run_head('priest')
        self.assertEqual(r.calls, ('004cf8b8', '004d0c18', '004cfc74', '004cee18',
                                  '004d20b0', '004d0434'))
        self.assertEqual(r.state, AlternateState())

    def test_priest_support_early_exit_order(self):
        r = self.run_head('priest', replies=self.replies('004cee18'))
        self.assertEqual(r.calls, ('004cf8b8', '004d0c18', '004cfc74', '004cee18'))
        self.assertEqual(r.state.interval_ms, 650)

    def test_priest_final_timer_is_independent_1500(self):
        state = AlternateState(0, 5000)
        self.assertFalse(self.run_head('priest', state=state, now_ms=1499).calls)
        self.assertEqual(self.run_head('priest', state=state, now_ms=1500).calls, ('004d2aa8',))

    def test_priest_final_ignores_attack_route_gates(self):
        r = self.run_head('priest', actor_state_554034=6, now_ms=1500,
                          attack_enabled_561f6c=False, guard_fe384=True, guard_46fe90=True)
        self.assertEqual(r.calls, ('004d2aa8',))

    def test_priest_final_requires_positive_target_vitals(self):
        self.assertNotIn('004d2aa8', self.run_head('priest', now_ms=1500,
                                                 target_hp_positive=False).calls)

    def test_priest_final_reads_are_not_invented(self):
        r = self.run_head('priest', actor_state_554034=6, priest_final_raw_float_554030=None)
        self.assertEqual(r.reason, 'final_raw_float')

    def test_priest_retargets_and_continues_in_both_passes(self):
        r = self.run_head('priest', now_ms=1500, current_target_462630=3)
        self.assertEqual(r.calls.count('0046493c'), 2)
        self.assertEqual(r.calls[-1], '004d2aa8')

    def test_rogue_support_order(self):
        r = self.run_head('rogue')
        self.assertEqual(r.calls, ('004da2d4', '004da568', '004da784', '004dd2e0', '004dc0a0'))
        self.assertEqual(r.state, AlternateState(0, 100))

    def test_rogue_support_consumed(self):
        r = self.run_head('rogue', replies=self.replies('004da568'))
        self.assertEqual(r.calls, ('004da2d4', '004da568'))
        self.assertEqual(r.state, AlternateState(1000, 500))

    def test_rogue_interval_goto_skips_support_tail(self):
        r = self.run_head('rogue', state=AlternateState(900, 500))
        self.assertEqual(r.calls, ())

    def test_rogue_support_tail_when_attack_disabled(self):
        r = self.run_head('rogue', attack_enabled_561f6c=False)
        self.assertEqual(r.calls, ('004da784',))

    def test_rogue_actor_six_skips_initial_raw_gates(self):
        r = self.run_head('rogue', actor_state_554034=6, raw_float_554030=None,
                          rogue_attack_actor_state_554034=6)
        self.assertEqual(r.calls, ('004dc0a0',))

    def test_rogue_minor_precedes_raw_gate_and_updates_own_timer(self):
        r = self.run_head('rogue', rogue_flag_0=True, raw_byte_55402c=1,
                          replies=self.replies('004da25c'))
        self.assertEqual(r.calls, ('004da25c',))
        self.assertEqual(r.state.minor_last_ms, 1000)
        self.assertEqual(r.state.last_ms, 0)

    def test_rogue_minor_actor_six_skips_minor(self):
        r = self.run_head('rogue', rogue_flag_0=True, rogue_minor_actor_state_554034=6)
        self.assertNotIn('004da25c', r.calls)

    def test_rogue_path_one_and_attack_consumed(self):
        r = self.run_head('rogue', rogue_raw_463fc4=1)
        self.assertEqual(r.calls[-1], '004db864')
        r = self.run_head('rogue', replies=self.replies('004dd2e0'))
        self.assertNotIn('004dc0a0', r.calls)
        self.assertEqual(r.state, AlternateState(1000, 500))

    def test_rogue_unknown_attack_state_stops(self):
        r = self.run_head('rogue', rogue_attack_actor_state_554034=None)
        self.assertEqual(r.reason, 'attack_actor_state')

    def test_unknown_final_raw_byte_short_circuits_float(self):
        r = self.run_head('priest', actor_state_554034=6, priest_final_raw_byte_55402c=1,
                          priest_final_raw_float_554030=None)
        self.assertEqual(r.status, 'complete')

    def test_new_input_types_rejected(self):
        for values in ({'warrior_flag_198': 1}, {'priest_final_raw_float_554030': float('nan')},
                       {'rogue_attack_actor_state_554034': -1}):
            with self.assertRaises(ValueError):
                self.snapshot(**values)


if __name__ == '__main__':
    unittest.main()
