"""00459970 normal control composition; never runs source native effects."""
from dataclasses import dataclass, field, replace
from dc_full_chain import DCFullChainFrame, DCFullChainObservation
from disconnect_action import DisconnectActionPlan
from jail_preload import JailPreloadFrame, MASK
from jail_protection import JailObservation
from relog_entry import RelogSnapshotFrame
from relog_countdown import (RelogCountdownFrame, DisconnectRecoveryFrame,
                             DisconnectRecoveryObservation)


class SpecialReconnectInitFrame(JailPreloadFrame):
    """45998e..459a6e: special context+6e path, not automatic DC options."""
    def __init__(self, *, context=0x562194):
        if type(context) is not int or not 0 <= context <= MASK:
            raise ValueError('Raw reconnect context required')
        self.context = context
        self.stores, self.intents = [], []
        self.next_address = None
        super().__init__()

    def _read(self, label, address, width=4):
        self.reads.append((address & MASK, width, label))
        return (yield from self._value(label))

    def _plan(self, complete=False):
        return DisconnectActionPlan(complete, tuple(self.reads), tuple(self.calls),
                                    tuple(self.stores), tuple(self.intents),
                                    None if complete else self._needed, self.next_address)

    def _run(self):
        yield ('entry', '0045998e')
        if (yield from self._read('bot_running_byte', 0x561f60, 1)):
            yield from self._call('stop_bot', '0040ae0c', (0, 0x561f34))
        if (yield from self._read('initialized_byte', self.context + 0x74, 1)):
            self.next_address = 0x459a6e
            return
        mode = yield from self._read('connection_mode_byte', 0x553e46, 1)
        self.stores.append(((self.context + 0x70) & MASK, 4, 31 if mode == 1 else 1))
        slot = yield from self._read('guard_root_slot', 0x553e80)
        yield from self._call('guard_root', '0045dc44', (slot,))
        root = yield from self._value('guard_root_eax')
        offset = yield from self._read('guard_offset', 0x55406c)
        yield from self._call('guard_byte', '0045dbdc', ((root + offset) & MASK,))
        if (yield from self._value('guard_eax')) & 255:
            slot = yield from self._read('clear_root_slot', 0x553e80)
            yield from self._call('clear_root', '0045dc44', (slot,))
            root = yield from self._value('clear_root_eax')
            offset = yield from self._read('clear_offset', 0x55406c)
            address = (root + offset) & MASK
            self.intents.append(('source_byte_clear', address, 0))
            yield from self._call('clear_byte', '0045de4c', (0, address))
        self.stores.extend((((self.context + 0x74) & MASK, 1, 1),
                            ((self.context + 0x75) & MASK, 1, 1)))
        yield from self._call('tick', 'GetTickCount')
        tick = yield from self._value('tick_eax')
        self.stores.extend((((self.context + 0x78) & MASK, 4, tick),
                            ((self.context + 0x7c) & MASK, 4, 0),
                            ((self.context + 0x80) & MASK, 4, 0),
                            ((self.context + 0x84) & MASK, 4, 0),
                            ((self.context + 0x88) & MASK, 1, 0)))
        root = yield from self._read('reset_root', 0x5539f8)
        form = yield from self._read('reset_form', root)
        obj = yield from self._read('reset_object', form + 0x478)
        table = yield from self._read('reset_vtable', obj)
        target = yield from self._read('reset_target', table + 0x94)
        yield from self._call('reset', 'captured_virtual_94',
                              (('target', target), ('EAX', obj), ('EDX', 0)))
        yield from self._call('runtime_snapshot', '00412ed0')
        self.next_address = 0x459c05


class SpecialReconnectCountdownFrame(RelogCountdownFrame):
    _entry_address = '00459a6e'
    _wait_offset = 0x70
    _notice_stamp = 0x553cdc
    _suffix_address = 0x521435
    _exit_address = 0x459c05


class SpecialReconnectFrame(DisconnectRecoveryFrame):
    _action_type = SpecialReconnectInitFrame
    _countdown_type = SpecialReconnectCountdownFrame
    _countdown_address = 0x459a6e


@dataclass(frozen=True)
class RoutineExitPlan:
    complete: bool
    calls: tuple = ()
    intents: tuple = ()
    needed: object = None
    native_execution_verified: bool = False


class _RoutineExitFrame(JailPreloadFrame):
    def __init__(self, address):
        if address not in (0x459c05, 0x459fa0, 0x459faa):
            raise ValueError('Known source exit edge required')
        self.address = address
        super().__init__()

    def _run(self):
        yield ('entry', '%08x' % self.address)
        if self.address != 0x459faa:
            saved = yield from self._value('saved_fs_dword')
            self.ui.append(('restore_FS0', saved))
            yield from self._call('seh_restore', 'source_FS_restore_span')
        yield from self._call('return', 'source_stack_restore_return_span')

    def _plan(self, complete=False):
        return RoutineExitPlan(complete, tuple(self.calls), tuple(self.ui),
                               None if complete else self._needed)


