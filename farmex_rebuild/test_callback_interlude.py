import unittest
from dataclasses import replace
from callback_interlude import *

class CallbackInterludeTests(unittest.TestCase):
    def plan(self,state=None,observation=None,**changes):
        o=observation or CallbackInterludeObservation(20000,0,predicate_al=1,
            flag_after_predicate=1,final_random_return=70000)
        return replay_callback_interlude(state or CallbackInterludeState(10000,0),replace(o,**changes))

    def test_zero_delta_skips_unknown_interval_and_helpers(self):
        p=self.plan(CallbackInterludeState(),tick=1,session_stamp_qword=1)
        self.assertTrue(p.complete);self.assertEqual(p.status,'session_delta_zero')
        self.assertEqual(p.calls,(('005074da',()),));self.assertEqual(p.writes,())

    def test_session_interval_is_strict_and_last_attempt_inclusive(self):
        p=self.plan(tick=10000)
        self.assertTrue(p.complete);self.assertEqual(p.status,'session_interval_wait')
        p=self.plan(CallbackInterludeState(10000,10000))
        self.assertEqual(p.status,'interlude_return_planned')
        self.assertEqual(p.state,CallbackInterludeState(70000,20000))
        p=self.plan(CallbackInterludeState(10000,10001))
        self.assertEqual(p.status,'attempt_interval_wait')

    def test_signed_qword_delta_does_not_use_dword_wrap(self):
        p=self.plan(tick=0x10,session_stamp_qword=0xfffffff0)
        self.assertEqual(p.status,'session_interval_wait')
        p=self.plan(CallbackInterludeState(0xffffffff,0),tick=1)
        self.assertEqual(p.status,'interlude_return_planned') # sign-extended interval=-1
        p=self.plan(tick=1,session_stamp_qword=0xffffffffffffffff)
        self.assertEqual(p.status,'session_interval_wait') # modular64 delta=2

    def test_initial_random_requires_fresh_session_and_attempt_samples(self):
        s=CallbackInterludeState(0,0)
        p=self.plan(s);self.assertFalse(p.complete)
        self.assertEqual(p.calls[-1],('00467cc4',(60000,300000)))
        p=self.plan(s,initial_random_return=10000)
        self.assertEqual(p.missing,'fresh005620a4 after initial random helper')
        self.assertEqual(p.prospective_state.interval_dword,10000)
        p=self.plan(s,initial_random_return=10000,session_stamp_after_random=0)
        self.assertIn('005620d4',p.missing)
        p=self.plan(s,initial_random_return=10000,session_stamp_after_random=0,last_attempt_after_random=0)
        self.assertTrue(p.complete);self.assertEqual(len([c for c in p.calls if c[0]=='00467cc4']),2)

    def test_initial_random_known_write_can_precede_early_wait(self):
        p=self.plan(CallbackInterludeState(0,9),initial_random_return=300000,session_stamp_after_random=0)
        self.assertTrue(p.complete);self.assertEqual(p.status,'session_interval_wait')
        self.assertEqual(p.state,CallbackInterludeState(300000,None))
        self.assertEqual(p.writes,((0x5620cc,300000,32),))

    def test_predicate_al_and_fresh_flag_have_separate_reachability(self):
        p=self.plan(predicate_al=2,flag_after_predicate=None)
        self.assertFalse(p.complete);self.assertEqual(p.missing,'fresh00555e23 BYTE')
        p=self.plan(predicate_al=0,flag_after_predicate=None,target_554218=123,replacement_returned=True)
        self.assertTrue(p.complete)
        self.assertIn(('0046b8fc',(0x554228,123,0x46eca8)),p.calls)
        self.assertFalse(p.native_execution_verified)

    def test_pointer_helper_must_return_before_stamp_and_new_random(self):
        for returned in (None,False):
            p=self.plan(predicate_al=1,flag_after_predicate=0,target_554218=123,replacement_returned=returned)
            self.assertFalse(p.complete);self.assertEqual(p.missing,'0046b8fc normal return')
            self.assertEqual(p.writes,());self.assertEqual(p.state,CallbackInterludeState(10000,0))

    def test_final_random_gap_preserves_known_stamp_only_in_prospective_state(self):
        p=self.plan(final_random_return=None)
        self.assertFalse(p.complete);self.assertEqual(p.state,CallbackInterludeState(10000,0))
        self.assertEqual(p.prospective_state,CallbackInterludeState(None,20000))
        self.assertEqual(p.writes,((0x5620d4,20000,32),(0x5620d8,0,32)))

    def test_missing_clock_or_unknown_global_cannot_complete(self):
        for o in (CallbackInterludeObservation(),CallbackInterludeObservation(tick=1)):
            self.assertFalse(self.plan(observation=o).complete)
        self.assertEqual(self.plan(CallbackInterludeState()).missing,'005620cc DWORD')

    def test_raw_source_widths_are_enforced(self):
        for kw in ({'tick':True},{'tick':-1},{'predicate_al':256},{'session_stamp_qword':1<<64},
                   {'replacement_returned':1}):
            with self.assertRaises(ValueError):CallbackInterludeObservation(**kw)
        with self.assertRaises(ValueError):CallbackInterludeState(1<<32,0)

if __name__=='__main__':unittest.main()
