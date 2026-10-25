"""Source-backed, pure support selection. No targeting scan or game actions.

Richard helpers: 4cf8b8/4cecc0 (Priest), 4da25c/4de490 (Minor),
499620/499358 (TP), 471c38 (Kurian), 40a39c/40d224 (target state).
All timestamps are injected monotonic ms. Producer/ABI and server results are
external. An intent does not change HP, inventory or acknowledged timestamps.
"""
import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


def _int(value, name, maximum=None):
    if type(value) is not int or value < 0 or (maximum is not None and value > maximum):
        raise ValueError(name + ' negatif olmayan tam sayı olmalı')


def _bool(value, name, optional=False):
    if optional and value is None:
        return
    if type(value) is not bool:
        raise ValueError(name + ' boolean olmalı')


def _percent(value):
    _int(value, 'Yüzde', 100)


@dataclass(frozen=True)
class Vitals:
    actor_id: int
    current_hp: int
    maximum_hp: int
    current_mp: int = 0

    def __post_init__(self):
        for name in ('actor_id', 'current_hp', 'maximum_hp', 'current_mp'):
            _int(getattr(self, name), name)
        if not self.actor_id or not self.maximum_hp or self.current_hp > self.maximum_hp:
            raise ValueError('Kimlik ve maksimum HP pozitif, HP maksimumdan küçük/eşit olmalı')


@dataclass(frozen=True)
class PartyMember:
    vitals: Vitals
    name: str = ''
    last_heal_ms: int = 0
    last_tp_ms: int = 0
    target_available: Optional[bool] = None
    distance: Optional[float] = None
    mage_eligible: Optional[bool] = None

    def __post_init__(self):
        if not isinstance(self.vitals, Vitals) or not isinstance(self.name, str):
            raise ValueError('Party üyesi geçersiz')
        _int(self.last_heal_ms, 'Son heal zamanı')
        _int(self.last_tp_ms, 'Son TP zamanı')
        _bool(self.target_available, 'Hedef yardımcı sonucu', True)
        _bool(self.mage_eligible, 'Mage eligibility', True)
        if self.distance is not None and (type(self.distance) not in (int, float) or not math.isfinite(self.distance) or self.distance < 0):
            raise ValueError('Mesafe sonlu ve negatif olmayan sayı olmalı')


@dataclass(frozen=True)
class SupportIntent:
    kind: str
    target_id: int
    skill_id: Optional[int] = None
    hp_deficit: Optional[int] = None


@dataclass(frozen=True)
class SupportDecision:
    status: str
    intent: Optional[SupportIntent] = None
    reason: str = ''
    local_lock_ms: Optional[int] = None
    consumes_retry: bool = False


@dataclass(frozen=True)
class SupportSnapshot:
    now_ms: int
    actor: Vitals
    members: Tuple[PartyMember, ...] = ()
    party_count: Optional[int] = None
    party_complete: bool = False
    global_blocked: Optional[bool] = None
    route_guard_active: Optional[bool] = None
    alternate_action_path: Optional[bool] = None
    self_heal_ready: Optional[bool] = None
    party_heal_ready: Optional[bool] = None
    minor_action_ready: Optional[bool] = None
    kurian_action_ready: Optional[bool] = None
    tp_action_ready: Optional[bool] = None
    unnamed_stat: Optional[int] = None
    named_tp_target_id: Optional[int] = None
    last_self_heal_ms: int = 0
    last_minor_ms: int = 0

    def __post_init__(self):
        _int(self.now_ms, 'Saat')
        if not isinstance(self.actor, Vitals):
            raise ValueError('Vitals gerekli')
        if not isinstance(self.members, tuple) or any(not isinstance(m, PartyMember) for m in self.members):
            raise ValueError('Party üyeleri geçersiz')
        if len({m.vitals.actor_id for m in self.members}) != len(self.members):
            raise ValueError('Party kimlikleri benzersiz olmalı')
        _bool(self.party_complete, 'Party eksiksiz')
        for name in ('global_blocked', 'route_guard_active', 'alternate_action_path', 'self_heal_ready', 'party_heal_ready', 'minor_action_ready', 'kurian_action_ready', 'tp_action_ready'):
            _bool(getattr(self, name), name, True)
        if self.party_count is not None:
            _int(self.party_count, 'Party sayısı')
        if self.unnamed_stat is not None:
            _int(self.unnamed_stat, 'Stat yardımcı sonucu')
        if self.named_tp_target_id is not None:
            _int(self.named_tp_target_id, 'İsim TP resolver kimliği')
        for name in ('last_self_heal_ms', 'last_minor_ms'):
            value = getattr(self, name)
            _int(value, name)
            if value > self.now_ms:
                raise ValueError('Son işlem zamanı gelecekte olamaz')
        for member in self.members:
            if max(member.last_heal_ms, member.last_tp_ms) > self.now_ms:
                raise ValueError('Party zaman kaydı gelecekte olamaz')


