"""Independent target selection from typed snapshots, Richard40bb30.

Two source pools are intentionally A/B: their game object classes are unknown.
Unsigned distance integers are supplied as the results of source __ftol calls;
we do not guess game coordinate layouts. This module never scans the process.
"""
import re
from dataclasses import dataclass, replace
from typing import Optional, Tuple


AUTO_EXCLUDED_NAMES = (
    '<Suspicious Chest>', 'Mine Guard', '<Captured Girl>',
    '<Captured Karus Warrior>', '[Monster Strategist]', '[Sundries]Ghost',
    "<Girl's Father>", "<Girl's Mother>", '<Scorpion King>',
    '<Princess of El Morad>', '<Forgotten Royal Knight>',
)


def _int(value, name, maximum=0xffffffff):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError(name + ' geçerli unsigned tam sayı olmalı')


def _bool(value, name, optional=False):
    if value is None and optional:
        return
    if type(value) is not bool:
        raise ValueError(name + ' boolean olmalı')


@dataclass(frozen=True)
class RejectedTarget:
    target_id: int
    timestamp_ms: int

    def __post_init__(self):
        _int(self.target_id, 'Hedef ID')
        _int(self.timestamp_ms, 'Ret zamanı', maximum=2**63-1)


def remember_rejection(records, target_id, now_ms):
    """40b5b8: duplicate ID leaves its original timestamp unchanged."""
    _int(target_id, 'Hedef ID')
    _int(now_ms, 'Saat', maximum=2**63-1)
    records = tuple(records)
    if any(not isinstance(r, RejectedTarget) for r in records):
        raise ValueError('Hedef ret listesi geçersiz')
    if any(r.target_id == target_id for r in records):
        return records
    return records + (RejectedTarget(target_id, now_ms),)


def prune_rejections(records, now_ms):
    """40b294: >4999 removes nonzero ID; increment after erase skips shifted row.

    This unusual one-pass behavior is preserved, rather than replacing it with
    a filter that removes all expired entries immediately. Zero IDs persist.
    """
    _int(now_ms, 'Saat', maximum=2**63-1)
    records = list(records)
    if any(not isinstance(r, RejectedTarget) or r.timestamp_ms > now_ms for r in records):
        raise ValueError('Hedef ret listesi/saat geçersiz')
    index = 0
    while index < len(records):
        record = records[index]
        if record.target_id and now_ms - record.timestamp_ms > 4999:
            records.pop(index)
        index += 1
    return tuple(records)


@dataclass(frozen=True)
class ResolverSettings:
    mode: int = 3
    raw_pool_selector: int = 0
    radius: int = 50
    run_to_target: bool = False
    return_to_center: bool = False
    entries: Tuple[str, ...] = ()
    retarget_wait_ms: int = 0
    extra_rejection_guard: bool = False

    def __post_init__(self):
        if type(self.mode) is not int or self.mode not in (2, 3):
            raise ValueError('Bu resolver yalnız name/ID2 ve auto3 modlarını destekler')
        _int(self.raw_pool_selector, 'Raw pool selector')
        _int(self.radius, 'Radius', 0x7fffffff)
        _int(self.retarget_wait_ms, 'Retarget beklemesi')
        for name in ('run_to_target', 'return_to_center', 'extra_rejection_guard'):
            _bool(getattr(self, name), name)
        if not isinstance(self.entries, tuple) or any(not isinstance(e, str) for e in self.entries):
            raise ValueError('Hedef name/ID listesi geçersiz')


@dataclass(frozen=True)
class ResolverCandidate:
    object_key: str
    target_id: int
    name: str
    self_distance: int
    center_distance: int
    status_byte: int = 0
    state_code: int = 0
    visibility: Optional[bool] = None
    repeated_visibility: Optional[bool] = None

    def __post_init__(self):
        if not isinstance(self.object_key, str) or not self.object_key or not isinstance(self.name, str):
            raise ValueError('Aday nesne anahtarı/name geçersiz')
        for name in ('target_id', 'self_distance', 'center_distance', 'state_code'):
            _int(getattr(self, name), name)
        _int(self.status_byte, 'Status byte', 255)
        _bool(self.visibility, 'Visibility callback', True)
        _bool(self.repeated_visibility, 'İkinci visibility callback', True)


@dataclass(frozen=True)
class ResolverSnapshot:
    pool_a: Tuple[ResolverCandidate, ...] = ()
    pool_b: Tuple[ResolverCandidate, ...] = ()
    complete: bool = False

    def __post_init__(self):
        _bool(self.complete, 'Eksiksiz aday snapshot')
        for rows in (self.pool_a, self.pool_b):
            if not isinstance(rows, tuple) or any(not isinstance(c, ResolverCandidate) for c in rows):
                raise ValueError('Aday pool geçersiz')


