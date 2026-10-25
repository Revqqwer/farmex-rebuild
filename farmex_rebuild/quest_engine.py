"""004d5a8c selected-quest replay; queue plans only, no game or network IO.

The caller supplies source record index and script bytes. No invented encoding,
game pointer, lookup result, helper success or server acknowledgement is used.
"""
import math
import struct
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class QuestRecord:
    npc_name: str
    script_bytes: Optional[bytes] = None

    def __post_init__(self):
        if type(self.npc_name) is not str:
            raise ValueError('NPC name must be text')
        if self.script_bytes is not None and (type(self.script_bytes) is not bytes or len(self.script_bytes) > 508):
            raise ValueError('script must be bytes fitting our512-byte serialization cap')


@dataclass(frozen=True)
class QuestSnapshot:
    selected_index: int = -1
    record_index_from_row: Optional[int] = None
    npc_id_465960: Optional[int] = None
    npc_pointer_464a10: Optional[int] = None
    distance: Optional[float] = None
    current_target_462630: Optional[int] = None
    record_data_20: Optional[int] = None
    quest_lookup_4d642c: Optional[int] = None

    def __post_init__(self):
        if type(self.selected_index) is not int or not -0x80000000 <= self.selected_index < 0x80000000:
            raise ValueError('selected index must be signed32')
        for value in (self.record_index_from_row, self.npc_id_465960, self.npc_pointer_464a10,
                      self.current_target_462630, self.record_data_20, self.quest_lookup_4d642c):
            if value is not None and (type(value) is not int or not 0 <= value <= 0xffffffff):
                raise ValueError('DWORD observations or unknown required')
        if self.distance is not None:
            if type(self.distance) not in (float, int) or not math.isfinite(self.distance):
                raise ValueError('finite distance required')
            try:
                single = struct.unpack('<f', struct.pack('<f', self.distance))[0]
            except (struct.error, OverflowError):
                raise ValueError('distance must fit finite float32') from None
            if not math.isfinite(single):
                raise ValueError('distance must fit finite float32')


@dataclass(frozen=True)
class QuestCall:
    helper: str
    arguments: tuple = ()


@dataclass(frozen=True)
class QuestQueuePlan:
    payload: bytes
    delay_ms: int


@dataclass(frozen=True)
class QuestDecision:
    status: str
    calls: Tuple[QuestCall, ...] = ()
    queue_plans: Tuple[QuestQueuePlan, ...] = ()
    reason: str = ''


class _Missing(Exception):
    pass


def plan_take_quest(records, s):
    records = tuple(records)
    if not isinstance(s, QuestSnapshot) or any(not isinstance(r, QuestRecord) for r in records):
        raise ValueError('typed records/snapshot required')
    calls, queue = [], []

    def need(value, label):
        if value is None:
            raise _Missing(label)
        return value

    def call(helper, *arguments):
        calls.append(QuestCall(helper, tuple(arguments)))

    def result(status, reason=''):
        return QuestDecision(status, tuple(calls), tuple(queue), reason)

    try:
        if s.selected_index < 0:
            return result('no_selection')
        index = need(s.record_index_from_row, 'record_index_from_selected_row')
        if index >= len(records):
            # Our typed-record boundary prevents the native unchecked array read.
            return result('invalid_record', 'outside supplied record database')
        record = records[index]
        call('00465960', record.npc_name)
        npc = need(s.npc_id_465960, 'FUN_00465960')
        if npc == 0:
            return result('npc_not_found')
        call('00464a10', npc)
        pointer = need(s.npc_pointer_464a10, 'FUN_00464a10')
        if pointer == 0:
            return result('npc_pointer_missing')
        distance = struct.unpack('<f', struct.pack('<f', need(s.distance, 'distance')))[0]
        if not 0 <= distance <= 10:
            return result('out_of_range')
        call('00462630')
        if need(s.current_target_462630, 'current_target') != npc:
            # Assembly uses the NPC pointer, not the integer lookup ID.
            call('0046493c', pointer)
        call('0046fb38', '005690e0', npc)
        call('0045dc44:record_data_plus20')
        value = need(s.record_data_20, 'record_data_plus20')
        call('004d5244', 'source_quest_object', value)
        call('0045dc44:record_data_plus1c')  # Result is unused in this caller.
        call('004d642c', 'source_quest_record_lookup')
        identifier = need(s.quest_lookup_4d642c, 'FUN_004d642c')
        first = bytes.fromhex('6407') + (identifier & 0xffff).to_bytes(2, 'little') + b'\0\0'
        queue.append(QuestQueuePlan(first, 500))
        call('004c7710', '00561ef8', first, 6, 500)
        script = need(record.script_bytes, 'source_script_bytes')
        # Caller appends only the low length byte, then copies the full string.
        second = b'\x55\x00' + bytes([len(script) & 255]) + script
        queue.append(QuestQueuePlan(second, 1000))
        call('004c7710', '00561ef8', second, len(second), 1000)
        third = second + b'\xff'
        queue.append(QuestQueuePlan(third, 1500))
        call('004c7710', '00561ef8', third, len(third), 1500)
        return result('local_plan')
    except _Missing as error:
        return result('needs_observation', str(error))
