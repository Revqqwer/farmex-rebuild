import unittest
from dataclasses import replace
from potion_engine import (PotionSettings, PotionSnapshot, PotionRunner, potion_decision,
    MP_FALLBACK, HP_FALLBACK, MP_SELECTED, HP_SELECTED, SPECIAL_NUMERIC,
    AvailabilityObservation, LocalActionResult, ordered_candidates)


def snapshot(**changes):
    base = PotionSnapshot(20, 100, 20, 100, availability_complete=True,
                          action_path='direct', state_3a=True, state_3b=False, state_3c=False)
    return replace(base, **changes)


class PotionTests(unittest.TestCase):
    def test_inventory_and_action_domains_are_distinct(self):
        candidate = MP_SELECTED[1][0]
        self.assertEqual(candidate.inventory_id, 0x172fe9c0)
        self.assertEqual(candidate.action_id, 0x77a20)
        result = potion_decision(PotionSettings(mp_enabled=True, mp_combo_index=1),
                                 snapshot(available_inventory_ids=(candidate.inventory_id,)))
        self.assertEqual(result.intents[0].inventory_id, candidate.inventory_id)
        self.assertEqual(result.intents[0].action_id, candidate.action_id)

    def test_mp_precedes_hp_and_local_return_is_not_ack(self):
        hp, mp = HP_FALLBACK[0], MP_FALLBACK[0]
        result = potion_decision(PotionSettings(True, 50, 0, True),
                                 snapshot(available_inventory_ids=(hp.inventory_id, mp.inventory_id)))
        self.assertEqual([i.kind for i in result.intents], ['mp'])
        self.assertTrue(result.local_return)
        self.assertEqual(result.retry_ms, 3000)

    def test_selected_candidate_precedes_all_fallbacks(self):
        selected, fallback = MP_SELECTED[4][0], MP_FALLBACK[0]
        result = potion_decision(PotionSettings(mp_enabled=True, mp_combo_index=4),
                                 snapshot(available_inventory_ids=(selected.inventory_id, fallback.inventory_id)))
        self.assertEqual(result.intents[0].action_id, selected.action_id)

    def test_selected_unavailable_uses_first_available_fallback(self):
        second, third = MP_FALLBACK[1:3]
        result = potion_decision(PotionSettings(mp_enabled=True, mp_combo_index=4),
                                 snapshot(available_inventory_ids=(third.inventory_id, second.inventory_id)))
        self.assertEqual(result.intents[0].action_id, second.action_id)

    def test_hp_index_ten_falls_back(self):
        self.assertNotIn(10, HP_SELECTED)
        self.assertEqual(ordered_candidates('hp', 10), HP_FALLBACK)
        self.assertEqual(len(HP_FALLBACK), 16)
        self.assertEqual(len(MP_FALLBACK), 16)

    def test_unknown_availability_does_not_skip_priority_candidate(self):
        result = potion_decision(PotionSettings(mp_enabled=True),
                                 snapshot(availability_complete=False,
                                          available_inventory_ids=(MP_FALLBACK[1].inventory_id,)))
        self.assertEqual(result.status, 'needs_availability')
        self.assertEqual(result.intents, ())

    def test_explicit_false_is_not_unknown(self):
        first, second = MP_FALLBACK[:2]
        result = potion_decision(PotionSettings(mp_enabled=True), snapshot(availability_complete=False,
            availability=(AvailabilityObservation(first.inventory_id, False),),
            available_inventory_ids=(second.inventory_id,)))
        self.assertEqual(result.intents[0].action_id, second.action_id)

    def test_alternate_false_allows_hp_attempt(self):
        hp, mp = HP_FALLBACK[0], MP_FALLBACK[0]
        result = potion_decision(PotionSettings(True, 50, 0, True), snapshot(
            action_path='alternate', available_inventory_ids=(hp.inventory_id, mp.inventory_id),
            local_action_results=(LocalActionResult('mp', mp.action_id, False),
                                  LocalActionResult('hp', hp.action_id, True))))
        self.assertEqual([i.kind for i in result.intents], ['mp', 'hp'])
        self.assertEqual([i.local_return for i in result.intents], [False, True])

    def test_unknown_alternate_return_blocks_hp_priority(self):
        hp, mp = HP_FALLBACK[0], MP_FALLBACK[0]
        result = potion_decision(PotionSettings(True, 50, 0, True), snapshot(
            action_path='alternate', available_inventory_ids=(hp.inventory_id, mp.inventory_id)))
        self.assertEqual(result.status, 'needs_local_action_result')
        self.assertEqual([i.kind for i in result.intents], ['mp'])

    def test_special_second_candidate_overrides_first(self):
        result = potion_decision(PotionSettings(special_enabled=True, special_selection=2),
            snapshot(special_due=True, available_inventory_ids=tuple(c.inventory_id for c in SPECIAL_NUMERIC)))
        self.assertEqual(result.intents[0].action_id, SPECIAL_NUMERIC[1].action_id)
        self.assertEqual(result.intents[0].kind, 'special')

    def test_magic_hammer_named_lookup(self):
        result = potion_decision(PotionSettings(special_enabled=True),
                                 snapshot(special_due=True, magic_hammer_available=True))
        self.assertEqual(result.intents[0].lookup_name, 'Magic Hammer')
        self.assertEqual(result.intents[0].action_id, 0x77ada)

    def test_inclusive_integer_percentage(self):
        candidate = HP_FALLBACK[0]
        settings = PotionSettings(hp_enabled=True)
        at = snapshot(current_hp=50, maximum_hp=101, available_inventory_ids=(candidate.inventory_id,))
        self.assertEqual(potion_decision(settings, at).status, 'local_action')
        self.assertEqual(potion_decision(settings, replace(at, current_hp=51)).intents, ())

    def test_raw_state_blocking_and_unknown(self):
        settings = PotionSettings(mp_enabled=True)
        self.assertEqual(potion_decision(settings, snapshot(state_3a=False)).status, 'blocked')
        self.assertEqual(potion_decision(settings, snapshot(state_3b=True)).status, 'blocked')
        self.assertEqual(potion_decision(settings, snapshot(state_3c=None)).status, 'needs_observation')

    def test_wrapper_strict_time_and_no_timestamp_write_for_zero(self):
        runner = PotionRunner(50, 0)
        settings = PotionSettings()
        self.assertEqual(runner.tick(50, settings, snapshot(), False, False).status, 'waiting')
        result = runner.tick(51, settings, snapshot(), False, False)
        self.assertFalse(result.local_return)
        self.assertEqual(runner.last_action_ms, 0)
        self.assertNotEqual(runner.tick(52, settings, snapshot(), False, False).status, 'waiting')

    def test_wrapper_action_interval_and_unknown_guards(self):
        candidate = MP_FALLBACK[0]
        runner = PotionRunner()
        settings = PotionSettings(mp_enabled=True)
        data = snapshot(available_inventory_ids=(candidate.inventory_id,))
        self.assertEqual(runner.tick(1, settings, data).status, 'needs_observation')
        self.assertTrue(runner.tick(2, settings, data, False, False).local_return)
        self.assertEqual(runner.tick(3002, settings, data, False, False).status, 'waiting')
        self.assertEqual(runner.tick(3003, settings, data, False, False).status, 'local_action')


if __name__ == '__main__':
    unittest.main()
