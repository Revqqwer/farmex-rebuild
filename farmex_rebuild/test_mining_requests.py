import unittest
from mining_requests import *
from mining_engine import OreSlotState,OreSlotSnapshot,process_ore_slot

class OreRequestTests(unittest.TestCase):
    def test_gold_name_selects_script_one(self):
        self.assertEqual(plan_ore_request_name(GOLD_NAME).packets[1][0][1],1)

    def test_ore_name_selects_script_zero(self):
        self.assertEqual(plan_ore_request_name(ORE_NAME).packets[1][0][1],0)

    def test_names_require_full_case_sensitive_byte_match(self):
        for name in (b'',GOLD_NAME.lower(),ORE_NAME+b' ',b'x'+ORE_NAME,ORE_NAME+b'\0',b'\xff'):
            with self.subTest(name=name):
                plan=plan_ore_request_name(name)
                self.assertEqual(plan.status,'source_early_return')
                self.assertEqual(plan.packets,())

    def test_missing_name_is_not_empty(self):
        self.assertFalse(plan_ore_request_name(None).complete)
        self.assertTrue(plan_ore_request_name(b'').complete)
        with self.assertRaises(ValueError):plan_ore_request_name('Mysterious Ore')

    def test_actual_request_name_is_independent_of_earlier_gate(self):
        child=process_ore_slot(OreSlotState(),OreSlotSnapshot(True,None,True),2000,1,False)
        self.assertEqual(plan_slot_request_name(child).status,'needs_fresh_ansi_name')
        self.assertEqual(plan_slot_request_name(child,b'changed item').status,'source_early_return')
        self.assertEqual(plan_slot_request_name(child,ORE_NAME).status,'locally_serialized')

    def test_child_binding_demands_fresh_comparisons(self):
        child=process_ore_slot(OreSlotState(),OreSlotSnapshot(True,None,True),2000,1,False)
        self.assertEqual(plan_slot_request(child).missing,'first_505138')
        self.assertEqual(plan_slot_request(child,OreRequestObservation(False,None,False)).status,'locally_serialized')

    def test_child_cadence_does_not_generate_request(self):
        child=process_ore_slot(OreSlotState(),OreSlotSnapshot(),500,1,False)
        self.assertEqual(plan_slot_request(child).status,'request_not_reached')

    def test_short_circuit_requires_no_second_result(self):
        plan=plan_ore_request(OreRequestObservation(False,None,False))
        self.assertTrue(plan.complete)
        self.assertEqual(plan.packets,((b'\x64\x07TN\0\0\0\0',300),(b'U\0\x1031511_Pitman.lua',600)))

    def test_early_return_skips_gold_and_queue(self):
        plan=plan_ore_request(OreRequestObservation(True,True))
        self.assertEqual(plan.status,'source_early_return')
        queued=enqueue_ore_request(QueueState(),plan,())
        self.assertTrue(queued.complete)
        self.assertEqual(queued.completed_calls,0)

    def test_second_false_reaches_gold(self):
        plan=plan_ore_request(OreRequestObservation(True,False,True))
        self.assertEqual(plan.packets[1][0],b'U\x01\x1031511_Pitman.lua')
        self.assertEqual(len(plan.packets[1][0]),19)
        self.assertFalse(plan.context_preparation_verified)
        self.assertFalse(plan.server_acknowledged)

    def test_missing_comparisons_are_ordered(self):
        for obs,missing in ((OreRequestObservation(),'first_505138'),
                            (OreRequestObservation(True),'second_505138'),
                            (OreRequestObservation(False),'gold_505118')):
            plan=plan_ore_request(obs)
            self.assertFalse(plan.complete)
            self.assertEqual(plan.missing,missing)
            self.assertEqual(plan.packets,())

    def test_fresh_queue_samples_not_shared(self):
        plan=plan_ore_request(OreRequestObservation(False,None,False))
        result=enqueue_ore_request(QueueState(),plan,(QueueSample(100,1),QueueSample(108,1)))
        self.assertTrue(result.complete)
        self.assertEqual([(r.created_tick,r.delay_dword) for r in result.state.records],[(100,300),(108,600)])

    def test_disconnected_first_does_not_skip_second_call(self):
        plan=plan_ore_request(OreRequestObservation(False,None,True))
        result=enqueue_ore_request(QueueState(),plan,(QueueSample(None,0),QueueSample(108,1)))
        self.assertTrue(result.complete)
        self.assertEqual(len(result.state.records),1)
        self.assertEqual(result.state.records[0].delay_dword,600)

    def test_missing_second_keeps_explicit_prefix(self):
        plan=plan_ore_request(OreRequestObservation(False,None,False))
        result=enqueue_ore_request(QueueState(),plan,(QueueSample(100,1),))
        self.assertFalse(result.complete)
        self.assertEqual(result.completed_calls,1)
        self.assertEqual(len(result.state.records),1)

    def test_no_integer_boolean_coercion(self):
        with self.assertRaises(ValueError):OreRequestObservation(1)

if __name__=='__main__':unittest.main()
