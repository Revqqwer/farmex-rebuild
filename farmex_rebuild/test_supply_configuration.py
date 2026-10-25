import json,unittest
from pathlib import Path
from profiles import Profiles
from supply_configuration import *

class SupplyConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles=Profiles(json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf8')))
    def setUp(self):self.values=dict(self.profiles.defaults)
    def compile(self,**kw):return compile_supply_panel(self.values,**kw)
    def enabled(self):
        self.values[TRIGGERS+'chTedarikWeight']=True
        return self.compile()
    def test_all_scalar_controls_exist_and_defaults_preserved(self):
        self.assertTrue(set(SUPPLY_PANEL_INPUTS)<=set(self.values))
        p=self.compile();self.assertEqual(p.fields[0x54c],1);self.assertEqual(p.fields[0x550],1)
        self.assertEqual(p.fields[0x560],95);self.assertFalse(p.independently_verified)
        with self.assertRaises(TypeError):p.fields[0x560]=20
    def test_each_flag_is_independent_at_source_offset(self):
        baseline=self.compile()
        for path,offset in FLAG_PATHS.items():
            saved=self.values[path];self.values[path]=not saved;p=self.compile()
            self.assertEqual(p.fields[offset],int(not saved))
            self.assertEqual({k:v for k,v in p.fields.items() if k!=offset},
                {k:v for k,v in baseline.fields.items() if k!=offset})
            self.values[path]=saved
    def test_only_magic_radio_is_source_input_both_false_selects2(self):
        self.values[HAMMER_PATH]=False
        self.values[SUPPLY+'GroupBox31/rdgeniehammer']=False
        self.assertEqual(self.compile().fields[0x550],2)
        self.values[HAMMER_PATH]=True;self.values[SUPPLY+'GroupBox31/rdgeniehammer']=True
        self.assertEqual(self.compile().fields[0x550],1)
    def test_signed64_decimal_parser_low_dword_and_no_percent_clamp(self):
        for text,expected in (('-1',0xffffffff),('4294967297',1),('-9223372036854775808',0),('  +150 ',150)):
            self.values[TRIGGERS+'txtTedarikWeightLimit']=text
            self.assertEqual(self.compile().fields[0x560],expected)
        for text in ('1.000','0x20','9223372036854775808',''):
            self.values[TRIGGERS+'txtTedarikWeightLimit']=text
            with self.assertRaises(ValueError):self.compile()
    def test_unicode_text_is_not_trimmed_or_converted_to_ansi(self):
        for path,offset in TEXT_PATHS.items():self.values[path]=' İtem\x00😀 '
        p=self.compile()
        self.assertTrue(all(p.texts[offset]==' İtem\x00😀 ' for offset in TEXT_PATHS.values()))
    def test_combo_itemindex_is_never_guessed_as_gettext(self):
        p=self.compile();self.assertEqual(p.status,'needs_combo_text');self.assertEqual(len(p.missing),2)
        self.assertNotIn(0x580,p.texts)
        texts={path:'Rota '+str(offset) for path,offset in COMBO_TEXT_PATHS.items()}
        p=self.compile(combo_texts=texts);self.assertEqual(p.status,'compiled_scalars')
        self.assertEqual(p.texts[0x580],texts[GROUP+'cmbTedarikRoutes'])
    def test_branch_reachability_and_disabled_short_circuit(self):
        p=self.compile()
        self.assertEqual(plan_supply_weight(p).status,'needs_branch_observation')
        self.assertEqual(plan_supply_weight(p,branch_reached=False).status,'weight_branch_not_reached')
        self.assertEqual(plan_supply_weight(p,branch_reached=True).status,'weight_disabled')
        self.assertEqual(plan_supply_weight(self.enabled(),branch_reached=True).status,'needs_weight_observation')
    def test_weight_boundary_and_town_alarm_choice_use_panel(self):
        p=self.enabled()
        self.assertFalse(plan_supply_weight(p,94,branch_reached=True).due)
        self.assertEqual(plan_supply_weight(p,95,branch_reached=True).action,'supply_route')
        self.values[TRIGGERS+'chSupplyTownAlarm']=True
        self.assertEqual(plan_supply_weight(self.compile(),95,branch_reached=True).action,'town_alarm')
    def test_weight_comparison_is_signed_dword(self):
        self.enabled();self.values[TRIGGERS+'txtTedarikWeightLimit']='-1'
        self.assertTrue(plan_supply_weight(self.compile(),0,branch_reached=True).due)
        self.assertFalse(plan_supply_weight(self.compile(),0xfffffffe,branch_reached=True).due)
        self.values[TRIGGERS+'txtTedarikWeightLimit']='2147483648'
        self.assertTrue(plan_supply_weight(self.compile(),0x7fffffff,branch_reached=True).due)
    def test_x86_weight_multiply_overflow_and_signed_truncation(self):
        self.assertEqual(weight_percent_dword(95,100),95)
        self.assertEqual(weight_percent_dword(0xffffffff,3),(-33)&0xffffffff)
        self.assertEqual(weight_percent_dword(0x40000000,100),0) # lowDWORD IMUL wraps to0.
        self.assertEqual(weight_percent_dword(0x7fffffff,100),0xffffffff) # product=-100.
        self.assertEqual(weight_percent_dword(100,0),0)
        self.assertEqual(weight_percent_dword(100,0xffffffff),0)
    def test_invalid_input_types_rejected_without_profile_mutation(self):
        path=next(iter(FLAG_PATHS));before=dict(self.values);self.values[path]=1
        with self.assertRaises(ValueError):self.compile()
        self.values=dict(before);self.assertEqual(self.compile().fields[0x560],95)
        for bad in (True,-1,0x100000000):
            with self.assertRaises(ValueError):weight_percent_dword(bad,100)

if __name__=='__main__':unittest.main()
