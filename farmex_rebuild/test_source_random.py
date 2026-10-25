import json
import unittest
from dataclasses import replace
from source_random import SourceRandomObservation as Observation,replay_source_random
from callback_interlude import CallbackInterludeState,CallbackInterludeObservation,replay_callback_interlude
from callback_predicate import CallbackPredicateObservation,replay_callback_predicate
from callback_capture import parse_interlude_sample

class SourceRandomTests(unittest.TestCase):
    def ready(self,raw,**kwargs):return Observation(123,True,raw,**kwargs)

    def test_positive_range_includes_both_endpoints(self):
        for raw,expected in ((0,3),(17,20),(18,3),(32767,10)):
            p=replay_source_random(3,20,self.ready(raw))
            self.assertTrue(p.complete);self.assertEqual(p.result_dword,expected)
        p=replay_source_random(60000,300000,self.ready(240000))
        self.assertEqual(p.result_dword,300000)

    def test_negative_dividend_uses_truncation_toward_zero(self):
        p=replay_source_random(3,20,self.ready(0xffffffff))
        self.assertEqual((p.divisor_signed,p.quotient_signed,p.remainder_signed,p.result_dword),(18,0,-1,2))
        p=replay_source_random(0,10,self.ready(0xfffffff4))
        self.assertEqual((p.quotient_signed,p.remainder_signed,p.result_dword),(-1,-1,0xffffffff))

    def test_reversed_bounds_and_dword_wrap_are_not_rejected(self):
        p=replay_source_random(20,3,self.ready(17))
        self.assertEqual((p.divisor_signed,p.quotient_signed,p.remainder_signed,p.result_dword),(-16,-1,1,21))
        p=replay_source_random(0xfffffffe,0,self.ready(2))
        self.assertEqual((p.divisor_signed,p.result_dword),(3,0))

    def test_zero_divisor_is_fault_after_reached_crt_calls(self):
        for lower,upper in ((1,0),(0,0xffffffff)):
            p=replay_source_random(lower,upper,self.ready(0))
            self.assertFalse(p.complete);self.assertEqual(p.status,'integer_divide_by_zero')
            self.assertIsNone(p.result_dword);self.assertEqual(len(p.calls),3)

    def test_idiv_overflow_has_no_return_value(self):
        p=replay_source_random(2,0,self.ready(0x80000000))
        self.assertFalse(p.complete);self.assertEqual(p.status,'integer_divide_overflow')
        self.assertEqual(p.quotient_signed,1<<31);self.assertIsNone(p.result_dword)

    def test_missing_seed_clock_srand_return_and_rand_are_separate(self):
        p=replay_source_random(3,20,Observation(rand_eax=0))
        self.assertEqual(p.calls,(('005074da',()),));self.assertIn('GetTickCount',p.missing)
        for returned in (False,None):
            p=replay_source_random(3,20,Observation(7,returned,0))
            self.assertEqual(p.calls[-1],('00507966',(7,)));self.assertIn('srand',p.missing)
        p=replay_source_random(3,20,Observation(7,True))
        self.assertEqual(p.calls[-1],('00507942',()));self.assertIn('rand EAX',p.missing)

    def test_no_clock_or_rng_executes_and_verification_remains_false(self):
        p=replay_source_random(3,20,self.ready(17))
        self.assertEqual(p.calls,(('005074da',()),('00507966',(123,)),('00507942',())))
        self.assertFalse(p.native_execution_verified)

    def test_raw_scalar_schema_is_strict(self):
        for kwargs in ({'tick':True},{'rand_eax':-1},{'rand_eax':1<<32},{'srand_returned':1}):
            with self.assertRaises(ValueError):Observation(**kwargs)
        for lower,upper in ((True,20),(None,20),(3,-1),(3,1<<32)):
            with self.assertRaises(ValueError):replay_source_random(lower,upper,self.ready(0))

    def snapshot(self):
        return {'initial_state':{'interval_dword':0,'last_attempt_qword':0},
            'observation':{'tick':100000,'session_stamp_qword':0,
                'initial_random_inputs':{'tick':11,'srand_returned':True,'rand_eax':0},
                'session_stamp_after_random':0,'last_attempt_after_random':0,
                'predicate_inputs':{'mode_byte':1,'enabled_byte':1,'field_555dd8':0xffffffff,
                    'field_555de4':0xffffffff,'field_555ddc':0xffffffff,'field_555de0':0xffffffff,
                    'minutes_dword':0,'random_inputs':{'tick':22,'srand_returned':True,'rand_eax':2},
                    'tick':300000,'stamp_qword':0},
                'flag_after_predicate':1,
                'final_random_inputs':{'tick':33,'srand_returned':True,'rand_eax':7}}}

    def test_all_three_bound_helpers_compose_without_legacy_returns(self):
        sample=parse_interlude_sample(json.dumps(self.snapshot()))
        p=replay_callback_interlude(sample.initial_state,sample.observation)
        self.assertTrue(p.complete);self.assertEqual(p.state,CallbackInterludeState(60007,100000))
        self.assertEqual(p.initial_random_plan.result_dword,60000)
        self.assertEqual(p.predicate_plan.random_plan.result_dword,5)
        self.assertEqual(p.final_random_plan.result_dword,60007)
        seeds=[c[1][0] for c in p.calls if c[0]=='00507966']
        self.assertEqual(seeds,[11,22,33])
        self.assertEqual(len([c for c in p.calls if c[0]=='005074da']),5)
        self.assertIn((0x553d30,5,32),p.writes)

    def test_final_random_gap_keeps_caller_stamp_prospective(self):
        data=self.snapshot();data['observation']['final_random_inputs']['srand_returned']=False
        sample=parse_interlude_sample(json.dumps(data));p=replay_callback_interlude(sample.initial_state,sample.observation)
        self.assertFalse(p.complete);self.assertIn('srand',p.missing)
        self.assertEqual(p.state,CallbackInterludeState(0,0))
        self.assertEqual(p.prospective_state,CallbackInterludeState(None,100000))
        self.assertFalse(p.final_random_plan.complete)

    def test_nested_helper_cannot_reuse_legacy_return_or_caller_clock(self):
        data=self.snapshot();data['observation']['final_random_inputs'].pop('tick')
        sample=parse_interlude_sample(json.dumps(data));p=replay_callback_interlude(sample.initial_state,sample.observation)
        self.assertFalse(p.complete);self.assertEqual(p.missing,'random helper GetTickCount DWORD')
        for key in ('initial_random_return','final_random_return'):
            data=self.snapshot();data['observation'][key]=60000
            sample=parse_interlude_sample(json.dumps(data))
            with self.assertRaises(ValueError):replay_callback_interlude(sample.initial_state,sample.observation)
        data=self.snapshot();data['observation']['predicate_inputs']['random_return']=5
        sample=parse_interlude_sample(json.dumps(data))
        with self.assertRaises(ValueError):replay_callback_interlude(sample.initial_state,sample.observation)

    def test_unreached_helper_inputs_do_not_force_execution(self):
        p=replay_callback_interlude(CallbackInterludeState(),CallbackInterludeObservation(
            tick=1,session_stamp_qword=1,initial_random_return=1,initial_random_inputs=Observation()))
        self.assertTrue(p.complete);self.assertIsNone(p.initial_random_plan)
        p=replay_callback_predicate(CallbackPredicateObservation(mode_byte=1,enabled_byte=0,
            random_return=5,random_inputs=Observation()))
        self.assertTrue(p.complete);self.assertIsNone(p.random_plan)

    def test_nested_json_rejects_invalid_and_duplicate_observations(self):
        for text in ('{"observation":{"initial_random_inputs":null}}',
                     '{"observation":{"final_random_inputs":{"verified":true}}}',
                     '{"observation":{"predicate_inputs":{"random_inputs":[]}}}',
                     '{"observation":{"predicate_inputs":{"random_inputs":{"tick":1,"tick":2}}}}'):
            with self.assertRaises(ValueError):parse_interlude_sample(text)

if __name__=='__main__':unittest.main()
