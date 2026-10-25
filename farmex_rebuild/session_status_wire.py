"""Bounded 004fa097 serialization after captured getters/string conversion.

Only owned bytes are produced. No socket, credentials, process or native call.
Prepared values are source observations, not defaults for missing game values.
"""
from dataclasses import dataclass
from types import MappingProxyType

FIELDS = ('session_byte', 'name_header_byte', 'mode_byte', 'status_byte',
          'getter_46209c', 'getter_462670', 'getter_46256c', 'ratio_division_eax',
          'getter_46258c', 'getter_4625ac', 'getter_4625d8', 'exclusive_byte')

@dataclass(frozen=True)
class SessionStatusPrepared:
    values: object
    serialized_name: bytes
    def __post_init__(self):
        values = dict(self.values)
        if set(values) != set(FIELDS):
            raise ValueError('Every prepared field required; unknown fields rejected')
        if any(type(v) is not int or not 0 <= v <= 0xffffffff for v in values.values()):
            raise ValueError('Raw prepared DWORD observations required')
        if any(values[k] > 255 for k in ('session_byte', 'name_header_byte',
                                       'mode_byte', 'status_byte', 'exclusive_byte')):
            raise ValueError('Prepared byte field exceeds source width')
        if values['exclusive_byte'] not in (0, 1):
            raise ValueError('Exclusive byte comes from source boolean normalization')
        if type(self.serialized_name) is not bytes:
            raise ValueError('Captured string serializer bytes required')
        object.__setattr__(self, 'values', MappingProxyType(values))

@dataclass(frozen=True)
class SessionStatusWire:
    complete: bool
    plain_frame: bytes = b''
    wire_frame: bytes = b''
    buffer_512: bytes = b''
    length_word: object = None
    writes: tuple = ()
    missing: str = ''
    helper: str = ''
    full_builder_verified: bool = False
    string_identity_verified: bool = False
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False

def transform_status_bytes(data, count, variant):
    """004f94f8/004f9564: change only 4 <= index < signed(count)-2.

    variant is the explicitly selected helper, not inferred from count. The
    caller uses the current global length WORD for both helper selection and
    count, which can differ from the earlier local serialization length.
    """
    if type(data) is not bytes or type(count) is not int or not 0 <= count <= 0xffffffff:
        raise ValueError('Owned bytes and raw DWORD count required')
    if type(variant) is not int or variant not in (0, 1):
        raise ValueError('Explicit source helper variant required')
    signed = count if count < 0x80000000 else count - 0x100000000
    # For count<=6 no index satisfies the source guards, even for empty data.
    stop = max(4, signed - 2)
    if stop > 4 and stop > len(data):
        raise ValueError('Reached source write lies outside the owned byte buffer')
    out = bytearray(data)
    even, odd = ((0x6e, 0x5e), (0x58, 0x4a))[variant]
    for i in range(4, stop):
        out[i] = (out[i] + (odd if i & 1 else even)) & 255
    return bytes(out)

def build_session_status_wire(prepared, *, entry_observed=False, transform_length_word=None):
    """Serialize the bounded normal stage, preserving an independently read WORD.

    The source can overflow its fixed buffer for a long string. Such executions
    are reported unsupported rather than truncated or passed off as equivalent.
    This atomic stage assumes ordinary completion of memcpy/string helpers;
    it does not model their exceptions, concurrent changes or return registers.
    """
    if not isinstance(prepared, SessionStatusPrepared) or type(entry_observed) is not bool:
        raise ValueError('Typed prepared stage and explicit entry observation required')
    if not entry_observed:
        return SessionStatusWire(False, missing='004fa097 stage entry unobserved')
    if transform_length_word is not None and (type(transform_length_word) is not int or
                                             not 0 <= transform_length_word <= 0xffff):
        raise ValueError('Fresh source global WORD required')
    v = prepared.values; out = bytearray(); writes = []
    def raw(label, data):
        writes.append((len(out), bytes(data), label)); out.extend(data)
    def scalar(label, value, size):
        raw(label, (value & ((1 << (8*size))-1)).to_bytes(size, 'little'))
    raw('header', b'\xaa\x55\x00\x00')
    scalar('message_kind', 2, 1)
    scalar('session_byte', v['session_byte'], 1)
    scalar('name_header_byte', v['name_header_byte'], 1)
    raw('captured_string_bytes', prepared.serialized_name)
    for key in ('mode_byte', 'status_byte', 'getter_46209c', 'getter_462670',
                'getter_46256c', 'ratio_division_eax'):
        scalar(key, v[key], 1)
    scalar('getter_46258c', v['getter_46258c'], 4)
    scalar('zero_word', 0, 2)
    for i in range(3): scalar('zero_dword_%d'%i, 0, 4)
    scalar('getter_4625ac', v['getter_4625ac'], 4)
    scalar('getter_4625d8', v['getter_4625d8'], 4)
    scalar('exclusive_byte', v['exclusive_byte'], 1)
    raw('trailer', b'\x55\xaa')
    length = len(out)
    if length > 512:
        return SessionStatusWire(False, writes=tuple(writes), missing='Source buffer overflow effects unmodeled')
    encoded = (length + (0x1f40 if length & 1 else 0x3afc)) & 0xffff
    out[2:4] = encoded.to_bytes(2, 'little')
    writes.append((2, bytes(out[2:4]), 'encoded_local_length'))
    plain = bytes(out)
    if transform_length_word is None:
        return SessionStatusWire(False, plain_frame=plain, length_word=length,
                                 writes=tuple(writes), missing='Fresh global555db8 WORD required')
    # The source reloads the global before selecting either transform. This
    # stage supports one stable observation; reentrant changes between these
    # fresh reads are not modeled as an ordinary single transform.
    count = transform_length_word
    if count > 514:
        return SessionStatusWire(False, plain_frame=plain, length_word=length,
                                 writes=tuple(writes), missing='Transform writes outside source buffer')
    buffer = plain + bytes(512-length)
    wire = transform_status_bytes(buffer, count, count & 1)
    return SessionStatusWire(True, plain, wire[:length], wire, length,
                             tuple(writes), helper='004f9564' if count & 1 else '004f94f8')
