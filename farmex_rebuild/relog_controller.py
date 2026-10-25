"""00412adc normal relog controller; native effects are opaque inert records."""
from dataclasses import dataclass
from jail_preload import JailPreloadFrame, MASK


@dataclass(frozen=True)
class RelogControllerPlan:
    complete: bool
    reads: tuple = ()
    calls: tuple = ()
    stores: tuple = ()
    captured_locals: tuple = ()
    return_eax: object = None
    needed: object = None
    whole_function_verified: bool = False
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False
    external_actions_executed: int = 0


class RelogControllerFrame(JailPreloadFrame):
    """One invocation. No secret/string data, actual game pointers or APIs read.

    Each source dereference/result is a caller-supplied raw observation. Native
    selector/auth/UI/replacement helpers stay separate normal-return boundaries.
    Kernel tuples use physical PUSH order; original callback registers labelled.
    """
    def __init__(self):
        self.stores = []
        self.locals = {}
        self.return_eax = None
        super().__init__()

    def _read(self, label, address, width=4):
        self.reads.append((address & MASK, width, label))
        return (yield from self._value(label))

    def _byte(self, label, address):
        return (yield from self._read(label + '_byte', address, 1))

    def _guard(self, label, address, helper='0045dc44'):
        yield from self._call(label, helper, (address & MASK,))
        return (yield from self._value(label + '_eax'))

    def _field(self, label, root, offset_address, helper='0045dc44'):
        offset = yield from self._read(label + '_offset', offset_address)
        return (yield from self._guard(label, root + offset, helper))

    def _tick(self, label):
        yield from self._call(label, 'GetTickCount')
        return (yield from self._value(label + '_eax'))

    def _elapsed(self, label, address, threshold):
        tick = yield from self._tick(label + '_tick')
        low = yield from self._read(label + '_low', address)
        high = yield from self._read(label + '_high', address + 4)
        delta = (tick - ((high << 32) | low)) & ((1 << 64) - 1)
        return not (delta & (1 << 63)) and delta >= threshold

    def _stamp(self, label, address):
        tick = yield from self._tick(label)
        self.stores.extend(((address, 4, tick), (address + 4, 4, 0)))

    def _enabled(self, label, global_address):
        # Source OR is short-circuited; pending is a fresh read per stage.
        if (yield from self._byte(label + '_enabled', global_address)):
            return True
        return bool((yield from self._byte(label + '_pending', 0x562208)))

    def _plan(self, complete=False):
        return RelogControllerPlan(complete, tuple(self.reads), tuple(self.calls),
                                    tuple(self.stores), tuple(self.locals.items()), self.return_eax,
                                    None if complete else self._needed)

    def _run(self):
        yield ('entry', '00412adc')
        yield from self._call('prologue', 'source_frame_setup_span')
        if (yield from self._byte('sleep_enabled', 0x553e3c)):
            delay = yield from self._read('sleep_delay', 0x553e40)
            yield from self._call('sleep', 'SleepEx', (0, delay))
        if (yield from self._byte('watchdog_first', 0x561f7c)):
            if (yield from self._byte('watchdog_second', 0x561ed0)):
                if (yield from self._byte('watchdog_third', 0x555e80)):
                    if (yield from self._elapsed('watchdog', 0x555e88, 5000)):
                        yield from self._call('watchdog', '0042732c', (0x555e70,))
        slot = yield from self._read('base_slot', 0x553f3c)
        root = yield from self._guard('base_root', slot)
        base = yield from self._field('base_value', root, 0x5541a0)
        self.locals['base'] = base
        slot = yield from self._read('alternate_slot', 0x553f3c)
        root = yield from self._guard('alternate_root', slot)
        offset = yield from self._read('alternate_offset', 0x5541a0)
        self.locals['alternate'] = yield from self._guard('alternate_value', root + offset + 8)
        # These two chains dereference base again before adding their offsets.
        for label, address in (('first_input', 0x5541a4), ('second_input', 0x5541a8)):
            root = yield from self._guard(label + '_root', base)
            self.locals[label] = yield from self._field(label, root, address)
        for label, address in (('prepare', 0x5541c0), ('unused', 0x5541c4),
                               ('advance', 0x5541c8), ('advance_alt', 0x5541cc),
                               ('selection', 0x5541d4)):
            self.locals[label] = yield from self._field(label + '_object', base, address)
        yield from self._body(base)
        # Every normal controller path reaches the original callback, including
        # bootstrap/replacement and all skipped selector branches.
        slot = yield from self._read('original_slot', 0x553f3c)
        root = yield from self._read('original_root', slot)
        offset = yield from self._read('original_offset', 0x5541a0)
        obj = yield from self._read('original_object', root + offset)
        target = yield from self._read('original_target', 0x554220)
        yield from self._call('original', 'captured_original_callback',
                              (('EAX', target), ('ECX', obj), ('stack_args', ())))
        self.return_eax = yield from self._value('original_eax')
        yield from self._call('epilogue', 'source_frame_restore_return_span')

    def _body(self, base):
        state = yield from self._field('prepare_ui', self.locals['prepare'], 0x5541fc, '0045dbdc')
        if state & 255 == 1:
            if (yield from self._enabled('prepare', 0x50b2d8)):
                if (yield from self._elapsed('prepare', 0x553c6c, 5000)):
                    yield from self._stamp('prepare_post_tick', 0x553c6c)
                    if (yield from self._byte('prepare_mode', 0x553e46)) == 1:
                        yield from self._call('prepare_inputs', '0041245c')
        state = yield from self._field('advance_ui', self.locals['advance'], 0x5541fc, '0045dbdc')
        if state & 255 != 1:
            state = yield from self._field('advance_alt_ui', self.locals['advance_alt'], 0x5541fc, '0045dbdc')
        if state & 255 == 1:
            if (yield from self._enabled('advance', 0x50b2d9)):
                yield from self._call('advance', '004126f4')
        if not (yield from self._byte('bootstrap_done', 0x553c8c)):
            yield from self._call('bootstrap_probe', '004e2bc8', ('source_local_dword',))
            if not (yield from self._value('bootstrap_probe_eax')) & 255:
                raw = yield from self._value('bootstrap_local_dword')
                signed = raw if raw < 1 << 31 else raw - (1 << 32)
                if signed > 90:
                    target = yield from self._read('bootstrap_target', 0x554214)
                    yield from self._call('bootstrap_replace', '0046b8fc', (0x412874, target, 0x554224))
            self.stores.append((0x553c8c, 1, 1))
            return
        state = yield from self._field('alternate_ui', self.locals['alternate'], 0x5541fc, '0045dbdc')
        if state & 255 == 1:
            if not (yield from self._byte('alternate_ready_first', 0x555e6c)):
                self.stores.append((0x553c88, 4, 0))
                yield from self._call('alternate_prepare', '004c6a24', (0x555e34,))
            if (yield from self._byte('alternate_mode', 0x553e46)) == 1:
                if (yield from self._byte('alternate_enabled', 0x555e58)):
                    if (yield from self._byte('alternate_ready_second', 0x555e6c)):
                        if (yield from self._elapsed('alternate', 0x553c74, 5000)):
                            yield from self._call('alternate_action', '004c6934', (0x555e34,))
                            yield from self._call('alternate_first', '004123b0')
                            yield from self._call('alternate_second', '004126b8')
                            yield from self._stamp('alternate_post_tick', 0x553c74)
                            counter = yield from self._read('alternate_counter', 0x553c88)
                            self.stores.append((0x553c88, 4, (counter + 1) & MASK))
        if not (yield from self._enabled('select', 0x50b2d9)):
            return
        state = yield from self._field('select_ui', self.locals['selection'], 0x5541fc, '0045dbdc')
        if state & 255 != 1:
            return
        if not (yield from self._field('first_selection', base, 0x5541d8)):
            desired = yield from self._read('first_desired', 0x50b2cc)
            yield from self._call('select_first', '0041272c', (desired,))
        if not (yield from self._field('first_selection_fresh', base, 0x5541d8)):
            return
        current = yield from self._field('second_selection', base, 0x5541dc)
        desired = yield from self._read('second_desired_compare', 0x50b2d0)
        if current != desired:
            desired = yield from self._read('second_desired_push', 0x50b2d0)
            yield from self._call('select_second', '0041279c', (desired,))
        current = yield from self._field('second_selection_fresh', base, 0x5541dc)
        desired = yield from self._read('second_desired_fresh', 0x50b2d0)
        if current != desired:
            return
        if not (yield from self._elapsed('confirm', 0x553c7c, 30000)):
            return
        slot = yield from self._read('confirm_root_slot', 0x553e84)
        root = yield from self._guard('confirm_root', slot)
        state = yield from self._field('confirm_state', root, 0x5541f8, '0045dbdc')
        if state & 255 != 1:
            yield from self._call('confirm', '004127c4')
            yield from self._stamp('confirm_post_tick', 0x553c7c)
