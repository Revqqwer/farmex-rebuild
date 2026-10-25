"""Richard004f2750 special route branches; plans only, no game or network IO.

Randomize is a Change Camp parameter, not a standalone command. This generic
stable-command subset selects one posture action; the raw caller separately
rechecks Otur/Kalk inside their paired body. Numeric inputs are pre-parsed
signed32 observations; this module does not claim to emulate Delphi text parsing.
"""
import math
from dataclasses import dataclass, replace
from typing import Optional, Tuple

SPECIAL_COMMANDS = ('Town', 'Otur', 'Kalk', 'Gate Skill', 'Gate Open', 'Gate',
                    'Delos Gate Open', 'Delos Gate', 'Change Camp', 'NPC')


@dataclass(frozen=True)
class SpecialCommand:
    name: str
    number: Optional[int] = None
    randomize: bool = False

    def __post_init__(self):
        if type(self.name) is not str or type(self.randomize) is not bool:
            raise ValueError('command text and randomize bool required')
        if self.number is not None and (type(self.number) is not int or not -0x80000000 <= self.number < 0x80000000):
            raise ValueError('pre-parsed signed32 number required')


@dataclass(frozen=True)
class SpecialRouteState:
    processing: bool = True
    started: bool = False
    started_qword: int = 0
    auxiliary_phase: int = 0

    def __post_init__(self):
        if type(self.processing) is not bool or type(self.started) is not bool:
            raise ValueError('state flags must be bool')
        if type(self.started_qword) is not int or not 0 <= self.started_qword < 1 << 64:
            raise ValueError('timestamp must be QWORD')
        if type(self.auxiliary_phase) is not int or not 0 <= self.auxiliary_phase <= 0xffffffff:
            raise ValueError('auxiliary phase must be DWORD')


@dataclass(frozen=True)
class SpecialRouteSnapshot:
    now_ms: int
    actor_raw_byte_554020: Optional[int] = None
    hp_4611a0: Optional[int] = None
    max_hp_4611c0: Optional[int] = None
    npc_found_465960: Optional[bool] = None
    npc_pointer_found_464a10: Optional[bool] = None
    npc_distance: Optional[float] = None
    npc_interaction_raw_byte: Optional[int] = None
    displacement: Optional[float] = None
    npc_helper_return_4f11a0: Optional[bool] = None

    def __post_init__(self):
        if type(self.now_ms) is not int or not 0 <= self.now_ms <= 0xffffffff:
            raise ValueError('clock must be DWORD')
        for value in (self.npc_found_465960, self.npc_pointer_found_464a10, self.npc_helper_return_4f11a0):
            if value is not None and type(value) is not bool:
                raise ValueError('bool or unknown required')
        for value in (self.actor_raw_byte_554020, self.npc_interaction_raw_byte):
            if value is not None and (type(value) is not int or not 0 <= value <= 255):
                raise ValueError('byte or unknown required')
        for value in (self.hp_4611a0, self.max_hp_4611c0):
            if value is not None and (type(value) is not int or not -0x80000000 <= value < 0x80000000):
                raise ValueError('signed32 raw health required')
        for value in (self.npc_distance, self.displacement):
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
                raise ValueError('finite nonnegative distance required')


@dataclass(frozen=True)
class SpecialRouteDecision:
    status: str
    state: SpecialRouteState
    calls: Tuple[str, ...] = ()
    queue_payloads: Tuple[bytes, ...] = ()
    reason: str = ''


class _Missing(Exception):
    pass

def source_half_health_threshold(maximum):
    """Source IMUL low32 followed by signed IDIV100, not floor division."""
    product=(maximum*50)&0xffffffff
    if product>=1<<31:product-=1<<32
    return abs(product)//100*(-1 if product<0 else 1)


