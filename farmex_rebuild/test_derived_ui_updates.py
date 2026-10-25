import json,unittest
from pathlib import Path
from types import MappingProxyType
from profiles import Profiles

class DerivedUiUpdateTests(unittest.TestCase):
    def setUp(self):
        catalog=json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf-8'))
        self.profiles=Profiles(catalog);self.values=dict(self.profiles.defaults)
        self.normal='frmMain/MainTab/SheetBot/GroupBox34/rdUseNormalSkill'
        self.group=next(g for g in self.profiles.radio_groups.values() if self.normal in g)

    def test_normal_effect_clears_sibling_and_preserves_shared_mapping(self):
        sibling=next(k for k in self.group if k!=self.normal)
        self.profiles.update(self.values,sibling,True)
        identity=id(self.values)
        self.profiles.apply_boolean_updates(self.values,MappingProxyType({self.normal:True}))
        self.assertEqual(id(self.values),identity)
        self.assertTrue(self.values[self.normal]);self.assertFalse(self.values[sibling])

    def test_unknown_effect_rolls_back_whole_update(self):
        before=dict(self.values)
        with self.assertRaises(ValueError):self.profiles.apply_boolean_updates(self.values,{self.normal:True,'unknown':True})
        self.assertEqual(self.values,before)

    def test_wrong_value_type_is_rejected_without_changes(self):
        before=dict(self.values)
        with self.assertRaises(ValueError):self.profiles.apply_boolean_updates(self.values,{self.normal:1})
        self.assertEqual(self.values,before)

    def test_conflicting_radio_effects_are_not_order_dependent(self):
        before=dict(self.values)
        with self.assertRaises(ValueError):self.profiles.apply_boolean_updates(self.values,{k:True for k in self.group})
        self.assertEqual(self.values,before)

    def test_empty_effect_does_not_reset_latched_normal_choice(self):
        self.profiles.apply_boolean_updates(self.values,{self.normal:True})
        self.profiles.apply_boolean_updates(self.values,{})
        self.assertTrue(self.values[self.normal])
