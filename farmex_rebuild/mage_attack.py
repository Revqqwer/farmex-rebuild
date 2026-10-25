"""Pure Richard 0049bc9c replay, with explicit observations and no game IO.

The 62 branch table comes from assembly, not decompiler x87 expressions.
Timer slots are signed 64-bit pairs; current clock is a zero-extended DWORD.
Helper calls and writes below are local plans, never game/server success.
"""
import math
import struct
from dataclasses import dataclass
from typing import Mapping, Optional, Tuple


@dataclass(frozen=True)
class MageAttackRow:
    address: str
    flag_offset: int
    stat_reader: Optional[str]
    stat_minimum: Optional[int]
    mp_minimum: int
    timer_offset: Optional[int]
    interval_ms: Optional[int]
    skill_number: int
    cast_ms: int
    mode: int
    distance_exclusive: float
    stat_first: bool


@dataclass(frozen=True)
class MageAttackSnapshot:
    now_ms: int
    distance: Optional[float]
    configured_range: Optional[int]
    mp: Optional[int]
    flags: Mapping[int, Optional[bool]]
    raw_stats: Mapping[str, Optional[int]]
    timer_values: Mapping[int, Optional[int]]
    locked_561f7e: Optional[bool] = None
    raw_field_55403c_nonzero: Optional[bool] = None
    raw_field_554020_nonzero: Optional[bool] = None

    def __post_init__(self):
        if type(self.now_ms) is not int or not 0 <= self.now_ms <= 0xffffffff:
            raise ValueError('now_ms must be a DWORD clock sample')
        if self.configured_range is not None and (type(self.configured_range) is not int or not -0x80000000 <= self.configured_range < 0x80000000):
            raise ValueError('configured_range must be signed DWORD or unknown')
        if self.distance is not None:
            if type(self.distance) not in (int, float) or not math.isfinite(self.distance) or self.distance < 0:
                raise ValueError('distance must be finite and nonnegative')
            try:
                value = struct.unpack('<f', struct.pack('<f', self.distance))[0]
            except (OverflowError, struct.error):
                raise ValueError('distance must fit finite float32') from None
            if not math.isfinite(value):
                raise ValueError('distance must fit finite float32')
        for mapping in (self.flags, self.raw_stats, self.timer_values):
            if not isinstance(mapping, Mapping):
                raise ValueError('flags/stats/timers must be mappings')
        for key in self.flags:
            if type(key) is not int or key < 0:
                raise ValueError('flag offsets must be nonnegative integers')
        for value in (*self.flags.values(), self.locked_561f7e,
                      self.raw_field_55403c_nonzero, self.raw_field_554020_nonzero):
            if value is not None and type(value) is not bool:
                raise ValueError('flags/observations must be bool or unknown')
        for value in (*self.raw_stats.values(), self.mp):
            if value is not None and (type(value) is not int or not -0x80000000 <= value < 0x80000000):
                raise ValueError('stats/MP must be signed DWORD or unknown')
        for key, value in self.timer_values.items():
            if type(key) is not int or key < 0 or (value is not None and (type(value) is not int or not -(1 << 63) <= value < (1 << 63))):
                raise ValueError('timer slot must be signed 64-bit or unknown')


@dataclass(frozen=True)
class MageAttackDecision:
    status: str
    row: Optional[MageAttackRow] = None
    calls: Tuple[str, ...] = ()
    local_timer_updates: Tuple[Tuple[int, int], ...] = ()
    local_lock_ms: Optional[int] = None
    local_lock_started_ms: Optional[int] = None
    reason: str = ''


