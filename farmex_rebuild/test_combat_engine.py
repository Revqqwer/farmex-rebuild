import unittest
from dataclasses import replace

from combat_engine import (
    Vitals, PartyMember, SupportSnapshot, select_party_member, PriestSettings,
    priest_heal, MinorSettings, rogue_minor, MageSettings, mage_tp,
    KurianSettings, kurian_heal, TargetMode, TargetState, TargetCandidate,
    TargetSnapshot, target_step,
)


def member(identifier, hp=100, maximum=1000, **kw):
    return PartyMember(Vitals(identifier, hp, maximum), target_available=True, distance=10, mage_eligible=True, **kw)


def snapshot(**kw):
    base = SupportSnapshot(3001, Vitals(1, 100, 1000, 1000),
        members=(member(2), member(3, 80)), party_count=3, party_complete=True,
        global_blocked=False, route_guard_active=False, alternate_action_path=False,
        self_heal_ready=True, party_heal_ready=True, minor_action_ready=True,
        kurian_action_ready=True, tp_action_ready=True, unnamed_stat=60)
    return replace(base, **kw)


class PartySelectionTests(unittest.TestCase):
    def test_absolute_hp_not_lowest_percentage(self):
        # Member2=20% but HP40, member3=1% but HP100: choose member2.
        state = snapshot(members=(member(2, 40, 200), member(3, 100, 10000)))
        self.assertEqual(select_party_member(state, 50).member.vitals.actor_id, 2)

    def test_equal_hp_last_member_wins(self):
        state = snapshot(members=(member(2, 100), member(3, 100)))
        self.assertEqual(select_party_member(state, 50).member.vitals.actor_id, 3)

    def test_cooldown_2499_vs_2500(self):
        state = snapshot(now_ms=2499, members=(member(2),))
        self.assertEqual(select_party_member(state, 50).status, 'no_candidate')
        self.assertEqual(select_party_member(replace(state, now_ms=2500), 50).status, 'selected')

    def test_int_distance_29_boundary(self):
        far = replace(member(2), distance=29)
        self.assertEqual(select_party_member(snapshot(members=(far,)), 50).status, 'no_candidate')
        near = replace(far, distance=28.99)
        self.assertEqual(select_party_member(snapshot(members=(near,)), 50).status, 'selected')

    def test_self_dead_and_invalid_target_excluded(self):
        invalid = replace(member(4), target_available=False)
        state = snapshot(members=(member(1), member(2, 0), invalid))
        self.assertEqual(select_party_member(state, 50).status, 'no_candidate')

    def test_hp_ceiling_50000_in_source(self):
        state = snapshot(members=(member(2, 50001, 100000),))
        self.assertEqual(select_party_member(state, 100).status, 'no_candidate')
        self.assertEqual(select_party_member(snapshot(members=(member(2, 50000, 100000),)), 100).status, 'selected')

    def test_unknown_potential_winner_prevents_guess(self):
        unknown = replace(member(2, 10), distance=None)
        self.assertEqual(select_party_member(snapshot(members=(unknown, member(3))), 50).status, 'needs_member_observation')

    def test_incomplete_party_requires_observation(self):
        self.assertEqual(select_party_member(snapshot(party_complete=False), 50).status, 'needs_party_observation')


class PriestTests(unittest.TestCase):
    def settings(self):
        return PriestSettings(self_enabled=True, party_enabled=True, self_skill_id=500, party_skill_id=509)

    def test_self_before_party(self):
        result = priest_heal(self.settings(), snapshot())
        self.assertEqual(result.intent.kind, 'priest_self_heal')
        self.assertEqual(result.intent.target_id, 1)
        self.assertEqual(result.intent.skill_id, 500)
        self.assertEqual(result.intent.hp_deficit, 900)
        self.assertEqual(result.local_lock_ms, 1500)

    def test_self_2000_strict_then_party(self):
        state = snapshot(now_ms=3001, last_self_heal_ms=1001)
        self.assertEqual(priest_heal(self.settings(), state).intent.kind, 'priest_party_heal')
        result = priest_heal(self.settings(), replace(state, now_ms=3002))
        self.assertEqual(result.intent.kind, 'priest_self_heal')

    def test_self_not_ready_falls_through_party(self):
        result = priest_heal(self.settings(), snapshot(self_heal_ready=False))
        self.assertEqual(result.intent.target_id, 3)
        self.assertEqual(result.intent.skill_id, 509)

    def test_unknown_self_readiness_preserves_priority(self):
        self.assertEqual(priest_heal(self.settings(), snapshot(self_heal_ready=None)).status, 'needs_observation')

    def test_route_guard_and_global_gate(self):
        settings = replace(self.settings(), no_heal_on_route=True)
        self.assertEqual(priest_heal(settings, snapshot(route_guard_active=True)).reason, 'route_heal_guard')
        self.assertEqual(priest_heal(settings, snapshot(route_guard_active=None)).status, 'needs_observation')
        self.assertEqual(priest_heal(settings, snapshot(global_blocked=True)).reason, 'global_gate')

    def test_full_hp_has_no_self_deficit(self):
        settings = PriestSettings(self_enabled=True, self_threshold=100)
        state = snapshot(actor=Vitals(1, 1000, 1000))
        self.assertEqual(priest_heal(settings, state).status, 'no_action')

    def test_alternate_lock_not_server_cooldown(self):
        result = priest_heal(self.settings(), snapshot(alternate_action_path=True))
        self.assertEqual(result.local_lock_ms, 2000)
        self.assertEqual(priest_heal(self.settings(), snapshot(alternate_action_path=None)).status, 'needs_observation')


