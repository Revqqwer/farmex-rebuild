import unittest
from dataclasses import replace
from loot_records import plan_loot_creation,materialize_created_record,decode_loot_record,PADDING_OFFSETS
from loot_replies import replay_loot_reply
from loot_packets import plan_loot_intents
from operation_engine import LootSettings,LootSnapshot,loot_step

PACKET=bytes.fromhex('23785634124433221101')

class LootRecordTests(unittest.TestCase):
    def plan(self,**kw):return plan_loot_creation(PACKET,1,lookup_result=kw.get('lookup_result',0xaabbccdd),created_tick=kw.get('created_tick',123))
    def test_creation_order_is_bundle_source_lookup_not_packet_order(self):
        p=self.plan()
        self.assertEqual((p.bundle_id,p.source_id,p.lookup_result,p.created_tick),(0x11223344,0x12345678,0xaabbccdd,123))
        raw=materialize_created_record(p,b'xyz')
        self.assertEqual(raw[:12],bytes.fromhex('4433221178563412ddccbbaa'))
        self.assertEqual(raw[0x48:],bytes.fromhex('7b0000000000000000000000'))
        self.assertFalse(p.independently_verified)
    def test_exact_zero_initialization_except_known_fields_and_unknown_padding(self):
        raw=materialize_created_record(self.plan(),bytes.fromhex('aabbcc'))
        self.assertEqual(len(raw),84);self.assertEqual(raw[12:0x45],b'\0'*57)
        self.assertEqual(PADDING_OFFSETS,(69,70,71));self.assertEqual(raw[0x45:0x48],bytes.fromhex('aabbcc'))
    def test_gate_order_does_not_require_header_or_lookup_when_disabled(self):
        self.assertEqual(plan_loot_creation(b'\x23',0).status,'dispatch_disabled')
        self.assertEqual(plan_loot_creation(b'\x24',1).status,'not_creation_opcode')
        self.assertEqual(plan_loot_creation(PACKET[:-1]+b'\0',1).status,'creation_guard_zero')
        self.assertEqual(plan_loot_creation(b'\x23',1).missing,'creation guard byte9')
    def test_lookup_before_clock_and_zero_lookup_is_not_filtered(self):
        p=plan_loot_creation(PACKET,1,created_tick=123)
        self.assertEqual(p.status,'needs_lookup_observation')
        self.assertEqual(plan_loot_creation(PACKET,1,lookup_result=0).status,'needs_clock_observation')
        self.assertEqual(self.plan(lookup_result=0).status,'local_append_plan')
        raw=materialize_created_record(self.plan(lookup_result=0),b'\0'*3)
        self.assertEqual(decode_loot_record(raw,'r',distance=25).lookup_result,0)
    def test_raw_dword_limits_and_nonzero_guard_byte(self):
        p=plan_loot_creation(b'\x23'+b'\xff'*9,255,lookup_result=0xffffffff,created_tick=0xffffffff)
        self.assertEqual(p.status,'local_append_plan')
        self.assertEqual(p.bundle_id,0xffffffff)
        for value in (True,-1,0x100000000):
            with self.assertRaises(ValueError):self.plan(lookup_result=value)
            with self.assertRaises(ValueError):self.plan(created_tick=value)
    def test_materialization_never_guesses_uninitialized_padding(self):
        for padding in (None,b'',b'xx',bytearray(3)):
            with self.assertRaises(ValueError):materialize_created_record(self.plan(),padding)
        with self.assertRaises(ValueError):materialize_created_record(plan_loot_creation(b'\x23',0),b'xxx')
    def test_decode_all_offsets_and_raw_nonboolean_bytes(self):
        raw=bytearray(materialize_created_record(self.plan(),b'abc'))
        for i in range(8):raw[12+4*i:16+4*i]=(100+i).to_bytes(4,'little')
        raw[0x2c:0x30]=(7).to_bytes(4,'little');raw[0x30:0x35]=bytes((2,3,0,4,5))
        raw[0x35:0x3d]=bytes(range(8));raw[0x3d:0x45]=bytes((0,2,0,255,0,0,1,0))
        raw[0x4c:0x50]=(0xffffffff).to_bytes(4,'little');raw[0x50:]=(19).to_bytes(4,'little')
        p=decode_loot_record(bytes(raw),'local',distance=15.75);r=p.model
        self.assertEqual(p.nonzero_count,7) # Stored source count is not recomputed.
        self.assertEqual(r.item_ids,tuple(range(100,108)));self.assertEqual(r.disposed_flags,(True,False,True))
        self.assertEqual((r.list_state.classified,r.list_state.discarded),(4,5))
        self.assertEqual(r.list_state.done[3],255);self.assertTrue(r.slot_done[3])
        self.assertEqual((r.open_attempt_ms,r.item_attempt_ms,r.distance),(0xffffffff,19,15.75))
        self.assertEqual(p.raw[0x45:0x48],b'abc');self.assertFalse(p.independently_verified)
    def test_decode_requires_complete_capture_and_explicit_distance(self):
        raw=materialize_created_record(self.plan(),b'abc')
        for bad in (raw[:-1],raw+b'0',bytearray(raw)):
            with self.assertRaises(ValueError):decode_loot_record(bad,'r',distance=0)
        with self.assertRaises(TypeError):decode_loot_record(raw,'r')
        with self.assertRaises(ValueError):decode_loot_record(raw,'r',distance=float('nan'))
    def test_duplicate_bundle_creation_is_not_deduplicated_by_planner(self):
        p=self.plan();raw=materialize_created_record(p,b'abc')
        a=decode_loot_record(raw,'first',distance=0);b=decode_loot_record(raw,'second',distance=0)
        self.assertEqual(a.bundle_id,b.bundle_id);self.assertNotEqual(a.model.reference,b.model.reference)
    def test_creation_capture_open_reply_and_take_plan_compose(self):
        p=self.plan(created_tick=0);raw=materialize_created_record(p,b'abc')
        row=decode_loot_record(raw,'created',distance=5)
        bindings={'created':row.bundle_id}
        d=loot_step(LootSettings(),LootSnapshot(1000,(row.model,),open_state_allowed=True))
        self.assertEqual(plan_loot_intents(d,bindings).plans[0].payload,bytes.fromhex('2444332211'))
        response=b'\x24'+p.bundle_id.to_bytes(4,'little')+b'\1'+(10).to_bytes(4,'little')+b'\1\0'+b'\0'*42
        applied=replay_loot_reply(d.records,bindings,response,len(response),1)
        self.assertTrue(applied.complete)
        d=loot_step(LootSettings(),LootSnapshot(1000,applied.records))
        self.assertEqual(plan_loot_intents(d,bindings).plans[0].payload,bytes.fromhex('26443322110a0000000000'))

if __name__=='__main__':unittest.main()
