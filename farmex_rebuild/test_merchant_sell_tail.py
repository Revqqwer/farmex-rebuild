import unittest
from dataclasses import replace
from action_queue import QueueState,QueueSample
from merchant_sell_selection import SellSelectionObservation as Selection, SellPreparedRow,plan_sell_selection
from merchant_sell_tail import SellSlotState as State,SellSlotObservation as Obs,SellSlotFrame as Frame,SEED
from operation_engine import MerchantRunner,MerchantSettings,MerchantKind,MerchantSnapshot

class SellTailTests(unittest.TestCase):
    def inputs(self):
        return Selection((SellPreparedRow(0x11223344,0x10001,0x155667788),),True,
            (0x11223344,),(0,),(0x10001,))
    def selected(self):return plan_sell_selection(False,self.inputs())
    def ready(self,**changes):
        return replace(Obs(10,97,(True,)*5,QueueSample(11,1),True),**changes)
    def test_pending_used_precede_clock_and_do_not_commit_on_gap(self):
        initial=State();p=Frame(self.selected(),initial,QueueState()).step()
        self.assertFalse(p.complete);self.assertEqual(p.state,initial)
        self.assertEqual(p.prospective_state.used_bytes[0],1);self.assertEqual(p.prospective_state.item_pending_byte,1)
        self.assertEqual([w[0] for w in p.writes],[0x67,0x28]);self.assertEqual(p.prospective_payload,SEED)
    def test_clock_then_accumulator_before_unknown_ftol(self):
        p=Frame(self.selected(),State(accumulated_qword=0xffffffffffffffff),QueueState()).step(Obs(item_tick_dword=0xffffffff))
        self.assertFalse(p.complete);self.assertEqual(p.prospective_state.item_stamp_qword,0xffffffff)
        term=(0x10001*0x55667788)&0xffffffff
        self.assertEqual(p.prospective_state.accumulated_qword,(term-1)&0xffffffffffffffff)
        self.assertNotIn(('_memcpy',0,4),p.calls)
    def test_missing_ftol_is_not_rounded_python_formula(self):
        p=Frame(self.selected(),State(),QueueState()).step(Obs(10,None,(True,)*5,QueueSample(11,1),True))
        self.assertFalse(p.complete);self.assertIn('__ftol',p.missing);self.assertIsNone(p.payload)
    def test_exact_14byte_payload_and_independent_clock(self):
        p=Frame(self.selected(),State(),QueueState()).step(self.ready())
        self.assertTrue(p.complete);self.assertEqual(p.payload,bytes.fromhex('6803443322110100887766550000'))
        self.assertEqual(p.queue.records[0].created_tick,11);self.assertEqual(p.state.item_stamp_qword,10)
        self.assertEqual(p.state.net_qword,97);self.assertEqual(p.state.prepared_slots_dword,1)
        self.assertEqual(p.return_al,1);self.assertFalse(p.independently_verified)
    def test_each_memcpy_requires_separate_normal_return(self):
        for i in range(5):
            p=Frame(self.selected(),State(),QueueState()).step(self.ready(copy_returns=(True,)*i+(False,)))
            self.assertFalse(p.complete);self.assertIn('memcpy%d'%i,p.missing);self.assertEqual(p.queue.records,())
    def test_cached_local_queue_copy_not_repeated_waiting_for_return(self):
        f=Frame(self.selected(),State(),QueueState())
        a=f.step(self.ready(enqueue_returned=False))
        self.assertFalse(a.complete);self.assertEqual(a.queue.records,());self.assertEqual(len(a.prospective_queue.records),1)
        b=f.step(Obs(enqueue_returned=True))
        self.assertTrue(b.complete);self.assertEqual(len(b.queue.records),1)
        self.assertEqual(f.step(self.ready(item_tick_dword=999)).queue,b.queue)
    def test_disconnected_enqueue_still_advances_prepared_counter(self):
        p=Frame(self.selected(),State(),QueueState()).step(self.ready(queue_sample=QueueSample(connection_gate=0)))
        self.assertTrue(p.complete);self.assertEqual(p.queue.records,());self.assertEqual(p.state.prepared_slots_dword,1)
    def test_unknown_enqueue_gate_or_tick_never_assumes_ready(self):
        for sample in (QueueSample(),QueueSample(connection_gate=1)):
            p=Frame(self.selected(),State(),QueueState()).step(self.ready(queue_sample=sample))
            self.assertFalse(p.complete);self.assertEqual(p.prospective_state.prepared_slots_dword,0)
    def test_frozen_known_clock_and_ftol_observation(self):
        f=Frame(self.selected(),State(),QueueState());f.step(Obs(10,97))
        with self.assertRaises(ValueError):f.step(Obs(item_tick_dword=11))
        with self.assertRaises(ValueError):f.step(Obs(ftol_qword=98))
    def test_market_slot_lowbyte_and_dword_increment_wrap(self):
        p=Frame(self.selected(),State(prepared_slots_dword=0xffffffff),QueueState()).step(self.ready())
        self.assertEqual(p.payload[-1],255);self.assertEqual(p.state.prepared_slots_dword,0)
    def test_frame_rejects_unmatched_or_incomplete_selection(self):
        p=plan_sell_selection(True,Selection(item_results=(0,)))
        with self.assertRaises(ValueError):Frame(p,State(),QueueState())
    def test_runner_waits_for_bound_tail_and_then_advances_caller(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=3
        f=Frame(self.selected(),State(),QueueState());p=f.step()
        snapshot=MerchantSnapshot(1,sale_session_ready=True,item_pending=False,prepared_slot_count=0,
            sell_selection_inputs=self.inputs(),sell_slot_execution=p)
        self.assertEqual(r.tick(snapshot).status,'needs_adapter');self.assertEqual(r.entry_index,0)
        p=f.step(self.ready())
        result=r.tick(replace(snapshot,now_ms=20,sell_slot_execution=p))
        self.assertEqual(result.status,'slot_attempt');self.assertEqual(r.entry_index,1);self.assertEqual(r.item_ms,10)
    def test_opaque_return_cannot_override_bound_frame_gap(self):
        with self.assertRaises(ValueError):MerchantSnapshot(1,sell_selection_inputs=self.inputs(),
            sell_slot_execution=Frame(self.selected(),State(),QueueState()).step(),sell_slot_helper_returned=True)
    def test_bound_frame_market_slot_must_match_caller_snapshot(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=3
        execution=Frame(self.selected(),State(prepared_slots_dword=1),QueueState()).step(self.ready())
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(20,sale_session_ready=True,item_pending=False,
            prepared_slot_count=0,sell_selection_inputs=self.inputs(),sell_slot_execution=execution))
    def test_zero_clock_ftol_and_last_inventory_slot_are_explicit_values(self):
        selection=plan_sell_selection(True,replace(self.inputs(),inventory_slot_dword=41,
            item_results=(None,)*27+(0x11223344,),used_bytes=(None,)*27+(0,)))
        f=Frame(selection,State(prepared_slots_dword=5),QueueState())
        a=f.step(Obs(item_tick_dword=0,ftol_qword=0))
        total=a.prospective_state.accumulated_qword
        b=f.step(Obs(copy_returns=(True,)*5,queue_sample=QueueSample(connection_gate=0),enqueue_returned=True))
        self.assertTrue(b.complete);self.assertEqual(b.payload[-2:],bytes((27,5)))
        self.assertEqual(b.state.net_qword,0);self.assertEqual(b.state.item_stamp_qword,0)
        self.assertEqual(b.state.accumulated_qword,total);self.assertEqual(b.calls.count(('GetTickCount',)),1)
    def test_explicit_disk_crt_replay_derives_net_from_source_total(self):
        selected=plan_sell_selection(False,Selection((SellPreparedRow(1,2,50),),True,(1,),(0,),(2,)))
        p=Frame(selected,State(),QueueState()).step(self.ready(ftol_qword=None,disk_crt_replay=True,
            x87_control_word=0x37f,x87_clean_context=True))
        self.assertTrue(p.complete);self.assertEqual(p.state.accumulated_qword,100);self.assertEqual(p.state.net_qword,97)
        self.assertEqual(p.ftol_source,'local_disk_crt_replay');self.assertFalse(p.ftol_plan.loaded_game_runtime_verified)
    def test_replay_missing_control_word_waits_without_raw_result_fallback(self):
        f=Frame(self.selected(),State(),QueueState())
        p=f.step(self.ready(ftol_qword=None,disk_crt_replay=True,x87_clean_context=True))
        self.assertFalse(p.complete);self.assertIn('control WORD',p.missing)
        p=f.step(Obs(x87_control_word=0x37f))
        self.assertTrue(p.complete);self.assertEqual(len(p.queue.records),1)
    def test_replay_and_observed_ftol_result_are_mutually_exclusive(self):
        with self.assertRaises(ValueError):Obs(ftol_qword=97,disk_crt_replay=True)

if __name__=='__main__':unittest.main()