class MinorTests(unittest.TestCase):
    def test_hp_mp_stat_and_interval_exact_boundaries(self):
        settings = MinorSettings(True, 50, 100)
        state = snapshot(now_ms=100, actor=Vitals(1, 500, 1000, 100), unnamed_stat=5)
        result = rogue_minor(settings, state)
        self.assertEqual(result.intent.kind, 'rogue_minor')
        self.assertTrue(result.consumes_retry)
        self.assertEqual(rogue_minor(settings, replace(state, now_ms=99)).status, 'waiting')
        self.assertEqual(rogue_minor(settings, replace(state, actor=Vitals(1, 501, 1000, 100))).status, 'no_action')
        self.assertEqual(rogue_minor(settings, replace(state, actor=Vitals(1, 500, 1000, 99))).status, 'no_action')
        self.assertEqual(rogue_minor(settings, replace(state, unnamed_stat=4)).status, 'no_action')

    def test_alternate_block_still_consumes_local_retry(self):
        result = rogue_minor(MinorSettings(True), snapshot(alternate_action_path=True, minor_action_ready=False))
        self.assertEqual(result.status, 'local_retry_consumed')
        self.assertTrue(result.consumes_retry)
        self.assertIsNone(result.intent)

    def test_helper_does_not_require_shared_gate_for_minor(self):
        self.assertEqual(rogue_minor(MinorSettings(True), snapshot(global_blocked=True)).status, 'intent')

    def test_unknown_inputs(self):
        self.assertEqual(rogue_minor(MinorSettings(True), snapshot(unnamed_stat=None)).status, 'needs_observation')
        self.assertEqual(rogue_minor(MinorSettings(True), snapshot(alternate_action_path=True, minor_action_ready=None)).status, 'needs_observation')


class MageTests(unittest.TestCase):
    def test_low_hp_target_and_boundary_0_100(self):
        result = mage_tp(MageSettings(low_hp_tp=True), snapshot())
        self.assertEqual(result.intent.target_id, 3)
        self.assertEqual(result.intent.kind, 'mage_party_tp')
        for threshold in (0, 100):
            self.assertEqual(mage_tp(MageSettings(low_hp_tp=True, threshold=threshold), snapshot()).reason, 'tp_threshold_guard')

    def test_party_stat_mp_guards(self):
        settings = MageSettings(low_hp_tp=True)
        self.assertEqual(mage_tp(settings, snapshot(unnamed_stat=9)).status, 'no_action')
        self.assertEqual(mage_tp(settings, snapshot(actor=Vitals(1, 100, 1000, 4))).status, 'no_action')
        self.assertEqual(mage_tp(settings, snapshot(party_count=1)).status, 'no_action')

    def test_eligibility_not_guessed_from_distance(self):
        unknown = replace(member(2), mage_eligible=None, distance=100)
        result = mage_tp(MageSettings(low_hp_tp=True), snapshot(members=(unknown,)))
        self.assertEqual(result.status, 'needs_observation')
        eligible = replace(unknown, mage_eligible=True)
        self.assertEqual(mage_tp(MageSettings(low_hp_tp=True), snapshot(members=(eligible,))).status, 'intent')

    def test_name_tp_requires_explicit_resolver_and_3001(self):
        settings = MageSettings(continuous_name_tp=True, target_name='nick')
        self.assertEqual(mage_tp(settings, snapshot()).status, 'needs_observation')
        state = snapshot(now_ms=3000, named_tp_target_id=2)
        self.assertEqual(mage_tp(settings, state).status, 'waiting')
        result = mage_tp(settings, replace(state, now_ms=3001))
        self.assertEqual(result.intent.target_id, 2)

    def test_low_hp_mode_overrides_continuous_name(self):
        settings = MageSettings(low_hp_tp=True, continuous_name_tp=True, target_name='nick')
        self.assertEqual(mage_tp(settings, snapshot(named_tp_target_id=2)).intent.target_id, 3)

    def test_unknown_action_ready_no_claim(self):
        self.assertEqual(mage_tp(MageSettings(low_hp_tp=True), snapshot(tp_action_ready=None)).status, 'needs_observation')
        self.assertEqual(mage_tp(MageSettings(low_hp_tp=True), snapshot(tp_action_ready=False)).reason, 'tp_action_gate')


