import json,unittest
from dataclasses import replace
from merchant_buy_failure import BuyFailureObservation as Obs,BuyFailurePlan,parse_buy_failure,plan_buy_failure
from merchant_bank_route import MerchantBankRoutePlan
from route_ui import RoutePage
from operation_engine import MerchantRunner,MerchantSettings,MerchantKind,MerchantSnapshot

class BuyFailureBindingTests(unittest.TestCase):
    def raw(self,**changes):
        data=dict(inventory_returned=True,free_count_dword=1,threshold_dword=0,
            policy_results=[2,2,2],bank_count_returned=True,bank_count_dword=1,
            setup_gate_byte=0,branch_span_returns=[True,True])
        data.update(changes);return data
    def test_unknown_inventory_return_skips_invalid_count_and_other_tail(self):
        o=parse_buy_failure(json.dumps(self.raw(inventory_returned=False,free_count_dword='bad',bank_error_returns=3)))
        self.assertIsNone(o.free_count_dword);self.assertEqual(o.policy_results,())
        self.assertFalse(plan_buy_failure(o).complete)
    def test_signed_alarm_skip_and_first_policy_stop_do_not_validate_tail(self):
        o=parse_buy_failure(json.dumps(self.raw(alarm_byte='unread',policy_results=[0,'unread'],
            branch_span_returns=[True,'unread'],stop_returned=True,bank_count_dword='unread')))
        self.assertEqual(plan_buy_failure(o).status,'stop_returned');self.assertEqual(o.policy_results,(0,))
        self.assertIsNone(o.alarm_byte);self.assertIsNone(o.bank_count_dword)
    def test_bank_unavailable_stop_gap_skips_later_notification(self):
        raw=self.raw(bank_count_dword=0,branch_span_returns='unread')
        o=parse_buy_failure(json.dumps(raw));self.assertEqual(o.branch_span_returns,())
        self.assertFalse(plan_buy_failure(o).complete)
        raw['stop_returned']=True
        with self.assertRaises(ValueError):parse_buy_failure(json.dumps(raw))
        raw['branch_span_returns']=[True]
        self.assertEqual(plan_buy_failure(parse_buy_failure(json.dumps(raw))).status,'bank_unavailable_stop_returned')
    def test_normal_return_and_its_raw_result_are_separate_operands(self):
        raw=self.raw(bank_count_returned=False,bank_count_dword='unread')
        o=parse_buy_failure(json.dumps(raw));self.assertIsNone(o.bank_count_dword)
        raw['bank_count_returned']=True
        with self.assertRaises(ValueError):parse_buy_failure(json.dumps(raw))
        raw=self.raw();o=parse_buy_failure(json.dumps(raw))
        self.assertFalse(plan_buy_failure(o).complete);self.assertIsNone(o.route_span_returned)
        raw['route_span_returned']=True
        self.assertTrue(plan_buy_failure(parse_buy_failure(json.dumps(raw))).complete)
    def test_json_cannot_inject_bindings_or_unknown_fields(self):
        for raw in ([],{'unknown':1},{'route_inputs':{}},{'bank_count_execution':{}},{'inventory_returned':1}):
            with self.assertRaises(ValueError):parse_buy_failure(json.dumps(raw))
    def test_lazy_factory_only_runs_after_delay_and_result1(self):
        calls=[]
        def factory():calls.append(1);return Obs()
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.BUY));r.start();r.phase=2
        self.assertEqual(r.tick(MerchantSnapshot(1,setup_result=1,buy_failure_factory=factory)).status,'waiting')
        r.tick(MerchantSnapshot(61000,setup_result=0,buy_failure_factory=factory));self.assertEqual(calls,[])
        self.assertEqual(r.tick(MerchantSnapshot(61001,setup_result=1,buy_failure_factory=factory)).status,'needs_adapter')
        self.assertEqual(calls,[1])
    def test_factory_and_legacy_gate_or_raw_inputs_conflict_at_reached_branch(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.BUY));r.start();r.phase=2
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(61000,setup_result=1,
            buy_failure_inputs=Obs(),buy_failure_factory=lambda:Obs()))
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(61000,setup_result=1,
            buy_failure_factory=lambda:Obs(),bank_route_allowed=True))
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(61000,setup_result=1,buy_failure_factory=lambda:7))
    def test_handoff_requires_matching_parent_role_and_filename_global(self):
        child=MerchantBankRoutePlan(True,'local_route_imported',complete=True)
        parent=BuyFailurePlan(True,'bank_route_span_returned',phase_dword=0,route_plan=child)
        with self.assertRaises(ValueError):RoutePage.accept_bank_route(None,parent)
        child=replace(child,kind='BMerchant') # Deliberately wrong source-global tag.
        with self.assertRaises(ValueError):RoutePage.accept_bank_route(None,replace(parent,route_plan=child))

if __name__=='__main__':unittest.main()
