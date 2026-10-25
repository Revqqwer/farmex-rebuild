import unittest
from dataclasses import replace
from storage_workers import (VIP_BASE,INN_BASE,StorageObservation,StorageCall,
                             storage_worker_step,dispatch_storage_worker)
from npc_route_engine import NpcRouteFrame,npc_route_step

class StorageTests(unittest.TestCase):
    def state(self,base=VIP_BASE,mode=2,**unused):
        return {VIP_BASE:1 if base==VIP_BASE else 0,INN_BASE:1 if base==INN_BASE else 0,
                base+4:mode,base+8:0,base+9:1,base+0xc:0,base+0x10:0,base+0x14:0,
                base+0x18:0,base+0x1c:0,0x561f60:1,0x561f6f:0,0x561f58:0,
                0x568cfe:0,0x5690cc:0,0x568dac:9,0x56ffe0:0,0x56ffe4:0,0x553d40:0,0x553d44:0}
    def obs(self,**changes):
        return replace(StorageObservation(1000,1,0,0,1,{'004611a0':1,'004fe3c4':0,'004fe420':0,'0046ff6c':8}),**changes)
    def call(self,mode=2,state=None,obs=None,base=VIP_BASE):
        return storage_worker_step(base,self.state(base,mode) if state is None else state,self.obs() if obs is None else obs)

    def test_dispatch_vip_has_priority_over_inn(self):
        state=self.state();state[INN_BASE]=1
        r=dispatch_storage_worker(state,self.obs());self.assertEqual(r.worker,'VIP')
        state[VIP_BASE]=0
        state.update({INN_BASE+4:2,INN_BASE+0x10:0})
        self.assertEqual(dispatch_storage_worker(state,self.obs()).worker,'Inn')
        state[INN_BASE]=0;self.assertEqual(dispatch_storage_worker(state,self.obs()).status,'inactive')

    def test_dispatch_unknown_vip_flag_does_not_assume_inn(self):
        state=self.state(INN_BASE);del state[VIP_BASE]
        self.assertEqual(dispatch_storage_worker(state,self.obs()).status,'needs_observation')

    def test_vip_outer_stop_gates_short_circuit(self):
        for address,value in ((0x561f60,0),(0x561f6f,1)):
            state=self.state();state[address]=value
            r=self.call(state=state,obs=self.obs(helpers={}))
            self.assertEqual(r.status,'finished_plan');self.assertNotIn(StorageCall('004611a0'),r.calls)
            self.assertEqual(r.globals[VIP_BASE],0)

    def test_vip_signed_nonpositive_helper_stops(self):
        for value in (0,0xffffffff,0x80000000):
            r=self.call(obs=self.obs(helpers={'004611a0':value}))
            self.assertEqual(r.status,'finished_plan')

    def test_exact_open_one_and_busy_any_nonzero(self):
        r=self.call(obs=self.obs(open_byte=2));self.assertEqual(r.status,'waiting_open')
        r=self.call(obs=self.obs(busy_byte=2));self.assertEqual(r.status,'waiting_busy')
        self.assertEqual(r.globals[VIP_BASE+0x10],0)

    def test_vip_open_retry5000_boundary(self):
        self.assertEqual(self.call(obs=self.obs(now_ms=4999,open_byte=0)).status,'waiting_open')
        r=self.call(obs=self.obs(now_ms=5000,open_byte=0))
        self.assertEqual(r.status,'open_planned');self.assertIn(StorageCall('004fe1c4',(VIP_BASE,)),r.calls)
        self.assertEqual(r.globals[0x56ffe0],5000)

    def test_vip_open_retry_clock_wrap_not_positive_elapsed(self):
        state=self.state();state[0x56ffe0]=0xfffffff0
        self.assertEqual(self.call(state=state,obs=self.obs(open_byte=0)).status,'waiting_open')

    def test_vip_mode1_and4_use28_source_slots(self):
        for mode,address in ((1,'004ff600'),(4,'004fe5d8'),(6,'004fea78')):
            state=self.state(mode=mode);state[VIP_BASE+0xc]=27
            r=self.call(state=state)
            self.assertIn(StorageCall(address,(VIP_BASE,27)),r.calls)
            self.assertEqual(r.globals[VIP_BASE+0xc],28);self.assertEqual(r.globals[VIP_BASE],1)

    def test_vip_modes2_3_5_use48_destination_slots_and_selector(self):
        for mode,address in ((2,'004ff074'),(3,'004fed78'),(5,'004fe828')):
            state=self.state(mode=mode);state[VIP_BASE+0x10]=47
            r=self.call(state=state)
            args=(VIP_BASE,47,1) if mode==2 else (VIP_BASE,47)
            self.assertIn(StorageCall(address,args),r.calls)
            self.assertEqual(r.globals[VIP_BASE+0x10],48)
            self.assertEqual(r.globals[VIP_BASE+0x14],48 if mode in (2,5) else 0)
            self.assertIn(StorageCall('004fe420',(VIP_BASE,2 if mode==5 else 0)),r.calls)

    def test_vip_modes4_and5_switch6_return_without_same_tick_action(self):
        for mode,counter in ((4,0xc),(5,0x10)):
            for full in (False,True):
                state=self.state(mode=mode);state[VIP_BASE+counter]=28 if mode==4 else 48
                obs=self.obs(helpers={'004611a0':1,'004fe3c4':1 if full else 0,'004fe420':1 if full else 0})
                r=self.call(state=state,obs=obs)
                self.assertEqual(r.status,'mode_changed');self.assertEqual(r.globals[VIP_BASE+4],6)
                self.assertEqual(r.globals[VIP_BASE+0xc],0)
                self.assertNotIn('004fea78',[c.address for c in r.calls])

    def test_vip_terminal_cleanup_fresh_open_byte_and_timer(self):
        state=self.state();state[VIP_BASE+0x10]=48;state[VIP_BASE+8]=1
        r=self.call(state=state,obs=self.obs(cleanup_open_byte=0))
        self.assertEqual(r.status,'finished_plan');self.assertEqual(r.globals[VIP_BASE+0x14],0)
        self.assertEqual(r.globals[VIP_BASE+0x18],1000);self.assertEqual(r.globals[VIP_BASE+8],0)
        self.assertNotIn('004fe21c',[c.address for c in r.calls])
        r=self.call(state=state);self.assertIn(StorageCall('004fe21c',(VIP_BASE,)),r.calls)

    def test_full_helper_boolean_is_low_byte_and_short_circuits_counter(self):
        state=self.state();del state[VIP_BASE+0x10]
        r=self.call(state=state,obs=self.obs(helpers={'004611a0':1,'004fe420':1}))
        self.assertEqual(r.status,'finished_plan')
        self.assertEqual(self.call(obs=self.obs(helpers={'004611a0':1,'004fe420':256})).status,'slot_planned')

    def test_negative_counters_are_signed_source_arguments(self):
        state=self.state();state[VIP_BASE+0x10]=0xffffffff
        r=self.call(state=state)
        self.assertIn(StorageCall('004ff074',(VIP_BASE,0xffffffff,1)),r.calls)
        self.assertEqual(r.globals[VIP_BASE+0x10],0)

    def test_unknown_mode_does_not_cleanup(self):
        for base in (VIP_BASE,INN_BASE):
            r=self.call(mode=99,base=base)
            self.assertEqual(r.status,'pending_unknown_mode');self.assertEqual(r.globals[base],1)

    def test_inn_mode1_end_switches2_or_finishes_by_vip_gate(self):
        for flag,vipcount,expected in ((0,0,'mode_changed'),(1,48,'mode_changed'),(1,47,'finished_plan')):
            state=self.state(INN_BASE,1);state[INN_BASE+0xc]=28;state[0x568cfe]=flag;state[0x5690cc]=vipcount
            r=self.call(state=state,base=INN_BASE)
            self.assertEqual(r.status,expected)
            if expected=='mode_changed':self.assertEqual(r.globals[INN_BASE+4],2)

    def test_inn_mode1_last_slot_advances_then_switches_on_next_call(self):
        state=self.state(INN_BASE,1);state[INN_BASE+0xc]=27
        r=self.call(state=state,base=INN_BASE)
        self.assertIn(StorageCall('00470584',(INN_BASE,27)),r.calls);self.assertEqual(r.globals[INN_BASE+4],1)
        self.assertEqual(self.call(state=r.globals,base=INN_BASE).status,'mode_changed')

    def test_inn_pages_every24_except192_and_close_next_tick(self):
        for before,page in ((22,False),(23,True),(47,True),(167,True),(191,False)):
            state=self.state(INN_BASE,2);state[INN_BASE+0x10]=before
            r=self.call(state=state,base=INN_BASE)
            self.assertEqual(StorageCall('0046fdf8',(INN_BASE,2)) in r.calls,page)
            self.assertEqual(r.globals[INN_BASE],1)
        self.assertEqual(self.call(state=r.globals,base=INN_BASE).status,'finished_plan')

    def test_inn_secondary_open_path_resets_free_count(self):
        state=self.state(INN_BASE);state[INN_BASE+0x14]=7
        r=self.call(state=state,base=INN_BASE,obs=self.obs(open_byte=0,secondary_open_byte=1))
        self.assertEqual(r.status,'secondary_close_planned');self.assertEqual(r.globals[INN_BASE+0x14],0)
        self.assertEqual(r.calls,(StorageCall('0046fc0c',(INN_BASE,)),))

    def test_inn_retry5000_with_or_without_npc_id(self):
        r=self.call(base=INN_BASE,obs=self.obs(open_byte=0,now_ms=5000))
        self.assertEqual(r.status,'interaction_planned');self.assertEqual(r.calls,(StorageCall('0046fb38',(INN_BASE,9)),))
        state=self.state(INN_BASE);state[0x568dac]=0
        r=self.call(state=state,base=INN_BASE,obs=self.obs(open_byte=0,now_ms=5000))
        self.assertEqual(r.status,'finished_plan');self.assertEqual(r.globals[0x553d40],5000)

    def test_inn_finish_sets_mode4_marker_counts_only_if_zero(self):
        state=self.state(INN_BASE);state[0x561f60]=0;state[0x561f58]=4
        r=self.call(state=state,base=INN_BASE,obs=self.obs(open_byte=None))
        self.assertEqual(r.globals[0x569870],1);self.assertEqual(r.globals[INN_BASE+0x14],8)
        state[INN_BASE+0x14]=7
        r=self.call(state=state,base=INN_BASE,obs=self.obs(helpers={}))
        self.assertEqual(r.globals[INN_BASE+0x14],7);self.assertNotIn('0046ff6c',[c.address for c in r.calls])

    def test_unknown_cleanup_or_raw_helpers_not_assumed_success(self):
        state=self.state();state[VIP_BASE+0x10]=48
        for obs in (self.obs(cleanup_open_byte=None),self.obs(helpers={}),self.obs(open_byte=None)):
            self.assertEqual(self.call(state=state,obs=obs).status,'needs_observation')
        self.assertEqual(self.call(state={},obs=self.obs()).status,'needs_observation')

    def test_worker_finish_updates_npc_phase5_retry_and_phase7(self):
        state=self.state();state[VIP_BASE+0x10]=48;state[VIP_BASE+0x14]=48;state[0x5690d8]=1
        frame=NpcRouteFrame(5,{0x556:1,0x688:1},state)
        r=self.call(state=state);frame=r.apply_to_npc(frame)
        parent=npc_route_step(frame,{'Sundries':True})
        self.assertEqual(parent.frame.phase,6)
        state=self.state(INN_BASE,2);state[INN_BASE+0x10]=192
        frame=NpcRouteFrame(7,{0x6d8:1},state)
        r=self.call(state=state,base=INN_BASE)
        parent=npc_route_step(r.apply_to_npc(frame),{'Inn Hostess':True},{'004fe384':0})
        self.assertEqual(parent.frame.phase,8)

    def test_globals_and_observations_are_copied_and_boundaries_validated(self):
        state=self.state();r=self.call(state=state);self.assertEqual(state[VIP_BASE+0x10],0)
        helpers={'004611a0':1};obs=self.obs(helpers=helpers);helpers.clear();self.assertEqual(obs.helpers['004611a0'],1)
        with self.assertRaises(ValueError):StorageObservation(0,open_byte=256)
        with self.assertRaises(ValueError):storage_worker_step(1,{},self.obs())
