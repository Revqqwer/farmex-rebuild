import unittest
from dataclasses import replace
from control_stop_binding import *
from control_settings import ControlSettingsFrame,ControlSettingsObservation
from test_control_settings import fixture

def settings(zone=0,town=0):
 o=fixture();values=dict(o.values);values.update(checked_8a4=zone,checked_8a8=town)
 return ControlSettingsFrame().advance(replace(o,values=values))

def zone_observation(**extra):
 values=dict(first_area_eax=11,tick_eax=0,start_low=0,start_high=0);values.update(extra)
 return TPObservation(values=values,normal_returns={'first_area':True,'area_change_stop':True,'tick':True})

class ControlStopBindingTests(unittest.TestCase):
 def test_town_uses_be_and_disabled_still_returns_one(self):
  for flag in (0,1,2):
   f=ControlStopSnapshotFrame('town',b'\x48',settings(zone=1,town=flag))
   p=f.advance(JailObservation(normal_returns={'town_request_stop':True}),dispatcher_setup_returned=True)
   self.assertTrue(p.complete);self.assertEqual(p.source_return_dword,1)
   self.assertEqual(bool(p.child.calls),bool(flag))

 def test_reached_town_flag_conflict_rejected_before_stop(self):
  f=ControlStopSnapshotFrame('town',b'\x48',settings(town=1))
  with self.assertRaises(ValueError):f.advance(JailObservation(values={'town_request_stop_byte':0}),dispatcher_setup_returned=True)
  self.assertFalse(f.dispatch.child.calls)
  p=f.advance(JailObservation(normal_returns={'town_request_stop':True}))
  self.assertTrue(p.complete)

 def test_zone_reuses_existing_tp_dispatch_with_bd_flag(self):
  f=ControlStopSnapshotFrame('zone',b'\x27\x00\x0a',settings(zone=1,town=0))
  p=f.advance(zone_observation(),dispatcher_setup_returned=True)
  self.assertTrue(p.complete);self.assertEqual(p.source_ret_pop_bytes,4)
  self.assertIn(('0040ae0c',(0,0x561f34),'area_change_stop'),p.child.calls)
  self.assertIn((0x562251,1,'area_change_stop_byte'),p.child.reads)

 def test_full_area_eax_comparison_does_not_truncate_to_byte(self):
  f=ControlStopSnapshotFrame('zone',b'\x27\x00\x0a',settings(zone=1))
  p=f.advance(zone_observation(first_area_eax=0x100a),dispatcher_setup_returned=True)
  self.assertTrue(p.complete);self.assertTrue(any(c[2]=='area_change_stop' for c in p.child.calls))

 def test_equal_area_skips_flag_so_unreached_conflict_is_ignored(self):
  f=ControlStopSnapshotFrame('zone',b'\x27\x00\x0a',settings(zone=1))
  p=f.advance(zone_observation(first_area_eax=10,area_change_stop_byte=0),dispatcher_setup_returned=True)
  self.assertTrue(p.complete);self.assertFalse(any(r[2]=='area_change_stop_byte' for r in p.child.reads))

 def test_accepted_flag_survives_stop_gap_and_later_conflicting_capture(self):
  f=ControlStopSnapshotFrame('zone',b'\x27\x00\x0a',settings(zone=1))
  o=zone_observation();o=replace(o,normal_returns={**o.normal_returns,'area_change_stop':False})
  p=f.advance(o,dispatcher_setup_returned=True);self.assertEqual(p.child.needed,('normal','area_change_stop'))
  p=f.advance(zone_observation(area_change_stop_byte=0));self.assertTrue(p.complete)
  self.assertEqual(f.dispatch.child.observation.values['area_change_stop_byte'],1)
  self.assertEqual(sum(c[2]=='area_change_stop' for c in p.child.calls),1)

 def test_town_earlier_branch_does_not_force_control_flag(self):
  f=ControlStopSnapshotFrame('town',b'\x06',settings(town=1))
  p=f.advance(JailObservation(values={'town_request_stop_byte':0}),dispatcher_setup_returned=True)
  self.assertEqual(p.status,'earlier_branch_not_bound');self.assertIsNone(f.dispatch.child)

 def test_source_settings_and_selected_observation_types_are_required(self):
  incomplete=ControlSettingsFrame().advance(ControlSettingsObservation())
  with self.assertRaises(ValueError):ControlStopSnapshotFrame('town',b'\x48',incomplete)
  with self.assertRaises(ValueError):ControlStopSnapshotFrame('unknown',b'\x48',settings())
  f=ControlStopSnapshotFrame('town',b'\x48',settings())
  with self.assertRaises(ValueError):f.advance(TPObservation())
  with self.assertRaises(TypeError):f.configuration.fields[0xbd]=1
