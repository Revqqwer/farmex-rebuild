import unittest
from dataclasses import replace
from combo_configuration import COMBO_PANEL_INPUTS,ComboPanelConfiguration,compile_combo_panel
from rogue_alternate_bow import plan_alternate_bow
from rogue_combo import ComboState,plan_rogue_combo
import test_rogue_combo as source_fixture

class ComboConfigurationTests(unittest.TestCase):
    def values(self,w=False,s=False,run=False,r_attack=False):return dict(zip(COMBO_PANEL_INPUTS,(w,s,run,r_attack)))
    def test_independent_four_way_switch_values(self):
        for w,s in ((False,False),(True,False),(False,True),(True,True)):
            config=compile_combo_panel(self.values(w,s))
            self.assertEqual((config.w_byte,config.s_byte),(int(w),int(s)))
    def test_missing_invalid_and_non_mapping_rejected(self):
        for values in ({},None,[],self.values(w=1),self.values(s='true'),self.values(run=None),self.values(r_attack=1)):
            with self.subTest(values=values),self.assertRaises(ValueError):compile_combo_panel(values)
    def test_compilation_does_not_clear_other_checkbox(self):
        values=self.values(True,True,True);before=dict(values)
        self.assertEqual(compile_combo_panel(values),ComboPanelConfiguration(True,True,True))
        self.assertEqual(values,before)
    def test_panel_switches_change_real_selector_range_branch(self):
        f=source_fixture.ComboTests();f.setUp()
        for w,s,wanted in ((False,False,0),(True,False,1),(False,True,1),(True,True,1)):
            config=compile_combo_panel(self.values(w,s))
            o=replace(f.selector['selector_observation'],execute_byte=0,byte_562011=config.w_byte,byte_562012=config.s_byte)
            p=plan_alternate_bow(f.selector['selector_snapshot'],f.selector['selector_ranges'],o)
            self.assertEqual(p.source_return,wanted)
    def test_run_to_target_controls_ordinary_pattern_pair(self):
        f=source_fixture.ComboTests();f.setUp()
        for run,stage,args in ((False,4,[(1,)]),(True,6,[(2,),(0,)])):
            config=compile_combo_panel(self.values(True,False,run))
            o=replace(f.o,byte_562011=config.w_byte,byte_562012=config.s_byte,byte_561ffc=config.run_byte)
            p=plan_rogue_combo(ComboState(3,category=3),o)
            self.assertEqual(p.state.stage,stage);self.assertEqual([a for h,a in p.calls],args)
    def test_s_only_and_both_panel_switches_consume_separate_patterns(self):
        f=source_fixture.ComboTests();f.setUp()
        for w,s,ah,arg,counter in ((False,True,1,2,0),(False,True,0x40,1,0),(True,True,None,2,1)):
            config=compile_combo_panel(self.values(w,s))
            o=replace(f.o,byte_562011=config.w_byte,byte_562012=config.s_byte,distance_vs_one_ah=ah)
            p=plan_rogue_combo(ComboState(3),o)
            self.assertEqual((p.calls[-1][1],p.state.pattern_counter),((arg,),counter))