@dataclass(frozen=True)
class PartySelection:
    status: str
    member: Optional[PartyMember] = None


def _low_hp(vitals, threshold):
    return vitals.current_hp <= vitals.maximum_hp * threshold // 100


def select_party_member(snapshot: SupportSnapshot, threshold: int, kind='heal') -> PartySelection:
    """Lowest absolute currentHP, source initial ceiling50000, last tie wins.

    HEAL: target helper nonzero + int(distance)<29. TP: eligibility must be
    supplied; x87 decompiler distance expression is not treated as a formula.
    Unknown potentially winning members prevent speculative selection.
    """
    if not isinstance(snapshot, SupportSnapshot) or kind not in ('heal', 'tp'):
        raise ValueError('Party seçim girdisi geçersiz')
    _percent(threshold)
    if snapshot.party_count is None or not snapshot.party_complete:
        return PartySelection('needs_party_observation')
    if snapshot.party_count < 2:
        return PartySelection('no_candidate')
    best = None
    best_hp = 50000
    unknown_hp = []
    for member in snapshot.members:
        vitals = member.vitals
        timestamp = member.last_heal_ms if kind == 'heal' else member.last_tp_ms
        if (vitals.actor_id == snapshot.actor.actor_id or vitals.current_hp <= 0 or
                snapshot.now_ms - timestamp <= 2499 or not _low_hp(vitals, threshold) or vitals.current_hp > 50000):
            continue
        if kind == 'heal':
            if member.target_available is False:
                continue
            unknown = member.target_available is None or member.distance is None
            eligible = not unknown and int(member.distance) < 29
        else:
            unknown = member.mage_eligible is None
            eligible = member.mage_eligible is True
        if unknown:
            unknown_hp.append(vitals.current_hp)
        elif eligible and vitals.current_hp <= best_hp:
            best = member
            best_hp = vitals.current_hp
    if any(hp <= best_hp for hp in unknown_hp):
        return PartySelection('needs_member_observation')
    return PartySelection('selected' if best is not None else 'no_candidate', best)


def _gate(snapshot):
    if snapshot.global_blocked is None:
        return SupportDecision('needs_observation', reason='Ortak çalışma gate bilinmiyor')
    if snapshot.global_blocked:
        return SupportDecision('blocked', reason='global_gate')
    return None


def _intent(snapshot, kind, target_id, skill_id=None, hp_deficit=None, lock=True):
    if lock and snapshot.alternate_action_path is None:
        return SupportDecision('needs_observation', reason='Eylem yolu bilinmiyor')
    duration = (2000 if snapshot.alternate_action_path else 1500) if lock else None
    return SupportDecision('intent', SupportIntent(kind, target_id, skill_id, hp_deficit), local_lock_ms=duration, consumes_retry=True)


@dataclass(frozen=True)
class PriestSettings:
    self_enabled: bool = False
    self_threshold: int = 50
    self_skill_id: int = 0
    party_enabled: bool = False
    party_threshold: int = 50
    party_skill_id: int = 0
    no_heal_on_route: bool = False

    def __post_init__(self):
        for name in ('self_enabled', 'party_enabled', 'no_heal_on_route'):
            _bool(getattr(self, name), name)
        _percent(self.self_threshold)
        _percent(self.party_threshold)
        _int(self.self_skill_id, 'Self skill')
        _int(self.party_skill_id, 'Party skill')


