import json,unittest
from pathlib import Path
from combat_configuration import PREFIX,compile_bot_combat
from profiles import Profiles
from priest_attack import PriestAttackSnapshot,select_priest_attack
from mage_attack import MageAttackSnapshot,select_mage_attack

class BotCombatConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.profiles=Profiles(json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf-8')))
        self.values=dict(self.profiles.defaults)
        self.set('rdUseNormalSkill',True)
        self.set('GroupBox35/chNManuelAtackSpeed',False)
        self.set('GroupBox38/chLManuelAtackSpeed',False)
    def set(self,name,value):self.profiles.update(self.values,PREFIX+name,value)
    def test_normal_default_interval_and_selected_ranges(self):
        self.set('GroupBox35/txtNAtackDistance','7');self.set('GroupBox35/txtNMobSelectDistance','31')
        self.set('GroupBox35/txtNMobSelectSpeed','321')
        settings=compile_bot_combat(self.values)
        self.assertEqual((settings.legal_mode,settings.attack_interval_ms,settings.attack_range,settings.target_range,
                          settings.target_select_ms),(False,1250,7,31,321))
    def test_legal_default_interval_and_own_fields(self):
        self.set('rdUseLegalSkill',True);self.set('GroupBox38/txtLAtackDistance','3')
        settings=compile_bot_combat(self.values)
        self.assertEqual((settings.legal_mode,settings.attack_interval_ms,settings.attack_range),(True,250,3))
    def test_manual_speed_switches_only_active_branch(self):
        self.set('GroupBox35/chNManuelAtackSpeed',True);self.set('GroupBox35/txtNiManuelAtackSpeed','2345')
        self.set('GroupBox38/chLManuelAtackSpeed',True);self.set('GroupBox38/txtLiManuelAtackSpeed','456')
        self.assertEqual(compile_bot_combat(self.values).attack_interval_ms,2345)
        self.set('rdUseLegalSkill',True)
        self.assertEqual(compile_bot_combat(self.values).attack_interval_ms,456)
    def test_legal_signed_speed_has_explicit_dword_representation(self):
        self.set('rdUseLegalSkill',True);self.set('GroupBox38/chLManuelAtackSpeed',True)
        self.set('GroupBox38/txtLiManuelAtackSpeed','-1')
        self.assertEqual(compile_bot_combat(self.values).attack_interval_ms,0xffffffff)
    def test_signed_range_is_not_clamped(self):
        self.set('GroupBox35/txtNAtackDistance','-1')
        self.assertEqual(compile_bot_combat(self.values).attack_range,-1)
    def test_normal_manual_outside_parser_bounds_needs_fallback(self):
        self.set('GroupBox35/chNManuelAtackSpeed',True)
        for value in ('-1','100000'):
            self.set('GroupBox35/txtNiManuelAtackSpeed',value)
            with self.assertRaises(ValueError):compile_bot_combat(self.values)
    def test_strict_decimal_policy_rejects_unknown_default(self):
        for value in ('','not a number','0x10','2147483648'):
            self.set('GroupBox35/txtNAtackDistance',value)
            with self.assertRaises(ValueError):compile_bot_combat(self.values)
    def test_missing_key_or_nonboolean_mode_not_guessed(self):
        values=dict(self.values);values.pop(PREFIX+'rdUseLegalSkill')
        with self.assertRaises(ValueError):compile_bot_combat(values)
        values=dict(self.values);values[PREFIX+'rdUseLegalSkill']=1
        with self.assertRaises(ValueError):compile_bot_combat(values)
    def test_priest_range_reaches_existing_gate(self):
        self.set('GroupBox35/txtNAtackDistance','4')
        settings=compile_bot_combat(self.values)
        snapshot=PriestAttackSnapshot(10000,5,settings.attack_range,None,{}, {}, {},locked_561f7e=False)
        self.assertEqual(select_priest_attack(snapshot).status,'out_of_range')
    def test_mage_source_cap_remains_45_for_range_eight_or_more(self):
        self.set('GroupBox35/txtNAtackDistance','50')
        snapshot=MageAttackSnapshot(10000,46,compile_bot_combat(self.values).attack_range,None,{}, {},{},locked_561f7e=False)
        self.assertEqual(select_mage_attack(snapshot).status,'out_of_range')
    def test_runtime_override_copies_matching_branch_without_changing_ui(self):
        before=dict(self.values)
        settings=compile_bot_combat(self.values,mode_byte_override=255)
        self.assertTrue(settings.legal_mode);self.assertEqual(settings.attack_interval_ms,250)
        self.assertEqual(self.values,before)
        self.set('rdUseLegalSkill',True)
        self.assertFalse(compile_bot_combat(self.values,mode_byte_override=0).legal_mode)
    def test_raw_mode_override_type_is_not_inferred(self):
        for value in (True,-1,256):
            with self.assertRaises(ValueError):compile_bot_combat(self.values,mode_byte_override=value)
