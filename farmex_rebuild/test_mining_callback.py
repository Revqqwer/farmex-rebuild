import unittest
from dataclasses import replace
from mining_callback import *
from mining_configuration import MiningPanelConfiguration
from mining_pipeline import MiningPipelineState,MiningPipelineObservation
from mining_engine import MiningExecutionState,OreSlotState,MiningSnapshot,OreSlotSnapshot

def state():
    return MiningCallbackState(AttackLockState(1,2000,1000),MiningFrameState(
        MiningPipelineState(MiningExecutionState(phase=2,route_active=True),OreSlotState())))

def cfg():return MiningPanelConfiguration('fixture',{
    0x6047:0,0x6029:0,0x602c:0,0x6035:0,0x604c:0,0x6030:1,0x6034:0})

def obs(clock=3000,post_lock=AttackLockState(0,2000,1000)):
    return MiningCallbackObservation(CallbackQueueGate(1,1,0,0,1),
        LockCallbackObservation(0,0,0,1,{a:True for a in ('00458c70','004c79a0','0045a4dc','00458f98')}),
        clock,True,post_lock,2,MiningFrameObservation(
            dict(active_initial=1,dead=0,merchant_after_speed=0,mining_after_merchant=0,
                 route_after_mining=1,active_after_route=0),
            MiningPipelineObservation(MiningSnapshot(comparison_505118=True,helper_477770_count=1,
                helper_464a10_result=True,distance_ore=1),OreSlotSnapshot(False))))

