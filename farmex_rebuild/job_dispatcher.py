"""Pure Richard class-head replay and Warrior skill priority, without game IO.

Helper observations are explicit caller inputs, never simulated game success.
Addresses name raw source gates/helpers, not executable runtime addresses.
"""
import math
from dataclasses import dataclass, replace
from typing import Mapping, Optional, Tuple


HEADS = {'warrior': '00501b64', 'priest': '004d1be4',
         'mage': '0049bad0', 'rogue': '004de490', 'kurian': '00471954'}


def _number(value, name, optional=False):
    if value is None and optional:
        return
    if type(value) is not int or value < 0:
        raise ValueError(name + ' must be a nonnegative integer')


@dataclass(frozen=True)
class JobSnapshot:
    now_ms: int
    locked_561f7e: Optional[bool] = None
    raw_byte_55402c: Optional[int] = None
    raw_float_554030: Optional[float] = None
    guard_fe384: Optional[bool] = None
    guard_46fe90: Optional[bool] = None
    attack_enabled_561f6c: Optional[bool] = None
    target_id_562040: Optional[int] = None
    target_ready_56204c: Optional[bool] = None
    current_target_462630: Optional[int] = None
    target_mode_561f64: Optional[int] = None
    target_raw_byte_554034: Optional[int] = None
    priest_pointer_a_nonzero: Optional[bool] = None
    priest_pointer_b_nonzero: Optional[bool] = None
    rogue_raw_463fc4: Optional[int] = None
    warrior_flag_89: Optional[bool] = None
    warrior_stat_462e08: Optional[int] = None
    mp_4611e0: Optional[int] = None
    rogue_flag_0: Optional[bool] = None
    rogue_flag_1c: Optional[bool] = None
    configured_interval_ms: int = 0
    rogue_minor_interval_ms: int = 0
    class_context_dword: Optional[int] = None

    def __post_init__(self):
        if self.class_context_dword is not None and (type(self.class_context_dword) is not int or not 0<=self.class_context_dword<=0xffffffff):
            raise ValueError('Raw class actor context DWORD required')
        for name in ('now_ms', 'configured_interval_ms', 'rogue_minor_interval_ms'):
            _number(getattr(self, name), name)
        for name in ('raw_byte_55402c', 'target_id_562040', 'current_target_462630',
                     'target_mode_561f64', 'target_raw_byte_554034', 'rogue_raw_463fc4',
                     'warrior_stat_462e08', 'mp_4611e0'):
            _number(getattr(self, name), name, True)
        for name in ('locked_561f7e', 'guard_fe384', 'guard_46fe90',
                     'attack_enabled_561f6c', 'target_ready_56204c',
                     'priest_pointer_a_nonzero', 'priest_pointer_b_nonzero',
                     'warrior_flag_89', 'rogue_flag_0', 'rogue_flag_1c'):
            value = getattr(self, name)
            if value is not None and type(value) is not bool:
                raise ValueError(name + ' must be boolean or unknown')
        if self.raw_float_554030 is not None and (
                type(self.raw_float_554030) not in (float, int)
                or not math.isfinite(self.raw_float_554030)):
            raise ValueError('raw float must be finite or unknown')


@dataclass(frozen=True)
class JobState:
    shared_last_ms: int = 0        # Warrior+1b0; Mage00553e38
    mage_interval_ms: int = 0     # Mage00553e34
    warrior_special_last_ms: int = 0  # Warrior+98
    priest_attack_last_ms: int = 0    # Priest+120
    rogue_minor_last_ms: int = 0      # 0056ff30
    rogue_attack_last_ms: int = 0     # Rogue+20
    rogue_special_last_ms: int = 0    # 0056ff34

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            _number(getattr(self, name), name)


