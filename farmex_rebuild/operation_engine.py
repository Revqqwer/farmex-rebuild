"""Pure local policies from Richard 416c10, 4f82cc, 420efc and 4220c8.

Intent generation is NOT a game action. The caller supplies producer snapshots;
only a separate adapter may acknowledge an intent. No addresses, packet bytes,
process reads, credentials or network I/O are used. Loot uses unsigned DWORD
differences; Upgrade has an explicit source-clock option and BUY phase4 accepts
an explicit source-clock sample. Other timing policies retain monotonic clocks. Unknown loot data remains
an explicit observation gap.
"""
import math
from dataclasses import dataclass, replace
from enum import Enum
from typing import Optional, Tuple
from collections.abc import Mapping
from loot_classifier import LootListState
from upgrade_scroll import UpgradeScrollObservation, plan_upgrade_scroll
from merchant_setup import (BuySetupObservation, MerchantInventoryObservation,
                            plan_buy_setup, plan_merchant_inventory)
from merchant_open_clock import BuyOpenClockSample,plan_buy_open_wait
from merchant_monitor import BuyMonitorObservation,plan_buy_monitor
from merchant_sell_selection import SellSelectionObservation,plan_sell_selection
from merchant_sell_setup import SellSetupObservation,plan_sell_setup
from merchant_sell_tail import SellSlotDecision
from merchant_sell_session import SellSessionDecision
from merchant_sell_open import SellOpeningDecision
from merchant_sell_open_wait import SellOpenWaitDecision
from merchant_sell_monitor import SellMonitorObservation,plan_sell_monitor
from merchant_sell_prepare_wait import SellPrepareWaitObservation,plan_sell_prepare_wait
from merchant_sell_setup_delay import SellSetupDelayObservation,plan_sell_setup_delay
from merchant_sell_close import SellCloseDecision
from merchant_sell_close_wait import SellCloseWaitObservation,plan_sell_close_wait
from merchant_sell_coin_alarm import SellCoinAlarmObservation,plan_sell_coin_alarm
from merchant_sell_failure import SellFailureObservation,plan_sell_failure
from merchant_buy_failure import BuyFailureObservation,plan_buy_failure


def integer(value, name, maximum=None):
    if type(value) is not int or value < 0 or (maximum is not None and value > maximum):
        raise ValueError(name + ' negatif olmayan tam sayı olmalı')


def boolean(value, name):
    if type(value) is not bool:
        raise ValueError(name + ' boolean olmalı')


