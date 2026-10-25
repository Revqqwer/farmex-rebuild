import unittest
from game_provider import Observation, validate_vitals, ReadOnlyGameProvider
from session import Source, Snapshot, Session, observation_snapshot


class SessionTests(unittest.TestCase):
    def test_unknown_and_stale_observations_block_start(self):
        session = Session('A')
        self.assertEqual(session.start(0), 'needs_fresh_snapshot')
        session.accept_snapshot(Snapshot('A', Source.SIMULATION, 10, {'hp': None}))
        self.assertEqual(session.start(11, ['hp']), 'needs_fields')
        self.assertEqual(session.start(1011), 'needs_fresh_snapshot')

    def test_candidate_read_does_not_enable_live_start(self):
        candidate = Observation('candidate', timestamp_ms=10, fields={'hp': 50})
        session = Session('A', Source.LIVE)
        session.accept_snapshot(observation_snapshot(candidate, 'A'))
        self.assertEqual(session.start(10, ['hp']), 'needs_verification')

    def test_simulation_is_not_acknowledgement(self):
        session = Session('A')
        session.accept_snapshot(Snapshot('A', Source.SIMULATION, 10, {'hp': 50}))
        self.assertEqual(session.start(10, ['hp']), 'started')
        result = session.issue('potion', 11)
        self.assertEqual(result['status'], 'simulated')
        self.assertFalse(result['acknowledged'])
        session.target_id = 12
        session.disconnect()
        self.assertEqual((session.snapshot, session.target_id, session.pending), (None, None, {}))

    def test_mixed_sources_and_regression_rejected(self):
        session = Session('A')
        with self.assertRaises(ValueError):
            session.accept_snapshot(Snapshot('A', Source.LIVE, 10))
        session.accept_snapshot(Snapshot('A', Source.SIMULATION, 10))
        with self.assertRaises(ValueError):
            session.accept_snapshot(Snapshot('A', Source.SIMULATION, 9))

    def test_expired_snapshot_stops_and_clears_pending(self):
        session = Session('A')
        session.accept_snapshot(Snapshot('A', Source.SIMULATION, 10))
        session.start(10)
        session.issue('move', 20)
        self.assertEqual(session.issue('move', 1011)['status'], 'stale')
        self.assertFalse(session.active)
        self.assertEqual(session.pending, {})

    def test_live_transport_explicitly_unavailable(self):
        provider = ReadOnlyGameProvider()
        self.assertEqual(provider.submit('move')['status'], 'unavailable')
        session = Session('A', Source.LIVE)
        session.accept_snapshot(Snapshot('A', Source.LIVE, 10, verified=True))
        session.start(10)
        self.assertEqual(session.issue('move', 10)['status'], 'unavailable')

    def test_vital_sanity_and_no_unavailable_to_snapshot_conversion(self):
        good = {'hp': 0, 'hp_max': 100, 'mp': 50, 'mp_max': 100}
        self.assertEqual(validate_vitals(good), good)
        with self.assertRaises(ValueError):
            validate_vitals(dict(good, hp=101))
        self.assertIsNone(observation_snapshot(Observation('unavailable'), 'A'))


if __name__ == '__main__':
    unittest.main()
