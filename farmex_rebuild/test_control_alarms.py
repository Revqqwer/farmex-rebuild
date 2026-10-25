import unittest
import json
from pathlib import Path
from control_alarms import *
from loot_records import plan_loot_creation
from profiles import Profiles

class ControlAlarmTests(unittest.TestCase):
    def config(self,loot=0,devil=0):return ControlGuardConfiguration({0xee:loot,0xec:devil})
    def plan(self,cfg,state,obs,entry=0x459496):return plan_control_alarm_tail(cfg,state,obs,entry_address=entry)

    def test_alarm_fields_compile_from_real_profile_group41(self):
        profiles=Profiles(json.loads(Path(__file__).with_name('ui_model.json').read_text(encoding='utf-8')))
        values=dict(profiles.defaults)
        for path in FLAG_PATHS:self.assertIn(path,values);self.assertIn('/GroupBox41/',path)
        c=compile_control_alarms(values)
        self.assertEqual(set(c.fields),{0xee,0xec})

    def test_opcode23_activity_updates_independently_of_loot_enable_and_capture_guard(self):
        p=plan_loot_activity(b'\x23',123)
        self.assertTrue(p.complete);self.assertEqual(p.global_writes,((0x562284,123),(0x562288,0)))
        self.assertEqual(apply_loot_activity(LootActivityState(),p).last_activity_qword,123)
        creation=plan_loot_creation(b'\x23',0)
        self.assertEqual(creation.status,'dispatch_disabled')
        self.assertEqual(plan_loot_creation(b'\x23',1).status,'needs_capture_observation')

    def test_activity_clock_is_separate_from_creation_clock(self):
        captured=b'\x23'+(1).to_bytes(4,'little')+(2).to_bytes(4,'little')+b'\1'
        activity=plan_loot_activity(captured,100)
        creation=plan_loot_creation(captured,1,lookup_result=0,created_tick=101)
        self.assertEqual(dict(activity.global_writes)[0x562284],100)
        self.assertEqual(creation.created_tick,101)

    def test_missing_activity_opcode_or_clock_and_other_opcode_preserves_state(self):
        self.assertFalse(plan_loot_activity(b'').complete)
        self.assertFalse(plan_loot_activity(b'\x23').complete)
        state=LootActivityState(123)
        self.assertIs(apply_loot_activity(state,plan_loot_activity(b'\x24')),state)

    def test_no_loot600000_boundary_and_repeated_alarm_does_not_reset_stamp(self):
        state=LootActivityState(1)
        for now,expected in ((600000,()),(600001,('no_loot',)),(600002,('no_loot',))):
            p=self.plan(self.config(1),state,ControlAlarmObservation(now,alarm_returns={'no_loot':True}))
            self.assertTrue(p.complete);self.assertEqual(p.alarm_requests,expected)
        self.assertEqual(state.last_activity_qword,1)

    def test_zero_activity_disables_timer_and_wrap_is_signed_qword_not_dword(self):
        p=self.plan(self.config(1),LootActivityState(0),ControlAlarmObservation())
        self.assertTrue(p.complete);self.assertEqual(p.calls,())
        p=self.plan(self.config(1),LootActivityState(0xfffffff0),ControlAlarmObservation(700000))
        self.assertTrue(p.complete);self.assertEqual(p.alarm_requests,())

    def test_entry519_skips_no_loot_flag_and_state_even_if_unknown(self):
        p=self.plan(ControlGuardConfiguration({0xec:0}),LootActivityState(),ControlAlarmObservation(),0x459519)
        self.assertTrue(p.complete);self.assertTrue(p.source_return_planned)

    def test_unknown_alarm_data_or_return_is_not_success(self):
        p=self.plan(self.config(1),LootActivityState(),ControlAlarmObservation())
        self.assertEqual(p.missing,'source last-activity QWORD')
        p=self.plan(self.config(1),LootActivityState(1),ControlAlarmObservation())
        self.assertEqual(p.missing,'alarm GetTickCount DWORD')
        p=self.plan(self.config(1),LootActivityState(1),ControlAlarmObservation(600001))
        self.assertFalse(p.complete);self.assertEqual(p.alarm_requests,('no_loot',))
        self.assertFalse(p.native_execution_verified)

    def test_fresh_name_for_each_comparison_no_reuse_of_first_read(self):
        names={(14,0):b'Other',(14,1):b'Claw of Devil'}
        p=self.plan(self.config(devil=1),LootActivityState(),ControlAlarmObservation(name_samples=names,alarm_returns={'devil_item':True}),0x459519)
        self.assertTrue(p.complete);self.assertEqual(p.matching_sample,(14,1))
        self.assertEqual(p.visited,((14,0),(14,1)))
        self.assertEqual(p.alarm_requests,('devil_item',))
        missing=self.plan(self.config(devil=1),LootActivityState(),ControlAlarmObservation(name_samples={(14,0):b'Other'}),0x459519)
        self.assertEqual(missing.missing,'fresh name slot14 comparison1');self.assertEqual(missing.alarm_requests,())

    def test_all28slots_and8names_scan224_fresh_samples(self):
        names={(slot,index):b'' for slot in range(14,42) for index in range(8)}
        p=self.plan(self.config(devil=1),LootActivityState(),ControlAlarmObservation(name_samples=names),0x459519)
        self.assertTrue(p.complete);self.assertEqual(len(p.visited),224)
        self.assertEqual(p.visited[-1],(41,7));self.assertEqual(p.alarm_requests,())

    def test_exact_ansi_equality_no_casefold_substring_or_nul_stripping(self):
        for name in (b'teeth of devil',b'[Teeth of Devil]',b'Teeth of Devil\0'):
            names={(slot,index):b'' for slot in range(14,42) for index in range(8)};names[(14,0)]=name
            p=self.plan(self.config(devil=1),LootActivityState(),ControlAlarmObservation(name_samples=names),0x459519)
            self.assertTrue(p.complete);self.assertIsNone(p.matching_sample)

    def test_two_alarm_returns_are_independent_and_prefix_survives_unknown_name(self):
        p=self.plan(self.config(1,1),LootActivityState(1),ControlAlarmObservation(600001,alarm_returns={'no_loot':True}))
        self.assertFalse(p.complete);self.assertEqual(p.alarm_requests,('no_loot',));self.assertEqual(p.missing,'fresh name slot14 comparison0')
        p=self.plan(self.config(1,1),LootActivityState(1),ControlAlarmObservation(600001,{(14,0):b'Teeth of Devil'},{'no_loot':True}))
        self.assertFalse(p.complete);self.assertEqual(p.alarm_requests,('no_loot','devil_item'))
        self.assertEqual(p.missing,'devil_item 00404260 normal return')

    def test_activity_tick0_is_not_replaced_and_observations_are_copied(self):
        state=apply_loot_activity(LootActivityState(1),plan_loot_activity(b'\x23',0))
        self.assertEqual(state.last_activity_qword,0)
        names={(14,0):b'Teeth of Devil'};returns={'devil_item':True}
        obs=ControlAlarmObservation(name_samples=names,alarm_returns=returns);names.clear();returns.clear()
        self.assertTrue(self.plan(self.config(devil=1),state,obs,0x459519).complete)

if __name__=='__main__':unittest.main()
