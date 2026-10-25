import unittest
from dataclasses import replace

from job_dispatcher import (JobSnapshot, JobState, HelperReply, dispatch_job,
                            WarriorSkillSnapshot, WARRIOR_ROWS, select_warrior_skill)


def observation(**changes):
    base = JobSnapshot(60000, locked_561f7e=False, raw_byte_55402c=0,
        raw_float_554030=-1.0, guard_fe384=False, guard_46fe90=False,
        attack_enabled_561f6c=True, target_id_562040=7, target_ready_56204c=True,
        current_target_462630=7, target_mode_561f64=3, target_raw_byte_554034=0,
        priest_pointer_a_nonzero=True, priest_pointer_b_nonzero=True,
        rogue_raw_463fc4=0, warrior_flag_89=False, warrior_stat_462e08=50,
        mp_4611e0=100, rogue_flag_0=False, rogue_flag_1c=False,
        configured_interval_ms=1000, rogue_minor_interval_ms=500)
    return replace(base, **changes)


HELPERS = ('005006e4', '0040da60', '00500e90', '00499b88', '00499620',
           '004994bc', '0049bc9c', '004cf8b8', '004d0c18', '004cfc74',
           '004cee18', '004d0eb0', '0046493c', '004d0434', '004da25c',
           '004da2d4', '004da568', '004dc820', '004dd2e0')


def responses(**changes):
    result = {h: HelperReply(False, False) for h in HELPERS}
    result.update(changes)
    return result


