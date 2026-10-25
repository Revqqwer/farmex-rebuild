"""Pure full potion selection from Richard0040e7ac + wrapper0040f204.

Availability inventory IDs and dispatched action IDs are DIFFERENT domains.
All pairs below are traced to PUSH->CALL00463924->MOV in source assembly.
No inventory reads, action calls or network I/O are performed by this module.
"""
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class PotionCandidate:
    inventory_id: int
    action_id: int
    availability_call: str
    action_assignment: str


def _p(inventory_id, action_id, call, assignment):
    return PotionCandidate(inventory_id, action_id, call, assignment)


# These addresses refer to static source provenance, never runtime game offsets.
MP_FALLBACK = (
    _p(0x35b11e00, 0x781e5, '0040ebd3', '0040ebdd'),
    _p(0x35b14510, 0x781e6, '0040ebee', '0040ebf8'),
    _p(0x35b16c20, 0x781e7, '0040ec09', '0040ec13'),
    _p(0x172fe9c0, 0x77a20, '0040ec24', '0040ec2e'),
    _p(0x172feda8, 0x77a21, '0040ec3f', '0040ec49'),
    _p(0x172ff190, 0x77a22, '0040ec5a', '0040ec64'),
    _p(0x172ff578, 0x77a23, '0040ec75', '0040ec7f'),
    _p(0x172ff960, 0x77a24, '0040ec90', '0040ec9a'),
    _p(0x1731a710, 0x77a58, '0040ecab', '0040ecb5'),
    _p(0x35b16450, 0x781fa, '0040ecc6', '0040ecd0'),
    _p(0x17350270, 0x7a1af, '0040ece1', '0040eceb'),
    _p(0x1735c5c0, 0x7a1b2, '0040ecf9', '0040ed03'),
    _p(0x30496b70, 0x77a64, '0040ed11', '0040ed1b'),
    _p(0x17cc9b08, 0x77a9c, '0040ed29', '0040ed33'),
    _p(0x304ba5c0, 0x7a202, '0040ed41', '0040ed4b'),
    _p(0x3789f0f8, 0x7efaf, '0040ed59', '0040ed63'),
)
HP_FALLBACK = (
    _p(0x35b0a8d0, 0x781e2, '0040efea', '0040eff4'),
    _p(0x35b0cfe0, 0x781e3, '0040f005', '0040f00f'),
    _p(0x35b0f6f0, 0x781e4, '0040f020', '0040f02a'),
    _p(0x172fd250, 0x77a1a, '0040f03b', '0040f045'),
    _p(0x172fd638, 0x77a1b, '0040f056', '0040f060'),
    _p(0x172fda20, 0x77a1c, '0040f071', '0040f07b'),
    _p(0x172fde08, 0x77a1d, '0040f08c', '0040f096'),
    _p(0x172fe1f0, 0x77a1e, '0040f0a7', '0040f0b1'),
    _p(0x30496788, 0x77a5c, '0040f0c2', '0040f0cc'),
    _p(0x35b16068, 0x781f9, '0040f0dd', '0040f0e7'),
    _p(0x17348d40, 0x7a1ac, '0040f0f8', '0040f102'),
    _p(0x17359eb0, 0x7a1b1, '0040f110', '0040f11a'),
    _p(0x17cc9720, 0x77a5a, '0040f128', '0040f132'),
    _p(0x304ba9a8, 0x7a206, '0040f140', '0040f14a'),
    _p(0x304a80c8, 0x7a172, '0040f158', '0040f162'),
    _p(0x3789ed10, 0x7efae, '0040f170', '0040f17a'),
)
# HP actually has SIXTEEN fallback tests, despite older prose count15.
MP_SELECTED = {
    1: (_p(0x172fe9c0,0x77a20,'0040e9f0','0040e9fa'),),
    2: (_p(0x172feda8,0x77a21,'0040ea17','0040ea21'),),
    3: (_p(0x172ff190,0x77a22,'0040ea3e','0040ea48'),),
    4: (_p(0x172ff578,0x77a23,'0040ea65','0040ea6f'),),
    5: (_p(0x172ff960,0x77a24,'0040ea8c','0040ea96'),),
    6: (_p(0x35b11e00,0x781e5,'0040eab3','0040eabd'),),
    7: (_p(0x35b14510,0x781e6,'0040eada','0040eae4'),),
    8: (_p(0x35b16c20,0x781e7,'0040eb01','0040eb0b'),),
    9: (_p(0x17350270,0x7a1af,'0040eb28','0040eb32'), _p(0x1735c5c0,0x7a1b2,'0040eb43','0040eb4d')),
    10: (_p(0x17cc9b08,0x77a9c,'0040eb6a','0040eb74'),),
    11: (_p(0x30496b70,0x77a64,'0040eb91','0040eb9b'),),
    12: (_p(0x3789f0f8,0x7efaf,'0040ebb8','0040ebc2'),),
}
HP_SELECTED = {
    1: (_p(0x172fd250,0x77a1a,'0040ee2e','0040ee38'),),
    2: (_p(0x172fd638,0x77a1b,'0040ee55','0040ee5f'),),
    3: (_p(0x172fda20,0x77a1c,'0040ee7c','0040ee86'),),
    4: (_p(0x172fde08,0x77a1d,'0040eea3','0040eead'),),
    5: (_p(0x172fe1f0,0x77a1e,'0040eeca','0040eed4'),),
    6: (_p(0x35b0a8d0,0x781e2,'0040eef1','0040eefb'),),
    7: (_p(0x35b0cfe0,0x781e3,'0040ef18','0040ef22'),),
    8: (_p(0x35b0f6f0,0x781e4,'0040ef3f','0040ef49'),),
    9: (_p(0x17348d40,0x7a1ac,'0040ef66','0040ef70'), _p(0x17359eb0,0x7a1b1,'0040ef81','0040ef8b')),
    # There is NO explicit index10 HP branch in the source: use fallback only.
    11: (_p(0x30496788,0x77a5c,'0040efa8','0040efb2'),),
    12: (_p(0x3789ed10,0x7efae,'0040efcf','0040efd9'),),
}
SPECIAL_NUMERIC = (
    _p(0x3055e2d8,0x78232,'0040e927','0040e931'),
    _p(0x304b1538,0x7a184,'0040e93d','0040e947'),
)


