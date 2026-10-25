import unittest
from dataclasses import replace
from mage_attack import MageAttackSnapshot, MAGE_ATTACK_ROWS, select_mage_attack


def snapshot(row=None, **changes):
    flags = {r.flag_offset: False for r in MAGE_ATTACK_ROWS}
    if row:
        flags[row.flag_offset] = True
    s = MageAttackSnapshot(100000, 1.0, 8, 1000, flags,
                           {name: 100 for name in ('00462ddc','00462e08','00462e34','00462670')},
                           {r.timer_offset: 0 for r in MAGE_ATTACK_ROWS if r.timer_offset is not None},
                           False, False, False)
    return replace(s, **changes)


class MageAttackTests(unittest.TestCase):
    def test_all_62_branches_reachable_with_exact_thresholds(self):
        self.assertEqual(len(MAGE_ATTACK_ROWS), 62)
        self.assertEqual(len({r.flag_offset for r in MAGE_ATTACK_ROWS}), 62)
        for r in MAGE_ATTACK_ROWS:
            with self.subTest(skill=r.skill_number):
                stats = {r.stat_reader: r.stat_minimum} if r.stat_reader else {}
                result = select_mage_attack(snapshot(r, mp=r.mp_minimum, raw_stats=stats))
                self.assertEqual(result.status, 'local_attempt')
                self.assertEqual(result.row, r)

    def test_priority_across_groups(self):
        s = snapshot()
        for r in MAGE_ATTACK_ROWS: s.flags[r.flag_offset] = True
        self.assertEqual(select_mage_attack(s).row.skill_number, 671)

    def test_every_mp_threshold_minus_one(self):
        for r in MAGE_ATTACK_ROWS:
            with self.subTest(skill=r.skill_number):
                self.assertEqual(select_mage_attack(snapshot(r, mp=r.mp_minimum-1)).status, 'no_eligible_skill')

    def test_every_stat_threshold_minus_one(self):
        for r in MAGE_ATTACK_ROWS:
            if not r.stat_reader: continue
            with self.subTest(skill=r.skill_number):
                self.assertEqual(select_mage_attack(snapshot(r, raw_stats={r.stat_reader:r.stat_minimum-1})).status, 'no_eligible_skill')

    def test_every_group_range_equality_rejected(self):
        for r in MAGE_ATTACK_ROWS:
            with self.subTest(skill=r.skill_number):
                self.assertEqual(select_mage_attack(snapshot(r, distance=r.distance_exclusive)).status,'no_eligible_skill')

    def test_every_timer_exact_interval_and_one_before(self):
        for r in MAGE_ATTACK_ROWS:
            if r.timer_offset is None: continue
            with self.subTest(skill=r.skill_number):
                s=snapshot(r, timer_values={r.timer_offset:100000-r.interval_ms})
                self.assertEqual(select_mage_attack(s).status,'local_attempt')
                self.assertEqual(select_mage_attack(replace(s,timer_values={r.timer_offset:100001-r.interval_ms})).status,'no_eligible_skill')

    def test_every_timer_writes_next_now_not_last_now(self):
        for r in MAGE_ATTACK_ROWS:
            result=select_mage_attack(snapshot(r))
            expected=() if r.timer_offset is None else ((r.timer_offset,100000+r.cast_ms),)
            self.assertEqual(result.local_timer_updates,expected)

    def test_mode_one_has_no_cast_lock_or_timer(self):
        r=next(r for r in MAGE_ATTACK_ROWS if r.mode==1)
        d=select_mage_attack(snapshot(r, raw_field_554020_nonzero=None))
        self.assertEqual(d.calls,('0049d79c',))
        self.assertIsNone(d.local_lock_ms)
        self.assertEqual(d.local_timer_updates,())

    def test_modes_two_and_three_plan_same_cast_helper(self):
        for mode in (2,3):
            r=next(r for r in MAGE_ATTACK_ROWS if r.mode==mode)
            d=select_mage_attack(snapshot(r))
            self.assertEqual(d.calls,('0049ea1c',))
            self.assertEqual((d.local_lock_ms,d.local_lock_started_ms),(r.cast_ms,100000))

    def test_optional_clear_call_precedes_cast(self):
        d=select_mage_attack(snapshot(MAGE_ATTACK_ROWS[0],raw_field_55403c_nonzero=True))
        self.assertEqual(d.calls,('00465ef8','0049ea1c'))

    def test_post_selection_observations_unknown(self):
        for field in ('raw_field_55403c_nonzero','raw_field_554020_nonzero'):
            d=select_mage_attack(snapshot(MAGE_ATTACK_ROWS[0],**{field:None}))
            self.assertEqual(d.status,'needs_observation')
            self.assertEqual(d.row,MAGE_ATTACK_ROWS[0])
            self.assertEqual(d.local_timer_updates,())

    def test_cast_block_preserves_clear_plan_but_no_lock_or_timer(self):
        d=select_mage_attack(snapshot(MAGE_ATTACK_ROWS[0],raw_field_55403c_nonzero=True,raw_field_554020_nonzero=True))
        self.assertEqual(d.status,'cast_blocked')
        self.assertEqual(d.calls,('00465ef8',))
        self.assertEqual(d.local_timer_updates,())
        self.assertIsNone(d.local_lock_ms)

    def test_range_config_eight_switches_to_forty_five(self):
        r=next(r for r in MAGE_ATTACK_ROWS if r.distance_exclusive==38)
        self.assertEqual(select_mage_attack(snapshot(r,distance=30,configured_range=8)).status,'local_attempt')
        self.assertEqual(select_mage_attack(snapshot(r,distance=30,configured_range=7)).status,'out_of_range')

    def test_global_range_equality_passes_then_branch_strict_range(self):
        self.assertEqual(select_mage_attack(snapshot(MAGE_ATTACK_ROWS[0],distance=7,configured_range=7)).status,'local_attempt')
        self.assertEqual(select_mage_attack(snapshot(distance=45)).status,'no_eligible_skill')
        self.assertEqual(select_mage_attack(snapshot(distance=45.01)).status,'out_of_range')

    def test_float32_rounding_respects_strict_boundary(self):
        r=MAGE_ATTACK_ROWS[0]
        self.assertEqual(select_mage_attack(snapshot(r,distance=26-1e-8)).status,'no_eligible_skill')
        self.assertEqual(select_mage_attack(snapshot(r,distance=26-1e-4)).status,'local_attempt')

    def test_unknown_earlier_flag_prevents_lower_candidate(self):
        s=snapshot(MAGE_ATTACK_ROWS[1]);s.flags[MAGE_ATTACK_ROWS[0].flag_offset]=None
        self.assertEqual(select_mage_attack(s).status,'needs_observation')

    def test_range_skipped_unknown_flags_do_not_block(self):
        r=next(r for r in MAGE_ATTACK_ROWS if r.distance_exclusive==38)
        s=snapshot(r,distance=30)
        for item in MAGE_ATTACK_ROWS:
            if item.distance_exclusive<=29: s.flags[item.flag_offset]=None
        self.assertEqual(select_mage_attack(s).row,r)

    def test_unknown_stat_and_timer(self):
        r=MAGE_ATTACK_ROWS[0]
        self.assertEqual(select_mage_attack(snapshot(r,raw_stats={})).reason,'stat:00462e08')
        self.assertEqual(select_mage_attack(snapshot(r,timer_values={})).reason,'timer:+50')

    def test_observation_order_mp_first_and_stat_first(self):
        r=MAGE_ATTACK_ROWS[0]
        self.assertEqual(select_mage_attack(snapshot(r,mp=0,raw_stats={})).status,'no_eligible_skill')
        r=next(r for r in MAGE_ATTACK_ROWS if r.flag_offset==0x84)
        self.assertTrue(r.stat_first)
        self.assertEqual(select_mage_attack(snapshot(r,mp=None,raw_stats={r.stat_reader:0})).status,'no_eligible_skill')

    def test_future_signed64_timer_and_clock_rollover_not_corrected(self):
        r=MAGE_ATTACK_ROWS[0]
        self.assertEqual(select_mage_attack(snapshot(r,timer_values={r.timer_offset:101000})).status,'no_eligible_skill')
        self.assertEqual(select_mage_attack(snapshot(r,now_ms=1000,timer_values={r.timer_offset:0xfffffff0})).status,'no_eligible_skill')

    def test_dword_next_timer_wraps_high_word_zero(self):
        r=MAGE_ATTACK_ROWS[0]
        d=select_mage_attack(snapshot(r,now_ms=0xfffffff0))
        self.assertEqual(d.local_timer_updates,((r.timer_offset,(0xfffffff0+r.cast_ms)&0xffffffff),))

    def test_initial_lock_and_unknown(self):
        self.assertEqual(select_mage_attack(snapshot(locked_561f7e=True)).status,'locked')
        self.assertEqual(select_mage_attack(snapshot(locked_561f7e=None)).status,'needs_observation')

    def test_invalid_types_and_ranges_rejected(self):
        for changes in ({'now_ms':True},{'now_ms':0x100000000},{'distance':float('nan')},
                        {'distance':float('inf')},{'distance':-1},{'distance':1e100},
                        {'mp':True},{'locked_561f7e':1},{'timer_values':{0x50:1<<63}},
                        {'configured_range':1<<31}):
            with self.subTest(changes=changes),self.assertRaises(ValueError): snapshot(**changes)


if __name__=='__main__': unittest.main()
