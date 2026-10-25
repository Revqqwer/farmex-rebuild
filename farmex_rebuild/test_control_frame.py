import unittest
from control_frame import *
from control_guards import ControlGuardConfiguration,ControlGuardObservation
from control_continuation import ControlContinuationObservation
from party_help import PartyHelpConfiguration,PartyHelpObservation
from control_alarms import ControlAlarmObservation

class ControlFrameTests(unittest.TestCase):
    def entry(self):return ControlGuardConfiguration({0xbf:0,0xc0:0,0xd0:0})
    def follow(self):return ControlGuardConfiguration({0xd8:0,0xe8:0,0xe9:0,0xea:0,0xeb:0})
    def state(self):return ControlFrameState(PartyHelpState({0x553cb4:0}),LootActivityState(1))

    def test_np_early_return_excludes_all_later_configs_and_observations(self):
        c=ControlFrameConfiguration(ControlGuardConfiguration({0xbf:1}))
        p=replay_control_frame(c,self.state(),ControlFrameObservation(ControlGuardObservation(np_462718=0,stop_returned=True,town_returned=True)))
        self.assertTrue(p.complete);self.assertTrue(p.source_return_planned)
        self.assertIsNone(p.clock_party);self.assertIsNone(p.party_help);self.assertIsNone(p.alarms)

    def test_nonzero_mode_skips_help_and_no_loot_but_reaches_item_tail(self):
        c=ControlFrameConfiguration(self.entry(),ControlGuardConfiguration({0xd8:0}),None,ControlGuardConfiguration({0xec:0}))
        o=ControlFrameObservation(ControlGuardObservation(),ControlContinuationObservation(runtime_mode=2),None,ControlAlarmObservation())
        p=replay_control_frame(c,self.state(),o)
        self.assertTrue(p.complete);self.assertTrue(p.source_return_planned)
        self.assertIsNone(p.party_help);self.assertIsNotNone(p.alarms)

    def test_mode0_help_clock_writes_before_alarm_and_incomplete_tail_freezes_acceptance(self):
        c=ControlFrameConfiguration(self.entry(),self.follow(),PartyHelpConfiguration({k:0 for k in (0x103,0x104,0x105,0x106)},{}),ControlGuardConfiguration({0xee:1,0xec:0}))
        help_obs=PartyHelpObservation(party_count=2,outer_tick=5000,final_tick=5001)
        o=ControlFrameObservation(ControlGuardObservation(),ControlContinuationObservation(runtime_mode=0),help_obs,ControlAlarmObservation(600001))
        state=self.state();p=replay_control_frame(c,state,o)
        self.assertFalse(p.complete);self.assertIs(p.state,state)
        self.assertEqual(p.prospective_state.party_help.timers[0x553cb4],5001)
        self.assertEqual(p.alarms.alarm_requests,('no_loot',))
        o=ControlFrameObservation(o.entry,o.clock_party,o.party_help,ControlAlarmObservation(600001,alarm_returns={'no_loot':True}))
        p=replay_control_frame(c,state,o)
        self.assertTrue(p.complete);self.assertEqual(p.state.party_help.timers[0x553cb4],5001)
        self.assertEqual(p.state.loot_activity.last_activity_qword,1)
        self.assertTrue(p.source_return_planned);self.assertFalse(p.native_execution_verified)

    def test_missing_help_input_cannot_bypass_to_alarm(self):
        c=ControlFrameConfiguration(self.entry(),self.follow(),None,ControlGuardConfiguration({0xee:0,0xec:0}))
        p=replay_control_frame(c,self.state(),ControlFrameObservation(ControlGuardObservation(),ControlContinuationObservation(runtime_mode=0),None,ControlAlarmObservation()))
        self.assertFalse(p.complete);self.assertEqual(p.missing,'party-help stage');self.assertIsNone(p.alarms)

    def test_clock_termination_plan_is_not_return_or_execution_proof(self):
        c=ControlFrameConfiguration(self.entry(),ControlGuardConfiguration({0xd8:1,0xdc:15,0xe0:0}))
        o=ControlFrameObservation(ControlGuardObservation(),ControlContinuationObservation(local_hour=15,local_minute=0,current_process_handle=1))
        p=replay_control_frame(c,self.state(),o)
        self.assertTrue(p.complete);self.assertTrue(p.termination_call_planned)
        self.assertFalse(p.source_return_planned);self.assertFalse(p.native_execution_verified)
        self.assertIsNone(p.party_help);self.assertIsNone(p.alarms)

if __name__=='__main__':unittest.main()
