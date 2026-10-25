import unittest
from source_coin import GuardedByteSample as Byte,GuardedDwordSample as Word,plan_guarded_byte
from route_resume import RouteResumeState as State,RouteResumeObservation as Obs,plan_route_resume as plan
from merchant_callback import MerchantCallbackObservation,tick_merchant_callback
from operation_engine import MerchantRunner,MerchantSettings,MerchantSnapshot
from route_start_state import RouteStartState,RouteStartObservation,RouteStartFrame

class RouteResumeTests(unittest.TestCase):
    def sample(self,value=0,ret=1):
        return Obs(((0x553e7c,1),(0x554020,0x20)),Word(1,1,0x100),Byte(0x120,ret,value))
    def test_byte_helper_retains_upper_api_eax_bits(self):
        p=plan_guarded_byte(7,Byte(7,0xabcdef01,2))
        self.assertTrue(p.complete);self.assertEqual(p.eax_dword,0xabcdef02);self.assertEqual(p.value_byte,2)
        self.assertEqual(p.steps[0],('VirtualProtect_plan',7,1,0x40))
    def test_null_failure_and_observed_zero_have_distinct_provenance(self):
        a=plan_guarded_byte(0);b=plan_guarded_byte(7,Byte(7,0));c=plan_guarded_byte(7,Byte(7,1,0))
        self.assertEqual((a.eax_dword,b.eax_dword,c.eax_dword),(0,0,0))
        self.assertEqual(len({a.status,b.status,c.status}),3);self.assertIsNone(b.value_byte)
    def test_missing_api_or_byte_does_not_become_zero(self):
        self.assertFalse(plan_guarded_byte(7).complete)
        self.assertFalse(plan_guarded_byte(7,Byte(7,1)).complete)
    def test_tail_tests_al_not_full_eax_and_writes_in_order(self):
        p=plan(State(1,0),self.sample(0,0x100))
        self.assertTrue(p.complete);self.assertEqual(p.byte_plan.eax_dword,0x100)
        self.assertEqual(p.state,State(0,1))
        self.assertEqual(p.writes,(('object',0x5d9,1,0),('global',0x561f6c,1,1)))
    def test_nonzero_al_preserves_both_existing_bytes(self):
        p=plan(State(255,1),self.sample(2))
        self.assertEqual(p.status,'no_tail_writes');self.assertEqual(p.state,State(255,1));self.assertEqual(p.writes,())
    def test_zero_root_still_reaches_offset_byte_read(self):
        o=Obs(((0x553e7c,1),(0x554020,0x20)),Word(1,0),Byte(0x20,1,0))
        p=plan(State(1,0),o);self.assertTrue(p.complete);self.assertEqual(p.state.enable_byte,1)
        self.assertEqual(p.root_plan.status,'protection_failure_returns_zero')
    def test_wrapped_null_byte_and_failure_al_zero_follow_source_branch(self):
        p=plan(State(1,0),Obs(((0x553e7c,1),(0x554020,0x10)),Word(1,1,0xfffffff0)))
        self.assertTrue(p.complete);self.assertEqual(p.byte_plan.status,'null_returns_zero')
        o=Obs(((0x553e7c,0),(0x554020,7)),byte_sample=Byte(7,0))
        p=plan(State(1,0),o);self.assertEqual(p.state,State(0,1))
        self.assertEqual(p.byte_plan.status,'protection_failure_returns_zero')
    def test_gaps_do_not_resume_and_addresses_must_match(self):
        p=plan(State(1,0),Obs());self.assertFalse(p.complete);self.assertEqual(p.state,State(1,0))
        with self.assertRaises(ValueError):plan(State(1,0),Obs(((0x553e7c,1),),Word(2,1,0)))
    def test_start_clear_then_tail_enable_can_feed_fresh_callback(self):
        started=RouteStartFrame(RouteStartState({0x88:1})).step(RouteStartObservation(True,True,100,1))
        entry=State(started.state.fields[0x5d9],started.state.globals[0x561f6c])
        tail=plan(entry,self.sample(0));self.assertTrue(tail.complete)
        r=MerchantRunner(MerchantSettings());r.start()
        # Explicit reached-tail and normal outer route-return fixtures; no automatic completion detection.
        o=MerchantCallbackObservation(1,0,1,True,1,tail.state.enable_byte,(1,))
        d=tick_merchant_callback(r,o,MerchantSnapshot(101,currently_open=False))
        self.assertEqual(d.status,'callback_modeled');self.assertEqual(r.phase,1)
    def test_types(self):
        with self.assertRaises(ValueError):Byte(1,1,256)
        with self.assertRaises(ValueError):State(True,0)
        with self.assertRaises(ValueError):plan_guarded_byte(1,Byte(2,1,0))

if __name__=='__main__':unittest.main()
