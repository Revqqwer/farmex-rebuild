import struct
import unittest
from crt_startup import StartupTables, decode_startup_records, replay_startup_dispatch


class StartupTests(unittest.TestCase):
    def table(self, descriptor, base, entries):
        records = decode_startup_records(base, b''.join(struct.pack('<BBI', *x) for x in entries))
        return StartupTables(descriptor, records, records)

    def test_priority_before_descriptor_before_record(self):
        a = self.table(0x1000, 0x2000, [(0, 255, 1), (9, 32, 2), (0, 32, 3)])
        b = self.table(0x3000, 0x4000, [(0, 32, 4), (0, 0, 5)])
        p = replay_startup_dispatch((a, b), 0, stable_tables=True, normal_returns=(True,)*5)
        self.assertEqual([c.record.handler for c in p.calls_reached], [5, 2, 3, 4, 1])
        self.assertTrue(p.complete)

    def test_exit_keeps_descriptor_order_and_reverses_its_records(self):
        a = self.table(0x1000, 0x2000, [(0, 32, 1), (255, 32, 2), (0, 0, 3)])
        b = self.table(0x3000, 0x4000, [(0, 32, 4), (0, 255, 5)])
        p = replay_startup_dispatch((a, b), 0xffffffff, stable_tables=True, normal_returns=(True,)*5)
        self.assertEqual([c.record.handler for c in p.calls_reached], [5, 2, 1, 4, 3])

    def test_unknown_return_prevents_reaching_later_handler(self):
        a = self.table(0x1000, 0x2000, [(0, 0, 10), (0, 0, 11), (0, 0, 12)])
        p = replay_startup_dispatch((a,), 0, stable_tables=True, normal_returns=(True,))
        self.assertEqual([c.record.handler for c in p.calls_reached], [10, 11])
        self.assertEqual(p.calls_returned, 1)
        self.assertFalse(p.complete)
        p = replay_startup_dispatch((a,), 0, stable_tables=True, normal_returns=(False,))
        self.assertEqual([c.record.handler for c in p.calls_reached], [10])
        self.assertEqual(p.calls_returned, 0)

    def test_no_implicit_stability_or_live_execution(self):
        a = self.table(0x1000, 0x2000, [(0, 0, 1)])
        p = replay_startup_dispatch((a,), 0)
        self.assertFalse(p.complete)
        self.assertFalse(p.native_execution_verified)
        self.assertFalse(p.live_compatibility_verified)
        self.assertEqual(p.calls_reached, ())

    def test_empty_count_and_empty_tables(self):
        self.assertTrue(replay_startup_dispatch((), 0).complete)
        empty = StartupTables(0x1000, (), ())
        self.assertTrue(replay_startup_dispatch((empty,), 1, stable_tables=True).complete)

    def test_partial_wrapping_and_untyped_inputs_are_not_valid_snapshots(self):
        for base, raw in [(0, b'1'), (0xfffffffc, b'123456'), (True, b''), (0, bytearray())]:
            with self.assertRaises(ValueError):
                decode_startup_records(base, raw)
        with self.assertRaises(ValueError):
            replay_startup_dispatch((), True)
        with self.assertRaises(ValueError):
            replay_startup_dispatch((), 0, normal_returns=(True,))

    def test_prefix_and_null_handler_are_not_silent_filters(self):
        a = self.table(0x1000, 0x2000, [(255, 32, 0)])
        p = replay_startup_dispatch((a,), 0, stable_tables=True)
        self.assertFalse(p.complete)
        self.assertEqual(p.calls_reached[0].record.handler, 0)
        self.assertEqual(p.missing, 'handler normal return')
