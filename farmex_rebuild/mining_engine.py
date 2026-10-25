"""Confirmed mining fragments and recovered route data, without game actions."""
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional, Tuple


def load_mining_routes(path=None):
    path = Path(path) if path else Path(__file__).with_name('mining_routes.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema_version') != 1:
        raise ValueError('Unknown mining route schema')
    return {r['name']: r for r in data['routes']}


def route_records(name, catalog=None):
    """Return recovered records; refuse unresolved declarations, never fill them."""
    routes = load_mining_routes() if catalog is None else catalog
    if name not in routes:
        raise ValueError('Unknown mining route')
    route = routes[name]
    records = route['records']
    if len(records) != route['declared_count'] or any(not r['literal_recovered'] for r in records):
        raise ValueError('Mining route has unresolved declared records')
    return tuple(records)


@dataclass(frozen=True)
class MiningExecutionState:
    phase: int = 0
    route_active: bool = False
    auxiliary_flag: bool = False
    item_index: int = 14
    started_ms: int = 0
    target_id: int = 0
    last_control_ms: int = 0
    last_move_ms: int = 0


def stop_mining():
    """0047baa4: reset observed execution fields, including item index 14."""
    return MiningExecutionState()


def signed_duration_product(value,multiplier):
    """Source IMUL lowDWORD then CDQ; the timestamp domain stays local monotonic."""
    if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw duration DWORD required')
    raw=(value*multiplier)&0xffffffff
    return raw-(0x100000000 if raw&0x80000000 else 0)


def crash_wait_complete(enabled: bool, wait_minutes: int, started_ms: int,
                        now_ms: int, blocked: bool = False):
    """00479d70 phase 0: wait is minutes, and equality still waits.

    A true result permits advancing phase 0 to phase 1 only. It does not
    authorize dispatching an arbitrary subsequent route or NPC command.
    """
    threshold=signed_duration_product(wait_minutes,60000)
    if started_ms < 0 or now_ms < started_ms:
        raise ValueError('Invalid mining wait timeline')
    if blocked:
        return False
    return not enabled or now_ms - started_ms > threshold


@dataclass(frozen=True)
class MiningStartDecision:
    accepted: bool
    coordinate: Optional[Tuple[float, float]]
    reason: str


def select_start_coordinate(mode: int, state_reader_result: int,
                            current: Tuple[float, float],
                            manual: Tuple[float, float] = (0, 0),
                            previous: Optional[Tuple[float, float]] = None,
                            fallback_measurement: Optional[float] = None):
    """0047baa4 coordinate branch only, after its earlier zone guards.

    004677f0 == 0x44 is passed explicitly; its semantic name is unresolved.
    The mode-2 fallback measurement from 00460548 has no assumed distance unit.
    """
    if mode == 1:
        if state_reader_result == 0x44:
            return MiningStartDecision(True, current, 'current_position')
        if previous is not None and previous[0] != 0 and previous[1] != 0:
            return MiningStartDecision(True, previous, 'retained_start_position')
        return MiningStartDecision(False, None, 'mining_area_required')
    if mode == 2:
        if manual[0] == 0 or manual[1] == 0:
            if state_reader_result == 0x44:
                return MiningStartDecision(True, current, 'zero_manual_uses_current')
            if fallback_measurement is None:
                return MiningStartDecision(False, None, 'fallback_measurement_unknown')
            if fallback_measurement >= 50:
                return MiningStartDecision(False, None, 'fallback_measurement_limit')
            return MiningStartDecision(True, current, 'fallback_current_position')
        return MiningStartDecision(True, manual, 'manual_position')
    if mode == 3:
        if state_reader_result == 0x44:
            return MiningStartDecision(True, current, 'manual_route_current_position')
        return MiningStartDecision(False, None, 'manual_route_state_required')
    return MiningStartDecision(False, None, 'unresolved_start_mode')