class DispatcherTests(unittest.TestCase):
    def test_warrior_support_before_basic_before_attack(self):
        r = dispatch_job('warrior', observation(), replies=responses())
        self.assertEqual(r.calls, ('005006e4', '0040da60', '00500e90'))
        self.assertEqual(r.status, 'complete')

    def test_warrior_support_success_early_return(self):
        r = dispatch_job('warrior', observation(), replies=responses(**{'005006e4': HelperReply(True, False)}))
        self.assertEqual(r.calls, ('005006e4',))
        self.assertEqual(r.state.shared_last_ms, 60000)

    def test_warrior_support_499_vs_500(self):
        r = dispatch_job('warrior', observation(now_ms=499, configured_interval_ms=1000), replies=responses())
        self.assertEqual(r.calls, ('0040da60',))
        r = dispatch_job('warrior', observation(now_ms=500, configured_interval_ms=1000), replies=responses())
        self.assertEqual(r.calls, ('005006e4', '0040da60'))

    def test_warrior_special_stat_mp_and_30s_boundary(self):
        for now, stat, mp, chosen in ((29999, 45, 60, False), (30000, 44, 60, False),
                                      (30000, 45, 59, False), (30000, 45, 60, True)):
            with self.subTest(now=now, stat=stat, mp=mp):
                s = observation(now_ms=now, warrior_flag_89=True, warrior_stat_462e08=stat, mp_4611e0=mp)
                r = dispatch_job('warrior', s, replies=responses())
                self.assertEqual('0050378c' in r.calls, chosen)
                if chosen:
                    self.assertEqual(r.local_lock_ms, 2000)
                    self.assertEqual(r.calls, ('005006e4', '0050378c'))

    def test_warrior_attack_success_only_updates_local_timestamp(self):
        st = JobState(shared_last_ms=2)
        r = dispatch_job('warrior', observation(), st, responses(**{'00500e90': HelperReply(True, False)}))
        self.assertEqual(st.shared_last_ms, 2)
        self.assertEqual(r.state.shared_last_ms, 60000)

    def test_warrior_target_not_ready_still_calls_basic_source(self):
        r = dispatch_job('warrior', observation(target_ready_56204c=False), replies=responses())
        self.assertIn('0040da60', r.calls)

    def test_mage_support_priority_and_retry650(self):
        r = dispatch_job('mage', observation(), replies=responses(**{'00499620': HelperReply(True, False)}))
        self.assertEqual(r.calls, ('00499b88', '00499620'))
        self.assertEqual(r.state.mage_interval_ms, 650)
        self.assertEqual(r.state.shared_last_ms, 60000)

    def test_mage_all_support_false_then_basic_then_attack(self):
        r = dispatch_job('mage', observation(), replies=responses())
        self.assertEqual(r.calls, ('00499b88', '00499620', '004994bc', '0040da60', '0049bc9c'))

    def test_mage_support_even_attack_disabled(self):
        r = dispatch_job('mage', observation(attack_enabled_561f6c=False), replies=responses())
        self.assertEqual(r.calls, ('00499b88', '00499620', '004994bc'))

    def test_mage_attack_success_uses_configured_retry(self):
        r = dispatch_job('mage', observation(configured_interval_ms=777), replies=responses(**{'0049bc9c': HelperReply(True, False)}))
        self.assertEqual(r.state.mage_interval_ms, 777)

    def test_priest_pre_support_before_bad_raw_gate(self):
        r = dispatch_job('priest', observation(raw_byte_55402c=1), replies=responses())
        self.assertEqual(r.calls, ('004cf8b8',))

    def test_priest_full_support_order_before_target_and_attack(self):
        r = dispatch_job('priest', observation(), replies=responses())
        self.assertEqual(r.calls, ('004cf8b8', '004d0c18', '004cfc74', '004cee18',
                                  '004d0eb0', '004d0434', '0040da60', '004d1694'))

    def test_priest_target_switch_continues_other_class_returns(self):
        s = observation(current_target_462630=8)
        r = dispatch_job('priest', s, replies=responses())
        self.assertIn('0046493c', r.calls)
        self.assertIn('004d1694', r.calls)
        for job in ('warrior', 'mage', 'rogue', 'kurian'):
            with self.subTest(job=job):
                r = dispatch_job(job, s, replies=responses())
                self.assertEqual(r.calls[-1], '0046493c')
                self.assertEqual(r.reason, 'retarget_or_preserve')

    def test_manual_and_autoz_preserve_target(self):
        for job in ('warrior', 'mage', 'rogue', 'kurian'):
            for mode in (1, 5):
                with self.subTest(job=job, mode=mode):
                    r = dispatch_job(job, observation(current_target_462630=8, target_mode_561f64=mode), replies=responses())
                    self.assertNotIn('0046493c', r.calls)
                    self.assertEqual(r.reason, 'retarget_or_preserve')

    def test_priest_pointer_failure_stops_before_attack(self):
        r = dispatch_job('priest', observation(priest_pointer_b_nonzero=False), replies=responses())
        self.assertNotIn('004d0434', r.calls)
        self.assertNotIn('004d1694', r.calls)

    def test_priest_does_not_skip_support_on_route_guard(self):
        r = dispatch_job('priest', observation(guard_fe384=True), replies=responses())
        self.assertEqual(r.calls, ('004cf8b8', '004d0c18', '004cfc74', '004cee18', '004d0eb0'))

    def test_rogue_minor_before_global_lock_or_raw_gate(self):
        r = dispatch_job('rogue', observation(rogue_flag_0=True, locked_561f7e=True, raw_byte_55402c=1),
            replies=responses(**{'004da25c': HelperReply(True, True)}))
        self.assertEqual(r.calls, ('004da25c',))
        self.assertEqual(r.state.rogue_minor_last_ms, 60000)

    def test_rogue_support_side_effect_lock_stops_next_support(self):
        r = dispatch_job('rogue', observation(), replies=responses(**{'004da568': HelperReply(False, True)}))
        self.assertEqual(r.calls, ('004da2d4', '004da568'))

    def test_rogue_first_attack_before_basic_and_melee(self):
        r = dispatch_job('rogue', observation(), replies=responses(**{'004dd2e0': HelperReply(True, False)}))
        self.assertEqual(r.calls, ('004da2d4', '004da568', '004dc820', '004dd2e0'))
        self.assertEqual(r.state.rogue_attack_last_ms, 60000)

    def test_rogue_first_false_then_basic_then_melee(self):
        r = dispatch_job('rogue', observation(), replies=responses())
        self.assertEqual(r.calls[-3:], ('004dd2e0', '0040da60', '004dd780'))

    def test_rogue_path1_replaces_attack_queue(self):
        r = dispatch_job('rogue', observation(rogue_raw_463fc4=1), replies=responses())
        self.assertEqual(r.calls[-1], '004de224')
        self.assertNotIn('004dd2e0', r.calls)

    def test_rogue_special_interval_and_raw_target_state(self):
        r = dispatch_job('rogue', observation(rogue_flag_1c=True, rogue_raw_463fc4=1),
            JobState(rogue_special_last_ms=59001), responses())
        self.assertEqual(r.reason, 'special_interval')
        r = dispatch_job('rogue', observation(target_raw_byte_554034=4), replies=responses())
        self.assertNotIn('004dd2e0', r.calls)

    def test_kurian_strict_float_negative_vs_zero(self):
        for value, expected in ((-0.1, ('0040da60',)), (0.0, ()), (1.0, ())):
            r = dispatch_job('kurian', observation(raw_float_554030=value), replies=responses())
            self.assertEqual(r.calls, expected)

    def test_common_lock_skips_pre_support_except_rogue(self):
        for job in ('warrior', 'priest', 'mage', 'kurian'):
            self.assertEqual(dispatch_job(job, observation(locked_561f7e=True), replies=responses()).calls, ())

    def test_missing_helper_or_gate_never_guesses_action_success(self):
        r = dispatch_job('warrior', observation())
        self.assertEqual(r.status, 'needs_observation')
        self.assertEqual(r.calls, ('005006e4',))
        self.assertEqual(r.state.shared_last_ms, 0)
        r = dispatch_job('kurian', observation(guard_fe384=None), replies=responses())
        self.assertEqual(r.status, 'needs_observation')
        self.assertEqual(r.calls, ())

    def test_invalid_values_and_future_state(self):
        with self.assertRaises(ValueError):
            observation(raw_float_554030=float('nan'))
        with self.assertRaises(ValueError):
            dispatch_job('warrior', observation(), JobState(shared_last_ms=60001))
        with self.assertRaises(ValueError):
            dispatch_job('unknown', observation())


