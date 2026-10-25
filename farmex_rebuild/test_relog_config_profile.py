import unittest
from dataclasses import replace
from jail_protection import JailObservation
from relog_config_profile import RelogConfigProfileFrame,RelogConfigProfileObservation,STRING_NAMES
from relog_startup import RelogStartupProfileFrame,RelogStartupProfileObservation
import test_relog_config_numeric as numeric_fixture
import test_profile_string as string_fixture
import test_relog_startup as startup_fixture


def sample(mode=2):
    old=numeric_fixture.sample(mode)
    return RelogConfigProfileObservation(old.parent,{**old.helpers,**{n:string_fixture.sample() for n in STRING_NAMES}})


class RelogConfigProfileTests(unittest.TestCase):
    def test_steam_eight_and_usko_ten_reached_helpers(self):
        for mode,count in ((2,8),(1,10)):
            p=RelogConfigProfileFrame().advance(sample(mode))
            self.assertTrue(p.complete);self.assertEqual(len(p.helpers),count)
            self.assertIn('captcha_detail',p.helpers)
            self.assertEqual('id' in p.helpers,mode==1)

    def test_string_formals_derive_from_actual_source_call(self):
        f=RelogConfigProfileFrame();p=f.advance(sample(1));self.assertTrue(p.complete)
        for name in STRING_NAMES:self.assertEqual(f.frames[name].formal,(0x200,0x100,0x1000,0x300,0x500))

    def test_completed_string_does_not_supply_unused_parent_eax(self):
        o=sample();o=replace(o,parent=replace(o.parent,values={**o.parent.values,'captcha_detail.eax':0xffffffff}))
        p=RelogConfigProfileFrame().advance(o)
        self.assertTrue(p.complete);self.assertEqual(p.helpers['captcha_detail'].return_eax,0x600)
        self.assertNotIn('captcha_detail.eax',RelogConfigProfileFrame().parent.values)

    def test_string_gap_blocks_parent_conversion(self):
        o=sample();child=o.helpers['captcha_detail'];child=replace(child,normal_returns={**child.normal_returns,'temp_cleanup':False})
        f=RelogConfigProfileFrame();p=f.advance(replace(o,helpers={**o.helpers,'captcha_detail':child}))
        self.assertEqual(p.needed,('captcha_detail',('normal','temp_cleanup')))
        self.assertFalse(any(label=='captcha_detail.convert' for _,_,label in p.parent.calls))
        self.assertFalse(p.parent.string_assignments)
        self.assertTrue(f.advance(o).complete)

    def test_string_child_done_still_needs_outer_helper_return(self):
        o=sample();parent=replace(o.parent,normal_returns={**o.parent.normal_returns,'captcha_detail.read':False})
        f=RelogConfigProfileFrame();p=f.advance(replace(o,parent=parent))
        self.assertTrue(p.helpers['captcha_detail'].complete)
        self.assertEqual(p.needed,('parent',('normal','captcha_detail.read')))
        self.assertTrue(f.advance(o).complete)

    def test_nested_startup_completes_with_profile_children(self):
        old=startup_fixture.bound();o=RelogStartupProfileObservation(old.parent,old.replacement,old.code_state,sample(1))
        p=RelogStartupProfileFrame().advance(o);self.assertTrue(p.complete)
        self.assertEqual(len(p.children['config'].helpers),10)
        self.assertFalse(p.live_compatibility_verified)

    def test_nested_string_gap_blocks_code_state(self):
        old=startup_fixture.bound();config=sample();config=replace(config,helpers={k:v for k,v in config.helpers.items() if k!='captcha_detail'})
        f=RelogStartupProfileFrame();p=f.advance(RelogStartupProfileObservation(old.parent,old.replacement,old.code_state,config))
        self.assertEqual(p.needed,('config',('captcha_detail',('normal','prologue'))))
        self.assertNotIn('code_state',f.frames)

    def test_typed_observations_and_immutable_plans(self):
        with self.assertRaises(ValueError):RelogConfigProfileObservation(helpers={'unknown':JailObservation()})
        with self.assertRaises(ValueError):RelogStartupProfileObservation(config=JailObservation())
        with self.assertRaises(ValueError):RelogConfigProfileFrame().advance(numeric_fixture.sample())
        p=RelogConfigProfileFrame().advance(sample())
        with self.assertRaises(TypeError):p.helpers['new']=None
