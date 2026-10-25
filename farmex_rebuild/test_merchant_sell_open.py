import unittest
from dataclasses import replace
from merchant_sell_open import (SellNativeOpenObservation as Native,plan_sell_native_open,
    SellOpeningState as State,SellOpeningObservation as Obs,SellOpeningFrame as Frame)
from operation_engine import MerchantRunner,MerchantSettings,MerchantKind,MerchantSnapshot

def own_open_operands():
    return Native(global_samples=((0x553e80,0x1000),(0x554140,0x20),(0x554144,0x30),
                                 (0x553e80,0x1100),(0x554140,0x40),(0x554200,0x10)),
        protected_samples=((0x1000,0x2000),(0x2020,0x3000),(0x3030,0x11223344)),
        direct_samples=((0x1100,0x4000),(0x4040,0x5000),(0x5000,0x6000),(0x6010,0x7000)))

class SellOpenTests(unittest.TestCase):
    def test_fresh_roots_and_offsets_are_independent(self):
        p=plan_sell_native_open(own_open_operands())
        self.assertTrue(p.complete);self.assertEqual(p.native_call.ecx_dword,0x5000)
        self.assertEqual(p.native_call.target_dword,0x7000);self.assertEqual(p.native_call.eax_dword,0x10)
        self.assertEqual(p.native_call.push_order,(1,0x11223344))
        self.assertEqual(p.native_call.stack_arguments,(0x11223344,1));self.assertFalse(p.native_call.abi_verified)
    def test_missing_second_root_never_reuses_first(self):
        p=plan_sell_native_open(replace(own_open_operands(),direct_samples=()))
        self.assertFalse(p.complete);self.assertIn('direct sample0',p.missing)
        self.assertEqual(len([r for r in p.reads if r[0]=='protected']),3)
    def test_address_mismatch_rejected(self):
        with self.assertRaises(ValueError):plan_sell_native_open(replace(own_open_operands(),direct_samples=((0x1000,0x4000),)))
    def test_zero_target_is_not_invented_validity_guard(self):
        o=own_open_operands();p=plan_sell_native_open(replace(o,direct_samples=o.direct_samples[:-1]+((0x6010,0),)))
        self.assertTrue(p.complete);self.assertEqual(p.native_call.target_dword,0)
        self.assertFalse(p.native_call.executable_target_verified)
    def test_pending_precedes_missing_clock(self):
        p=Frame(State(prepared_slots_dword=1)).step()
        self.assertFalse(p.complete);self.assertEqual(p.state.pending_byte,0)
        self.assertEqual(p.prospective_state.pending_byte,1);self.assertEqual(p.writes,((0x48,1,1),))
    def test_clock_then_operands_then_separate_helper_return(self):
        f=Frame(State(prepared_slots_dword=1));p=f.step(Obs(100,own_open_operands(),False))
        self.assertFalse(p.complete);self.assertEqual(p.prospective_state.pending_stamp_qword,100)
        self.assertTrue(p.native_plan.complete);self.assertEqual(p.state.phase_dword,4)
        p=f.step(Obs(helper_returned=True));self.assertTrue(p.complete);self.assertEqual(p.state.phase_dword,5)
        self.assertEqual(p.calls.count(('GetTickCount',)),1)
    def test_missing_operands_cannot_be_bypassed_by_return_receipt(self):
        p=Frame(State(prepared_slots_dword=1)).step(Obs(100,helper_returned=True))
        self.assertFalse(p.complete);self.assertIn('global sample0',p.missing)
    def test_partial_samples_fill_without_changing_known_values(self):
        f=Frame(State(prepared_slots_dword=1));o=own_open_operands()
        f.step(Obs(100,replace(o,global_samples=o.global_samples[:1],protected_samples=(),direct_samples=())))
        p=f.step(Obs(native_inputs=o,helper_returned=True));self.assertTrue(p.complete)
        f=Frame(State(prepared_slots_dword=1));f.step(Obs(100))
        with self.assertRaises(ValueError):f.step(Obs(101))
    def test_signed_count_gate_does_not_call_native_open(self):
        for count in (0,0xffffffff,0x80000000):
            p=Frame(State(prepared_slots_dword=count)).step(Obs(empty_span_returned=True))
            self.assertTrue(p.complete);self.assertEqual(p.status,'no_sale_slots')
            self.assertEqual(p.writes,());self.assertIsNone(p.native_plan)
    def test_empty_span_requires_normal_return(self):
        p=Frame(State()).step();self.assertFalse(p.complete)
        self.assertEqual(p.prospective_state.phase_dword,4)
    def test_runner_holds_then_advances_with_bound_opening(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=4
        f=Frame(State(prepared_slots_dword=1))
        self.assertEqual(r.tick(MerchantSnapshot(1,prepared_slot_count=1,sell_opening_execution=f.step())).status,'needs_adapter')
        p=f.step(Obs(100,own_open_operands(),True))
        result=r.tick(MerchantSnapshot(101,prepared_slot_count=1,sell_opening_execution=p))
        self.assertEqual((r.phase,r.phase_ms),(5,100));self.assertEqual(result.status,'open_attempt')
    def test_counter_conflict_rejected(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=4
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(1,prepared_slot_count=1,sell_opening_execution=Frame(State()).step()))
    def test_bound_empty_stop_waits_for_span_receipt(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=4
        f=Frame(State())
        self.assertEqual(r.tick(MerchantSnapshot(1,prepared_slot_count=0,sell_opening_execution=f.step())).status,'needs_adapter')
        self.assertTrue(r.active)
        p=r.tick(MerchantSnapshot(2,prepared_slot_count=0,sell_opening_execution=f.step(Obs(empty_span_returned=True))))
        self.assertEqual(p.reason,'no_sale_slots');self.assertFalse(r.active)
    def test_source_address_addition_wraps_dword(self):
        o=own_open_operands()
        changed=replace(o,protected_samples=((0x1000,0xfffffff0),(0x10,0x3000),(0x3030,0x11223344)))
        self.assertTrue(plan_sell_native_open(changed).complete)

if __name__=='__main__':unittest.main()
