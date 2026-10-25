"""Source jail helper control plans. All API calls and reads are inert records."""
from dataclasses import dataclass, field
from types import MappingProxyType

MASK = 0xffffffff

@dataclass(frozen=True)
class JailObservation:
    entry_reached: bool = False
    values: object = field(default_factory=dict)
    normal_returns: object = field(default_factory=dict)

    def __post_init__(self):
        if type(self.entry_reached) is not bool:
            raise ValueError('Explicit helper entry required')
        values, normals = dict(self.values), dict(self.normal_returns)
        for k, v in values.items():
            if type(k) is not str or type(v) is not int or not 0 <= v < (256 if k.endswith('_byte') else 1 << 32):
                raise ValueError('Raw jail BYTE/DWORD observations required')
        if any(type(k) is not str or type(v) is not bool for k, v in normals.items()):
            raise ValueError('Separate normal return receipts required')
        object.__setattr__(self, 'values', MappingProxyType(values))
        object.__setattr__(self, 'normal_returns', MappingProxyType(normals))

@dataclass(frozen=True)
class JailPlan:
    complete: bool
    kind: str
    reads: tuple = ()
    calls: tuple = ()
    needed: object = None
    iterations: int = 0
    next_address: object = None
    whole_function_verified: bool = False
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False
    process_termination_calls_executed: int = 0

def source_vector_count(end, begin):
    """SUB DWORD, signed-negative +3, SAR2; return raw DWORD for unsigned JA."""
    if any(type(v) is not int or not 0 <= v <= MASK for v in (end, begin)):
        raise ValueError('Raw vector bounds required')
    delta = (end - begin) & MASK
    if delta & 0x80000000:
        delta = (delta + 3) & MASK
    signed = delta - (1 << 32) if delta & 0x80000000 else delta
    return (signed >> 2) & MASK

