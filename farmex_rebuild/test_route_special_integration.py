import unittest
from routes import RouteStep, RouteRunner, route_to_data, route_from_data
from special_routes import SpecialRouteSnapshot, SpecialRouteState


class RouteSpecialIntegrationTests(unittest.TestCase):
    def ready(self, now):
        return SpecialRouteSnapshot(now, actor_raw_byte_554020=0, hp_4611a0=100,
                                    max_hp_4611c0=100, npc_helper_return_4f11a0=True)

    def test_mixed_v2_roundtrip_preserves_npc_text(self):
        rows = [RouteStep('Town'), RouteStep('NPC', parameter1='Sundries', parameter2='Al'),
                RouteStep('Koordinat', 10, 20), RouteStep('Bekle', seconds=0)]
        data = route_to_data(rows)
        self.assertEqual(data['version'], 2)
        self.assertEqual(route_from_data(data), rows)

    def test_legacy_route_stays_v1(self):
        self.assertEqual(route_to_data([RouteStep('Bekle', seconds=1)])['version'], 1)

    def test_v1_cannot_smuggle_special_command(self):
        with self.assertRaises(ValueError):
            route_from_data({'version': 1, 'steps': [{'command': 'Town', 'seconds': None}]})

    def test_no_observation_does_not_guess_health(self):
        r = RouteRunner()
        r.start([RouteStep('Town')])
        self.assertEqual(r.tick(0).kind, 'selected')
        outcome = r.tick(1)
        self.assertEqual(outcome.kind, 'needs_observation')
        self.assertTrue(r.processing)

    def test_town_then_wait_and_finished(self):
        r = RouteRunner()
        r.start([RouteStep('Town'), RouteStep('Bekle', seconds=0)])
        r.tick(0)
        self.assertEqual(r.tick(1, special_observation=self.ready(1)).kind, 'started')
        self.assertEqual(r.tick(2000, special_observation=self.ready(2000)).kind, 'waiting')
        self.assertEqual(r.tick(2001, special_observation=self.ready(2001)).kind, 'step_complete')
        self.assertEqual(r.tick(2002).kind, 'selected')
        r.tick(2003)
        r.tick(2004)
        self.assertEqual(r.tick(2005).kind, 'finished')

    def test_special_selection_resets_previous_phase(self):
        r = RouteRunner()
        r.start([RouteStep('Otur'), RouteStep('Kalk')])
        r.tick(0)
        r.tick(1, special_observation=self.ready(1))
        r.tick(2001, special_observation=self.ready(2001))
        r.tick(2002)
        self.assertEqual(r.special_state, SpecialRouteState())

    def test_gate_plan_has_payload_but_no_io(self):
        r = RouteRunner()
        r.start([RouteStep('Gate Open', parameter1='5')])
        r.tick(0)
        result = r.tick(1, special_observation=self.ready(1))
        self.assertEqual(result.queue_payloads, (bytes.fromhex('3305000000'),))

    def test_gate_skill_needs_no_parameter_and_gate_parses_signed_value(self):
        for row,expected in ((RouteStep('Gate Skill'),()),(RouteStep('Gate',parameter1='-1'),(bytes.fromhex('4bffffffff'),))):
            r=RouteRunner();r.start([row]);r.tick(0)
            result=r.tick(1,special_observation=self.ready(1))
            self.assertEqual(result.kind,'started');self.assertEqual(result.queue_payloads,expected)
            if row.command=='Gate Skill':self.assertEqual(result.calls,('004c8d84',))

    def test_gate_parser_is_deferred_until_actor_gate_reached(self):
        r=RouteRunner();r.start([RouteStep('Gate Open',parameter1='not numeric')]);r.tick(0)
        blocked=r.tick(1,special_observation=SpecialRouteSnapshot(1,actor_raw_byte_554020=1))
        self.assertEqual(blocked.kind,'blocked')
        unknown=r.tick(2,special_observation=SpecialRouteSnapshot(2))
        self.assertEqual(unknown.kind,'needs_observation')
        with self.assertRaises(ValueError):r.tick(3,special_observation=self.ready(3))

    def test_gate_wait_does_not_parse_parameter_again(self):
        r=RouteRunner();r.start([RouteStep('Gate Open',parameter1='not numeric')]);r.tick(0)
        r.special_state=SpecialRouteState(started=True,started_qword=0)
        self.assertEqual(r.tick(1499,special_observation=self.ready(1499)).kind,'waiting')
        self.assertEqual(r.tick(1500,special_observation=self.ready(1500)).kind,'step_complete')

    def test_wrong_observation_clock_rejected(self):
        r = RouteRunner()
        r.start([RouteStep('Town')])
        r.tick(0)
        with self.assertRaises(ValueError):
            r.tick(1, special_observation=self.ready(2))

    def test_stop_clears_special_state(self):
        r = RouteRunner()
        r.start([RouteStep('Town')])
        r.tick(0)
        r.tick(1, special_observation=self.ready(1))
        r.stop()
        self.assertEqual(r.special_state, SpecialRouteState())

    def test_randomize_parameter_compiles_to_change_camp_path(self):
        r = RouteRunner()
        r.start([RouteStep('Change Camp', parameter1='Randomize')])
        r.tick(0)
        result = r.tick(1, special_observation=self.ready(1))
        self.assertIn('004c8a98', result.calls)


if __name__ == '__main__':
    unittest.main()
