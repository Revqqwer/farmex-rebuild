import tempfile,unittest
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
from simulation_ui import EnginePage
from route_catalog import ROUTE_COMBO_PATHS
from name_codec import WindowsNameCodec
from merchant_bank_route import merchant_bank_route_inputs_from_panel,plan_merchant_bank_route
from merchant_sell_failure import SellFailureObservation
from operation_engine import MerchantRunner,MerchantSettings,MerchantKind,MerchantSnapshot

class EngineRouteSampleTests(unittest.TestCase):
    def engine(self,reader):
        engine=object.__new__(EnginePage);engine.route_configuration_reader=reader;return engine
    def test_absent_provider_is_unknown_while_observed_empty_is_known(self):
        engine=self.engine(None)
        self.assertIsNone(engine.panel_route_sample('Mine',ansi=True))
        self.assertIsNone(engine.panel_route_sample('SMerchant'))
        engine.route_configuration_reader=lambda:({ROUTE_COMBO_PATHS['Mine']:''},1254)
        self.assertEqual(engine.panel_route_sample('Mine'), '');self.assertEqual(engine.panel_route_sample('Mine',ansi=True),b'')
    def test_one_fresh_snapshot_per_reached_call_and_no_other_text_required(self):
        samples=iter((({ROUTE_COMBO_PATHS['SMerchant']:'first.R'},1254),
                      ({ROUTE_COMBO_PATHS['SMerchant']:'second.R'},1254)))
        engine=self.engine(lambda:next(samples))
        self.assertEqual(engine.panel_route_sample('SMerchant'),'first.R')
        self.assertEqual(engine.panel_route_sample('SMerchant',ansi=True),b'second.R')
    def test_unicode_text_does_not_claim_ansi_conversion_or_require_codepage(self):
        engine=self.engine(lambda:({ROUTE_COMBO_PATHS['BMerchant']:'😀.R'},None))
        self.assertEqual(engine.panel_route_sample('BMerchant'),'😀.R')
        with self.assertRaises(ValueError):engine.panel_route_sample('BMerchant',ansi=True)
        engine.route_configuration_reader=lambda:({ROUTE_COMBO_PATHS['Mine']:'😀.R'},1254)
        with self.assertRaises(ValueError):engine.panel_route_sample('Mine',ansi=True)
        engine.route_configuration_reader=lambda:({ROUTE_COMBO_PATHS['Mine']:'😀.R'},65001)
        self.assertEqual(engine.panel_route_sample('Mine',ansi=True),'😀.R'.encode('utf-8'))
    def test_missing_text_bad_reader_and_unsupported_kind_are_not_defaults(self):
        for sample in (({},1254),({ROUTE_COMBO_PATHS['Mine']:None},1254),[{},1254],({},),None):
            with self.assertRaises(ValueError):self.engine(lambda:sample).panel_route_sample('Mine')
        with self.assertRaises(ValueError):self.engine(None).panel_route_sample('supply')

class PanelBankRouteInputsTests(unittest.TestCase):
    def texts(self,name):return {ROUTE_COMBO_PATHS['SMerchant']:name,ROUTE_COMBO_PATHS['BMerchant']:'other.R'}
    def test_factory_does_no_io_and_supplies_no_native_normal_return_receipts(self):
        with patch('merchant_bank_route.import_panel_route_choice',side_effect=AssertionError('early file IO')):
            o=merchant_bank_route_inputs_from_panel(self.texts('bank.R'),r'C:\owned',WindowsNameCodec(1254))
        self.assertEqual(o.filename_ansi,b'bank.R');self.assertEqual(o.prefix_ansi,b'C:\\owned\\')
        self.assertIsNone(o.prestart_span_returned);self.assertIsNone(o.error_stop_returned)
        self.assertIsNone(o.start_execution)
    def test_profile_name_to_owned_file_to_failure_caller_retains_outer_return_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory,'İsim.R').write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=Bekle\nSub10=3\n')
            o=merchant_bank_route_inputs_from_panel(self.texts('İsim.R'),directory,WindowsNameCodec(1254))
            p=plan_merchant_bank_route(o)
            self.assertTrue(p.ready);self.assertEqual(p.imported_start.imported.steps[0].seconds,3)
            observation=SellFailureObservation(header_span_returns=(True,True),alarm_byte=0,
                policy_results=(2,2,2),status_byte_90=0,setup_gate_byte=0,
                branch_span_returns=(True,True),route_inputs=o)
            runner=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL,failure_policy='bank_route'))
            runner.start();runner.phase=2
            result=runner.tick(MerchantSnapshot(61000,setup_result=1,sell_failure_inputs=observation))
            self.assertEqual(result.status,'needs_adapter');self.assertEqual(runner.phase,2)
            self.assertTrue(runner.last_sell_failure_plan.route_plan.ready)
            result=runner.tick(MerchantSnapshot(61001,setup_result=1,
                sell_failure_inputs=replace(observation,route_span_returned=True)))
            self.assertEqual(result.status,'bank_route');self.assertEqual(runner.phase,0)
            self.assertEqual(result.intents[0].kind,'load_bank_route')
            self.assertFalse(runner.last_sell_failure_plan.route_plan.native_helper_executed)
    def test_unknown_prefix_and_empty_name_keep_existing_source_gap_branches(self):
        codec=WindowsNameCodec(1254)
        o=merchant_bank_route_inputs_from_panel(self.texts('bank.R'),None,codec)
        self.assertIsNone(o.prefix_ansi);self.assertFalse(plan_merchant_bank_route(o).complete)
        o=merchant_bank_route_inputs_from_panel(self.texts(''),None,codec)
        p=plan_merchant_bank_route(o);self.assertEqual(p.error_kind,'unselected');self.assertFalse(p.complete)
        o=merchant_bank_route_inputs_from_panel(self.texts(''),object(),codec)
        self.assertIsNone(o.prefix_ansi) # Empty-name branch never consumes the later directory operand.
    def test_invalid_or_lossy_prefix_is_not_silently_used(self):
        for directory in ('relative',r'C:\😀'):
            with self.assertRaises(ValueError):merchant_bank_route_inputs_from_panel(self.texts('bank.R'),directory,WindowsNameCodec(1254))
        with self.assertRaises(ValueError):merchant_bank_route_inputs_from_panel({},r'C:\owned',WindowsNameCodec(1254))

if __name__=='__main__':unittest.main()
