"""Static0045dca8/004f11a0 byte-copy plans; never dereference game pointers.

Source uses a zeroed512-byte local buffer, then ANSI PChar construction and
ANSI-to-Unicode conversion. Codepage0 is observed; its live mapping is unknown.
Unsafe native stack overread/overwrite is reported rather than reproduced.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TextReadRequest:
    address: Optional[int]
    byte_count: int
    indirect: bool


@dataclass(frozen=True)
class TextCopyResult:
    status: str
    ansi_bytes: bytes = b''
    text: Optional[str] = None


def _dword(value):
    if type(value) is not int or not 0 <= value <= 0xffffffff:
        raise ValueError('Raw DWORD required')
    return value


def npc_text_request(record_pointer, field_fe8, raw_field_fec, indirect_pointer=None,
                     *, signed_threshold=True):
    pointer,offset,raw=map(_dword,(record_pointer,field_fe8,raw_field_fec))
    if type(signed_threshold) is not bool:raise ValueError('Explicit source comparison kind required')
    compared=raw if not signed_threshold or raw<0x80000000 else raw-0x100000000
    if compared<16:
        return TextReadRequest((pointer+offset)&0xffffffff,255,False)
    address=None if indirect_pointer is None else _dword(indirect_pointer)
    return TextReadRequest(address,raw,True)


def replay_text_copy(byte_count, readable, copied_bytes=None, *, codec=None):
    _dword(byte_count)
    if readable is None:return TextCopyResult('needs_observation')
    if type(readable) is not bool:raise ValueError('IsBadReadPtr outcome must be observed boolean')
    if not readable:
        #523469 begins with NUL, so the source fallback ANSI PChar is empty.
        return TextCopyResult('complete',text='')
    if byte_count>512:return TextCopyResult('unresolved_native_buffer_overflow')
    if copied_bytes is None:return TextCopyResult('needs_observation')
    if type(copied_bytes) is not bytes or len(copied_bytes)!=byte_count:
        raise ValueError('Exact observed memcpy byte range required')
    buffer=copied_bytes+b'\0'*(512-byte_count)
    end=buffer.find(b'\0')
    if end<0:return TextCopyResult('unresolved_native_string_overread',buffer)
    ansi=buffer[:end]
    if not ansi:return TextCopyResult('complete',ansi,'')
    if codec is None:return TextCopyResult('needs_codepage',ansi)
    if type(codec) is not str:raise ValueError('Explicit observed codepage/codec required')
    try:return TextCopyResult('complete',ansi,ansi.decode(codec,errors='strict'))
    except UnicodeDecodeError:return TextCopyResult('unresolved_conversion',ansi)
