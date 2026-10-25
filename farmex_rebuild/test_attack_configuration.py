import json,unittest
from pathlib import Path
from class_configuration import compile_class_configuration,ClassConfiguration
from attack_configuration import rogue_volley_ranges,warrior_provoke_settings
from profiles import Profiles
from rogue_attack import RogueSnapshot,BOW_ROWS,plan_rogue_volley
from warrior_alternate import ProvokeSnapshot,PROVOKE_ROWS,replay_warrior_provoke

class AttackConfigurationTests(unittest.TestCase):
    def setUp(self):
        base=Path(__file__).parent
        self.schema=json.loads((base/'class_configuration_map.json').read_text(encoding='utf-8'))
        self.profiles=Profiles(json.loads((base/'ui_model.json').read_text(encoding='utf-8')))
        self.values=dict(self.profiles.defaults);self.lists=self.profiles.validate_lists({})
    def set_field(self,job,kind,offset,value):
        path=next(p for p,o in self.schema[job][kind].items() if o==offset)
        self.profiles.update(self.values,path,value)
    def config(self,job):return compile_class_configuration(job,self.values,self.lists)
    def test_rogue_exact_panel_offsets_keep_different_ranges(self):
        self.set_field('rogue','integers',16,'3');self.set_field('rogue','integers',20,'7')
        settings=rogue_volley_ranges(self.config('rogue'))
        self.assertEqual((settings.triple,settings.quintuple),(3,7))
    def test_signed_range_is_not_clamped(self):
        self.set_field('rogue','integers',16,'-1')
        self.assertEqual(rogue_volley_ranges(self.config('rogue')).triple,-1)
    def test_rogue_range_controls_actual_helper_plan_boundary(self):
        flags={r.flag_offset:False for r in BOW_ROWS};flags.update({0x89:True,0x91:False})
        timers={r.timer_offset:0 for r in BOW_ROWS if r.timer_offset is not None};timers.update({0x2c:0,0x30:0,0x34:0})
        snapshot=RogueSnapshot(10000,5,8,1100,flags,{'00462ddc':100},timers,locked_561f7e=False)
        for value,wanted in ((4,False),(5,True)):
            self.set_field('rogue','integers',16,str(value));self.set_field('rogue','integers',20,'0')
            settings=rogue_volley_ranges(self.config('rogue'))
            plan=plan_rogue_volley(snapshot,1000,settings.triple,settings.quintuple,1,False)
            self.assertEqual(any(call[0]=='004de710' for call in plan.calls),wanted)
    def test_warrior_window_start_and_skill_wait_are_not_swapped(self):
        for offset,value in ((0x1a0,'60'),(0x1a4,'2'),(0x1a8,'3')):self.set_field('warrior','integers',offset,value)
        self.set_field('warrior','booleans',0x198,True)
        settings=warrior_provoke_settings(self.config('warrior'))
        self.assertEqual((settings.enabled,settings.window_seconds,settings.start_delay_seconds,settings.skill_delay_seconds),(True,60,2,3))
    def test_warrior_signed_seconds_preserve_source_wrap_policy(self):
        self.set_field('warrior','integers',0x1a4,'-1')
        self.assertEqual(warrior_provoke_settings(self.config('warrior')).start_delay_seconds,-1)
    def test_provoke_panel_waits_reach_existing_motor(self):
        for offset,value in ((0x1a0,'60'),(0x1a4,'2'),(0x1a8,'3')):self.set_field('warrior','integers',offset,value)
        self.set_field('warrior','booleans',0x198,True)
        config=self.config('warrior');settings=warrior_provoke_settings(config)
        for now,wanted in ((1000,'wait_start_delay'),(2000,'wait_skill_delay')):
            snapshot=ProvokeSnapshot(now,config.flags,{},None,settings.window_seconds,settings.start_delay_seconds,
                settings.skill_delay_seconds,settings.enabled,0)
            self.assertEqual(replay_warrior_provoke(snapshot).status,wanted)
    def test_missing_parameter_and_wrong_class_rejected(self):
        with self.assertRaises(ValueError):rogue_volley_ranges(ClassConfiguration('rogue','source',{}, {16:5},()))
        with self.assertRaises(ValueError):warrior_provoke_settings(self.config('rogue'))
    def test_rogue_combo_distance_is_not_used_as_volley_interval(self):
        self.set_field('rogue','integers',16,'4');self.set_field('rogue','integers',20,'6')
        before=rogue_volley_ranges(self.config('rogue'))
        self.set_field('rogue','integers',24,'12345')
        self.assertEqual(rogue_volley_ranges(self.config('rogue')),before)
