"""Source relog startup/snapshot normal paths; all reads/calls/stores are inert."""
from dataclasses import dataclass
from jail_preload import JailPreloadFrame, MASK


@dataclass(frozen=True)
class RelogEntryPlan:
    complete: bool
    kind: str
    reads: tuple = ()
    calls: tuple = ()
    stores: tuple = ()
    needed: object = None
    whole_function_verified: bool = False
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False
    external_actions_executed: int = 0


class _RelogEntryFrame(JailPreloadFrame):
    def __init__(self):
        self.stores = []
        super().__init__()

    def _read(self, label, address):
        self.reads.append((address & MASK, 4, label))
        return (yield from self._value(label))

    def _plan(self, complete=False):
        return RelogEntryPlan(complete, self.kind, tuple(self.reads), tuple(self.calls),
                              tuple(self.stores), None if complete else self._needed)


class RelogSnapshotFrame(_RelogEntryFrame):
    """00412ed0: preserve three raw helper returns, not inferred server values."""
    kind = 'snapshot'

    def _run(self):
        yield ('entry', '00412ed0')
        yield from self._call('prologue', 'source_frame_setup_span')
        slot = yield from self._read('root_slot', 0x553f6c)
        yield from self._call('root_value', '0045dc44', (slot,))
        result = yield from self._value('root_value_eax')
        self.stores.append((0x50b2d4, 4, result))
        yield from self._call('first_selector', '00461b24')
        result = yield from self._value('first_selector_eax')
        self.stores.append((0x50b2cc, 4, result))
        yield from self._call('second_selector', '004619b8')
        result = yield from self._value('second_selector_eax')
        self.stores.append((0x50b2d0, 4, result))
        yield from self._call('epilogue', 'source_frame_restore_return_span')


class ManualRelogFrame(_RelogEntryFrame):
    """00412efc: set manual flag, UI, counters, then exact-one queue helper gate."""
    kind = 'manual'

    def _run(self):
        yield ('entry', '00412efc')
        yield from self._call('prologue', 'source_frame_setup_span')
        self.stores.append((0x562202, 1, 1))
        root = yield from self._read('button_root', 0x5539f8)
        form = yield from self._read('button_form', root)
        button = yield from self._read('button_object', form + 0x458)
        table = yield from self._read('button_vtable', button)
        target = yield from self._read('button_target', table + 0x94)
        yield from self._call('button_setter', 'captured_virtual_94',
                              (('target', target), ('EAX', button), ('EDX', 0)))
        self.stores.extend(((0x553c7c, 4, 0), (0x553c80, 4, 0)))
        yield from self._call('connection', '00462738')
        result = yield from self._value('connection_eax')
        if result == 1:
            yield from self._call('queue_helper', '004c7e0c', (0x561ef8,))
        yield from self._call('epilogue', 'source_frame_restore_return_span')