def distance_value(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('Mesafe sonlu ve negatif olmayan sayı olmalı')


class LootMode(Enum):
    ALL = 1
    COINS = 2
    LIST = 3


class ReceiptOutcome(Enum):
    UNKNOWN = 'unknown'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'


@dataclass(frozen=True)
class OperationIntent:
    kind: str
    reference: str = ''
    item_id: Optional[int] = None
    slot: Optional[int] = None
    quantity: Optional[int] = None
    price: Optional[int] = None

    def __post_init__(self):
        if not isinstance(self.kind, str) or not self.kind or not isinstance(self.reference, str):
            raise ValueError('Geçersiz işlem niyeti')
        for name in ('item_id', 'slot', 'quantity', 'price'):
            value = getattr(self, name)
            if value is not None:
                integer(value, name)


@dataclass(frozen=True)
class OperationDecision:
    status: str
    intents: Tuple[OperationIntent, ...] = ()
    reason: str = ''
    remaining_ms: Optional[int] = None


@dataclass(frozen=True)
class ActionReceipt:
    intent_id: int
    intent: OperationIntent
    outcome: ReceiptOutcome
    note: str = ''


class IntentJournal:
    """Explicit acknowledgement boundary; acknowledgements never advance engines.

    ACCEPTED means an adapter reported acceptance, not independently verified
    success. UNKNOWN is the default until there is external evidence. Replayed,
    fabricated and duplicate acknowledgement IDs are rejected.
    """
    def __init__(self):
        self.pending = {}
        self.receipts = []
        self.next_id = 1

    def issue(self, intent):
        if not isinstance(intent, OperationIntent):
            raise ValueError('OperationIntent gerekli')
        intent_id = self.next_id
        self.next_id += 1
        self.pending[intent_id] = intent
        return intent_id

    def acknowledge(self, intent_id, outcome=ReceiptOutcome.UNKNOWN, note=''):
        integer(intent_id, 'İşlem ID')
        if intent_id not in self.pending or not isinstance(outcome, ReceiptOutcome) or not isinstance(note, str):
            raise ValueError('Geçersiz veya tekrar edilmiş onay')
        receipt = ActionReceipt(intent_id, self.pending.pop(intent_id), outcome, note)
        self.receipts.append(receipt)
        return receipt


@dataclass(frozen=True)
class LootSettings:
    enabled: bool = True
    mode: LootMode = LootMode.ALL
    wait_enabled: bool = False
    wait_ms: int = 0
    listed_ids: Tuple[int, ...] = ()
    extended_filters: bool = False

    def __post_init__(self):
        for name in ('enabled', 'wait_enabled', 'extended_filters'):
            boolean(getattr(self, name), name)
        if not isinstance(self.mode, LootMode):
            raise ValueError('Geçersiz loot modu')
        integer(self.wait_ms, 'Loot gecikmesi',0xffffffff)
        if not isinstance(self.listed_ids, tuple):
            raise ValueError('Loot listesi tuple olmalı')
        for item in self.listed_ids:
            integer(item, 'Item ID', 0xffffffff)


@dataclass(frozen=True)
class LootRecord:
    reference: str
    created_ms: int
    item_ids: Tuple[int, ...] = (0,) * 8
    slot_done: Tuple[bool, ...] = (False,) * 8
    item_phase: bool = False
    disposed_flags: Tuple[bool, bool, bool] = (False, False, False)
    open_attempt_ms: int = 0
    item_attempt_ms: int = 0
    distance: float = 0
    list_state: Optional[LootListState] = None

    def __post_init__(self):
        if self.list_state is not None and not isinstance(self.list_state,LootListState):
            raise ValueError('Typed LIST record state required')
        if not isinstance(self.reference, str) or not self.reference:
            raise ValueError('Loot kaydı anahtarı gerekli')
        for name in ('created_ms', 'open_attempt_ms', 'item_attempt_ms'):
            integer(getattr(self, name), name,0xffffffff)
        boolean(self.item_phase, 'Loot aşaması')
        distance_value(self.distance)
        if (not isinstance(self.item_ids, tuple) or len(self.item_ids) != 8 or
                not isinstance(self.slot_done, tuple) or len(self.slot_done) != 8 or
                not isinstance(self.disposed_flags, tuple) or len(self.disposed_flags) != 3):
            raise ValueError('Loot kaydı 8 item/slot ve 3 disposal flag gerektirir')
        for item in self.item_ids:
            integer(item, 'Item ID', 0xffffffff)
        for flag in self.slot_done + self.disposed_flags:
            boolean(flag, 'Loot kayıt flag')


@dataclass(frozen=True)
class LootClockSamples:
    wait: Optional[int] = None
    retry: Optional[int] = None
    stamp: Optional[int] = None
    expiry: Optional[int] = None

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            value=getattr(self,name)
            if value is not None:integer(value,'Loot clock '+name,0xffffffff)


@dataclass(frozen=True)
class LootSnapshot:
    now_ms: int
    records: Tuple[LootRecord, ...]
    global_blocked: bool = False
    special_context: bool = False
    open_state_allowed: bool = False
    clock_samples: Optional[Mapping] = None

    def __post_init__(self):
        integer(self.now_ms, 'Saat',0xffffffff)
        for name in ('global_blocked', 'special_context', 'open_state_allowed'):
            boolean(getattr(self, name), name)
        if not isinstance(self.records, tuple) or any(not isinstance(r, LootRecord) for r in self.records):
            raise ValueError('Loot kayıtları geçersiz')
        if len({r.reference for r in self.records}) != len(self.records):
            raise ValueError('Loot kayıt anahtarları benzersiz olmalı')
        # A numerically larger stored DWORD may precede now across tick wrap.
        if self.clock_samples is not None:
            if not isinstance(self.clock_samples,Mapping):raise ValueError('Per-record clock mapping required')
            for key,value in self.clock_samples.items():
                if type(key) is not str or not isinstance(value,LootClockSamples):raise ValueError('Typed per-record clock samples required')


@dataclass(frozen=True)
class LootDecision:
    status: str
    records: Tuple[LootRecord, ...]
    intents: Tuple[OperationIntent, ...] = ()
    removed_reference: Optional[str] = None
    reason: str = ''
    classifier_reference: Optional[str] = None


def loot_step(settings: LootSettings, snapshot: LootSnapshot) -> LootDecision:
    """One consumer pass. Retry updates are local attempts, never server flags.

    999 < delta means >=1000ms; user delay uses strict age > wait. Disposal is
    tested only in item phase. Item dispatch returns before age expiry; open
    dispatch can be followed by expiry in the same pass, exactly as the source.
    Adapter supplies integer-distance interpretation (source uses __ftol).
    clock_samples=None reuses the frame DWORD as a deliberate approximation;
    an explicit mapping requires every reached sample independently. Missing
    samples preserve the known prefix and return needs_clock_observation.
    """
    if not isinstance(settings, LootSettings) or not isinstance(snapshot, LootSnapshot):
        raise ValueError('LootSettings ve LootSnapshot gerekli')
    records = list(snapshot.records)
    intents = []
    if not settings.enabled or snapshot.global_blocked:
        return LootDecision('blocked', snapshot.records)
    class _MissingClock(Exception):pass
    def clock(record,kind):
        if snapshot.clock_samples is None:return snapshot.now_ms
        samples=snapshot.clock_samples.get(record.reference)
        value=None if samples is None else getattr(samples,kind)
        if value is None:raise _MissingClock(record.reference+':'+kind)
        return value
    def elapsed(now,then):return (now-then)&0xffffffff
    try:
        for index,record in enumerate(snapshot.records):
            if record.item_phase and (any(record.disposed_flags) or (record.list_state is not None and record.list_state.discarded)):
                records.pop(index)
                return LootDecision('removed',tuple(records),tuple(intents),record.reference,'disposal_flag')
            delay_ready=not settings.wait_enabled or elapsed(clock(record,'wait'),record.created_ms)>settings.wait_ms
            if record.item_phase:
                limit=80 if snapshot.special_context else 16
                if delay_ready and elapsed(clock(record,'retry'),record.item_attempt_ms)>=1000 and int(record.distance)<limit:
                    records[index]=replace(record,item_attempt_ms=clock(record,'stamp'))
                    if settings.mode==LootMode.LIST and settings.extended_filters:
                        return LootDecision('needs_item_classifier',tuple(records),tuple(intents),
                            reason='Metadata/name/cache observations required',classifier_reference=record.reference)
                    chosen=[]
                    for slot,item in enumerate(record.item_ids):
                        if not item or record.slot_done[slot]:continue
                        if settings.mode==LootMode.COINS and (slot!=0 or item!=900000000):continue
                        if settings.mode==LootMode.LIST and item not in settings.listed_ids:continue
                        chosen.append(OperationIntent('loot_item',record.reference,item_id=item,slot=slot))
                    intents.extend(chosen)
                    return LootDecision('item_attempt',tuple(records),tuple(intents))
            elif delay_ready and elapsed(clock(record,'retry'),record.open_attempt_ms)>=1000:
                if snapshot.special_context or snapshot.open_state_allowed:
                    intents.append(OperationIntent('loot_open',record.reference))
                    records[index]=replace(record,open_attempt_ms=clock(record,'stamp'))
            if elapsed(clock(record,'expiry'),record.created_ms)>16999:
                records.pop(index)
                return LootDecision('removed',tuple(records),tuple(intents),record.reference,'local_expiry')
        return LootDecision('scanned',tuple(records),tuple(intents))
    except _MissingClock as exc:
        return LootDecision('needs_clock_observation',tuple(records),tuple(intents),reason=str(exc))


@dataclass(frozen=True)
class UpgradeRow:
    item_key: int
    checked: bool = True

    def __post_init__(self):
        integer(self.item_key, 'Upgrade item anahtarı', 0xffffffff)
        boolean(self.checked, 'Satır seçimi')


@dataclass(frozen=True)
class UpgradeSnapshot:
    now_ms: int
    queue_action_ready: Optional[bool] = None
    scroll_index: Optional[int] = None
    armor_distance: Optional[float] = None
    armor_blocked: Optional[bool] = None
    source_helper_returned: Optional[bool] = None
    source_stamp_tick_dword: Optional[int] = None
    scroll_lookup: Optional[UpgradeScrollObservation] = None
    armor_distance_ftol_dword: Optional[int] = None

    def __post_init__(self):
        integer(self.now_ms, 'Saat')
        for name in ('queue_action_ready', 'armor_blocked', 'source_helper_returned'):
            if getattr(self, name) is not None:
                boolean(getattr(self, name), name)
        if self.scroll_index is not None and (type(self.scroll_index) is not int or self.scroll_index < -1):
            raise ValueError('Scroll indeksi -1 veya pozitif tam sayı olmalı')
        if self.armor_distance is not None:
            distance_value(self.armor_distance)
        if self.armor_distance_ftol_dword is not None:
            integer(self.armor_distance_ftol_dword,'Armor kaynak ftol DWORD',0xffffffff)
            if self.armor_distance is not None:raise ValueError('Raw ftol and local float distance conflict')
        if self.source_stamp_tick_dword is not None:
            integer(self.source_stamp_tick_dword, 'Kaynak son tick', 0xffffffff)
        if self.scroll_lookup is not None and not isinstance(self.scroll_lookup, UpgradeScrollObservation):
            raise ValueError('Typed scroll lookup observation required')


@dataclass(frozen=True)
class UpgradePendingAttempt:
    intent: OperationIntent
    queue_after: tuple
    armor_attempts_after: int
    helper_returned: bool = False


class UpgradeRunner:
    """State1 checked-row FIFO, state2 armor local attempts. No item outcomes."""
    def __init__(self, interval_ms=2000, anvil_id=0, *, source_clock=False):
        boolean(source_clock, 'Kaynak saat seçimi')
        integer(interval_ms, 'Upgrade aralığı', 0xffffffff if source_clock else None)
        integer(anvil_id, 'Anvil ID', 0xffffffff)
        self.interval_ms = interval_ms
        self.anvil_id = anvil_id
        self.state = 0
        self.queue = ()
        self.last_attempt_ms = 0
        self.last_tick = None
        self.armor_attempts = 0
        self.reason = ''
        self.source_clock = source_clock
        self.queue_stamp_qword = None
        self.armor_stamp_qword = None
        self.source_pending = None
        self.scroll_lookup_plan = None
        self.source_scroll_index = None

    def stop(self, reason='stopped'):
        self.state = 0
        self.reason = reason
        self.source_pending = None

    def start(self, rows, now_ms=0, *, initial_stamp_qword=None):
        integer(now_ms, 'Saat')
        if initial_stamp_qword is not None:
            integer(initial_stamp_qword, 'Kaynak başlangıç stamp', 0xffffffffffffffff)
        rows = tuple(rows)
        if any(not isinstance(row, UpgradeRow) for row in rows):
            raise ValueError('Upgrade satırları geçersiz')
        self.queue = tuple(row.item_key for row in rows if row.checked)
        self.state = 1
        self.last_attempt_ms = now_ms
        self.last_tick = now_ms
        self.reason = ''
        self.source_pending = None
        if initial_stamp_qword is not None:
            self.queue_stamp_qword = initial_stamp_qword

    def start_armor(self, now_ms=0, *, initial_stamp_qword=None):
        integer(now_ms, 'Saat')
        if initial_stamp_qword is not None:
            integer(initial_stamp_qword, 'Kaynak başlangıç stamp', 0xffffffffffffffff)
        self.queue = ()
        self.state = 2
        self.armor_attempts = 0
        self.last_attempt_ms = now_ms
        self.last_tick = now_ms
        self.reason = ''
        self.source_pending = None
        if initial_stamp_qword is not None:
            self.armor_stamp_qword = initial_stamp_qword

    def _finish_source_attempt(self, snapshot):
        pending = self.source_pending
        if not pending.helper_returned:
            if snapshot.source_helper_returned is not True:
                return OperationDecision('needs_helper_return' if snapshot.source_helper_returned is None
                                         else 'helper_did_not_return', reason='Normal helper dönüşü bilinmiyor')
            pending = replace(pending, helper_returned=True)
            self.source_pending = pending
        if snapshot.source_stamp_tick_dword is None:
            return OperationDecision('needs_stamp_tick', reason='Helper sonrasındaki ayrı GetTickCount sonucu yok')
        self.queue = pending.queue_after
        self.armor_attempts = ((self.armor_attempts+1)&0xffffffff) if pending.intent.kind=='armor_purchase' else pending.armor_attempts_after
        if self.state == 1:
            self.queue_stamp_qword = snapshot.source_stamp_tick_dword
        else:
            self.armor_stamp_qword = snapshot.source_stamp_tick_dword
        self.source_pending = None
        # Source compares the incremented DWORD counter as signed32.
        if self.state == 2 and 42 < self._signed(self.armor_attempts, 32):
            self.stop('armor_attempt_limit')
        return OperationDecision('attempt', (pending.intent,), self.reason)

    @staticmethod
    def _signed(value, bits):
        value &= (1 << bits)-1
        return value-(1 << bits) if value & (1 << (bits-1)) else value

    def _tick_source(self, snapshot):
        if not self.state:
            return OperationDecision('inactive', reason=self.reason)
        if self.source_pending is not None:
            # Resume the same reached helper; do not resample its earlier gates.
            return self._finish_source_attempt(snapshot)
        integer(snapshot.now_ms, 'Kaynak GetTickCount DWORD', 0xffffffff)
        stamp = self.queue_stamp_qword if self.state == 1 else self.armor_stamp_qword
        if stamp is None:
            return OperationDecision('needs_initial_stamp', reason='Kaynak QWORD stamp bilinmiyor')
        integer(stamp, 'Kaynak QWORD stamp', 0xffffffffffffffff)
        interval = self._signed(self.interval_ms, 32) if self.state == 1 else 200
        delta = self._signed(snapshot.now_ms-stamp, 64)
        if delta < interval:
            return OperationDecision('waiting', remaining_ms=interval-delta)
        if self.state == 1:
            if not self.queue:
                self.stop('queue_empty')
                return OperationDecision('stopped', reason=self.reason)
            if snapshot.queue_action_ready is None:
                return OperationDecision('needs_adapter', reason='Upgrade çalışma gate bilgisi yok')
            if not snapshot.queue_action_ready:
                index = snapshot.scroll_index
                if snapshot.scroll_lookup is not None:
                    if index is not None:
                        raise ValueError('Raw scroll index and bound lookup conflict')
                    self.scroll_lookup_plan = plan_upgrade_scroll(snapshot.scroll_lookup)
                    if not self.scroll_lookup_plan.complete:
                        return OperationDecision('needs_scroll_lookup', reason=self.scroll_lookup_plan.missing)
                    index = self.scroll_lookup_plan.relative_index
                if index is not None:
                    self.source_scroll_index = index
                if index == -1:
                    self.stop('scroll_unavailable')
                    return OperationDecision('stopped', reason=self.reason)
                return OperationDecision('needs_scroll' if index is None else 'blocked')
            intent = OperationIntent('upgrade_item', str(self.anvil_id), item_id=self.queue[0])
            self.source_pending = UpgradePendingAttempt(intent, self.queue[1:], self.armor_attempts)
        else:
            distance=(self._signed(snapshot.armor_distance_ftol_dword,32) if snapshot.armor_distance_ftol_dword is not None
                      else None if snapshot.armor_distance is None else int(snapshot.armor_distance))
            if distance is None or snapshot.armor_blocked is None:
                return OperationDecision('needs_adapter', reason='Armor NPC mesafesi/durum bilgisi yok')
            if distance >= 10 or snapshot.armor_blocked:
                self.stop('armor_gate')
                return OperationDecision('stopped', reason=self.reason)
            self.source_pending = UpgradePendingAttempt(OperationIntent('armor_purchase'), self.queue,
                                                        (self.armor_attempts+1) & 0xffffffff)
        # Queue removal is a prospective source prefix until the helper returns
        # and its fresh timestamp is observed. Nothing here executes that helper.
        return self._finish_source_attempt(snapshot)

    def tick(self, snapshot: UpgradeSnapshot) -> OperationDecision:
        if not isinstance(snapshot, UpgradeSnapshot):
            raise ValueError('UpgradeSnapshot gerekli')
        if self.source_clock:
            return self._tick_source(snapshot)
        if self.last_tick is not None and snapshot.now_ms < self.last_tick:
            raise ValueError('Saat geriye gidemez')
        self.last_tick = snapshot.now_ms
        if not self.state:
            return OperationDecision('inactive', reason=self.reason)
        interval = self.interval_ms if self.state == 1 else 200
        remaining = interval - (snapshot.now_ms - self.last_attempt_ms)
        if remaining > 0:
            return OperationDecision('waiting', remaining_ms=remaining)
        if self.state == 1:
            if not self.queue:
                self.stop('queue_empty')
                return OperationDecision('stopped', reason=self.reason)
            if snapshot.queue_action_ready is None:
                return OperationDecision('needs_adapter', reason='Upgrade çalışma gate bilgisi yok')
            if not snapshot.queue_action_ready:
                if snapshot.scroll_index == -1:
                    self.stop('scroll_unavailable')
                    return OperationDecision('stopped', reason=self.reason)
                return OperationDecision('needs_scroll' if snapshot.scroll_index is None else 'blocked')
            front = self.queue[0]
            # Source removes before sending. A rejection does not restore the row.
            self.queue = self.queue[1:]
            self.last_attempt_ms = snapshot.now_ms
            return OperationDecision('attempt', (OperationIntent('upgrade_item', str(self.anvil_id), item_id=front),))
        if snapshot.armor_distance is None or snapshot.armor_blocked is None:
            return OperationDecision('needs_adapter', reason='Armor NPC mesafesi/durum bilgisi yok')
        if int(snapshot.armor_distance) >= 10 or snapshot.armor_blocked:
            self.stop('armor_gate')
            return OperationDecision('stopped', reason=self.reason)
        self.last_attempt_ms = snapshot.now_ms
        self.armor_attempts += 1
        if self.armor_attempts > 42:
            self.stop('armor_attempt_limit')
        return OperationDecision('attempt', (OperationIntent('armor_purchase'),), self.reason)


class MerchantKind(Enum):
    SELL = 'sell'
    BUY = 'buy'


@dataclass(frozen=True)
class MerchantRow:
    item_id: int
    quantity: int
    price: int

    def __post_init__(self):
        integer(self.item_id, 'Item ID', 0xffffffff)
        integer(self.quantity, 'Adet')
        integer(self.price, 'Fiyat')
        if not self.item_id or not self.quantity:
            raise ValueError('Item ID ve adet sıfır olamaz')


@dataclass(frozen=True)
class MerchantSettings:
    kind: MerchantKind = MerchantKind.SELL
    rows: Tuple[MerchantRow, ...] = ()
    reopen: bool = False
    reopen_minutes: int = 0
    extra_wait_seconds: int = 0
    failure_policy: str = 'stop'
    buy_free_threshold: int = 0
    sell_all_inventory: bool = False
    # Historical name above is an alias for inventory traversal order, not
    # permission to sell inventory items absent from the prepared sales list.
    sell_inventory_order: Optional[bool] = None

    def __post_init__(self):
        if self.sell_inventory_order is not None:
            boolean(self.sell_inventory_order,'Sell inventory order')
            if self.sell_all_inventory and not self.sell_inventory_order:
                raise ValueError('Conflicting legacy/canonical Sell traversal settings')
        if not isinstance(self.kind, MerchantKind):
            raise ValueError('Pazar türü geçersiz')
        for name in ('reopen', 'sell_all_inventory'):
            boolean(getattr(self, name), name)
        for name in ('reopen_minutes', 'extra_wait_seconds', 'buy_free_threshold'):
            integer(getattr(self, name), name)
        if self.reopen_minutes > 35791 or self.extra_wait_seconds > 2147422:
            raise ValueError('Pazar süreleri desteklenen normal alanı aşıyor')
        if self.failure_policy not in ('stop', 'disconnect', 'bank_route'):
            raise ValueError('Pazar hata politikası geçersiz')
        if not isinstance(self.rows, tuple) or len(self.rows) > 12 or any(not isinstance(row, MerchantRow) for row in self.rows):
            raise ValueError('Pazar listesi en fazla 12 geçerli kayıt olmalı')


@dataclass(frozen=True)
class MerchantSnapshot:
    now_ms: int
    currently_open: Optional[bool] = None
    close_pending: Optional[bool] = None
    setup_result: Optional[int] = None
    sale_session_ready: Optional[bool] = None
    item_pending: Optional[bool] = None
    prepared_slot_count: Optional[int] = None
    opening_pending: Optional[bool] = None
    established_ms: Optional[int] = None
    setup_started_ms: Optional[int] = None
    bank_route_allowed: Optional[bool] = None
    buy_free_slots: Optional[int] = None
    buy_setup_inputs: Optional[BuySetupObservation] = None
    buy_inventory_inputs: Optional[MerchantInventoryObservation] = None
    buy_open_clock: Optional[BuyOpenClockSample] = None
    buy_monitor_inputs: Optional[BuyMonitorObservation] = None
    sell_selection_inputs: Optional[SellSelectionObservation] = None
    sell_slot_helper_returned: Optional[bool] = None
    sell_setup_inputs: Optional[SellSetupObservation] = None
    sell_slot_execution: Optional[SellSlotDecision] = None
    sell_session_execution: Optional[SellSessionDecision] = None
    sell_opening_execution: Optional[SellOpeningDecision] = None
    sell_open_wait_execution: Optional[SellOpenWaitDecision] = None
    sell_monitor_inputs: Optional[SellMonitorObservation] = None
    sell_prepare_wait_inputs: Optional[SellPrepareWaitObservation] = None
    sell_setup_delay_inputs: Optional[SellSetupDelayObservation] = None
    sell_close_execution: Optional[SellCloseDecision] = None
    sell_close_wait_inputs: Optional[SellCloseWaitObservation] = None
    sell_coin_alarm_inputs: Optional[SellCoinAlarmObservation] = None
    sell_failure_inputs: Optional[SellFailureObservation] = None
    sell_failure_factory: object = None
    buy_failure_inputs: Optional[BuyFailureObservation] = None
    buy_failure_factory: object = None

    def __post_init__(self):
        integer(self.now_ms, 'Saat')
        if self.buy_open_clock is not None and not isinstance(self.buy_open_clock,BuyOpenClockSample):
            raise ValueError('Typed BUY opening source clock required')
        if self.buy_monitor_inputs is not None and not isinstance(self.buy_monitor_inputs,BuyMonitorObservation):
            raise ValueError('Typed BUY monitor required')
        if self.sell_selection_inputs is not None and not isinstance(self.sell_selection_inputs,SellSelectionObservation):
            raise ValueError('Typed SELL selection required')
        if self.sell_slot_helper_returned is not None:boolean(self.sell_slot_helper_returned,'Sell helper normal return')
        if self.sell_setup_inputs is not None and not isinstance(self.sell_setup_inputs,SellSetupObservation):
            raise ValueError('Typed SELL setup required')
        if self.sell_slot_execution is not None:
            if not isinstance(self.sell_slot_execution,SellSlotDecision) or self.sell_selection_inputs is None:
                raise ValueError('Typed SELL execution requires bound selection inputs')
            if self.sell_slot_helper_returned is not None:raise ValueError('Bound SELL execution conflicts with opaque helper return')
        if self.sell_session_execution is not None and not isinstance(self.sell_session_execution,SellSessionDecision):
            raise ValueError('Typed SELL session execution required')
        if self.sell_opening_execution is not None and not isinstance(self.sell_opening_execution,SellOpeningDecision):
            raise ValueError('Typed SELL opening execution required')
        if self.sell_open_wait_execution is not None and not isinstance(self.sell_open_wait_execution,SellOpenWaitDecision):
            raise ValueError('Typed SELL opening-wait execution required')
        if self.sell_monitor_inputs is not None and not isinstance(self.sell_monitor_inputs,SellMonitorObservation):
            raise ValueError('Typed SELL monitor required')
        if self.sell_prepare_wait_inputs is not None and not isinstance(self.sell_prepare_wait_inputs,SellPrepareWaitObservation):
            raise ValueError('Typed SELL preparation wait required')
        if self.sell_setup_delay_inputs is not None and not isinstance(self.sell_setup_delay_inputs,SellSetupDelayObservation):
            raise ValueError('Typed SELL setup delay required')
        if self.sell_close_execution is not None and not isinstance(self.sell_close_execution,SellCloseDecision):
            raise ValueError('Typed SELL close execution required')
        if self.sell_close_wait_inputs is not None and not isinstance(self.sell_close_wait_inputs,SellCloseWaitObservation):
            raise ValueError('Typed SELL close wait required')
        if self.sell_coin_alarm_inputs is not None and not isinstance(self.sell_coin_alarm_inputs,SellCoinAlarmObservation):
            raise ValueError('Typed SELL coin alarm required')
        if self.sell_failure_inputs is not None and not isinstance(self.sell_failure_inputs,SellFailureObservation):
            raise ValueError('Typed SELL failure observations required')
        if self.sell_failure_factory is not None and not callable(self.sell_failure_factory):raise ValueError('Own lazy failure factory required')
        if self.buy_failure_inputs is not None and not isinstance(self.buy_failure_inputs,BuyFailureObservation):raise ValueError('Typed BUY failure required')
        if self.buy_failure_factory is not None and not callable(self.buy_failure_factory):raise ValueError('Own lazy BUY failure factory required')
        if self.buy_setup_inputs is not None and not isinstance(self.buy_setup_inputs,BuySetupObservation):
            raise ValueError('Typed BUY setup observation required')
        if self.buy_inventory_inputs is not None and not isinstance(self.buy_inventory_inputs,MerchantInventoryObservation):
            raise ValueError('Typed BUY inventory observation required')
        for name in ('currently_open', 'close_pending', 'sale_session_ready', 'item_pending', 'opening_pending', 'bank_route_allowed'):
            value = getattr(self, name)
            if value is not None:
                boolean(value, name)
        if self.setup_result is not None:
            integer(self.setup_result, 'Pazar setup sonucu')
        for name in ('prepared_slot_count', 'established_ms', 'setup_started_ms', 'buy_free_slots'):
            value = getattr(self, name)
            if value is not None:
                integer(value, name)
        if self.prepared_slot_count is not None and self.prepared_slot_count > 12:
            raise ValueError('Pazar slot sayısı 12yi aşamaz')
        if self.established_ms is not None and self.established_ms > self.now_ms:
            raise ValueError('Pazar kurulum zamanı gelecekte olamaz')
        if self.setup_started_ms is not None and self.setup_started_ms > self.now_ms:
            raise ValueError('Pazar hazırlık zamanı gelecekte olamaz')


class MerchantRunner:
    """Source phases with external producer flags, not fabricated acceptance.

    SELL phases0..6; BUY0..5. Setup result0=prepare,1=failure-policy,
    >=2=stop as observed (unknown Buy codes>2 remain unresolved). Inventory
    classifiers, bank completion and game-side producer flags stay external.
    """
    def __init__(self, settings: MerchantSettings):
        if not isinstance(settings, MerchantSettings):
            raise ValueError('MerchantSettings gerekli')
        self.settings = settings
        self.last_buy_setup_plan = None
        self.last_buy_monitor_plan = None
        self.last_sell_selection_plan = None
        self.last_sell_setup_plan = None
        self.last_sell_slot_execution = None
        self.last_sell_session_execution = None
        self.last_sell_opening_execution = None
        self.last_sell_open_wait_execution = None
        self.last_sell_monitor_plan = None
        self.last_sell_prepare_wait_plan = None
        self.last_sell_setup_delay_plan = None
        self.last_sell_close_execution = None
        self.last_sell_close_wait_plan = None
        self.last_sell_coin_alarm_plan = None
        self.last_sell_failure_plan = None
        self.last_buy_failure_plan = None
        self.active = False
        self.phase = 0
        self.last_tick = None
        self.started_ms = 0
        self.phase_ms = 0
        self.item_ms = 0
        self.entry_index = 0
        self.inventory_slot = 14
        self.setup_seen = False
        self.restarting = False
        self.reason = ''

    def start(self, now_ms=0):
        integer(now_ms, 'Saat')
        self.last_buy_setup_plan = None
        self.last_buy_monitor_plan = None
        self.last_sell_selection_plan = None
        self.last_sell_setup_plan = None
        self.last_sell_slot_execution = None
        self.last_sell_session_execution = None
        self.last_sell_opening_execution = None
        self.last_sell_open_wait_execution = None
        self.last_sell_monitor_plan = None
        self.last_sell_prepare_wait_plan = None
        self.last_sell_setup_delay_plan = None
        self.last_sell_close_execution = None
        self.last_sell_close_wait_plan = None
        self.last_sell_coin_alarm_plan = None
        self.last_sell_failure_plan = None
        self.last_buy_failure_plan = None
        self.active = True
        self.phase = 0
        self.started_ms = self.phase_ms = self.item_ms = now_ms
        self.last_tick = now_ms
        self.entry_index = 0
        self.inventory_slot = 14
        self.setup_seen = False
        self.restarting = False
        self.reason = ''

    def stop(self, reason='stopped'):
        self.active = False
        self.reason = reason

    def _advance(self, now_ms):
        self.phase += 1
        self.phase_ms = now_ms
        return OperationDecision('phase_changed')

    def _timeout(self, now_ms, since, interval, reason):
        remaining = interval - (now_ms - since)
        if remaining > 0:
            return OperationDecision('waiting', remaining_ms=remaining)
        self.stop(reason)
        return OperationDecision('stopped', reason=reason)

    def _failure(self, snapshot):
        policy = self.settings.failure_policy
        if policy == 'bank_route' and snapshot.bank_route_allowed is None:
            return OperationDecision('needs_adapter', reason='Banka rota gate bilgisi yok')
        if policy == 'bank_route' and snapshot.bank_route_allowed:
            self.phase = 0
            self.restarting = True
            self.setup_seen = True
            context = 'SMerchant' if self.settings.kind == MerchantKind.SELL else 'BMerchant'
            return OperationDecision('bank_route', (OperationIntent('load_bank_route', context),))
        self.stop('setup_failed')
        intents = (OperationIntent('disconnect'),) if policy == 'disconnect' else ()
        return OperationDecision('stopped', intents, self.reason)

    def tick(self, snapshot: MerchantSnapshot) -> OperationDecision:
        if not isinstance(snapshot, MerchantSnapshot):
            raise ValueError('MerchantSnapshot gerekli')
        if self.last_tick is not None and snapshot.now_ms < self.last_tick:
            raise ValueError('Saat geriye gidemez')
        self.last_tick = snapshot.now_ms
        if not self.active:
            return OperationDecision('inactive', reason=self.reason)
        now = snapshot.now_ms
        selling = self.settings.kind == MerchantKind.SELL
        if selling and snapshot.sell_coin_alarm_inputs is not None:
            alarm=plan_sell_coin_alarm(snapshot.sell_coin_alarm_inputs);self.last_sell_coin_alarm_plan=alarm
            if not alarm.complete:return OperationDecision('needs_adapter',reason='SELL coin alarm: '+alarm.missing)
        if self.phase == 0:
            if selling and snapshot.sell_close_execution is not None:
                closed=snapshot.sell_close_execution;self.last_sell_close_execution=closed
                if closed.probe is not None and closed.probe.is_open is not None and snapshot.currently_open is not None:
                    if closed.probe.is_open!=snapshot.currently_open:raise ValueError('SELL close probe conflicts with caller')
                if not closed.complete:return OperationDecision('needs_adapter',reason='SELL close: '+closed.missing)
                if closed.state.phase_dword!=1:raise ValueError('SELL close handoff phase mismatch')
                self.phase=1;self.phase_ms=closed.state.close_stamp_qword
                if closed.status=='no_close_required':return OperationDecision('phase_changed')
                if closed.status!='close_prepared':raise ValueError('SELL close branch mismatch')
                return OperationDecision('close_attempt',(OperationIntent('merchant_close',self.settings.kind.value),))
            if snapshot.currently_open is None:
                return OperationDecision('needs_adapter', reason='Pazar açık durum bilgisi yok')
            self._advance(now)
            return OperationDecision('close_attempt', (OperationIntent('merchant_close', self.settings.kind.value),)) if snapshot.currently_open else OperationDecision('phase_changed')
        if self.phase == 1:
            if snapshot.close_pending is None:
                return OperationDecision('needs_adapter', reason='Pazar kapatma flag bilgisi yok')
            if selling and snapshot.sell_close_wait_inputs is not None:
                o=snapshot.sell_close_wait_inputs
                if o.pending_byte is not None and bool(o.pending_byte)!=snapshot.close_pending:
                    raise ValueError('SELL close pending conflicts with caller')
                if o.pending_byte and o.close_stamp_qword is not None and o.close_stamp_qword!=self.phase_ms:
                    raise ValueError('SELL close wait stamp conflicts with caller')
                plan=plan_sell_close_wait(o);self.last_sell_close_wait_plan=plan
                if not plan.complete:return OperationDecision('needs_adapter',reason='SELL close wait: '+plan.missing)
                if plan.status=='waiting':return OperationDecision('waiting',remaining_ms=plan.clock_plan.remaining_ms)
                if plan.status=='timed_out':
                    self.stop('close_timeout');return OperationDecision('stopped',reason=self.reason)
                if plan.status!='pending_cleared' or plan.phase_dword!=2:raise ValueError('SELL close wait phase mismatch')
                return self._advance(now)
            if not snapshot.close_pending:
                return self._advance(now)
            return self._timeout(now, self.phase_ms, 10000 if selling else 5000, 'close_timeout')
        if self.phase == 2:
            if selling and snapshot.sell_setup_delay_inputs is not None:
                delay=plan_sell_setup_delay(snapshot.sell_setup_delay_inputs);self.last_sell_setup_delay_plan=delay
                if not delay.complete:return OperationDecision('needs_adapter',reason='SELL setup delay: '+delay.missing)
                if delay.status=='waiting':return OperationDecision('waiting',remaining_ms=delay.remaining_ms)
                if delay.status!='setup_helper_reached':raise ValueError('SELL setup delay branch mismatch')
            else:
                if self.restarting and snapshot.setup_started_ms is None:
                    return OperationDecision('needs_adapter', reason='Tekrar kurma hazırlık zamanı yok')
                base_ms = self.started_ms if snapshot.setup_started_ms is None else snapshot.setup_started_ms
                remaining = (self.settings.extra_wait_seconds + 61) * 1000 - (now - base_ms)
                if remaining > 0:
                    return OperationDecision('waiting', remaining_ms=remaining)
            setup_result = snapshot.setup_result
            if selling and snapshot.sell_setup_inputs is not None:
                if setup_result is not None:raise ValueError('SELL setup result conflicts with bound preparation')
                setup_plan=plan_sell_setup(snapshot.sell_setup_inputs);self.last_sell_setup_plan=setup_plan
                if not setup_plan.complete:return OperationDecision('needs_adapter',reason='SELL setup: '+setup_plan.missing)
                setup_result=setup_plan.result_dword
            if not selling and snapshot.buy_setup_inputs is not None:
                if setup_result is not None:
                    raise ValueError('BUY setup result conflicts with bound preparation')
                setup_plan = plan_buy_setup(self.settings.buy_free_threshold,snapshot.buy_setup_inputs)
                self.last_buy_setup_plan = setup_plan
                if not setup_plan.complete:
                    return OperationDecision('needs_adapter',reason='BUY setup: '+setup_plan.missing)
                setup_result = setup_plan.result_dword
            if setup_result is None:
                return OperationDecision('needs_adapter', reason='Pazar hazırlık helper sonucu yok')
            if setup_result == 0:
                if not self.setup_seen:
                    self.setup_seen = True
                    return OperationDecision('setup_gate_armed')
                if selling and snapshot.sell_session_execution is not None:
                    session=snapshot.sell_session_execution;self.last_sell_session_execution=session
                    if not session.complete:return OperationDecision('needs_adapter',reason='SELL session: '+session.missing)
                    if session.state.phase_dword!=3 or not session.state.setup_gate_byte:
                        raise ValueError('SELL handoff phase/setup gate mismatch')
                    self.entry_index=session.state.list_index_dword;self.inventory_slot=session.state.inventory_slot_dword
                    self.phase=session.state.phase_dword;self.phase_ms=session.state.session_stamp_qword
                    return OperationDecision('prepare_attempt',(OperationIntent('sell_session_prepare'),))
                self.entry_index = 0
                self.inventory_slot = 14
                self._advance(now)
                return OperationDecision('prepare_attempt', (OperationIntent('sell_session_prepare'),)) if selling else OperationDecision('phase_changed')
            if setup_result == 1:
                if selling and (snapshot.sell_failure_inputs is not None or snapshot.sell_failure_factory is not None):
                    if snapshot.bank_route_allowed is not None:raise ValueError('Bound SELL failure conflicts with legacy bank gate')
                    o=snapshot.sell_failure_inputs
                    if snapshot.sell_failure_factory is not None:
                        if o is not None:raise ValueError('Raw and lazy failure inputs conflict')
                        o=snapshot.sell_failure_factory()
                        if not isinstance(o,SellFailureObservation):raise ValueError('Failure factory must return typed observations')
                    plan=plan_sell_failure(o);self.last_sell_failure_plan=plan
                    if ('read','+58') in plan.steps and o.setup_gate_byte is not None and bool(o.setup_gate_byte)!=self.setup_seen:
                        raise ValueError('SELL failure setup gate conflicts with caller')
                    if not plan.complete:return OperationDecision('needs_adapter',reason='SELL failure: '+plan.missing)
                    if plan.status=='unhandled_policy':return OperationDecision('unresolved',reason='Fresh SELL policy samples select no branch')
                    if plan.status=='bank_route_span_returned':
                        self.phase=plan.phase_dword;self.setup_seen=bool(plan.setup_gate_byte);self.restarting=True
                        return OperationDecision('bank_route',(OperationIntent('load_bank_route','SMerchant'),))
                    if plan.status=='bank_route_error_span_returned':
                        self.phase=plan.phase_dword;self.setup_seen=bool(plan.setup_gate_byte);self.restarting=False
                        self.stop('bank_route_load_failed')
                        return OperationDecision('stopped',reason=self.reason)
                    if plan.status not in ('stop_returned','disconnect_returned','bank_unavailable_stop_returned'):
                        raise ValueError('SELL failure branch mismatch')
                    self.stop('setup_failed')
                    intents=(OperationIntent('disconnect'),) if plan.status=='disconnect_returned' else ()
                    return OperationDecision('stopped',intents,self.reason)
                if not selling and (snapshot.buy_failure_inputs is not None or snapshot.buy_failure_factory is not None):
                    if snapshot.bank_route_allowed is not None:raise ValueError('Bound BUY failure conflicts with legacy bank gate')
                    o=snapshot.buy_failure_inputs
                    if snapshot.buy_failure_factory is not None:
                        if o is not None:raise ValueError('Raw and lazy BUY failure inputs conflict')
                        o=snapshot.buy_failure_factory()
                        if not isinstance(o,BuyFailureObservation):raise ValueError('Factory must return typed BUY failure')
                    plan=plan_buy_failure(o);self.last_buy_failure_plan=plan
                    if ('read','+58') in plan.steps and o.setup_gate_byte is not None and bool(o.setup_gate_byte)!=self.setup_seen:
                        raise ValueError('BUY failure setup gate conflicts with caller')
                    if not plan.complete:return OperationDecision('needs_adapter',reason='BUY failure: '+plan.missing)
                    if plan.status=='unhandled_policy':return OperationDecision('unresolved',reason='Fresh BUY policies select no branch')
                    if plan.status=='bank_route_span_returned':
                        self.phase=plan.phase_dword;self.setup_seen=bool(plan.setup_gate_byte);self.restarting=True
                        return OperationDecision('bank_route',(OperationIntent('load_bank_route','BMerchant'),))
                    if plan.status=='bank_route_error_span_returned':
                        self.phase=plan.phase_dword;self.setup_seen=bool(plan.setup_gate_byte);self.restarting=False
                        self.stop('bank_route_load_failed');return OperationDecision('stopped',reason=self.reason)
                    if plan.status not in ('stop_returned','disconnect_returned','bank_unavailable_stop_returned'):raise ValueError('BUY failure branch mismatch')
                    self.stop('setup_failed')
                    return OperationDecision('stopped',(OperationIntent('disconnect'),) if plan.status=='disconnect_returned' else (),self.reason)
                return self._failure(snapshot)
            if selling or setup_result == 2:
                self.stop('setup_result')
                return OperationDecision('stopped', reason=self.reason)
            return OperationDecision('unresolved', reason='Buy helper sonucu çözümlenmedi')
        if selling and self.phase == 3:
            if snapshot.sale_session_ready is None:
                return OperationDecision('needs_adapter', reason='Sell session producer flag yok')
            if snapshot.sell_prepare_wait_inputs is not None:
                o=snapshot.sell_prepare_wait_inputs
                if o.ready_byte is not None and bool(o.ready_byte)!=snapshot.sale_session_ready:
                    raise ValueError('SELL preparation ready flag conflicts with caller')
                if snapshot.sale_session_ready and o.item_pending_byte is not None:
                    if snapshot.item_pending is None or bool(o.item_pending_byte)!=snapshot.item_pending:
                        raise ValueError('SELL preparation item flag conflicts with caller')
                stamp=(o.session_stamp_qword if not snapshot.sale_session_ready else
                       o.item_stamp_qword if o.item_pending_byte else None)
                if stamp is not None and stamp!=(self.phase_ms if not snapshot.sale_session_ready else self.item_ms):
                    raise ValueError('SELL preparation wait stamp conflicts with caller')
                plan=plan_sell_prepare_wait(o);self.last_sell_prepare_wait_plan=plan
                if not plan.complete:return OperationDecision('needs_adapter',reason='SELL preparation wait: '+plan.missing)
                if plan.status=='waiting':return OperationDecision('waiting',remaining_ms=plan.clock_plan.remaining_ms)
                if plan.status=='timed_out':
                    self.stop('sale_'+plan.branch+'_timeout')
                    return OperationDecision('stopped',reason=self.reason)
                if plan.status!='selection_path':raise ValueError('SELL preparation wait branch mismatch')
            if not snapshot.sale_session_ready:
                return self._timeout(now, self.phase_ms, 10000, 'sale_session_timeout')
            if snapshot.item_pending is None or snapshot.prepared_slot_count is None:
                return OperationDecision('needs_adapter', reason='Sell slot producer bilgisi yok')
            if snapshot.item_pending:
                return self._timeout(now, self.item_ms, 10000, 'sale_item_timeout')
            if snapshot.prepared_slot_count >= 12:
                return self._advance(now)
            inventory_order=(self.settings.sell_all_inventory if self.settings.sell_inventory_order is None
                             else self.settings.sell_inventory_order)
            if snapshot.sell_selection_inputs is not None:
                o=snapshot.sell_selection_inputs
                if inventory_order and o.inventory_slot_dword!=self.inventory_slot:
                    raise ValueError('SELL selection slot conflicts with caller counter')
                if not inventory_order and o.list_index_dword!=self.entry_index:
                    raise ValueError('SELL selection index conflicts with caller counter')
                if (inventory_order and self.inventory_slot>=42) or (not inventory_order and o.stable_rows is True and self.entry_index>=len(o.rows)):
                    return self._advance(now)
                plan=plan_sell_selection(inventory_order,o);self.last_sell_selection_plan=plan
                if not plan.complete:return OperationDecision('needs_adapter',reason='SELL selection: '+plan.missing)
                execution=snapshot.sell_slot_execution
                if execution is not None:
                    self.last_sell_slot_execution=execution
                    if execution.selection!=plan:raise ValueError('SELL execution does not match current selection plan')
                    entry_count=((execution.state.prepared_slots_dword-1)&0xffffffff if execution.complete
                                 else execution.state.prepared_slots_dword)
                    if entry_count!=snapshot.prepared_slot_count:raise ValueError('SELL execution market-slot counter conflicts with snapshot')
                    if not execution.complete:return OperationDecision('needs_adapter',reason='SELL slot tail: '+execution.missing)
                elif plan.requires_tail_return and snapshot.sell_slot_helper_returned is not True:
                    return OperationDecision('needs_adapter',reason='SELL packet/FPU/queue tail normal return not observed')
                if inventory_order:self.inventory_slot+=1
                else:self.entry_index+=1
                if plan.status=='unmatched':return OperationDecision('slot_unmatched')
                self.item_ms=execution.state.item_stamp_qword if execution is not None else now
                return OperationDecision('slot_attempt',(OperationIntent('sale_inventory_slot' if inventory_order else 'sale_list_slot',
                    slot=plan.inventory_slot,item_id=plan.item_dword,quantity=plan.quantity_dword,price=plan.price_dword),))
            if inventory_order:
                if self.inventory_slot >= 42:
                    return self._advance(now)
                slot = self.inventory_slot
                self.inventory_slot += 1
                self.item_ms = now
                return OperationDecision('classify_inventory', (OperationIntent('sale_inventory_slot', slot=slot),))
            if self.entry_index >= len(self.settings.rows):
                return self._advance(now)
            row = self.settings.rows[self.entry_index]
            self.entry_index += 1
            self.item_ms = now
            return OperationDecision('slot_attempt', (OperationIntent('sale_list_slot', item_id=row.item_id, quantity=row.quantity, price=row.price),))
        open_phase = 4 if selling else 3
        if self.phase == open_phase:
            if selling:
                if snapshot.prepared_slot_count is None:
                    return OperationDecision('needs_adapter', reason='Sell hazırlanmış slot sayısı yok')
                if snapshot.sell_opening_execution is not None:
                    opened=snapshot.sell_opening_execution;self.last_sell_opening_execution=opened
                    if opened.state.prepared_slots_dword!=snapshot.prepared_slot_count:
                        raise ValueError('SELL opening market-slot counter conflicts with snapshot')
                    if not opened.complete:return OperationDecision('needs_adapter',reason='SELL opening: '+opened.missing)
                    if opened.status=='no_sale_slots':
                        self.stop('no_sale_slots')
                        return OperationDecision('stopped',reason=self.reason)
                    if opened.state.phase_dword!=5:raise ValueError('SELL opening handoff phase mismatch')
                    self.phase=5;self.phase_ms=opened.state.pending_stamp_qword
                    return OperationDecision('open_attempt',(OperationIntent('merchant_open',self.settings.kind.value),))
                if snapshot.prepared_slot_count < 1:
                    self.stop('no_sale_slots')
                    return OperationDecision('stopped', reason=self.reason)
            self._advance(now)
            return OperationDecision('open_attempt', (OperationIntent('merchant_open', self.settings.kind.value),))
        if self.phase == open_phase + 1:
            if snapshot.opening_pending is None:
                return OperationDecision('needs_adapter', reason='Pazar kurulum producer flag yok')
            if selling and snapshot.sell_open_wait_execution is not None:
                waited=snapshot.sell_open_wait_execution;self.last_sell_open_wait_execution=waited
                if bool(waited.state.pending_byte)!=snapshot.opening_pending or waited.state.pending_stamp_qword!=self.phase_ms:
                    raise ValueError('SELL opening-wait producer/clock conflicts with caller')
                if not waited.complete:return OperationDecision('needs_adapter',reason='SELL opening wait: '+waited.missing)
                if waited.status=='waiting':return OperationDecision('waiting',remaining_ms=waited.clock_plan.remaining_ms)
                if waited.status=='timed_out':
                    self.stop('open_timeout');return OperationDecision('stopped',reason=self.reason)
                if waited.status!='pending_cleared' or waited.state.phase_dword!=6:raise ValueError('SELL wait phase mismatch')
                self.setup_seen=False;self.phase=6;self.phase_ms=now
                return OperationDecision('phase_changed')
            if not snapshot.opening_pending:
                self.setup_seen = False
                return self._advance(now)
            if not selling and snapshot.buy_open_clock is not None:
                clock_plan=plan_buy_open_wait(1,snapshot.buy_open_clock)
                if not clock_plan.timeout_due:
                    return OperationDecision('waiting',remaining_ms=clock_plan.remaining_ms)
                # This is the reconstruction's stop policy, not emulation of
                # source 40ae0c/global/UI/string effects on the timeout path.
                self.stop('open_timeout')
                return OperationDecision('stopped',reason=self.reason)
            return self._timeout(now, self.phase_ms, 10000, 'open_timeout')
        if self.phase == open_phase + 2:
            if selling and snapshot.sell_monitor_inputs is not None:
                plan=plan_sell_monitor(snapshot.sell_monitor_inputs)
                self.last_sell_monitor_plan=plan
                if not plan.complete:return OperationDecision('needs_adapter',reason='SELL monitor: '+plan.missing)
                self.phase=plan.phase_dword
                if self.phase==0:
                    self.restarting=True
                    return OperationDecision('restart_due',reason='reopen_timer')
                return OperationDecision('monitoring')
            if not selling and snapshot.buy_monitor_inputs is not None:
                if snapshot.buy_inventory_inputs is not None or snapshot.buy_free_slots is not None:
                    raise ValueError('Bound BUY monitor conflicts with legacy inventory inputs')
                plan=plan_buy_monitor(snapshot.buy_monitor_inputs)
                self.last_buy_monitor_plan=plan
                if not plan.complete:
                    return OperationDecision('needs_adapter',reason='BUY monitor: '+plan.missing)
                self.phase=plan.phase_dword
                if self.phase==0:
                    self.restarting=True
                    return OperationDecision('restart_due',reason='reopen_timer' if plan.timer_due else 'buy_free_threshold')
                return OperationDecision('monitoring')
            # Source BUY free-space reset is checked after reopen timer.
            if self.settings.reopen:
                if snapshot.established_ms is None:
                    return OperationDecision('needs_adapter', reason='Pazar gerçek kurulum zamanı yok')
                remaining = self.settings.reopen_minutes * 60000 - (now - snapshot.established_ms)
                if remaining <= 0:
                    self.phase = 0
                    self.restarting = True
                    return OperationDecision('restart_due', reason='reopen_timer')
            else:
                remaining = None
            if not selling:
                free_slots = snapshot.buy_free_slots
                free_threshold = self.settings.buy_free_threshold
                if snapshot.buy_inventory_inputs is not None:
                    if free_slots is not None:
                        raise ValueError('BUY free count conflicts with bound inventory')
                    inventory_plan = plan_merchant_inventory(snapshot.buy_inventory_inputs)
                    if not inventory_plan.complete:
                        return OperationDecision('needs_adapter',reason='BUY inventory: '+inventory_plan.missing)
                    free_slots = inventory_plan.free_count
                    integer(free_threshold,'BUY source threshold',0xffffffff)
                    if free_threshold>=0x80000000:free_threshold-=1<<32
                if free_slots is None:
                    return OperationDecision('needs_adapter', reason='Buy boş slot helper sonucu yok')
                if free_slots <= free_threshold:
                    self.phase = 0
                    self.restarting = True
                    return OperationDecision('restart_due', reason='buy_free_threshold')
            return OperationDecision('monitoring', remaining_ms=remaining)
        return OperationDecision('unresolved', reason='Pazar aşaması çözümlenmedi')
