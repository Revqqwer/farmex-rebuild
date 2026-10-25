"""Five alternative class heads, static replay only, no game actions."""
import math
from dataclasses import dataclass, replace
from typing import Mapping, Optional, Tuple
from job_dispatcher import JobSnapshot, HelperReply,checked_chat_reply


@dataclass(frozen=True)
class AlternateSnapshot(JobSnapshot):
    actor_state_554034: Optional[int] = None
    rogue_minor_actor_state_554034: Optional[int] = None
    rogue_attack_actor_state_554034: Optional[int] = None
    warrior_flag_198: Optional[bool] = None
    priest_final_raw_byte_55402c: Optional[int] = None
    priest_final_raw_float_554030: Optional[float] = None
    target_max_hp_positive: Optional[bool] = None
    target_hp_positive: Optional[bool] = None

    def __post_init__(self):
        super().__post_init__()
        for name in ('actor_state_554034', 'rogue_minor_actor_state_554034',
                     'rogue_attack_actor_state_554034', 'priest_final_raw_byte_55402c'):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(name + ' must be nonnegative integer or unknown')
        for name in ('warrior_flag_198', 'target_max_hp_positive', 'target_hp_positive'):
            value = getattr(self, name)
            if value is not None and type(value) is not bool:
                raise ValueError(name + ' must be bool or unknown')
        value = self.priest_final_raw_float_554030
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
            raise ValueError('final raw float must be finite or unknown')


@dataclass(frozen=True)
class AlternateState:
    last_ms: int = 0
    interval_ms: int = 0
    minor_last_ms: int = 0

    def __post_init__(self):
        if any(type(v) is not int or v < 0 for v in (self.last_ms, self.interval_ms, self.minor_last_ms)):
            raise ValueError('state fields must be nonnegative integers')


@dataclass(frozen=True)
class AlternateDecision:
    status: str
    calls: Tuple[str, ...]
    state: AlternateState
    reason: str = ''
    chat_consumers: tuple = ()


class _Missing(Exception):
    pass


