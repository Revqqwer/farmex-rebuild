import json,unittest
from dataclasses import replace
from crt_rng import replay_crt_rand_step,replay_crt_seeded_pair,CRT_SOURCE_SHA256
from source_random import SourceRandomObservation,replay_source_random
from callback_capture import parse_interlude_sample
from callback_interlude import replay_callback_interlude

class CrtRngTests(unittest.TestCase):
    def test_seeded_vectors_include_discarded_warmup(self):
        for seed,warmup,state,output in ((0,0,22695478,346),(1,346,2156045615,130),
                                         (0xffffffff,32421,2184312637,561)):
            p=replay_crt_seeded_pair(seed)
            self.assertEqual((p.warmup.result_eax,p.output.seed_after,p.output.result_eax),(warmup,state,output))
            self.assertEqual(p.thread_auxiliary_dword_after,0)

    def test_multiply_wrap_and_shift_mask_bound_output(self):
        p=replay_crt_rand_step(0xffffffff)
        self.assertEqual((p.seed_after,p.result_eax),(4272271820,32421))
        for seed in (0,1,0x7fffffff,0x80000000,0xffffffff):
            p=replay_crt_seeded_pair(seed)
            self.assertTrue(0<=p.output.result_eax<=32767)

    def test_seed_type_is_explicit_raw_dword(self):
        for seed in (True,None,-1,1<<32,1.0):
            with self.assertRaises(ValueError):replay_crt_seeded_pair(seed)

    def observation(self,**kwargs):
        return replace(SourceRandomObservation(tick=0,srand_returned=True,
            disk_crt_replay=True,same_thread_context=True),**kwargs)

    def test_source_helper_replay_has_distinct_provenance(self):
        p=replay_source_random(60000,300000,self.observation())
        self.assertTrue(p.complete);self.assertEqual(p.result_dword,60346)
        self.assertEqual(p.rand_source,'local_disk_crt_replay')
        self.assertEqual(p.crt_replay.source_sha256,CRT_SOURCE_SHA256)
        self.assertFalse(p.crt_replay.loaded_game_runtime_verified)
        self.assertFalse(p.native_execution_verified)

    def test_unknown_thread_contract_or_normal_return_holds(self):
        for contract in (None,False):
            p=replay_source_random(3,20,self.observation(same_thread_context=contract))
            self.assertFalse(p.complete);self.assertIn('stable thread',p.missing)
            self.assertIsNone(p.crt_replay)
        p=replay_source_random(3,20,self.observation(srand_returned=False))
        self.assertFalse(p.complete);self.assertIn('srand normal return',p.missing)

    def test_observed_rand_conflict_is_rejected_only_when_reached(self):
        with self.assertRaises(ValueError):replay_source_random(3,20,self.observation(rand_eax=0))
        p=replay_source_random(3,20,self.observation(tick=None,rand_eax=0))
        self.assertFalse(p.complete);self.assertIn('GetTickCount',p.missing)

    def test_replay_options_have_strict_boolean_types(self):
        for kwargs in ({'disk_crt_replay':1},{'disk_crt_replay':None},{'same_thread_context':1}):
            with self.assertRaises(ValueError):SourceRandomObservation(**kwargs)

    def test_json_binding_does_not_need_observed_rand_eax(self):
        sample=parse_interlude_sample(json.dumps({'initial_state':{'interval_dword':1000,'last_attempt_qword':0},
            'observation':{'tick':3000,'session_stamp_qword':0,'predicate_al':1,'flag_after_predicate':1,
            'final_random_inputs':{'tick':0,'srand_returned':True,'disk_crt_replay':True,'same_thread_context':True}}}))
        p=replay_callback_interlude(sample.initial_state,sample.observation)
        self.assertTrue(p.complete);self.assertEqual(p.state.interval_dword,60346)
        self.assertEqual(p.final_random_plan.rand_source,'local_disk_crt_replay')

    def test_file_rng_range_is_narrower_than_arithmetic_bounds(self):
        for seed in range(0,1<<32,0x1000001):
            p=replay_source_random(60000,300000,self.observation(tick=seed))
            self.assertTrue(p.complete);self.assertTrue(60000<=p.result_dword<=92767)

if __name__=='__main__':unittest.main()
