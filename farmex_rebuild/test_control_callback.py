import unittest
from dataclasses import replace
from control_callback import *
from attack_lock import LockCallbackObservation
from action_queue import CallbackQueueGate
from control_guards import ControlGuardConfiguration,ControlGuardObservation
from control_continuation import ControlContinuationObservation
from control_alarms import ControlAlarmObservation,LootActivityState
from party_help import PartyHelpState,PartyHelpConfiguration,PartyHelpObservation

class ControlCallbackTests(unittest.TestCase):
    def state(self):return ControlCallbackState(AttackLockState(1,2000,1000),ControlFrameState(PartyHelpState(),LootActivityState()))
    def prefix(self,active=1):return LockCallbackObservation(0,0,0,active,{a:True for a in ('00458c70','004c79a0','0045a4dc')})
    def inputs(self):
        c=ControlFrameConfiguration(ControlGuardConfiguration({0xbf:0,0xc0:0,0xd0:0}),
            ControlGuardConfiguration({0xd8:0}),None,ControlGuardConfiguration({0xec:0}))
        o=ControlFrameObservation(ControlGuardObservation(),ControlContinuationObservation(runtime_mode=2),None,ControlAlarmObservation())
        return ControlCallbackInputs(c,o,AttackLockState(1,2000,1000))
    def run_plan(self,inputs=None,prefix=None,state=None,clock=3000):
        return replay_control_callback(state or self.state(),CallbackQueueGate(1,1,0,0,1),prefix or self.prefix(),inputs or self.inputs(),clock)

    def test_bound_control_return_then_fresh_timer_unlock(self):
        p=self.run_plan()
        self.assertTrue(p.complete);self.assertTrue(p.control_return_assumed_from_local_plan)
        self.assertEqual(p.control.status,'control_return_planned');self.assertEqual(p.state.lock.byte,0)
        self.assertEqual(p.unlock.calls,('00458c70','004c79a0','0045a4dc','00458f98','005074da'))
        self.assertFalse(p.native_execution_verified)

    def test_external_whole_control_completion_is_rejected(self):
        for flag in (None,False,True):
            prefix=replace(self.prefix(),completed={**self.prefix().completed,'00458f98':flag})
            with self.assertRaises(ValueError):self.run_plan(prefix=prefix)

    def test_reached_control_requires_typed_config_state_and_observation(self):
        p=self.run_plan(inputs=ControlCallbackInputs())
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_control_frame');self.assertFalse(p.unlock.timer_reached)
        p=self.run_plan(state=ControlCallbackState(self.state().lock,None))
        self.assertEqual(p.status,'needs_control_frame')

    def test_earlier_helper_or_worker_exit_does_not_invoke_control(self):
        prefix=replace(self.prefix(),completed={})
        p=self.run_plan(inputs=ControlCallbackInputs(),prefix=prefix)
        self.assertEqual(p.status,'needs_prefix_observation');self.assertIsNone(p.control)
        p=self.run_plan(inputs=ControlCallbackInputs(),prefix=replace(self.prefix(),byte_568dbc=1))
        self.assertTrue(p.complete);self.assertEqual(p.status,'callback_skipped_control');self.assertIsNone(p.control)

    def test_inactive_control_still_needs_fresh_timer_lock_after_other_helpers(self):
        p=self.run_plan(inputs=ControlCallbackInputs(),prefix=self.prefix(0))
        self.assertEqual(p.status,'needs_timer_lock_observation');self.assertIsNone(p.control)
        p=self.run_plan(inputs=ControlCallbackInputs(timer_lock=AttackLockState(0,9000,2999)),prefix=self.prefix(0))
        self.assertTrue(p.complete);self.assertEqual(p.state.lock.duration_ms,9000)
        self.assertFalse(p.control_return_assumed_from_local_plan)

    def test_control_missing_observation_or_timer_snapshot_cannot_clear_old_lock(self):
        i=self.inputs()
        c=replace(i.configuration,entry=ControlGuardConfiguration({0xbf:1}))
        p=self.run_plan(inputs=replace(i,configuration=c))
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_control_observation')
        self.assertEqual(p.state.lock.byte,1);self.assertFalse(p.unlock.timer_reached)
        p=self.run_plan(inputs=replace(i,timer_lock=None))
        self.assertFalse(p.complete);self.assertTrue(p.control_return_assumed_from_local_plan)
        self.assertEqual(p.status,'needs_timer_lock_observation');self.assertEqual(p.state.lock.byte,1)

    def test_fresh_post_control_lock_replaces_stale_persisted_values(self):
        p=self.run_plan(inputs=replace(self.inputs(),timer_lock=AttackLockState(1,9000,2990)))
        self.assertTrue(p.complete);self.assertEqual(p.unlock.status,'wait_lock_duration')
        self.assertEqual(p.state.lock,AttackLockState(1,9000,2990))

    def test_clock_termination_plan_cannot_assume_control_return_or_reach_timer(self):
        i=self.inputs();c=replace(i.configuration,clock_party=ControlGuardConfiguration({0xd8:1,0xdc:15,0xe0:0}))
        o=replace(i.frame_observation,clock_party=ControlContinuationObservation(local_hour=15,local_minute=0,current_process_handle=1))
        p=self.run_plan(inputs=replace(i,configuration=c,frame_observation=o,timer_lock=AttackLockState()))
        self.assertFalse(p.complete);self.assertEqual(p.status,'control_return_unproven')
        self.assertTrue(p.control.termination_call_planned);self.assertFalse(p.unlock.timer_reached)
        self.assertFalse(p.control_return_assumed_from_local_plan)

    def test_missing_unlock_clock_keeps_fresh_lock_only_as_prospective_prefix(self):
        p=self.run_plan(clock=None)
        self.assertFalse(p.complete);self.assertEqual(p.status,'needs_unlock_observation')
        self.assertTrue(p.unlock.timer_reached);self.assertEqual(p.unlock.reason,'unlock GetTickCount')

if __name__=='__main__':unittest.main()
