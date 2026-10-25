"""Bounded 00459970:459c5a..459e06 control model; effects are inert records."""
from dataclasses import dataclass
from jail_preload import JailPreloadFrame, MASK


@dataclass(frozen=True)
class DisconnectActionPlan:
    complete: bool
    reads: tuple = ()
    calls: tuple = ()
    stores: tuple = ()
    intents: tuple = ()
    needed: object = None
    next_address: object = None
    whole_function_verified: bool = False
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False
    external_actions_executed: int = 0


class DisconnectActionFrame(JailPreloadFrame):
    """Reached-only normal paths, beginning after the periodic DC block.

    Kernel argument tuples use physical PUSH order. Delphi/VCL register arguments
    are labelled. Normal receipts establish control continuation only; they do
    not certify that shutdown, process exit, an alarm or relog actually happened.
    A completed plan stops at the named source continuation, before its body.
    """
    def __init__(self, *, context=0x562194):
        if type(context) is not int or not 0 <= context <= MASK:
            raise ValueError('Raw disconnect context required')
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
                                    None if complete else self._needed,
                                    self.next_address)

    def _run(self):
        yield ('entry', '00459c5a')
        self.next_address = 0x459fa0
        if not (yield from self._read('enabled_byte', self.context + 0x8a, 1)):
            return
        if (yield from self._read('bot_running_byte', 0x561f60, 1)):
            yield from self._call('stop_bot', '0040ae0c', (0, 0x561f34))
        if (yield from self._read('alarm_byte', self.context + 0x8b, 1)):
            yield from self._call('alarm_construct', '004040bc', (0x521454, 'alarm_local'))
            result = yield from self._value('alarm_construct_eax')
            text = yield from self._read('alarm_text_pointer', result)
            self.intents.append(('alarm', text, 0x569568))
            yield from self._call('alarm', '00404260', (text, 0x569568))
            yield from self._call('alarm_cleanup', '004040f8', (2, 'alarm_local'))
        if (yield from self._read('initialized_byte', self.context + 0x74, 1)):
            self.next_address = 0x459e06
            return
        if not (yield from self._read('procedure_byte', self.context + 0x8c, 1)):
            return
        # Three separate instructions reload the mode; asynchronous changes are
        # representable rather than silently collapsed into one Python enum.
        if (yield from self._read('mode_zero_dword', self.context + 0x90)) == 0:
            yield from self._call('command_construct', '004040bc', (0x521457, 'command_local'))
            pointer = yield from self._value('command_local_pointer')
            effective = pointer or 0x521463
            self.intents.append(('command', effective, 0))
            yield from self._call('command', 'WinExec', (0, effective))
            yield from self._call('command_cleanup', '004040f8', (2, 'command_local'))
            return
        if (yield from self._read('mode_one_dword', self.context + 0x90)) == 1:
            yield from self._call('current_process', 'GetCurrentProcess')
            handle = yield from self._value('current_process_eax')
            self.intents.append(('terminate_current_process', handle, 0))
            yield from self._call('terminate', 'TerminateProcess', (0, handle))
            saved = yield from self._value('saved_fs_dword')
            self.intents.append(('restore_FS0', saved))
            self.next_address = 0x459faa
            return
        if (yield from self._read('mode_two_dword', self.context + 0x90)) != 2:
            return
        self.stores.extend(((self.context + 0x74 & MASK, 1, 1),
                            (self.context + 0x75 & MASK, 1, 1)))
        yield from self._call('tick', 'GetTickCount')
        tick = yield from self._value('tick_eax')
        self.stores.extend(((self.context + 0x78 & MASK, 4, tick),
                            (self.context + 0x7c & MASK, 4, 0),
                            (self.context + 0x80 & MASK, 4, 0),
                            (self.context + 0x84 & MASK, 4, 0)))
        # Each UI chain reloads the root and all dereferences independently.
        root = yield from self._read('reset_root', 0x5539f8)
        form = yield from self._read('reset_form', root)
        obj = yield from self._read('reset_object', form + 0x478)
        table = yield from self._read('reset_vtable', obj)
        target = yield from self._read('reset_target', table + 0x94)
        yield from self._call('reset', 'captured_virtual_94',
                              (('target', target), ('EAX', obj), ('EDX', 0)))
        root = yield from self._read('page_root', 0x5539f8)
        form = yield from self._read('page_form', root)
        page = yield from self._read('page_object', form + 0x1008)
        yield from self._call('page_index', 'TTabSheet.GetPageIndex', (('EAX', page),))
        index = yield from self._value('page_index_eax')
        root = yield from self._read('select_root', 0x5539f8)
        form = yield from self._read('select_form', root)
        obj = yield from self._read('select_object', form + 0x478)
        table = yield from self._read('select_vtable', obj)
        target = yield from self._read('select_target', table + 0x13c)
        yield from self._call('select', 'captured_virtual_13c',
                              (('target', target), ('EAX', obj), ('EDX', index)))
        yield from self._call('relog_start', '00412ed0')
