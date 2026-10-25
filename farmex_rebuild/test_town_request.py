import unittest
from dataclasses import replace
from town_request import *

def sample(flag=1,returned=True):
 return JailObservation(True,{'town_request_stop_byte':flag},{'town_request_stop':returned})

class TownRequestTests(unittest.TestCase):
 def test_explicit_middle_entry_and_exact_byte_read(self):
  f=TownRequestFrame(b'\x48');p=f.advance(JailObservation())
  self.assertEqual(p.needed,('entry','004e35de'));self.assertFalse(p.reads or p.calls)
  p=f.advance(JailObservation(True));self.assertEqual(p.needed,('value','town_request_stop_byte'))
  self.assertEqual(p.reads,((0x562252,1,'town_request_stop_byte'),))

 def test_flag_matrix_and_unconditional_normal_return_one(self):
  for flag in (0,1,2,255):
   p=TownRequestFrame(b'\x48').advance(sample(flag))
   self.assertTrue(p.complete);self.assertEqual(p.planned_eax,1);self.assertEqual(p.source_ret_pop_bytes,12)
   self.assertEqual(p.next_address,0x4e3ca7)
   self.assertEqual(p.calls,() if flag==0 else (('0040ae0c',(0,0x561f34),'town_request_stop'),))
   self.assertFalse(p.whole_handler_verified or p.native_execution_verified or p.live_compatibility_verified)

 def test_stop_return_gap_preserves_flag_and_single_call(self):
  f=TownRequestFrame(b'\x48');p=f.advance(sample(1,False))
  self.assertEqual(p.needed,('normal','town_request_stop'));self.assertIsNone(p.planned_eax)
  self.assertEqual(len(p.calls),1)
  p=f.advance(sample(0));self.assertTrue(p.complete);self.assertEqual(len(p.calls),1)
  self.assertEqual(f.values['town_request_stop_byte'],1);self.assertIs(f.advance(JailObservation()),p)

 def test_non48_falls_through_without_reading_flag_or_claiming_return(self):
  p=TownRequestFrame(b'\x49').advance(sample())
  self.assertTrue(p.complete);self.assertEqual(p.next_address,0x4e361b)
  self.assertFalse(p.reads or p.calls);self.assertIsNone(p.planned_eax)

 def test_immutable_packet_and_source_pin_validation(self):
  for packet in (b'',bytearray(b'\x48'),'48'):
   with self.assertRaises(ValueError):TownRequestFrame(packet)
  with self.assertRaises(ValueError):TownRequestFrame(b'\x48',source_sha256='unknown')
  with self.assertRaises(ValueError):TownRequestFrame(b'\x48').advance({})
  with self.assertRaises(ValueError):sample(256)

 def test_child_entry_cannot_bypass_prologue(self):
  f=TownRequestDispatchFrame(b'\x48');p=f.advance(sample())
  self.assertEqual(p.status,'needs_dispatcher_setup');self.assertIsNone(f.child)
  self.assertFalse(p.opcode_reads)

 def test_each_earlier_opcode_stops_at_its_real_body(self):
  for i,(_,opcode,body,_) in enumerate(PREFIX_CASES):
   f=TownRequestDispatchFrame(bytes([opcode]));p=f.advance(sample(),dispatcher_setup_returned=True)
   self.assertFalse(p.complete);self.assertEqual(p.status,'earlier_branch_not_bound')
   self.assertEqual(p.next_address,body);self.assertEqual(len(p.opcode_reads),i+1);self.assertIsNone(f.child)

 def test_dispatch_derives_entry_after_four_nonmatches_and_ret12(self):
  f=TownRequestDispatchFrame(b'\x48');p=f.advance(sample(1,False),dispatcher_setup_returned=True)
  self.assertEqual(p.status,'needs_town_observation');self.assertEqual(len(p.opcode_reads),4)
  p=f.advance(JailObservation(normal_returns={'town_request_stop':True}))
  self.assertTrue(p.complete);self.assertEqual(p.source_return_dword,1);self.assertEqual(p.source_ret_pop_bytes,12)
  self.assertIs(f.advance(JailObservation()),p)

 def test_empty_and_later_packets_are_not_falsely_claimed_handled(self):
  p=TownRequestDispatchFrame(b'').advance(JailObservation(),dispatcher_setup_returned=True)
  self.assertEqual(p.status,'unsupported_packet_span');self.assertFalse(p.complete)
  p=TownRequestDispatchFrame(b'\x49').advance(JailObservation(),dispatcher_setup_returned=True)
  self.assertEqual(p.status,'later_branch_not_bound');self.assertFalse(p.complete)
  self.assertTrue(p.child.complete);self.assertIsNone(p.source_return_dword)