def route_browser(catalog=None):
    """Small summaries for a UI; no implied execution availability."""
    routes = load_mining_routes() if catalog is None else catalog
    return tuple({'name': r['name'], 'declared_count': r['declared_count'],
                  'initialized_count': r['initialized_count'],
                  'complete_literals': r['initialized_count'] == r['declared_count'],
                  'coordinate_count': sum(x['command'] == 'Koordinat' for x in r['records']),
                  'npc_count': sum(x['command'] == 'NPC' for x in r['records']),
                  'town_count': sum(x['command'] == 'Town' for x in r['records'])}
                 for r in routes.values())


@dataclass(frozen=True)
class MiningRunnerConfig:
    crash_wait_enabled: bool = False
    crash_wait_minutes: int = 0
    override_6035: bool = False
    vip_storage: bool = False

    def __post_init__(self):
        signed_duration_product(self.crash_wait_minutes,60000)


@dataclass(frozen=True)
class MiningSnapshot:
    """Values supplied by an observation adapter, not fabricated game state.

    Numeric helper names deliberately retain unresolved semantics. Distances
    refer to the respective 00460548 result, with no invented physical unit.
    """
    blocked_561f7e: bool = False
    comparison_505118: Optional[bool] = None
    helper_479988_result: Optional[bool] = None
    fallback_coordinate_selected: Optional[bool] = None
    distance_outer: Optional[float] = None
    distance_inner: Optional[float] = None
    helper_465960_target_id: Optional[int] = None
    helper_477770_count: Optional[int] = None
    helper_464a10_result: Optional[bool] = None
    distance_ore: Optional[float] = None
    job_568dbc_active: Optional[bool] = None
    storage_5690b8_active: Optional[bool] = None
    storage_5690cc_value: Optional[int] = None


@dataclass(frozen=True)
class MiningIntent:
    name: str
    source_address: str
    value: Optional[int] = None


@dataclass(frozen=True)
class MiningTick:
    state: MiningExecutionState
    intents: Tuple[MiningIntent, ...] = ()
    required_observations: Tuple[str, ...] = ()


