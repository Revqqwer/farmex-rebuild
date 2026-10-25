"""Own raw-data projection of 004bc650, before actor/item metadata helpers.

No packet capture, process access, runtime helper return or UI effect is implied.
The source dispatcher validates opcode/status separately from this byte reader.
"""
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class MerchantSlotExtension:
    data: bytes
    dword: int
    word: int
    byte: int


@dataclass(frozen=True)
class MerchantRawSlot:
    index: int
    item_id: int
    word_a: Optional[int] = None
    word_b: Optional[int] = None
    price: Optional[int] = None
    sell_extra_dword: Optional[int] = None
    extension: Optional[MerchantSlotExtension] = None


@dataclass(frozen=True)
class MerchantScanDataPlan:
    complete: bool
    status: str
    direction: Optional[int] = None
    entity_id: Optional[int] = None
    slots: Tuple[MerchantRawSlot, ...] = ()
    cursor: int = 0
    reads: tuple = ()
    stopped_slot: Optional[int] = None
    reached_fields: tuple = ()
    source_length_gate_passed: bool = False
    native_execution_verified: bool = False
    result_records_verified: bool = False
    live_compatibility_verified: bool = False


def decode_merchant_scan_data(payload):
    """Decode immutable bytes without fabricating metadata or zero padding.

    Cursor helpers increment before dereferencing. Empty slots skip their
    remaining bytes without reading them; that final skip may exceed length.
    Read truncation is an explicit own boundary, not a native source guard.
    Native actor/name/coordinate and item/category/name helper calls interleave
    with the original parser; this standalone data projection does not emulate
    their execution, exceptions, record append or incremental UI updates.
    """
    if type(payload) is not bytes:
        raise ValueError('Immutable supplied reply bytes required')
    if len(payload) < 0x95:
        return MerchantScanDataPlan(True, 'source_length_rejected')
    direction = int(payload[1] == 0x23)
    cursor = 3 if direction else 4
    reads = [(1, 1)]
    fields = []
    slots = []
    entity = None
    index = None

    class Truncated(Exception):
        pass

    def take(width, name, numeric=True):
        nonlocal cursor
        start = cursor
        cursor += width
        reads.append((start, width))
        if start + width > len(payload):
            raise Truncated(name)
        data = payload[start:start + width]
        value = int.from_bytes(data, 'little') if numeric else data
        fields.append((name, value))
        return value

    def finish(complete, status):
        return MerchantScanDataPlan(complete, status, direction, entity, tuple(slots),
            cursor, tuple(reads), None if complete else index, tuple(fields), True)

    try:
        entity = take(2, 'entity_id')
        for index in range(12):
            fields = []
            item = take(4, 'item_id')
            if item == 0:
                cursor += 8 if direction else 12
                slots.append(MerchantRawSlot(index, 0))
                continue
            word_a = take(2, 'word_a')
            word_b = take(2, 'word_b')
            price = take(4, 'price')
            extra = None
            extension = None
            if not direction:
                extra = take(4, 'sell_extra_dword')
                if extra != 0:
                    length = take(2, 'extension_length')
                    data = take(length, 'extension_data', False)
                    dword = take(4, 'extension_dword')
                    word = take(2, 'extension_word')
                    byte = take(1, 'extension_byte')
                    extension = MerchantSlotExtension(data, dword, word, byte)
            slots.append(MerchantRawSlot(index, item, word_a, word_b, price, extra, extension))
        return finish(True, 'raw_slots_decoded')
    except Truncated as error:
        return finish(False, 'truncated:' + str(error))
