import unittest
from policies import weight_percent, weight_supply_due, stock_supply_due, MessageRow, MessageSequence


class PolicyTests(unittest.TestCase):
    def test_weight_integer_boundary(self):
        self.assertEqual(weight_percent(50, 101), 49)
        self.assertFalse(weight_supply_due(True, 50, 101, 50))
        self.assertTrue(weight_supply_due(True, 51, 101, 50))
        self.assertFalse(weight_supply_due(False, 99, 100, 50))

    def test_nonpositive_weight_denominator(self):
        self.assertEqual(weight_percent(50, 0), 0)
        self.assertEqual(weight_percent(50, -1), 0)

    def test_stock_thresholds(self):
        self.assertTrue(stock_supply_due('Arrow', 10))
        self.assertFalse(stock_supply_due('Arrow', 11))
        self.assertTrue(stock_supply_due('Potion', 2))
        self.assertFalse(stock_supply_due('Potion', 3))

    def test_message_order_waits_and_wrap(self):
        first, second = MessageRow('Merchant', 'A', 1), MessageRow('All Chat', 'B', 2)
        sequence = MessageSequence()
        sequence.start([first, second])
        self.assertIsNone(sequence.tick(999, 4))
        self.assertEqual(sequence.tick(1000, 4), first)
        self.assertIsNone(sequence.tick(2999, 4))
        self.assertEqual(sequence.tick(3000, 4), second)
        self.assertEqual(sequence.tick(4000, 4), first)

    def test_message_mode_guard_and_stop(self):
        sequence = MessageSequence()
        sequence.start([MessageRow('Merchant', 'A', 1)])
        self.assertIsNone(sequence.tick(2000, 0))
        self.assertEqual(sequence.index, 0)
        self.assertIsNotNone(sequence.tick(2001, 4))
        sequence.stop()
        self.assertEqual((sequence.index, sequence.rows, sequence.last_action), (0, (), 0))
        self.assertIsNone(sequence.tick(3000, 4))

    def test_message_zero_time_and_initial_timestamp(self):
        sequence = MessageSequence()
        sequence.start([MessageRow('Merchant', 'A', 5)])
        self.assertIsNotNone(sequence.tick(100000, 4))
        self.assertIsNone(sequence.tick(104999, 4))

    def test_message_validation_and_clock(self):
        with self.assertRaises(ValueError):
            MessageRow('unknown', 'A', 1)
        sequence = MessageSequence()
        sequence.start([MessageRow('Merchant', 'A', 1)])
        sequence.tick(1000, 4)
        with self.assertRaises(ValueError):
            sequence.tick(999, 4)
        self.assertEqual(sequence.last_action, 1000)
