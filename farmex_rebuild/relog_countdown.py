"""00459970:459e06..459fa0 normal countdown paths; all effects are inert."""
from dataclasses import dataclass, field, replace
from disconnect_action import DisconnectActionFrame
from jail_preload import JailPreloadFrame, MASK
from jail_protection import JailObservation
from source_math64 import divide64_bits, MASK64


def signed32(bits):
    return bits if bits < 1 << 31 else bits - (1 << 32)


@dataclass(frozen=True)
class RelogCountdownPlan:
    complete: bool
    reads: tuple = ()
    calls: tuple = ()
    stores: tuple = ()
    intents: tuple = ()
    remaining_dword: object = None
    needed: object = None
    next_address: object = None
    whole_function_verified: bool = False
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False


class RelogCountdownFrame(JailPreloadFrame):
    """One reached countdown poll, with separate native normal receipts.

    Signed64 division result bits are derived using the separately audited pure
    source arithmetic model. The native division's normal return is still a
    distinct boundary. String, queue and cleanup helper semantics stay opaque.
    """
    _entry_address = '00459e06'
    _wait_offset = 0x94
    _notice_stamp = 0x553ce8
    _suffix_address = 0x521464
    _exit_address = 0x459fa0

    def __init__(self, *, context=0x562194):
        if type(context) is not int or not 0 <= context <= MASK:
            raise ValueError('Raw relog context required')
        self.context = context
        self.stores, self.intents = [], []
        self.remaining = self.next_address = None
        super().__init__()

    def _read(self, label, address, width=4):
        self.reads.append((address & MASK, width, label))
        return (yield from self._value(label))

    def _plan(self, complete=False):
        return RelogCountdownPlan(complete, tuple(self.reads), tuple(self.calls),
                                  tuple(self.stores), tuple(self.intents), self.remaining,
                                  None if complete else self._needed, self.next_address)

    def _run(self):
        yield ('entry', self._entry_address)
        if not (yield from self._read('waiting_byte', self.context + 0x75, 1)):
            self.next_address = self._exit_address
            return
        yield from self._call('elapsed_tick', 'GetTickCount')
        tick = yield from self._value('elapsed_tick_eax')
        low = yield from self._read('started_low_dword', self.context + 0x78)
        high = yield from self._read('started_high_dword', self.context + 0x7c)
        elapsed = (tick - (high << 32 | low)) & MASK64
        yield from self._call('seconds_division', '00503e75',
                              (('PUSH', 0), ('PUSH', 1000), ('EDX:EAX', elapsed)))
        seconds = divide64_bits(elapsed, 1000).eax
        wait = yield from self._read('wait_dword', self.context + self._wait_offset)
        self.remaining = (wait - seconds) & MASK
        if signed32(self.remaining) <= 0:
            self.stores.append(((self.context + 0x75) & MASK, 1, 0))
            self.next_address = self._exit_address
            return
        yield from self._call('notice_tick', 'GetTickCount')
        tick = yield from self._value('notice_tick_eax')
        low = yield from self._read('notice_stamp_low_dword', self._notice_stamp)
        high = yield from self._read('notice_stamp_high_dword', self._notice_stamp + 4)
        delta = (tick - (high << 32 | low)) & MASK64
        # CMP high,0; signed JL if nonzero, else unsigned low CMP1000.
        if delta & (1 << 63) or delta < 1000:
            self.next_address = self._exit_address
            return
        yield from self._call('suffix_construct', '00505bb8', (self._suffix_address, 'suffix_unicode'))
        yield from self._call('number_construct', '00407360', (self.remaining, 'number_unicode'))
        number = yield from self._value('number_construct_eax')
        yield from self._call('empty_construct', '00404a78', ('joined_unicode',))
        joined = yield from self._value('empty_construct_eax')
        # First argument was pushed before number_construct and remains live.
        yield from self._call('concatenate', '00505cb8', ('suffix_unicode', number, joined))
        yield from self._call('ansi_convert', '004073a0', ('joined_unicode', 'notice_ansi'))
        for label, local in (('joined_cleanup', 'joined_unicode'),
                             ('suffix_cleanup', 'suffix_unicode'),
                             ('number_cleanup', 'number_unicode')):
            yield from self._call(label, '00505c64', (2, local))
        yield from self._call('queue_size', '00409f6c', (0x561f34,))
        size = yield from self._value('queue_size_eax')
        yield from self._call('queue_capacity', '00409f94', (0x561f34,))
        capacity = yield from self._value('queue_capacity_eax')
        if size < capacity:
            end = yield from self._read('queue_end_dword', 0x561f48)
            self.intents.append(('queue_notice', self.remaining, 'fast'))
            yield from self._call('queue_insert', '00409fbc', ('notice_ansi', 1, end, 0x561f34))
            returned = yield from self._value('queue_insert_eax')
            self.stores.append((0x561f48, 4, returned))
        else:
            yield from self._call('queue_end', '00409e98', (0x561f34, 'end_iterator'))
            self.intents.append(('queue_notice', self.remaining, 'slow'))
            yield from self._call('queue_insert', '0040a01c',
                                  ('notice_ansi', 'end_iterator_copy16', 0x561f34, 'result_iterator'))
        yield from self._call('post_tick', 'GetTickCount')
        fresh = yield from self._value('post_tick_eax')
        self.stores.extend(((self._notice_stamp, 4, fresh), (self._notice_stamp + 4, 4, 0)))
        yield from self._call('notice_cleanup', '004040f8', (2, 'notice_ansi'))
        self.next_address = self._exit_address


@dataclass(frozen=True)
class DisconnectRecoveryObservation:
    action: JailObservation = field(default_factory=JailObservation)
    countdown: JailObservation = field(default_factory=JailObservation)

    def __post_init__(self):
        if not isinstance(self.action, JailObservation) or not isinstance(self.countdown, JailObservation):
            raise ValueError('Typed action and countdown observations required')


@dataclass(frozen=True)
class DisconnectRecoveryPlan:
    complete: bool
    action: object
    countdown: object = None
    needed: object = None
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False


class DisconnectRecoveryFrame:
    """Join only the source action->459e06 edge, never countdown after init."""
    _action_type = DisconnectActionFrame
    _countdown_type = RelogCountdownFrame
    _countdown_address = 0x459e06

    def __init__(self, *, context=0x562194):
        self.context = context
        self.action = self._action_type(context=context)
        self.countdown = self.final = None

    def advance(self, o):
        if not isinstance(o, DisconnectRecoveryObservation):
            raise ValueError('Typed disconnect recovery observations required')
        if self.final is not None:
            return self.final
        action = self.action.advance(o.action)
        if not action.complete:
            return DisconnectRecoveryPlan(False, action, needed=('action', action.needed))
        if action.next_address != self._countdown_address:
            self.final = DisconnectRecoveryPlan(True, action)
            return self.final
        if self.countdown is None:
            self.countdown = self._countdown_type(context=self.context)
        countdown = self.countdown.advance(replace(o.countdown, entry_reached=True))
        result = DisconnectRecoveryPlan(countdown.complete, action, countdown,
                                        None if countdown.complete else ('countdown', countdown.needed))
        if result.complete:
            self.final = result
        return result
