import unittest
from dataclasses import replace
from priest_attack import PriestAttackSnapshot, PRIEST_ATTACK_ROWS, select_priest_attack


class PriestAttackTests(unittest.TestCase):
    def snapshot(self, **changes):
        defaults = dict(now_ms=10000, distance=8, configured_range=8, mp=500,
                        flags={r.flag_offset: False for r in PRIEST_ATTACK_ROWS},
                        raw_stats={k: 100 for k in ('00462ddc', '00462e08', '00462e34',
                                                  '00462e60', '00462670')},
                        last_ms_by_offset={r.timer_offset: 0 for r in PRIEST_ATTACK_ROWS
                                           if r.timer_offset is not None}, locked_561f7e=False)
        defaults.update(changes)
        return PriestAttackSnapshot(**defaults)

    def enabled(self, *offsets, **changes):
        s = self.snapshot(**changes)
        return replace(s, flags={k: k in offsets for k in s.flags})

    def test_locked_precedes_missing_fields(self):
        s = self.snapshot(locked_561f7e=True, distance=None, flags={})
        self.assertEqual(select_priest_attack(s).status, 'locked')

    def test_unknown_lock(self):
        self.assertEqual(select_priest_attack(self.snapshot(locked_561f7e=None)).status,
                         'needs_observation')

    def test_range_equality_and_beyond(self):
        s = self.enabled(0x0a)
        self.assertEqual(select_priest_attack(s).status, 'local_attempt')
        self.assertEqual(select_priest_attack(replace(s, distance=8.001)).status, 'out_of_range')
        self.assertEqual(select_priest_attack(replace(s, configured_range=7)).status, 'out_of_range')

    def test_invalid_distance_and_lock(self):
        for values in ({'distance': float('nan')}, {'distance': -1}, {'locked_561f7e': 1}):
            with self.assertRaises(ValueError):
                self.snapshot(**values)

    def test_priority(self):
        self.assertEqual(select_priest_attack(self.enabled(0x0a, 0x0e, 0)).row.skill_number, 0x227)

    def test_timed_boundary_3050(self):
        s = self.enabled(0x0a, 0, now_ms=3049)
        self.assertEqual(select_priest_attack(s).row.helper, '004c856c')
        self.assertEqual(select_priest_attack(replace(s, now_ms=3050)).row.skill_number, 0x227)

    def test_timed_boundary_2050(self):
        s = self.enabled(0x09, 0, now_ms=2049)
        self.assertEqual(select_priest_attack(s).row.flag_offset, 0)
        self.assertEqual(select_priest_attack(replace(s, now_ms=2050)).row.flag_offset, 9)

    def test_stat_and_mp_boundaries(self):
        s = self.enabled(0x0a, 0, mp=120, raw_stats={'00462ddc': 51})
        self.assertEqual(select_priest_attack(s).row.flag_offset, 10)
        self.assertEqual(select_priest_attack(replace(s, mp=119)).row.flag_offset, 0)
        self.assertEqual(select_priest_attack(replace(s, raw_stats={'00462ddc': 50})).row.flag_offset, 0)

    def test_source_reader_anomaly(self):
        s = self.enabled(0x0f, raw_stats={'00462e08': 12, '00462e34': 0}, mp=30)
        self.assertEqual(select_priest_attack(s).row.skill_number, 0x2c8)
        self.assertEqual(select_priest_attack(replace(s, raw_stats={'00462e08': 11,
                                                                  '00462e34': 100})).status,
                         'no_eligible_skill')

    def test_unknown_earlier_flag_blocks_fallback(self):
        self.assertEqual(select_priest_attack(self.snapshot(flags={0: True})).reason, 'flag:+a')

    def test_timer_precedes_stat_unknown(self):
        s = self.enabled(0x0a, 0, now_ms=100, raw_stats={})
        self.assertEqual(select_priest_attack(s).row.flag_offset, 0)
        s = replace(s, now_ms=10000, last_ms_by_offset={})
        self.assertEqual(select_priest_attack(s).reason, 'timer:+2c')

    def test_unknown_eligible_stat_blocks_fallback(self):
        s = self.enabled(0x0a, 0, raw_stats={})
        self.assertEqual(select_priest_attack(s).reason, 'stat:00462ddc')

    def test_updates_timed_and_untimed(self):
        self.assertEqual(select_priest_attack(self.enabled(0x0a)).local_timer_updates,
                         ((0x120, 10000), (0x2c, 10000)))
        self.assertEqual(select_priest_attack(self.enabled(0x08)).local_timer_updates,
                         ((0x120, 10000),))

    def test_basic_fallback_has_no_stat_or_mp_requirement(self):
        s = self.enabled(0, raw_stats={}, mp=None)
        self.assertEqual(select_priest_attack(s).row.helper, '004c856c')

    def test_no_selection(self):
        self.assertEqual(select_priest_attack(self.snapshot()).status, 'no_eligible_skill')

    def test_future_timer_rejected(self):
        with self.assertRaises(ValueError):
            self.snapshot(last_ms_by_offset={0x2c: 10001})


if __name__ == '__main__':
    unittest.main()