def priest_heal(settings: PriestSettings, snapshot: SupportSnapshot) -> SupportDecision:
    if not isinstance(settings, PriestSettings) or not isinstance(snapshot, SupportSnapshot):
        raise ValueError('PriestSettings/SupportSnapshot gerekli')
    gate = _gate(snapshot)
    if gate:
        return gate
    if settings.no_heal_on_route:
        if snapshot.route_guard_active is None:
            return SupportDecision('needs_observation', reason='Rota engel gate bilinmiyor')
        if snapshot.route_guard_active:
            return SupportDecision('blocked', reason='route_heal_guard')
    actor = snapshot.actor
    if (settings.self_enabled and actor.maximum_hp - actor.current_hp > 0 and
            snapshot.now_ms - snapshot.last_self_heal_ms > 2000 and _low_hp(actor, settings.self_threshold)):
        if snapshot.self_heal_ready is None:
            return SupportDecision('needs_observation', reason='Self heal hazırlığı bilinmiyor')
        if snapshot.self_heal_ready:
            return _intent(snapshot, 'priest_self_heal', actor.actor_id, settings.self_skill_id, actor.maximum_hp - actor.current_hp)
    if settings.party_enabled:
        selection = select_party_member(snapshot, settings.party_threshold)
        if selection.status.startswith('needs_'):
            return SupportDecision('needs_observation', reason=selection.status)
        if selection.member is not None:
            if snapshot.party_heal_ready is None:
                return SupportDecision('needs_observation', reason='Party heal hazırlığı bilinmiyor')
            if snapshot.party_heal_ready:
                member = selection.member.vitals
                return _intent(snapshot, 'priest_party_heal', member.actor_id, settings.party_skill_id, member.maximum_hp - member.current_hp)
    return SupportDecision('no_action')


@dataclass(frozen=True)
class MinorSettings:
    enabled: bool = False
    threshold: int = 50
    interval_ms: int = 100

    def __post_init__(self):
        _bool(self.enabled, 'Minor açık')
        _percent(self.threshold)
        _int(self.interval_ms, 'Minor aralığı')


def rogue_minor(settings: MinorSettings, snapshot: SupportSnapshot) -> SupportDecision:
    if not isinstance(settings, MinorSettings) or not isinstance(snapshot, SupportSnapshot):
        raise ValueError('MinorSettings/SupportSnapshot gerekli')
    if not settings.enabled or not _low_hp(snapshot.actor, settings.threshold):
        return SupportDecision('no_action')
    if snapshot.now_ms - snapshot.last_minor_ms < settings.interval_ms:
        return SupportDecision('waiting', reason='minor_interval')
    if snapshot.unnamed_stat is None:
        return SupportDecision('needs_observation', reason='Minor stat yardımcı sonucu bilinmiyor')
    if snapshot.unnamed_stat <= 4 or snapshot.actor.current_mp <= 99:
        return SupportDecision('no_action')
    if snapshot.alternate_action_path is None:
        return SupportDecision('needs_observation', reason='Minor eylem yolu bilinmiyor')
    if snapshot.alternate_action_path:
        if snapshot.minor_action_ready is None:
            return SupportDecision('needs_observation', reason='Minor durum yardımcı sonucu bilinmiyor')
        if not snapshot.minor_action_ready:
            # 4da25c still returns1 even when this branch does not issue a call.
            return SupportDecision('local_retry_consumed', reason='minor_state_gate', consumes_retry=True)
    return _intent(snapshot, 'rogue_minor', snapshot.actor.actor_id, lock=False)


@dataclass(frozen=True)
class MageSettings:
    low_hp_tp: bool = False
    threshold: int = 50
    continuous_name_tp: bool = False
    target_name: str = ''

    def __post_init__(self):
        _bool(self.low_hp_tp, 'Düşük HP TP')
        _bool(self.continuous_name_tp, 'İsim TP')
        _percent(self.threshold)
        if not isinstance(self.target_name, str):
            raise ValueError('TP hedef adı metin olmalı')


