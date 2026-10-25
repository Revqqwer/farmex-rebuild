import unittest
from unittest.mock import patch, MagicMock
from native_ipc import NativeVitalsProvider, NativeIpcResult
from session import Session, Source, observation_snapshot


class NativeProviderTests(unittest.TestCase):
    def observe(self, result, **options):
        with patch('native_ipc.ReadOnlyNativeMap') as mapping:
            mapping.return_value.__enter__.return_value.read.return_value = result
            provider = NativeVitalsProvider(123, 'a'*32, **options)
            observation = provider.observe(123)
            mapping.assert_called_once_with(123, 'a'*32, profile=2 if options.get('profile') == 'steam' else 1,
                                           source_kind=options.get('source_kind', 2))
            mapping.return_value.__enter__.return_value.read.assert_called_once_with(
                max_age_ms=options.get('max_age_ms', 1000))
            mapping.return_value.__exit__.assert_called_once()
            return observation

    def test_game_candidate_cannot_start_live_session(self):
        fields = dict(hp=250, hp_max=500, mp=100, mp_max=300)
        observation = self.observe(NativeIpcResult('candidate_unverified', fields, pid=123))
        self.assertEqual(observation.fields, fields)
        self.assertFalse(observation.independently_verified)
        self.assertEqual((observation.image_sha256, observation.bytes_read), ('', 0))
        session = Session('ipc', Source.LIVE)
        session.accept_snapshot(observation_snapshot(observation, 'ipc'))
        self.assertEqual(session.start(observation.timestamp_ms, ('hp',)), 'needs_verification')

    def test_fixture_is_displayable_but_not_a_live_snapshot(self):
        observation = self.observe(NativeIpcResult('fixture_candidate', {'hp': 250}), source_kind=1)
        self.assertEqual(observation.status, 'fixture_candidate')
        self.assertIsNone(observation_snapshot(observation, 'ipc'))

    def test_errors_and_stale_frames_have_no_fields(self):
        for status in ('stale', 'updating', 'identity_mismatch', 'origin_mismatch', 'invalid_frame'):
            observation = self.observe(NativeIpcResult(status, error='Rejected frame'))
            self.assertEqual(observation.status, status)
            self.assertEqual(observation.fields, {})
            self.assertIsNone(observation_snapshot(observation, 'ipc'))

    def test_native_diagnostic_keeps_winerror_and_stage(self):
        observation = self.observe(NativeIpcResult('native_error', native_status=3, win_error=998, failed_step=1))
        self.assertEqual(observation.error_code, 998)
        self.assertIn('aşama 1', observation.error)
        self.assertEqual(observation.failed_operation, 'ReadNativeFrame')

    def test_mapping_open_failure_is_an_observation(self):
        with patch('native_ipc.ReadOnlyNativeMap', side_effect=OSError('Missing mapping')):
            observation = NativeVitalsProvider(123, 'a'*32).observe(123)
        self.assertEqual(observation.status, 'unavailable')
        self.assertEqual(observation.failed_operation, 'OpenFileMapping(FILE_MAP_READ)')
        self.assertEqual(observation.fields, {})

    def test_reader_failure_closes_context(self):
        with patch('native_ipc.ReadOnlyNativeMap') as mapping:
            mapping.return_value.__enter__.return_value.read.side_effect = OSError('Read failed')
            observation = NativeVitalsProvider(123, 'a'*32).observe(123)
            mapping.return_value.__exit__.assert_called_once()
        self.assertEqual(observation.failed_operation, 'ReadNativeFrame')

    def test_steam_profile_and_explicit_expiry_forwarded(self):
        self.observe(NativeIpcResult('stale'), profile='steam', max_age_ms=25)

    def test_bound_pid_required_before_open(self):
        with patch('native_ipc.ReadOnlyNativeMap') as mapping:
            for pid in (124, True, 0):
                with self.assertRaises(ValueError):NativeVitalsProvider(123, 'a'*32).observe(pid)
            mapping.assert_not_called()

    def test_invalid_session_configuration_rejected(self):
        for options in ({'profile':'other'}, {'source_kind':True}, {'source_kind':0},
                        {'max_age_ms':0}, {'max_age_ms':True}, {'max_age_ms':-1}):
            with self.assertRaises(ValueError):NativeVitalsProvider(123, 'a'*32, **options)

    def test_submission_remains_unavailable(self):
        self.assertEqual(NativeVitalsProvider(123, 'a'*32).submit({'action':'attack'})['status'], 'unavailable')