def _int(value, name, maximum=0x7fffffff):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError(name + ' geçerli negatif olmayan tam sayı olmalı')


def _bool(value, name, optional=False):
    if value is None and optional:
        return
    if type(value) is not bool:
        raise ValueError(name + ' boolean olmalı')


def ordered_candidates(kind, combo_index):
    """Selected tests then FULL fallback, including repeated availability tests."""
    if kind not in ('hp', 'mp'):
        raise ValueError('Potion türü hp/mp olmalı')
    _int(combo_index, 'Combo indeksi', 12)
    selected = HP_SELECTED if kind == 'hp' else MP_SELECTED
    fallback = HP_FALLBACK if kind == 'hp' else MP_FALLBACK
    return selected.get(combo_index, ()) + fallback


@dataclass(frozen=True)
class PotionSettings:
    hp_enabled: bool = False
    hp_threshold: int = 50
    hp_combo_index: int = 0
    mp_enabled: bool = False
    mp_threshold: int = 50
    mp_combo_index: int = 0
    special_enabled: bool = False
    special_selection: int = 1

    def __post_init__(self):
        for name in ('hp_enabled', 'mp_enabled', 'special_enabled'):
            _bool(getattr(self, name), name)
        for name in ('hp_threshold', 'mp_threshold'):
            _int(getattr(self, name), name, 100)
        for name in ('hp_combo_index', 'mp_combo_index'):
            _int(getattr(self, name), name, 12)
        if type(self.special_selection) is not int or self.special_selection not in (1, 2):
            raise ValueError('Special seçim1 veya2 olmalı')


@dataclass(frozen=True)
class AvailabilityObservation:
    inventory_id: int
    available: Optional[bool]

    def __post_init__(self):
        _int(self.inventory_id, 'Inventory ID', 0xffffffff)
        _bool(self.available, 'Availability', True)


@dataclass(frozen=True)
class LocalActionResult:
    kind: str
    action_id: int
    returned_nonzero: Optional[bool]

    def __post_init__(self):
        if self.kind not in ('hp', 'mp', 'special'):
            raise ValueError('Eylem türü geçersiz')
        _int(self.action_id, 'Action ID', 0xffffffff)
        _bool(self.returned_nonzero, 'Yerel eylem dönüşü', True)


