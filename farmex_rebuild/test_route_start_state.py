import unittest,tempfile
from pathlib import Path
from dataclasses import replace
from route_start_state import RouteStartState as State,RouteStartObservation as Obs,RouteStartFrame
from merchant_bank_route import MerchantBankRouteInputs,plan_merchant_bank_route
from name_codec import WindowsNameCodec

class RouteStartStateTests(unittest.TestCase):
    def entry(self):return State({0x88:1,0x544:17,0x5d9:255,0x618:99,0x654:99},{0x561f6c:1,7:9})
    def test_first_helper_precedes_global_resets_and_second_helper(self):
        f=RouteStartFrame(self.entry());p=f.step()
        self.assertFalse(p.complete);self.assertEqual(p.writes,());self.assertEqual(len(p.steps),1)
        p=f.step(Obs(first_helper_returned=True))
        self.assertEqual(p.prospective_state.globals[0x561f6c],0)
        self.assertEqual(p.prospective_state.fields[0x618],99)
        self.assertEqual(p.steps[-1],('00464714',))
    def test_object_resets_precede_clock_and_preserve_unwritten_fields(self):
        f=RouteStartFrame(self.entry());p=f.step(Obs(True,True))
        self.assertFalse(p.complete);s=p.prospective_state
        self.assertEqual((s.fields[0x618],s.fields[0x654]),(14,13))
        self.assertEqual((s.fields[0x5ec],s.fields[0x690]),(0xffffffff,0xffffffff))
        self.assertEqual(s.fields[0x544],17);self.assertEqual(s.globals[7],9)
        self.assertEqual(s.fields[0x5d9],0);self.assertEqual(p.steps[-1],('GetTickCount',))
    def test_tick_is_zero_extended_then_fresh_count_then_active(self):
        f=RouteStartFrame(self.entry());p=f.step(Obs(True,True,0xffffffff))
        self.assertFalse(p.complete);self.assertEqual(p.prospective_state.fields[0x5e0],0xffffffff)
        self.assertEqual(p.prospective_state.fields[0x5e4],0);self.assertEqual(p.prospective_state.fields[0x5d9],0)
        p=f.step(Obs(count_dword=2));self.assertTrue(p.complete)
        self.assertEqual((p.state.fields[0x5f0],p.state.fields[0x5d9]),(2,1))
        self.assertEqual(p.writes[-2:],(('object',0x5f0,4,2),('object',0x5d9,1,1)))
    def test_repeated_gap_does_not_repeat_resets_and_known_tick_is_frozen(self):
        f=RouteStartFrame(self.entry());p=f.step(Obs(True,True,123))
        self.assertEqual(f.step().writes,p.writes)
        with self.assertRaises(ValueError):f.step(Obs(tick_dword=124))
        d=f.step(Obs(count_dword=1));self.assertEqual(f.step(),d)
    def test_zero_count_still_sets_active_in_source_helper(self):
        p=RouteStartFrame(State()).step(Obs(True,True,0,0))
        self.assertTrue(p.complete);self.assertEqual(p.state.fields[0x5d9],1);self.assertEqual(p.state.fields[0x5f0],0)
    def test_bound_import_needs_prestart_span_and_complete_start(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory,'bank.R').write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=Bekle\nSub10=0\n')
            c=WindowsNameCodec(1254);f=RouteStartFrame(self.entry());d=f.step()
            o=MerchantBankRouteInputs(b'bank.R',c.encode(directory+'\\')[0],c,start_execution=d)
            p=plan_merchant_bank_route(o);self.assertTrue(p.ready);self.assertFalse(p.complete)
            p=plan_merchant_bank_route(replace(o,prestart_span_returned=True));self.assertFalse(p.complete)
            done=f.step(Obs(True,True,100,1))
            p=plan_merchant_bank_route(replace(o,prestart_span_returned=True,start_execution=done))
            self.assertTrue(p.ready and p.complete);self.assertEqual(p.status,'local_route_start_modeled')
    def test_bound_count_mismatch_and_fresh_change_are_distinct(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory,'bank.R').write_bytes(b'[Count]\nValue=1\n[ROUTE]\nISLEM0=Bekle\nSub10=0\n')
            c=WindowsNameCodec(1254)
            o=MerchantBankRouteInputs(b'bank.R',c.encode(directory+'\\')[0],c,prestart_span_returned=True)
            d=RouteStartFrame(State({0x88:2})).step(Obs(True,True,1,2))
            with self.assertRaises(ValueError):plan_merchant_bank_route(replace(o,start_execution=d))
            d=RouteStartFrame(self.entry()).step(Obs(True,True,1,2))
            p=plan_merchant_bank_route(replace(o,start_execution=d));self.assertFalse(p.complete)
            self.assertIn('changed',p.missing)
    def test_types_and_immutable_own_state(self):
        with self.assertRaises(ValueError):Obs(tick_dword=True)
        with self.assertRaises(ValueError):State({0x5d9:256})
        with self.assertRaises(TypeError):self.entry().fields[0x88]=2
        with self.assertRaises(ValueError):MerchantBankRouteInputs(start_execution=0)

if __name__=='__main__':unittest.main()
