"""Snapshot-only plan for CRT 322392b8; never execute a handler address.

The source re-reads mutable tables around calls. This bounded model requires
stable captured tables and normal-return observations; it does not infer them
from a disk mapping or run any original initialization code.
"""
from dataclasses import dataclass
import struct
from crt_rng import CRT_SOURCE_SHA256


def _dword(value, label):
    if type(value) is not int or not 0 <= value < 1 << 32:
        raise ValueError(label + ' must be an explicit DWORD')


@dataclass(frozen=True)
class StartupRecord:
    address: int
    prefix: int
    priority: int
    handler: int


@dataclass(frozen=True)
class StartupTables:
    descriptor_address: int
    init_records: tuple
    exit_records: tuple


@dataclass(frozen=True)
class StartupCall:
    descriptor_index: int
    record: StartupRecord


@dataclass(frozen=True)
class StartupDispatch:
    calls_reached: tuple
    calls_returned: int
    complete: bool
    missing: str
    source_sha256: str = CRT_SOURCE_SHA256
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False


def decode_startup_records(base, raw):
    """Decode a complete nonwrapping six-byte table from an explicit snapshot.

    Malformed/wrapping source tables are unsupported, rather than pretending
    the native loop validates them or silently dropping partial records.
    """
    _dword(base, 'base')
    if type(raw) is not bytes or len(raw) % 6 or base + len(raw) >= 1 << 32:
        raise ValueError('Complete nonwrapping bytes table required')
    return tuple(StartupRecord(base+i, *struct.unpack_from('<BBI', raw, i))
                 for i in range(0, len(raw), 6))


def replay_startup_dispatch(tables, mode_dword, *, stable_tables=None,
                            normal_returns=()):
    """Replay dispatcher order up to the first unknown/non-normal return.

    The source receives a count followed by descriptor pointers. Here the
    supplied tuple represents a captured, nonnegative count and pointer list.
    Nonzero mode selects exit records. Descriptor order stays forward even on
    exit; only priorities and records within each descriptor reverse.
    """
    _dword(mode_dword, 'mode')
    if type(tables) is not tuple or any(type(t) is not StartupTables for t in tables):
        raise ValueError('Captured descriptor tuple required')
    if stable_tables is not None and type(stable_tables) is not bool:
        raise ValueError('stable_tables must be boolean or unknown')
    if type(normal_returns) is not tuple or any(type(x) is not bool for x in normal_returns):
        raise ValueError('Explicit normal-return tuple required')
    if not tables:
        if normal_returns:
            raise ValueError('No calls can return for an empty descriptor list')
        return StartupDispatch((), 0, True, '')
    if stable_tables is not True:
        return StartupDispatch((), 0, False, 'stable table snapshot contract')
    selected = []
    for table in tables:
        _dword(table.descriptor_address, 'descriptor')
        records = table.init_records if mode_dword == 0 else table.exit_records
        if type(records) is not tuple or any(type(r) is not StartupRecord for r in records):
            raise ValueError('Decoded record tuple required')
        for i, record in enumerate(records):
            _dword(record.address, 'record address')
            _dword(record.handler, 'handler')
            if (type(record.prefix) is not int or not 0 <= record.prefix <= 255 or
                    type(record.priority) is not int or not 0 <= record.priority <= 255):
                raise ValueError('Record prefix/priority must be bytes')
            if i and record.address != records[i-1].address + 6:
                raise ValueError('Contiguous source table required')
        selected.append(records if mode_dword == 0 else tuple(reversed(records)))
    reached = []
    priorities = range(256) if mode_dword == 0 else range(255, -1, -1)
    for priority in priorities:
        for index, records in enumerate(selected):
            for record in records:
                if record.priority != priority:
                    continue
                reached.append(StartupCall(index, record))
                call_index = len(reached)-1
                if call_index >= len(normal_returns):
                    return StartupDispatch(tuple(reached), call_index, False,
                                           'handler normal return')
                if normal_returns[call_index] is not True:
                    return StartupDispatch(tuple(reached), call_index, False,
                                           'handler did not return normally')
    if len(normal_returns) != len(reached):
        raise ValueError('Extra return observations beyond source calls')
    return StartupDispatch(tuple(reached), len(reached), True, '')
