import unittest
from dataclasses import replace

from target_resolver import (
    AUTO_EXCLUDED_NAMES, ResolverCandidate, ResolverSettings, ResolverSnapshot,
    resolve_target, match_name_or_id, RejectedTarget, prune_rejections,
    remember_rejection, CurrentTargetObservation, evaluate_current_target,
    TargetResolver,
)


def candidate(identifier, distance, **kw):
    result = ResolverCandidate('object-' + str(identifier), identifier, 'Worm',
        distance, distance, visibility=True, repeated_visibility=True)
    return replace(result, **kw)


class ResolverSelectionTests(unittest.TestCase):
    def test_nearest_integer_distance_source_order(self):
        rows = (candidate(1, 12), candidate(2, 5), candidate(3, 9))
        decision = resolve_target(ResolverSettings(), ResolverSnapshot(rows, complete=True))
        self.assertEqual(decision.status, 'selected')
        self.assertEqual(decision.candidate.target_id, 2)

    def test_tie_last_candidate_and_later_pool_wins(self):
        rows = (candidate(1, 5), candidate(2, 5))
        snapshot = ResolverSnapshot(rows, (candidate(3, 5),), True)
        self.assertEqual(resolve_target(ResolverSettings(), snapshot).candidate.target_id, 3)

    def test_raw_pool_selectors(self):
        snapshot = ResolverSnapshot((candidate(1, 1),), (candidate(2, 2),), True)
        self.assertEqual(resolve_target(ResolverSettings(raw_pool_selector=1), snapshot).candidate.target_id, 2)
        self.assertEqual(resolve_target(ResolverSettings(raw_pool_selector=2), snapshot).candidate.target_id, 1)

    def test_status_and_dword_codes_filtered(self):
        rows = (candidate(1, 1, status_byte=10), candidate(2, 1, state_code=4),
            candidate(3, 1, state_code=5), candidate(4, 1, state_code=13), candidate(5, 10))
        self.assertEqual(resolve_target(ResolverSettings(), ResolverSnapshot(rows, complete=True)).candidate.target_id, 5)

    def test_radius_equality_and_coarse_or_final_self_gate(self):
        settings = ResolverSettings(radius=10)
        # Center-only coarse gate passes but final self gate still rejects.
        far = candidate(1, 11, center_distance=1)
        boundary = candidate(2, 10, center_distance=100)
        decision = resolve_target(settings, ResolverSnapshot((far, boundary), complete=True))
        self.assertEqual(decision.candidate.target_id, 2)

    def test_run_return_requires_center_but_run_alone_does_not(self):
        row = candidate(1, 5, center_distance=11)
        snapshot = ResolverSnapshot((row,), complete=True)
        self.assertEqual(resolve_target(ResolverSettings(radius=10, run_to_target=True), snapshot).status, 'selected')
        self.assertEqual(resolve_target(ResolverSettings(radius=10, run_to_target=True, return_to_center=True), snapshot).status, 'cleared')

    def test_fixed_auto_exclusions(self):
        for name in AUTO_EXCLUDED_NAMES:
            with self.subTest(name=name):
                row = candidate(1, 5, name=name)
                self.assertEqual(resolve_target(ResolverSettings(), ResolverSnapshot((row,), complete=True)).status, 'cleared')
        row = candidate(1, 5, name='mine guard')
        self.assertEqual(resolve_target(ResolverSettings(), ResolverSnapshot((row,), complete=True)).status, 'selected')

    def test_rejected_and_visibility_candidates_skipped(self):
        rows = (candidate(1, 1), candidate(2, 2, visibility=False), candidate(3, 3))
        result = resolve_target(ResolverSettings(), ResolverSnapshot(rows, complete=True), (RejectedTarget(1, 0),))
        self.assertEqual(result.candidate.target_id, 3)

    def test_unknown_potential_winner_blocks_commit(self):
        rows = (candidate(1, 1, visibility=None), candidate(2, 2))
        result = resolve_target(ResolverSettings(), ResolverSnapshot(rows, complete=True))
        self.assertEqual(result.status, 'needs_observation')
        self.assertEqual(result.unresolved_object_keys, ('object-1',))
        # An unknown candidate farther than the known winner cannot win.
        result = resolve_target(ResolverSettings(), ResolverSnapshot((candidate(1, 5, visibility=None), candidate(2, 1)), complete=True))
        self.assertEqual(result.status, 'selected')

    def test_incomplete_snapshot_cannot_clear_or_choose(self):
        self.assertEqual(resolve_target(ResolverSettings(), ResolverSnapshot()).status, 'needs_candidate_snapshot')

    def test_name_mode_second_visibility_only_without_run(self):
        settings = ResolverSettings(mode=2, entries=('Worm',))
        row = candidate(1, 5, repeated_visibility=False)
        snapshot = ResolverSnapshot((row,), complete=True)
        self.assertEqual(resolve_target(settings, snapshot).status, 'cleared')
        self.assertEqual(resolve_target(replace(settings, run_to_target=True), snapshot).status, 'selected')

    def test_name_id_filter_is_independent(self):
        rows = (candidate(1, 1, name='Worm'), candidate(2, 5, name='Ape'))
        settings = ResolverSettings(mode=2, entries=('2',))
        result = resolve_target(settings, ResolverSnapshot(rows, complete=True))
        self.assertEqual(result.candidate.target_id, 2)