@dataclass(frozen=True)
class HelperReply:
    returned_nonzero: Optional[bool] = None
    locked_after: Optional[bool] = None
    chat_consumer: object = None
    normal_returned: Optional[bool] = None

    def __post_init__(self):
        for value in (self.returned_nonzero, self.locked_after,self.normal_returned):
            if value is not None and type(value) is not bool:
                raise ValueError('helper reply values must be bool or unknown')
        if self.chat_consumer is not None:
            from chat_skill_consumers import ChatConsumerPlan
            if not isinstance(self.chat_consumer,ChatConsumerPlan):raise ValueError('Typed bound chat consumer required')

def checked_chat_reply(address,context,reply,check_return):
    child=reply.chat_consumer
    expected={'004994bc':'Mage','004da568':'Rogue','004cee18':'Priest'}.get(address)
    if child is None or expected is None or child.family!=expected:raise ValueError('Bound consumer differs from reached source helper')
    if context is None:return None,'chat consumer actor context DWORD'
    if child.actor_context_dword!=context:raise ValueError('Bound consumer actor context differs from class-head argument')
    if not child.complete:return None,'bound chat consumer: '+child.missing
    if type(child.return_low_al) is not int or child.return_low_al not in (0,1):raise ValueError('Known source lowAL required')
    if reply.normal_returned is not True:return None,'normal:'+address
    outcome=bool(child.return_low_al)
    if check_return and reply.returned_nonzero is not None and reply.returned_nonzero!=outcome:
        raise ValueError('Parent lowAL observation differs from bound consumer result')
    return outcome,None


@dataclass(frozen=True)
class DispatchResult:
    status: str
    calls: Tuple[str, ...]
    state: JobState
    reason: str = ''
    local_lock_ms: Optional[int] = None
    chat_consumers: tuple = ()


class _Unknown(Exception):
    pass


