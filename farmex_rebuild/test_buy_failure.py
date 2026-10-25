import tempfile,unittest
from pathlib import Path
from dataclasses import replace
from merchant_bank_count import BankCountObservation as CountObs,plan_bank_count
from merchant_buy_failure import BuyFailureObservation as Obs,plan_buy_failure
from merchant_bank_route import MerchantBankRouteInputs,merchant_bank_route_inputs_from_panel
from merchant_setup import MerchantInventoryObservation
from name_codec import WindowsNameCodec
from route_catalog import ROUTE_COMBO_PATHS
from operation_engine import MerchantRunner,MerchantSettings,MerchantKind,MerchantSnapshot

class BankCountTests(unittest.TestCase):
    def test_exact_192_slots_all_zero_or_nonzero(self):
        for value,expected in ((0,192),(1,0),(0xffffffff,0)):
            p=plan_bank_count(CountObs((value,)*192,(True,)*192))
            self.assertTrue(p.complete);self.assertEqual(p.count_dword,expected)
            self.assertEqual(p.calls[0],('0046fed8',0));self.assertEqual(p.calls[-1],('0046fed8',191))
    def test_prefix_and_return_gaps_do_not_complete_or_invent_zero(self):
        p=plan_bank_count(CountObs((0,1),(True,True)))
        self.assertFalse(p.complete);self.assertIsNone(p.count_dword);self.assertEqual(p.zero_slots,(0,))
        p=plan_bank_count(CountObs((0,)*192,(True,)*191))
        self.assertFalse(p.complete);self.assertIn('191',p.missing)
    def test_mixed_zero_slots_preserve_indices(self):
        values=tuple(0 if i in (0,17,191) else 99 for i in range(192))
        p=plan_bank_count(CountObs(values,(True,)*192))
        self.assertEqual(p.count_dword,3);self.assertEqual(p.zero_slots,(0,17,191))
    def test_types(self):
        with self.assertRaises(ValueError):CountObs((0,)*193)
        with self.assertRaises(ValueError):CountObs((True,))
        with self.assertRaises(ValueError):CountObs((),(1,))