class NameListTests(unittest.TestCase):
    def test_exact_name_and_decimal_id(self):
        self.assertTrue(match_name_or_id('Worm', 2, ('Worm',)).matched)
        self.assertTrue(match_name_or_id('Ape', 2, ('1', '2')).matched)
        self.assertFalse(match_name_or_id('Ape', 2, ('1', '3')).matched)

    def test_low16_id_and_empty_guard(self):
        self.assertTrue(match_name_or_id('Ape', 0x10002, ('2',)).matched)
        self.assertFalse(match_name_or_id('', 2, ('2',)).matched)
        self.assertFalse(match_name_or_id('Ape', 0x10000, ('0',)).matched)

    def test_conversion_failure_is_explicit_not_false(self):
        result = match_name_or_id('Ape', 2, ('Worm', '2'))
        self.assertIsNone(result.matched)
        self.assertEqual(result.status, 'unresolved_numeric_conversion')
        self.assertEqual(result.unresolved_entry, 'Worm')
        self.assertTrue(match_name_or_id('Worm', 2, ('Worm', 'bad later')).matched)

    def test_hex_overflow_and_nonascii_contract(self):
        for entry in ('$2', '0x2', str(2**63), ' 2 '):
            self.assertEqual(match_name_or_id('Ape', 2, (entry,)).status, 'unresolved_numeric_conversion')
        self.assertEqual(match_name_or_id('Türk', 2, ('2',)).status, 'needs_string_codec')
        self.assertTrue(match_name_or_id('Ape', 2, ('2', 'Türk')).matched)


class RejectionTests(unittest.TestCase):
    def test_duplicate_does_not_refresh_timestamp(self):
        records = remember_rejection((), 1, 100)
        self.assertEqual(remember_rejection(records, 1, 4000), records)

    def test_expiry_boundary_and_shifted_record_skip(self):
        records = (RejectedTarget(1, 0), RejectedTarget(2, 0), RejectedTarget(3, 0))
        self.assertEqual(prune_rejections(records, 4999), records)
        self.assertEqual(prune_rejections(records, 5000), (RejectedTarget(2, 0),))
        self.assertEqual(prune_rejections(prune_rejections(records, 5000), 5000), ())
        self.assertEqual(prune_rejections((RejectedTarget(0, 0),), 9999), (RejectedTarget(0, 0),))

    def test_missing_object_clears_and_float_range_retargets(self):
        settings = ResolverSettings(radius=10)
        missing = evaluate_current_target(settings, CurrentTargetObservation(1, object_exists=False))
        self.assertTrue(missing.clear_state)
        self.assertTrue(missing.needs_retarget)
        far = evaluate_current_target(settings, CurrentTargetObservation(1, True, 10.01))
        self.assertTrue(far.needs_retarget)
        self.assertFalse(far.add_rejection)

    def test_raw_word_condition_and_extra_guard(self):
        settings = ResolverSettings()
        current = CurrentTargetObservation(1, True, 5, 0, 1, 0)
        self.assertTrue(evaluate_current_target(settings, current).add_rejection)
        settings = ResolverSettings(run_to_target=True, extra_rejection_guard=True)
        self.assertEqual(evaluate_current_target(settings, current).status, 'needs_observation')
        guarded = replace(current, special_context=False, state_byte=4)
        self.assertFalse(evaluate_current_target(settings, guarded).needs_retarget)
        self.assertTrue(evaluate_current_target(settings, replace(guarded, state_byte=5)).needs_retarget)
        self.assertTrue(evaluate_current_target(settings, replace(guarded, special_context=True)).needs_retarget)


class WrapperTests(unittest.TestCase):
    def test_arm_then_delay_no_same_call_resolution(self):
        resolver = TargetResolver(ResolverSettings(retarget_wait_ms=100))
        current = CurrentTargetObservation(0)
        snapshot = ResolverSnapshot((candidate(1, 1),), complete=True)
        self.assertEqual(resolver.tick(0, current, snapshot).status, 'retarget_armed')
        self.assertEqual(resolver.tick(99, current, snapshot).status, 'waiting')
        self.assertEqual(resolver.tick(100, current, snapshot).candidate.target_id, 1)
        self.assertIsNone(resolver.armed_ms)

    def test_false_predicate_does_not_reset_armed_timestamp(self):
        resolver = TargetResolver(ResolverSettings(retarget_wait_ms=100))
        snapshot = ResolverSnapshot((candidate(1, 1),), complete=True)
        resolver.tick(0, CurrentTargetObservation(0), snapshot)
        valid = CurrentTargetObservation(2, True, 2, 0, 0, 0)
        self.assertEqual(resolver.tick(100, valid, snapshot).status, 'retained')
        self.assertEqual(resolver.armed_ms, 0)
        self.assertEqual(resolver.tick(101, CurrentTargetObservation(0), snapshot).status, 'selected')

    def test_unknown_snapshot_leaves_timer_armed(self):
        resolver = TargetResolver(ResolverSettings())
        resolver.tick(0, CurrentTargetObservation(0), ResolverSnapshot())
        self.assertEqual(resolver.tick(1, CurrentTargetObservation(0), ResolverSnapshot()).status, 'needs_candidate_snapshot')
        self.assertEqual(resolver.armed_ms, 0)

    def test_validation_backwards_clock_and_invalid_data(self):
        resolver = TargetResolver(ResolverSettings())
        resolver.tick(1, CurrentTargetObservation(0), ResolverSnapshot())
        with self.assertRaises(ValueError):
            resolver.tick(0, CurrentTargetObservation(0), ResolverSnapshot())
        with self.assertRaises(ValueError):
            ResolverSettings(radius=0x80000000)
        with self.assertRaises(ValueError):
            candidate(1, -1)
        with self.assertRaises(ValueError):
            CurrentTargetObservation(1, raw_word_a=65536)


if __name__ == '__main__':
    unittest.main()
