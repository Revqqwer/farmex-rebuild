import copy
import json
import unittest
from pathlib import Path
from profiles import Profiles
from operation_engine import UpgradeSnapshot
from upgrade_configuration import (SCROLL_PATH, WAIT_PATH, ANVIL_PATH, LIST_PATH,
    compile_upgrade_panel, upgrade_runner_from_panel, selected_upgrade_scroll_text)


class UpgradeConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((Path(__file__).parent/'ui_model.json').read_text(encoding='utf-8'))
        cls.profiles = Profiles(cls.catalog)

    def setUp(self):
        self.values = dict(self.profiles.defaults)
        self.lists = self.profiles.validate_lists({})

    def compile(self, text='explicit scroll'):
        return compile_upgrade_panel(self.values, self.lists, scroll_text=text)

    def test_real_defaults_and_immutable_fields(self):
        p = self.compile()
        self.assertEqual(dict(p.fields), {4: 2000, 8: 0})
        self.assertFalse(p.independently_verified)
        self.assertFalse(p.ansi_conversion_verified)
        with self.assertRaises(TypeError):
            p.fields[4] = 10

    def test_checked_caption_order_duplicates_and_unchecked_bypass(self):
        self.lists[LIST_PATH] = [{'caption': '17', 'checked': True, 'subitems': ['999']},
                                {'caption': 'invalid', 'checked': False},
                                {'caption': '-1', 'checked': True},
                                {'caption': '17', 'checked': True}]
        p = self.compile()
        self.assertEqual([r.item_key for r in p.rows], [17, 0xffffffff, 17])

    def test_selected_invalid_caption_has_no_partial_profile_mutation(self):
        self.lists[LIST_PATH] = [{'caption': '1', 'checked': True}, {'caption': 'bad', 'checked': True}]
        before = copy.deepcopy((self.values, self.lists))
        with self.assertRaises(ValueError):
            self.compile()
        self.assertEqual((self.values, self.lists), before)

    def test_signed64_scalar_low_dword_and_distinct_units(self):
        self.values[WAIT_PATH] = '4294968796'
        self.values[ANVIL_PATH] = '-1'
        p = self.compile()
        runner = upgrade_runner_from_panel(p)
        self.assertEqual((runner.interval_ms, runner.anvil_id), (1500, 0xffffffff))
        runner.start((), initial_stamp_qword=0)
        self.assertEqual(runner.tick(UpgradeSnapshot(1499)).status, 'waiting')
        self.assertEqual(runner.tick(UpgradeSnapshot(1500)).reason, 'queue_empty')

    def test_negative_timer_is_signed_on_source_clock_path(self):
        self.values[WAIT_PATH] = '-1'
        p = self.compile()
        self.assertEqual(p.fields[4], 0xffffffff)
        runner = upgrade_runner_from_panel(p)
        self.assertTrue(runner.source_clock)
        runner.start((), initial_stamp_qword=0)
        self.assertEqual(runner.tick(UpgradeSnapshot(0)).reason, 'queue_empty')

    def test_combo_gettext_is_not_itemindex_or_inventory_index(self):
        text = selected_upgrade_scroll_text(self.values, self.catalog)
        self.assertEqual(text, 'Upgrade Scroll (Low Class item)')
        p = self.compile(text)
        self.assertEqual(p.scroll_text, text)
        self.assertFalse(hasattr(p, 'scroll_index'))
        self.values[SCROLL_PATH] = -1
        self.assertIsNone(selected_upgrade_scroll_text(self.values, self.catalog))
        p = self.compile(None)
        self.assertTrue(p.missing)
        with self.assertRaises(ValueError):
            upgrade_runner_from_panel(p)
        self.assertEqual(self.compile('').scroll_text, '')

    def test_local_parser_bounds_and_types(self):
        for invalid in (True, '0x10', '1.0', str(1 << 63), str(-(1 << 63)-1)):
            self.values[WAIT_PATH] = invalid
            with self.assertRaises(ValueError):
                self.compile()
        self.values[WAIT_PATH] = ' +2000 '
        self.assertEqual(self.compile().fields[4], 2000)
        for caption in (str(1 << 31), str(-(1 << 31)-1), ''):
            self.lists[LIST_PATH] = [{'caption': caption, 'checked': True}]
            with self.assertRaises(ValueError):
                self.compile()

    def test_runner_consumes_panel_without_inventing_game_gate(self):
        self.values[WAIT_PATH] = '1500'
        self.values[ANVIL_PATH] = '42'
        self.lists[LIST_PATH] = [{'caption': '11', 'checked': True}, {'caption': '22', 'checked': True}]
        p = self.compile()
        runner = upgrade_runner_from_panel(p)
        runner.start(p.rows, initial_stamp_qword=0)
        self.assertEqual(runner.tick(UpgradeSnapshot(1500)).status, 'needs_adapter')
        self.assertEqual(runner.queue, (11, 22))
        action = runner.tick(UpgradeSnapshot(1500, True, source_helper_returned=True,
                                            source_stamp_tick_dword=1501)).intents[0]
        self.assertEqual((action.item_id, action.reference, runner.queue), (11, '42', (22,)))