@dataclass(frozen=True)
class DisconnectRoutineObservation:
    boundary: JailObservation = field(default_factory=JailObservation)
    periodic: DCFullChainObservation = field(default_factory=DCFullChainObservation)
    recovery: DisconnectRecoveryObservation = field(default_factory=DisconnectRecoveryObservation)
    special: DisconnectRecoveryObservation = field(default_factory=DisconnectRecoveryObservation)
    snapshot: object = None

    def __post_init__(self):
        for value, kind in ((self.boundary, JailObservation), (self.periodic, DCFullChainObservation),
                            (self.recovery, DisconnectRecoveryObservation),
                            (self.special, DisconnectRecoveryObservation)):
            if not isinstance(value, kind):
                raise ValueError('Typed disconnect routine observations required')
        if self.snapshot is not None and not isinstance(self.snapshot, JailObservation):
            raise ValueError('Typed relog snapshot observation required')


@dataclass(frozen=True)
class DisconnectRoutinePlan:
    complete: bool
    calls: tuple = ()
    periodic: object = None
    recovery: object = None
    special: object = None
    exit: object = None
    needed: object = None
    normal_control_paths_composed: bool = True
    whole_function_verified: bool = False
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False
    external_actions_executed: int = 0
    snapshot: object = None


class DisconnectRoutineFrame:
    """One source invocation; child entries follow edges, returns stay separate.

    Both context+6e branches are represented. This composes normal-path control
    only; opaque helpers and symbolic SEH/stack receipts are not full-function,
    native return, game interaction or live equivalence certificates.
    """
    def __init__(self, *, context=0x562194):
        self.context = context
        self.periodic = DCFullChainFrame(context=context)
        self.recovery = self.special = self.exit = self.final = None
        self.periodic_plan = self.recovery_plan = self.special_plan = self.exit_plan = None
        self.entered = self.prologue = False
        self.calls = []
        self.snapshot_frame = self.snapshot_plan = None

    def _plan(self, needed=None, complete=False):
        return DisconnectRoutinePlan(complete, tuple(self.calls), self.periodic_plan,
                                      self.recovery_plan, self.special_plan, self.exit_plan, needed,
                                      snapshot=self.snapshot_plan)

    def advance(self, o):
        if not isinstance(o, DisconnectRoutineObservation):
            raise ValueError('Typed disconnect routine observations required')
        if o.snapshot is not None and self.snapshot_frame is None:
            for frame, label in ((self.recovery, 'relog_start'), (self.special, 'runtime_snapshot')):
                if frame is not None and frame.action.normals.get(label) is True:
                    raise ValueError('Cannot retroactively bind opaque relog snapshot')
        if self.final is not None:
            return self.final
        if not self.entered:
            if not o.boundary.entry_reached:
                return self._plan(('boundary', ('entry', '00459970')))
            self.entered = True
            self.calls.append(('source_SEH_prologue_span', (('EAX', 0x521a04),), 'prologue'))
        if not self.prologue:
            if o.boundary.normal_returns.get('prologue') is not True:
                return self._plan(('boundary', ('normal', 'prologue')))
            self.prologue = True
        self.periodic_plan = self.periodic.advance(replace(o.periodic,
            parent=replace(o.periodic.parent, entry_reached=True)))
        if not self.periodic_plan.complete:
            return self._plan(('periodic', self.periodic_plan.needed))
        edge = self.periodic_plan.parent.next_address
        if edge == 0x45998e:
            if self.special is None:
                self.special = SpecialReconnectFrame(context=self.context)
            snapshot_label = 'runtime_snapshot'
            original = replace(o.special, action=replace(o.special.action, entry_reached=True))
            observed = self._snapshot_gate(original, snapshot_label, o.snapshot)
            self.special_plan = self.special.advance(observed)
            child = self.special_plan
            label = 'special'
        elif edge == 0x459c5a:
            if self.recovery is None:
                self.recovery = DisconnectRecoveryFrame(context=self.context)
            snapshot_label = 'relog_start'
            original = replace(o.recovery, action=replace(o.recovery.action, entry_reached=True))
            observed = self._snapshot_gate(original, snapshot_label, o.snapshot)
            self.recovery_plan = self.recovery.advance(observed)
            child = self.recovery_plan
            label = 'recovery'
        else:
            raise AssertionError('Unexpected source periodic continuation')
        if child.needed == ('action', ('normal', snapshot_label)) and (
                o.snapshot is not None or self.snapshot_frame is not None):
            if self.snapshot_frame is None:
                self.snapshot_frame = RelogSnapshotFrame()
            self.snapshot_plan = self.snapshot_frame.advance(replace(
                o.snapshot or JailObservation(), entry_reached=True))
            if not self.snapshot_plan.complete:
                return self._plan(('snapshot', self.snapshot_plan.needed))
            frame = self.special if label == 'special' else self.recovery
            child = frame.advance(original)
            if label == 'special':
                self.special_plan = child
            else:
                self.recovery_plan = child
        if not child.complete:
            return self._plan((label, child.needed))
        edge = (child.action if child.countdown is None else child.countdown).next_address
        if self.exit is None:
            self.exit = _RoutineExitFrame(edge)
        self.exit_plan = self.exit.advance(replace(o.boundary, entry_reached=True))
        if not self.exit_plan.complete:
            return self._plan(('boundary', self.exit_plan.needed))
        self.final = self._plan(complete=True)
        return self.final

    def _snapshot_gate(self, observed, label, supplied):
        if (supplied is not None or self.snapshot_frame is not None) and (
                self.snapshot_frame is None or self.snapshot_frame.final is None):
            normals = {**observed.action.normal_returns, label: False}
            return replace(observed, action=replace(observed.action, normal_returns=normals))
        return observed
