import unittest,struct
from native_ipc import MAGIC,mapping_name,decode_frame

class NativeFrameTests(unittest.TestCase):
    def frame(self,changes=None):
        words=[MAGIC,1,84,2,123,1,52,0,1,52,0,0,24,123,1000,1,0,250,500,100,300]
        for index,value in (changes or {}).items():words[index]=value
        return struct.pack('<21I',*words)
    def decode(self,changes=None,**args):
        opts=dict(expected_pid=123,expected_profile=1,expected_source=1,now_tick=1000)
        opts.update(args)
        return decode_frame(self.frame(changes),2,2,**opts)

    def test_fixture_candidate_has_no_independent_verification(self):
        r=self.decode();self.assertEqual(r.status,'fixture_candidate');self.assertFalse(r.independently_verified)
        self.assertEqual(dict(r.fields),{'hp':250,'hp_max':500,'mp':100,'mp_max':300})

    def test_game_origin_remains_candidate_unverified(self):
        r=self.decode({5:2},expected_source=2)
        self.assertEqual(r.status,'candidate_unverified');self.assertFalse(r.independently_verified)

    def test_fixture_cannot_satisfy_game_origin_expectation(self):
        self.assertEqual(self.decode(expected_source=2).status,'origin_mismatch')

    def test_sequence_zero_odd_or_torn_is_updating(self):
        for before,inside,after in ((0,0,0),(3,3,3),(2,2,4),(2,4,2)):
            r=decode_frame(self.frame({3:inside}),before,after,expected_pid=123,expected_profile=1,expected_source=1,now_tick=1000)
            self.assertEqual(r.status,'updating')

    def test_header_magic_abi_size_reserved_and_payload_size(self):
        for index,value in ((0,0),(1,2),(2,85),(6,51),(7,1)):
            self.assertEqual(self.decode({index:value}).status,'invalid_frame')

    def test_declared_pid_mismatch_in_either_header_or_payload(self):
        for index in (4,13):self.assertEqual(self.decode({index:124}).status,'identity_mismatch')

    def test_profile_mismatch(self):self.assertEqual(self.decode({15:2}).status,'profile_mismatch')

    def test_sample_age_and_tick_wrap(self):
        self.assertEqual(self.decode(now_tick=2000).status,'fixture_candidate')
        self.assertEqual(self.decode(now_tick=2001).status,'stale')
        self.assertEqual(self.decode({14:0xfffffff0},now_tick=32).status,'fixture_candidate')

    def test_candidate_bytecount_error_stage_or_invalid_vitals(self):
        for index,value in ((12,0),(11,5),(16,1),(17,501),(18,0),(8,2),(9,51),(10,10)):
            self.assertEqual(self.decode({index:value}).status,'invalid_frame')

    def test_native_read_error_is_zero_data_and_retains_diagnostics(self):
        r=self.decode({10:3,11:998,12:0,16:1,17:0,18:0,19:0,20:0})
        self.assertEqual(r.status,'native_error');self.assertEqual(r.fields,{})
        self.assertEqual((r.win_error,r.failed_step),(998,1))

    def test_error_payload_leak_rejected(self):self.assertEqual(self.decode({10:3}).status,'invalid_frame')

    def test_frame_length_and_raw_argument_validation(self):
        for data in (b'',self.frame()+b'x'):
            self.assertEqual(decode_frame(data,2,2,expected_pid=123,expected_profile=1,expected_source=1,now_tick=1000).status,'invalid_frame')
        with self.assertRaises(ValueError):self.decode(expected_profile=True)
        with self.assertRaises(ValueError):self.decode(expected_source=True)
        with self.assertRaises(ValueError):self.decode(now_tick=-1)

    def test_mapping_name_exact_pid_lowercase_nonce_and_namespace(self):
        self.assertEqual(mapping_name(123,'a'*32),'Local\\FarmexVitals.123.'+'a'*32)
        for pid,nonce in ((0,'a'*32),(True,'a'*32),(123,'A'*32),(123,'a'*31)):
            with self.assertRaises(ValueError):mapping_name(pid,nonce)