def dispatch_job(job: str, snapshot: JobSnapshot, state: JobState = JobState(),
                 replies: Optional[Mapping[str, HelperReply]] = None) -> DispatchResult:
    """Replay one class-head invocation using ordered explicit helper replies.

    A call is an intent. Missing reply stops before dependent branching.
    Void/helper side effects require an explicit post-call lock observation.
    Terminal calls require no reply when source does not inspect their result.
    No timers are acknowledged server timers; source local changes only.
    """
    if job not in HEADS or not isinstance(snapshot, JobSnapshot) or not isinstance(state, JobState):
        raise ValueError('unknown job or invalid snapshot/state')
    replies = {} if replies is None else replies
    if not isinstance(replies, Mapping) or any(not isinstance(v, HelperReply) for v in replies.values()):
        raise ValueError('replies must map helper addresses to HelperReply')
    if any(getattr(state, n) > snapshot.now_ms for n in state.__dataclass_fields__ if n != 'mage_interval_ms'):
        raise ValueError('state timestamp is in the future')
    s, st, calls, lock = snapshot, state, [], snapshot.locked_561f7e
    bound_consumers=[]

    def need(value, name):
        if value is None:
            raise _Unknown(name)
        return value

    def emit(address, result=False, terminal=False):
        nonlocal lock
        calls.append(address)
        if terminal:
            return None
        reply = replies.get(address)
        if reply is None:
            raise _Unknown('helper:' + address)
        outcome=None
        if reply.chat_consumer is not None:
            bound_consumers.append((address,reply.chat_consumer))
            outcome,missing=checked_chat_reply(address,s.class_context_dword,reply,result)
            if missing is not None:raise _Unknown(missing)
        lock = reply.locked_after
        if result:
            if reply.chat_consumer is not None:return outcome
            return need(reply.returned_nonzero, 'return:' + address)
        return None

    def unlocked():
        return not need(lock, 'DAT_00561f7e')

    def raw_gate(strict_negative=False):
        if need(s.raw_byte_55402c, 'byte:+DAT_0055402c') != 0:
            return False
        value = need(s.raw_float_554030, 'float:+DAT_00554030')
        return value < 0 if strict_negative else value <= 0

    def route_clear():
        return not need(s.guard_fe384, 'FUN_004fe384') and not need(s.guard_46fe90, 'FUN_0046fe90')

    def mismatch():
        return need(s.current_target_462630, 'FUN_00462630') != need(s.target_id_562040, 'DAT_00562040')

    def switch_allowed():
        return need(s.target_mode_561f64, 'DAT_00561f64') not in (1, 5)

    def finish(reason='', status='complete', local_lock_ms=None):
        return DispatchResult(status, tuple(calls), st, reason, local_lock_ms,tuple(bound_consumers))

    try:
        if job == 'rogue':
            # Minor is before raw byte/float and global-lock checks.
            if need(s.rogue_flag_0, 'Rogue+0') and s.now_ms - st.rogue_minor_last_ms >= s.rogue_minor_interval_ms:
                if emit('004da25c', True):
                    st = replace(st, rogue_minor_last_ms=s.now_ms)
            if not raw_gate():
                return finish('raw_gate')
            emit('004da2d4')
            if not unlocked():
                return finish('locked_after_004da2d4')
            emit('004da568')
            if not unlocked():
                return finish('locked_after_004da568')
            emit('004dc820')
            if not unlocked() or not need(s.attack_enabled_561f6c, 'DAT_00561f6c') or not route_clear():
                return finish('attack_gate')
            if need(s.rogue_flag_1c, 'Rogue+1c') and need(s.rogue_raw_463fc4, 'FUN_00463fc4') == 1:
                if s.now_ms - st.rogue_special_last_ms < s.configured_interval_ms:
                    return finish('special_interval')
                st = replace(st, rogue_special_last_ms=s.now_ms)
                emit('004e0230', terminal=True)
                return finish('rogue_special')
            if not need(s.target_ready_56204c, 'DAT_0056204c'):
                return finish('no_ready_target')
            if need(s.target_raw_byte_554034, 'target_byte:+DAT_00554034') in (4, 5):
                return finish('target_raw_state')
            if mismatch():
                if switch_allowed():
                    emit('0046493c', terminal=True)
                return finish('retarget_or_preserve')
            if need(s.rogue_raw_463fc4, 'FUN_00463fc4') == 1:
                emit('004de224', terminal=True)
                return finish('rogue_path_1')
            if s.now_ms - st.rogue_attack_last_ms >= s.configured_interval_ms:
                if emit('004dd2e0', True):
                    st = replace(st, rogue_attack_last_ms=s.now_ms)
                    return finish('rogue_first_attack')
            emit('0040da60')
            if s.now_ms - st.rogue_attack_last_ms >= s.configured_interval_ms:
                emit('004dd780', terminal=True)
            return finish()

        if not unlocked():
            return finish('locked')
        if job == 'priest':
            emit('004cf8b8')  # Before the raw byte/float gates.
        if not raw_gate(strict_negative=(job == 'kurian')):
            return finish('raw_gate')

        if job == 'warrior':
            if not route_clear():
                return finish('route_gate')
            if s.now_ms - st.shared_last_ms >= 500:
                if emit('005006e4', True):
                    st = replace(st, shared_last_ms=s.now_ms)
                    return finish('warrior_support')
            if need(s.warrior_flag_89, 'Warrior+89'):
                if (s.now_ms - st.shared_last_ms >= s.configured_interval_ms
                        and s.now_ms - st.warrior_special_last_ms >= 30000
                        and need(s.warrior_stat_462e08, 'FUN_00462e08') > 44
                        and need(s.mp_4611e0, 'FUN_004611e0') > 59):
                    st = replace(st, shared_last_ms=s.now_ms, warrior_special_last_ms=s.now_ms)
                    emit('0050378c', terminal=True)
                    return finish('warrior_special', local_lock_ms=2000)
            if need(s.target_id_562040, 'DAT_00562040') == 0:
                return finish('no_target')
            if need(s.target_ready_56204c, 'DAT_0056204c') and mismatch():
                if switch_allowed():
                    emit('0046493c', terminal=True)
                return finish('retarget_or_preserve')
            if unlocked():
                emit('0040da60')
            if s.now_ms - st.shared_last_ms >= s.configured_interval_ms:
                if emit('00500e90', True):
                    st = replace(st, shared_last_ms=s.now_ms)
            return finish()

        if job == 'mage':
            if s.now_ms - st.shared_last_ms >= st.mage_interval_ms:
                for address in ('00499b88', '00499620', '004994bc'):
                    if emit(address, True):
                        st = replace(st, shared_last_ms=s.now_ms, mage_interval_ms=650)
                        return finish('mage_support:' + address)
            if not need(s.attack_enabled_561f6c, 'DAT_00561f6c') or not unlocked() or not route_clear():
                return finish('attack_gate')
            if not need(s.target_ready_56204c, 'DAT_0056204c'):
                return finish('no_ready_target')
            if need(s.target_id_562040, 'DAT_00562040') != 0 and mismatch():
                if switch_allowed():
                    emit('0046493c', terminal=True)
                return finish('retarget_or_preserve')
            if unlocked():
                emit('0040da60')
            if s.now_ms - st.shared_last_ms >= st.mage_interval_ms:
                if emit('0049bc9c', True):
                    st = replace(st, shared_last_ms=s.now_ms, mage_interval_ms=s.configured_interval_ms)
            return finish()

        if job == 'priest':
            for address in ('004d0c18', '004cfc74', '004cee18', '004d0eb0'):
                emit(address)
            if not route_clear() or need(s.target_id_562040, 'DAT_00562040') == 0:
                return finish('target_or_route_gate')
            if need(s.target_raw_byte_554034, 'target_byte:+DAT_00554034') in (4, 5):
                return finish('target_raw_state')
            # Source does not return after this switch, unlike other classes.
            if need(s.target_ready_56204c, 'DAT_0056204c') and mismatch() and switch_allowed():
                emit('0046493c')
            if not need(s.priest_pointer_a_nonzero, 'Priest:pointer_helper_A') or not need(s.priest_pointer_b_nonzero, 'Priest:pointer_helper_B'):
                return finish('priest_pointer_gate')
            emit('004d0434')
            if unlocked():
                emit('0040da60')
            if s.now_ms - st.priest_attack_last_ms >= s.configured_interval_ms:
                emit('004d1694', terminal=True)
            return finish()

        # Kurian head has a strict <0 raw float gate, no support/attack queue.
        if not route_clear() or need(s.target_id_562040, 'DAT_00562040') == 0:
            return finish('target_or_route_gate')
        if need(s.target_ready_56204c, 'DAT_0056204c') and mismatch():
            if switch_allowed():
                emit('0046493c', terminal=True)
            return finish('retarget_or_preserve')
        if unlocked():
            emit('0040da60', terminal=True)
        return finish()
    except _Unknown as exc:
        return finish(str(exc), 'needs_observation')


