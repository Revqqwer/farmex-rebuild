import unittest
from dataclasses import replace
from npc_sell_engine import NpcSaleState,NpcSaleObservation,npc_sale_step
from npc_sell_filter import SellFilterObservation
from npc_sell_packets import NpcSellRecord,SellCacheSlot,VENDORS
from npc_route_engine import NpcRouteFrame,npc_route_step


class SaleEngineTests(unittest.TestCase):
    def state(self,phase=14,batch=(),variant=0):
        return NpcSaleState({0x654:phase,0x658:0,0x660:0,0x664:0,0x604:8,0x60c:0x100000},
                            {0x553e44:variant,0x561f58:0},batch)

    def observation(self,phase=14,**changes):
        selection=SellFilterObservation(0,False,-1,False,list_index_41a5cc=1,list_checked_5622e1=True)
        obs=NpcSaleObservation(1000,0x200000,8,True,selection,NpcSellRecord(100+phase,(phase-14)&255,1),
                              {name:name=='Sundries' for name,value in VENDORS},
                              {slot:SellCacheSlot(1,100,20) for slot in range(14,42)})
        return replace(obs,**changes)

    def test_root_zero_returns43_without_changing_internal_phase(self):
        r=npc_sale_step(self.state(13),NpcSaleObservation(0,inventory_pointer=0))
        self.assertEqual(r.returned_phase,43);self.assertEqual(r.state.fields[0x654],13)

    def test_root_unknown_is_not_no_inventory(self):
        r=npc_sale_step(self.state(),NpcSaleObservation(0))
        self.assertEqual(r.status,'needs_observation');self.assertEqual(r.returned_phase,14)

    def test_initial13_clears_batch_selects_npc_and_waits3215_or1000(self):
        for variant,delay in ((0,3215),(1,1000)):
            state=self.state(13,(NpcSellRecord(1,0,1),),variant)
            r=npc_sale_step(state,self.observation(13))
            self.assertEqual(r.state.batch,());self.assertEqual(r.state.globals[0x56ffb4],delay)
            self.assertIn('0046493c',r.calls);self.assertIn('0046fb38',r.calls)

    def test_changed_target_clears_existing_batch(self):
        r=npc_sale_step(self.state(20,(NpcSellRecord(1,0,1),)),self.observation(20,current_target=9))
        self.assertEqual(r.state.batch,());self.assertEqual(r.returned_phase,20)

    def test_wait_boundary_advances_once_without_new_slot_processing(self):
        r=npc_sale_step(self.state(13),self.observation(13))
        self.assertEqual(npc_sale_step(r.state,self.observation(now_ms=4214)).returned_phase,13)
        done=npc_sale_step(r.state,self.observation(now_ms=4215))
        self.assertEqual(done.returned_phase,14);self.assertEqual(done.calls,())

    def test_dword_wrap_preserves_signed_qword_wait(self):
        r=npc_sale_step(self.state(13),self.observation(13,now_ms=0xfffffff0))
        self.assertEqual(npc_sale_step(r.state,self.observation(now_ms=500)).status,'waiting')

    def test_empty_slot_advances_without_metadata_or_mode(self):
        obs=NpcSaleObservation(1000,0x200000,8,False)
        r=npc_sale_step(self.state(),obs)
        self.assertEqual(r.returned_phase,15);self.assertEqual(r.state.batch,())

    def test_filter_skip_does_not_append(self):
        obs=self.observation(selection=SellFilterObservation(0,excluded_4e7c60=True))
        r=npc_sale_step(self.state(),obs)
        self.assertEqual(r.returned_phase,15);self.assertEqual(r.state.batch,())

    def test_selected_small_batch_appends_and_advances(self):
        r=npc_sale_step(self.state(),self.observation())
        self.assertEqual(len(r.state.batch),1);self.assertEqual(r.returned_phase,15)
        self.assertEqual(r.queue_payloads,())

    def test14th_record_flush_delay_and_payload(self):
        batch=tuple(NpcSellRecord(100+i,i,1) for i in range(13))
        for mode,variant,delay in ((0,0,2443),(2,0,2853),(0,1,1000),(2,1,1000)):
            state=self.state(27,batch,variant)
            state=NpcSaleState(state.fields,{**state.globals,0x561f58:mode},batch)
            obs=self.observation(27)
            if mode==2:obs=replace(obs,selection=SellFilterObservation(2,mode2_index_47677c=0,mode2_checked=True))
            r=npc_sale_step(state,obs)
            self.assertEqual(r.state.batch,());self.assertEqual(r.returned_phase,27)
            self.assertEqual(r.state.globals[0x56ffb4],delay);self.assertEqual(len(r.queue_payloads[0]),109)

    def test_unresolved_producer_does_not_commit_duplicate14th_record(self):
        batch=tuple(NpcSellRecord(100+i,i,1) for i in range(13));state=self.state(27,batch)
        r=npc_sale_step(state,self.observation(27,cache_slots=None))
        self.assertEqual(r.status,'needs_observation');self.assertEqual(r.state.batch,batch)
        self.assertEqual(r.state.fields[0x658],0)

    def test_final42_flush_or_empty_wait_and_then43(self):
        for batch,variant,delay in (((),0,1000),((NpcSellRecord(1,0,1),),0,2553),((NpcSellRecord(1,0,1),),1,1000)):
            r=npc_sale_step(self.state(42,batch,variant),self.observation(42))
            self.assertEqual(r.state.globals[0x56ffb4],delay);self.assertEqual(r.state.batch,())
            self.assertEqual(npc_sale_step(r.state,self.observation(now_ms=1000+delay)).returned_phase,43)

    def test_unsupported_vendor_no_queue_still_clears_source_batch(self):
        obs=self.observation(42,vendor_matches={name:False for name,value in VENDORS})
        r=npc_sale_step(self.state(42,(NpcSellRecord(1,0,1),)),obs)
        self.assertEqual(r.status,'waiting');self.assertEqual(r.queue_payloads,());self.assertEqual(r.state.batch,())

    def test_parent_phase4_no_inventory_advances5(self):
        state=self.state(13);fields={**state.fields,0x650:1}
        r=npc_route_step(NpcRouteFrame(4,fields,state.globals),{'Sundries':True},
                         {'004fe384':0},
                         sale_observation=NpcSaleObservation(0,inventory_pointer=0))
        self.assertEqual(r.frame.phase,5);self.assertEqual((r.frame.fields[0x654],r.frame.fields[0x650]),(13,0))

    def test_parent_guard_unknown_prevents_no_inventory_shortcut(self):
        state=self.state(13);fields={**state.fields,0x650:1}
        r=npc_route_step(NpcRouteFrame(4,fields,state.globals),{'Sundries':True},
                         sale_observation=NpcSaleObservation(0,inventory_pointer=0))
        self.assertEqual(r.status,'needs_observation');self.assertEqual(r.frame.phase,4)
        self.assertEqual(r.calls,('004fe384',))

    def test_parent_batch_flush_carries_packet_and_cache_plan_then_advances(self):
        batch=(NpcSellRecord(1,0,1),);state=self.state(42,batch)
        frame=NpcRouteFrame(4,{**state.fields,0x650:1},state.globals,sale_batch=batch)
        r=npc_route_step(frame,{'Sundries':True},{'004fe384':0},sale_observation=self.observation(42))
        self.assertEqual(len(r.queue_payloads),1);self.assertEqual(len(r.cache_writes),145)
        self.assertEqual(r.frame.sale_batch,());self.assertEqual(r.frame.phase,4)
        r=npc_route_step(r.frame,{'Sundries':True},{'004fe384':0},
                         sale_observation=self.observation(42,now_ms=3553))
        self.assertEqual(r.frame.phase,5);self.assertEqual(r.frame.fields[0x658],0)