def special_route_step(command, snapshot, state=SpecialRouteState()):
    if not isinstance(command, SpecialCommand) or not isinstance(snapshot, SpecialRouteSnapshot) or not isinstance(state, SpecialRouteState):
        raise ValueError('typed command/snapshot/state required')
    c, s, st, calls, packets = command, snapshot, state, [], []

    def need(value, label):
        if value is None:
            raise _Missing(label)
        return value

    def result(status, reason=''):
        return SpecialRouteDecision(status, st, tuple(calls), tuple(packets), reason)

    def start():
        nonlocal st
        st = replace(st, started=True, started_qword=s.now_ms)
        return result('started')

    def finish():
        nonlocal st
        st = replace(st, started=False, processing=False)
        return result('step_complete')

    def wait(milliseconds):
        delta = (s.now_ms - st.started_qword) & ((1 << 64) - 1)
        if delta >= 1 << 63:
            delta -= 1 << 64
        return finish() if delta >= milliseconds else result('waiting')

    def actor_clear():
        return need(s.actor_raw_byte_554020, 'actor_raw_byte') == 0

    def health_ready():
        calls.append('00464714')
        maximum = need(s.max_hp_4611c0, 'FUN_004611c0')
        threshold = source_half_health_threshold(maximum)
        return need(s.hp_4611a0, 'FUN_004611a0') >= threshold

    try:
        if not st.processing:
            return result('inactive')
        if c.name not in SPECIAL_COMMANDS:
            # Native unknown command clears processing; it is not Randomize.
            st=replace(st,processing=False)
            return result('step_complete')
        if st.started:
            if c.name == 'NPC':
                calls.append('004f11a0')
                return finish() if need(s.npc_helper_return_4f11a0, 'return:004f11a0') else result('waiting')
            if c.name == 'Delos Gate' and need(s.displacement, 'displacement_from_saved_position') <= 10:
                return result('waiting', 'displacement must exceed10')
            return wait({'Town': 2000, 'Otur': 2000, 'Kalk': 2000, 'Gate Skill': 3000,
                         'Gate Open': 1500, 'Gate': 3000, 'Delos Gate Open': 1000,
                         'Delos Gate': 3000, 'Change Camp': 2000}[c.name])
        if c.name in ('Otur', 'Kalk'):
            if not actor_clear():
                return result('blocked')
            calls.append('00465de0' if c.name == 'Otur' else '00465e50')
            return start()
        if c.name in ('Town', 'Change Camp'):
            if not health_ready():
                return result('waiting', 'health_below_half')
            if c.name == 'Town':
                calls.append('004c8604')
            elif c.randomize:
                calls.append('004c8a98')
            elif need(c.number, 'Change Camp numeric parameter') != 0:
                calls.append('004c8698')
            return start()
        if not actor_clear():
            return result('blocked')
        if c.name == 'Gate Skill':
            calls.append('004c8d84')
        elif c.name in ('Gate Open', 'Gate'):
            number = need(c.number, 'numeric_gate_parameter') & 0xffffffff
            prefix = b'\x33' if c.name == 'Gate Open' else b'\x4b'
            packets.append(prefix + number.to_bytes(4, 'little'))
            calls.append('004c7710')
        elif c.name == 'Delos Gate':
            number = need(c.number, 'Delos Gate parameter') & 255
            payload = bytearray.fromhex('550010373030315f64756e6765756e2e6c7561')
            payload[1] = number
            packets.append(bytes(payload))
            calls.extend(('004625ac:save_x', '004625d8:save_y', '004c7710'))
        elif c.name == 'Delos Gate Open':
            calls.append('00465960:[Teleport Gate]')
            if need(s.npc_found_465960, 'npc_found'):
                calls.append('00464a10')
                if need(s.npc_pointer_found_464a10, 'npc_pointer_found'):
                    if need(s.npc_distance, 'npc_distance') < 9:
                        if need(s.npc_interaction_raw_byte, 'npc_interaction_raw_byte') != 0:
                            return result('blocked')
                        calls.append('004c8f7c')
                    else:
                        calls.append('004646b4')
            # Native starts the1000ms wait even when no NPC was found.
        elif c.name == 'NPC':
            st = replace(st, auxiliary_phase=1)
        return start()
    except _Missing as error:
        return result('needs_observation', str(error))
