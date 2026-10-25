import unittest,tempfile
from pathlib import Path
from dataclasses import replace
from merchant_bank_route import MerchantBankRouteInputs as Inputs,plan_merchant_bank_route
from name_codec import WindowsNameCodec
from merchant_sell_failure import SellFailureObservation,plan_sell_failure
from operation_engine import MerchantRunner,MerchantKind,MerchantSettings,MerchantSnapshot

class MerchantBankRouteTests(unittest.TestCase):
    def failure(self,route,**changes):
        return replace(SellFailureObservation(header_span_returns=(True,True),alarm_byte=0,
            policy_results=(2,2,2),status_byte_90=0,setup_gate_byte=0,
            branch_span_returns=(True,True),route_inputs=route),**changes)
    def route(self,directory,filename=b'bank.R'):
        codec=WindowsNameCodec(1254)
        return Inputs(filename,codec.encode(str(directory)+'\\')[0],codec)
    def test_unknown_filename_and_empty_filename_are_distinct(self):
        p=plan_merchant_bank_route(Inputs());self.assertEqual(p.status,'needs_observation')
        self.assertEqual(p.filename_global,0x5698bc)
        p=plan_merchant_bank_route(Inputs(b''));self.assertEqual(p.status,'source_error_needs_observation')
        self.assertEqual(p.error_kind,'unselected')
        self.assertIsNone(p.imported_start);self.assertFalse(p.ready)
    def test_prefix_and_codec_stay_separate_missing_observations(self):
        p=plan_merchant_bank_route(Inputs(b'bank.R'));self.assertFalse(p.ready);self.assertIn('+57c',p.missing)
        p=plan_merchant_bank_route(Inputs(b'bank.R',b'C:\\own\\'));self.assertFalse(p.ready);self.assertIn('codec',p.missing)
    def test_owned_local_route_import_preserves_rows_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory,'bank.R').write_bytes(b'[Count]\nValue=2\n[ROUTE]\nISLEM0=Bekle\nSub10=3\nISLEM1=Koordinat\nSub11=10\nSub21=20\n')
            p=plan_merchant_bank_route(self.route(directory))
            self.assertTrue(p.ready);self.assertEqual(len(p.imported_start.imported.steps),2)
            self.assertEqual(p.imported_start.imported.steps[0].seconds,3)
            self.assertFalse(p.native_helper_executed);self.assertFalse(p.live_compatibility_verified)
    def test_missing_zero_count_unsupported_and_budget_are_not_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            o=self.route(directory)
            self.assertFalse(plan_merchant_bank_route(o).ready)
            for raw in (b'[Count]\nValue=0\n',b'[Count]\nValue=1\n[ROUTE]\nISLEM0=UNSUPPORTED\n',b'[Count]\nValue=2\n'):
                Path(directory,'bank.R').write_bytes(raw)
                self.assertFalse(plan_merchant_bank_route(replace(o,max_rows=1)).ready)
    def test_failure_cannot_bypass_bound_missing_route_with_receipt(self):
        o=self.failure(Inputs(),route_span_returned=True)
        p=plan_sell_failure(o);self.assertFalse(p.complete);self.assertIsNotNone(p.route_plan)
        self.assertEqual(p.phase_dword,2);self.assertEqual(p.prospective_phase_dword,0)
    def test_unreached_route_input_does_not_read_file(self):
        o=SellFailureObservation(route_inputs=Inputs(b'bank.R',b'relative-prefix',WindowsNameCodec(1254)))
        p=plan_sell_failure(o);self.assertFalse(p.complete);self.assertIsNone(p.route_plan)
    def test_import_does_not_replace_outer_helper_return(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory,'bank.R').write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=Bekle\nSub10=0\n')
            o=self.failure(self.route(directory));p=plan_sell_failure(o)
            self.assertTrue(p.route_plan.ready);self.assertFalse(p.complete)
            r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=2
            self.assertEqual(r.tick(MerchantSnapshot(61000,setup_result=1,sell_failure_inputs=o)).status,'needs_adapter')
            d=r.tick(MerchantSnapshot(61001,setup_result=1,sell_failure_inputs=replace(o,route_span_returned=True)))
            self.assertEqual(d.status,'bank_route');self.assertEqual(r.phase,0)
    def test_types(self):
        with self.assertRaises(ValueError):Inputs(filename_ansi='bank.R')
        with self.assertRaises(ValueError):Inputs(max_rows=True)
        with self.assertRaises(ValueError):SellFailureObservation(route_inputs=0)
    def receipts(self,o):
        return replace(o,error_message_returned=True,path_cleanup_returned=True,error_stop_returned=True,
            error_notification_returned=True,error_final_cleanup_returned=True)
    def test_unselected_error_skips_path_cleanup_but_needs_other_receipts(self):
        o=Inputs(b'');p=plan_merchant_bank_route(o)
        self.assertFalse(p.complete);self.assertTrue(p.stop_required)
        self.assertFalse(any(s[0]=='0040ae0c' for s in p.steps))
        o=replace(self.receipts(o),path_cleanup_returned=False)
        p=plan_merchant_bank_route(o);self.assertTrue(p.complete);self.assertFalse(p.ready)
        self.assertNotIn('path cleanup',[s[1] for s in p.steps if s[0]=='normal_span'])
    def test_missing_file_message_and_path_cleanup_precede_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            o=replace(self.receipts(self.route(directory)),error_message_returned=False)
            p=plan_merchant_bank_route(o);self.assertEqual(p.error_kind,'file_missing');self.assertFalse(p.complete)
            self.assertFalse(any(s[0]=='0040ae0c' for s in p.steps))
            p=plan_merchant_bank_route(replace(o,error_message_returned=True,path_cleanup_returned=False))
            self.assertFalse(p.complete);self.assertFalse(any(s[0]=='0040ae0c' for s in p.steps))
    def test_notification_and_final_cleanup_are_after_stop_and_independent(self):
        o=self.receipts(Inputs(b''))
        for field in ('error_stop_returned','error_notification_returned','error_final_cleanup_returned'):
            p=plan_merchant_bank_route(replace(o,**{field:False}))
            self.assertFalse(p.complete);self.assertFalse(p.native_helper_executed)
        p=plan_merchant_bank_route(o);self.assertTrue(p.complete)
        self.assertEqual([s[0] for s in p.steps],['normal_span','0040ae0c','normal_span','normal_span'])
    def test_nonpositive_count_selects_its_own_message_path(self):
        with tempfile.TemporaryDirectory() as directory:
            for count in ('0','4294967295'):
                Path(directory,'bank.R').write_text('[Count]\nValue='+count+'\n',encoding='ascii')
                p=plan_merchant_bank_route(self.receipts(self.route(directory)))
                self.assertTrue(p.complete);self.assertEqual(p.error_kind,'nonpositive_count');self.assertFalse(p.ready)
                self.assertEqual(p.steps[0][-2:],('004ecf79','004ed0be'))
    def test_unsupported_import_does_not_become_a_source_error_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory,'bank.R').write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=UNSUPPORTED\n')
            p=plan_merchant_bank_route(self.receipts(self.route(directory)))
            self.assertFalse(p.complete);self.assertFalse(p.stop_required);self.assertIsNone(p.error_kind)
    def test_error_return_still_requires_outer_span_then_own_runner_stops(self):
        o=self.failure(self.receipts(Inputs(b'')))
        p=plan_sell_failure(o);self.assertFalse(p.complete);self.assertTrue(p.route_plan.complete)
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=2
        d=r.tick(MerchantSnapshot(61000,setup_result=1,sell_failure_inputs=replace(o,route_span_returned=True)))
        self.assertEqual((d.status,d.reason),('stopped','bank_route_load_failed'))
        self.assertEqual(r.phase,0);self.assertTrue(r.setup_seen);self.assertFalse(r.active);self.assertEqual(d.intents,())

if __name__=='__main__':unittest.main()
