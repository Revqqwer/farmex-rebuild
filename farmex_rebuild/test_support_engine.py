import unittest
from support_engine import (
    Action, GuardConfig, GuardSnapshot, evaluate_guards, DCConfig, DCChoice,
    begin_dc, advance_relog, PartyPolicy, party_invitation, CaptchaPolicy,
    manual_captcha, choose_event_groups, CrashSnapshot, abyss_crash_decision,
    loot_inactivity_alarm,
)


class SupportTests(unittest.TestCase):
    def test_guard_priority_masks_close(self):
        cfg = GuardConfig(np_enabled=True, coin_limit=50, close_time=(12, 30))
        result = evaluate_guards(cfg, GuardSnapshot(np_reader_result=0, coins=0,
                                                    local_time=(12, 30)))
        self.assertEqual([x.action for x in result], [Action.STOP, Action.CONTROL_ACTION])
        self.assertEqual(result[0].reason, "np_reader_zero")

    def test_coin_boundary(self):
        for coins, expected in ((99, True), (100, True), (101, False)):
            self.assertEqual(bool(evaluate_guards(GuardConfig(coin_limit=100),
                             GuardSnapshot(coins=coins))), expected)

    def test_coin_high_word_is_not_guessed(self):
        with self.assertRaises(ValueError):
            GuardConfig(coin_limit=2**32)

    def test_level_is_equal_not_greater(self):
        cfg = GuardConfig(target_level=80)
        self.assertTrue(evaluate_guards(cfg, GuardSnapshot(level=80)))
        self.assertFalse(evaluate_guards(cfg, GuardSnapshot(level=81)))

    def test_clock_exact_minute(self):
        cfg = GuardConfig(close_time=(23, 59))
        self.assertEqual(evaluate_guards(cfg, GuardSnapshot(local_time=(23, 59)))[0].action,
                         Action.CLOSE_PROCESS)
        self.assertFalse(evaluate_guards(cfg, GuardSnapshot(local_time=(0, 0))))

    def test_party_strict_boundary_and_mode(self):
        cfg = GuardConfig(party_minimum=3, party_stop=True, party_alarm=True)
        self.assertEqual(len(evaluate_guards(cfg, GuardSnapshot(party_count=2))), 2)
        self.assertFalse(evaluate_guards(cfg, GuardSnapshot(party_count=3)))
        self.assertFalse(evaluate_guards(cfg, GuardSnapshot(mode=2, party_count=0)))

    def test_priest_short_party_branch(self):
        cfg = GuardConfig(priest_stop=True)
        self.assertTrue(evaluate_guards(cfg, GuardSnapshot(party_count=1, party_has_priest=True)))
        self.assertFalse(evaluate_guards(cfg, GuardSnapshot(party_count=2, party_has_priest=True)))

    def test_missing_observations_dont_trigger(self):
        cfg = GuardConfig(np_enabled=True, coin_limit=100, target_level=80,
                          party_minimum=3, party_stop=True, priest_alarm=True)
        self.assertFalse(evaluate_guards(cfg, GuardSnapshot()))

    def test_invalid_clock(self):
        with self.assertRaises(ValueError):
            GuardConfig(close_time=(24, 0))

    def test_dc_disabled_is_quiet(self):
        state, intents = begin_dc(DCConfig(), True, 0)
        self.assertFalse(state.waiting)
        self.assertFalse(intents)

    def test_dc_action_selection(self):
        for choice, expected in ((DCChoice.SHUTDOWN, Action.SHUTDOWN),
                                 (DCChoice.CLOSE_PROCESS, Action.CLOSE_PROCESS),
                                 (DCChoice.RELOG, Action.RELOG)):
            state, intents = begin_dc(DCConfig(True, True, choice, 3), True, 100)
            self.assertEqual([i.action for i in intents], [Action.STOP, Action.ALARM, expected])
            self.assertEqual(state.waiting, choice == DCChoice.RELOG)

    def test_relog_countdown_rate_and_completion(self):
        state, _ = begin_dc(DCConfig(True, False, DCChoice.RELOG, 3), False, 100)
        unchanged, quiet = advance_relog(state, 3, 1099)
        self.assertEqual(unchanged, state)
        self.assertFalse(quiet)
        state, notice = advance_relog(state, 3, 1100)
        self.assertEqual(notice[0].value, 2)
        state, done = advance_relog(state, 3, 3100)
        self.assertEqual(done[0].action, Action.RELOG_READY)
        self.assertFalse(state.waiting)
        self.assertFalse(advance_relog(state, 3, 5000)[1])

    def test_relog_invalid_timeline(self):
        state, _ = begin_dc(DCConfig(True, False, DCChoice.RELOG, 3), False, 100)
        with self.assertRaises(ValueError):
            advance_relog(state, 3, 99)

    def test_party_exact_case_sensitive(self):
        policy = PartyPolicy(True, False, ("Knight",), True)
        self.assertEqual(party_invitation(policy, "Knight")[0].action, Action.ACCEPT_PARTY)
        self.assertEqual(party_invitation(policy, "knight")[0].action, Action.REJECT_PARTY)
        self.assertEqual(party_invitation(policy, "Knight*")[0].action, Action.REJECT_PARTY)

    def test_party_accept_all_and_disabled(self):
        self.assertEqual(party_invitation(PartyPolicy(True, True), "Other")[0].action,
                         Action.ACCEPT_PARTY)
        self.assertFalse(party_invitation(PartyPolicy(), "Other"))

    def test_manual_captcha_independent_flags(self):
        result = manual_captcha(CaptchaPolicy(True, True, True, True))
        self.assertEqual([x.action for x in result],
                         [Action.STOP, Action.TOWN, Action.ALARM, Action.CAPTCHA_WINDOW])
        self.assertFalse(manual_captcha(CaptchaPolicy()))

    def test_event_group_priority_is_not_schedule(self):
        self.assertEqual(choose_event_groups({"knight_royale", "bdw", "chaos", "juraid", "utc", "ft"}),
                         ("chaos", "ft"))
        self.assertEqual(choose_event_groups({"juraid"}), (None, "juraid"))
        with self.assertRaises(ValueError):
            choose_event_groups({"draki"})

    def test_crash_prerequisite_priority(self):
        result = abyss_crash_decision(CrashSnapshot(True, False, 0, None), 5, 0, 9999)
        self.assertEqual(result[0].reason, "inventory_full")
        result = abyss_crash_decision(CrashSnapshot(False, False, 0, None), 5, 0, 9999)
        self.assertEqual(result[0].reason, "abyss_gem_missing")

    def test_crash_distance_boundary_and_timer(self):
        snap = CrashSnapshot(False, True, 123, 10)
        self.assertFalse(abyss_crash_decision(snap, 5, 100, 5099))
        self.assertEqual(abyss_crash_decision(snap, 5, 100, 5100)[0].value, 123)
        self.assertEqual(abyss_crash_decision(snap, 5, 100, 5101)[0].value, 123)
        self.assertEqual(abyss_crash_decision(CrashSnapshot(False, True, 123, 10.1),
                         5, 100, 5101)[0].reason, "npc_unavailable")

    def test_crash_invalid_timeline(self):
        with self.assertRaises(ValueError):
            abyss_crash_decision(CrashSnapshot(False, True, 123, 5), 5, 100, 99)

    def test_loot_nonzero_baseline_and_boundary(self):
        self.assertFalse(loot_inactivity_alarm(True, 0, 700000))
        self.assertFalse(loot_inactivity_alarm(True, 1, 600000))
        self.assertEqual(loot_inactivity_alarm(True, 1, 600001)[0].action, Action.ALARM)
        self.assertEqual(loot_inactivity_alarm(True, 1, 600002)[0].action, Action.ALARM)
        self.assertFalse(loot_inactivity_alarm(False, 1, 700000))


if __name__ == "__main__":
    unittest.main()
