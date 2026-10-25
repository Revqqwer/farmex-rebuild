import json
import unittest
from pathlib import Path
from profiles import Profiles
from configuration import compile_potions, HEALTH_PREFIX


class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        catalog = json.loads((Path(__file__).parent / 'ui_model.json').read_text(encoding='utf-8'))
        self.values = dict(Profiles(catalog).defaults)

    def test_source_defaults_and_changed_control_binding(self):
        initial = compile_potions(self.values)
        self.assertFalse(initial.hp_enabled)
        self.assertEqual(initial.mp_threshold, 35)
        self.values[HEALTH_PREFIX+'chhp'] = True
        self.values[HEALTH_PREFIX+'txthp'] = '70'
        self.values[HEALTH_PREFIX+'cmbhppot'] = 9
        changed = compile_potions(self.values)
        self.assertEqual((changed.hp_enabled, changed.hp_threshold, changed.hp_combo_index), (True, 70, 9))

    def test_invalid_percent_is_not_silently_defaulted(self):
        for value in ['abc', '101', '-1']:
            self.values[HEALTH_PREFIX+'txthp'] = value
            with self.assertRaises(ValueError):
                compile_potions(self.values)

    def test_unselected_combo_uses_fallthrough_and_bool_is_not_index(self):
        self.values[HEALTH_PREFIX+'cmbhppot'] = -1
        self.assertEqual(compile_potions(self.values).hp_combo_index, 0)
        self.values[HEALTH_PREFIX+'cmbhppot'] = True
        with self.assertRaises(ValueError):
            compile_potions(self.values)


if __name__ == '__main__':
    unittest.main()
