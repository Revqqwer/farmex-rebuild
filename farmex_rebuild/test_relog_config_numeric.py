import unittest
from dataclasses import replace
from jail_protection import JailObservation
from relog_config_numeric import RelogConfigNumericFrame,RelogConfigNumericObservation,NAMES
import test_relog_config as config_fixture
import test_profile_numeric as numeric_fixture
import test_relog_startup as startup_fixture
from relog_startup import RelogStartupNumericFrame,RelogStartupNumericObservation


def sample(mode=2,values=None):
    parent=config_fixture.sample(mode)
    parent=replace(parent,values={k:v for k,v in parent.values.items() if not any(k==n+'.eax' for n in NAMES)})
    helpers={name:numeric_fixture.sample((values or {}).get(name,0)) for name in NAMES}
    return RelogConfigNumericObservation(parent,helpers)


class RelogConfigNumericTests(unittest.TestCase):
    def test_chosen_branch_creates_only_seven_helpers(self):
        for mode,prefix in ((1,'usko_'),(0,'steam_'),(2,'steam_')):
            f=RelogConfigNumericFrame();p=f.advance(sample(mode))
            self.assertTrue(p.complete);self.assertEqual(len(p.helpers),7)
            self.assertTrue(all(n.startswith(('captcha_',prefix)) for n in p.helpers))

    def test_api256_becomes_boolean1_while_service_is256(self):
        p=RelogConfigNumericFrame().advance(sample(values={'captcha_enabled':256,'captcha_service':256}))
        self.assertIn((0x561ed0,1,1),p.parent.stores);self.assertIn((0x561ed4,4,256),p.parent.stores)
        self.assertEqual(p.helpers['captcha_enabled'].return_eax,1)

    def test_formals_derive_from_actual_distinct_source_pushes(self):
        f=RelogConfigNumericFrame();p=f.advance(sample())
        self.assertTrue(p.complete)
        self.assertEqual(f.frames['captcha_enabled'].formal,(0x200,0x100,0x1000,0))
        self.assertEqual(f.frames['captcha_service'].formal,(0x200,0x100,0x1000,0))
        self.assertEqual(f.frames['captcha_service'].kind,'dword')

    def test_child_entry_derived_but_missing_prologue_waits(self):
        o=sample();o=replace(o,helpers={})
        p=RelogConfigNumericFrame().advance(o)
        self.assertEqual(p.needed,('captcha_enabled',('normal','prologue')));self.assertFalse(p.parent.stores)

    def test_api_result_and_helper_outer_return_are_separate(self):
        o=sample();parent=replace(o.parent,normal_returns={**o.parent.normal_returns,'captcha_enabled.read':False})
        f=RelogConfigNumericFrame();p=f.advance(replace(o,parent=parent))
        self.assertTrue(p.helpers['captcha_enabled'].complete)
        self.assertEqual(p.needed,('parent',('normal','captcha_enabled.read')));self.assertFalse(p.parent.stores)
        self.assertTrue(f.advance(o).complete)

    def test_conflicting_raw_helper_value_rejected(self):
        o=sample(values={'captcha_enabled':256})
        o=replace(o,parent=replace(o.parent,values={**o.parent.values,'captcha_enabled.eax':256}))
        with self.assertRaises(ValueError):RelogConfigNumericFrame().advance(o)

    def test_prefix_and_completed_children_retained_during_later_gap(self):
        o=sample();helper=o.helpers['captcha_service']
        helper=replace(helper,normal_returns={**helper.normal_returns,'path_cleanup':False})
        f=RelogConfigNumericFrame();p=f.advance(replace(o,helpers={**o.helpers,'captcha_service':helper}))
        old=p.helpers['captcha_enabled'];self.assertEqual(p.parent.stores,((0x561ed0,1,0),))
        self.assertEqual(p.needed,('captcha_service',('normal','path_cleanup')))
        p=f.advance(o);self.assertTrue(p.complete);self.assertIs(p.helpers['captcha_enabled'],old)

    def test_future_config_observations_remain_required(self):
        o=sample();parent=replace(o.parent,values={k:v for k,v in o.parent.values.items() if k!='mode_byte'})
        f=RelogConfigNumericFrame();p=f.advance(replace(o,parent=parent))
        self.assertEqual(p.needed,('parent',('value','mode_byte')))
        self.assertEqual(tuple(p.helpers),('captcha_enabled','captcha_service'))
        self.assertTrue(f.advance(o).complete)

    def test_observations_are_typed_and_frozen(self):
        with self.assertRaises(ValueError):RelogConfigNumericObservation(helpers={'unknown':JailObservation()})
        with self.assertRaises(ValueError):RelogConfigNumericObservation(helpers={'captcha_enabled':{}})
        with self.assertRaises(ValueError):RelogConfigNumericFrame().advance(JailObservation())
        p=RelogConfigNumericFrame().advance(sample())
        with self.assertRaises(TypeError):p.helpers['new']=None

    def test_numeric_helpers_reach_startup_chain(self):
        old=startup_fixture.bound()
        o=RelogStartupNumericObservation(old.parent,old.replacement,old.code_state,
            sample(values={'captcha_enabled':256}))
        p=RelogStartupNumericFrame().advance(o)
        self.assertTrue(p.complete)
        self.assertEqual(tuple(p.children),('replace','config','code_state'))
        self.assertIn((0x561ed0,1,1),p.children['config'].parent.stores)
        self.assertEqual(len(p.children['config'].helpers),7)

    def test_nested_api_gap_blocks_code_state(self):
        old=startup_fixture.bound();config=sample();child=config.helpers['captcha_enabled']
        child=replace(child,values={k:v for k,v in child.values.items() if k!='profile_api_eax'})
        config=replace(config,helpers={**config.helpers,'captcha_enabled':child})
        f=RelogStartupNumericFrame();p=f.advance(RelogStartupNumericObservation(old.parent,old.replacement,old.code_state,config))
        self.assertEqual(p.needed,('config',('captcha_enabled',('value','profile_api_eax'))))
        self.assertNotIn('code_state',f.frames);self.assertEqual(len(p.parent.stores),1)

    def test_startup_numeric_requires_nested_observation_type(self):
        with self.assertRaises(ValueError):RelogStartupNumericObservation(config=JailObservation())
