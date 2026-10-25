import json
import tempfile
import unittest
from pathlib import Path
from profiles import Profiles


class ListProfileTests(unittest.TestCase):
    def setUp(self):
        catalog = json.loads((Path(__file__).parent / 'ui_model.json').read_text(encoding='utf-8'))
        self.profiles = Profiles(catalog)

    def test_version_two_roundtrip_with_changed_selection_and_rows(self):
        lists = self.profiles.validate_lists({})
        key = next(k for k, rows in lists.items() if rows)
        lists[key][0]['checked'] = True
        lists[key].append({'caption': 'Örnek', 'subitems': ['12', '34'], 'checked': False})
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'profile.json'
            self.profiles.save(path, self.profiles.defaults, lists)
            values, loaded = self.profiles.load_document(path)
            self.assertEqual(values, self.profiles.defaults)
            self.assertEqual(loaded, lists)

    def test_v1_migration_and_default_list_independence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'v1.json'
            self.profiles.save(path, self.profiles.defaults)
            _, first = self.profiles.load_document(path)
            _, second = self.profiles.load_document(path)
            key = next(k for k, rows in first.items() if rows)
            first[key][0]['caption'] = 'Changed'
            self.assertNotEqual(first[key], second[key])

    def test_invalid_list_does_not_replace_profile(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'profile.json'
            self.profiles.save(path, self.profiles.defaults, {})
            original = path.read_bytes()
            with self.assertRaises(ValueError):
                self.profiles.save(path, self.profiles.defaults, {'unknown': []})
            self.assertEqual(path.read_bytes(), original)

    def test_row_type_and_unknown_fields(self):
        key = next(iter(self.profiles.list_defaults))
        for row in [{'caption': 'A', 'subitems': [1], 'checked': False},
                    {'caption': 'A', 'subitems': [], 'checked': 1},
                    {'caption': 'A', 'subitems': [], 'checked': False, 'extra': True}]:
            with self.assertRaises(ValueError):
                self.profiles.validate_lists({key: [row]})


if __name__ == '__main__':
    unittest.main()
