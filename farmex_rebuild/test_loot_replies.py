import unittest
from dataclasses import replace
from operation_engine import LootRecord,LootSettings,LootSnapshot,loot_step,OperationIntent
from loot_replies import replay_loot_reply
from loot_packets import plan_loot_intents,plan_loot_packet
from loot_classifier import LootListState

def opened(bundle,items,quantities=(1,)*8,flag=0):
    return b'\x24'+bundle.to_bytes(4,'little')+bytes((flag,))+b''.join(
        item.to_bytes(4,'little')+(q&0xffff).to_bytes(2,'little') for item,q in zip(items,quantities))
def taken(status,bundle,item,skip=99):
    return b'\x26'+bytes((status,))+bundle.to_bytes(4,'little')+(
        bytes((skip,)) if status in (1,2) else b'')+item.to_bytes(4,'little')

class LootReplyTests(unittest.TestCase):
    def setUp(self):
        self.r=LootRecord('local',0);self.ids={'local':0x11223344}
    def call(self,data,length=None,records=None,enabled=1,ids=None):
        return replay_loot_reply((self.r,) if records is None else records,self.ids if ids is None else ids,
            data,len(data) if length is None else length,enabled)
    def test_open_loads_eight_pairs_count_and_signed_quantities(self):
        ids=(10,0,30,0,50,0,70,80)
        p=self.call(opened(0x11223344,ids,(0,1,32767,-32768,-1,2,3,4),255))
        self.assertTrue(p.complete);self.assertEqual(p.records[0].item_ids,ids)
        self.assertTrue(p.records[0].item_phase);self.assertEqual(p.nonzero_count,5)
        self.assertEqual(p.quantities,(0,1,32767,-32768,-1,2,3,4))
    def test_open_empty_sets_disposal_then_lifecycle_removes(self):
        p=self.call(opened(0x11223344,(0,)*8))
        self.assertEqual(p.nonzero_count,0);self.assertEqual(p.records[0].disposed_flags,(False,True,False))
        d=loot_step(LootSettings(),LootSnapshot(1000,p.records))
        self.assertEqual(d.records,());self.assertEqual(d.reason,'disposal_flag')
    def test_open_signed_short_length_marks_without_resetting_items(self):
        r=replace(self.r,item_ids=(10,)*8)
        for length in (0,5,6,0x80000000,0xffffffff):
            p=self.call(b'\x24\x44\x33\x22\x11',length,records=(r,))
            self.assertEqual(p.status,'open_short_marked');self.assertEqual(p.records[0].item_ids,(10,)*8)
    def test_declared_length7_does_not_bound_unchecked_source_reads(self):
        p=self.call(opened(0x11223344,(10,)*8),7)
        self.assertTrue(p.complete);self.assertEqual(p.nonzero_count,8)
        short=self.call(opened(0x11223344,(10,)*8)[:10],7)
        self.assertFalse(short.complete);self.assertEqual(short.records[0].item_ids[0],10)
        self.assertFalse(short.records[0].item_phase);self.assertEqual(short.quantities,())
        self.assertEqual(short.missing,'captured bytes[10:12]')
    def test_open_preserves_cached_mask_done_timers_and_existing_disposal(self):
        r=replace(self.r,list_state=LootListState(classified=1),slot_done=(True,)*8,
            disposed_flags=(True,True,False),open_attempt_ms=17,item_attempt_ms=23)
        p=self.call(opened(0x11223344,(20,)*8),records=(r,))
        actual=p.records[0]
        self.assertEqual(actual,replace(r,item_phase=True,item_ids=(20,)*8))
    def test_take_status1_2_skip_byte_status3_no_skip(self):
        r=replace(self.r,item_ids=(10,20,0,0,0,0,0,0))
        for status in (1,2,3):
            p=self.call(taken(status,0x11223344,20),records=(r,))
            self.assertEqual(p.source_marked_slot,1)
            self.assertEqual(p.records[0].slot_done,(False,True,False,False,False,False,False,False))
            self.assertFalse(p.independently_verified)
    def test_take_length_exact2_skips_all_handler_reads(self):
        p=self.call(b'\x26',2)
        self.assertTrue(p.complete);self.assertEqual(p.status,'take_length2_ignored')
        self.assertFalse(self.call(b'\x26',1).complete)
    def test_invalid_take_status_still_requires_item_capture_before_rejection(self):
        for status in (0,4,255):
            p=self.call(taken(status,0x11223344,10))
            self.assertEqual(p.status,'take_status_ignored');self.assertEqual(p.records,(self.r,))
            self.assertFalse(self.call(taken(status,0x11223344,10)[:6]).complete)
    def test_duplicate_item_marks_first_match_even_if_already_done(self):
        r=replace(self.r,item_ids=(10,10,0,0,0,0,0,0),slot_done=(True,False,False,False,False,False,False,False))
        p=self.call(taken(3,0x11223344,10),records=(r,))
        self.assertEqual(p.source_marked_slot,0);self.assertEqual(p.records,(r,))
    def test_zero_item_can_match_first_empty_slot(self):
        p=self.call(taken(3,0x11223344,0))
        self.assertEqual(p.source_marked_slot,0)
    def test_bundle_first_match_and_no_matching_item(self):
        other=replace(self.r,reference='other',item_ids=(10,)*8)
        p=self.call(taken(3,0x11223344,10),records=(self.r,other),ids={'local':0x11223344,'other':0x11223344})
        self.assertEqual(p.status,'item_not_found');self.assertEqual(p.records,(self.r,other))
        self.assertEqual(self.call(taken(3,0xffffffff,0)).status,'bundle_not_found')
    def test_explicit_dispatch_disabled_and_missing_identity(self):
        self.assertEqual(self.call(b'\x24',enabled=0).status,'dispatch_disabled')
        self.assertEqual(self.call(b'\x25').status,'not_loot_opcode')
        self.assertFalse(self.call(opened(0x11223344,(0,)*8),ids={}).complete)
    def test_open_plan_reply_take_plan_reply_and_retry_compose(self):
        d=loot_step(LootSettings(),LootSnapshot(1000,(self.r,),open_state_allowed=True))
        self.assertEqual(plan_loot_intents(d,self.ids).plans[0].payload[0],0x24)
        reply=self.call(opened(0x11223344,(10,20,0,0,0,0,0,0)))
        d=loot_step(LootSettings(),LootSnapshot(1000,reply.records))
        packets=plan_loot_intents(d,self.ids)
        self.assertEqual(len(packets.plans),2)
        self.assertFalse(any(d.records[0].slot_done))
        done=self.call(taken(1,0x11223344,10),records=d.records)
        d=loot_step(LootSettings(),LootSnapshot(2000,done.records))
        self.assertEqual([i.item_id for i in d.intents],[20])
    def test_outbound_take_buffer_is_not_an_inbound_reply(self):
        packet=plan_loot_packet(OperationIntent('loot_item','local',item_id=10,slot=0),0x11223344).payload
        p=self.call(packet)
        self.assertEqual(p.status,'take_status_ignored');self.assertFalse(any(p.records[0].slot_done))

if __name__=='__main__':unittest.main()
