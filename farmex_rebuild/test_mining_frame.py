import unittest
from dataclasses import replace
from mining_frame import *
from mining_engine import MiningExecutionState,MiningSnapshot,OreSlotState,OreSlotSnapshot
from item_name import ItemNameObservation

def configuration(**extras):
    values={0x603c:0,0x6040:1,0x6047:0,0x6029:0,0x602c:0,0x6035:0,0x604c:0,0x6030:1,0x6034:0}
    values.update({int(k,16):v for k,v in extras.items()})
    return MiningPanelConfiguration('fixture',values)

def entry(phase=2,active=True):
    return MiningFrameState(MiningPipelineState(MiningExecutionState(phase=phase,route_active=active),OreSlotState()))

def observations():
    outer=MiningSnapshot(comparison_505118=True,helper_477770_count=1,
                         helper_464a10_result=True,distance_ore=1)
    name=b'Mysterious Ore';size=16
    return MiningFrameObservation(
        dict(active_initial=1,dead=0,merchant_after_speed=0,mining_after_merchant=0,
             route_after_mining=1,active_after_route=0),
        MiningPipelineObservation(outer,OreSlotSnapshot(True,None,True)),
        SlotNameObservation(0x100,0x20,0x30,0x200,0x300,0x400,0x500,0x600,123000,456,
            ItemNameObservation(metadata_category=3,storage_dword=size,pointer_dword=0x700,
                                bad_read_result=0,captured=name.ljust(size,b'\0'))),
        (QueueSample(2000,1),QueueSample(2003,1)))