def select_mage_attack(s: MageAttackSnapshot) -> MageAttackDecision:
    """Replay priority and local post-selection plan using supplied observations.

    Source samples its clock repeatedly; this replay uses one caller sample.
    Future timer slots are valid and block candidates. No rollover correction is
    invented: zero-extended now minus signed stored pair is compared as int64.
    """
    if not isinstance(s, MageAttackSnapshot):
        raise ValueError('MageAttackSnapshot required')
    def unknown(name, row=None, calls=()):
        return MageAttackDecision('needs_observation', row, calls, reason=name)
    if s.locked_561f7e is None:
        return unknown('DAT_00561f7e')
    if s.locked_561f7e:
        return MageAttackDecision('locked')
    if s.distance is None or s.configured_range is None:
        return unknown('distance/range')
    distance = struct.unpack('<f', struct.pack('<f', s.distance))[0]
    limit = float(s.configured_range) if s.configured_range < 8 else 45.0
    if distance > limit:
        return MageAttackDecision('out_of_range')
    for row in MAGE_ATTACK_ROWS:
        if distance >= row.distance_exclusive:
            continue
        enabled = s.flags.get(row.flag_offset)
        if enabled is None:
            return unknown('flag:+%x' % row.flag_offset)
        if not enabled:
            continue
        # Final level-gated generic rows test stat before MP.
        stat = s.raw_stats.get(row.stat_reader) if row.stat_reader else None
        if row.stat_first:
            if stat is None:
                return unknown('stat:' + row.stat_reader)
            if stat < row.stat_minimum:
                continue
        if s.mp is None:
            return unknown('MP')
        if s.mp < row.mp_minimum:
            continue
        if row.stat_reader is not None and not row.stat_first:
            if stat is None:
                return unknown('stat:' + row.stat_reader)
            if stat < row.stat_minimum:
                continue
        if row.timer_offset is not None:
            stored = s.timer_values.get(row.timer_offset)
            if stored is None:
                return unknown('timer:+%x' % row.timer_offset)
            delta = (s.now_ms - stored) & ((1 << 64) - 1)
            if delta >= (1 << 63):
                delta -= (1 << 64)
            if delta < row.interval_ms:
                continue
        if s.raw_field_55403c_nonzero is None:
            return unknown('raw:+DAT_0055403c', row)
        calls = ('00465ef8',) if s.raw_field_55403c_nonzero else ()
        if row.mode == 1:
            return MageAttackDecision('local_attempt', row, calls + ('0049d79c',))
        if s.raw_field_554020_nonzero is None:
            return unknown('raw:+DAT_00554020', row, calls)
        if s.raw_field_554020_nonzero:
            return MageAttackDecision('cast_blocked', row, calls)
        updates = () if row.timer_offset is None else ((row.timer_offset, (s.now_ms + row.cast_ms) & 0xffffffff),)
        return MageAttackDecision('local_attempt', row, calls + ('0049ea1c',),
                                  updates, row.cast_ms, s.now_ms)
    return MageAttackDecision('no_eligible_skill')