class BuyFailureTests(unittest.TestCase):
    def o(self,**changes):
        return replace(Obs(inventory_returned=True,free_count_dword=1,threshold_dword=0,
            policy_results=(2,2,2),bank_count_returned=True,bank_count_dword=1,
            setup_gate_byte=0,branch_span_returns=(True,True),route_span_returned=True),**changes)
    def test_alarm_signed_comparison_and_fresh_failure_inventory(self):
        p=plan_buy_failure(self.o(free_count_dword=0,threshold_dword=0))
        self.assertFalse(p.complete);self.assertIn('alarm BYTE',p.missing)
        self.assertTrue(plan_buy_failure(self.o(free_count_dword=0,threshold_dword=0,alarm_byte=0)).complete)
        self.assertTrue(plan_buy_failure(self.o(free_count_dword=0xffffffff,threshold_dword=0xfffffffe)).complete)
        p=plan_buy_failure(self.o(free_count_dword=None,inventory_inputs=MerchantInventoryObservation((0,)*28)))
        self.assertTrue(p.complete);self.assertEqual(p.inventory_plan.free_count,28)
        self.assertFalse(plan_buy_failure(self.o(inventory_returned=None)).complete)
    def test_alarm_span_and_three_policy_reads_remain_independent(self):
        p=plan_buy_failure(self.o(free_count_dword=0,alarm_byte=1))
        self.assertFalse(p.complete);self.assertIn('alarm normal',p.missing)
        o=self.o(policy_results=(0,),stop_returned=True,route_inputs_factory=lambda:(_ for _ in ()).throw(AssertionError('unreached')))
        self.assertEqual(plan_buy_failure(o).status,'stop_returned')
        self.assertEqual(plan_buy_failure(self.o(policy_results=(9,1),stop_returned=True,disconnect_returned=True)).status,'disconnect_returned')
        self.assertEqual(plan_buy_failure(self.o(policy_results=(9,9,9))).status,'unhandled_policy')
    def test_bank_dec_wrap_and_unavailable_stop_precedes_notification(self):
        for count,due in ((0,False),(1,True),(0xffffffff,False),(0x80000000,True),(0x80000001,False)):
            p=plan_buy_failure(self.o(bank_count_dword=count,stop_returned=True))
            self.assertTrue(p.complete)
            self.assertEqual(p.status=='bank_route_span_returned',due)
            self.assertEqual(p.bank_count_after_dec,(count-1)&0xffffffff)
            if not due:
                stop=next(i for i,s in enumerate(p.steps) if s[0]=='0040ae0c')
                notice=next(i for i,s in enumerate(p.steps) if s[:2]==('normal_span','bank unavailable notification'))
                self.assertLess(stop,notice);self.assertEqual(p.writes,())
        p=plan_buy_failure(self.o(bank_count_dword=0))
        self.assertFalse(p.complete);self.assertFalse(any(s[:2]==('normal_span','bank unavailable notification') for s in p.steps))
    def test_bound_count_completion_and_separate_helper_return(self):
        complete=plan_bank_count(CountObs((0,)*192,(True,)*192))
        p=plan_buy_failure(self.o(bank_count_dword=None,bank_count_execution=complete))
        self.assertTrue(p.complete);self.assertEqual(p.bank_count_after_dec,191)
        self.assertFalse(plan_buy_failure(self.o(bank_count_dword=None,bank_count_execution=complete,bank_count_returned=None)).complete)
        partial=plan_bank_count(CountObs((0,),(True,)))
        self.assertFalse(plan_buy_failure(self.o(bank_count_dword=None,bank_count_execution=partial)).complete)
        with self.assertRaises(ValueError):plan_buy_failure(self.o(bank_count_execution=complete))
    def test_native_call_return_gap_keeps_only_prospective_writes(self):
        p=plan_buy_failure(self.o(route_span_returned=None))
        self.assertFalse(p.complete);self.assertEqual(p.phase_dword,2);self.assertEqual(p.prospective_phase_dword,0)
        self.assertEqual(p.prospective_setup_gate_byte,1);self.assertEqual(p.writes,((0x58,1,1),(4,4,0)))
        self.assertFalse(p.independently_verified)
    def test_bmerchant_file_import_cannot_be_replaced_with_smerchant(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory,'buy.R').write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=Bekle\nSub10=4\n')
            texts={ROUTE_COMBO_PATHS['BMerchant']:'buy.R',ROUTE_COMBO_PATHS['SMerchant']:'wrong.R'}
            inputs=merchant_bank_route_inputs_from_panel(texts,directory,WindowsNameCodec(1254),kind='BMerchant')
            p=plan_buy_failure(self.o(route_inputs=inputs))
            self.assertTrue(p.complete);self.assertEqual(p.route_plan.kind,'BMerchant')
            self.assertEqual(p.route_plan.filename_global,0x569908);self.assertEqual(p.route_plan.imported_start.imported.steps[0].seconds,4)
            with self.assertRaises(ValueError):plan_buy_failure(self.o(route_inputs=replace(inputs,kind='SMerchant')))
        p=plan_buy_failure(self.o(route_inputs=MerchantBankRouteInputs(kind='BMerchant')))
        self.assertFalse(p.complete) # Outer receipt cannot bypass missing detailed filename.
        self.assertEqual(p.route_plan.filename_global,0x569908)
    def test_runner_bound_failure_and_legacy_gate_conflict(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.BUY));r.start();r.phase=2
        d=r.tick(MerchantSnapshot(61000,setup_result=1,buy_failure_inputs=self.o(route_span_returned=None)))
        self.assertEqual(d.status,'needs_adapter');self.assertEqual(r.phase,2)
        d=r.tick(MerchantSnapshot(61001,setup_result=1,buy_failure_inputs=self.o()))
        self.assertEqual(d.status,'bank_route');self.assertEqual(d.intents[0].reference,'BMerchant');self.assertEqual(r.phase,0)
        r.phase=2
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(61002,setup_result=1,setup_started_ms=0,buy_failure_inputs=self.o(),bank_route_allowed=True))
    def test_typed_inputs_and_reached_raw_conflicts(self):
        with self.assertRaises(ValueError):Obs(bank_count_dword=True)
        with self.assertRaises(ValueError):Obs(alarm_byte=256)
        with self.assertRaises(ValueError):plan_buy_failure(self.o(inventory_inputs=MerchantInventoryObservation((0,)*28)))

if __name__=='__main__':unittest.main()