@dataclass(frozen=True)
class WarriorSkillRow:
    flag_offset: int
    stat_reader: Optional[str]
    stat_minimum: Optional[int]
    mp_minimum: int
    timer_read_offset: Optional[int]
    interval_ms: Optional[int]
    timer_write_offset: Optional[int]
    skill_number: Optional[int]
    helper: str


@dataclass(frozen=True)
class WarriorSkillSnapshot:
    now_ms: int
    distance: Optional[float]
    configured_range: Optional[int]
    mp: Optional[int]
    flags: Mapping[int, Optional[bool]]
    raw_stats: Mapping[str, Optional[int]]
    last_ms_by_offset: Mapping[int, Optional[int]]
    raw_skill_prefix_46256c: Optional[int] = None

    def __post_init__(self):
        _number(self.now_ms, 'now_ms')
        _number(self.mp, 'mp', True)
        _number(self.raw_skill_prefix_46256c, 'skill prefix', True)
        if self.configured_range is not None and type(self.configured_range) is not int:
            raise ValueError('configured range must be integer or unknown')
        if self.distance is not None and (type(self.distance) not in (int, float) or not math.isfinite(self.distance) or self.distance < 0):
            raise ValueError('distance must be finite and nonnegative')
        for mapping in (self.flags, self.raw_stats, self.last_ms_by_offset):
            if not isinstance(mapping, Mapping):
                raise ValueError('flags/stats/timers must be mappings')
        for value in self.flags.values():
            if value is not None and type(value) is not bool:
                raise ValueError('flag must be bool or unknown')
        for value in self.raw_stats.values():
            _number(value, 'raw stat', True)
        for value in self.last_ms_by_offset.values():
            _number(value, 'last timestamp', True)
            if value is not None and value > self.now_ms:
                raise ValueError('last timestamp in future')


