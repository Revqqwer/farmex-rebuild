import unittest
from callback_capture import parse_interlude_sample

class CallbackCaptureTests(unittest.TestCase):
    def test_empty_object_does_not_create_clock_or_initial_state(self):
        p=parse_interlude_sample('{}')
        self.assertIsNone(p.initial_state);self.assertIsNone(p.observation.tick)
        self.assertFalse(p.independently_verified)

    def test_source_values_are_preserved_without_clock_generation(self):
        p=parse_interlude_sample('{"initial_state":{"interval_dword":1000,"last_attempt_qword":0},"observation":{"tick":3000,"session_stamp_qword":0,"predicate_al":1,"flag_after_predicate":1,"final_random_return":70000}}')
        self.assertEqual(p.initial_state.interval_dword,1000)
        self.assertEqual(p.observation.final_random_return,70000)
        self.assertIsNone(p.observation.target_554218)

    def test_invalid_schema_and_duplicate_fields_are_rejected(self):
        for text in ('[]','{"initial_state":null}','{"observation":[]}',
                     '{"verified":true}','{"observation":{"native_execution_verified":true}}',
                     '{"observation":{"tick":1,"tick":2}}'):
            with self.assertRaises(ValueError):parse_interlude_sample(text)

    def test_raw_width_and_normal_return_types_are_enforced(self):
        for text in ('{"observation":{"tick":true}}','{"initial_state":{"interval_dword":-1}}',
                     '{"observation":{"predicate_al":256}}','{"observation":{"replacement_returned":1}}'):
            with self.assertRaises(ValueError):parse_interlude_sample(text)

if __name__=='__main__':unittest.main()