MAGE_ATTACK_ROWS = (
    MageAttackRow('0049bd8f', 24, '00462e08', 70, 600, 80, 18300, 671, 1300, 3, 26, False),
    MageAttackRow('0049bde1', 21, '00462ddc', 70, 600, 56, 18300, 571, 1300, 3, 26, False),
    MageAttackRow('0049be33', 27, '00462e34', 70, 600, 104, 18300, 771, 1300, 3, 26, False),
    MageAttackRow('0049be85', 25, '00462e08', 60, 400, 88, 15300, 660, 1500, 3, 26, False),
    MageAttackRow('0049bed7', 22, '00462ddc', 60, 400, 64, 15300, 560, 1500, 3, 26, False),
    MageAttackRow('0049bf29', 28, '00462e34', 60, 400, 112, 15300, 760, 1500, 3, 26, False),
    MageAttackRow('0049bf7b', 26, '00462e08', 45, 200, 96, 15300, 645, 1500, 3, 26, False),
    MageAttackRow('0049bfcd', 23, '00462ddc', 45, 200, 72, 15300, 545, 1500, 3, 26, False),
    MageAttackRow('0049c01f', 29, '00462e34', 45, 200, 120, 15300, 745, 1500, 3, 26, False),
    MageAttackRow('0049c071', 19, '00462e08', 33, 150, 40, 1000, 633, 1500, 3, 26, False),
    MageAttackRow('0049c0c3', 18, '00462ddc', 33, 150, 32, 1000, 533, 1500, 3, 26, False),
    MageAttackRow('0049c115', 20, '00462e34', 33, 150, 48, 1000, 733, 1500, 3, 26, False),
    MageAttackRow('0049c17f', 165, '00462e08', 80, 350, 376, 60000, 674, 1500, 2, 29, False),
    MageAttackRow('0049c1da', 150, '00462ddc', 80, 390, 304, 15000, 575, 1100, 2, 29, False),
    MageAttackRow('0049c235', 163, '00462e08', 70, 390, 368, 21300, 670, 1100, 2, 29, False),
    MageAttackRow('0049c290', 147, '00462ddc', 70, 390, 288, 21300, 570, 1100, 2, 29, False),
    MageAttackRow('0049c2eb', 179, '00462e34', 70, 390, 448, 21300, 770, 1100, 2, 29, False),
    MageAttackRow('0049c346', 162, '00462e08', 57, 220, 360, 20300, 657, 1500, 2, 29, False),
    MageAttackRow('0049c3a1', 146, '00462ddc', 57, 220, 280, 20300, 557, 1500, 2, 29, False),
    MageAttackRow('0049c3fc', 178, '00462e34', 57, 220, 440, 20300, 757, 1500, 2, 29, False),
    MageAttackRow('0049c457', 144, '00462ddc', 54, 220, 272, 6000, 554, 1500, 2, 29, False),
    MageAttackRow('0049c4b2', 176, '00462e34', 54, 200, 432, 6000, 754, 1500, 2, 29, False),
    MageAttackRow('0049c50d', 160, '00462e08', 51, 160, 352, 5300, 651, 1500, 2, 29, False),
    MageAttackRow('0049c568', 143, '00462ddc', 51, 160, 264, 5300, 551, 1500, 2, 29, False),
    MageAttackRow('0049c5c3', 175, '00462e34', 51, 160, 424, 5300, 751, 1500, 2, 29, False),
    MageAttackRow('0049c61e', 157, '00462e08', 39, 150, 344, 4300, 639, 1500, 2, 29, False),
    MageAttackRow('0049c679', 140, '00462ddc', 39, 150, 256, 4300, 539, 1500, 2, 29, False),
    MageAttackRow('0049c6d4', 172, '00462e34', 39, 150, 416, 4300, 739, 1500, 2, 29, False),
    MageAttackRow('0049c747', 156, '00462e08', 35, 150, 336, 4300, 635, 1500, 2, 38, False),
    MageAttackRow('0049c7a2', 139, '00462ddc', 35, 150, 248, 4300, 535, 1500, 2, 38, False),
    MageAttackRow('0049c7fd', 171, '00462e34', 35, 150, 408, 4300, 735, 1500, 2, 38, False),
    MageAttackRow('0049c858', 155, '00462e08', 27, 80, 328, 4300, 627, 1500, 2, 38, False),
    MageAttackRow('0049c8b0', 138, '00462ddc', 27, 80, 240, 4300, 527, 1500, 2, 38, False),
    MageAttackRow('0049c908', 170, '00462e34', 27, 80, 400, 4300, 727, 1500, 2, 38, False),
    MageAttackRow('0049c960', 153, '00462e08', 15, 50, 320, 4300, 615, 1500, 2, 38, False),
    MageAttackRow('0049c9b8', 136, '00462ddc', 15, 50, 232, 4300, 515, 1500, 2, 38, False),
    MageAttackRow('0049ca10', 168, '00462e34', 15, 50, 392, 4300, 715, 1500, 2, 38, False),
    MageAttackRow('0049ca80', 161, '00462e08', 56, 95, None, None, 656, 1000, 2, 9.5, False),
    MageAttackRow('0049cab2', 145, '00462ddc', 56, 95, None, None, 556, 1000, 2, 9.5, False),
    MageAttackRow('0049cae4', 177, '00462e34', 56, 95, None, None, 756, 1000, 2, 9.5, False),
    MageAttackRow('0049cb16', 159, '00462e08', 43, 75, None, None, 643, 1000, 2, 9.5, False),
    MageAttackRow('0049cb48', 142, '00462ddc', 43, 75, None, None, 543, 1000, 2, 9.5, False),
    MageAttackRow('0049cb7a', 174, '00462e34', 43, 75, None, None, 743, 1000, 2, 9.5, False),
    MageAttackRow('0049cbc4', 148, '00462ddc', 72, 300, None, None, 572, 0, 1, 9.5, False),
    MageAttackRow('0049cbf7', 164, '00462e08', 72, 300, None, None, 672, 0, 1, 9.5, False),
    MageAttackRow('0049cc2a', 180, '00462e34', 72, 300, None, None, 772, 0, 1, 9.5, False),
    MageAttackRow('0049cc5d', 141, '00462ddc', 42, 100, None, None, 542, 0, 1, 9.5, False),
    MageAttackRow('0049cc8d', 158, '00462e08', 42, 100, None, None, 642, 0, 1, 9.5, False),
    MageAttackRow('0049ccbd', 173, '00462e34', 42, 100, None, None, 742, 0, 1, 9.5, False),
    MageAttackRow('0049cced', 133, '00462670', 10, 10, None, None, 10, 0, 1, 9.5, False),
    MageAttackRow('0049cd1d', 17, None, None, 2, None, None, 1, 0, 1, 9.5, False),
    MageAttackRow('0049cd5c', 154, '00462e08', 18, 60, None, None, 618, 1500, 2, 29, False),
    MageAttackRow('0049cd8e', 137, '00462ddc', 18, 60, None, None, 518, 1200, 2, 29, False),
    MageAttackRow('0049cdc0', 169, '00462e34', 18, 60, None, None, 718, 1500, 2, 29, False),
    MageAttackRow('0049ce0a', 151, '00462e08', 3, 20, None, None, 603, 1500, 2, 9.5, False),
    MageAttackRow('0049ce3c', 134, '00462ddc', 3, 20, None, None, 503, 1000, 2, 9.5, False),
    MageAttackRow('0049ce6e', 166, '00462e34', 3, 20, None, None, 703, 1500, 2, 9.5, False),
    MageAttackRow('0049ceb8', 132, '00462670', 9, 15, 216, 4300, 9, 1500, 2, 29, True),
    MageAttackRow('0049cf10', 131, '00462670', 7, 7, 208, 4300, 7, 1500, 2, 29, True),
    MageAttackRow('0049cf68', 130, '00462670', 5, 5, 200, 4300, 5, 1500, 2, 29, True),
    MageAttackRow('0049cfc0', 129, '00462670', 3, 5, 192, 4300, 3, 1500, 2, 29, True),
    MageAttackRow('0049d015', 128, None, None, 4, 184, 4300, 2, 1500, 2, 29, False),
)
