import unittest
from dataclasses import replace
from armor_start import (ITEM_IDS,armor_item_id,ArmorStartState,ArmorStartObservation,replay_armor_start,
                         capture_armor_start_state,apply_armor_start)
from npc_lookup import NpcCandidate
from operation_engine import UpgradeRunner


class ArmorStartTests(unittest.TestCase):
    def observation(self,**kw):
        o=ArmorStartObservation(filter_ready_returned=True,npc_id_dword=9,npc_pointer_dword=0x7000,
            x_offset_dword=4,y_offset_dword=8,x_ftol_dword=30,y_ftol_dword=100,distance_ftol_dword=9,
            first_combo_dword=0,second_combo_dword=22,bag_flag_byte=0,
            message_returns={n:True for n in ('npc_missing','too_far','item_missing','bag_full')},
            message_cleanup_returns={n:True for n in ('npc_missing','too_far','item_missing','bag_full')})
        return replace(o,**kw)

    def state(self,mode=1):return ArmorStartState({0x10:mode,0x60:8,0x50:99})

    def test_item_mapping_groups_blanks_and_default(self):
        self.assertEqual(len(ITEM_IDS),23)
        self.assertEqual([armor_item_id(i) for i in (0,6,12,18)],
                         [0x0bfb0829,0x0e5d6229,0x0f8e8f29,0x10bfbc29])
        for i in (5,11,17,23,0xffffffff):self.assertEqual(armor_item_id(i),0)
        for invalid in (None,True,-1,1<<32):
            with self.assertRaises(ValueError):armor_item_id(invalid)

    def test_success_separate_combo_reads_and_reset_only_counter_mode(self):
        p=replay_armor_start(self.state(),self.observation())
        self.assertTrue(p.complete and p.armed)
        self.assertEqual({k:p.state.fields[k] for k in (0x10,0x60,0x4c,0x48,0x58,0x5c)},
                         {0x10:2,0x60:0,0x4c:9,0x48:0x7000,0x58:0x0bfb0829,0x5c:22})
        self.assertEqual([c for c in p.calls if c[0].startswith('GetItemIndex')],
                         [('GetItemIndex:first','frmMain/MainTab/SheetUpgrade/GroupBox23/cmbUpgArmorList'),
                          ('GetItemIndex:second','frmMain/MainTab/SheetUpgrade/GroupBox23/cmbUpgArmorList')])
        self.assertFalse(p.independently_verified)

    def test_missing_filter_does_not_reach_npc(self):
        p=replay_armor_start(self.state(),self.observation(filter_ready_returned=None))
        self.assertFalse(p.complete);self.assertEqual(len(p.calls),1)
        self.assertEqual(p.state,self.state())

    def test_missing_npc_keeps_existing_mode_and_requires_message_returns(self):
        s=self.state(mode=2)
        p=replay_armor_start(s,self.observation(npc_id_dword=0,npc_pointer_dword=None))
        self.assertTrue(p.complete);self.assertFalse(p.armed)
        self.assertEqual((p.status,p.state.fields[0x10],p.state.fields[0x60]),('npc_missing',2,8))
        p=replay_armor_start(s,self.observation(npc_id_dword=0,message_returns={}))
        self.assertFalse(p.complete);self.assertEqual(p.prospective_state.fields[0x4c],0)

    def test_zero_pointer_silently_returns_without_coordinate_or_message(self):
        p=replay_armor_start(self.state(),self.observation(npc_pointer_dword=0,x_offset_dword=None))
        self.assertTrue(p.complete);self.assertFalse(p.armed)
        self.assertEqual((p.status,p.messages,p.state.fields[0x50]),('npc_pointer_zero',(),99))

    def test_signed_distance_ten_boundary_and_captured_intmin(self):
        p=replay_armor_start(self.state(),self.observation(distance_ftol_dword=10))
        self.assertEqual(p.status,'too_far');self.assertFalse(p.armed)
        p=replay_armor_start(self.state(),self.observation(distance_ftol_dword=0x80000000))
        self.assertTrue(p.armed)

    def test_blank_item_returns_before_second_combo_and_bag(self):
        p=replay_armor_start(self.state(),self.observation(first_combo_dword=5,second_combo_dword=None,bag_flag_byte=None))
        self.assertEqual(p.status,'item_missing');self.assertEqual(p.state.fields[0x58],0)
        self.assertNotIn(('00463ac0',0),p.calls)
        self.assertFalse(any(c[0]=='GetItemIndex:second' for c in p.calls))

    def test_second_combo_gap_and_nonzero_bag_preserve_prefix(self):
        s=self.state();p=replay_armor_start(s,self.observation(second_combo_dword=None))
        self.assertFalse(p.complete);self.assertEqual(p.state,s)
        self.assertEqual(p.prospective_state.fields[0x58],0x0bfb0829)
        p=replay_armor_start(s,self.observation(bag_flag_byte=255))
        self.assertEqual(p.status,'bag_full');self.assertEqual((p.state.fields[0x10],p.state.fields[0x60]),(1,8))

    def test_bound_selector_requires_completion_and_keeps_its_distance_separate(self):
        o=self.observation(npc_id_dword=None,lookup_candidates=(NpcCandidate(7,11,b'[Armor Merchant]'),NpcCandidate(7)),traversal_complete=True)
        p=replay_armor_start(self.state(),o)
        self.assertTrue(p.armed);self.assertEqual(p.state.fields[0x4c],11)
        self.assertEqual(p.lookup.distance_integer,7)
        p=replay_armor_start(self.state(),replace(o,traversal_complete=False))
        self.assertFalse(p.complete);self.assertNotIn(0x4c,p.prospective_state.fields)
        with self.assertRaises(ValueError):replay_armor_start(self.state(),replace(o,npc_id_dword=11))

    def test_apply_preserves_queue_and_clocks_and_rejects_stale_input(self):
        r=UpgradeRunner(source_clock=True);r.queue=(11,);r.armor_attempts=8
        r.queue_stamp_qword=777;r.armor_stamp_qword=999
        p=replay_armor_start(capture_armor_start_state(r),self.observation())
        apply_armor_start(r,p)
        self.assertEqual((r.state,r.armor_attempts,r.queue,r.queue_stamp_qword,r.armor_stamp_qword),(2,0,(11,),777,999))
        with self.assertRaises(ValueError):apply_armor_start(r,p)
        p=replay_armor_start(capture_armor_start_state(r),self.observation(first_combo_dword=None))
        with self.assertRaises(ValueError):apply_armor_start(r,p)
