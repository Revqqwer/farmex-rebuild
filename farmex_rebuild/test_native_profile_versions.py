import unittest
from dataclasses import replace
from native_profile_versions import *

class NativeVersionTests(unittest.TestCase):
    def test_us_current_storage_root_and_context_differ_from_legacy(self):
        old=versioned_profile_globals(LEGACY_SOURCE_SHA256,'us','storage')
        new=versioned_profile_globals(CURRENT_SOURCE_SHA256,'us','storage')
        self.assertEqual((old[0x553e80],old[0x5540bc],old[0x554128]),(0x111563c,0x22c,0x230))
        self.assertEqual((new[0x553e80],new[0x5540bc],new[0x554128]),(0x1128a7c,0x26c,0x270))

    def test_steam_current_roots_and_current_skill_targets(self):
        g=versioned_profile_globals(CURRENT_SOURCE_SHA256,'steam','storage')
        self.assertEqual((g[0x553e80],g[0x553f44],g[0x553f48]),(0x11eaab0,0x11fd704,0x11e867c))
        g=versioned_profile_globals(CURRENT_SOURCE_SHA256,'us','skill')
        self.assertEqual((g[0x553eb8],g[0x553ebc],g[0x553ee4],g[0x5540a0]),(0,0x5066b0,0x88eb50,0x4a8))

    def test_hash_and_profile_are_required_and_maps_immutable(self):
        for sha,profile,kind in (('unknown','us','storage'),(CURRENT_SOURCE_SHA256,'auto','storage'),(CURRENT_SOURCE_SHA256,'us','anything')):
            with self.assertRaises(ValueError):versioned_profile_globals(sha,profile,kind)
        with self.assertRaises(TypeError):CURRENT_STORAGE_GLOBALS['us'][0x553e80]=0
        with self.assertRaises(TypeError):versioned_profile_globals(CURRENT_SOURCE_SHA256,'us','storage')[0x553e80]=0

    def test_moved_helper_addresses_cannot_cross_source_versions(self):
        for sha,helper in ((CURRENT_SOURCE_SHA256,'004fe2fc'),(LEGACY_SOURCE_SHA256,'004fe318')):
            with self.assertRaises(ValueError):make_versioned_storage_observation(sha,'us',helper,0)
        o=make_versioned_storage_observation(CURRENT_SOURCE_SHA256,'us','004fe318',0)
        self.assertEqual((o.source_helper,o.modeled_helper),('004fe318','004fe2fc'))

    def test_current_source_helpers_feed_existing_operand_model_with_current_addresses(self):
        for profile in ('us','steam'):
            g=versioned_profile_globals(CURRENT_SOURCE_SHA256,profile,'storage');root=g[0x553e80];offset=g[0x554128]
            o=make_versioned_storage_observation(CURRENT_SOURCE_SHA256,profile,'004fe318',0,
                protected_words={root:0x1000,0x1000+offset:0x2000,0x2414:0x3000,0x3000:0x4000},
                direct_words={root:0x5000,0x5000+offset:0x6000,0x6000:0x7000,0x7084:0x8000})
            p=plan_versioned_native(o)
            self.assertEqual((p.plan.call.ecx,p.plan.call.target,p.plan.call.push_order),(0x6000,0x8000,(0x04000000,0x4000)))
            self.assertEqual(p.module_sha256,CURRENT_SOURCE_SHA256)
            self.assertFalse(p.game_image_verified or p.native_execution_verified or p.plan.call.abi_verified)

    def test_historical_snapshot_cannot_satisfy_current_root_read(self):
        o=make_versioned_storage_observation(CURRENT_SOURCE_SHA256,'us','004fe318',0,protected_words={0x111563c:0x1000})
        p=plan_versioned_native(o)
        self.assertEqual(p.plan.status,'needs_observation');self.assertIn('01128a7c',p.plan.missing)

    def test_current_quantity_fixture_uses_current_input_root_and_explicit_cache(self):
        o=make_versioned_storage_observation(CURRENT_SOURCE_SHA256,'us','004653a8',42,
            runtime_globals={0x553d20:0},protected_words={0x11283bc:0x9000})
        p=plan_versioned_native(o)
        self.assertEqual(p.plan.globals[0x553d20],0x914c)
        self.assertEqual(p.plan.memory_writes[1],(0x914c,b'42'))
        self.assertFalse(p.native_execution_verified)

    def test_current_skill_calls_use_current_targets_and_source_identity(self):
        for profile in ('us','steam'):
            g=versioned_profile_globals(CURRENT_SOURCE_SHA256,profile,'skill')
            words={g[0x553e80]:0x1000,0x1000+g[0x5540a0]:0x2000}
            if profile=='steam':words[g[0x553eb8]]=0x3000
            o=make_versioned_skill_observation(CURRENT_SOURCE_SHA256,profile,123,456,direct_words=words,lookup_return=0x4000,native_return=1)
            p=plan_versioned_native(o)
            self.assertEqual([c.target for c in p.plan.calls],[g[0x553ebc],g[0x553ee4]])
            self.assertEqual(p.plan.calls[-1].ecx,0x2000)
            self.assertFalse(p.native_execution_verified)

    def test_cache_extension_copied_but_cannot_override_source_projection(self):
        runtime={0x553d20:0x9000};g=versioned_profile_globals(CURRENT_SOURCE_SHA256,'us','storage',runtime_globals=runtime)
        runtime.clear();self.assertEqual(g[0x553d20],0x9000)
        with self.assertRaises(ValueError):versioned_profile_globals(CURRENT_SOURCE_SHA256,'us','storage',runtime_globals={0x553e80:0x111563c})
        with self.assertRaises(ValueError):versioned_profile_globals(CURRENT_SOURCE_SHA256,'us','storage',runtime_globals={1:True})

    def test_relabeling_legacy_fixture_cannot_claim_current_source(self):
        o=make_versioned_storage_observation(LEGACY_SOURCE_SHA256,'us','004fe2fc',0)
        with self.assertRaises(ValueError):replace(o,module_sha256=CURRENT_SOURCE_SHA256)
        with self.assertRaises(ValueError):replace(o,profile='steam')

if __name__=='__main__':unittest.main()
