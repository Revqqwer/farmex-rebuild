import json,unittest
from pathlib import Path
from class_configuration import compile_class_configuration,ClassConfiguration
from support_configuration import support_settings_from_config
from combat_engine import Vitals,SupportSnapshot,priest_heal,rogue_minor,kurian_heal
from profiles import Profiles

class SupportConfigurationTests(unittest.TestCase):
    def setUp(self):
        base=Path(__file__).parent
        self.schema=json.loads((base/'class_configuration_map.json').read_text(encoding='utf-8'))
        self.profiles=Profiles(json.loads((base/'ui_model.json').read_text(encoding='utf-8')))
        self.values=dict(self.profiles.defaults);self.lists=self.profiles.validate_lists({})
    def set(self,job,kind,suffix,value):
        path=next(p for p in self.schema[job][kind] if p.endswith('/'+suffix))
        self.profiles.update(self.values,path,value)
    def compile(self,job):
        return support_settings_from_config(compile_class_configuration(job,self.values,self.lists))
    def snapshot(self,**changes):
        values=dict(now_ms=10000,actor=Vitals(1,20,100,1100),global_blocked=False,
            route_guard_active=False,alternate_action_path=False,self_heal_ready=True,
            unnamed_stat=5,kurian_action_ready=True)
        values.update(changes);return SupportSnapshot(**values)

    def test_priest_threshold_and_combo_become_exact_skill_settings(self):
        self.set('priest','booleans','chSelfHeal',True)
        self.set('priest','integers','txtSelfHealPercent','40')
        self.set('priest','combos','cmbSelfHeal',3)
        settings=self.compile('priest')
        self.assertEqual((settings.self_threshold,settings.self_skill_id),(40,500))
        self.assertEqual(priest_heal(settings,self.snapshot()).intent.skill_id,500)

    def test_priest_disabled_flag_is_not_synthetic_enabled(self):
        self.set('priest','booleans','chSelfHeal',False)
        self.set('priest','booleans','chPartyHeal',False)
        self.assertEqual(priest_heal(self.compile('priest'),self.snapshot()).status,'no_action')

    def test_priest_party_and_route_fields_are_kept(self):
        self.set('priest','booleans','chPartyHeal',True)
        self.set('priest','integers','txtPartyHealPercent','33')
        self.set('priest','combos','cmbPartyHeal',2)
        self.set('priest','booleans','chPriRouteNotHeal',True)
        settings=self.compile('priest')
        self.assertEqual((settings.party_enabled,settings.party_threshold,settings.party_skill_id),(True,33,5))
        self.assertEqual(priest_heal(settings,self.snapshot(route_guard_active=True)).status,'blocked')

    def test_minor_speed_and_threshold_come_from_panel(self):
        self.set('rogue','booleans','chmnr',True)
        self.set('rogue','integers','txtminor','25')
        # Keep the catalog's original identifier bytes/decoding; resolve speed by proven offset.
        speed=next(p for p,o in self.schema['rogue']['integers'].items() if o==8)
        self.profiles.update(self.values,speed,'1500')
        settings=self.compile('rogue');self.assertEqual(settings.interval_ms,1500)
        self.assertEqual(rogue_minor(settings,self.snapshot(last_minor_ms=9000)).status,'waiting')
        self.assertIsNotNone(rogue_minor(settings,self.snapshot(last_minor_ms=8000)).intent)

    def test_mage_flags_threshold_and_name_are_preserved(self):
        self.set('mage','booleans','chMageHPTP',True);self.set('mage','integers','txtMageHPTP','45')
        self.set('mage','booleans','chMageConTP',True);self.set('mage','texts','txtMageTPNick','İsim X')
        settings=self.compile('mage')
        self.assertEqual((settings.low_hp_tp,settings.threshold,settings.continuous_name_tp,settings.target_name),
                         (True,45,True,'İsim X'))

    def test_kurian_checkbox_and_percent_control_local_decision(self):
        self.set('kurian','booleans','chKurianSelfHeal',True)
        self.set('kurian','integers','txtKurianSelfHealPercent','19')
        self.assertEqual(kurian_heal(self.compile('kurian'),self.snapshot()).status,'no_action')
        self.set('kurian','integers','txtKurianSelfHealPercent','20')
        self.assertIsNotNone(kurian_heal(self.compile('kurian'),self.snapshot()).intent)

    def test_missing_field_is_not_defaulted(self):
        with self.assertRaises(ValueError):support_settings_from_config(ClassConfiguration('rogue','source',{0:True},{4:50},()))

    def test_out_of_model_range_is_rejected_not_clamped(self):
        self.set('rogue','integers','txtminor','101')
        with self.assertRaises(ValueError):self.compile('rogue')

    def test_unknown_support_class_is_not_guessed(self):
        with self.assertRaises(ValueError):self.compile('warrior')