@dataclass(frozen=True)
class PotionSnapshot:
    current_hp: int
    maximum_hp: int
    current_mp: int
    maximum_mp: int
    available_inventory_ids: Tuple[int, ...] = ()
    availability_complete: bool = False
    availability: Tuple[AvailabilityObservation, ...] = ()
    action_path: Optional[str] = None
    local_action_results: Tuple[LocalActionResult, ...] = ()
    state_3a: Optional[bool] = None
    state_3b: Optional[bool] = None
    state_3c: Optional[bool] = None
    special_due: Optional[bool] = None
    magic_hammer_available: Optional[bool] = None

    def __post_init__(self):
        for name in ('current_hp', 'maximum_hp', 'current_mp', 'maximum_mp'):
            _int(getattr(self, name), name)
        if self.current_hp > self.maximum_hp or self.current_mp > self.maximum_mp:
            raise ValueError('Mevcut HP/MP maksimumu aşamaz')
        _bool(self.availability_complete, 'Inventory observation eksiksiz')
        for name in ('state_3a', 'state_3b', 'state_3c', 'special_due', 'magic_hammer_available'):
            _bool(getattr(self, name), name, True)
        if self.action_path not in (None, 'direct', 'alternate'):
            raise ValueError('Eylem yolu direct/alternate veyaunknown olmalı')
        if not isinstance(self.available_inventory_ids, tuple):
            raise ValueError('Availability ID tuple gerekli')
        for value in self.available_inventory_ids:
            _int(value, 'Availability ID', 0xffffffff)
        if (not isinstance(self.availability, tuple) or any(not isinstance(v, AvailabilityObservation) for v in self.availability) or
                len({v.inventory_id for v in self.availability}) != len(self.availability)):
            raise ValueError('Availability gözlemleri geçersiz/duplicate')
        if (not isinstance(self.local_action_results, tuple) or any(not isinstance(v, LocalActionResult) for v in self.local_action_results) or
                len({(v.kind,v.action_id) for v in self.local_action_results}) != len(self.local_action_results)):
            raise ValueError('Eylem sonuç gözlemleri geçersiz/duplicate')


@dataclass(frozen=True)
class PotionIntent:
    kind: str
    inventory_id: Optional[int]
    action_id: int
    action_path: str
    local_return: Optional[bool]
    lookup_name: Optional[str] = None


@dataclass(frozen=True)
class PotionDecision:
    status: str
    intents: Tuple[PotionIntent, ...] = ()
    local_return: Optional[bool] = None
    retry_ms: Optional[int] = None
    reason: str = ''
    availability_checks: Tuple[int, ...] = ()


def _available(snapshot, identifier):
    explicit = {a.inventory_id:a.available for a in snapshot.availability}
    if identifier in explicit:
        return explicit[identifier]
    if identifier in snapshot.available_inventory_ids:
        return True
    return False if snapshot.availability_complete else None


def _select(snapshot, candidates):
    checks = []
    for candidate in candidates:
        checks.append(candidate.inventory_id)
        available = _available(snapshot, candidate.inventory_id)
        if available is None:
            return None, tuple(checks), 'needs_availability'
        if available:
            return candidate, tuple(checks), 'selected'
    return None, tuple(checks), 'empty'


def _local_result(snapshot, kind, action_id):
    if snapshot.action_path == 'direct':
        return True
    for result in snapshot.local_action_results:
        if (result.kind, result.action_id) == (kind, action_id):
            return result.returned_nonzero
    return None


