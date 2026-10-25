import unittest
from operation_engine import UpgradeRunner, UpgradeRow, UpgradeSnapshot


class UpgradeClockTests(unittest.TestCase):
    def runner(self, interval=2000, stamp=0):
        r = UpgradeRunner(interval, 42, source_clock=True)
        r.start((UpgradeRow(11), UpgradeRow(22)), initial_stamp_qword=stamp)
        return r

    def complete(self, r, tick, stamp_tick):
        return r.tick(UpgradeSnapshot(tick, True, source_helper_returned=True,
                                      source_stamp_tick_dword=stamp_tick))

    def test_missing_initial_stamp_is_not_start_clock_or_zero(self):
        r = self.runner(stamp=None)
        self.assertEqual(r.tick(UpgradeSnapshot(9999, True)).status, 'needs_initial_stamp')
        self.assertEqual(r.queue, (11, 22))

    def test_signed_interval_boundaries(self):
        for interval in (0, 0xffffffff, 0x80000000):
            r = self.runner(interval)
            self.assertEqual(self.complete(r, 0, 1).status, 'attempt')
        r = self.runner(0x7fffffff)
        self.assertEqual(r.tick(UpgradeSnapshot(0x7ffffffe)).status, 'waiting')
        self.assertEqual(self.complete(r, 0x7fffffff, 0x80000001).status, 'attempt')

    def test_raw_tick_rollover_is_not_unsigned_dword_elapsed(self):
        r = self.runner(100, 0xfffffff0)
        p = r.tick(UpgradeSnapshot(0x54, True))
        self.assertEqual((p.status, p.remaining_ms), ('waiting', 4294967296))
        self.assertEqual(r.queue, (11, 22))

    def test_qword_stamp_signed_wrap(self):
        r = self.runner(100, 0xfffffffffffffff0)
        self.assertEqual(self.complete(r, 0x54, 0x55).status, 'attempt')
        self.assertEqual(r.queue_stamp_qword, 0x55)
        r = self.runner(0, 0x8000000000000001)
        self.assertEqual(self.complete(r, 0, 1).status, 'attempt')

    def test_fresh_post_helper_tick_controls_next_interval(self):
        r = self.runner()
        self.assertEqual(self.complete(r, 2000, 2500).status, 'attempt')
        self.assertEqual(r.tick(UpgradeSnapshot(4499)).remaining_ms, 1)
        self.assertEqual(self.complete(r, 4500, 4509).status, 'attempt')
        self.assertEqual(r.queue_stamp_qword, 4509)

    def test_missing_return_and_tick_freeze_prefix_and_resume_same_helper(self):
        r = self.runner(0)
        self.assertEqual(r.tick(UpgradeSnapshot(10, True)).status, 'needs_helper_return')
        self.assertEqual((r.queue, r.source_pending.queue_after), ((11, 22), (22,)))
        self.assertEqual(r.tick(UpgradeSnapshot(11, False, -1, source_helper_returned=True)).status,
                         'needs_stamp_tick')
        self.assertEqual(r.queue_stamp_qword, 0)
        # The reached helper already returned; fresh gates and absent return do
        # not restart its earlier part or dequeue a second record.
        p = r.tick(UpgradeSnapshot(12, False, -1, source_stamp_tick_dword=99))
        self.assertEqual((p.intents[0].item_id, r.queue, r.queue_stamp_qword), (11, (22,), 99))
        self.assertIsNone(r.source_pending)

    def test_non_normal_return_cannot_stamp_or_consume(self):
        r = self.runner(0)
        p = r.tick(UpgradeSnapshot(1, True, source_helper_returned=False, source_stamp_tick_dword=50))
        self.assertEqual(p.status, 'helper_did_not_return')
        self.assertEqual((r.queue, r.queue_stamp_qword), ((11, 22), 0))

    def test_armor_stamp_counter_and_limit_after_normal_return(self):
        r = self.runner()
        r.start_armor(initial_stamp_qword=0)
        r.armor_attempts = 42
        p = r.tick(UpgradeSnapshot(200, armor_distance=9, armor_blocked=False))
        self.assertEqual(p.status, 'needs_helper_return')
        self.assertEqual((r.armor_attempts, r.state), (42, 2))
        p = r.tick(UpgradeSnapshot(201, source_helper_returned=True, source_stamp_tick_dword=222))
        self.assertEqual((p.status, r.armor_attempts, r.state, r.armor_stamp_qword), ('attempt', 43, 0, 222))
        self.assertEqual(r.queue_stamp_qword, 0)

    def test_armor_counter_is_signed_dword_after_wrap(self):
        r = self.runner()
        r.start_armor(initial_stamp_qword=0)
        r.armor_attempts = 0xffffffff
        p = r.tick(UpgradeSnapshot(200, armor_distance=9, armor_blocked=False,
                                  source_helper_returned=True, source_stamp_tick_dword=201))
        self.assertEqual((p.status, r.armor_attempts, r.state), ('attempt', 0, 2))

    def test_source_start_preserves_existing_stamp_and_separates_modes(self):
        r = self.runner(0, 100)
        r.start_armor(initial_stamp_qword=200)
        r.start((UpgradeRow(33),), now_ms=9999)
        self.assertEqual((r.queue_stamp_qword, r.armor_stamp_qword), (100, 200))
        self.assertEqual(r.tick(UpgradeSnapshot(99, True)).status, 'waiting')
        with self.assertRaises(ValueError):
            r.tick(UpgradeSnapshot(1 << 32))
        with self.assertRaises(ValueError):
            UpgradeRunner(1 << 32, source_clock=True)
        with self.assertRaises(ValueError):
            UpgradeSnapshot(0, source_helper_returned=1)