@dataclass(frozen=True)
class WarriorSkillDecision:
    status: str
    row: Optional[WarriorSkillRow] = None
    skill_id: Optional[int] = None
    local_timer_update: Optional[Tuple[int, int]] = None
    reason: str = ''


def select_warrior_skill(snapshot: WarriorSkillSnapshot) -> WarriorSkillDecision:
    """Exact 00500e90 priority, returns local attempt not server success.

    Unknown earlier eligible branches prevent guessing a later skill.
    Range assembly accepts equality at min(8, configured range).
    Preserve source 0x3c timer read+68 vs write+60 discrepancy.
    """
    if not isinstance(snapshot, WarriorSkillSnapshot):
        raise ValueError('WarriorSkillSnapshot required')
    s = snapshot
    if s.distance is None or s.configured_range is None:
        return WarriorSkillDecision('needs_observation', reason='distance/range')
    if s.distance > min(8, s.configured_range):
        return WarriorSkillDecision('out_of_range')
    for row in WARRIOR_ROWS:
        enabled = s.flags.get(row.flag_offset)
        if enabled is None:
            return WarriorSkillDecision('needs_observation', reason='flag:+%x' % row.flag_offset)
        if not enabled:
            continue
        if row.stat_reader is not None:
            stat = s.raw_stats.get(row.stat_reader)
            if stat is None:
                return WarriorSkillDecision('needs_observation', reason='stat:' + row.stat_reader)
            if stat < row.stat_minimum:
                continue
        if s.mp is None:
            return WarriorSkillDecision('needs_observation', reason='MP')
        if s.mp < row.mp_minimum:
            continue
        if row.timer_read_offset is not None:
            last = s.last_ms_by_offset.get(row.timer_read_offset)
            if last is None:
                return WarriorSkillDecision('needs_observation', reason='timer:+%x' % row.timer_read_offset)
            if s.now_ms - last < row.interval_ms:
                continue
        skill_id = None
        if row.skill_number is not None and s.raw_skill_prefix_46256c is not None:
            skill_id = s.raw_skill_prefix_46256c * 1000 + row.skill_number
        update = (row.timer_write_offset, s.now_ms) if row.timer_write_offset is not None else None
        return WarriorSkillDecision('local_attempt', row, skill_id, update)
    return WarriorSkillDecision('no_eligible_skill')


