import unittest
from dataclasses import replace
from monster_stone_use import *
from genie_recovery import RecoverySlotSample as S
from direct_chat_packets import QueueAttempt as Q
from action_queue import enqueue
from test_bot_switch import fixture as switch
from test_mining_slot_name import fixture as name_fixture
from upgrade_packets import UpgradeItemObservation

ITEM_RETURNS={k:True for k in ('item_frame_setup','item_copy','item_return_span')}
def inventory(slot=14,item=123):
 end=41 if slot is None else slot
 samples={i:S(TARGET if i==slot else b'Other',int(i==slot),item if i==slot else None) for i in range(14,end+1)}
 normals={prefix+str(i):True for i in range(14,end+1) for prefix in ('setup:','name:','compare:','cleanup:','item:')}
 return GenieRecoveryObservation(samples,normals)
def sample(**changes):
 values=dict(area1_eax=0,area2_eax=0,area3_eax=0,cooldown_tick=1000,cooldown_low=0,cooldown_high=0,post_tick=1234,alarm_byte=1)
 values.update(changes)
 normals={k:True for k in ('worker_setup','area1','area2','area3','cooldown_tick','item_use','completion_message_span','disable_checkbox','bot_stop','alarm_span','completion_tail_cleanup','post_tick','worker_return')}
 return MSUseObservation(values,{**normals,**ITEM_RETURNS},inventory(),Q(1,321,True))

