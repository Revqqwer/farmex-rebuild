import math
import unittest
from dataclasses import replace

from operation_engine import (
    IntentJournal, LootMode, LootSettings, LootRecord, LootSnapshot, loot_step,
    OperationIntent, ReceiptOutcome, UpgradeRunner, UpgradeRow, UpgradeSnapshot,
    MerchantKind, MerchantSettings, MerchantRow, MerchantSnapshot, MerchantRunner,
)


class LootTests(unittest.TestCase):
    def record(self, **kw):
        return replace(LootRecord('bundle', 0, item_ids=(1, 900000000, 3, 0, 0, 0, 0, 0)), **kw)

    def step(self, record=None, now=1000, settings=None, **kw):
        return loot_step(settings or LootSettings(), LootSnapshot(now, (record or self.record(),), **kw))

    def test_open_retry_exact_boundary(self):
        self.assertEqual(self.step(now=999, open_state_allowed=True).intents, ())
        result = self.step(open_state_allowed=True)
        self.assertEqual(result.intents[0].kind, 'loot_open')
        self.assertEqual(result.records[0].open_attempt_ms, 1000)
        self.assertFalse(result.records[0].item_phase)

    def test_user_delay_is_strict(self):
        config = LootSettings(wait_enabled=True, wait_ms=1000)
        self.assertEqual(self.step(settings=config, open_state_allowed=True).intents, ())
        self.assertEqual(len(self.step(now=1001, settings=config, open_state_allowed=True).intents), 1)

    def test_gate_blocks_open_not_expiry(self):
        self.assertEqual(self.step().intents, ())
        self.assertEqual(self.step(now=17000).reason, 'local_expiry')
        self.assertEqual(self.step(now=17000, global_blocked=True).status, 'blocked')

    def test_special_context_opens_without_normal_gate(self):
        self.assertEqual(self.step(special_context=True).intents[0].kind, 'loot_open')

    def test_coins_filter_and_slot_flags(self):
        record = self.record(item_phase=True)
        result = self.step(record, settings=LootSettings(mode=LootMode.COINS))
        self.assertEqual(result.intents, ()) # Coins in slot1 is ignored by source mode2.
        record=replace(record,item_ids=(900000000,900000000,0,0,0,0,0,0))
        result=self.step(record,settings=LootSettings(mode=LootMode.COINS))
        self.assertEqual([(x.item_id,x.slot) for x in result.intents],[(900000000,0)])
        flags = (True, False, False, False, False, False, False, False)
        self.assertEqual(self.step(replace(record, slot_done=flags), settings=LootSettings(mode=LootMode.COINS)).intents, ())

    def test_all_and_list_filters(self):
        record = self.record(item_phase=True)
        self.assertEqual(len(self.step(record).intents), 3)
        result = self.step(record, settings=LootSettings(mode=LootMode.LIST, listed_ids=(3,)))
        self.assertEqual([x.item_id for x in result.intents], [3])

    def test_unresolved_classifiers_fail_closed(self):
        record = self.record(item_phase=True)
        result = self.step(record, settings=LootSettings(mode=LootMode.LIST, extended_filters=True))
        self.assertEqual(result.status, 'needs_item_classifier')
        self.assertEqual(result.records[0].item_attempt_ms, 1000)
        self.assertEqual(result.classifier_reference,'bundle')
        self.assertEqual(result.intents, ())

    def test_distance_is_truncated_and_strict(self):
        self.assertEqual(self.step(self.record(item_phase=True, distance=16)).intents, ())
        self.assertEqual(len(self.step(self.record(item_phase=True, distance=15.99)).intents), 3)
        self.assertEqual(self.step(self.record(item_phase=True, distance=80), special_context=True).intents, ())
        self.assertEqual(len(self.step(self.record(item_phase=True, distance=79.9), special_context=True).intents), 3)

    def test_disposal_only_item_phase_one_removal_per_pass(self):
        flag = (True, False, False)
        result = self.step(self.record(disposed_flags=flag))
        self.assertEqual(len(result.records), 1)
        records = (self.record(item_phase=True, disposed_flags=flag), LootRecord('second', 0, item_phase=True, disposed_flags=flag))
        result = loot_step(LootSettings(), LootSnapshot(1000, records))
        self.assertEqual(result.removed_reference, 'bundle')
        self.assertEqual(len(result.records), 1)

    def test_expiry_order_item_before_expiry_open_then_expiry(self):
        result = self.step(self.record(item_phase=True), now=17000)
        self.assertEqual(result.status, 'item_attempt')
        self.assertEqual(len(result.records), 1)
        result = self.step(now=17000, open_state_allowed=True)
        self.assertEqual(result.reason, 'local_expiry')
        self.assertEqual(result.intents[0].kind, 'loot_open')
        self.assertEqual(result.records, ())
        self.assertEqual(len(self.step(now=16999).records), 1)

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            LootRecord('x', 0, item_ids=(1,))
        with self.assertRaises(ValueError):
            LootRecord('x', 0, distance=math.nan)
        with self.assertRaises(ValueError):
            LootSnapshot(0x100000000, (LootRecord('x', 1),))
        with self.assertRaises(ValueError):
            LootSnapshot(1, (LootRecord('x', 0), LootRecord('x', 0)))
        with self.assertRaises(ValueError):
            LootSettings(mode=1)