class MiningRunner:
    """One source phase per tick, mirroring 00479d70's if/else chain.

    Helper invocation intents mark real unresolved boundaries. They neither
    execute the helper nor assert its server success. Adapter observations are
    mandatory before dependent transitions. No automatic phase timeout is
    invented: source uses retry gates, and an observation can remain pending.
    """
    def __init__(self, config=None):
        self.config = config or MiningRunnerConfig()

    def tick(self, state: MiningExecutionState, snapshot: MiningSnapshot, now_ms: int):
        if now_ms < max(state.started_ms, state.last_control_ms, state.last_move_ms):
            raise ValueError('Mining clock moved backwards')
        if not 0 <= state.phase <= 7:
            raise ValueError('Unknown mining phase')
        if not state.route_active or snapshot.blocked_561f7e:
            return MiningTick(state)
        cfg = self.config

        def missing(*fields):
            absent = tuple(name for name in fields if getattr(snapshot, name) is None)
            return MiningTick(state, required_observations=absent) if absent else None

        if state.phase == 0:
            if crash_wait_complete(cfg.crash_wait_enabled, cfg.crash_wait_minutes,
                                   state.started_ms, now_ms):
                return MiningTick(replace(state, phase=1),
                                  (MiningIntent('reset_5690cc_5690d8', '00479d70'),))
            return MiningTick(state)

        if state.phase == 1:
            gap = None if cfg.override_6035 else missing('comparison_505118')
            if gap:
                return gap
            special = cfg.override_6035 or snapshot.comparison_505118
            if special:
                if snapshot.helper_479988_result is None:
                    return MiningTick(state, (MiningIntent('evaluate_479988', '00479988'),),
                                      ('helper_479988_result',))
                return MiningTick(replace(state, phase=2) if snapshot.helper_479988_result else state)
            gap = missing('fallback_coordinate_selected')
            if gap:
                return gap
            if not snapshot.fallback_coordinate_selected:
                return MiningTick(state)
            gap = missing('distance_outer')
            if gap:
                return gap
            if snapshot.distance_outer <= 50:
                gap = missing('distance_inner')
                if gap:
                    return gap
                if snapshot.distance_inner <= 2:
                    if snapshot.helper_465960_target_id is None:
                        return MiningTick(state, (MiningIntent('resolve_target_465960', '00465960'),),
                                          ('helper_465960_target_id',))
                    target = snapshot.helper_465960_target_id
                    return MiningTick(replace(state, target_id=target, phase=2 if target != 0 else 1))
                if now_ms - state.last_control_ms >= 3000 and now_ms - state.last_move_ms >= 1000:
                    return MiningTick(replace(state, last_move_ms=now_ms),
                                      (MiningIntent('move_to_selected_coordinate', '004646b4'),))
            elif now_ms - state.last_control_ms >= 5000:
                return MiningTick(replace(state, last_control_ms=now_ms),
                                  (MiningIntent('control_action_465678', '00465678'),))
            return MiningTick(state)

        if state.phase == 2:
            gap = None if cfg.override_6035 else missing('comparison_505118')
            if gap:
                return gap
            if not (cfg.override_6035 or snapshot.comparison_505118):
                return MiningTick(replace(state, phase=3))
            gap = missing('helper_477770_count')
            if gap:
                return gap
            if snapshot.helper_477770_count == 0:
                return MiningTick(replace(state, phase=4))
            gap = missing('helper_464a10_result')
            if gap:
                return gap
            if not snapshot.helper_464a10_result:
                return MiningTick(state)
            if state.item_index >= 42:
                return MiningTick(replace(state, phase=4))
            gap = missing('distance_ore')
            if gap:
                return gap
            # Source __ftol truncates before the comparison; retain that order.
            if int(snapshot.distance_ore) < 8:
                return MiningTick(state, (MiningIntent('process_ore_slot_479698', '00479698', state.item_index),))
            if now_ms - state.last_move_ms >= 1000:
                return MiningTick(replace(state, last_move_ms=now_ms),
                                  (MiningIntent('move_to_ore_target', '004646b4'),))
            return MiningTick(state)

        if state.phase == 3:
            gap = missing('helper_477770_count')
            if gap:
                return gap
            if snapshot.helper_477770_count < 1:
                return MiningTick(replace(state, phase=4))
            gap = missing('distance_ore')
            if gap:
                return gap
            if snapshot.distance_ore >= 10:
                return MiningTick(replace(state, phase=1))
            if state.item_index < 42:
                return MiningTick(state, (MiningIntent('process_ore_slot_479698', '00479698', state.item_index),))
            return MiningTick(replace(state, phase=4))

        if state.phase == 4:
            gap = missing('helper_477770_count')
            if gap:
                return gap
            if snapshot.helper_477770_count > 0:
                return MiningTick(replace(state, phase=2, item_index=14))
            gap = missing('job_568dbc_active')
            if gap:
                return gap
            if not snapshot.job_568dbc_active:
                return MiningTick(replace(state, phase=5),
                                  (MiningIntent('begin_job_568dbc', '00479d70', 14),))
            return MiningTick(state)

        if state.phase == 5:
            if not cfg.vip_storage:
                return MiningTick(replace(state, phase=6))
            if not state.auxiliary_flag:
                return MiningTick(replace(state, auxiliary_flag=True),
                                  (MiningIntent('begin_storage_operation_5', '00479d70', 5),))
            gap = missing('storage_5690b8_active')
            if gap:
                return gap
            if snapshot.storage_5690b8_active:
                return MiningTick(state)
            gap = missing('storage_5690cc_value')
            if gap:
                return gap
            if snapshot.storage_5690cc_value < 48:
                return MiningTick(replace(state, auxiliary_flag=False, item_index=0, phase=2))
            gap = missing('helper_477770_count')
            if gap:
                return gap
            if snapshot.helper_477770_count < 1:
                return MiningTick(replace(state, auxiliary_flag=False, phase=6))
            return MiningTick(replace(state, auxiliary_flag=False, item_index=0, phase=2))

        if state.phase == 6:
            return MiningTick(replace(state, phase=7))
        return MiningTick(replace(state, route_active=False),
                          (MiningIntent('return_route_477bd4', '00477bd4'),))


