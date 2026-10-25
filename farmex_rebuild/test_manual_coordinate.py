import unittest
from dataclasses import replace
from manual_coordinate import *


def sample():
    normals = {axis + '_' + stage: True for axis in ('x', 'y')
               for stage in ('construct', 'get_text', 'parse', 'cleanup')}
    normals.update(entry_setup=True, movement=True)
    return ManualCoordinateObservation(True, {'x': '10', 'y': '20'},
                                       {'x': 0x41200000, 'y': 0x41a00000}, normals)


class ManualCoordinateTests(unittest.TestCase):
    def test_entry_is_required_before_any_call(self):
        p = plan_manual_coordinate(ManualCoordinateObservation())
        self.assertEqual(p.needed, ('entry', '004a8478'))
        self.assertEqual(p.steps, ())

    def test_source_order_fields_and_physical_pushes(self):
        p = plan_manual_coordinate(sample())
        self.assertTrue(p.complete)
        self.assertEqual([s[1] for s in p.steps if s[0] == 'form_field'], [0x4f8, 0x4fc])
        self.assertEqual(p.movement, (0x41200000, 0x41a00000))
        self.assertIn(('physical_push_y_x', 0x41a00000, 0x41200000), p.steps)
        self.assertFalse(p.native_execution_verified)
        self.assertFalse(p.live_compatibility_verified)
        self.assertFalse(p.exceptional_paths_verified)

    def test_every_normal_gap_blocks_later_source_calls(self):
        full = sample()
        order = ['entry_setup'] + [a + '_' + s for a in ('x', 'y')
                                  for s in ('construct', 'get_text', 'parse', 'cleanup')] + ['movement']
        for i, name in enumerate(order):
            with self.subTest(name=name):
                p = plan_manual_coordinate(replace(full, normal_returns={**full.normal_returns, name: False}))
                self.assertEqual(p.needed, ('normal', name))
                self.assertEqual([s[3] for s in p.steps if s[0] == 'call'], order[:i+1])

    def test_parse_return_does_not_supply_binary32_rounding(self):
        p = plan_manual_coordinate(replace(sample(), float_bits={}))
        self.assertEqual(p.needed, ('float_bits', 'x'))
        self.assertEqual(p.coordinates, ())
        self.assertIsNone(p.movement)

    def test_x_cleanup_holds_y_acquisition_and_preserves_x(self):
        f = ManualCoordinateFrame(); o = sample()
        p = f.advance(replace(o, normal_returns={**o.normal_returns, 'x_cleanup': False}))
        self.assertEqual(p.coordinates, (0x41200000,))
        self.assertEqual(p.needed, ('normal', 'x_cleanup'))
        self.assertNotIn('y', f.observation.texts)
        changed = replace(o, texts={'x': '999', 'y': '30'}, float_bits={'x': 0, 'y': 0x41f00000})
        p = f.advance(changed)
        self.assertEqual(p.movement, (0x41200000, 0x41f00000))
        self.assertIn(('getter_text', 'x', '10'), p.steps)
        self.assertIn(('getter_text', 'y', '30'), p.steps)

    def test_getter_return_and_text_are_separate_captures(self):
        f = ManualCoordinateFrame(); o = sample()
        p = f.advance(replace(o, texts={}))
        self.assertEqual(p.needed, ('text', 'x'))
        self.assertTrue(f.observation.normal_returns['x_get_text'])
        self.assertNotIn('x_parse', f.observation.normal_returns)
        self.assertTrue(f.advance(o).complete)

    def test_raw_float_payloads_have_no_invented_range_or_finite_gate(self):
        o = replace(sample(), float_bits={'x': 0x80000000, 'y': 0x7fc12345})
        self.assertEqual(plan_manual_coordinate(o).movement, (0x80000000, 0x7fc12345))

    def test_text_is_not_python_parsed_or_normalized(self):
        o = replace(sample(), texts={'x': '1,5', 'y': '\x00\ud800'})
        p = plan_manual_coordinate(o)
        self.assertTrue(p.complete)
        self.assertIn(('call', '00506348', ('1,5',), 'x_parse'), p.steps)

    def test_movement_receipt_resumes_and_terminal_result_is_immutable(self):
        f = ManualCoordinateFrame(); o = sample()
        p = f.advance(replace(o, normal_returns={**o.normal_returns, 'movement': False}))
        self.assertEqual(p.needed, ('normal', 'movement'))
        self.assertIsNotNone(p.movement)
        done = f.advance(ManualCoordinateObservation(normal_returns={'movement': True}))
        self.assertTrue(done.complete)
        self.assertIs(f.advance(ManualCoordinateObservation()), done)

    def test_rejects_bool_overflow_and_mutable_observation_aliases(self):
        for bits in (-1, 1 << 32, True):
            with self.assertRaises(ValueError):
                ManualCoordinateObservation(float_bits={'x': bits})
        d = {'x': 'old'}; o = ManualCoordinateObservation(texts=d); d['x'] = 'new'
        self.assertEqual(o.texts['x'], 'old')
        with self.assertRaises(TypeError): o.texts['x'] = 'changed'


if __name__ == '__main__':
    unittest.main()
