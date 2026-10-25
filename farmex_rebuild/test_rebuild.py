import json
import tempfile
import unittest
from pathlib import Path
from engine import Vitals, PotionRule, choose_potion, next_check_ms
from profiles import Profiles


class RulesTests(unittest.TestCase):
    def test_mp_precedes_hp_when_both_low(self):
        result = choose_potion(Vitals(10, 100, 10, 100), PotionRule(True, 50, 2),
                               PotionRule(True, 50, 1), {1, 2})
        self.assertEqual((result.resource, result.item_id), ('MP', 2))

    def test_missing_mp_allows_hp(self):
        result = choose_potion(Vitals(10, 100, 10, 100), PotionRule(True, 50, 2),
                               PotionRule(True, 50, 1), {1})
        self.assertEqual(result.resource, 'HP')

    def test_fallback(self):
        result = choose_potion(Vitals(90, 100, 10, 100), PotionRule(True, 50, 2, 3),
                               PotionRule(), {3})
        self.assertEqual(result.item_id, 3)

    def test_integer_threshold_and_inclusive_boundary(self):
        mp = PotionRule(True, 50, 2)
        self.assertIsNotNone(choose_potion(Vitals(100, 100, 50, 101), mp, PotionRule(), {2}))
        self.assertIsNone(choose_potion(Vitals(100, 100, 51, 101), mp, PotionRule(), {2}))

    def test_disabled_and_no_inventory(self):
        self.assertIsNone(choose_potion(Vitals(0, 100, 0, 100), PotionRule(), PotionRule(), {1}))
        self.assertIsNone(choose_potion(Vitals(0, 100, 0, 100), PotionRule(True, 50, 2), PotionRule(), set()))

    def test_local_scheduler(self):
        self.assertEqual(next_check_ms(True), 3000)
        self.assertEqual(next_check_ms(False), 50)

    def test_invalid_values(self):
        with self.assertRaises(ValueError):
            Vitals(101, 100, 1, 100)
        with self.assertRaises(ValueError):
            PotionRule(True, 101, 2)


class ProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((Path(__file__).parent / 'ui_model.json').read_text(encoding='utf-8'))

    def test_catalog_integrity_and_profile_roundtrip(self):
        self.assertEqual(len(self.catalog), 1037)
        self.assertEqual(len({n['path'] for n in self.catalog}), 1037)
        self.assertEqual(sum('/' not in n['path'] for n in self.catalog), 11)
        profiles = Profiles(self.catalog)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'örnek.json'
            profiles.save(path, profiles.defaults)
            self.assertEqual(profiles.load(path), profiles.defaults)
            self.assertEqual(len(list(Path(directory).iterdir())), 1)

    def test_unknown_key_and_bool_as_int_rejected(self):
        profiles = Profiles(self.catalog)
        with self.assertRaises(ValueError):
            profiles.validate({'version': 1, 'values': {'unknown': True}})
        key = next(k for k, v in profiles.defaults.items() if type(v) is int)
        with self.assertRaises(ValueError):
            profiles.validate({'version': 1, 'values': {key: True}})

    def test_partial_profile_uses_defaults(self):
        profiles = Profiles(self.catalog)
        self.assertEqual(profiles.validate({'version': 1, 'values': {}}), profiles.defaults)

    def test_bad_combo_does_not_overwrite_saved_profile(self):
        profiles = Profiles(self.catalog)
        key = next(k for k in profiles.bounds if self.catalog[[n['path'] for n in self.catalog].index(k)]['class'] == 'TComboBox')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'profile.json'
            profiles.save(path, profiles.defaults)
            original = path.read_bytes()
            invalid = dict(profiles.defaults, **{key: 999999})
            with self.assertRaises(ValueError):
                profiles.save(path, invalid)
            self.assertEqual(path.read_bytes(), original)

    def test_radio_group_exclusion_and_saved_conflict(self):
        profiles = Profiles(self.catalog)
        group = next(g for g in profiles.radio_groups.values() if len(g) > 1)
        values = dict(profiles.defaults)
        profiles.update(values, group[0], True)
        profiles.update(values, group[1], True)
        self.assertFalse(values[group[0]])
        self.assertTrue(values[group[1]])
        values[group[0]] = True
        with self.assertRaises(ValueError):
            profiles.validate({'version': 1, 'values': values})

    def test_invalid_update_is_transactional(self):
        profiles = Profiles(self.catalog)
        values = dict(profiles.defaults)
        original = dict(values)
        key = next(iter(profiles.bounds))
        with self.assertRaises(ValueError):
            profiles.update(values, key, 999999)
        self.assertEqual(values, original)


if __name__ == '__main__':
    unittest.main()
