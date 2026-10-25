import unittest
from incoming_tp_dispatch import *

class IncomingTPDispatchTests(unittest.TestCase):
 def observation(self):return TPObservation(values={'first_area_eax':10,'tick_eax':1,'start_low':0,'start_high':0},
    normal_returns={'first_area':True,'tick':True})
 def test_child_cannot_bypass_dispatcher_setup(self):
  f=IncomingTPDispatchFrame(b'\x27\x01\x0a');o=self.observation()
  p=f.advance(replace(o,entry_reached=True))
  self.assertEqual(p.status,'needs_dispatcher_setup');self.assertIsNone(f.child)
  self.assertEqual(p.opcode_reads,())
 def test_all_earlier_matches_stop_at_their_body(self):
  for index,(address,opcode,body,_) in enumerate(PREFIX_CASES):
   f=IncomingTPDispatchFrame(bytes([opcode]));p=f.advance(TPObservation(True),dispatcher_setup_returned=True)
   self.assertFalse(p.complete);self.assertEqual(p.next_address,body)
   self.assertEqual(len(p.opcode_reads),index+1);self.assertIsNone(f.child)
   self.assertIsNone(p.source_return_dword)
 def test_tp_entry_is_derived_after_fourteen_nonmatches(self):
  f=IncomingTPDispatchFrame(b'\x27\x01\x0a');p=f.advance(self.observation(),dispatcher_setup_returned=True)
  self.assertTrue(p.complete);self.assertEqual(len(p.opcode_reads),14)
  self.assertTrue(f.child.observation.entry_reached)
  self.assertEqual(p.source_return_dword,1);self.assertEqual(p.source_ret_pop_bytes,4)
  self.assertEqual(p.next_address,0x4d9233)
  self.assertFalse(p.whole_dispatcher_verified or p.native_execution_verified or p.live_compatibility_verified)
 def test_setup_and_child_prefix_survive_gaps(self):
  f=IncomingTPDispatchFrame(b'\x27\x01\x0a')
  p=f.advance(TPObservation(),dispatcher_setup_returned=True)
  self.assertEqual(p.child.needed,('normal','first_area'))
  p=f.advance(TPObservation(values={'first_area_eax':10},normal_returns={'first_area':True}))
  self.assertEqual(p.child.needed,('normal','tick'))
  p=f.advance(TPObservation(values={'first_area_eax':11,'tick_eax':1,'start_low':0,'start_high':0},normal_returns={'tick':True}))
  self.assertTrue(p.complete);self.assertEqual(f.child.observation.values['first_area_eax'],10)
 def test_unmatched_later_opcode_is_not_claimed_handled(self):
  f=IncomingTPDispatchFrame(b'\x29');p=f.advance(TPObservation(),dispatcher_setup_returned=True)
  self.assertFalse(p.complete);self.assertTrue(p.child.complete)
  self.assertEqual(p.status,'later_branch_not_bound');self.assertEqual(p.next_address,0x4d8a98)
  self.assertIsNone(p.source_return_dword)
 def test_empty_and_truncated_tp_packets_are_not_successes(self):
  p=IncomingTPDispatchFrame(b'').advance(TPObservation(),dispatcher_setup_returned=True)
  self.assertEqual(p.status,'unsupported_packet_span')
  p=IncomingTPDispatchFrame(b'\x27').advance(TPObservation(),dispatcher_setup_returned=True)
  self.assertFalse(p.complete);self.assertEqual(p.child.needed[0],'unsupported')
 def test_final_return_is_cached_without_replaying_calls(self):
  f=IncomingTPDispatchFrame(b'\x27\x01\x0a');p=f.advance(self.observation(),dispatcher_setup_returned=True)
  self.assertIs(f.advance(TPObservation(),dispatcher_setup_returned=False),p)
  self.assertEqual([c[2] for c in p.child.calls],['first_area','tick'])
 def test_input_boundaries(self):
  with self.assertRaises(ValueError):IncomingTPDispatchFrame(bytearray(b'\x27'))
  f=IncomingTPDispatchFrame(b'\x27')
  with self.assertRaises(ValueError):f.advance(TPObservation(),dispatcher_setup_returned=1)
  with self.assertRaises(ValueError):f.advance({})

if __name__=='__main__':unittest.main()
