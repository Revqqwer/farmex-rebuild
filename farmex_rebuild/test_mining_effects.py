import unittest
from dataclasses import replace
from mining_effects import *
from mining_configuration import MiningPanelConfiguration
from mining_engine import MiningExecutionState,MiningSnapshot,OreSlotState,OreSlotSnapshot
from mining_frame import MiningFrameState,MiningFrameObservation,replay_mining_frame
from mining_pipeline import MiningPipelineObservation

def cfg(**kw):
    values={0x6046:0,0x604c:0,0x6044:1,0x6045:0,0x5ff8:1,0x6047:0,
        0x603b:0,0x6038:0,0x6036:0,0x6028:1,0x6029:1,0x602c:1,0x6035:0,0x6030:1,0x6034:0}
    values.update({int(k,16):v for k,v in kw.items()});return MiningPanelConfiguration('fixture',values)
def state(phase=2,index=30):
    return MiningFrameState(MiningPipelineState(MiningExecutionState(phase=phase,route_active=True,item_index=index),
        OreSlotState(item_index=index,last_attempt_ms=77,ws_active=True,ws_counter=5)))
def returning():
    return dict(sell_476c7c=1,bank_476d44=0,region_1_equal=0,region_2_equal=0,region_3_equal=1,
                distance_fpu_ah=0x40,use_constructor_defaults=1,**{'returned:004eb9f4':True})
def frame_obs(maintenance=True):
    m=dict(storage_5690b8=0,storage_helper_4fe384=0,inn_helper_46fe90=0,full_463ac0=1,ore_count_477770=1)
    return MiningFrameObservation(dict(active_initial=1,dead=0,merchant_after_speed=0,
        mining_after_merchant=int(maintenance),route_after_mining=1,active_after_route=0),
        MiningPipelineObservation(MiningSnapshot(),OreSlotSnapshot()),maintenance=m if maintenance else None,
        post_maintenance_lock_byte=0)

class MiningEffectTests(unittest.TestCase):
    def test_producer_respects_sell_before_bank_order(self):
        p=plan_mining_effect('00477bd4',cfg(),MiningEffectObservation(returning={},bank_slots={}))
        self.assertFalse(p.complete);self.assertEqual(p.missing,'sell_476c7c');self.assertIsNone(p.bank)

    def test_producer_and_observed_result_cannot_conflict(self):
        with self.assertRaises(ValueError):
            plan_mining_effect('00477bd4',cfg(),MiningEffectObservation(returning=returning(),sell_slots={}))

    def test_vip_candidate_shortcuts_feed_return_selector(self):
        o=returning();del o['sell_476c7c'];del o['bank_476d44']
        p=plan_mining_effect('00477bd4',cfg(**{'604c':1,'6045':1}),MiningEffectObservation(returning=o,sell_slots={},bank_slots={}))
        self.assertTrue(p.complete);self.assertEqual(p.sell.status,'vip_short_circuit')
        self.assertEqual(p.returning.selector,1);self.assertEqual(p.returning.route.name,'MoradonMiningRoute1')

    def test_start_prefix_reducer_preserves_ws_and_retry(self):
        s=state();p=plan_mining_ore_start(cfg(),{'gate_4631a8':0})
        updated=apply_start_write_prefix(s.pipeline,p)
        self.assertFalse(p.complete);self.assertEqual((updated.execution.phase,updated.execution.item_index),(0,14))
        self.assertEqual((updated.ore.last_attempt_ms,updated.ore.ws_active,updated.ore.ws_counter),(77,True,5))

    def test_missing_start_blocks_maintenance_and_route(self):
        s=state();p=replay_mining_frame(cfg(),s,frame_obs(),2000)
        self.assertFalse(p.complete);self.assertEqual(p.missing,('maintenance_effect.start',))
        self.assertIsNone(p.pipeline);self.assertEqual(p.state,s)

    def test_start_normal_plan_resets_before_route_phase0(self):
        o=replace(frame_obs(),maintenance_effects=MiningEffectObservation(start={'gate_4631a8':0,'start_tick':2000}))
        p=replay_mining_frame(cfg(),state(),o,2000)
        self.assertTrue(p.complete);self.assertEqual(p.maintenance_effect.start.status,'ore_start_planned')
        self.assertEqual((p.state.pipeline.execution.phase,p.state.pipeline.execution.item_index,p.state.pipeline.execution.started_ms),(0,14,2000))
        self.assertEqual(p.state.pipeline.ore.ws_counter,5);self.assertEqual(p.state.pipeline.ore.last_attempt_ms,77)

    def test_start_clock_domain_gap_is_explicit(self):
        o=replace(frame_obs(),maintenance_effects=MiningEffectObservation(start={'gate_4631a8':0,'start_tick':2000}))
        p=replay_mining_frame(cfg(),state(),o,0x100000000+2000)
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_start_clock_binding')

    def test_phase7_return_waits_for_effect_without_committing_parent(self):
        s=state(7);p=replay_mining_frame(cfg(),s,frame_obs(False),2000)
        self.assertFalse(p.complete);self.assertEqual(p.missing,('route_effect.returning',))
        self.assertTrue(p.state.pipeline.execution.route_active)
        self.assertFalse(p.prospective_state.pipeline.execution.route_active)

    def test_phase7_binds_return_plan_and_finishes_local_invocation(self):
        o=replace(frame_obs(False),route_effects=MiningEffectObservation(returning=returning()))
        p=replay_mining_frame(cfg(),state(7),o,2000)
        self.assertTrue(p.complete);self.assertEqual(p.route_effect.returning.route.name,'MoradonMiningRoute2')
        self.assertFalse(p.state.pipeline.execution.route_active);self.assertFalse(p.native_execution_verified)

    def test_external_effect_return_marker_rejected_by_frame(self):
        for address in ('004779dc','00477bd4'):
            with self.assertRaises(ValueError):MiningFrameObservation({},maintenance={'returned:'+address:True})

    def test_start_and_post_route_false_conflict_is_not_silently_accepted(self):
        o=frame_obs();s=dict(o.scheduler);s['route_after_mining']=0
        o=replace(o,scheduler=s,maintenance_effects=MiningEffectObservation(start={'gate_4631a8':0,'start_tick':2000}))
        p=replay_mining_frame(cfg(),state(),o,2000)
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_post_start_route_flag')

if __name__=='__main__':unittest.main()
