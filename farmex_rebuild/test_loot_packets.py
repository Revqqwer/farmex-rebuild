import unittest
from operation_engine import OperationIntent,LootDecision,LootRecord,LootSnapshot,LootSettings,loot_step
from action_queue import QueueState,QueueSample,drain
from loot_packets import plan_loot_packet,plan_loot_intents,enqueue_loot_intent,TAKE_TEMPLATE

class LootPacketTests(unittest.TestCase):
    def test_open_exact_opcode_dword_and_length(self):
        p=plan_loot_packet(OperationIntent('loot_open','local'),0x12345678)
        self.assertEqual(p.payload,bytes.fromhex('2478563412'))
        self.assertEqual((p.source_helper,p.queue_delay_ms),('00414938',0))

    def test_take_exact_template_and_offsets(self):
        p=plan_loot_packet(OperationIntent('loot_item','local',item_id=0xa1b2c3d4,slot=7),0x12345678)
        self.assertEqual(p.payload,bytes.fromhex('2678563412d4c3b2a10700'))
        self.assertEqual((p.source_helper,p.queue_delay_ms),('00414984',0))
        self.assertEqual(TAKE_TEMPLATE,bytes.fromhex('2600000000000000000000'))
        self.assertIs(type(p.payload),bytes)

    def test_raw_helper_slot_copies_low_byte_without_guessing_slot_guard(self):
        for slot in (0,7,8,255,256,0xffffffff):
            p=plan_loot_packet(OperationIntent('loot_item',item_id=0,slot=slot),0)
            self.assertEqual(p.payload[9:],bytes((slot&255,0)))

    def test_dword_zero_and_max_remain_raw(self):
        self.assertEqual(plan_loot_packet(OperationIntent('loot_open'),0).payload,b'\x24'+b'\0'*4)
        self.assertEqual(plan_loot_packet(OperationIntent('loot_item',item_id=0xffffffff,slot=0xffffffff),0xffffffff).payload,
            b'\x26'+b'\xff'*9+b'\0')

    def test_reference_is_never_interpreted_as_bundle_id(self):
        p=plan_loot_packet(OperationIntent('loot_open','12345'))
        self.assertIsNone(p.payload);self.assertEqual(p.status,'needs_bundle_id')

    def test_invalid_raw_values_and_other_operations_rejected(self):
        for bad in (True,-1,0x100000000,'1'):
            with self.assertRaises(ValueError):plan_loot_packet(OperationIntent('loot_open'),bad)
        for intent in (OperationIntent('loot_item',item_id=None,slot=0),
                       OperationIntent('loot_item',item_id=1,slot=0x100000000),OperationIntent('repair')):
            with self.assertRaises(ValueError):plan_loot_packet(intent,1)

    def test_lifecycle_open_then_all_slots_preserves_order_and_done(self):
        records=(LootRecord('open',0),LootRecord('item',0,item_phase=True,
            item_ids=(10,20,0,40,0,0,0,80),slot_done=(False,True,False,False,False,False,False,False)))
        d=loot_step(LootSettings(),LootSnapshot(1000,records,open_state_allowed=True))
        b=plan_loot_intents(d,{'open':0x10,'item':0x20})
        self.assertTrue(b.complete);self.assertFalse(b.independently_verified)
        self.assertEqual([p.payload[0] for p in b.plans],[0x24,0x26,0x26,0x26])
        self.assertEqual([p.payload[9] for p in b.plans[1:]],[0,3,7])
        self.assertEqual([int.from_bytes(p.payload[5:9],'little') for p in b.plans[1:]],[10,40,80])

    def test_open_expired_record_can_be_serialized_from_external_observation(self):
        d=loot_step(LootSettings(),LootSnapshot(17000,(LootRecord('expired',0),),open_state_allowed=True))
        self.assertEqual(d.records,())
        self.assertEqual(plan_loot_intents(d,{'expired':1}).plans[0].payload,b'\x24\x01\0\0\0')

    def test_missing_later_id_retains_ordered_prefix_only(self):
        d=LootDecision('needs_clock_observation',(),(OperationIntent('loot_open','a'),OperationIntent('loot_open','b')))
        p=plan_loot_intents(d,{'a':1})
        self.assertFalse(p.complete);self.assertEqual(len(p.plans),1)
        self.assertEqual(p.lifecycle_status,'needs_clock_observation')
        self.assertTrue(p.missing.startswith('b:'))
        # Serialization completion is deliberately independent of callback return.
        self.assertTrue(plan_loot_intents(d,{'a':1,'b':2}).complete)

    def test_queue_gate_missing_tick_and_copy_are_separate_from_send(self):
        state=QueueState();intent=OperationIntent('loot_item','r',item_id=10,slot=0)
        self.assertEqual(enqueue_loot_intent(state,intent,1,0).state,state)
        self.assertEqual(enqueue_loot_intent(state,intent,1,1).status,'needs_observation')
        q=enqueue_loot_intent(state,intent,1,1,100)
        self.assertEqual(q.status,'locally_enqueued');self.assertEqual(q.state.records[0].delay_dword,0)
        self.assertTrue(all(not e.acknowledged for e in q.events))
        pending=drain(q.state,{1:QueueSample(100,1)})
        self.assertEqual(pending.status,'needs_sender_return')
        self.assertIsNone(pending.state)
        self.assertEqual(drain(q.state,{1:QueueSample(100,0)}).state.records,())

if __name__=='__main__':unittest.main()