class KurianTests(unittest.TestCase):
    def test_rank_and_mp_ladder_exact_boundaries(self):
        for stat, mp, expected in ((60, 1000, 760), (60, 999, 735), (35, 350, 735),
                (35, 349, 725), (25, 100, 725), (24, 100, 700), (3, 100, 700)):
            with self.subTest(stat=stat, mp=mp):
                state = snapshot(actor=Vitals(1, 100, 1000, mp), unnamed_stat=stat)
                result = kurian_heal(KurianSettings(True), state)
                self.assertEqual(result.intent.skill_id, expected)
                self.assertEqual(result.local_lock_ms, 1700)
        for stat, mp in ((2, 100), (3, 99)):
            self.assertEqual(kurian_heal(KurianSettings(True), snapshot(actor=Vitals(1, 100, 1000, mp), unnamed_stat=stat)).status, 'no_action')

    def test_unknown_gate_does_not_select_skill(self):
        self.assertEqual(kurian_heal(KurianSettings(True), snapshot(kurian_action_ready=None)).status, 'needs_observation')
        self.assertEqual(kurian_heal(KurianSettings(True), snapshot(global_blocked=True)).status, 'blocked')


class TargetTests(unittest.TestCase):
    def test_enum_matches_source(self):
        self.assertEqual([m.value for m in TargetMode], [1, 2, 3, 4, 5])

    def test_manual_requires_two_helper_conditions(self):
        candidate = TargetCandidate(42, True, True)
        state = TargetSnapshot(True, False, manual=candidate)
        self.assertEqual(target_step(TargetMode.MANUAL, state).state, TargetState(42, True, True))
        self.assertEqual(target_step(TargetMode.MANUAL, replace(state, manual=replace(candidate, manual_eligible=False))).status, 'cleared')
        self.assertEqual(target_step(TargetMode.MANUAL, replace(state, manual=replace(candidate, manual_eligible=None))).status, 'needs_observation')

    def test_inactive_preserves_previous_stop_is_separate(self):
        previous = TargetState(42, True, True)
        result = target_step(TargetMode.MANUAL, TargetSnapshot(False, False), previous)
        self.assertEqual(result.state, previous)
        self.assertEqual(TargetState(), TargetState(0, False, False))

    def test_autoz_keeps_source_ready_asymmetry(self):
        state = TargetSnapshot(True, False, auto_z=TargetCandidate(42, False))
        self.assertEqual(target_step(TargetMode.AUTO_Z, state).state, TargetState(42, False, True))
        self.assertEqual(target_step(TargetMode.AUTO_Z, replace(state, auto_z=TargetCandidate(0))).status, 'cleared')

    def test_name_auto_need_resolver_no_nearest_scan(self):
        previous = TargetState(42, True, True)
        for mode in (TargetMode.NAME_OR_ID, TargetMode.AUTOMATIC):
            self.assertEqual(target_step(mode, TargetSnapshot(True, False), previous).status, 'needs_resolver')
            result = target_step(mode, TargetSnapshot(True, False, resolved_state=TargetState(99, True, True)))
            self.assertEqual(result.status, 'adapter_state')
            self.assertEqual(result.state.target_id, 99)

    def test_leader_requires_party_and_distance_gate(self):
        state = TargetSnapshot(True, False, leader=TargetCandidate(42, True), party_count=2)
        self.assertEqual(target_step(TargetMode.LEADER, state).status, 'needs_observation')
        self.assertEqual(target_step(TargetMode.LEADER, replace(state, leader_gate=False)).status, 'unresolved')
        self.assertEqual(target_step(TargetMode.LEADER, replace(state, leader_gate=True)).state.target_id, 42)
        self.assertEqual(target_step(TargetMode.LEADER, replace(state, party_count=1)).status, 'retained')


class ValidationTests(unittest.TestCase):
    def test_reject_malformed_and_future_data(self):
        with self.assertRaises(ValueError):
            Vitals(1, 1001, 1000)
        with self.assertRaises(ValueError):
            snapshot(last_minor_ms=3002)
        with self.assertRaises(ValueError):
            snapshot(members=(member(2), member(2)))
        with self.assertRaises(ValueError):
            PriestSettings(self_threshold=101)
        with self.assertRaises(ValueError):
            TargetSnapshot(True, False, manual=42)


if __name__ == '__main__':
    unittest.main()