def dispatch_alternate(job, snapshot, state=AlternateState(), replies=None):
    """Alternative family, finite floats/monotonic time, stable named observations.

    Support nonzero means local branch consumed, not server acknowledgement.
    Only source-observed helper outcomes are supplied by the caller.
    Retarget is an intent and does not substitute a new current-target value.
    """
    if job not in ('mage', 'kurian', 'warrior', 'priest', 'rogue') or not isinstance(snapshot, AlternateSnapshot) or not isinstance(state, AlternateState):
        raise ValueError('supported job and typed snapshot/state required')
    if state.last_ms > snapshot.now_ms or state.minor_last_ms > snapshot.now_ms:
        raise ValueError('state timestamp in future')
    replies = {} if replies is None else replies
    if not isinstance(replies, Mapping) or any(not isinstance(v, HelperReply) for v in replies.values()):
        raise ValueError('typed helper replies required')
    s, st, calls, lock = snapshot, state, [], snapshot.locked_561f7e
    bound_consumers=[]

    def need(value, name):
        if value is None:
            raise _Missing(name)
        return value

    def finish(reason='', status='complete'):
        return AlternateDecision(status, tuple(calls), st, reason,tuple(bound_consumers))

    def finish_support(interval, reason):
        nonlocal st
        st = replace(st, last_ms=s.now_ms, interval_ms=interval)
        return finish(reason)

    def emit(address):
        nonlocal lock
        calls.append(address)
        reply = replies.get(address)
        if reply is None:
            raise _Missing('helper:' + address)
        if reply.chat_consumer is not None:
            bound_consumers.append((address,reply.chat_consumer))
            outcome,missing=checked_chat_reply(address,s.class_context_dword,reply,True)
            if missing is not None:raise _Missing(missing)
            lock=reply.locked_after
            return outcome
        lock = reply.locked_after
        return need(reply.returned_nonzero, 'return:' + address)

    def retarget():
        # Both heads keep executing after this call.
        if need(s.current_target_462630, 'current_target') != need(s.target_id_562040, 'target_id'):
            if need(s.target_mode_561f64, 'target_mode') not in (1, 5):
                calls.append('0046493c')

    def due():
        return s.now_ms - st.last_ms >= st.interval_ms

    def raw_gate(final=False):
        byte = s.priest_final_raw_byte_55402c if final else s.raw_byte_55402c
        value = s.priest_final_raw_float_554030 if final else s.raw_float_554030
        return need(byte, 'final_raw_byte' if final else 'raw_byte') == 0 and need(
            value, 'final_raw_float' if final else 'raw_float') <= 0

    def target_eligible():
        return need(s.target_id_562040, 'target_id') != 0 and need(s.target_raw_byte_554034, 'target_byte') not in (4, 5)

    def attack_gate():
        return (need(s.attack_enabled_561f6c, 'attack_enabled') and not need(lock, 'post_support_lock')
                and not need(s.guard_fe384, 'route_guard_A') and not need(s.guard_46fe90, 'route_guard_B'))

    try:
        if need(lock, 'DAT_00561f7e'):
            return finish('locked')

        if job == 'priest':
            # Heal precedes byte/float gates, and support precedes the final path.
            if need(s.actor_state_554034, 'actor_state') != 6 and due():
                if emit('004cf8b8'):
                    return finish_support(650, 'support_consumed')
                if not raw_gate():
                    return finish('raw_gate')
                for helper in ('004d0c18', '004cfc74', '004cee18', '004d20b0'):
                    if emit(helper):
                        return finish_support(650, 'support_consumed')
                if target_eligible():
                    if need(s.target_ready_56204c, 'target_ready'):
                        retarget()
                    if emit('004d0434'):
                        return finish_support(650, 'target_support_consumed')
            # This path has its own fresh raw reads and ignores attack/route flags.
            if not raw_gate(final=True) or not target_eligible():
                return finish('final_raw_or_target_gate')
            if need(s.target_ready_56204c, 'target_ready'):
                retarget()
            if (need(s.target_max_hp_positive, 'target_max_hp') and need(s.target_hp_positive, 'target_hp')
                    and s.now_ms - st.last_ms >= 1500):
                calls.append('004d2aa8')
            return finish()

        if job == 'rogue':
            if need(s.actor_state_554034, 'actor_state') != 6:
                if (need(s.rogue_flag_0, 'Rogue+0')
                        and s.now_ms - st.minor_last_ms >= s.rogue_minor_interval_ms):
                    if need(s.rogue_minor_actor_state_554034, 'minor_actor_state') != 6 and emit('004da25c'):
                        st = replace(st, minor_last_ms=s.now_ms)
                if not raw_gate():
                    return finish('raw_gate')
                skip_support_tail = False
                if need(s.attack_enabled_561f6c, 'attack_enabled'):
                    if not due():
                        skip_support_tail = True  # Source goto skips004da784 as well.
                    else:
                        for helper in ('004da2d4', '004da568'):
                            if emit(helper):
                                return finish_support(500, 'support_consumed')
                            st = replace(st, interval_ms=100)
                if not skip_support_tail:
                    if emit('004da784'):
                        return finish_support(500, 'support_consumed')
                    st = replace(st, interval_ms=100)
            if not attack_gate() or not target_eligible():
                return finish('attack_or_target_gate')
            if need(s.target_ready_56204c, 'target_ready'):
                retarget()
            if due():
                if need(s.rogue_raw_463fc4, 'FUN_00463fc4') == 1:
                    calls.append('004db864')
                    return finish('rogue_path_1')
                if need(s.rogue_attack_actor_state_554034, 'attack_actor_state') != 6:
                    if emit('004dd2e0'):
                        return finish_support(500, 'attack_consumed')
                calls.append('004dc0a0')
            return finish()

        if not raw_gate():
            return finish('raw_gate')
        # Both assemblies TEST AH,45 / JZ: finite zero passes in both.
        if need(s.actor_state_554034, 'actor_state') != 6 and due():
            if job == 'mage':
                for helper in ('00499b88', '00499620', '004994bc'):
                    if emit(helper):
                        st = replace(st, last_ms=s.now_ms, interval_ms=650)
                        return finish('support_consumed')
            elif job == 'kurian':
                if emit('00471c38'):
                    st = replace(st, last_ms=s.now_ms, interval_ms=500)
                    return finish('support_consumed')
                # Source changes interval to100, preserving last timestamp.
                st = replace(st, interval_ms=100)
                if need(s.target_id_562040, 'target_id') != 0:
                    if need(s.target_raw_byte_554034, 'target_byte') not in (4, 5):
                        if need(s.target_ready_56204c, 'target_ready'):
                            retarget()
                        if emit('00472b90'):
                            st = replace(st, last_ms=s.now_ms, interval_ms=650)
                            return finish('target_support_consumed')
            else:  # Warrior00501dbc support head.
                if emit('0050269c'):
                    return finish_support(500, 'support_consumed')
                st = replace(st, interval_ms=100)
        if not need(s.attack_enabled_561f6c, 'attack_enabled') or need(lock, 'post_support_lock'):
            return finish('attack_gate')
        if need(s.guard_fe384, 'route_guard_A') or need(s.guard_46fe90, 'route_guard_B'):
            return finish('route_gate')
        if job == 'warrior' and need(s.warrior_flag_198, 'Warrior+198'):
            calls.append('0050306c')
            return finish('warrior_special')
        if need(s.target_id_562040, 'target_id') == 0:
            return finish('no_target')
        ready = need(s.target_ready_56204c, 'target_ready')
        if job == 'mage' and not ready:
            return finish('target_not_ready')
        if ready:
            retarget()
        if due():
            calls.append({'mage': '0049b318', 'kurian': '0047225c', 'warrior': '00502c4c'}[job])
        return finish()
    except _Missing as error:
        return finish(str(error), 'needs_observation')