@dataclass(frozen=True)
class NameMatch:
    status: str
    matched: Optional[bool] = None
    unresolved_entry: Optional[str] = None


def match_name_or_id(name, target_id, entries):
    """40a0e8: empty name/low16ID0 false; equality OR StrToInt64==low16ID.

    ASCII equality is independently implemented. Non-ASCII ANSI conversion,
    nondecimal StrToInt64 forms and failed conversion exception handling remain
    explicit contracts; they never silently become 'no match'. List order is
    retained because conversion is only reached after name inequality.
    """
    if not isinstance(name, str) or not isinstance(entries, tuple) or any(not isinstance(e, str) for e in entries):
        raise ValueError('Hedef liste karşılaştırma girdisi geçersiz')
    _int(target_id, 'Hedef ID')
    identifier = target_id & 0xffff
    if not name or not identifier:
        return NameMatch('evaluated', False)
    if not name.isascii():
        return NameMatch('needs_string_codec')
    for entry in entries:
        if not entry.isascii():
            return NameMatch('needs_string_codec', unresolved_entry=entry)
        if entry == name:
            return NameMatch('evaluated', True)
        if not re.fullmatch(r'[+-]?[0-9]+', entry):
            return NameMatch('unresolved_numeric_conversion', unresolved_entry=entry)
        number = int(entry, 10)
        if not -(2**63) <= number < 2**63:
            return NameMatch('unresolved_numeric_conversion', unresolved_entry=entry)
        if number == identifier:
            return NameMatch('evaluated', True)
    return NameMatch('evaluated', False)


@dataclass(frozen=True)
class ResolverDecision:
    status: str
    candidate: Optional[ResolverCandidate] = None
    reason: str = ''
    unresolved_object_keys: Tuple[str, ...] = ()


def resolve_target(settings: ResolverSettings, snapshot: ResolverSnapshot, rejected=()) -> ResolverDecision:
    """40bb30: exact filter order + unsigned integer distance minimum.

    Initial gate permits self<=radius OR center<=radius; final self comparison
    always applies. Run+return additionally requires center<=radius. Ties replace
    the previous candidate, including when the second pool is processed later.
    """
    if not isinstance(settings, ResolverSettings) or not isinstance(snapshot, ResolverSnapshot):
        raise ValueError('ResolverSettings/ResolverSnapshot gerekli')
    rejected = tuple(rejected)
    if any(not isinstance(r, RejectedTarget) for r in rejected):
        raise ValueError('Ret listesi geçersiz')
    if not snapshot.complete:
        return ResolverDecision('needs_candidate_snapshot', reason='Kaynak iki pool tamlığı doğrulanmadı')
    pool_order = (() if settings.raw_pool_selector == 1 else snapshot.pool_a) + (() if settings.raw_pool_selector == 2 else snapshot.pool_b)
    excluded_ids = {r.target_id for r in rejected}
    best = None
    best_distance = settings.radius
    unknown = []
    unknown_reasons = []
    for candidate in pool_order:
        if candidate.status_byte == 10 or candidate.state_code in (4, 5, 13):
            continue
        if candidate.self_distance > settings.radius and candidate.center_distance > settings.radius:
            continue
        if candidate.visibility is False:
            continue
        if not candidate.target_id or candidate.target_id in excluded_ids:
            continue
        if candidate.self_distance > best_distance:
            continue
        if settings.run_to_target and settings.return_to_center and candidate.center_distance > settings.radius:
            continue
        uncertainty = None
        if candidate.visibility is None:
            uncertainty = 'Visibility callback464c2c sonucu eksik'
        if settings.mode == 2:
            if not settings.run_to_target:
                if candidate.repeated_visibility is False:
                    continue
                if candidate.repeated_visibility is None:
                    uncertainty = 'İkinci visibility callback sonucu eksik'
            match = match_name_or_id(candidate.name, candidate.target_id, settings.entries)
            if match.matched is False:
                continue
            if match.matched is None:
                uncertainty = match.status + (': ' + match.unresolved_entry if match.unresolved_entry is not None else '')
        elif candidate.name in AUTO_EXCLUDED_NAMES:
            continue
        if uncertainty is not None:
            unknown.append(candidate)
            unknown_reasons.append(uncertainty)
        else:
            best = candidate
            best_distance = candidate.self_distance
    potentially_winning = [(c, reason) for c, reason in zip(unknown, unknown_reasons) if c.self_distance <= best_distance]
    if potentially_winning:
        return ResolverDecision('needs_observation', best, '; '.join(dict.fromkeys(reason for _, reason in potentially_winning)), tuple(c.object_key for c, _ in potentially_winning))
    return ResolverDecision('selected' if best is not None else 'cleared', best)


