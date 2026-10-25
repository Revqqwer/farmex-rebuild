import unittest
from dataclasses import replace
from repair_engine import RepairObservation, repair_step
from npc_route_engine import NpcRouteFrame, npc_route_step


class RepairTests(unittest.TestCase):
    def fields(self,phase=1,wait=0,start=0):
        return {0x640:phase,0x644:wait,0x648:start,0x64c:0,0x604:8,0x60c:0x100000,0x555:1}

    def observation(self,**changes):
        return replace(RepairObservation(1000,current_target=8,candidate_count_4edc40=1,
                      item_id_4634a4=1,durability_46358c=1,maximum_4635e0=100,
                      producer_item_id_4634a4=1),**changes)

    def test_equipment_skip_chain_with_empty_items(self):
        fields=self.fields(1);seen=[]
        for _ in range(7):
            r=repair_step(fields,{},self.observation(item_id_4634a4=0))
            seen.append(r.returned_phase);fields=r.fields
        self.assertEqual(seen,[4,6,8,10,12,13,14])

    def test_phase0_candidate_zero_finishes42(self):
        r=repair_step(self.fields(0),{},self.observation(candidate_count_4edc40=0))
        self.assertEqual(r.returned_phase,42);self.assertEqual(r.calls,('004edc40',))

    def test_target_select_and_interact_then_wait(self):
        r=repair_step(self.fields(0),{},self.observation())
        self.assertEqual(r.calls,('004edc40','0046493c','0046fb38'))
        self.assertEqual(r.fields[0x644],1)

    def test_current_target_required_even_at_phase0(self):
        r=repair_step(self.fields(0),{},self.observation(current_target=None))
        self.assertEqual(r.status,'needs_observation');self.assertEqual(r.calls,())

    def test_equipment_damage_sets_shared_ack_and_slot(self):
        r=repair_step(self.fields(12),{},self.observation())
        self.assertEqual(r.globals[0x561fb0],0xffffffff)
        self.assertEqual((r.globals[0x561fab],r.globals[0x561fac]),(1,12))
        self.assertIn('004c8fdc',r.calls);self.assertEqual(r.returned_phase,12)

    def test_durability_equal_or_greater_skips(self):
        for durability in (100,101,0xffffffff):
            r=repair_step(self.fields(),{},self.observation(durability_46358c=durability))
            self.assertEqual(r.returned_phase,4);self.assertNotIn('004c8fdc',r.calls)

    def test_timer1000_boundary_and_ack_not_received(self):
        fields=self.fields(1,1,1000)
        globals={0x553e44:0,0x561fb0:0xffffffff}
        r=repair_step(fields,globals,self.observation(now_ms=1999))
        self.assertEqual(r.status,'waiting')
        r=repair_step(fields,globals,self.observation(now_ms=2000))
        self.assertEqual(r.status,'waiting_ack');self.assertEqual(r.fields[0x644],1)

    def test_timer200_boundary_and_ack_clears_wait(self):
        fields=self.fields(1,1,1000);globals={0x553e44:1,0x561fb0:0}
        self.assertEqual(repair_step(fields,globals,self.observation(now_ms=1199)).returned_phase,1)
        r=repair_step(fields,globals,self.observation(now_ms=1200))
        self.assertEqual(r.returned_phase,4);self.assertEqual(r.fields[0x644],0)

    def test_phase0_after_wait_advances_to1(self):
        r=repair_step(self.fields(0,1),{0x553e44:0,0x561fb0:0},self.observation())
        self.assertEqual(r.returned_phase,1)

    def test_dword_wrap_preserves_signed_qword_wait(self):
        r=repair_step(self.fields(1,1,0xfffffff0),{0x553e44:1},self.observation(now_ms=500))
        self.assertEqual(r.status,'waiting')

    def test_inventory_disabled_starts41_wait(self):
        fields=self.fields(14);fields[0x555]=0
        r=repair_step(fields,{0x56fad3:0,0x56fade:0},self.observation())
        self.assertEqual(r.returned_phase,41);self.assertEqual(r.fields[0x644],1)

    def test_mode0_cache_selects_inventory_request2(self):
        r=repair_step(self.fields(14),{0x561f58:0},self.observation(mode0_cache_match=True))
        self.assertEqual(r.globals[0x561fab],2);self.assertIn('004c9078',r.calls)

    def test_mode0_nonmatch_advances_directly(self):
        r=repair_step(self.fields(14),{0x561f58:0},self.observation(mode0_cache_match=False))
        self.assertEqual(r.returned_phase,15);self.assertEqual(r.fields[0x644],0)

    def test_mode2_first_true_short_circuits_second_unknown(self):
        r=repair_step(self.fields(14),{0x561f58:2},self.observation(mode2_type_matches=(True,None)))
        self.assertEqual(r.status,'waiting');self.assertEqual(r.globals[0x561fab],2)

    def test_mode2_second_unknown_is_required_after_first_false(self):
        r=repair_step(self.fields(14),{0x561f58:2},self.observation(mode2_type_matches=(False,None)))
        self.assertEqual(r.status,'needs_observation');self.assertNotIn(0x561fb0,r.globals)

    def test_parent_npc_advances4_when_no_repair_candidates(self):
        fields=self.fields(0);fields[0x63c]=1
        r=npc_route_step(NpcRouteFrame(3,fields,{0x561f58:0}),{'Sundries':True},
                         repair_observation=self.observation(candidate_count_4edc40=0))
        self.assertEqual(r.frame.phase,4);self.assertEqual((r.frame.fields[0x640],r.frame.fields[0x63c]),(0,0))

    def test_parent_preserves_repair_pending_ack(self):
        fields=self.fields(1,1,1000);fields[0x63c]=1
        r=npc_route_step(NpcRouteFrame(3,fields,{0x561f58:0,0x553e44:0,0x561fb0:0xffffffff}),
                         {'Sundries':True},repair_observation=self.observation(now_ms=2000))
        self.assertEqual(r.frame.phase,3);self.assertEqual(r.frame.fields[0x644],1)
