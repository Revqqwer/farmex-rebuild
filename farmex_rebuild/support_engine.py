"""Pure Richard control policies. Intents never perform game or OS actions.

Callers supply validated observations; an intent is a requested local action,
not evidence of acceptance by the game. Source map accompanies this module.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class Action(str, Enum):
    STOP = "stop_bot"
    ALARM = "alarm"
    CONTROL_ACTION = "configured_control_action"
    CLOSE_PROCESS = "close_current_process"
    SHUTDOWN = "shutdown_computer"
    RELOG = "begin_relog"
    COUNTDOWN = "relog_countdown"
    RELOG_READY = "relog_wait_complete"
    ACCEPT_PARTY = "accept_party"
    REJECT_PARTY = "reject_party"
    TOWN = "town"
    CAPTCHA_WINDOW = "show_captcha_window"
    CRASH_ITEM = "crash_abyss_gem"


@dataclass(frozen=True)
class Intent:
    action: Action
    reason: str
    value: Optional[int] = None


@dataclass(frozen=True)
class GuardConfig:
    np_enabled: bool = False
    coin_limit: Optional[int] = None
    target_level: Optional[int] = None
    close_time: Optional[Tuple[int, int]] = None
    party_minimum: Optional[int] = None
    party_stop: bool = False
    party_alarm: bool = False
    priest_stop: bool = False
    priest_alarm: bool = False

    def __post_init__(self):
        if self.coin_limit is not None and not 0 <= self.coin_limit <= 0xffffffff:
            raise ValueError("Only the confirmed 32-bit coin threshold is supported")
        if self.close_time is not None:
            hour, minute = self.close_time
            if not 0 <= hour <= 23 or not 0 <= minute <= 59:
                raise ValueError("Invalid local close time")
        if self.party_minimum is not None and self.party_minimum < 0:
            raise ValueError("Party minimum cannot be negative")


@dataclass(frozen=True)
class GuardSnapshot:
    mode: int = 0
    np_reader_result: Optional[int] = None
    coins: Optional[int] = None
    level: Optional[int] = None
    local_time: Optional[Tuple[int, int]] = None
    party_count: Optional[int] = None
    party_has_priest: Optional[bool] = None


def _party_intents(reason, stop, alarm):
    return tuple(Intent(action, reason) for action, enabled in
                 ((Action.STOP, stop), (Action.ALARM, alarm)) if enabled)


def evaluate_guards(config: GuardConfig, snapshot: GuardSnapshot) -> Tuple[Intent, ...]:
    """00458f98: return only the first matching guard's actions.

    Unknown observations do not match; the caller must report observation gaps.
    np_reader_result is the helper's result, not an assumed NP threshold.
    """
    reason = None
    if config.np_enabled and snapshot.np_reader_result == 0:
        reason = "np_reader_zero"
    elif (config.coin_limit is not None and snapshot.coins is not None
          and snapshot.coins <= config.coin_limit):
        reason = "coin_limit"
    elif config.target_level is not None and snapshot.level == config.target_level:
        reason = "target_level"
    if reason:
        return (Intent(Action.STOP, reason), Intent(Action.CONTROL_ACTION, reason))
    if config.close_time is not None and snapshot.local_time == config.close_time:
        return (Intent(Action.CLOSE_PROCESS, "local_clock_match"),)
    if snapshot.mode != 0:
        return ()
    if (config.party_minimum is not None and snapshot.party_count is not None
        and snapshot.party_count < config.party_minimum
        and (config.party_stop or config.party_alarm)):
        return _party_intents("party_count", config.party_stop, config.party_alarm)
    if config.priest_stop or config.priest_alarm:
        missing = (snapshot.party_count is not None and snapshot.party_count <= 1)
        missing = missing or snapshot.party_has_priest is False
        if missing:
            return _party_intents("priest_missing", config.priest_stop, config.priest_alarm)
    return ()


class DCChoice(int, Enum):
    SHUTDOWN = 0
    CLOSE_PROCESS = 1
    RELOG = 2


@dataclass(frozen=True)
class DCConfig:
    enabled: bool = False
    alarm: bool = False
    choice: Optional[DCChoice] = None
    wait_seconds: int = 0

    def __post_init__(self):
        if self.wait_seconds < 0:
            raise ValueError("Wait cannot be negative")
        if self.choice is not None and not isinstance(self.choice, DCChoice):
            raise ValueError("An explicit DCChoice is required")


@dataclass(frozen=True)
class RelogState:
    started_ms: Optional[int] = None
    last_notice_ms: Optional[int] = None
    waiting: bool = False


def begin_dc(config: DCConfig, bot_active: bool, now_ms: int):
    """00459970: one observed disconnect edge, not every disconnected tick."""
    if now_ms < 0:
        raise ValueError("Negative monotonic time")
    if not config.enabled:
        return RelogState(), ()
    intents = list(_party_intents("disconnected", bot_active, config.alarm))
    choices = {DCChoice.SHUTDOWN: Action.SHUTDOWN,
               DCChoice.CLOSE_PROCESS: Action.CLOSE_PROCESS, DCChoice.RELOG: Action.RELOG}
    if config.choice is not None:
        intents.append(Intent(choices[config.choice], "disconnected"))
    state = RelogState(now_ms, now_ms, True) if config.choice == DCChoice.RELOG else RelogState()
    return state, tuple(intents)


def advance_relog(state: RelogState, wait_seconds: int, now_ms: int):
    if wait_seconds < 0:
        raise ValueError("Wait cannot be negative")
    if not state.waiting:
        return state, ()
    if state.started_ms is None or state.last_notice_ms is None or now_ms < state.started_ms:
        raise ValueError("Invalid relog timeline")
    remaining = wait_seconds * 1000 - (now_ms - state.started_ms)
    if remaining <= 0:
        return RelogState(state.started_ms, state.last_notice_ms, False), (
            Intent(Action.RELOG_READY, "wait_complete"),)
    if now_ms - state.last_notice_ms >= 1000:
        updated = RelogState(state.started_ms, now_ms, True)
        return updated, (Intent(Action.COUNTDOWN, "wait_remaining", (remaining + 999) // 1000),)
    return state, ()


@dataclass(frozen=True)
class PartyPolicy:
    enabled: bool = False
    accept_everyone: bool = False
    names: Tuple[str, ...] = ()
    reject_unlisted: bool = False


def party_invitation(policy: PartyPolicy, name: str) -> Tuple[Intent, ...]:
    """004cbfac/004cbecc: exact comparison, no case folding or wildcard."""
    if not policy.enabled:
        return ()
    if policy.accept_everyone or name in policy.names:
        return (Intent(Action.ACCEPT_PARTY, "party_invitation"),)
    if policy.reject_unlisted:
        return (Intent(Action.REJECT_PARTY, "unlisted_party_invitation"),)
    return ()


@dataclass(frozen=True)
class CaptchaPolicy:
    stop: bool = False
    town: bool = False
    alarm: bool = False
    show_window: bool = False


def manual_captcha(policy: CaptchaPolicy) -> Tuple[Intent, ...]:
    """0042578c: manual response policy; no solver/service or submission."""
    return tuple(Intent(action, "captcha") for action, enabled in (
        (Action.STOP, policy.stop), (Action.TOWN, policy.town),
        (Action.ALARM, policy.alarm), (Action.CAPTCHA_WINDOW, policy.show_window)) if enabled)


def choose_event_groups(enabled):
    """0045a4dc group priority only; timing and join eligibility are unresolved."""
    names = frozenset(enabled)
    known = {"chaos", "bdw", "knight_royale", "ft", "utc", "juraid"}
    if not names <= known:
        raise ValueError("Unknown event")
    return tuple(next((name for name in group if name in names), None)
                 for group in (("chaos", "bdw", "knight_royale"), ("ft", "utc", "juraid")))


@dataclass(frozen=True)
class CrashSnapshot:
    inventory_full: bool
    has_abyss_gem: bool
    npc_id: int
    npc_distance: Optional[float]


def abyss_crash_decision(snapshot: CrashSnapshot, interval_seconds: int,
                         last_attempt_ms: int, now_ms: int) -> Tuple[Intent, ...]:
    """00470f6c/00470d98/004710d4: confirmed submode zero only.

    Equality reaches the attempt: source returns only when elapsed < interval.
    NPC name/identity resolution remains the observation adapter's obligation.
    """
    if interval_seconds < 0 or last_attempt_ms < 0 or now_ms < last_attempt_ms:
        raise ValueError("Invalid crash timer")
    if snapshot.inventory_full:
        return (Intent(Action.STOP, "inventory_full"),)
    if not snapshot.has_abyss_gem:
        return (Intent(Action.STOP, "abyss_gem_missing"),)
    if (snapshot.npc_id <= 0 or snapshot.npc_distance is None
        or not 0 <= snapshot.npc_distance <= 10):
        return (Intent(Action.STOP, "npc_unavailable"),)
    if now_ms - last_attempt_ms >= interval_seconds * 1000:
        return (Intent(Action.CRASH_ITEM, "abyss_gem", snapshot.npc_id),)
    return ()


def loot_inactivity_alarm(enabled: bool, started_ms: int, now_ms: int) -> Tuple[Intent, ...]:
    """00458f98: a nonzero baseline and 600000 ms inactivity boundary."""
    if now_ms < started_ms or started_ms < 0:
        raise ValueError("Invalid loot timeline")
    if enabled and started_ms != 0 and now_ms - started_ms >= 600000:
        return (Intent(Action.ALARM, "loot_inactive"),)
    return ()
