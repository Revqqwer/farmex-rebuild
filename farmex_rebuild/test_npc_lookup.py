import unittest
from npc_lookup import NpcCandidate, select_npc
from npc_route_engine import NpcRouteFrame, npc_route_step


class NpcLookupTests(unittest.TestCase):
    def select(self,rows,filter=b'otion',**changes):
        return select_npc(rows,filter,traversal_complete=changes.get('complete',True))

    def test_nearest_case_sensitive_substring_in_source_order(self):
        rows=[NpcCandidate(2,1,b'POTION'),NpcCandidate(70,2,b'[Potion] Vendor'),
              NpcCandidate(3,3,b'Potion Seller')]
        r=self.select(rows);self.assertEqual(r.candidate_id,3);self.assertEqual(r.distance_integer,3)

    def test_exact80_excluded79_accepted(self):
        r=self.select([NpcCandidate(80),NpcCandidate(79,4,b'Potion')])
        self.assertEqual(r.candidate_id,4)

    def test_equal_distance_keeps_first_and_does_not_read_later_id(self):
        r=self.select([NpcCandidate(5,7,b'Potion'),NpcCandidate(5)])
        self.assertEqual(r.candidate_id,7);self.assertEqual(r.status,'complete')

    def test_nearer_nonmatch_does_not_reduce_radius(self):
        r=self.select([NpcCandidate(1,2,b'Sundries'),NpcCandidate(70,3,b'Potion')])
        self.assertEqual(r.candidate_id,3)

    def test_matching_zero_id_still_reduces_distance(self):
        r=self.select([NpcCandidate(1,0,b'Potion'),NpcCandidate(2,5,b'Potion')])
        self.assertEqual(r.candidate_id,0);self.assertEqual(r.distance_integer,1)

    def test_signed_minimum_observation_not_replaced_by_float(self):
        r=self.select([NpcCandidate(-0x80000000,9,b'Potion')])
        self.assertEqual(r.candidate_id,9)

    def test_nul_termination_and_empty_filter(self):
        self.assertEqual(self.select([NpcCandidate(1,2,b'Other\0Potion')]).candidate_id,0)
        self.assertEqual(self.select([NpcCandidate(1,2,b'')],b'').candidate_id,2)

    def test_incomplete_iterator_never_claims_final_id(self):
        r=self.select([NpcCandidate(1,2,b'Potion')],complete=False)
        self.assertEqual(r.status,'needs_observation');self.assertEqual(r.candidate_id,2)

    def test_unknown_id_or_name_needs_observation_after_distance_gate(self):
        for row in (NpcCandidate(),NpcCandidate(1),NpcCandidate(1,2)):
            self.assertEqual(self.select([row]).status,'needs_observation')
        self.assertEqual(self.select([NpcCandidate(80)]).status,'complete')

    def test_route_phase1_consumes_selector_observations(self):
        r=npc_route_step(NpcRouteFrame(1),{'Potion':True},
                         lookup_candidates=[NpcCandidate(8,17,b'Potion')],lookup_traversal_complete=True)
        self.assertEqual(r.frame.phase,2);self.assertEqual(r.frame.fields[0x604],17)

    def test_route_phase1_incomplete_lookup_stays_in_phase1(self):
        r=npc_route_step(NpcRouteFrame(1),{'Potion':True},
                         lookup_candidates=[NpcCandidate(8,17,b'Potion')],lookup_traversal_complete=False)
        self.assertEqual(r.frame.phase,1);self.assertEqual(r.status,'needs_observation')

    def test_conflicting_lookup_helper_rejected(self):
        with self.assertRaises(ValueError):
            npc_route_step(NpcRouteFrame(1),{'Potion':True},{'00465960:otion':2},
                           lookup_candidates=[],lookup_traversal_complete=True)
