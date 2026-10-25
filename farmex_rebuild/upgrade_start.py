"""Ordered 4f7adc start/stop snapshot replay; no VCL/native/vector execution."""
from dataclasses import dataclass, field, replace
from collections.abc import Mapping
from upgrade_scroll import UpgradeScrollObservation, plan_upgrade_scroll


@dataclass(frozen=True)
class UpgradeStartState:
    mode: int = 0
    queue: tuple = ()
    scroll_index: object = None
    start_enabled: object = None
    stop_enabled: object = None

    def __post_init__(self):
        if type(self.mode) is not int or not 0 <= self.mode < 1 << 32:
            raise ValueError('Raw mode DWORD required')
        if type(self.queue) is not tuple or any(type(k) is not int or not 0 <= k < 1 << 32 for k in self.queue):
            raise ValueError('Captured DWORD queue required')
        if self.scroll_index is not None and (type(self.scroll_index) is not int or not -1 <= self.scroll_index < 1 << 32):
            raise ValueError('Captured scroll index required')
        for flag in (self.start_enabled, self.stop_enabled):
            if flag is not None and type(flag) is not bool:
                raise ValueError('Captured UI boolean required')


@dataclass(frozen=True)
class UpgradeStartRow:
    checked_byte: object = None
    key_dword: object = None
    caption: object = None


@dataclass(frozen=True)
class UpgradeStartObservation:
    start_byte: int
    start_ui_returned: object = None
    stop_ui_returned: object = None
    vector_clear_returned: object = None
    scroll_lookup: object = None
    scroll_cleanup_returned: object = None
    counts: tuple = ()  # One fresh signed GetCount result per loop test.
    rows: Mapping = field(default_factory=dict)
    append_returns: Mapping = field(default_factory=dict)
    local_decimal: bool = False


@dataclass(frozen=True)
class UpgradeStartPlan:
    complete: bool
    state: UpgradeStartState
    prospective_state: UpgradeStartState
    calls: tuple
    missing: str = ''
    scroll_plan: object = None
    independently_verified: bool = False
    input_state: object = None


def replay_upgrade_start(state, observation):
    if not isinstance(state, UpgradeStartState) or not isinstance(observation, UpgradeStartObservation):
        raise ValueError('Typed Upgrade start state/observations required')
    o = observation
    if type(o.start_byte) is not int or not 0 <= o.start_byte <= 255:
        raise ValueError('Source start BYTE required')
    if type(o.local_decimal) is not bool or type(o.counts) is not tuple:
        raise ValueError('Explicit parser policy and fresh count tuple required')
    if not isinstance(o.rows, Mapping) or not isinstance(o.append_returns, Mapping):
        raise ValueError('Indexed row/helper observations required')
    candidate = state
    calls = []
    scroll = None

    class Missing(Exception):
        pass

    def normal(value, label):
        if value is not None and type(value) is not bool:
            raise ValueError('Explicit normal-return boolean required')
        if value is not True:
            raise Missing(label+' normal return')

    def ui(start):
        nonlocal candidate
        calls.append(('SetEnabled:start', bool(start)))
        normal(o.start_ui_returned, 'Start SetEnabled')
        candidate = replace(candidate, start_enabled=bool(start))
        calls.append(('SetEnabled:stop', not start))
        normal(o.stop_ui_returned, 'Stop SetEnabled')
        candidate = replace(candidate, stop_enabled=not start)

    try:
        if o.start_byte == 0:
            # Stop writes mode before either UI call; it does not clear queue.
            candidate = replace(candidate, mode=0)
            ui(True)
        else:
            ui(False)
            calls.extend((('004f7d28:end',), ('004f7d04:begin',), ('004f7d4c:erase_range',)))
            normal(o.vector_clear_returned, 'begin/end/erase range')
            candidate = replace(candidate, queue=())
            calls.append(('004f7040',))
            scroll = plan_upgrade_scroll(o.scroll_lookup or UpgradeScrollObservation())
            if not scroll.complete:
                raise Missing(scroll.missing)
            candidate = replace(candidate, scroll_index=scroll.relative_index)
            calls.append(('00505c48:scroll_temporary_cleanup',))
            normal(o.scroll_cleanup_returned, 'scroll temporary cleanup')
            index = 0
            while True:
                calls.append(('GetCount', index))
                if index >= len(o.counts) or o.counts[index] is None:
                    raise Missing('fresh row count at index%d'%index)
                count = o.counts[index]
                if type(count) is not int or not -(1 << 31) <= count < 1 << 31:
                    raise ValueError('Signed32 source row count required')
                if count <= index:
                    break
                calls.append(('GetItem/GetChecked', index))
                row = o.rows.get(index)
                if row is None or (isinstance(row, UpgradeStartRow) and row.checked_byte is None):
                    raise Missing('fresh checked BYTE at index%d'%index)
                if not isinstance(row, UpgradeStartRow) or type(row.checked_byte) is not int or not 0 <= row.checked_byte <= 255:
                    raise ValueError('Typed row and raw checked BYTE required')
                if row.checked_byte:
                    calls.append(('0045f7f4:caption/StrToInt', index))
                    key = row.key_dword
                    if key is not None and row.caption is not None:
                        raise ValueError('Observed StrToInt return and local caption conflict')
                    if key is None and o.local_decimal and row.caption is not None:
                        from upgrade_configuration import _decimal
                        try:
                            key = _decimal(row.caption, 32, 'start row%d'%index)
                        except ValueError:
                            raise Missing('caption outside local decimal policy at index%d'%index)
                    if key is None:
                        raise Missing('StrToInt result at index%d'%index)
                    if type(key) is not int or not 0 <= key < 1 << 32:
                        raise ValueError('Raw StrToInt EAX DWORD required')
                    calls.append(('append DWORD', index, key))
                    normal(o.append_returns.get(index), 'row%d append'%index)
                    candidate = replace(candidate, queue=candidate.queue+(key,))
                index += 1
            candidate = replace(candidate, mode=1)
        return UpgradeStartPlan(True, candidate, candidate, tuple(calls), scroll_plan=scroll, input_state=state)
    except Missing as error:
        return UpgradeStartPlan(False, state, candidate, tuple(calls), str(error), scroll, input_state=state)


def apply_upgrade_start(runner, plan):
    """Commit only a complete local plan against its unchanged input snapshot.

    No source clock is initialized by this function; source start has no such
    write. UI state is a plan, not a native widget mutation.
    """
    if not isinstance(plan, UpgradeStartPlan) or not plan.complete:
        raise ValueError('Complete local start plan required')
    if not runner.source_clock:
        raise ValueError('Source-clock runner required')
    if runner.source_pending is not None:
        raise ValueError('Cannot replace an in-flight helper frame')
    before=plan.input_state
    if before is None or (runner.state,runner.queue,runner.source_scroll_index)!=(before.mode,before.queue,before.scroll_index):
        raise ValueError('Start input snapshot changed')
    candidate = plan.state
    runner.state = candidate.mode
    runner.queue = candidate.queue
    runner.source_scroll_index = candidate.scroll_index
    runner.source_start_ui = (candidate.start_enabled, candidate.stop_enabled)
    runner.reason = ''
