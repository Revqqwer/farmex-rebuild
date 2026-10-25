import unittest
from quest_engine import QuestRecord, QuestSnapshot, plan_take_quest


class QuestTests(unittest.TestCase):
    def snapshot(self, **changes):
        values = dict(selected_index=0, record_index_from_row=0, npc_id_465960=12,
                      npc_pointer_464a10=0x123400, distance=10, current_target_462630=12,
                      record_data_20=4, quest_lookup_4d642c=0x12345678)
        values.update(changes)
        return QuestSnapshot(**values)

    def plan(self, **changes):
        return plan_take_quest([QuestRecord('NPC', b'quest')], self.snapshot(**changes))

    def test_negative_selection_short_circuits_all_reads(self):
        self.assertEqual(plan_take_quest([], QuestSnapshot()).status, 'no_selection')

    def test_selected_row_index_is_not_database_record_index(self):
        records = [QuestRecord('A', b'a'), QuestRecord('B', b'b')]
        result = plan_take_quest(records, self.snapshot(record_index_from_row=1))
        self.assertEqual(result.calls[0].arguments, ('B',))

    def test_bounds_checked_at_own_record_boundary(self):
        self.assertEqual(self.plan(record_index_from_row=1).status, 'invalid_record')

    def test_npc_zero_does_not_require_pointer(self):
        result = self.plan(npc_id_465960=0, npc_pointer_464a10=None)
        self.assertEqual(result.status, 'npc_not_found')
        self.assertEqual(len(result.calls), 1)

    def test_pointer_zero_does_not_require_distance(self):
        self.assertEqual(self.plan(npc_pointer_464a10=0, distance=None).status, 'npc_pointer_missing')

    def test_distance_includes_zero_and_ten(self):
        for d in (0, 10):
            self.assertEqual(self.plan(distance=d).status, 'local_plan')
        for d in (-0.001, 10.001):
            self.assertEqual(self.plan(distance=d).status, 'out_of_range')

    def test_source_float32_rounding(self):
        self.assertEqual(self.plan(distance=10.00000001).status, 'local_plan')

    def test_retarget_uses_pointer(self):
        result = self.plan(current_target_462630=0)
        target = next(c for c in result.calls if c.helper == '0046493c')
        self.assertEqual(target.arguments, (0x123400,))

    def test_same_target_does_not_retarget(self):
        self.assertNotIn('0046493c', [c.helper for c in self.plan().calls])

    def test_three_payloads_and_delays(self):
        q = self.plan().queue_plans
        self.assertEqual([p.delay_ms for p in q], [500, 1000, 1500])
        self.assertEqual(q[0].payload, bytes.fromhex('640778560000'))
        self.assertEqual(q[1].payload, b'\x55\x00\x05quest')
        self.assertEqual(q[2].payload, q[1].payload + b'\xff')

    def test_unknown_lookup_has_no_packet_plan(self):
        result = self.plan(quest_lookup_4d642c=None)
        self.assertEqual(result.status, 'needs_observation')
        self.assertEqual(result.queue_plans, ())

    def test_missing_script_retains_prior_source_queue_plan(self):
        result = plan_take_quest([QuestRecord('NPC')], self.snapshot())
        self.assertEqual(result.status, 'needs_observation')
        self.assertEqual(len(result.queue_plans), 1)

    def test_length_byte_wrap_does_not_truncate_script(self):
        result = plan_take_quest([QuestRecord('NPC', b'x'*256)], self.snapshot())
        self.assertEqual(result.queue_plans[1].payload[2], 0)
        self.assertEqual(len(result.queue_plans[1].payload), 259)

    def test_scratch_buffer_bound(self):
        result = plan_take_quest([QuestRecord('NPC', b'x'*508)], self.snapshot())
        self.assertEqual(len(result.queue_plans[2].payload), 512)
        with self.assertRaises(ValueError):
            QuestRecord('NPC', b'x'*509)

    def test_lookup_minus_one_raw_dword_is_not_suppressed(self):
        self.assertEqual(self.plan(quest_lookup_4d642c=0xffffffff).queue_plans[0].payload[2:4], b'\xff\xff')

    def test_type_and_nan_rejected(self):
        with self.assertRaises(ValueError):
            self.snapshot(distance=float('nan'))
        with self.assertRaises(ValueError):
            self.snapshot(record_data_20=True)


if __name__ == '__main__':
    unittest.main()
