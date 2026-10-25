import unittest
from potion_packets import TEMPLATE,plan_potion_packet,enqueue_potion_intent,plan_alternate_potion
from skill_native_plans import SkillObservation,SOURCE_GLOBALS
from potion_engine import PotionIntent,PotionSettings,PotionSnapshot,MP_SELECTED,potion_decision
from action_queue import QueueState,QueueSample,drain


class PotionPacketTests(unittest.TestCase):
    def intent(self,kind='mp',path='direct',action=0x77a20):
        return PotionIntent(kind,0x172fe9c0,action,path,True)

    def test_exact_source_template_and_packet(self):
        self.assertEqual(TEMPLATE,bytes.fromhex('3103'+'00'*28))
        plan=plan_potion_packet(self.intent(),0x1234)
        self.assertEqual(plan.payload,bytes.fromhex('3103207a0700341200003412')+bytes(18))
        self.assertEqual(len(plan.payload),30);self.assertEqual(plan.queue_delay_ms,0)

    def test_inventory_identifier_is_not_serialized_as_action(self):
        payload=plan_potion_packet(self.intent(),1).payload
        self.assertEqual(int.from_bytes(payload[2:6],'little'),0x77a20)
        self.assertNotEqual(int.from_bytes(payload[2:6],'little'),0x172fe9c0)

    def test_actor_low_word_is_copied_to_both_fields(self):
        for actor in (0,0xffff,0x12345678,0xffffffff):
            payload=plan_potion_packet(self.intent(),actor).payload
            self.assertEqual(payload[6:8],(actor&65535).to_bytes(2,'little'))
            self.assertEqual(payload[10:12],payload[6:8])
            self.assertEqual(payload[8:10],b'\0\0')

    def test_all_direct_potion_kinds_use_same_builder(self):
        for kind in ('hp','mp','special'):
            self.assertEqual(plan_potion_packet(self.intent(kind),1).status,'local_packet_plan')

    def test_missing_fresh_actor_is_not_zero(self):
        self.assertIsNone(plan_potion_packet(self.intent()).payload)
        result=enqueue_potion_intent(QueueState(),self.intent(),None,0)
        self.assertEqual(result.status,'needs_observation');self.assertIsNone(result.state)

    def test_alternate_path_is_not_replaced_by_direct_packet(self):
        result=plan_potion_packet(self.intent(path='alternate'))
        self.assertEqual(result.status,'needs_native_call');self.assertIsNone(result.payload)

    def test_invalid_ids_and_untyped_intents_rejected(self):
        for actor in (True,-1,0x100000000):
            with self.assertRaises(ValueError):plan_potion_packet(self.intent(),actor)
        for action in (True,-1,0x100000000):
            with self.assertRaises(ValueError):plan_potion_packet(self.intent(action=action),1)
        with self.assertRaises(ValueError):plan_potion_packet('mp',1)

    def test_unknown_path_and_kind_are_not_guessed(self):
        with self.assertRaises(ValueError):plan_potion_packet(self.intent(path='unknown'),1)
        with self.assertRaises(ValueError):plan_potion_packet(self.intent(kind='other'),1)

    def test_full_selection_to_queue_drain_is_not_acknowledgement(self):
        candidate=MP_SELECTED[1][0]
        snapshot=PotionSnapshot(20,100,20,100,available_inventory_ids=(candidate.inventory_id,),
            availability_complete=True,action_path='direct',state_3a=True,state_3b=False,state_3c=False)
        decision=potion_decision(PotionSettings(mp_enabled=True,mp_combo_index=1),snapshot)
        queued=enqueue_potion_intent(QueueState(),decision.intents[0],0x1234,1,1000)
        self.assertEqual(queued.status,'locally_enqueued')
        drained=drain(queued.state,{1:QueueSample(1000,1,True)})
        self.assertEqual(drained.state.records,())
        self.assertEqual(drained.events[0].payload[2:6],candidate.action_id.to_bytes(4,'little'))
        self.assertTrue(all(not event.acknowledged for event in drained.events))

    def test_direct_local_return_does_not_guarantee_queue_insertion(self):
        intent=self.intent()
        result=enqueue_potion_intent(QueueState(),intent,1,0)
        self.assertTrue(intent.local_return)
        self.assertEqual(result.status,'not_enqueued');self.assertEqual(result.state.records,())

    def test_alternate_potion_uses_matching_native_action_domain(self):
        intent=self.intent(path='alternate')
        observation=SkillObservation(intent.action_id,0x12345678,SOURCE_GLOBALS['us'],
                          {0x111563c:0x100000,0x100468:0x200000},lookup_return=0x400000)
        result=plan_alternate_potion(intent,observation)
        self.assertEqual(result.calls[0].push_order,(intent.action_id,))
        self.assertEqual(result.calls[1].push_order,(0x400000,0x12345678))
        self.assertIsNone(result.returned_nonzero)

    def test_alternate_binding_rejects_other_action_and_direct_path(self):
        observation=SkillObservation(0x172fe9c0,1)
        with self.assertRaises(ValueError):plan_alternate_potion(self.intent(path='alternate'),observation)
        with self.assertRaises(ValueError):plan_alternate_potion(self.intent(),observation)