@dataclass(frozen=True)
class OreSlotState:
    item_index: int = 14
    last_attempt_ms: int = 0
    ws_active: bool = False
    ws_counter: int = 0
    ws_first_ms: int = 0
    ws_second_ms: int = 0

    def __post_init__(self):
        if type(self.ws_counter) is not int or not 0<=self.ws_counter<=0xffffffff:
            raise ValueError('Raw WS counter DWORD required')


@dataclass(frozen=True)
class OreSlotSnapshot:
    ore_name_match: Optional[bool] = None
    ws_helper_45dc44_zero: Optional[bool] = None
    request_helper_45dc44_zero: Optional[bool] = None


@dataclass(frozen=True)
class OreSlotTick:
    state: OreSlotState
    intents: Tuple[MiningIntent, ...] = ()
    required_observations: Tuple[str, ...] = ()
    request_prelude_calls: tuple = () # Deferred0046fb38 context and fresh00463670 name; no ABI execution.


def process_ore_slot(state: OreSlotState, snapshot: OreSlotSnapshot, now_ms: int,
                     interval_seconds: int, ws_enabled: bool = False):
    """00479698 pure slot/cadence model. Increment means local attempt only.

    Unknown 0045dc44 semantics are explicit separate required observations.
    00465f30 and 004c80e4 are named intents, never executable wire templates.
    """
    threshold=signed_duration_product(interval_seconds,1000)
    if now_ms < max(state.last_attempt_ms, state.ws_first_ms, state.ws_second_ms):
        raise ValueError('Invalid ore slot timeline')
    if now_ms - state.last_attempt_ms < threshold:
        return OreSlotTick(state)
    if snapshot.ore_name_match is None:
        return OreSlotTick(state, required_observations=('ore_name_match',))
    if not snapshot.ore_name_match:
        return OreSlotTick(replace(state, item_index=state.item_index + 1))
    intents = []
    updated = state
    if ws_enabled and not state.ws_active:
        if snapshot.ws_helper_45dc44_zero is None:
            return OreSlotTick(state, required_observations=('ws_helper_45dc44_zero',))
        counter=state.ws_counter-(0x100000000 if state.ws_counter&0x80000000 else 0)
        pattern=1 if counter%3==0 else 2 # Source signed IDIV remainder zero test.
        if snapshot.ws_helper_45dc44_zero:
            intents.append(MiningIntent('ws_action_465f30_first', '00465f30',pattern))
            updated = replace(state, ws_first_ms=now_ms, ws_counter=(state.ws_counter + 1)&0xffffffff)
        else:
            delay = 20 if pattern==1 else 50
            if now_ms - state.ws_first_ms > delay:
                intents.append(MiningIntent('ws_action_465f30_second', '00465f30',0))
                updated = replace(state, ws_second_ms=now_ms, ws_active=True)
    if snapshot.request_helper_45dc44_zero is None:
        return OreSlotTick(updated, tuple(intents), ('request_helper_45dc44_zero',))
    if snapshot.request_helper_45dc44_zero:
        intents.append(MiningIntent('ore_crash_request_attempt', '004c80e4', state.item_index))
        updated = replace(updated, last_attempt_ms=now_ms,
                          item_index=state.item_index + 1, ws_active=False)
    return OreSlotTick(updated, tuple(intents),request_prelude_calls=
        ('0046fb38','00463670') if snapshot.request_helper_45dc44_zero else ())
