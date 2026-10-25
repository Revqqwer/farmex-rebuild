import unittest
from storage_profiles import STORAGE_PROFILE_GLOBALS,storage_profile_globals,make_profiled_native_observation
from storage_native_plans import plan_native_helper

class StorageProfileTests(unittest.TestCase):
    def test_us_literal_root_slots_and_context_offsets(self):
        g=storage_profile_globals('us')
        self.assertEqual((g[0x553e80],g[0x553f44],g[0x553f48]),(0x111563c,0x1116394,0x1114f7c))
        self.assertEqual((g[0x5540bc],g[0x554128]),(0x22c,0x230));self.assertEqual(len(g),15)

    def test_steam_literal_slots_and_context_offsets(self):
        g=storage_profile_globals('steam')
        self.assertEqual((g[0x553e80],g[0x553f44],g[0x553f48]),(0x11ebab0,0x11fe704,0x11e967c))
        self.assertEqual((g[0x5540bc],g[0x554128]),(0x26c,0x270));self.assertEqual(len(g),15)

    def test_common_table_button_and_vtable_offsets(self):
        for profile in ('us','steam'):
            g=storage_profile_globals(profile)
            self.assertEqual((g[0x5540c0],g[0x55412c]),(0x114,0x114))
            self.assertEqual((g[0x5540c4],g[0x554130]),(0x414,0x414))
            self.assertEqual((g[0x5540cc],g[0x5540d0]),(0x49c,0x4a0))
            self.assertEqual((g[0x554134],g[0x554138],g[0x55413c],g[0x554200]),(0x14c,0x138,0x13c,0x84))

    def test_runtime_cache_not_invented_by_profile(self):
        obs=make_profiled_native_observation('us','004653a8',1)
        self.assertNotIn(0x553d20,obs.globals)
        self.assertEqual(plan_native_helper(obs).status,'needs_observation')

    def test_runtime_cache_copy_and_source_global_conflict(self):
        runtime={0x553d20:0x9000};g=storage_profile_globals('us',runtime);runtime.clear()
        self.assertEqual(g[0x553d20],0x9000)
        with self.assertRaises(ValueError):storage_profile_globals('us',{0x554128:0x270})
        with self.assertRaises(ValueError):storage_profile_globals('us',{0x553d20:True})

    def test_profiles_immutable_and_new_mapping_copies(self):
        with self.assertRaises(TypeError):STORAGE_PROFILE_GLOBALS['us'][0x554200]=0
        with self.assertRaises(TypeError):storage_profile_globals('us')[0x554200]=0
        self.assertIsNot(storage_profile_globals('us'),storage_profile_globals('us'))

    def test_profile_factory_fe2fc_uses_real_source_offsets_with_fixture_words(self):
        for profile,root_slot,offset in (('us',0x111563c,0x230),('steam',0x11ebab0,0x270)):
            obs=make_profiled_native_observation(profile,'004fe2fc',0,
                protected_words={root_slot:0x1000,0x1000+offset:0x2000,0x2414:0x3000,0x3000:0x4000},
                direct_words={root_slot:0x5000,0x5000+offset:0x6000,0x6000:0x7000,0x7084:0x8000})
            r=plan_native_helper(obs)
            self.assertEqual(obs.source_profile,profile);self.assertEqual(r.call.ecx,0x6000)
            self.assertEqual(r.call.target,0x8000);self.assertEqual(r.call.push_order,(0x04000000,0x4000))
            self.assertFalse(r.call.abi_verified)

    def test_us_quantity_cache_derivation_uses_source_root_slot(self):
        obs=make_profiled_native_observation('us','004653a8',42,runtime_globals={0x553d20:0},
                                           protected_words={0x1114f7c:0x9000})
        r=plan_native_helper(obs)
        self.assertEqual(r.globals[0x553d20],0x914c);self.assertEqual(r.memory_writes[1],(0x914c,b'42'))

    def test_source_constants_do_not_make_missing_game_snapshot_valid(self):
        r=plan_native_helper(make_profiled_native_observation('us','004fe274',0))
        self.assertEqual(r.status,'needs_observation');self.assertIsNone(r.call)
        self.assertIn('0111563c',r.missing)

    def test_profile_choice_explicit_no_file_or_membership_autodetection(self):
        for profile in ('auto','ST','unknown'):
            with self.assertRaises(ValueError):storage_profile_globals(profile)
