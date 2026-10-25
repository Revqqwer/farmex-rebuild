import unittest
from dataclasses import replace
from merchant_callback import MerchantCallbackObservation as Obs,plan_merchant_callback as plan,tick_merchant_callback
from operation_engine import MerchantRunner,MerchantSettings,MerchantKind,MerchantSnapshot
from route_start_state import RouteStartState,RouteStartObservation,RouteStartFrame

class MerchantCallbackTests(unittest.TestCase):
    def sample(self,**kw):return replace(Obs(1,0,0,None,1,1,(1,)),**kw)
    def runner(self,kind=MerchantKind.SELL):
        r=MerchantRunner(MerchantSettings(kind=kind));r.start();return r
    def test_first_gates_skip_unreached_fields(self):
        self.assertEqual(plan(Obs(entry_master_byte=0)).status,'entry_disabled')
        self.assertEqual(plan(Obs(entry_master_byte=1,lock_byte=255)).status,'locked')
    def test_route_helper_return_precedes_fresh_flags(self):
        o=self.sample(route_pending_byte=1,post_master_byte=0)
        p=plan(o);self.assertFalse(p.complete);self.assertEqual(p.steps[-1],('004eb2c4',0x5687a8))
        p=plan(replace(o,route_helper_returned=True));self.assertEqual(p.status,'post_route_disabled')
    def test_post_flags_are_fresh_even_without_route_call(self):
        for field in ('post_master_byte','post_enable_byte'):
            self.assertFalse(plan(self.sample(**{field:None})).complete)
        self.assertEqual(plan(self.sample(post_enable_byte=0,mode_results=())).status,'merchant_disabled')
    def test_mode_is_reread_when_sell_comparison_fails(self):
        self.assertEqual(plan(self.sample(mode_results=(1,))).selected_kind,'sell')
        self.assertFalse(plan(self.sample(mode_results=(2,))).complete)
        self.assertEqual(plan(self.sample(mode_results=(0,2))).selected_kind,'buy')
        self.assertEqual(plan(self.sample(mode_results=(2,1))).status,'unhandled_mode')
    def test_skip_does_not_evaluate_snapshot_factory_or_tick_runner(self):
        r=self.runner()
        def unreachable():raise AssertionError('unreached snapshot was evaluated')
        d=tick_merchant_callback(r,Obs(entry_master_byte=0),unreachable)
        self.assertEqual(d.status,'callback_skipped');self.assertEqual((r.phase,r.last_tick),(0,0))
    def test_selected_callback_evaluates_once_and_uses_bound_runner(self):
        r=self.runner();calls=[]
        def snapshot():calls.append(1);return MerchantSnapshot(10,currently_open=False)
        d=tick_merchant_callback(r,self.sample(),snapshot)
        self.assertEqual(d.status,'callback_modeled');self.assertEqual(d.operation.status,'phase_changed')
        self.assertEqual((len(calls),r.phase),(1,1));self.assertFalse(d.native_execution_verified)
    def test_route_start_enable_clear_suppresses_merchant_until_fresh_enable(self):
        start=RouteStartFrame(RouteStartState({0x88:1})).step(RouteStartObservation(True,True,100,1))
        r=self.runner();o=self.sample(post_enable_byte=start.state.globals[0x561f6c])
        d=tick_merchant_callback(r,o);self.assertEqual(d.status,'callback_skipped');self.assertEqual(r.phase,0)
        d=tick_merchant_callback(r,replace(o,post_enable_byte=1),MerchantSnapshot(101,currently_open=False))
        self.assertEqual(d.status,'callback_modeled');self.assertEqual(r.phase,1)
    def test_missing_snapshot_and_wrong_kind_are_not_success(self):
        r=self.runner();self.assertEqual(tick_merchant_callback(r,self.sample()).status,'needs_adapter')
        with self.assertRaises(ValueError):tick_merchant_callback(r,self.sample(mode_results=(2,2)))
        r=self.runner(MerchantKind.BUY)
        d=tick_merchant_callback(r,self.sample(mode_results=(2,2)),MerchantSnapshot(1,currently_open=False))
        self.assertEqual(d.status,'callback_modeled')
    def test_types(self):
        with self.assertRaises(ValueError):Obs(entry_master_byte=True)
        with self.assertRaises(ValueError):Obs(mode_results=(True,))
        with self.assertRaises(ValueError):Obs(route_helper_returned=1)
        with self.assertRaises(ValueError):tick_merchant_callback(self.runner(),self.sample(),lambda:None)

if __name__=='__main__':unittest.main()
