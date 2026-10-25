"""Richard 004d1694 priority replay; no game IO or success acknowledgement.

Raw stat reader names and skill-number arguments retain source semantics.
One caller-supplied monotonic time models the multiple source clock samples.
"""
from dataclasses import dataclass
from typing import Optional, Tuple
from job_dispatcher import WarriorSkillSnapshot


@dataclass(frozen=True)
class PriestAttackRow:
    flag_offset: int
    stat_reader: Optional[str]
    stat_minimum: Optional[int]
    mp_minimum: Optional[int]
    timer_offset: Optional[int]
    interval_ms: Optional[int]
    skill_number: Optional[int]
    helper: str = '004d2ee8'


@dataclass(frozen=True)
class PriestAttackSnapshot(WarriorSkillSnapshot):
    locked_561f7e: Optional[bool] = None

    def __post_init__(self):
        super().__post_init__()
        if self.locked_561f7e is not None and type(self.locked_561f7e) is not bool:
            raise ValueError('lock must be bool or unknown')


@dataclass(frozen=True)
class PriestAttackDecision:
    status: str
    row: Optional[PriestAttackRow] = None
    local_timer_updates: Tuple[Tuple[int, int], ...] = ()
    reason: str = ''


def select_priest_attack(s: PriestAttackSnapshot) -> PriestAttackDecision:
    """Select first eligible branch, preserving unknown earlier observations.

    Source writes +120 before its helper call and a row timer afterwards.
    Updates here are a replay plan, never committed game state/server success.
    Helper result is not tested by source; no fabricated success is required.
    """
    if not isinstance(s, PriestAttackSnapshot):
        raise ValueError('PriestAttackSnapshot required')
    if s.locked_561f7e is None:
        return PriestAttackDecision('needs_observation', reason='DAT_00561f7e')
    if s.locked_561f7e:
        return PriestAttackDecision('locked')
    if s.distance is None or s.configured_range is None:
        return PriestAttackDecision('needs_observation', reason='distance/range')
    if s.distance > min(8, s.configured_range):
        return PriestAttackDecision('out_of_range')
    for row in PRIEST_ATTACK_ROWS:
        enabled = s.flags.get(row.flag_offset)
        if enabled is None:
            return PriestAttackDecision('needs_observation', reason='flag:+%x' % row.flag_offset)
        if not enabled:
            continue
        # The source tests each row timer before its stat and MP.
        if row.timer_offset is not None:
            last = s.last_ms_by_offset.get(row.timer_offset)
            if last is None:
                return PriestAttackDecision('needs_observation', reason='timer:+%x' % row.timer_offset)
            if s.now_ms - last < row.interval_ms:
                continue
        if row.stat_reader is not None:
            stat = s.raw_stats.get(row.stat_reader)
            if stat is None:
                return PriestAttackDecision('needs_observation', reason='stat:' + row.stat_reader)
            if stat < row.stat_minimum:
                continue
        if row.mp_minimum is not None:
            if s.mp is None:
                return PriestAttackDecision('needs_observation', reason='MP')
            if s.mp < row.mp_minimum:
                continue
        updates = ((0x120, s.now_ms),)
        if row.timer_offset is not None:
            updates += ((row.timer_offset, s.now_ms),)
        return PriestAttackDecision('local_attempt', row, updates)
    return PriestAttackDecision('no_eligible_skill')


PRIEST_ATTACK_ROWS = (
    PriestAttackRow(0x0a, '00462ddc', 51, 120, 0x2c, 3050, 0x227),
    PriestAttackRow(0x0e, '00462e08', 51, 120, 0x30, 3050, 0x28a),
    PriestAttackRow(0x12, '00462e34', 51, 120, 0x34, 3050, 0x2ee),
    PriestAttackRow(0x09, '00462ddc', 42, 100, 0x38, 2050, 0x21e),
    PriestAttackRow(0x0d, '00462e08', 42, 100, 0x3c, 2050, 0x281),
    PriestAttackRow(0x11, '00462e34', 42, 100, 0x40, 2050, 0x2e3),
    PriestAttackRow(0x08, '00462ddc', 21, 40, None, None, 0x208),
    PriestAttackRow(0x0c, '00462e08', 21, 40, None, None, 0x26c),
    PriestAttackRow(0x10, '00462e34', 21, 40, None, None, 0x2d1),
    PriestAttackRow(0x07, '00462ddc', 12, 30, None, None, 0x1ff),
    PriestAttackRow(0x0b, '00462e08', 12, 30, None, None, 0x263),
    # Confirmed assembly reads EBP-8 (00462e08), not EBP-c (00462e34).
    PriestAttackRow(0x0f, '00462e08', 12, 30, None, None, 0x2c8),
    PriestAttackRow(0x14, '00462e60', 12, 350, None, None, 0x32f),
    PriestAttackRow(0x13, '00462e60', 2, 200, None, None, 0x322),
    PriestAttackRow(0x02, '00462670', 5, 8, None, None, 6),
    PriestAttackRow(0x00, None, None, None, None, None, None, '004c856c'),
)
