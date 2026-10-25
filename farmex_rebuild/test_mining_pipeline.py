import unittest
from dataclasses import replace
from mining_pipeline import *
from mining_configuration import MiningPanelConfiguration
from mining_engine import MiningExecutionState,MiningSnapshot,OreSlotState,OreSlotSnapshot,process_ore_slot

class MiningPipelineTests(unittest.TestCase):
    def config(self,interval=0,ws=False,vip=False):
        return MiningPanelConfiguration('fixture',{0x6029:0,0x602c:0,0x6035:0,0x604c:int(vip),0x6030:interval,0x6034:int(ws)})
    def state(self,phase=2,index=14,**ore):
        return MiningPipelineState(MiningExecutionState(phase=phase,route_active=True,item_index=index),OreSlotState(item_index=index,**ore))
    def outer(self,**kw):
        return replace(MiningSnapshot(comparison_505118=True,helper_477770_count=1,helper_464a10_result=True,distance_ore=1),**kw)
    def run_tick(self,state=None,outer=None,ore=None,now=1000,config=None):
        return replay_mining_pipeline(config or self.config(),state or self.state(),
            MiningPipelineObservation(outer or self.outer(),ore),now)
    def test_phase2_nested_call_updates_shared_index_without_server_ack(self):
        p=self.run_tick(ore=OreSlotSnapshot(True,request_helper_45dc44_zero=True))
        self.assertTrue(p.complete);self.assertEqual((p.state.execution.item_index,p.state.ore.item_index),(15,15))
        self.assertEqual(p.state.ore.last_attempt_ms,1000);self.assertEqual(p.state.execution.phase,2)
        self.assertEqual([i.source_address for i in p.intents],['00479698','004c80e4'])
        self.assertFalse(p.server_acknowledged);self.assertFalse(p.native_callback_return_verified)
        self.assertTrue(p.normal_helper_returns_assumed)
        self.assertEqual(p.ore.request_prelude_calls,('0046fb38','00463670'))
    def test_phase3_float_gate_and_phase2_truncation_are_distinct(self):
        ore=OreSlotSnapshot(False)
        self.assertIsNotNone(self.run_tick(state=self.state(2),outer=self.outer(distance_ore=7.99),ore=ore).ore)
        self.assertIsNone(self.run_tick(state=self.state(2),outer=self.outer(distance_ore=8),ore=ore).ore)
        self.assertIsNotNone(self.run_tick(state=self.state(3),outer=self.outer(distance_ore=9.99),ore=ore).ore)
        p=self.run_tick(state=self.state(3),outer=self.outer(distance_ore=10),ore=ore)
        self.assertIsNone(p.ore);self.assertEqual(p.state.execution.phase,1)
    def test_earlier_outer_gaps_and_count_zero_never_require_child(self):
        p=self.run_tick(outer=MiningSnapshot())
        self.assertFalse(p.complete);self.assertIsNone(p.ore);self.assertEqual(p.status,'needs_outer_observation')
        p=self.run_tick(outer=self.outer(helper_477770_count=0))
        self.assertTrue(p.complete);self.assertEqual(p.state.execution.phase,4);self.assertIsNone(p.ore)
    def test_child_cadence_short_circuit_does_not_require_name_snapshot(self):
        p=self.run_tick(now=999,config=self.config(interval=1))
        self.assertTrue(p.complete);self.assertIsNotNone(p.ore);self.assertEqual(p.state,self.state())
        p=self.run_tick(now=1000,config=self.config(interval=1))
        self.assertFalse(p.complete);self.assertEqual(p.required_observations,('ore.ore_name_match',))
    def test_non_ore_skips_index_without_retry_stamp_or_ack(self):
        p=self.run_tick(ore=OreSlotSnapshot(False))
        self.assertEqual(p.state.execution.item_index,15);self.assertEqual(p.state.ore.last_attempt_ms,0)
        self.assertEqual(len(p.intents),1)
    def test_missing_request_read_keeps_known_ws_prefix_prospective(self):
        p=self.run_tick(ore=OreSlotSnapshot(True,True,None),config=self.config(ws=True))
        self.assertFalse(p.complete);self.assertEqual(p.state.ore.ws_counter,1)
        self.assertEqual(p.state.ore.ws_first_ms,1000);self.assertEqual(p.state.execution.item_index,14)
        self.assertEqual(p.required_observations,('ore.request_helper_45dc44_zero',))
        self.assertEqual(p.ore.intents[0].value,1)
    def test_final_slot42_transition_occurs_on_next_outer_call(self):
        p=self.run_tick(state=self.state(index=41),ore=OreSlotSnapshot(True,request_helper_45dc44_zero=True))
        self.assertEqual((p.state.execution.phase,p.state.execution.item_index),(2,42))
        q=self.run_tick(state=p.state,now=1001)
        self.assertEqual(q.state.execution.phase,4);self.assertIsNone(q.ore)
    def test_outer_index_reset_preserves_global_ws_and_retry_fields(self):
        state=self.state(phase=4,index=41,ws_counter=7,ws_active=True,last_attempt_ms=200)
        p=self.run_tick(state=state)
        self.assertEqual((p.state.execution.phase,p.state.execution.item_index,p.state.ore.item_index),(2,14,14))
        self.assertEqual((p.state.ore.ws_counter,p.state.ore.ws_active,p.state.ore.last_attempt_ms),(7,True,200))
    def test_vip_reset_to_zero_is_not_clamped_to_inventory14(self):
        state=self.state(phase=5,index=20)
        state=replace(state,execution=replace(state.execution,auxiliary_flag=True))
        p=self.run_tick(state=state,config=self.config(vip=True),outer=self.outer(storage_5690b8_active=False,storage_5690cc_value=1))
        self.assertEqual((p.state.execution.phase,p.state.execution.item_index,p.state.ore.item_index),(2,0,0))
        q=self.run_tick(state=p.state,ore=OreSlotSnapshot(False),now=1001)
        self.assertEqual(q.state.execution.item_index,1)
    def test_shared_index_conflicts_rejected(self):
        with self.assertRaises(ValueError):MiningPipelineState(MiningExecutionState(item_index=14),OreSlotState(item_index=15))
    def test_ws_action_argument_signed_modulo_and_dword_wrap(self):
        for counter,arg,next_value in ((0,1,1),(1,2,2),(3,1,4),(0xffffffff,2,0),(0xfffffffd,1,0xfffffffe)):
            p=self.run_tick(state=self.state(ws_counter=counter),config=self.config(ws=True),ore=OreSlotSnapshot(True,True,False))
            self.assertEqual(p.ore.intents[0].value,arg);self.assertEqual(p.state.ore.ws_counter,next_value)
            self.assertEqual(p.state.execution.item_index,14)
    def test_ws_second_call_argument_zero_and_strict_delay(self):
        state=self.state(ws_counter=3,ws_first_ms=100)
        p=self.run_tick(state=state,now=120,config=self.config(ws=True),ore=OreSlotSnapshot(True,False,False))
        self.assertEqual(p.ore.intents,())
        p=self.run_tick(state=state,now=121,config=self.config(ws=True),ore=OreSlotSnapshot(True,False,False))
        self.assertEqual(p.ore.intents[0].value,0);self.assertTrue(p.state.ore.ws_active)

if __name__=='__main__':unittest.main()
