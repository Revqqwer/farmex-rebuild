import unittest
from routes import RouteStep, RouteRunner, route_to_data, route_from_data


class RouteTests(unittest.TestCase):
    def test_selection_is_separate_from_movement(self):
        runner = RouteRunner()
        runner.start([RouteStep('Koordinat', 12, 34)])
        self.assertEqual(runner.tick(0, 10).kind, 'selected')
        decision = runner.tick(1, 10)
        self.assertEqual((decision.kind, decision.x, decision.y), ('move', 12, 34))

    def test_distance_boundary_and_completion(self):
        runner = RouteRunner()
        runner.start([RouteStep('Koordinat', 12, 34)])
        runner.tick(0)
        self.assertEqual(runner.tick(1, 2.0001).kind, 'move')
        self.assertEqual(runner.tick(2, 2.0).kind, 'step_complete')
        self.assertEqual(runner.tick(3).kind, 'finished')
        self.assertFalse(runner.active)

    def test_movement_guard_preserves_step(self):
        runner = RouteRunner()
        runner.start([RouteStep('Koordinat', 0, 0)])
        runner.tick(0)
        self.assertEqual(runner.tick(1, 0, True).kind, 'blocked')
        self.assertTrue(runner.processing)
        self.assertEqual(runner.tick(2).kind, 'needs_distance')

    def test_wait_seconds_and_inclusive_expiry(self):
        runner = RouteRunner()
        runner.start([RouteStep('Bekle', seconds=2)])
        runner.tick(0)
        self.assertEqual(runner.tick(100).remaining_ms, 2000)
        self.assertEqual(runner.tick(2099).remaining_ms, 1)
        self.assertEqual(runner.tick(2100).kind, 'step_complete')

    def test_multiple_steps_do_not_overlap(self):
        runner = RouteRunner()
        runner.start([RouteStep('Bekle', seconds=0), RouteStep('Koordinat', 1, 2)])
        self.assertEqual(runner.tick(0).index, 0)
        self.assertEqual(runner.tick(1).kind, 'waiting')
        self.assertEqual(runner.tick(2).kind, 'step_complete')
        self.assertEqual(runner.tick(3).kind, 'selected')
        self.assertEqual(runner.tick(4, 0).kind, 'step_complete')
        self.assertEqual(runner.tick(5).kind, 'finished')

    def test_stop_clears_pending_wait_and_restart(self):
        runner = RouteRunner()
        route = [RouteStep('Bekle', seconds=2)]
        runner.start(route)
        runner.tick(0)
        runner.tick(100)
        runner.stop()
        self.assertEqual((runner.index, runner.wait_started, runner.steps), (-1, None, ()))
        self.assertEqual(runner.tick(300).kind, 'inactive')
        runner.start(route)
        self.assertEqual(runner.tick(0).kind, 'selected')
        self.assertEqual(runner.tick(1).remaining_ms, 2000)

    def test_invalid_start_stops_previous_run(self):
        runner = RouteRunner()
        runner.start([RouteStep('Bekle', seconds=1)])
        with self.assertRaises(ValueError):
            runner.start([])
        self.assertFalse(runner.active)

    def test_invalid_parameters_and_unsupported_command(self):
        for factory in [lambda: RouteStep('Unknown Command'), lambda: RouteStep('Bekle', seconds=-1),
                        lambda: RouteStep('Bekle', seconds=True),
                        lambda: RouteStep('Koordinat', float('nan'), 1)]:
            with self.assertRaises(ValueError):
                factory()

    def test_clock_regression_is_rejected_without_progress(self):
        runner = RouteRunner()
        runner.start([RouteStep('Bekle', seconds=1)])
        runner.tick(100)
        with self.assertRaises(ValueError):
            runner.tick(99)
        self.assertIsNone(runner.wait_started)
        self.assertEqual(runner.tick(101).remaining_ms, 1000)

    def test_route_schema_and_roundtrip(self):
        route = [RouteStep('Koordinat', 1.5, 7), RouteStep('Bekle', seconds=3)]
        self.assertEqual(route_from_data(route_to_data(route)), route)
        for data in [{'version': True, 'steps': []}, {'version': 1, 'steps': [
                     {'command': 'Koordinat', 'x': 1, 'y': 2, 'extra': 3}]},
                     {'version': 1, 'steps': [{'command': 'Town', 'seconds': 3}]}]:
            with self.assertRaises(ValueError):
                route_from_data(data)


if __name__ == '__main__':
    unittest.main()
