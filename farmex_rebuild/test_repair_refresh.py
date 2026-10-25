import unittest
from dataclasses import replace
from repair_refresh import RepairRefreshObservation,plan_repair_refresh

class RepairRefreshTests(unittest.TestCase):
    def observation(self,slot=1,profile=1):
        return RepairRefreshObservation(0x12345678,slot,
            {0x553e80:0x1000,0x5540a8:0x20,0x5540ac:0x80,0x5540b8:0x400,
             0x553e46:profile,0x553ef8:0x7000,0x553ef4:0x8000},
            ((0x1000,0x2000),(0x2020,0x3000),(0x3080+slot*4,0x4000),
             (0x1000,0x5000),(0x5020,0x6000)),
            ((0x1000,0x9000),(0x9020,0xa000)),profile)

    def test_three_independent_root_snapshots_and_native_context(self):
        p=plan_repair_refresh(self.observation())
        self.assertTrue(p.complete)
        self.assertEqual([r[2] for r in p.reads if r[1]==0x1000],[0x2000,0x5000,0x9000])
        self.assertEqual(p.native_call.ecx,0xa400)
        self.assertEqual(p.native_call.push_order,(0x12345678,1))
        self.assertTrue(p.native_call.preserve_gprs_and_flags)
        self.assertFalse(p.native_call.abi_verified)
        self.assertEqual(p.write_requests,(
            ('0045ddf4',0x6420,b'\0\x40\0\0'),
            ('0045ddf4',0x6424,b'\1\0\0\0'),
            ('0045ddf4',0x6428,b'\1\0\0\0'),
            ('0045de4c',0x8000,b'\0')))
        self.assertFalse(p.memory_effects_verified);self.assertFalse(p.helper_return_verified)

    def test_profile2_uses_inventory_without_scratch_addend(self):
        p=plan_repair_refresh(self.observation(profile=2))
        self.assertEqual(p.native_call.ecx,0xa000)
        self.assertEqual(p.native_call.target,0x7000)

    def test_other_profile_bytes_skip_native_but_keep_four_write_requests(self):
        for profile in (0,3,255):
            obs=self.observation(profile=profile)
            g=dict(obs.globals);g.pop(0x553ef8)
            p=plan_repair_refresh(replace(obs,globals=g,direct_samples=()))
            self.assertTrue(p.complete);self.assertIsNone(p.native_call)
            self.assertEqual(len(p.write_requests),4);self.assertEqual(len(p.reads),5)

    def test_slot13_14_255_kind_and_relative_index(self):
        for slot,kind,index in ((13,1,13),(14,2,0),(255,2,241)):
            p=plan_repair_refresh(self.observation(slot=slot))
            self.assertEqual(int.from_bytes(p.write_requests[1][2],'little'),kind)
            self.assertEqual(int.from_bytes(p.write_requests[2][2],'little'),index)

    def test_repeated_protected_read_is_required_not_reused(self):
        obs=self.observation()
        p=plan_repair_refresh(replace(obs,protected_samples=obs.protected_samples[:3]))
        self.assertFalse(p.complete);self.assertEqual(p.write_requests,())
        self.assertIn('protected sample3 DWORD00001000',p.missing)

    def test_missing_direct_snapshot_preserves_only_prior_write_requests(self):
        p=plan_repair_refresh(replace(self.observation(),direct_samples=()))
        self.assertFalse(p.complete);self.assertEqual(len(p.write_requests),3)
        self.assertIsNone(p.native_call)

    def test_missing_final_byte_address_is_after_native_call_plan(self):
        obs=self.observation();g=dict(obs.globals);g.pop(0x553ef4)
        p=plan_repair_refresh(replace(obs,globals=g))
        self.assertFalse(p.complete);self.assertIsNotNone(p.native_call)
        self.assertEqual(len(p.write_requests),3)

    def test_address_mismatch_not_silently_used_and_mapping_is_immutable(self):
        obs=self.observation()
        with self.assertRaises(ValueError):plan_repair_refresh(replace(obs,protected_samples=((0x9999,0),)))
        g=dict(obs.globals);o=replace(obs,globals=g);g.clear()
        self.assertTrue(plan_repair_refresh(o).complete)
        with self.assertRaises(ValueError):replace(obs,slot=256)

    def test_low_dword_pointer_wrap_and_zero_slot_pointer_are_preserved(self):
        obs=RepairRefreshObservation(0,0,{0x553e80:0x1000,0x5540a8:0x20,0x5540ac:0x80,
            0x5540b8:0x400,0x553e46:0,0x553ef4:0},
            ((0x1000,0xfffffff0),(0x10,0xffffffc0),(0x40,0),
             (0x1000,0xfffffff0),(0x10,0xffffffc0)),second_profile_byte=0)
        p=plan_repair_refresh(obs)
        self.assertTrue(p.complete);self.assertEqual(p.write_requests[0][1],0x3e0)
        self.assertEqual(p.write_requests[0][2],b'\0'*4)

    def test_second_profile_byte_is_fresh_and_read_only_after_first_not1(self):
        obs=self.observation(profile=0)
        p=plan_repair_refresh(replace(obs,second_profile_byte=None))
        self.assertFalse(p.complete);self.assertEqual(len(p.write_requests),3)
        p=plan_repair_refresh(replace(obs,second_profile_byte=2))
        self.assertEqual(p.native_call.ecx,0xa000)
        p=plan_repair_refresh(replace(self.observation(profile=2),second_profile_byte=1,direct_samples=()))
        self.assertTrue(p.complete);self.assertIsNone(p.native_call)
        self.assertTrue(plan_repair_refresh(replace(self.observation(profile=1),second_profile_byte=None)).complete)

if __name__=='__main__':unittest.main()