class UpgradeTests(unittest.TestCase):
    def test_checked_fifo_interval_and_no_success_count(self):
        runner = UpgradeRunner(2000, 55)
        runner.start((UpgradeRow(11), UpgradeRow(22, False), UpgradeRow(33)))
        self.assertEqual(runner.queue, (11, 33))
        self.assertEqual(runner.tick(UpgradeSnapshot(1999, True)).status, 'waiting')
        first = runner.tick(UpgradeSnapshot(2000, True)).intents[0]
        self.assertEqual((first.item_id, first.reference), (11, '55'))
        self.assertEqual(runner.queue, (33,))
        self.assertEqual(runner.tick(UpgradeSnapshot(3999, True)).status, 'waiting')
        self.assertEqual(runner.tick(UpgradeSnapshot(4000, True)).intents[0].item_id, 33)
        self.assertEqual(runner.tick(UpgradeSnapshot(6000, True)).reason, 'queue_empty')

    def test_unknown_gate_does_not_pop(self):
        runner = UpgradeRunner(0)
        runner.start((UpgradeRow(11),))
        self.assertEqual(runner.tick(UpgradeSnapshot(0)).status, 'needs_adapter')
        self.assertEqual(runner.queue, (11,))

    def test_scroll_not_found_stops(self):
        runner = UpgradeRunner(0)
        runner.start((UpgradeRow(11),))
        self.assertEqual(runner.tick(UpgradeSnapshot(0, False, -1)).reason, 'scroll_unavailable')
        self.assertEqual(runner.queue, (11,))

    def test_armor_43rd_attempt_stops_after_intent(self):
        runner = UpgradeRunner()
        runner.start_armor()
        self.assertEqual(runner.tick(UpgradeSnapshot(199, armor_distance=9, armor_blocked=False)).status, 'waiting')
        for index in range(1, 44):
            result = runner.tick(UpgradeSnapshot(index * 200, armor_distance=9.99, armor_blocked=False))
            self.assertEqual(result.intents[0].kind, 'armor_purchase')
            self.assertEqual(runner.state, 2 if index < 43 else 0)
        self.assertEqual(runner.armor_attempts, 43)
        self.assertEqual(result.reason, 'armor_attempt_limit')

    def test_armor_distance_gate_and_unknown(self):
        runner = UpgradeRunner()
        runner.start_armor()
        self.assertEqual(runner.tick(UpgradeSnapshot(200)).status, 'needs_adapter')
        self.assertEqual(runner.tick(UpgradeSnapshot(200, armor_distance=10, armor_blocked=False)).reason, 'armor_gate')

    def test_backward_clock_rejected(self):
        runner = UpgradeRunner()
        runner.start((), 20)
        with self.assertRaises(ValueError):
            runner.tick(UpgradeSnapshot(19))


