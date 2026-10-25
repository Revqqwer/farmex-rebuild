import unittest
from dataclasses import replace
from jail_protection import JailObservation
from detector_code_state import CURRENT,LEGACY
from relog_startup import RelogStartupConfigFrame,RelogStartupConfigObservation,RelogStartupChildrenFrame,RelogStartupChildrenObservation
import test_relog_startup as startup_fixture
import test_relog_config as config_fixture


def sample(parent=None,config=None,replacement=None,code=None):
    old=startup_fixture.bound(parent,code,replacement)
    return RelogStartupConfigObservation(old.parent,old.replacement,old.code_state,config or config_fixture.sample())


class RelogStartupConfigTests(unittest.TestCase):
    def test_all_three_children_in_actual_source_order(self):
        f=RelogStartupConfigFrame();p=f.advance(sample())
        self.assertTrue(p.complete);self.assertEqual(tuple(p.children),('replace','config','code_state'))
        self.assertEqual(p.children['config'].branch,'STEAMLOGIN')
        self.assertEqual(f.frames['config'].final.source_sha256,CURRENT)
        self.assertEqual(p.parent.stores,((0x554210,4,0x20),(0x554214,4,0x2040)))

    def test_config_not_created_until_replacement_outer_return(self):
        o=startup_fixture.sample();o=replace(o,normal_returns={**o.normal_returns,'replace':False})
        f=RelogStartupConfigFrame();p=f.advance(sample(parent=o))
        self.assertTrue(p.children['replace'].complete);self.assertNotIn('config',f.frames)
        self.assertEqual(p.needed,('parent',('normal','replace')))
        self.assertTrue(f.advance(sample()).complete)

    def test_config_child_entry_derived_but_prologue_required(self):
        f=RelogStartupConfigFrame();p=f.advance(sample(config=JailObservation()))
        self.assertEqual(p.needed,('config',('normal','prologue')))
        self.assertEqual(tuple(f.frames),('replace','config'))
        self.assertEqual(p.parent.stores,((0x554210,4,0x20),))

    def test_config_gap_retains_prefix_and_blocks_code_state(self):
        c=config_fixture.sample();c=replace(c,normal_returns={**c.normal_returns,'fs_restore':False})
        f=RelogStartupConfigFrame();p=f.advance(sample(config=c))
        self.assertEqual(p.needed,('config',('normal','fs_restore')))
        self.assertEqual(len(p.children['config'].stores),7)
        self.assertNotIn('code_state',f.frames);self.assertEqual(len(p.parent.stores),1)
        p=f.advance(sample());self.assertTrue(p.complete)

    def test_config_frame_return_separate_from_caller_return(self):
        o=startup_fixture.sample();o=replace(o,normal_returns={**o.normal_returns,'config':False})
        f=RelogStartupConfigFrame();p=f.advance(sample(parent=o))
        self.assertTrue(p.children['config'].complete)
        self.assertEqual(p.needed,('parent',('normal','config')))
        self.assertNotIn('code_state',f.frames)
        p=f.advance(sample());self.assertTrue(p.complete)

    def test_usko_copy_intents_retained_without_applying_them(self):
        c=config_fixture.sample(1,True)
        f=RelogStartupConfigFrame();p=f.advance(sample(config=c))
        self.assertTrue(p.complete)
        self.assertEqual(p.children['config'].copy_intents,((0x900,0x777,9),(0xa00,0x888,10)))
        self.assertFalse(p.children['config'].native_execution_verified)
        self.assertFalse(p.live_compatibility_verified)
        self.assertNotIn('byte0.eax',f.frames['code_state'].values)

    def test_future_parent_reads_are_required_independently_after_config(self):
        o=startup_fixture.sample();o=replace(o,values={k:v for k,v in o.values.items() if k!='next_slot_offset'})
        f=RelogStartupConfigFrame();p=f.advance(sample(parent=o))
        self.assertTrue(all(c.complete for c in p.children.values()))
        self.assertEqual(p.needed,('parent',('value','next_slot_offset')))
        self.assertEqual(len(p.parent.stores),1)
        p=f.advance(sample(parent=startup_fixture.sample(next_slot_offset=0x80)))
        self.assertTrue(p.complete);self.assertEqual(p.parent.stores[-1],(0x554214,4,0x2080))

    def test_multiple_resumes_do_not_replay_completed_children(self):
        o=startup_fixture.sample();o=replace(o,normal_returns={**o.normal_returns,'code_state':False})
        f=RelogStartupConfigFrame();p=f.advance(sample(parent=o))
        config_plan=p.children['config'];replacement_plan=p.children['replace']
        p=f.advance(sample(parent=o,config=JailObservation()))
        self.assertIs(p.children['config'],config_plan);self.assertIs(p.children['replace'],replacement_plan)
        self.assertEqual(p.needed,('parent',('normal','code_state')))
        p=f.advance(sample());self.assertTrue(p.complete)

    def test_legacy_two_child_api_still_treats_config_as_opaque(self):
        f=RelogStartupChildrenFrame(LEGACY);p=f.advance(startup_fixture.bound())
        self.assertTrue(p.complete);self.assertEqual(tuple(p.children),('replace','code_state'))
        self.assertNotIn('config',f.frames)

    def test_typed_and_source_guards(self):
        with self.assertRaises(ValueError):RelogStartupConfigFrame(LEGACY)
        with self.assertRaises(ValueError):RelogStartupConfigObservation(config={})
        with self.assertRaises(ValueError):RelogStartupConfigFrame().advance(RelogStartupChildrenObservation())
        p=RelogStartupConfigFrame().advance(sample())
        with self.assertRaises(TypeError):p.children['config']=None
