import unittest
from upgrade_scroll import UpgradeScrollSample, UpgradeScrollObservation, plan_upgrade_scroll
from mining_slot_name import SlotNameObservation
from operation_engine import UpgradeRunner, UpgradeRow, UpgradeSnapshot


class UpgradeScrollTests(unittest.TestCase):
    def samples(self, hit=None, key=b'Scroll'):
        return {slot: UpgradeScrollSample(key, key if slot == hit else b'other') for slot in range(14, 42)}

    def test_first_match_and_relative_not_absolute_slot(self):
        samples = self.samples(16)
        samples[17] = object()  # Unreached data must not be examined.
        p = plan_upgrade_scroll(UpgradeScrollObservation(samples))
        self.assertEqual((p.complete, p.relative_index, p.visited_slots), (True, 2, (14, 15, 16)))
        self.assertFalse(p.independently_verified)

    def test_last_slot_and_exhaustive_absence(self):
        p = plan_upgrade_scroll(UpgradeScrollObservation(self.samples(41)))
        self.assertEqual(p.relative_index, 27)
        p = plan_upgrade_scroll(UpgradeScrollObservation(self.samples()))
        self.assertEqual((p.relative_index, len(p.visited_slots), len(p.calls)), (-1, 28, 84))

    def test_missing_slot_or_name_is_not_absence(self):
        for sample, status in ((None, 'needs_key_conversion'), (UpgradeScrollSample(b'Scroll'), 'needs_slot_name')):
            samples = self.samples()
            samples[20] = sample
            p = plan_upgrade_scroll(UpgradeScrollObservation(samples))
            self.assertEqual((p.complete, p.relative_index, p.status), (False, None, status))
            self.assertEqual(p.visited_slots[-1], 20)

    def test_empty_key_matches_real_empty_slot(self):
        p = plan_upgrade_scroll(UpgradeScrollObservation({14: UpgradeScrollSample(b'', b'')}))
        self.assertEqual(p.relative_index, 0)

    def test_ansi_length_case_and_nul_are_preserved(self):
        samples = self.samples()
        samples[14] = UpgradeScrollSample(b'Scroll', b'scroll')
        samples[15] = UpgradeScrollSample(b'Scroll', b'Scroll\0')
        samples[16] = UpgradeScrollSample(b'Scroll\0x', b'Scroll\0x')
        p = plan_upgrade_scroll(UpgradeScrollObservation(samples))
        self.assertEqual(p.relative_index, 2)

    def test_key_conversion_is_observed_per_iteration(self):
        samples = {14: UpgradeScrollSample(b'first', b'second'),
                   15: UpgradeScrollSample(b'second', b'second')}
        p = plan_upgrade_scroll(UpgradeScrollObservation(samples))
        self.assertEqual(p.relative_index, 1)
        self.assertEqual(p.calls, (('004073a0', 14), ('00463670', 14), ('00505118', 14),
                                   ('004073a0', 15), ('00463670', 15), ('00505118', 15)))

    def test_bound_empty_slot_helper_and_unknown_root(self):
        empty = SlotNameObservation(global_553e80=0x1000, offset_5540a8=4,
                                   offset_5540ac=8, root=0x2000, inventory=0x3000, record=0)
        p = plan_upgrade_scroll(UpgradeScrollObservation({14: UpgradeScrollSample(b'', slot_name_inputs=empty)}))
        self.assertEqual((p.relative_index, p.slot_name_plans[0][1].status), (0, 'empty_slot'))
        p = plan_upgrade_scroll(UpgradeScrollObservation({14: UpgradeScrollSample(b'', slot_name_inputs=SlotNameObservation())}))
        self.assertFalse(p.complete)
        self.assertIn('global_553e80', p.slot_name_plans[0][1].missing)

    def test_capture_and_bound_helper_conflict_only_when_reached(self):
        sample = UpgradeScrollSample(b'Scroll', b'Scroll', SlotNameObservation())
        with self.assertRaises(ValueError):
            plan_upgrade_scroll(UpgradeScrollObservation({14: sample}))
        p = plan_upgrade_scroll(UpgradeScrollObservation({14: UpgradeScrollSample(b'x', b'x'), 15: sample}))
        self.assertTrue(p.complete)

    def runner(self):
        r = UpgradeRunner(100, source_clock=True)
        r.start((UpgradeRow(11),), initial_stamp_qword=0)
        return r

    def test_runner_refresh_keeps_queue_and_stamp_and_stops_only_on_known_absence(self):
        r = self.runner()
        p = r.tick(UpgradeSnapshot(100, False, scroll_lookup=UpgradeScrollObservation(self.samples(16))))
        self.assertEqual((p.status, r.source_scroll_index, r.queue, r.queue_stamp_qword), ('blocked', 2, (11,), 0))
        p = r.tick(UpgradeSnapshot(101, False, scroll_lookup=UpgradeScrollObservation(self.samples())))
        self.assertEqual((p.reason, r.source_scroll_index, r.state, r.queue), ('scroll_unavailable', -1, 0, (11,)))

    def test_runner_gap_is_not_unavailable_and_scan_is_lazy(self):
        r = self.runner()
        empty = UpgradeScrollObservation()
        self.assertEqual(r.tick(UpgradeSnapshot(99, False, 0, scroll_lookup=empty)).status, 'waiting')
        self.assertIsNone(r.scroll_lookup_plan)
        self.assertEqual(r.tick(UpgradeSnapshot(100, False, scroll_lookup=empty)).status, 'needs_scroll_lookup')
        self.assertEqual((r.state, r.source_scroll_index, r.queue), (1, None, (11,)))
        with self.assertRaises(ValueError):
            r.tick(UpgradeSnapshot(100, False, 0, scroll_lookup=empty))
        self.assertEqual(r.tick(UpgradeSnapshot(100, True, 0, scroll_lookup=empty)).status, 'needs_helper_return')

    def test_typed_mapping_and_captured_bytes(self):
        for data in ({13: None}, {42: None}, {True: None}):
            with self.assertRaises(ValueError):
                UpgradeScrollObservation(data)
        with self.assertRaises(ValueError):
            UpgradeScrollSample('Scroll', b'')
        p = UpgradeScrollObservation(self.samples())
        with self.assertRaises(TypeError):
            p.samples[14] = None