def mage_tp(settings: MageSettings, snapshot: SupportSnapshot) -> SupportDecision:
    if not isinstance(settings, MageSettings) or not isinstance(snapshot, SupportSnapshot):
        raise ValueError('MageSettings/SupportSnapshot gerekli')
    gate = _gate(snapshot)
    if gate:
        return gate
    if not settings.low_hp_tp and not settings.continuous_name_tp:
        return SupportDecision('no_action')
    if snapshot.party_count is None or not snapshot.party_complete or snapshot.unnamed_stat is None:
        return SupportDecision('needs_observation', reason='TP party/stat gözlemi eksik')
    if snapshot.party_count < 2 or snapshot.unnamed_stat <= 9 or snapshot.actor.current_mp <= 4:
        return SupportDecision('no_action')
    if settings.low_hp_tp:
        if not 0 < settings.threshold < 100:
            return SupportDecision('no_action', reason='tp_threshold_guard')
        selection = select_party_member(snapshot, settings.threshold, 'tp')
        if selection.status.startswith('needs_'):
            return SupportDecision('needs_observation', reason=selection.status)
        member = selection.member
    else:
        if not settings.target_name:
            return SupportDecision('no_action')
        if snapshot.named_tp_target_id is None:
            return SupportDecision('needs_observation', reason='İsim TP resolver sonucu yok')
        matches = [m for m in snapshot.members if m.vitals.actor_id == snapshot.named_tp_target_id]
        member = matches[0] if matches else None
        if member is not None:
            if snapshot.now_ms - member.last_tp_ms < 3001:
                return SupportDecision('waiting', reason='name_tp_interval')
            if member.mage_eligible is None:
                return SupportDecision('needs_observation', reason='TP hedef helper gate bilinmiyor')
            if not member.mage_eligible:
                member = None
    if member is None:
        return SupportDecision('no_action')
    if snapshot.tp_action_ready is None:
        return SupportDecision('needs_observation', reason='TP eylem hazırlığı bilinmiyor')
    if not snapshot.tp_action_ready:
        return SupportDecision('blocked', reason='tp_action_gate')
    return _intent(snapshot, 'mage_party_tp', member.vitals.actor_id)


@dataclass(frozen=True)
class KurianSettings:
    enabled: bool = False
    threshold: int = 50

    def __post_init__(self):
        _bool(self.enabled, 'Kurian heal')
        _percent(self.threshold)


def kurian_heal(settings: KurianSettings, snapshot: SupportSnapshot) -> SupportDecision:
    if not isinstance(settings, KurianSettings) or not isinstance(snapshot, SupportSnapshot):
        raise ValueError('KurianSettings/SupportSnapshot gerekli')
    gate = _gate(snapshot)
    if gate:
        return gate
    if not settings.enabled or not _low_hp(snapshot.actor, settings.threshold):
        return SupportDecision('no_action')
    if snapshot.unnamed_stat is None or snapshot.kurian_action_ready is None:
        return SupportDecision('needs_observation', reason='Kurian stat/skill gate eksik')
    if not snapshot.kurian_action_ready:
        return SupportDecision('blocked', reason='kurian_skill_gate')
    stat, mp = snapshot.unnamed_stat, snapshot.actor.current_mp
    if stat >= 60 and mp >= 1000:
        skill = 0x2f8
    elif stat >= 35 and mp >= 350:
        skill = 0x2df
    elif stat >= 25 and mp >= 100:
        skill = 0x2d5
    elif stat > 2 and mp > 99:
        skill = 700
    else:
        return SupportDecision('no_action')
    return SupportDecision('intent', SupportIntent('kurian_self_heal', snapshot.actor.actor_id, skill), local_lock_ms=1700, consumes_retry=True)


class TargetMode(Enum):
    MANUAL = 1
    NAME_OR_ID = 2
    AUTOMATIC = 3
    LEADER = 4
    AUTO_Z = 5


@dataclass(frozen=True)
class TargetState:
    target_id: int = 0
    object_available: bool = False
    ready: bool = False

    def __post_init__(self):
        _int(self.target_id, 'Hedef ID')
        _bool(self.object_available, 'Hedef nesne var')
        _bool(self.ready, 'Hedef hazır')
        if self.ready and not self.target_id:
            raise ValueError('Hazır hedefin IDsi sıfır olamaz')


