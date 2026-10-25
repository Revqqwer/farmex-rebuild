import unittest
from dataclasses import replace
from npc_buy_engine import NpcBuyState,NpcBuyObservation,NpcBuyRouteRow,npc_buy_step
from npc_buy_packets import NpcBuyRecord,NpcBuyPacketObservation,BUY_VENDORS
from npc_sell_packets import SellCacheSlot
from npc_route_engine import NpcRouteFrame,npc_route_step

class BuyEngineTests(unittest.TestCase):
    def record(self):return NpcBuyRecord(100,5,2,3,1,1)
    def state(self,phase=0,count=1,batch=()):
        return NpcBuyState({0x690:phase,0x68c:count,0x694:0,0x698:0,0x69c:0,0x604:9,0x60c:0x100000},batch)
    def obs(self,**changes):
        return replace(NpcBuyObservation(1000,9,NpcBuyRouteRow(1,0x3e418,self.record()),
                      {'Sundries':True}),**changes)
    def packets(self):
        return NpcBuyPacketObservation(0,1000,{name:name=='Sundries' for name,v in BUY_VENDORS},
                     {slot:SellCacheSlot(0,0,0) for slot in range(14,42)},{0:1000})

    def test_minus_one_clears_batch_and_selects_without_interaction(self):
        r=npc_buy_step(self.state(0xffffffff,batch=(self.record(),)),self.obs())
        self.assertEqual(r.state.batch,());self.assertEqual(r.returned_phase,0xffffffff)
        self.assertIn('0046493c',r.calls);self.assertNotIn('0046fb38',r.calls)
        r=npc_buy_step(r.state,NpcBuyObservation(1500))
        self.assertEqual(r.returned_phase,0);self.assertEqual(r.state.fields[0x698],0)

    def test_changed_target_clears_partial_batch(self):
        r=npc_buy_step(self.state(batch=(self.record(),)),self.obs(current_target=8))
        self.assertEqual(r.state.batch,());self.assertEqual(r.status,'npc_target_planned')

    def test_row_collection_wait_boundary_does_not_process_next_row(self):
        r=npc_buy_step(self.state(),self.obs())
        self.assertEqual(r.state.batch,(self.record(),));self.assertEqual(r.returned_phase,0)
        self.assertEqual(npc_buy_step(r.state,NpcBuyObservation(1499)).status,'waiting')
        r=npc_buy_step(r.state,NpcBuyObservation(1500))
        self.assertEqual(r.returned_phase,1);self.assertEqual(r.calls,());self.assertEqual(r.state.fields[0x694],0)

    def test_dword_clock_wrap_retains_wait(self):
        r=npc_buy_step(self.state(),self.obs(now_ms=0xfffffff0))
        self.assertEqual(npc_buy_step(r.state,NpcBuyObservation(1000)).status,'waiting')

    def test_enabled_must_be_exact_one(self):
        for flag in (0,2,255):
            r=npc_buy_step(self.state(),self.obs(row=NpcBuyRouteRow(flag),vendor_matches={}))
            self.assertEqual(r.returned_phase,1);self.assertEqual(r.state.batch,())

    def test_wrong_vendor_and_disabled_row_do_not_wait(self):
        r=npc_buy_step(self.state(),self.obs(row=NpcBuyRouteRow(1,1),
                      vendor_matches={name:True for name,v in BUY_VENDORS}))
        self.assertEqual(r.status,'vendor_skipped');self.assertEqual(r.state.fields[0x694],0)

    def test_short_circuit_vendor_comparisons_and_dc_vendor(self):
        r=npc_buy_step(self.state(),self.obs())
        self.assertIn('00505d20:Sundries',r.calls);self.assertNotIn('00505d20:Armor',r.calls)
        matches={name:name=='DC Sundries' for name,v in BUY_VENDORS}
        r=npc_buy_step(self.state(),self.obs(row=NpcBuyRouteRow(1,0x412f8,self.record()),vendor_matches=matches))
        self.assertEqual(r.status,'row_collected');self.assertNotIn('00505d20:Amore',r.calls)

    def test_empty_final_batch_waits_and_returns_count_plus_one(self):
        r=npc_buy_step(self.state(1),self.obs(row=None,vendor_matches={}))
        self.assertEqual(r.status,'final_wait');self.assertNotIn('004c95a4',r.calls)
        self.assertEqual(npc_buy_step(r.state,NpcBuyObservation(1500)).returned_phase,2)

    def test_final_batch_plans_packet_clears_and_waits(self):
        r=npc_buy_step(self.state(1,batch=(self.record(),)),self.obs(packet_observation=self.packets()))
        self.assertEqual(r.status,'batch_flushed');self.assertEqual(len(r.queue_payloads),1)
        self.assertEqual(len(r.cache_writes),145);self.assertEqual(r.state.batch,())
        self.assertEqual(r.returned_phase,1)

    def test_missing_packet_inputs_preserve_batch_before_clear(self):
        state=self.state(1,batch=(self.record(),))
        r=npc_buy_step(state,self.obs())
        self.assertEqual(r.status,'needs_observation');self.assertEqual(r.state.batch,state.batch)
        self.assertEqual(r.state.fields[0x694],0)

    def test_zero_acceptance_still_clears_and_waits(self):
        record=replace(self.record(),desired_quantity=0)
        r=npc_buy_step(self.state(1,batch=(record,)),self.obs(packet_observation=self.packets()))
        self.assertEqual(r.status,'final_wait');self.assertEqual(r.state.batch,());self.assertEqual(len(r.cache_writes),140)

    def test_unknown_target_row_or_comparison_not_assumed(self):
        for obs in (NpcBuyObservation(0),self.obs(row=None),self.obs(vendor_matches={})):
            self.assertEqual(npc_buy_step(self.state(),obs).status,'needs_observation')

    def test_out_of_vector_index_unresolved_and_conflicting_helper_rejected(self):
        self.assertEqual(npc_buy_step(self.state(2),self.obs()).status,'unresolved_row_index')
        frame=NpcRouteFrame(6,dict(self.state().fields)|{0x689:1}, {0x561f58:0})
        with self.assertRaises(ValueError):
            npc_route_step(frame,{'Sundries':True},{'004fe384':0,'004efa84':0},buy_observation=self.obs())

    def test_parent_phase6_collect_flush_wait_then_advances7(self):
        fields=dict(self.state().fields);fields[0x689]=1
        frame=NpcRouteFrame(6,fields,{0x561f58:0})
        def step(frame,obs):return npc_route_step(frame,{'Sundries':True},{'004fe384':0},buy_observation=obs)
        r=step(frame,self.obs());self.assertEqual(r.frame.buy_batch,(self.record(),))
        r=step(r.frame,NpcBuyObservation(1500));self.assertEqual(r.frame.fields[0x690],1)
        r=step(r.frame,self.obs(now_ms=1501,packet_observation=self.packets()))
        self.assertEqual(r.frame.phase,6);self.assertEqual(len(r.queue_payloads),1);self.assertEqual(len(r.cache_writes),145)
        r=step(r.frame,NpcBuyObservation(2001))
        self.assertEqual(r.frame.phase,7);self.assertEqual(r.frame.fields[0x690],0xffffffff)

    def test_parent_unknown_guard_prevents_nested_execution(self):
        fields=dict(self.state().fields);fields[0x689]=1
        r=npc_route_step(NpcRouteFrame(6,fields,{0x561f58:0}),{'Sundries':True},buy_observation=self.obs())
        self.assertEqual(r.status,'needs_observation');self.assertEqual(r.frame.buy_batch,())

    def test_immutable_state_and_batch_type_validation(self):
        fields=dict(self.state().fields);state=NpcBuyState(fields);fields[0x690]=42
        self.assertEqual(state.fields[0x690],0)
        with self.assertRaises(ValueError):NpcBuyState({},(1,))