class MiningFrameTests(unittest.TestCase):
    def test_full_caller_route_name_queue_composition(self):
        state=entry();p=replay_mining_frame(configuration(),state,observations(),2000)
        self.assertTrue(p.complete);self.assertEqual(p.status,'frame_planned')
        self.assertEqual(p.state.pipeline.execution.item_index,15)
        self.assertEqual([(r.created_tick,r.delay_dword) for r in p.state.queue.records],[(2000,300),(2003,600)])
        self.assertEqual(p.scheduler.calls,(('00479d70',('self',)),))
        self.assertTrue(p.route_return_assumed_from_local_plan)
        self.assertFalse(p.native_execution_verified);self.assertFalse(p.server_acknowledged)
        self.assertEqual(state.pipeline.execution.item_index,14)

    def test_inactive_caller_does_not_touch_nested_inputs(self):
        state=entry();o=MiningFrameObservation({'active_initial':0})
        p=replay_mining_frame(configuration(),state,o,2000)
        self.assertTrue(p.complete);self.assertIsNone(p.pipeline);self.assertEqual(p.state,state)

    def test_exclusive_respawn_branch_skips_route(self):
        p=replay_mining_frame(configuration(),entry(),MiningFrameObservation({'active_initial':1,'dead':1}),2000)
        self.assertTrue(p.complete);self.assertIsNone(p.pipeline)
        self.assertEqual(p.scheduler.status,'dead_respawn_disabled')

    def test_earlier_helper_gap_prevents_nested_invocation(self):
        state=entry();p=replay_mining_frame(configuration(**{'6047':1}),state,observations(),2000)
        self.assertFalse(p.complete);self.assertIsNone(p.pipeline)
        self.assertEqual(p.missing,('speed',));self.assertEqual(p.state,state)

    def test_speed_model_must_complete_before_route_invocation(self):
        p=replay_mining_frame(configuration(**{'6047':1}),entry(),replace(observations(),speed={}),2000)
        self.assertEqual(p.missing,('speed.lock_561f7e',));self.assertIsNone(p.pipeline)

    def test_locked_speed_helper_returns_to_caller_and_route(self):
        p=replay_mining_frame(configuration(**{'6047':1}),entry(),
            replace(observations(),speed={'lock_561f7e':1}),2000)
        self.assertTrue(p.complete);self.assertEqual(p.speed.status,'locked')
        self.assertTrue(p.speed_return_assumed_from_local_plan)
        self.assertEqual([a for a,_ in p.scheduler.calls],['0047b384','00479d70'])
        self.assertEqual(p.state.pipeline.execution.item_index,15)

    def test_speed_disabled_never_consumes_speed_snapshot(self):
        p=replay_mining_frame(configuration(),entry(),replace(observations(),speed={}),2000)
        self.assertTrue(p.complete);self.assertIsNone(p.speed)

    def test_external_speed_marker_cannot_bypass_model(self):
        with self.assertRaises(ValueError):MiningFrameObservation({SPEED_RETURN:True})

    def test_missing_maintenance_snapshot_stops_before_route(self):
        o=observations();values=dict(o.scheduler);values['mining_after_merchant']=1
        p=replay_mining_frame(configuration(),entry(),replace(o,scheduler=values),2000)
        self.assertFalse(p.complete);self.assertEqual(p.missing,('maintenance',))
        self.assertIsNone(p.pipeline)

    def test_maintenance_storage_guard_returns_into_route_caller(self):
        o=observations();values=dict(o.scheduler);values['mining_after_merchant']=1
        p=replay_mining_frame(configuration(),entry(),replace(o,scheduler=values,maintenance={'storage_5690b8':1},post_maintenance_lock_byte=0),2000)
        self.assertTrue(p.complete);self.assertEqual(p.maintenance.status,'storage_active')
        self.assertTrue(p.maintenance_return_assumed_from_local_plan)
        self.assertEqual([a for a,_ in p.scheduler.calls],['0047a61c','00479d70'])
        self.assertEqual(p.state.pipeline.execution.item_index,15)

    def test_maintenance_partial_field_gap_never_calls_route(self):
        o=observations();values=dict(o.scheduler);values['mining_after_merchant']=1
        p=replay_mining_frame(configuration(),entry(),replace(o,scheduler=values,maintenance={'storage_5690b8':0}),2000)
        self.assertFalse(p.complete);self.assertEqual(p.missing,('maintenance.storage_helper_4fe384',))
        self.assertIsNone(p.pipeline)

    def test_maintenance_return_does_not_guess_post_helper_route_byte(self):
        o=observations();values=dict(o.scheduler);values['mining_after_merchant']=1;del values['route_after_mining']
        p=replay_mining_frame(configuration(),entry(),replace(o,scheduler=values,maintenance={'storage_5690b8':1}),2000)
        self.assertFalse(p.complete);self.assertEqual(p.missing,('scheduler.route_after_mining',))
        self.assertIsNone(p.pipeline);self.assertTrue(p.maintenance_return_assumed_from_local_plan)

    def test_external_maintenance_marker_cannot_bypass_model(self):
        with self.assertRaises(ValueError):MiningFrameObservation({MAINTENANCE_RETURN:True})

    def test_maintenance_requires_fresh_lock_before_route(self):
        o=observations();values=dict(o.scheduler);values['mining_after_merchant']=1
        o=replace(o,scheduler=values,maintenance={'storage_5690b8':1})
        p=replay_mining_frame(configuration(),entry(),o,2000)
        self.assertFalse(p.complete);self.assertEqual(p.missing,('post_maintenance_lock_byte',))
        p=replay_mining_frame(configuration(),entry(),replace(o,post_maintenance_lock_byte=1),2000)
        self.assertTrue(p.complete);self.assertEqual(p.state.pipeline.execution.item_index,14)
        self.assertIsNone(p.pipeline.ore)

    def test_vip_direct_write_plan_remains_separate_from_game_execution(self):
        o=observations();values=dict(o.scheduler);values.update(mining_after_merchant=1,route_after_mining=0)
        c=configuration(**{'603b':0,'6038':0,'604c':1})
        maintenance=dict(storage_5690b8=0,storage_helper_4fe384=0,inn_helper_46fe90=0,
            full_463ac0=1,vip_tick=1001,vip_qword=0)
        p=replay_mining_frame(c,entry(),replace(o,scheduler=values,maintenance=maintenance),2000)
        self.assertTrue(p.complete);self.assertEqual(p.maintenance.status,'vip_operation4_planned')
        self.assertIn((0x5690b8,1,8),p.maintenance.writes)
        self.assertIsNone(p.pipeline);self.assertFalse(p.native_execution_verified)

    def test_swift_same_frame_lock_reaches_route_without_intervening_helper(self):
        speed=dict(lock_561f7e=0,dead_561f6f=0,ready_561f6e=1,blocked_561f70=0,
            merchant_568d81=0,route_5f54=1,actor_gate_initial=1,rogue_predicate_505d20=1,
            class_1=101,class_2=101,class_3=101,stat_462670=100,buff_1=0,buff_2=0,buff_3=0,
            retry_tick=2000,retry_qword=0,actor_gate_refresh=0,target_462630_first=0,
            target_gate_45dc44=0,actor_462650=1,cast_result=1,lock_stamp_tick=2001,
            retry_stamp_tick=2002,**{'returned:004655e8':True})
        p=replay_mining_frame(configuration(**{'6047':1,'6048':2}),entry(),
            replace(observations(),speed=speed),2000)
        self.assertTrue(p.complete);self.assertEqual(p.speed.status,'swift_planned')
        self.assertEqual(p.state.pipeline.execution.item_index,14)
        self.assertIsNone(p.pipeline.ore);self.assertEqual(p.state.queue.records,())

    def test_missing_name_does_not_commit_index(self):
        state=entry();p=replay_mining_frame(configuration(),state,replace(observations(),name=None),2000)
        self.assertFalse(p.complete);self.assertEqual(p.state,state)
        self.assertEqual(p.prospective_state.pipeline.execution.item_index,15)
        self.assertEqual(p.scheduler.missing,ROUTE_RETURN)

    def test_second_queue_gap_preserves_prefix_only(self):
        state=entry();o=observations();o=replace(o,queue_samples=o.queue_samples[:1])
        p=replay_mining_frame(configuration(),state,o,2000)
        self.assertFalse(p.complete);self.assertEqual(p.state,state)
        self.assertEqual(len(p.prospective_state.queue.records),1)
        self.assertEqual(p.queue.completed_calls,1)

    def test_post_route_reread_missing_holds_entire_local_commit(self):
        state=entry();o=observations();values=dict(o.scheduler);del values['active_after_route']
        p=replay_mining_frame(configuration(),state,replace(o,scheduler=values),2000)
        self.assertFalse(p.complete);self.assertEqual(p.state,state)
        self.assertEqual(p.missing,('scheduler.active_after_route',))
        self.assertEqual(len(p.prospective_state.queue.records),2)
        self.assertTrue(p.route_return_assumed_from_local_plan)

    def test_changed_empty_name_after_initial_match_is_early_return(self):
        o=observations();o=replace(o,name=replace(o.name,record=0),queue_samples=())
        p=replay_mining_frame(configuration(),entry(),o,2000)
        self.assertTrue(p.complete);self.assertEqual(p.state.pipeline.execution.item_index,15)
        self.assertEqual(p.state.queue.records,())
        self.assertEqual(p.request.request.status,'source_early_return')

    def test_caller_route_byte_cannot_disagree_with_entry_state(self):
        p=replay_mining_frame(configuration(),entry(active=False),observations(),2000)
        self.assertFalse(p.complete);self.assertEqual(p.status,'route_entry_state_mismatch')
        self.assertIsNone(p.pipeline)

    def test_external_return_marker_cannot_bypass_nested_model(self):
        with self.assertRaises(ValueError):MiningFrameObservation({ROUTE_RETURN:True})

    def test_cadence_skips_name_and_queue_requirements(self):
        o=replace(observations(),name=None,queue_samples=())
        p=replay_mining_frame(configuration(),entry(),o,999)
        self.assertTrue(p.complete);self.assertEqual(p.state.pipeline.execution.item_index,14)
        self.assertEqual(p.request.request.status,'request_not_reached')

    def test_two_disconnected_queue_calls_need_no_tick(self):
        o=replace(observations(),queue_samples=(QueueSample(connection_gate=0),QueueSample(connection_gate=0)))
        p=replay_mining_frame(configuration(),entry(),o,2000)
        self.assertTrue(p.complete);self.assertEqual(p.state.queue.records,())
        self.assertEqual(p.queue.completed_calls,2)

if __name__=='__main__':unittest.main()
