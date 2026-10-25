import json,unittest
from dataclasses import replace
from merchant_sell_failure import SellFailureObservation as Obs,plan_sell_failure,parse_sell_failure,parse_bank_error_returns
from merchant_bank_route import MerchantBankRouteInputs
from operation_engine import MerchantRunner,MerchantSettings,MerchantKind,MerchantSnapshot
from route_ui import RoutePage

class SellFailureBindingTests(unittest.TestCase):
    def bank(self,**changes):
        return replace(Obs(header_span_returns=(True,True),alarm_byte=0,policy_results=(2,2,2),
            status_byte_90=0,setup_gate_byte=0,branch_span_returns=(True,True)),**changes)
    def test_route_factory_not_called_on_earlier_gap_stop_or_unavailable_branch(self):
        def fail():raise AssertionError('unreached route input')
        for o in (Obs(route_inputs_factory=fail),
            self.bank(policy_results=(0,),stop_returned=True,route_inputs_factory=fail),
            self.bank(status_byte_90=1,stop_returned=True,route_inputs_factory=fail)):
            plan_sell_failure(o)
    def test_reached_route_factory_missing_input_cannot_be_bypassed_by_receipt(self):
        calls=[]
        p=plan_sell_failure(self.bank(route_inputs_factory=lambda:calls.append(1),route_span_returned=True))
        self.assertEqual(calls,[1]);self.assertFalse(p.complete);self.assertEqual(p.phase_dword,2)
        self.assertEqual(p.prospective_phase_dword,0)
        with self.assertRaises(ValueError):plan_sell_failure(self.bank(route_inputs_factory=lambda:7))
    def test_factory_raw_conflict_is_only_reached_at_bank_route(self):
        o=Obs(route_inputs=MerchantBankRouteInputs(),route_inputs_factory=lambda:MerchantBankRouteInputs())
        self.assertFalse(plan_sell_failure(o).complete)
        with self.assertRaises(ValueError):plan_sell_failure(self.bank(route_inputs=o.route_inputs,route_inputs_factory=o.route_inputs_factory))
    def test_json_does_not_validate_unreached_tail(self):
        o=parse_sell_failure(json.dumps(dict(header_span_returns=[False,'bad'],policy_results=['bad'],bank_error_returns=7)))
        self.assertEqual(o.header_span_returns,(False,));self.assertEqual(o.policy_results,())
        raw=dict(header_span_returns=[True,True],alarm_byte=0,policy_results=[0,'bad'],
                 branch_span_returns=[True,'bad'],stop_returned=True,bank_error_returns=7)
        o=parse_sell_failure(json.dumps(raw));self.assertEqual(o.policy_results,(0,))
        self.assertEqual(plan_sell_failure(o).status,'stop_returned')
    def test_json_bank_branch_and_normal_return_are_separate(self):
        raw=dict(header_span_returns=[True,True],alarm_byte=0,policy_results=[2,2,2],status_byte_90=0,
                 setup_gate_byte=0,branch_span_returns=[True,True])
        o=parse_sell_failure(json.dumps(raw));self.assertIsNone(o.route_span_returned)
        self.assertFalse(plan_sell_failure(o).complete)
        raw['route_span_returned']=True
        self.assertEqual(plan_sell_failure(parse_sell_failure(json.dumps(raw))).status,'bank_route_span_returned')
        # Detailed bound input remains an independent, non-bypassable gate.
        o=replace(parse_sell_failure(json.dumps(raw)),route_inputs_factory=lambda:MerchantBankRouteInputs())
        self.assertFalse(plan_sell_failure(o).complete)
    def test_reached_json_types_and_bank_error_receipts_are_strict(self):
        for raw in ({'unknown':1},{'route_inputs':{}},{'header_span_returns':[1]}):
            with self.assertRaises(ValueError):parse_sell_failure(json.dumps(raw))
        for raw in ([],{'bank_error_returns':7},{'bank_error_returns':{'error_stop_returned':1}},
                    {'bank_error_returns':{'unknown':True}}):
            with self.assertRaises(ValueError):parse_bank_error_returns(json.dumps(raw))
        self.assertEqual(parse_bank_error_returns('{"bank_error_returns":{"error_stop_returned":false}}'),{'error_stop_returned':False})
    def test_outer_factory_only_runs_after_delay_and_failed_setup(self):
        calls=[]
        def factory():calls.append(1);return Obs()
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=2
        self.assertEqual(r.tick(MerchantSnapshot(1,setup_result=1,sell_failure_factory=factory)).status,'waiting')
        r.tick(MerchantSnapshot(61000,setup_result=0,sell_failure_factory=factory));self.assertEqual(calls,[])
        d=r.tick(MerchantSnapshot(61001,setup_result=1,sell_failure_factory=factory))
        self.assertEqual(d.status,'needs_adapter');self.assertEqual(calls,[1])
    def test_outer_raw_factory_and_legacy_bank_gate_conflicts_cannot_override_bound_input(self):
        r=MerchantRunner(MerchantSettings(kind=MerchantKind.SELL));r.start();r.phase=2
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(61000,setup_result=1,sell_failure_inputs=Obs(),sell_failure_factory=lambda:Obs()))
        with self.assertRaises(ValueError):r.tick(MerchantSnapshot(61000,setup_result=1,sell_failure_factory=lambda:Obs(),bank_route_allowed=True))
    def test_route_handoff_rejects_bare_import_and_incomplete_or_wrong_parent(self):
        for plan in (MerchantBankRouteInputs(),plan_sell_failure(Obs()),
                     replace(plan_sell_failure(Obs()),complete=True,status='stop_returned',phase_dword=0)):
            with self.assertRaises(ValueError):RoutePage.accept_bank_route(None,plan)

if __name__=='__main__':unittest.main()