# Assembly skill-number arguments; raw stat names retain unknown game semantics.
WARRIOR_ROWS = (
WarriorSkillRow(189, '00462e34', 75, 500, 240, 11200, 240, 775, '00503638'),
    WarriorSkillRow(188, '00462e34', 60, 400, 232, 11200, 232, 760, '00503638'),
    WarriorSkillRow(182, '00462e34', 35, 300, 200, 11200, 200, 735, '00503638'),
    WarriorSkillRow(179, '00462e34', 25, 100, 192, 11200, 192, 725, '00503638'),
    WarriorSkillRow(362, '00462e60', 20, 250, 384, 30000, 384, 820, '0050331c'),
    WarriorSkillRow(361, '00462e60', 15, 400, 376, 60000, 376, 815, '0050331c'),
    WarriorSkillRow(71, '00462ddc', 75, 350, 128, 21000, 128, 575, '0050331c'),
    WarriorSkillRow(360, '00462e60', 2, 300, 368, 10100, 368, 802, '0050331c'),
    WarriorSkillRow(185, '00462e34', 53, 90, 224, 3100, 224, 752, '0050331c'),
    WarriorSkillRow(66, '00462ddc', 50, 60, 120, 3100, 120, 554, '0050331c'),
    WarriorSkillRow(184, '00462e34', 43, 90, 216, 3100, 216, 745, '0050331c'),
    WarriorSkillRow(64, '00462ddc', 40, 60, 112, 3100, 112, 540, '0050331c'),
    WarriorSkillRow(181, '00462e34', 33, 60, 208, 3100, 208, 733, '0050331c'),
    WarriorSkillRow(62, '00462ddc', 30, 40, 104, 3100, 104, 530, '0050331c'),
    WarriorSkillRow(60, '00462ddc', 20, 84, 104, 5100, 96, 520, '0050331c'),
    WarriorSkillRow(58, '00462ddc', 10, 20, 88, 3100, 88, 510, '0050331c'),
    WarriorSkillRow(56, '00462670', 10, 10, 80, 3100, 80, 500, '0050331c'),
    WarriorSkillRow(3, '00462670', 9, 10, 24, 3100, 24, 9, '0050331c'),
    WarriorSkillRow(2, '00462670', 5, 4, 16, 3100, 16, 5, '0050331c'),
    WarriorSkillRow(1, '00462670', 3, 8, 8, 3100, 8, 3, '0050331c'),
    WarriorSkillRow(190, '00462e34', 83, 500, None, None, None, 782, '0050331c'),
    WarriorSkillRow(72, '00462ddc', 80, 400, None, None, None, 580, '0050331c'),
    WarriorSkillRow(70, '00462ddc', 70, 400, None, None, None, 570, '0050331c'),
    WarriorSkillRow(187, '00462e34', 60, 375, None, None, None, 758, '0050331c'),
    WarriorSkillRow(69, '00462ddc', 60, 300, None, None, None, 560, '0050331c'),
    WarriorSkillRow(186, '00462e34', 58, 300, None, None, None, 757, '0050331c'),
    WarriorSkillRow(68, '00462ddc', 57, 250, None, None, None, 557, '0050331c'),
    WarriorSkillRow(67, '00462ddc', 55, 200, None, None, None, 555, '0050331c'),
    WarriorSkillRow(65, '00462ddc', 45, 150, None, None, None, 545, '0050331c'),
    WarriorSkillRow(183, '00462e34', 38, 180, None, None, None, 737, '0050331c'),
    WarriorSkillRow(63, '00462ddc', 35, 120, None, None, None, 535, '0050331c'),
    WarriorSkillRow(180, '00462e34', 28, 135, None, None, None, 727, '0050331c'),
    WarriorSkillRow(61, '00462ddc', 25, 90, None, None, None, 525, '0050331c'),
    WarriorSkillRow(178, '00462e34', 18, 90, None, None, None, 717, '0050331c'),
    WarriorSkillRow(59, '00462ddc', 15, 60, None, None, None, 515, '0050331c'),
    WarriorSkillRow(177, '00462e34', 15, 60, None, None, None, 715, '0050331c'),
    WarriorSkillRow(176, '00462e34', 8, 45, None, None, None, 707, '0050331c'),
    WarriorSkillRow(57, '00462ddc', 5, 30, None, None, None, 505, '0050331c'),
    WarriorSkillRow(0, None, None, 2, None, None, None, None, '004c856c'),
)
