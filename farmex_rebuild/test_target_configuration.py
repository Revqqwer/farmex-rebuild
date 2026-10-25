import json,unittest
from pathlib import Path
from profiles import Profiles
from target_configuration import *
from target_resolver import ResolverCandidate,ResolverSnapshot,CurrentTargetObservation,TargetResolver,resolve_target

class TargetConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.profiles=Profiles(json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf-8')))
        self.values=dict(self.profiles.defaults);self.lists=self.profiles.validate_lists({})
        self.profiles.update(self.values,MODE_PATHS[2],True)
    def compile(self,**args):return compile_target_configuration(self.values,self.lists,raw_pool_selector=0,**args)
    def row(self,caption,checked):return dict(caption=caption,checked=checked,subitems=[])
    def test_source_five_modes_are_not_collapsed_into_auto(self):
        for index,path in enumerate(MODE_PATHS,1):
            self.profiles.update(self.values,path,True);result=self.compile()
            self.assertEqual(result.mode,index)
            self.assertEqual(result.status,'compiled' if index in (2,3) else 'helper_branch_mode')
    def test_no_radio_needs_previous_field_instead_of_default_auto(self):
        for path in MODE_PATHS:self.values[path]=False
        self.assertEqual(self.compile().status,'needs_previous_mode')
        self.assertEqual(self.compile(previous_mode=2).mode,2)
    def test_source_radio_priority_preserved_for_raw_conflicting_input(self):
        self.values[MODE_PATHS[0]]=True
        self.assertEqual(self.compile().mode,1)
    def test_only_nonempty_checked_captions_in_source_order(self):
        self.lists[LIST_PATH]=[self.row('11',True),self.row('12',False),self.row('',True),self.row(' ',True),self.row('11',True)]
        self.assertEqual(self.compile().settings.entries,('11',' ','11'))
    def test_active_target_range_and_speed_reach_resolver(self):
        prefix=BASE+'GroupBox34/GroupBox35/'
        self.profiles.update(self.values,BASE+'GroupBox34/rdUseNormalSkill',True)
        self.profiles.update(self.values,prefix+'txtNMobSelectDistance','4')
        self.profiles.update(self.values,prefix+'txtNMobSelectSpeed','2000')
        settings=self.compile().settings
        resolver=TargetResolver(settings)
        snapshot=ResolverSnapshot((ResolverCandidate('A',11,'Worm',3,3,visibility=True,repeated_visibility=True),),complete=True)
        current=CurrentTargetObservation(0)
        self.assertEqual(resolver.tick(1000,current,snapshot).status,'retarget_armed')
        self.assertEqual(resolver.tick(2000,current,snapshot).status,'waiting')
        self.assertEqual(resolver.tick(3000,current,snapshot).candidate.target_id,11)
    def test_name_id_checked_list_controls_candidate(self):
        self.profiles.update(self.values,MODE_PATHS[1],True)
        self.lists[LIST_PATH]=[self.row('11',True)]
        snapshot=ResolverSnapshot((ResolverCandidate('A',11,'Worm',3,3,visibility=True,repeated_visibility=True),),complete=True)
        self.assertEqual(resolve_target(self.compile().settings,snapshot).candidate.target_id,11)
    def test_movement_flags_and_raw_pool_are_explicit(self):
        for path in FLAG_PATHS:self.profiles.update(self.values,path,True)
        result=compile_target_configuration(self.values,self.lists,raw_pool_selector=2)
        self.assertTrue(result.settings.run_to_target and result.settings.return_to_center and result.settings.extra_rejection_guard)
        self.assertEqual(result.settings.raw_pool_selector,2)
    def test_negative_radius_is_rejected_by_existing_model_not_clamped(self):
        self.profiles.update(self.values,BASE+'GroupBox34/rdUseNormalSkill',True)
        self.profiles.update(self.values,BASE+'GroupBox34/GroupBox35/txtNMobSelectDistance','-1')
        with self.assertRaises(ValueError):self.compile()
    def test_pool_checkboxes_map_to_verified_source_values(self):
        for selected,wanted in ((None,0),(POOL_PATHS[0],2),(POOL_PATHS[1],1)):
            for path in POOL_PATHS:self.profiles.update(self.values,path,False)
            if selected:self.profiles.update(self.values,selected,True)
            result=compile_target_configuration(self.values,self.lists)
            self.assertEqual(result.settings.raw_pool_selector,wanted)
    def test_source_checkbox_click_excludes_sibling(self):
        self.profiles.update(self.values,POOL_PATHS[0],True)
        self.profiles.update(self.values,POOL_PATHS[1],True)
        self.assertFalse(self.values[POOL_PATHS[0]]);self.assertTrue(self.values[POOL_PATHS[1]])
    def test_both_raw_flags_checked_needs_event_order(self):
        for path in POOL_PATHS:self.values[path]=True
        self.assertEqual(compile_target_configuration(self.values,self.lists).status,'needs_pool_event_order')
    def test_unchecking_last_pool_flag_returns_both_pools(self):
        self.profiles.update(self.values,POOL_PATHS[0],True);self.profiles.update(self.values,POOL_PATHS[0],False)
        self.assertEqual(compile_target_configuration(self.values,self.lists).settings.raw_pool_selector,0)
    def test_explicit_fixture_override_does_not_change_panel(self):
        self.profiles.update(self.values,POOL_PATHS[0],True);before=dict(self.values)
        self.assertEqual(compile_target_configuration(self.values,self.lists,raw_pool_selector=1).settings.raw_pool_selector,1)
        self.assertEqual(self.values,before)
    def test_manual_branch_does_not_require_unused_pool_fields(self):
        values={path:index==0 for index,path in enumerate(MODE_PATHS)}
        self.assertEqual(compile_target_configuration(values,{}).status,'helper_branch_mode')