@dataclass(frozen=True)
class TargetCandidate:
    target_id: int
    object_available: Optional[bool] = None
    manual_eligible: Optional[bool] = None

    def __post_init__(self):
        _int(self.target_id, 'Hedef ID')
        _bool(self.object_available, 'Hedef nesne', True)
        _bool(self.manual_eligible, 'Manuel uygunluk', True)


@dataclass(frozen=True)
class TargetSnapshot:
    active: bool
    blocked: bool
    manual: Optional[TargetCandidate] = None
    auto_z: Optional[TargetCandidate] = None
    leader: Optional[TargetCandidate] = None
    party_count: Optional[int] = None
    leader_gate: Optional[bool] = None
    resolved_state: Optional[TargetState] = None

    def __post_init__(self):
        _bool(self.active, 'Bot aktif')
        _bool(self.blocked, 'Hedef gate')
        _bool(self.leader_gate, 'Leader gate', True)
        if self.party_count is not None:
            _int(self.party_count, 'Party sayısı')
        for name in ('manual', 'auto_z', 'leader'):
            value = getattr(self, name)
            if value is not None and not isinstance(value, TargetCandidate):
                raise ValueError('Geçersiz hedef gözlemi')
        if self.resolved_state is not None and not isinstance(self.resolved_state, TargetState):
            raise ValueError('Hedef çözümleyici state geçersiz')


@dataclass(frozen=True)
class TargetDecision:
    status: str
    state: TargetState
    reason: str = ''


def target_step(mode: TargetMode, snapshot: TargetSnapshot, previous=TargetState()) -> TargetDecision:
    """Accept observed helpers only; NAME/AUTO scan is an explicit adapter seam.

    Inactive/gated paths retain old state, per40d224. Stop cleanup is a separate
    caller operation (TargetState()). Leader out-of-range raw branch is not
    guessed from x87 pseudocode. AUTO_Z source marks ready for nonzero targetID
    without checking object helper result; this asymmetry is retained.
    """
    if not isinstance(mode, TargetMode) or not isinstance(snapshot, TargetSnapshot) or not isinstance(previous, TargetState):
        raise ValueError('TargetMode/TargetSnapshot/TargetState gerekli')
    if not snapshot.active or snapshot.blocked:
        return TargetDecision('retained', previous, 'target_gate')
    if mode in (TargetMode.NAME_OR_ID, TargetMode.AUTOMATIC):
        if snapshot.resolved_state is None:
            return TargetDecision('needs_resolver', previous, 'Hedef liste/arama yardımcıları çözümlenmedi')
        return TargetDecision('adapter_state', snapshot.resolved_state, 'Harici resolver sonucu; bu motor tarama yapmaz')
    if mode == TargetMode.LEADER:
        if snapshot.party_count is None:
            return TargetDecision('needs_observation', previous, 'Party sayısı yok')
        if snapshot.party_count < 2:
            return TargetDecision('retained', previous, 'leader_party_gate')
        candidate = snapshot.leader
    else:
        candidate = snapshot.manual if mode == TargetMode.MANUAL else snapshot.auto_z
    if candidate is None:
        return TargetDecision('needs_observation', previous, 'Hedef helper sonucu yok')
    if candidate.target_id == 0:
        return TargetDecision('cleared', TargetState())
    if candidate.object_available is None:
        return TargetDecision('needs_observation', previous, 'Hedef nesne helper sonucu yok')
    if mode == TargetMode.MANUAL:
        if not candidate.object_available or candidate.manual_eligible is False:
            return TargetDecision('cleared', TargetState())
        if candidate.manual_eligible is None:
            return TargetDecision('needs_observation', previous, 'Manuel uygunluk helper sonucu yok')
    if mode == TargetMode.LEADER:
        if not candidate.object_available:
            return TargetDecision('cleared', TargetState())
        if snapshot.leader_gate is not True:
            return TargetDecision('unresolved' if snapshot.leader_gate is False else 'needs_observation', previous, 'Leader mesafe/durum branch semantiği eksik')
    return TargetDecision('selected', TargetState(candidate.target_id, candidate.object_available, True))