class MerchantTests(unittest.TestCase):
    def settings(self, kind=MerchantKind.SELL, **kw):
        return MerchantSettings(kind=kind, rows=(MerchantRow(11, 2, 300),), **kw)

    def prepare(self, settings=None):
        runner = MerchantRunner(settings or self.settings())
        runner.start()
        runner.tick(MerchantSnapshot(0, currently_open=False))
        runner.tick(MerchantSnapshot(1, close_pending=False))
        self.assertEqual(runner.phase, 2)
        return runner

    def arm_and_prepare(self, runner):
        self.assertEqual(runner.tick(MerchantSnapshot(61000, setup_result=0)).status, 'setup_gate_armed')
        runner.tick(MerchantSnapshot(61001, setup_result=0))
        self.assertEqual(runner.phase, 3)

    def test_missing_producers_do_not_claim_work(self):
        runner = MerchantRunner(self.settings())
        runner.start()
        self.assertEqual(runner.tick(MerchantSnapshot(0)).status, 'needs_adapter')
        self.assertEqual(runner.phase, 0)

    def test_sell_and_buy_close_timeout(self):
        for kind, timeout in ((MerchantKind.SELL, 10000), (MerchantKind.BUY, 5000)):
            runner = MerchantRunner(self.settings(kind))
            runner.start()
            self.assertEqual(runner.tick(MerchantSnapshot(0, currently_open=True)).intents[0].kind, 'merchant_close')
            self.assertEqual(runner.tick(MerchantSnapshot(timeout - 1, close_pending=True)).status, 'waiting')
            self.assertEqual(runner.tick(MerchantSnapshot(timeout, close_pending=True)).reason, 'close_timeout')

    def test_initial_61_seconds_extra_wait_gate(self):
        runner = self.prepare(self.settings(extra_wait_seconds=2))
        self.assertEqual(runner.tick(MerchantSnapshot(62999, setup_result=0)).remaining_ms, 1)
        self.assertEqual(runner.tick(MerchantSnapshot(63000, setup_result=0)).status, 'setup_gate_armed')

    def test_sell_full_phase_sequence_and_reopen(self):
        runner = self.prepare(self.settings(reopen=True, reopen_minutes=1))
        self.arm_and_prepare(runner)
        unknown = runner.tick(MerchantSnapshot(61002))
        self.assertEqual(unknown.status, 'needs_adapter')
        snapshot = MerchantSnapshot(61003, sale_session_ready=True, item_pending=False, prepared_slot_count=0)
        result = runner.tick(snapshot)
        self.assertEqual(result.intents[0], OperationIntent('sale_list_slot', item_id=11, quantity=2, price=300))
        runner.tick(replace(snapshot, now_ms=61004, prepared_slot_count=1))
        self.assertEqual(runner.phase, 4)
        self.assertEqual(runner.tick(MerchantSnapshot(61005, prepared_slot_count=1)).intents[0].kind, 'merchant_open')
        self.assertEqual(runner.phase, 5)
        self.assertEqual(runner.tick(MerchantSnapshot(61006, opening_pending=True)).status, 'waiting')
        runner.tick(MerchantSnapshot(61007, opening_pending=False))
        self.assertEqual(runner.phase, 6)
        self.assertEqual(runner.tick(MerchantSnapshot(121006, established_ms=61007)).remaining_ms, 1)
        self.assertEqual(runner.tick(MerchantSnapshot(121007, established_ms=61007)).reason, 'reopen_timer')
        self.assertEqual(runner.phase, 0)

    def test_no_prepared_sell_slots_stops(self):
        runner = self.prepare()
        self.arm_and_prepare(runner)
        runner.phase = 4
        self.assertEqual(runner.tick(MerchantSnapshot(61002, prepared_slot_count=0)).reason, 'no_sale_slots')

    def test_sell_all_inventory_14_through_41(self):
        runner = self.prepare(self.settings(sell_all_inventory=True))
        self.arm_and_prepare(runner)
        slots = []
        for offset in range(28):
            snapshot = MerchantSnapshot(61002 + offset, sale_session_ready=True, item_pending=False, prepared_slot_count=0)
            slots.append(runner.tick(snapshot).intents[0].slot)
        self.assertEqual(slots, list(range(14, 42)))
        runner.tick(MerchantSnapshot(61030, sale_session_ready=True, item_pending=False, prepared_slot_count=0))
        self.assertEqual(runner.phase, 4)

    def test_buy_phases_and_free_slot_boundary(self):
        runner = self.prepare(self.settings(MerchantKind.BUY, buy_free_threshold=2))
        self.arm_and_prepare(runner)
        self.assertEqual(runner.tick(MerchantSnapshot(61002)).intents[0].kind, 'merchant_open')
        runner.tick(MerchantSnapshot(61003, opening_pending=False))
        self.assertEqual(runner.phase, 5)
        self.assertEqual(runner.tick(MerchantSnapshot(61004, buy_free_slots=3)).status, 'monitoring')
        self.assertEqual(runner.tick(MerchantSnapshot(61005, buy_free_slots=2)).reason, 'buy_free_threshold')

    def test_failure_disconnect_and_bank_needs_gate(self):
        runner = self.prepare(self.settings(failure_policy='disconnect'))
        result = runner.tick(MerchantSnapshot(61000, setup_result=1))
        self.assertEqual(result.intents[0].kind, 'disconnect')
        self.assertFalse(runner.active)
        runner = self.prepare(self.settings(failure_policy='bank_route'))
        self.assertEqual(runner.tick(MerchantSnapshot(61000, setup_result=1)).status, 'needs_adapter')
        result = runner.tick(MerchantSnapshot(61001, setup_result=1, bank_route_allowed=True))
        self.assertEqual(result.intents[0].reference, 'SMerchant')
        self.assertTrue(runner.active)

    def test_session_and_open_timeouts(self):
        runner = self.prepare()
        self.arm_and_prepare(runner)
        self.assertEqual(runner.tick(MerchantSnapshot(71001, sale_session_ready=False)).reason, 'sale_session_timeout')
        runner = self.prepare(self.settings(MerchantKind.BUY))
        self.arm_and_prepare(runner)
        runner.tick(MerchantSnapshot(61002))
        self.assertEqual(runner.tick(MerchantSnapshot(71002, opening_pending=True)).reason, 'open_timeout')

    def test_buy_unknown_result_is_unresolved(self):
        runner = self.prepare(self.settings(MerchantKind.BUY))
        self.assertEqual(runner.tick(MerchantSnapshot(61000, setup_result=3)).status, 'unresolved')
        self.assertTrue(runner.active)

    def test_restart_requires_new_producer_time_and_rearms_setup(self):
        runner = self.prepare(self.settings(MerchantKind.BUY, buy_free_threshold=1))
        self.arm_and_prepare(runner)
        runner.tick(MerchantSnapshot(61002))
        runner.tick(MerchantSnapshot(61003, opening_pending=False))
        self.assertFalse(runner.setup_seen)
        runner.tick(MerchantSnapshot(61004, buy_free_slots=1))
        runner.tick(MerchantSnapshot(61005, currently_open=True))
        runner.tick(MerchantSnapshot(61006, close_pending=False))
        self.assertEqual(runner.tick(MerchantSnapshot(61007, setup_result=0)).status, 'needs_adapter')
        self.assertEqual(runner.tick(MerchantSnapshot(122004, setup_result=0, setup_started_ms=61005)).remaining_ms, 1)
        self.assertEqual(runner.tick(MerchantSnapshot(122005, setup_result=0, setup_started_ms=61005)).status, 'setup_gate_armed')

    def test_invalid_snapshots_and_settings(self):
        with self.assertRaises(ValueError):
            MerchantSnapshot(0, established_ms=1)
        with self.assertRaises(ValueError):
            MerchantSnapshot(1, prepared_slot_count=13)
        with self.assertRaises(ValueError):
            MerchantSettings(rows=(MerchantRow(1, 1, 1),) * 13)


