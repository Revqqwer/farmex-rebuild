import unittest
from routes import RouteRunner, RouteStep
from special_routes import SpecialRouteSnapshot
from npc_route_engine import NpcRouteFrame, NpcRouteObservation


class NpcIntegrationTests(unittest.TestCase):
    def runner(self):
        runner=RouteRunner();runner.start([RouteStep('NPC',parameter1='Potion')])
        runner.tick(0)
        runner.tick(1,special_observation=SpecialRouteSnapshot(1,actor_raw_byte_554020=0))
        return runner

    def test_inner_completion_advances_route(self):
        runner=self.runner()
        result=runner.tick(2,special_observation=SpecialRouteSnapshot(2),
                           npc_observation=NpcRouteObservation(NpcRouteFrame(9),{'Royal National Enchanter':False}))
        self.assertEqual(result.kind,'step_complete')
        self.assertEqual(runner.npc_result.frame.phase,11)
        self.assertEqual(runner.tick(3).kind,'finished')

    def test_missing_lookup_keeps_route_processing(self):
        runner=self.runner()
        r=runner.tick(2,special_observation=SpecialRouteSnapshot(2),
                      npc_observation=NpcRouteObservation(NpcRouteFrame(1),{'Potion':True}))
        self.assertEqual(r.kind,'needs_observation');self.assertTrue(runner.processing)
        self.assertEqual(runner.npc_result.frame.phase,1)

    def test_rejects_conflicting_helper_outcome(self):
        runner=self.runner()
        with self.assertRaises(ValueError):
            runner.tick(2,special_observation=SpecialRouteSnapshot(2,npc_helper_return_4f11a0=True),
                        npc_observation=NpcRouteObservation(NpcRouteFrame(1),{}))

    def test_potion_route_from_lookup_to_completion_uses_returned_frames(self):
        runner=self.runner()
        frame=NpcRouteFrame(1,{0x604:0,0x650:0,0x556:0,0x689:0,0x18:0},
                              {0x553fec:12,0x553fe8:8,0x56fae4:0,0x561f58:0})
        matches={kind:kind=='Potion' for kind in ('Potion','Sundries','Armor','Weapon',
                  'DC Sundries','Inn Hostess','Royal National Enchanter')}
        helpers={'00465960:otion':8,'00464a10':0x100000,'0045dc44:raw_field_fec':10,
                 '004fe384':0,'004eebf4':43}
        observed_phases=[]
        for now in range(2,12):
            result=runner.tick(now,special_observation=SpecialRouteSnapshot(now),
                               npc_observation=NpcRouteObservation(frame,matches,helpers,
                                                                  observed_text='fixture ANSI conversion output'))
            frame=runner.npc_result.frame
            observed_phases.append(frame.phase)
            if result.kind=='step_complete':break
            self.assertEqual(result.kind,'waiting')
        self.assertEqual(observed_phases,[2,3,4,4,5,6,7,8,9,11])
        self.assertEqual(frame.texts[0x610],'fixture ANSI conversion output')
        self.assertEqual(frame.texts[0x608],'Potion')
        self.assertEqual(result.kind,'step_complete')
