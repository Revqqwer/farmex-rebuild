import unittest
from dataclasses import replace
from item_break_settings import ItemBreakSettingsFrame, ItemBreakSettingsObservation
from protection_settings import ProtectionSettingsObservation
from source_integer import SourceIntegerObservation

def fixture(enabled=1, reset=1, fresh=1, number=None):
    child = number or SourceIntegerObservation(
        text_copy_returned=True, route='catch_landing',
        catch_landing_returned=True, cleanup_returned=True,
    )
    prefix = ProtectionSettingsObservation(
        entry_reached=True, values={'checked_ec0': enabled},
        normal_returns={key: True for key in (
            'checked_ec0', 'init_ec8', 'text_ec8', 'parser_outer_ec8', 'text_cleanup_ec8')},
        texts={'ec8': 'captured text, no lexical parse assumed'}, integer_children={'ec8': child},
    )
    return ItemBreakSettingsObservation(prefix, True, reset, fresh, True)

def parsed(value):
    return SourceIntegerObservation(True, 'normal', True, value & ((1 << 64) - 1),
                                    cleanup_returned=True)

class ItemBreakSettingsTests(unittest.TestCase):
    def test_entry_stops_before_any_getter_or_write(self):
        plan = ItemBreakSettingsFrame().advance(ItemBreakSettingsObservation())
        self.assertFalse(plan.complete)
        self.assertEqual(plan.needed, ('settings', ('entry', '00470cd5')))
        self.assertEqual(plan.stores, ())

    def test_explicit_catch_fallback_one_and_single_dword_reset(self):
        plan = ItemBreakSettingsFrame().advance(fixture())
        self.assertTrue(plan.complete)
        self.assertEqual(plan.stores, ((0x569a20, 1, 1), (0x569a24, 4, 1), (0x569a2c, 4, 0)))
        self.assertEqual(plan.next_address, 0x470d87)
        self.assertFalse(plan.whole_function_verified)
        self.assertFalse(plan.live_compatibility_verified)

    def test_only_low_eax_byte_controls_reset_without_touching_other_state(self):
        plan = ItemBreakSettingsFrame().advance(fixture(enabled=0xabcdef7f, reset=0x100))
        self.assertEqual(plan.stores, ((0x569a20, 1, 0x7f), (0x569a24, 4, 1)))
        plan = ItemBreakSettingsFrame().advance(fixture(reset=0x10000ff))
        self.assertEqual(plan.stores[-1], (0x569a2c, 4, 0))

    def test_speed_low_dword_truncation_without_range_clamp(self):
        for value, expected in ((0x12345678abcdef01, 0xabcdef01), (-1, 0xffffffff), (0, 0)):
            plan = ItemBreakSettingsFrame().advance(fixture(number=parsed(value)))
            self.assertEqual(plan.stores[1], (0x569a24, 4, expected))

    def test_number_is_read_even_when_enable_zero_and_needs_child_receipt(self):
        sample = fixture(enabled=0)
        sample = replace(sample, settings=replace(sample.settings, integer_children={}))
        frame = ItemBreakSettingsFrame()
        plan = frame.advance(sample)
        self.assertEqual(plan.needed, ('settings', ('child', 'ec8')))
        self.assertEqual(plan.stores, ((0x569a20, 1, 0),))
        self.assertNotIn((0x569a24, 4, 1), plan.stores)

    def test_outer_parser_and_cleanup_gaps_keep_prefix_and_block_suffix(self):
        sample = fixture()
        normals = dict(sample.settings.normal_returns)
        normals['parser_outer_ec8'] = False
        frame = ItemBreakSettingsFrame()
        plan = frame.advance(replace(sample, settings=replace(sample.settings, normal_returns=normals)))
        self.assertEqual(plan.needed, ('settings', ('normal', 'parser_outer_ec8')))
        self.assertEqual(len(plan.stores), 1)
        plan = frame.advance(ItemBreakSettingsObservation(settings=ProtectionSettingsObservation(
            normal_returns={'parser_outer_ec8': True})))
        self.assertEqual(plan.needed, ('settings', ('normal', 'text_cleanup_ec8')))
        self.assertEqual(len(plan.stores), 2)
        self.assertFalse(any(call[2] == 'reset_checked_a28' for call in plan.calls))
        plan = frame.advance(ItemBreakSettingsObservation(settings=ProtectionSettingsObservation(
            normal_returns={'text_cleanup_ec8': True})))
        self.assertEqual(plan.needed, 'reset_checked_returned')

    def test_fresh_enabled_operand_cannot_be_assumed_from_earlier_store(self):
        for stored, fresh, argument in ((1, 0, 0), (0, 255, 1)):
            frame = ItemBreakSettingsFrame()
            plan = frame.advance(replace(fixture(enabled=stored), fresh_enabled_byte=None))
            self.assertEqual(plan.needed, 'fresh_enabled_byte')
            self.assertIsNone(plan.toggle_argument)
            plan = frame.advance(ItemBreakSettingsObservation(fresh_enabled_byte=fresh, toggle_returned=True))
            self.assertEqual(plan.toggle_argument, argument)
            self.assertEqual(plan.toggle_physical_pushes, (argument, 0x561f34))
            self.assertEqual(plan.calls[-1], ('0040ae0c', (0x561f34, argument), 'toggle_returned'))

    def test_getter_normal_receipt_precedes_raw_result(self):
        frame = ItemBreakSettingsFrame()
        plan = frame.advance(replace(fixture(), reset_checked_returned=False))
        self.assertEqual(plan.needed, 'reset_checked_returned')
        self.assertEqual(len(plan.stores), 2)
        plan = frame.advance(ItemBreakSettingsObservation(reset_checked_returned=True))
        self.assertEqual(plan.needed, 'reset_checked_eax')

    def test_toggle_gap_retains_consumed_inputs_and_final_is_idempotent(self):
        frame = ItemBreakSettingsFrame()
        first = frame.advance(replace(fixture(), toggle_returned=False))
        changed = replace(fixture(enabled=0, reset=0, fresh=0, number=parsed(999)), toggle_returned=True)
        final = frame.advance(changed)
        self.assertTrue(final.complete)
        self.assertEqual(final.stores, first.stores)
        self.assertEqual(final.toggle_argument, 1)
        self.assertIs(frame.advance(ItemBreakSettingsObservation()), final)

    def test_wrapped_own_context_and_typed_operand_checks(self):
        plan = ItemBreakSettingsFrame(context=0xfffffffc).advance(fixture())
        self.assertEqual(plan.stores, ((0xfffffffc, 1, 1), (0, 4, 1), (8, 4, 0)))
        for args in ({'fresh_enabled_byte': 256}, {'reset_checked_eax': -1},
                     {'toggle_returned': 1}, {'settings': {}}, {'reset_checked_eax': True}):
            with self.assertRaises(ValueError):
                ItemBreakSettingsObservation(**args)
        with self.assertRaises(ValueError):
            ItemBreakSettingsFrame(context=-1)

if __name__ == '__main__':
    unittest.main()