class ReceiptTests(unittest.TestCase):
    def test_acknowledgement_is_explicit_and_no_replayed_ids(self):
        journal = IntentJournal()
        intent = OperationIntent('upgrade_item', item_id=11)
        identifier = journal.issue(intent)
        self.assertEqual(journal.receipts, [])
        receipt = journal.acknowledge(identifier)
        self.assertEqual(receipt.outcome, ReceiptOutcome.UNKNOWN)
        with self.assertRaises(ValueError):
            journal.acknowledge(identifier, ReceiptOutcome.ACCEPTED)
        with self.assertRaises(ValueError):
            journal.acknowledge(999, ReceiptOutcome.ACCEPTED)

    def test_rejected_receipt_does_not_restore_upgrade_queue(self):
        runner = UpgradeRunner(0)
        runner.start((UpgradeRow(11),))
        intent = runner.tick(UpgradeSnapshot(0, True)).intents[0]
        journal = IntentJournal()
        identifier = journal.issue(intent)
        journal.acknowledge(identifier, ReceiptOutcome.REJECTED, 'adapter reports rejection')
        self.assertEqual(runner.queue, ())
        self.assertEqual(journal.receipts[0].outcome, ReceiptOutcome.REJECTED)


if __name__ == '__main__':
    unittest.main()