class JailFrame:
    """Streaming reached-only observations; no fixed native loop bound is invented.

    API argument tuples are physical PUSH order. Symbolic local addresses denote
    captured source stack storage, never actual pointers in this Python process.
    A call appears once when reached, even while its normal return is missing.
    """
    def __init__(self, kind, *, context=0x5690f8):
        if kind not in ('list', 'scan') or type(context) is not int or not 0 <= context <= MASK:
            raise ValueError('Known jail helper and raw context required')
        self.kind, self.context = kind, context
        self.reads, self.calls, self.iterations = [], [], 0
        self.values, self.normals = {}, {}
        self.final = None
        self._flow = self._run()
        self._needed = next(self._flow)

    def _value(self, label):
        return (yield ('value', label))

    def _read(self, label, address, width=4):
        self.reads.append((address if isinstance(address, str) else address & MASK, width, label))
        return (yield from self._value(label))

    def _call(self, label, helper, pushes=()):
        self.calls.append((helper, pushes, label))
        yield ('normal', label)

    def _run(self):
        address = '0046dc5c' if self.kind == 'list' else '0046d66c'
        yield ('entry', address)
        yield from self._call('prologue', 'source_SEH_prologue_span')
        if self.kind == 'list':
            yield from self._call('initial_string', '00404148', ('local_string',))
            yield from self._read('initial_unused_byte', 0x526fa9, 1)
            index = 0
            while True:
                p = 'row%d.' % index
                initial = yield from self._read(p+'count_initial_begin', self.context+0xd0)
                count = 0
                if initial:
                    end = yield from self._read(p+'count_end', self.context+0xd4)
                    # Separate source load after reading end, not reuse of initial.
                    sub_begin = yield from self._read(p+'count_sub_begin', self.context+0xd0)
                    count = source_vector_count(end, sub_begin)
                if count <= index:
                    break
                begin = yield from self._read(p+'element_begin', self.context+0xd0)
                element = (begin + ((index << 2) & MASK)) & MASK
                yield from self._call(p+'string_assign', '005050e4', (element, 'local_string'))
                title = yield from self._read(p+'title_pointer', 'local_string')
                yield from self._call(p+'find_window', 'FindWindowA', (title or 0x52704b, 0))
                hwnd = yield from self._value(p+'hwnd')
                if hwnd:
                    yield from self._call(p+'window_pid', 'GetWindowThreadProcessId', ('local_pid', hwnd))
                    # Source checks the written PID, not the API return/thread ID.
                    pid = yield from self._read(p+'pid', 'local_pid')
                    if pid:
                        yield from self._call(p+'open', 'OpenProcess', (pid, 0, 0x1fffff))
                        handle = yield from self._value(p+'handle')
                        if handle:
                            yield from self._call(p+'terminate', 'TerminateProcess', (0, handle))
                self.iterations += 1
                index = (index + 1) & MASK
            yield from self._call('final_cleanup', '004040f8', (2, 'local_string'))
        else:
            # Text initialization includes local-source read and .bnbx creation;
            # helper and encoding semantics are deliberately explicit boundaries.
            yield from self._call('initial_text_span', '0046d685..0046d718')
            yield from self._call('snapshot', 'CreateToolhelp32Snapshot', (0, 2))
            snapshot = yield from self._value('snapshot_handle')
            if snapshot != MASK:
                yield from self._call('process_first', 'Process32First', ('entry_size_0x128', snapshot))
                present = yield from self._value('process_first_eax')
                index = 0
                while present:
                    p = 'row%d.' % index
                    yield from self._call(p+'executable_text', '0046d79a..0046d7f8_opaque_string_preparation')
                    yield from self._call(p+'search', '0041ac60', ('search_length', 0, 'search_pointer', 'executable_string'))
                    search = yield from self._value(p+'search_eax')
                    if search != MASK:
                        pid = yield from self._read(p+'pid', 'process_entry+8')
                        yield from self._call(p+'open', 'OpenProcess', (pid, 0, 0x1fffff))
                        handle = yield from self._value(p+'handle')
                        # There is no handle!=0 guard in this source path.
                        source = yield from self._read(p+'identity_address', 0x55420c)
                        yield from self._call(p+'remote_text', '004604d4', (0xff, source, handle))
                        pointer = yield from self._value(p+'remote_pointer')
                        yield from self._call(p+'unicode_convert', '00505bb8', (pointer, 'remote_unicode'))
                        yield from self._call(p+'compare', '00505d4c', ('initial_unicode', 'remote_unicode'))
                        comparison = yield from self._value(p+'compare_eax')
                        if comparison & 255:
                            yield from self._call(p+'terminate', 'TerminateProcess', (0, handle))
                        yield from self._call(p+'unicode_cleanup', '00505c64', (2, 'remote_unicode'))
                    yield from self._call(p+'process_next', 'Process32Next', ('process_entry', snapshot))
                    # Source asks Process32Next BEFORE destroying current exe text.
                    present = yield from self._value(p+'process_next_eax')
                    yield from self._call(p+'executable_cleanup', '00403860', (0, 1, 'executable_string'))
                    self.iterations += 1
                    index = (index + 1) & MASK
            yield from self._call('final_cleanup', 'source_string_cleanup_span')
        yield from self._call('epilogue', 'source_FS_restore_stack_return_span')

    def _plan(self, complete=False):
        return JailPlan(complete, self.kind, tuple(self.reads), tuple(self.calls),
                        None if complete else self._needed, self.iterations,
                        (0x46dd6f if self.kind == 'list' else 0x46d903) if complete else None)

    def advance(self, observation):
        if not isinstance(observation, JailObservation):
            raise ValueError('Typed jail observation required')
        if self.final is not None:
            return self.final
        while True:
            kind, label = self._needed
            if kind == 'entry':
                if not observation.entry_reached:
                    return self._plan()
                value = True
            elif kind == 'normal':
                if observation.normal_returns.get(label) is not True:
                    return self._plan()
                value = True
                self.normals[label] = True
            else:
                if label not in observation.values:
                    return self._plan()
                value = observation.values[label]
                self.values[label] = value
            try:
                self._needed = self._flow.send(value)
            except StopIteration:
                self.final = self._plan(True)
                return self.final
