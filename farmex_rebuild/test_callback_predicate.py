import unittest
from dataclasses import replace
from callback_predicate import CallbackPredicateObservation as Observation,replay_callback_predicate
from callback_capture import parse_interlude_sample
from callback_interlude import CallbackInterludeState,CallbackInterludeObservation,replay_callback_interlude

class CallbackPredicateTests(unittest.TestCase):
    def enabled(self,**kwargs):
        return replace(Observation(1,1,0xffffffff,0xffffffff,0xffffffff,0xffffffff,
                                   3,None,180000,0),**kwargs)

    def test_fixed_threshold_equality_and_signed_qword_delta(self):
        for tick,stamp,expected in ((300000,0,1),(300001,0,0),(0,1,1),
                                    (0x10,0xfffffff0,1),(1,0xffffffffffffffff,1)):
            p=replay_callback_predicate(Observation(mode_byte=0,tick=tick,stamp_qword=stamp))
            self.assertTrue(p.complete);self.assertEqual(p.al,expected)
            self.assertEqual(p.writes,((0x555e23,1,8),) if expected else ())

    def test_each_precondition_short_circuits_later_unknown_fields(self):
        cases=(Observation(mode_byte=1,enabled_byte=0),
               Observation(mode_byte=1,enabled_byte=1,field_555dd8=0),
               Observation(1,1,0xffffffff,0),Observation(1,1,0xffffffff,0xffffffff,0),
               Observation(1,1,0xffffffff,0xffffffff,0xffffffff,0x7fffffff))
        for o in cases:
            p=replay_callback_predicate(o)
            self.assertTrue(p.complete);self.assertEqual(p.al,0)
            self.assertEqual((p.calls,p.writes),((),()))

    def test_minutes_threshold_boundary_and_raw_multiply_overflow(self):
        for minutes,tick,stamp,expected in ((3,180000,0,1),(3,180001,0,0),
                (0x10000000,0,0,1),(35792,0,0,0),(0xffffffff,0,60000,1),
                (0xffffffff,0,59999,0)):
            p=replay_callback_predicate(self.enabled(minutes_dword=minutes,tick=tick,stamp_qword=stamp))
            self.assertTrue(p.complete);self.assertEqual(p.al,expected)

    def test_random_store_precedes_missing_independent_clock(self):
        o=self.enabled(minutes_dword=0,random_return=5,tick=None)
        p=replay_callback_predicate(o)
        self.assertFalse(p.complete);self.assertIsNone(p.al)
        self.assertEqual(p.writes,((0x553d30,5,32),))
        self.assertEqual(p.calls,(('00467cc4',(3,20)),('005074da',())))
        self.assertEqual(p.minutes_dword_after,5)
        p=replay_callback_predicate(replace(o,random_return=None))
        self.assertFalse(p.complete);self.assertEqual(p.writes,())
        self.assertEqual(p.calls,(('00467cc4',(3,20)),))

    def test_missing_mode_or_reached_field_never_invents_return(self):
        for o in (Observation(),Observation(mode_byte=1),Observation(1,1),
                  Observation(mode_byte=0,tick=1)):
            p=replay_callback_predicate(o)
            self.assertFalse(p.complete);self.assertIsNone(p.al)
            self.assertFalse(p.native_execution_verified)

    def test_bound_interlude_cannot_use_caller_clock_or_legacy_al(self):
        state=CallbackInterludeState(1000,0)
        o=CallbackInterludeObservation(tick=3000,session_stamp_qword=0,
            predicate_inputs=Observation(mode_byte=0),flag_after_predicate=1,final_random_return=70000)
        p=replay_callback_interlude(state,o)
        self.assertFalse(p.complete);self.assertEqual(p.missing,'predicate GetTickCount DWORD')
        with self.assertRaises(ValueError):replay_callback_interlude(state,replace(o,predicate_al=1))
        p=replay_callback_interlude(state,replace(o,predicate_inputs=Observation(mode_byte=0,tick=300000,stamp_qword=0)))
        self.assertTrue(p.complete);self.assertEqual(p.predicate_plan.al,1)
        self.assertIn((0x555e23,1,8),p.writes)
        self.assertEqual(p.state,CallbackInterludeState(70000,3000))

    def test_caller_still_requires_fresh_flag_and_replacement_return(self):
        s=CallbackInterludeState(1000,0)
        o=CallbackInterludeObservation(tick=3000,session_stamp_qword=0,
            predicate_inputs=Observation(mode_byte=0,tick=1,stamp_qword=0))
        p=replay_callback_interlude(s,o)
        self.assertFalse(p.complete);self.assertEqual(p.missing,'fresh00555e23 BYTE')
        self.assertEqual(p.writes,((0x555e23,1,8),));self.assertEqual(p.state,s)
        p=replay_callback_interlude(s,replace(o,predicate_inputs=Observation(mode_byte=0,tick=300001,stamp_qword=0),
            target_554218=7,replacement_returned=False))
        self.assertFalse(p.complete);self.assertEqual(p.missing,'0046b8fc normal return')

    def test_json_nested_snapshot_and_schema_rejection(self):
        sample=parse_interlude_sample('{"observation":{"predicate_inputs":{"mode_byte":0,"tick":1,"stamp_qword":0}}}')
        self.assertEqual(sample.observation.predicate_inputs,Observation(mode_byte=0,tick=1,stamp_qword=0))
        for text in ('{"observation":{"predicate_inputs":null}}',
                     '{"observation":{"predicate_inputs":{"mode_byte":0,"mode_byte":1}}}',
                     '{"observation":{"predicate_inputs":{"verified":true}}}'):
            with self.assertRaises(ValueError):parse_interlude_sample(text)

    def test_source_widths_and_types_are_validated(self):
        for kwargs in ({'mode_byte':True},{'enabled_byte':256},{'tick':-1},
                       {'minutes_dword':1<<32},{'stamp_qword':1<<64},{'field_555dd8':-1}):
            with self.assertRaises(ValueError):Observation(**kwargs)

if __name__=='__main__':unittest.main()