def potion_decision(settings: PotionSettings, snapshot: PotionSnapshot) -> PotionDecision:
    """Special->MP->HP. Alternate false still emits an attempted intent then
    continues; unknown result cannot be guessed to schedule HP or success retry.
    Direct branch returns1 locally regardless of the game/server outcome.
    """
    if not isinstance(settings, PotionSettings) or not isinstance(snapshot, PotionSnapshot):
        raise ValueError('PotionSettings/PotionSnapshot gerekli')
    if snapshot.state_3a is False or snapshot.state_3b is True or snapshot.state_3c is True:
        return PotionDecision('blocked', local_return=False, retry_ms=50, reason='raw_state_gate')
    if None in (snapshot.state_3a, snapshot.state_3b, snapshot.state_3c):
        return PotionDecision('needs_observation', reason='Raw3a/3b/3c gate gözlemi eksik')
    intents = []
    checks = []

    def attempt(kind, candidate=None, action_id=None, lookup_name=None):
        action = candidate.action_id if candidate else action_id
        if snapshot.action_path is None:
            return PotionDecision('needs_observation', tuple(intents), reason='Action path54 bilinmiyor', availability_checks=tuple(checks))
        result = _local_result(snapshot, kind, action)
        intents.append(PotionIntent(kind, candidate.inventory_id if candidate else None, action, snapshot.action_path, result, lookup_name))
        if result is None:
            return PotionDecision('needs_local_action_result', tuple(intents), reason='Alternate local return bilinmiyor', availability_checks=tuple(checks))
        if result:
            return PotionDecision('local_action', tuple(intents), True, 3000, availability_checks=tuple(checks))
        return None

    if settings.special_enabled:
        if snapshot.special_due is None:
            return PotionDecision('needs_observation', reason='Special slot durum gate bilinmiyor')
        if snapshot.special_due:
            if settings.special_selection == 1:
                if snapshot.magic_hammer_available is None:
                    return PotionDecision('needs_observation', reason='Named availability463950 bilinmiyor')
                if snapshot.magic_hammer_available:
                    decision = attempt('special', action_id=0x77ada, lookup_name='Magic Hammer')
                    if decision:
                        return decision
            else:
                # Source has two independent ifs; SECOND candidate overrides first.
                first, second = SPECIAL_NUMERIC
                checks.extend((first.inventory_id, second.inventory_id))
                second_available = _available(snapshot, second.inventory_id)
                if second_available is None:
                    return PotionDecision('needs_availability', availability_checks=tuple(checks), reason='Special ikinci aday sonucu bilinmiyor')
                if second_available:
                    chosen = second
                else:
                    first_available = _available(snapshot, first.inventory_id)
                    if first_available is None:
                        return PotionDecision('needs_availability', availability_checks=tuple(checks))
                    chosen = first if first_available else None
                if chosen is not None:
                    decision = attempt('special', chosen)
                    if decision:
                        return decision
    for kind, enabled, current, maximum, threshold, index in (
            ('mp', settings.mp_enabled, snapshot.current_mp, snapshot.maximum_mp, settings.mp_threshold, settings.mp_combo_index),
            ('hp', settings.hp_enabled, snapshot.current_hp, snapshot.maximum_hp, settings.hp_threshold, settings.hp_combo_index)):
        if not enabled or current > maximum * threshold // 100:
            continue
        candidate, observed, status = _select(snapshot, ordered_candidates(kind, index))
        checks.extend(observed)
        if status == 'needs_availability':
            return PotionDecision(status, tuple(intents), reason=kind + ' availability snapshot eksik', availability_checks=tuple(checks))
        if candidate is not None:
            decision = attempt(kind, candidate)
            if decision:
                return decision
    return PotionDecision('no_local_action', tuple(intents), False, 50, availability_checks=tuple(checks))


class PotionRunner:
    """0040f204 strict interval; zero return changes50ms without timestamp write.

    Wrapper guards are separately supplied. Unknown data does not advance state.
    This normal monotonically increasing clock excludes GetTickCount wraparound.
    """
    def __init__(self, interval_ms=0, last_action_ms=0):
        _int(interval_ms, 'Interval')
        _int(last_action_ms, 'Son action zamanı', 2**63-1)
        self.interval_ms = interval_ms
        self.last_action_ms = last_action_ms
        self.last_tick = None

    def tick(self, now_ms, settings, snapshot, guard_a=None, guard_b=None):
        _int(now_ms, 'Saat', 2**63-1)
        _bool(guard_a, 'Wrapper guard A', True)
        _bool(guard_b, 'Wrapper guard B', True)
        if now_ms < self.last_action_ms or (self.last_tick is not None and now_ms < self.last_tick):
            raise ValueError('Saat geriye gidemez')
        self.last_tick = now_ms
        if guard_a is True or guard_b is True:
            return PotionDecision('wrapper_blocked')
        if guard_a is None or guard_b is None:
            return PotionDecision('needs_observation', reason='Wrapper guardlar bilinmiyor')
        if now_ms - self.last_action_ms <= self.interval_ms:
            return PotionDecision('waiting', retry_ms=self.interval_ms)
        decision = potion_decision(settings, snapshot)
        if decision.local_return is True:
            self.last_action_ms = now_ms
            self.interval_ms = 3000
        elif decision.local_return is False:
            self.interval_ms = 50
        return decision