class MonsterStoneUseTests(unittest.TestCase):
 def test_sixbyte_packet_fullID_and_zeroID_are_both_serialized(self):
  for item in (0,0x11223344):
   p=MSItemUseFrame(item).advance(Q(1,100,True),ITEM_RETURNS)
   self.assertTrue(p.complete);self.assertEqual(p.payload,b'\x5f\x06'+item.to_bytes(4,'little'))
   self.assertEqual((len(p.queue.records[0].payload),p.queue.records[0].delay_dword),(6,0))
   self.assertFalse(p.delivery_verified)

 def test_gate_zero_still_requires_normal_returns_without_copying_record(self):
  f=MSItemUseFrame(123);p=f.advance(Q(0,None,False),ITEM_RETURNS)
  self.assertFalse(p.complete);self.assertEqual(p.queue.records,())
  p=f.advance(Q(1,77,True),{'item_return_span':True})
  self.assertTrue(p.complete);self.assertEqual(p.queue.records,())

 def test_known_gate_and_copied_record_retained_across_missing_tick_and_return(self):
  prior=enqueue(QueueState(),b'old',3,0,1,1).state
  f=MSItemUseFrame(1,prior);p=f.advance(Q(1,None,True),ITEM_RETURNS);self.assertFalse(p.complete)
  p=f.advance(Q(0,77,False),ITEM_RETURNS);self.assertFalse(p.complete);self.assertEqual(len(p.queue.records),2)
  p=f.advance(Q(0,999,True),ITEM_RETURNS);self.assertTrue(p.complete)
  self.assertEqual([r.created_tick for r in p.queue.records],[1,77])

 def test_three_distinct_area_samples_short_circuit_before_clock_or_inventory(self):
  o=MSUseObservation({'area1_eax':0x10051,'area2_eax':0x52},{'worker_setup':True,'area1':True,'area2':True,'worker_return':True},GenieRecoveryObservation({14:object()}))
  p=MSUseFrame().advance(o);self.assertTrue(p.complete);self.assertEqual(p.status,'excluded_area')
  self.assertIsNone(p.scan);self.assertEqual(p.stores,());self.assertFalse(any(c[2]=='area3' for c in p.calls))

 def test_cooldown_equality_is_inclusive_and_QWORD_wrap_is_signed(self):
  p=MSUseFrame().advance(sample(cooldown_tick=999));self.assertTrue(p.complete);self.assertEqual(p.status,'cooldown_wait')
  p=MSUseFrame().advance(sample());self.assertTrue(p.complete);self.assertEqual(p.status,'item_helper_returned')
  p=MSUseFrame().advance(sample(cooldown_tick=0x100,cooldown_low=0xffffff00))
  self.assertTrue(p.complete);self.assertEqual(p.status,'cooldown_wait');self.assertEqual(p.stores,())

 def test_first_match_zeroID_stops_before_later_invalid_slot_and_no_exhaustion(self):
  o=sample();s=inventory(item=0);s=replace(s,samples={**s.samples,15:object()})
  p=MSUseFrame().advance(replace(o,scan=s));self.assertTrue(p.complete)
  self.assertEqual(p.scan.visited_slots,(14,));self.assertEqual(p.item.payload,bytes.fromhex('5f0600000000'))
  self.assertEqual(p.ui_updates,());self.assertEqual(p.stores,((0x56fb40,4,1234),(0x56fb44,4,0)))

 def test_absence_requires_all28_slots_and_exhaustion_order_is_preserved(self):
  o=replace(sample(),scan=inventory(None));f=MSUseFrame();r=dict(o.normal_returns);r['bot_stop']=False
  p=f.advance(replace(o,normal_returns=r));self.assertFalse(p.complete)
  self.assertEqual(p.scan.visited_slots,tuple(range(14,42)));self.assertEqual(p.ui_updates,((MS_ENABLE_INPUT,False),))
  self.assertEqual(p.stores,());self.assertFalse(any(c[2]=='alarm_span' for c in p.calls))
  p=f.advance(o);self.assertTrue(p.complete);self.assertEqual(p.status,'inventory_exhausted')
  labels=[c[2] for c in p.calls]
  self.assertLess(labels.index('completion_message_span'),labels.index('disable_checkbox'))
  self.assertLess(labels.index('bot_stop'),labels.index('alarm_span'))
  self.assertLess(labels.index('completion_tail_cleanup'),labels.index('post_tick'))
  self.assertFalse(any(s[0]==0x561f5c for s in p.stores)) #Setter is opaque, no invented callback store.

 def test_item_record_survives_parent_clock_gap_without_duplicate(self):
  f=MSUseFrame();o=sample();r=dict(o.normal_returns);r['post_tick']=False
  p=f.advance(replace(o,normal_returns=r));self.assertFalse(p.complete);self.assertEqual(len(p.item.queue.records),1)
  p=f.advance(MSUseObservation({'post_tick':888},{'post_tick':True,'worker_return':True}))
  self.assertTrue(p.complete);self.assertEqual(len(p.item.queue.records),1);self.assertEqual(p.stores[0],(0x56fb40,4,888))
  self.assertIs(f.advance(MSUseObservation()),p)

 def test_generated_stop_child_blocks_outer_fallback_and_resumes(self):
  f=MSUseFrame();o=replace(sample(),scan=inventory(None),stop_inputs=BotSwitchObservation())
  p=f.advance(o);self.assertFalse(p.complete);self.assertEqual(p.needed,('stop','bot_stop'))
  p=f.advance(replace(o,stop_inputs=switch()));self.assertTrue(p.complete)
  self.assertEqual(p.stop.push_order,(0,0x561f34));self.assertFalse(p.MonsterStone_effect_verified)

 def test_owned_exact_comparison_uses_MonsterStone_literal_without_extra_scan_setup(self):
  o=sample();s=o.scan;s=replace(s,samples={14:S(TARGET,None,123)})
  p=MSUseFrame(owned_byte_compare=True).advance(replace(o,scan=s));self.assertTrue(p.complete)
  self.assertFalse(any(c[2]=='frame_setup' for c in p.scan.calls))
  s=replace(s,samples={14:S(b'monster stone',None,123)})
  p=MSUseFrame(owned_byte_compare=True).advance(replace(o,scan=s));self.assertFalse(p.complete)
  self.assertEqual(p.scan.visited_slots,(14,15))

 def test_scan_cleanup_gap_does_not_consume_ID_or_queue_and_cached_prefix_resumes(self):
  f=MSUseFrame();o=sample();s=o.scan;r=dict(s.normal_returns);r['cleanup:14']=False
  p=f.advance(replace(o,scan=replace(s,normal_returns=r)));self.assertFalse(p.complete)
  self.assertIsNone(p.item);self.assertEqual(f.queue.records,())
  tail=GenieRecoveryObservation({14:S(b'changed',0,456)},{'cleanup:14':True,'item:14':True})
  p=f.advance(replace(o,scan=tail));self.assertTrue(p.complete)
  self.assertEqual(p.item.payload,b'\x5f\x06'+(456).to_bytes(4,'little'))

 def test_typed_name_and_fresh_ID_readers_bind_to_actual_slot(self):
  inputs=UpgradeItemObservation(0x1000,4,8,0x2000,0x3000,0x4000,0x5000,0x6000,1000,1002)
  o=sample();s=replace(o.scan,samples={14:S(comparison_eax=1,name_inputs=name_fixture(TARGET),item_inputs=inputs)})
  p=MSUseFrame().advance(replace(o,scan=s));self.assertTrue(p.complete)
  self.assertEqual(p.item.payload,bytes.fromhex('5f06ea030000'));self.assertEqual(len(p.scan.getter_executions),2)

if __name__=='__main__':unittest.main()
