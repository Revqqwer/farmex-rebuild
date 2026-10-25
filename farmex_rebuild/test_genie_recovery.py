import unittest
from dataclasses import replace
from genie_recovery import GenieRecoveryObservation as O,RecoverySlotSample as S,GenieRecoveryFrame,plan_genie_recovery_scan,TARGET_NAME
from direct_chat_packets import QueueAttempt as Q
from action_queue import QueueState,enqueue

def sample(slot=14,item=0x11223344,owned=False):
 last=41 if slot is None else slot
 samples={i:S(TARGET_NAME if i==slot else b'Other',None if owned else int(i==slot),item if i==slot else None) for i in range(14,last+1)}
 normals={'frame_setup':True,'return_span':True}
 normals.update({prefix+str(i):True for i in range(14,last+1) for prefix in ('setup:','name:','compare:','cleanup:','item:')})
 return O(samples,normals,Q(1,100,True))

class GenieRecoveryTests(unittest.TestCase):
 def test_exact_seven_bytes_item_id_not_slot_and_return_AL_only(self):
  p=GenieRecoveryFrame(0x561ef8).advance(sample())
  self.assertTrue(p.complete);self.assertEqual(p.scan.payload,bytes.fromhex('97010144332211'))
  self.assertEqual(p.scan.selected_slot,14);self.assertEqual(p.push_order,(0x561ef8,))
  self.assertEqual(p.return_low_al,1);self.assertIsNone(p.source_return_eax)
  self.assertEqual((len(p.queue.records[0].payload),p.queue.records[0].delay_dword),(7,0));self.assertFalse(p.Genie_effect_verified)

 def test_all28_slots_required_for_absence_and_slot41_can_match(self):
  p=GenieRecoveryFrame(1).advance(sample(None));self.assertTrue(p.complete)
  self.assertEqual(p.scan.visited_slots,tuple(range(14,42)));self.assertEqual(p.source_return_eax,0);self.assertEqual(p.queue.records,())
  p=GenieRecoveryFrame(1).advance(sample(41));self.assertTrue(p.complete);self.assertEqual(p.scan.selected_slot,41)

 def test_first_match_zero_id_stops_without_trying_later_duplicate(self):
  o=sample(item=0);p=GenieRecoveryFrame(1).advance(replace(o,samples={**o.samples,15:object()}))
  self.assertTrue(p.complete);self.assertEqual(p.scan.visited_slots,(14,));self.assertEqual(p.source_return_eax,0)

 def test_cleanup_required_before_first_match_id_and_later_slots(self):
  o=sample();r=dict(o.normal_returns);r['cleanup:14']=False
  p=plan_genie_recovery_scan(replace(o,normal_returns=r));self.assertFalse(p.complete)
  self.assertEqual(p.needed,('normal','cleanup:14'));self.assertIsNone(p.selected_slot)
  self.assertFalse(any(c[0]=='004634a4' for c in p.calls))

 def test_owned_byte_adapter_is_explicit_exact_and_preserves_NUL(self):
  o=sample(owned=True);p=GenieRecoveryFrame(1,owned_byte_compare=True).advance(o);self.assertTrue(p.complete)
  p=GenieRecoveryFrame(1).advance(o);self.assertFalse(p.complete);self.assertIn('comparison_eax',p.missing)
  for name in (b'spirit of genie',TARGET_NAME+b'\0'):
   p=plan_genie_recovery_scan(replace(o,samples={14:S(name)}),owned_byte_compare=True)
   self.assertFalse(p.complete);self.assertEqual(p.visited_slots,(14,15))

 def test_gate0_returns_AL1_without_record_or_delivery(self):
  o=sample();p=GenieRecoveryFrame(1).advance(replace(o,attempt=Q(0,None,True)))
  self.assertTrue(p.complete);self.assertEqual(p.return_low_al,1);self.assertEqual(p.queue.records,())
  self.assertFalse(p.packet_delivery_verified)

 def test_copied_record_and_gate_survive_normal_gap_without_duplicate(self):
  f=GenieRecoveryFrame(1);o=sample();p=f.advance(replace(o,attempt=Q(1,100,False)))
  self.assertFalse(p.complete);self.assertEqual(len(p.queue.records),1)
  p=f.advance(O(normal_returns={'return_span':True},attempt=Q(0,999,True)))
  self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1);self.assertEqual(p.queue.records[0].created_tick,100)
  self.assertIs(f.advance(O()),p)

 def test_consumed_slot_prefix_kept_while_item_id_arrives_late(self):
  f=GenieRecoveryFrame(1);o=sample();samples=dict(o.samples);samples[14]=replace(samples[14],item_id_eax=None)
  p=f.advance(replace(o,samples=samples));self.assertFalse(p.complete);self.assertEqual(p.scan.selected_slot,14)
  p=f.advance(O({14:S(b'changed',0,0x55667788)},o.normal_returns,o.attempt))
  self.assertTrue(p.complete);self.assertEqual(p.scan.payload,bytes.fromhex('97010188776655'))

 def test_existing_queue_preserved_and_return_span_separate(self):
  q=enqueue(QueueState(),b'prior',5,0,1,1).state;f=GenieRecoveryFrame(1,q);o=sample();r=dict(o.normal_returns);r['return_span']=False
  p=f.advance(replace(o,normal_returns=r));self.assertFalse(p.complete);self.assertEqual(len(p.queue.records),2)
  p=f.advance(O(normal_returns={'return_span':True}))
  self.assertTrue(p.complete);self.assertEqual([r.record_id for r in p.queue.records],[1,2])

 def test_invalid_source_compare_and_unreached_sample_handling(self):
  o=sample();samples=dict(o.samples);samples[14]=replace(samples[14],comparison_eax=2)
  with self.assertRaises(ValueError):plan_genie_recovery_scan(replace(o,samples=samples))
  p=GenieRecoveryFrame(1).advance(replace(o,samples={**o.samples,15:object()}));self.assertTrue(p.complete)
  with self.assertRaises(ValueError):O({42:S(b'Other',0)})

 def test_known_gate_stays_nonzero_while_waiting_for_tick(self):
  f=GenieRecoveryFrame(1);o=sample();p=f.advance(replace(o,attempt=Q(1,None,True)))
  self.assertFalse(p.complete);self.assertEqual(p.queue.records,());self.assertIn('GetTickCount',p.missing)
  p=f.advance(O(normal_returns={'return_span':True},attempt=Q(0,123,True)))
  self.assertTrue(p.complete);self.assertEqual(p.queue.records[0].created_tick,123)

if __name__=='__main__':unittest.main()
