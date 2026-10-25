import unittest
from dataclasses import replace
from merchant_open import BuyOpenState as State,BuyOpenObservation as Obs,plan_buy_open,compose_buy_open,PREFIX
from merchant_preparation import BuyPreparedRecord as Row
from merchant_setup import MerchantInventoryObservation as Inventory
from action_queue import QueueState,QueueSample

class BuyOpenTests(unittest.TestCase):
    def obs(self,**changes):
        fields=dict(initial_global_base=0x1000,free_count=28,coins_dword=0xffffffff,
          records=(Row(1,2,3),),stable_records=True,
          fresh_global_bases={i:0x2000+i*4 for i in range(12)},
          zero_helper_returns={i:True for i in range(12)},memset_returns={i:True for i in range(12)})
        fields.update(changes);return Obs(**fields)
    def test_byte_widths_and_two_packets(self):
        row=Row(0x11223344,0x10002,0x155667788)
        p=plan_buy_open(State(),self.obs(records=(row,)))
        self.assertTrue(p.complete);self.assertEqual(PREFIX,b'\x68\x21')
        self.assertEqual(p.packets,((b'\x68\x21',0),(bytes.fromhex('68220144332211020088776655'),1000)))
        self.assertEqual(p.state.accumulated_qword,(row.quantity_dword*(row.price_qword&0xffffffff))&0xffffffff)
    def test_skipped_expensive_rows_and_cursor_follows_selected_not_list_index(self):
        p=plan_buy_open(State(),self.obs(coins_dword=10,records=(Row(9,1,11),Row(1,1,6),Row(2,1,5),Row(3,1,4))))
        self.assertEqual(p.selected_indices,(1,3));self.assertEqual(p.remaining_coins,0)
        self.assertEqual(p.write_plans[1],('memset_plan',0x1000,b'\0'*35))
        self.assertEqual(p.write_plans[3],('memset_plan',0x1028,b'\0'*35))
        self.assertEqual(p.write_plans[2][1],0x2004-0x28)
    def test_cap12_and_no_extra_row_access(self):
        p=plan_buy_open(State(),self.obs(records=(Row(1,0,0),)*12+(None,)))
        self.assertTrue(p.complete);self.assertEqual(len(p.selected_indices),12)
        self.assertEqual(len(p.packets[1][0]),123);self.assertEqual(p.packets[1][0][2],12)
        self.assertEqual(len(p.write_plans),24)
    def test_no_affordable_rows_has_no_writes_or_packets(self):
        p=plan_buy_open(State(9),self.obs(coins_dword=0,fresh_global_bases={},records=(Row(1,1,1),)))
        self.assertTrue(p.complete);self.assertEqual(p.packets,());self.assertEqual(p.write_plans,())
        self.assertEqual(p.state,State(9))
    def test_fresh_count_precedes_cap_and_free_tests(self):
        p=plan_buy_open(State(),self.obs(free_count=1,stable_records=False,vector_counts=(1,)))
        self.assertFalse(p.complete);self.assertIn('count1',p.missing)
        self.assertEqual(p.selected_indices,(0,));self.assertEqual(p.state,State())
        self.assertEqual(p.prospective_state,State(6))
        p=plan_buy_open(State(),self.obs(free_count=0,stable_records=False,vector_counts=()))
        self.assertFalse(p.complete);self.assertIn('count0',p.missing)
    def test_write_helper_and_memset_gaps_precede_queue(self):
        o=self.obs(zero_helper_returns={})
        p=plan_buy_open(State(),o)
        self.assertFalse(p.complete);self.assertEqual(len(p.write_plans),1)
        self.assertEqual(p.partial_payload[2],0)
        self.assertNotIn(('004c7710',0x561ef8,2,0),p.calls)
        p=plan_buy_open(State(),replace(o,zero_helper_returns={0:True},memset_returns={}))
        self.assertFalse(p.complete);self.assertEqual(len(p.write_plans),2)
    def test_accumulator_and_address_wrap(self):
        p=plan_buy_open(State((1<<64)-2),self.obs(initial_global_base=0xfffffff0,
            fresh_global_bases={0:0,1:0},records=(Row(1,1,3),Row(2,0,0))))
        self.assertEqual(p.state,State(1));self.assertEqual(p.write_plans[0][1],0xffffffd8)
        self.assertEqual(p.write_plans[3][1],0x18)
    def test_bound_inventory_gap_and_explicit_count_conflict(self):
        p=plan_buy_open(State(),self.obs(free_count=None,inventory_inputs=Inventory((0,)*28)))
        self.assertTrue(p.complete);self.assertEqual(p.inventory_plan.free_count,28)
        p=plan_buy_open(State(),self.obs(free_count=None,inventory_inputs=Inventory((0,))))
        self.assertFalse(p.complete);self.assertEqual(p.calls,(('0042070c',),))
        with self.assertRaises(ValueError):plan_buy_open(State(),self.obs(inventory_inputs=Inventory((0,)*28)))
    def test_two_enqueue_gates_ticks_and_partial_queue(self):
        state=State();queue=QueueState();obs=self.obs()
        p=compose_buy_open(state,obs,queue,{0:QueueSample(10,1)})
        self.assertFalse(p.complete);self.assertEqual(p.queue,queue);self.assertEqual(p.state,state)
        self.assertEqual(len(p.prospective_queue.records),1)
        p=compose_buy_open(state,obs,queue,{0:QueueSample(None,0),1:QueueSample(11,1)})
        self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1)
        self.assertEqual((p.queue.records[0].created_tick,p.queue.records[0].delay_dword),(11,1000))
        p=compose_buy_open(state,obs,queue,{0:QueueSample(10,1),1:QueueSample(None,1)})
        self.assertFalse(p.complete);self.assertEqual(p.queue,queue)
        p=compose_buy_open(state,obs,queue,{0:QueueSample(10,1),1:QueueSample(11,1)})
        self.assertEqual([(r.record_id,r.delay_dword,r.created_tick) for r in p.queue.records],[(1,0,10),(2,1000,11)])
    def test_empty_selection_needs_no_enqueue_samples(self):
        p=compose_buy_open(State(),self.obs(records=()),QueueState(),{})
        self.assertTrue(p.complete);self.assertEqual(p.queue.records,())
        with self.assertRaises(ValueError):self.obs(stable_records=True,vector_counts=(0,))

if __name__=='__main__':unittest.main()