@dataclass(frozen=True)
class CurrentTargetObservation:
    target_id: int
    object_exists: Optional[bool] = None
    self_distance: Optional[float] = None
    status_byte: Optional[int] = None
    raw_word_a: Optional[int] = None
    raw_word_b: Optional[int] = None
    special_context: Optional[bool] = None
    state_byte: Optional[int] = None

    def __post_init__(self):
        _int(self.target_id, 'Mevcut hedef ID')
        _bool(self.object_exists, 'Nesne var', True)
        _bool(self.special_context, 'Özel context', True)
        for name, maximum in (('status_byte',255), ('raw_word_a',65535), ('raw_word_b',65535), ('state_byte',255)):
            value = getattr(self, name)
            if value is not None:
                _int(value, name, maximum)
        if self.self_distance is not None and (type(self.self_distance) not in (float,int) or not 0 <= self.self_distance < float('inf')):
            raise ValueError('Mevcut hedef mesafesi geçersiz')


@dataclass(frozen=True)
class CurrentTargetDecision:
    status: str
    needs_retarget: Optional[bool] = None
    clear_state: bool = False
    add_rejection: bool = False
    reason: str = ''


def evaluate_current_target(settings: ResolverSettings, current: CurrentTargetObservation):
    """40b978 rejection predicate; raw fields are unnamed, not guessed as HP."""
    if not isinstance(settings, ResolverSettings) or not isinstance(current, CurrentTargetObservation):
        raise ValueError('ResolverSettings/CurrentTargetObservation gerekli')
    if not current.target_id:
        return CurrentTargetDecision('evaluated', True)
    if current.object_exists is None:
        return CurrentTargetDecision('needs_observation', reason='Nesne helper464a10 sonucu eksik')
    if not current.object_exists:
        return CurrentTargetDecision('evaluated', True, clear_state=True)
    if not settings.run_to_target:
        if current.self_distance is None:
            return CurrentTargetDecision('needs_observation', reason='Float self distance eksik')
        if current.self_distance > settings.radius:
            return CurrentTargetDecision('evaluated', True)
    if current.status_byte is None or current.raw_word_a is None or current.raw_word_b is None:
        return CurrentTargetDecision('needs_observation', reason='Statusbyte/raw word çift eksik')
    rejected_condition = current.status_byte == 10 or (current.raw_word_a > 0 and current.raw_word_b == 0)
    if not rejected_condition:
        return CurrentTargetDecision('evaluated', False)
    if settings.run_to_target and settings.extra_rejection_guard:
        if current.special_context is None:
            return CurrentTargetDecision('needs_observation', reason='Özel context yardımcıları eksik')
        if not current.special_context:
            if current.state_byte is None:
                return CurrentTargetDecision('needs_observation', reason='Raw statebyte eksik')
            if current.state_byte != 5:
                return CurrentTargetDecision('evaluated', False)
    return CurrentTargetDecision('evaluated', True, add_rejection=True)


class TargetResolver:
    """40d224 wrapper: cleanup -> retarget predicate -> arm -> delayed resolve.

    This runner has no game memory state. Return candidate is a local snapshot
    decision, never a pointer write. Unknown observations don't advance timers.
    """
    def __init__(self, settings: ResolverSettings):
        if not isinstance(settings, ResolverSettings):
            raise ValueError('ResolverSettings gerekli')
        self.settings = settings
        self.rejected = ()
        self.armed_ms = None
        self.last_tick = None

    def tick(self, now_ms, current: CurrentTargetObservation, candidates: ResolverSnapshot):
        _int(now_ms, 'Saat', maximum=2**63-1)
        if self.last_tick is not None and now_ms < self.last_tick:
            raise ValueError('Saat geriye gidemez')
        self.last_tick = now_ms
        self.rejected = prune_rejections(self.rejected, now_ms)
        check = evaluate_current_target(self.settings, current)
        if check.needs_retarget is None:
            return ResolverDecision('needs_observation', reason=check.reason)
        if not check.needs_retarget:
            # Source does not reset the armed flag on the false predicate path.
            return ResolverDecision('retained')
        if check.add_rejection:
            self.rejected = remember_rejection(self.rejected, current.target_id, now_ms)
        if self.armed_ms is None:
            self.armed_ms = now_ms
            return ResolverDecision('retarget_armed', reason='clear_current_state' if check.clear_state else '')
        if now_ms - self.armed_ms < self.settings.retarget_wait_ms:
            return ResolverDecision('waiting', reason='clear_current_state' if check.clear_state else '')
        decision = resolve_target(self.settings, candidates, self.rejected)
        if decision.status in ('selected', 'cleared'):
            self.armed_ms = None
        return decision
