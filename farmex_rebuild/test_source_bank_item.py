import unittest
from dataclasses import replace
from source_coin import GuardedDwordSample as D
from source_bank_item import BankItemObservation as Obs,plan_bank_item
from merchant_bank_count import BankCountObservation,plan_bank_count
from merchant_buy_failure import BuyFailureObservation,plan_buy_failure

class BankItemTests(unittest.TestCase):
    def fixture(self,slot=3,base=100000,variant=123456):
        globals=((0x553e80,0x1000),(0x5540bc,0x10),(0x5540c0,0x20))
        samples=(D(0x1000,1,0x2000),D(0x2010,1,0x3000),D((0x3020+(slot<<2))&0xffffffff,1,0x4000),
            D(0x4060,1,0x5000),D(0x4064,1,0x6000),D(0x5000,1,base),D(0x6000,1,variant))
        return Obs(globals,samples)
    def test_both_pointers_precede_unsigned_value_reads_and_remainder(self):
        p=plan_bank_item(3,self.fixture())
        self.assertTrue(p.complete);self.assertEqual(p.result_dword,100456)
        addresses=[s[1] for s in p.steps if s[0]=='0045dc44']
        self.assertEqual(addresses,[0x1000,0x2010,0x302c,0x4060,0x4064,0x5000,0x6000])
        self.assertFalse(p.independently_verified)
    def test_unsigned_variant_and_low32_result_overflow(self):
        p=plan_bank_item(3,self.fixture(base=0xfffffff0,variant=0xffffffff))
        self.assertEqual(p.result_dword,279) # unsigned remainder295, then low32 ADD.
    def test_record_zero_exits_before_pointer_and_value_reads(self):
        o=self.fixture();samples=o.guarded_samples[:2]+(replace(o.guarded_samples[2],value_dword=0),D(0xdead,1,99))
        p=plan_bank_item(3,Obs(o.global_samples,samples))
        self.assertTrue(p.complete);self.assertEqual(p.result_dword,0);self.assertEqual(len(p.guarded_plans),3)
    def test_null_root_continues_offsets_without_consuming_null_api_samples(self):
        o=Obs(((0x553e80,0),(0x5540bc,0),(0x5540c0,4)),(D(4,1,0),))
        p=plan_bank_item(0,o)
        self.assertTrue(p.complete);self.assertEqual(p.result_dword,0)
        self.assertEqual([g.status for g in p.guarded_plans],['null_returns_zero','null_returns_zero','value_observed'])
    def test_protection_failure_zero_is_not_unknown_or_healthy_empty_proof(self):
        o=Obs(((0x553e80,0x1000),(0x5540bc,0x10),(0x5540c0,0x20)),
              (D(0x1000,0),D(0x10,1,0x3000),D(0x302c,1,0)))
        p=plan_bank_item(3,o)
        self.assertTrue(p.complete);self.assertEqual(p.result_dword,0)
        self.assertEqual(p.guarded_plans[0].status,'protection_failure_returns_zero')
        self.assertFalse(p.guarded_plans[0].native_effects_verified)
        unknown=replace(o,guarded_samples=(D(0x1000),))
        self.assertFalse(plan_bank_item(3,unknown).complete)
    def test_null_base_pointer_still_reads_variant_pointer_and_value(self):
        o=self.fixture(variant=999)
        samples=o.guarded_samples[:3]+(D(0x4060,1,0),D(0x4064,1,0x6000),D(0x6000,1,999))
        p=plan_bank_item(3,replace(o,guarded_samples=samples))
        self.assertTrue(p.complete);self.assertEqual(p.result_dword,999)
        self.assertEqual([s[1] for s in p.steps if s[0]=='0045dc44'][-3:],[0x4064,0,0x6000])
    def test_slot_shift_and_all_address_additions_wrap_low32(self):
        o=Obs(((0x553e80,0x1000),(0x5540bc,0xffffffff),(0x5540c0,0xc)),
              (D(0x1000,1,0x2000),D(0x1fff,1,0xfffffff8),D(8,1,0)))
        p=plan_bank_item(0x40000001,o)
        self.assertTrue(p.complete);self.assertIn(('slot_shift_low32',0x40000001,4),p.steps)
        self.assertEqual(p.result_dword,0)
    def test_reached_order_mismatch_and_missing_data_do_not_become_zero(self):
        o=self.fixture()
        for n in range(7):
            p=plan_bank_item(3,replace(o,guarded_samples=o.guarded_samples[:n]))
            self.assertFalse(p.complete);self.assertIsNone(p.result_dword)
        with self.assertRaises(ValueError):plan_bank_item(3,replace(o,global_samples=((0x5540bc,0x10),)))
        with self.assertRaises(ValueError):plan_bank_item(3,replace(o,guarded_samples=(D(0x9999,1,0),)))
        with self.assertRaises(ValueError):plan_bank_item(True,o)

class BoundBankCountTests(unittest.TestCase):
    def zero(self,slot,offset=0):
        at=(offset+(slot<<2))&0xffffffff
        return Obs(((0x553e80,0),(0x5540bc,0),(0x5540c0,offset)),() if at==0 else (D(at,1,0),))
    def test_bound_slots_own_their_fresh_globals_and_do_not_fill_caller_return(self):
        raw=tuple(None if i in (0,191) else 1 for i in range(192))
        inputs=tuple(self.zero(i,8 if i==191 else 0) if i in (0,191) else None for i in range(192))
        o=BankCountObservation(raw,(True,)*192,inputs)
        p=plan_bank_count(o)
        self.assertTrue(p.complete);self.assertEqual(p.count_dword,2);self.assertEqual(p.zero_slots,(0,191))
        self.assertEqual([q.slot_dword for q in p.item_plans],[0,191])
        self.assertFalse(plan_bank_count(replace(o,item_returned=())).complete)
        parent=BuyFailureObservation(inventory_returned=True,free_count_dword=1,threshold_dword=0,
            policy_results=(2,2,2),bank_count_execution=p,setup_gate_byte=0,
            branch_span_returns=(True,True),route_span_returned=True)
        self.assertFalse(plan_buy_failure(parent).complete)
        self.assertTrue(plan_buy_failure(replace(parent,bank_count_returned=True)).complete)
    def test_bound_gap_raw_conflict_and_late_slot_not_consumed(self):
        o=BankCountObservation((),(True,),(Obs(),))
        p=plan_bank_count(o);self.assertFalse(p.complete);self.assertEqual(p.zero_slots,())
        self.assertEqual(len(p.item_plans),1)
        with self.assertRaises(ValueError):plan_bank_count(BankCountObservation((0,),(True,),(self.zero(0),)))
        p=plan_bank_count(BankCountObservation((0,),(False,),(self.zero(0),)))
        self.assertFalse(p.complete);self.assertEqual(p.item_plans,())
        with self.assertRaises(ValueError):BankCountObservation(item_inputs=(7,))

if __name__=='__main__':unittest.main()