class MiningCallbackTests(unittest.TestCase):
    def test_bound_control_model_replaces_external_marker_before_mining(self):
        from test_control_callback import ControlCallbackTests
        helper=ControlCallbackTests();inputs=helper.inputs();control_state=helper.state().control
        o=obs();prefix=replace(o.prefix,completed={k:v for k,v in o.prefix.completed.items() if k!='00458f98'})
        p=replay_mining_callback(cfg(),replace(state(),control=control_state),replace(o,prefix=prefix,control=inputs),3000)
        self.assertTrue(p.complete);self.assertIsNotNone(p.control)
        self.assertTrue(p.control.control_return_assumed_from_local_plan)
        self.assertEqual(p.state.frame.pipeline.execution.item_index,15)
        self.assertEqual(p.state.control,control_state)
        # Both recovered callers compose without either whole-helper marker.
        from callback_interlude import CallbackInterludeState,CallbackInterludeObservation
        bound_state=replace(state(),control=control_state,interlude=CallbackInterludeState(1000,0))
        bound_observation=replace(o,prefix=prefix,control=inputs,post_timer_completed=None,
            interlude=CallbackInterludeObservation(3000,0,predicate_al=1,flag_after_predicate=1,final_random_return=70000))
        combined=replay_mining_callback(cfg(),bound_state,bound_observation,3000)
        self.assertTrue(combined.complete);self.assertIsNotNone(combined.control)
        self.assertTrue(combined.interlude.segment_fallthrough_planned)
        self.assertEqual(combined.state.interlude,CallbackInterludeState(70000,3000))
        self.assertEqual(combined.state.frame.pipeline.execution.item_index,15)

    def test_bound_control_missing_post_timer_data_preserves_only_prospective_control_writes(self):
        from control_frame import ControlFrameConfiguration,ControlFrameObservation,ControlFrameState
        from control_guards import ControlGuardConfiguration,ControlGuardObservation
        from control_continuation import ControlContinuationObservation
        from control_alarms import ControlAlarmObservation,LootActivityState
        from party_help import PartyHelpConfiguration,PartyHelpObservation,PartyHelpState
        c=ControlFrameConfiguration(ControlGuardConfiguration({0xbf:0,0xc0:0,0xd0:0}),
            ControlGuardConfiguration({0xd8:0,0xe8:0,0xe9:0,0xea:0,0xeb:0}),
            PartyHelpConfiguration({k:0 for k in (0x103,0x104,0x105,0x106)},{}),ControlGuardConfiguration({0xee:0,0xec:0}))
        co=ControlFrameObservation(ControlGuardObservation(),ControlContinuationObservation(runtime_mode=0),
            PartyHelpObservation(party_count=2,outer_tick=5000,final_tick=5001),ControlAlarmObservation())
        cs=ControlFrameState(PartyHelpState({0x553cb4:0}),LootActivityState())
        o=obs();prefix=replace(o.prefix,completed={k:v for k,v in o.prefix.completed.items() if k!='00458f98'})
        s=replace(state(),control=cs)
        o=replace(o,prefix=prefix,post_timer_completed=None,control=ControlCallbackInputs(c,co,AttackLockState()))
        p=replay_mining_callback(cfg(),s,o,3000)
        self.assertFalse(p.complete);self.assertEqual(p.state,s)
        self.assertEqual(p.prospective_state.control.party_help.timers[0x553cb4],5001)
        self.assertEqual(p.state.control.party_help.timers[0x553cb4],0)

    def test_bound_interlude_replaces_completion_but_still_needs_fresh_lock(self):
        from callback_interlude import CallbackInterludeState,CallbackInterludeObservation
        s=replace(state(),interlude=CallbackInterludeState(1000,0))
        o=replace(obs(),post_timer_completed=None,post_timer_lock=None,
            interlude=CallbackInterludeObservation(3000,0,predicate_al=1,flag_after_predicate=1,final_random_return=70000))
        p=replay_mining_callback(cfg(),s,o,3000)
        self.assertEqual(p.status,'needs_post_timer_lock');self.assertEqual(p.state,s)
        self.assertEqual(p.prospective_state.interlude,CallbackInterludeState(70000,3000))
        p=replay_mining_callback(cfg(),s,replace(o,post_timer_lock=AttackLockState()),3000)
        self.assertTrue(p.complete);self.assertTrue(p.interlude.segment_fallthrough_planned)
        self.assertEqual(p.state.interlude,CallbackInterludeState(70000,3000))
        for flag in (False,True):
            with self.assertRaises(ValueError):replay_mining_callback(cfg(),s,replace(o,post_timer_completed=flag),3000)

    def test_bound_interlude_gap_cannot_reach_mining_or_commit_unlock(self):
        from callback_interlude import CallbackInterludeState,CallbackInterludeObservation
        s=replace(state(),interlude=CallbackInterludeState(1000,0))
        o=replace(obs(),post_timer_completed=None,interlude=CallbackInterludeObservation(3000,0))
        p=replay_mining_callback(cfg(),s,o,3000)
        self.assertEqual(p.status,'needs_interlude_observation');self.assertEqual(p.state,s)
        self.assertEqual(p.prospective_state.lock.byte,0);self.assertIsNone(p.frame)
        p=replay_mining_callback(cfg(),state(),o,3000)
        self.assertEqual(p.status,'needs_interlude_state')

    def test_unlock_before_mining_2000_boundary(self):
        p=replay_mining_callback(cfg(),state(),obs(),3000)
        self.assertTrue(p.complete);self.assertEqual(p.unlock.status,'lock_cleared')
        self.assertEqual(p.state.lock,AttackLockState(0,2000,1000))
        self.assertEqual(p.state.frame.pipeline.execution.item_index,15)
        self.assertFalse(p.native_execution_verified);self.assertFalse(p.server_acknowledged)

    def test_1999_remains_blocked(self):
        p=replay_mining_callback(cfg(),state(),obs(2999,AttackLockState(1,2000,1000)),2999)
        self.assertTrue(p.complete);self.assertEqual(p.unlock.status,'wait_lock_duration')
        self.assertEqual(p.state.frame.pipeline.execution.item_index,14)

    def test_worker_branch_skips_timer_and_mining(self):
        o=obs();o=replace(o,prefix=replace(o.prefix,byte_568dbc=1))
        p=replay_mining_callback(cfg(),state(),o,3000)
        self.assertTrue(p.complete);self.assertEqual(p.status,'callback_skipped_mining')
        self.assertEqual(p.state,state());self.assertIsNone(p.frame)

    def test_missing_intermediate_completion_does_not_commit_timer_prefix(self):
        p=replay_mining_callback(cfg(),state(),replace(obs(),post_timer_completed=None),3000)
        self.assertFalse(p.complete);self.assertEqual(p.state,state())
        self.assertEqual(p.prospective_state.lock.byte,0);self.assertIsNone(p.frame)

    def test_post_segment_lock_not_inferred_from_timer(self):
        p=replay_mining_callback(cfg(),state(),replace(obs(),post_timer_lock=None),3000)
        self.assertEqual(p.status,'needs_post_timer_lock');self.assertIsNone(p.frame)
        p=replay_mining_callback(cfg(),state(),obs(post_lock=AttackLockState(1,9000,2990)),3000)
        self.assertTrue(p.complete);self.assertEqual(p.state.frame.pipeline.execution.item_index,14)
        self.assertEqual(p.state.lock.duration_ms,9000)

    def test_other_mode_not_claimed_as_completed_callback(self):
        p=replay_mining_callback(cfg(),state(),replace(obs(),mode_after_segment=3),3000)
        self.assertFalse(p.complete);self.assertIsNone(p.frame)

    def test_dword_timer_wrap_is_preserved(self):
        s=replace(state(),lock=AttackLockState(1,32,0xfffffff0))
        o=obs(0x10,AttackLockState(0,32,0xfffffff0))
        p=replay_mining_callback(cfg(),s,o,3000)
        self.assertTrue(p.complete);self.assertEqual(p.unlock.status,'lock_cleared')

    def test_missing_nested_frame_rolls_back_only_local_commit(self):
        o=obs();o=replace(o,frame=replace(o.frame,scheduler={}))
        p=replay_mining_callback(cfg(),state(),o,3000)
        self.assertFalse(p.complete);self.assertEqual(p.state,state())
        self.assertEqual(p.prospective_state.lock.byte,0)

    def test_swift_can_relock_after_timer_clear_in_same_callback(self):
        o=obs()
        speed=dict(lock_561f7e=1,dead_561f6f=0,ready_561f6e=1,blocked_561f70=0,
            merchant_568d81=0,route_5f54=1,actor_gate_initial=1,rogue_predicate_505d20=1,
            class_1=101,class_2=101,class_3=101,stat_462670=100,buff_1=0,buff_2=0,buff_3=0,
            retry_tick=3000,retry_qword=0,actor_gate_refresh=0,target_462630_first=0,
            target_gate_45dc44=0,actor_462650=1,cast_result=1,lock_stamp_tick=3001,
            retry_stamp_tick=3002,**{'returned:004655e8':True})
        values=dict(cfg().fields);values.update({0x6047:1,0x6048:2})
        p=replay_mining_callback(MiningPanelConfiguration('fixture',values),state(),
            replace(o,frame=replace(o.frame,speed=speed)),3000)
        self.assertTrue(p.complete);self.assertEqual(p.unlock.status,'lock_cleared')
        self.assertEqual(p.state.lock,AttackLockState(1,2000,3001))
        self.assertEqual(p.state.frame.pipeline.execution.item_index,14)

        # A later explicit lock observation must not be overwritten by the
        # earlier Swift write when the maintenance stage was reached.
        values2=dict(o.frame.scheduler);values2['mining_after_merchant']=1
        frame2=replace(o.frame,scheduler=values2,speed=speed,
            maintenance={'storage_5690b8':1},post_maintenance_lock_byte=0)
        p2=replay_mining_callback(MiningPanelConfiguration('fixture',values),state(),
            replace(o,frame=frame2),3000)
        self.assertTrue(p2.complete);self.assertEqual(p2.state.lock.byte,0)
        self.assertEqual(p2.state.lock.started_ms,3001)
        # The later BYTE cannot be consumed while maintenance has not returned.
        p3=replay_mining_callback(MiningPanelConfiguration('fixture',values),state(),
            replace(o,frame=replace(frame2,maintenance={})),3000)
        self.assertFalse(p3.complete);self.assertEqual(p3.prospective_state.lock.byte,1)
        self.assertEqual(p3.prospective_state.lock.started_ms,3001)

if __name__=='__main__':unittest.main()