def skill_snapshot(**changes):
    base = WarriorSkillSnapshot(100000, 5.0, 8, 1000,
        {r.flag_offset: False for r in WARRIOR_ROWS},
        {r.stat_reader: 100 for r in WARRIOR_ROWS if r.stat_reader},
        {r.timer_read_offset: 0 for r in WARRIOR_ROWS if r.timer_read_offset is not None}, 101)
    return replace(base, **changes)


class WarriorPriorityTests(unittest.TestCase):
    def test_all39_branches_at_exact_eligibility_boundary(self):
        for row in WARRIOR_ROWS:
            with self.subTest(flag=hex(row.flag_offset), skill=row.skill_number):
                base = skill_snapshot()
                flags = dict(base.flags, **{})
                flags[row.flag_offset] = True
                stats = dict(base.raw_stats)
                if row.stat_reader:
                    stats[row.stat_reader] = row.stat_minimum
                timers = dict(base.last_ms_by_offset)
                if row.timer_read_offset is not None:
                    timers[row.timer_read_offset] = base.now_ms - row.interval_ms
                s = replace(base, flags=flags, raw_stats=stats, mp=row.mp_minimum, last_ms_by_offset=timers)
                r = select_warrior_skill(s)
                self.assertEqual(r.status, 'local_attempt')
                self.assertEqual(r.row, row)
                self.assertEqual(r.skill_id, 101000 + row.skill_number if row.skill_number else None)
                self.assertEqual(select_warrior_skill(replace(s, mp=row.mp_minimum - 1)).status, 'no_eligible_skill')
                if row.stat_reader:
                    stats[row.stat_reader] -= 1
                    self.assertEqual(select_warrior_skill(replace(s, raw_stats=stats)).status, 'no_eligible_skill')
                if row.timer_read_offset is not None:
                    timers[row.timer_read_offset] += 1
                    self.assertEqual(select_warrior_skill(replace(s, last_ms_by_offset=timers)).status, 'no_eligible_skill')

    def test_source_priority_beats_list_input_order(self):
        b = skill_snapshot()
        flags = dict(reversed(list(b.flags.items())))
        flags[0xbc] = flags[0xbd] = True
        self.assertEqual(select_warrior_skill(replace(b, flags=flags)).row.flag_offset, 0xbd)

    def test_earlier_not_ready_falls_through_to_next(self):
        b = skill_snapshot()
        flags = dict(b.flags)
        flags[0xbc] = flags[0xbd] = True
        timers = dict(b.last_ms_by_offset)
        timers[0xf0] = 99999
        self.assertEqual(select_warrior_skill(replace(b, flags=flags, last_ms_by_offset=timers)).row.flag_offset, 0xbc)

    def test_range_equality8_and_configured_smaller(self):
        b = skill_snapshot()
        flags = dict(b.flags)
        flags[0] = True
        self.assertEqual(select_warrior_skill(replace(b, flags=flags, distance=8)).status, 'local_attempt')
        self.assertEqual(select_warrior_skill(replace(b, flags=flags, distance=8.0001)).status, 'out_of_range')
        self.assertEqual(select_warrior_skill(replace(b, flags=flags, distance=5, configured_range=4)).status, 'out_of_range')

    def test_timer_read_write_discrepancy_preserved(self):
        b = skill_snapshot()
        flags = dict(b.flags)
        flags[0x3c] = True
        timers = dict(b.last_ms_by_offset)
        timers[0x68] = b.now_ms - 5100
        timers[0x60] = b.now_ms
        r = select_warrior_skill(replace(b, flags=flags, last_ms_by_offset=timers))
        self.assertEqual(r.local_timer_update, (0x60, b.now_ms))
        self.assertEqual(r.row.timer_read_offset, 0x68)

    def test_unknown_earlier_flag_blocks_guessed_later_selection(self):
        b = skill_snapshot()
        flags = dict(b.flags)
        flags[0xbd] = None
        flags[0] = True
        r = select_warrior_skill(replace(b, flags=flags))
        self.assertEqual(r.status, 'needs_observation')
        self.assertIsNone(r.row)

    def test_unknown_stat_and_timer_require_observation(self):
        b = skill_snapshot()
        flags = dict(b.flags)
        flags[0xbd] = True
        self.assertEqual(select_warrior_skill(replace(b, flags=flags, raw_stats={})).status, 'needs_observation')
        self.assertEqual(select_warrior_skill(replace(b, flags=flags, last_ms_by_offset={})).status, 'needs_observation')

    def test_unknown_skill_prefix_does_not_invent_class_id(self):
        b = skill_snapshot()
        flags = dict(b.flags)
        flags[0xbd] = True
        r = select_warrior_skill(replace(b, flags=flags, raw_skill_prefix_46256c=None))
        self.assertEqual(r.row.skill_number, 775)
        self.assertIsNone(r.skill_id)

    def test_selector_does_not_mutate_timers_or_flags(self):
        b = skill_snapshot()
        flags = dict(b.flags)
        flags[0xbd] = True
        s = replace(b, flags=flags)
        before = dict(s.last_ms_by_offset)
        select_warrior_skill(s)
        self.assertEqual(s.last_ms_by_offset, before)
        self.assertTrue(flags[0xbd])

    def test_nonfinite_invalid_inputs(self):
        with self.assertRaises(ValueError):
            skill_snapshot(distance=float('nan'))
        with self.assertRaises(ValueError):
            skill_snapshot(last_ms_by_offset={0xf0: 100001})


if __name__ == '__main__':
    unittest.main()
