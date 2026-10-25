"""004dd2e0 post-selection pure replay; raw helper returns never imply server ACK.

Read observations are keyed by source step, not invented live addresses. Calls and
writes below are a source trace/plan only; no IO, memory access or helper execution.
"""
from dataclasses import dataclass
from typing import Mapping, Optional, Tuple
from rogue_attack import RogueDecision

@dataclass(frozen=True)
class SpecialObservation:
    alternate_561f88: bool
    values: Mapping[str, Optional[int]]
    def __post_init__(self):
        if type(self.alternate_561f88) is not bool or not isinstance(self.values,Mapping):raise ValueError('mode bool and observation mapping required')
        for value in self.values.values():
            if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):raise ValueError('observation must be DWORD or unknown')

@dataclass(frozen=True)
class SpecialExecutionPlan:
    status: str
    trace: Tuple[Tuple[str,Tuple[object,...]],...] = ()
    local_writes: Tuple[Tuple[str,int],...] = ()
    source_return: Optional[int] = None
    reason: str = ''

class _Missing(Exception):pass

def plan_rogue_special_execution(decision,observations):
    """One continuation after selection, with explicit independent rereads.

    Keys: normal.caller_20_dword, normal.helper_20_byte,
    preparation.3c_dword, preparation.target_462630,
    preparation.lookup_464a10, preparation.context_553e80,
    normal.context_553e80, alternate.prefix_46256c,
    alternate.lookup_464990, alternate.context_5540a0,
    alternate.target_562040, alternate.return_553ee4,
    normal.target_pointer_56203c, clock.lock, clock.after_send.
    Every key is required only when the source reaches that step. Indirect
    trace first argument records ECX context, then logical stack arguments.
    Lookup results are explicit observations, not executable transport.
    """
    if not isinstance(decision,RogueDecision) or not isinstance(observations,SpecialObservation):raise ValueError('decision and observations required')
    if decision.status!='selected_requires_helpers' or decision.row is None:
        return SpecialExecutionPlan('not_selected',reason=decision.status)
    skill=decision.row.skill_number
    if skill not in (0x262,0x276,0x28a,0x290):raise ValueError('unsupported special selection')
    alt=observations.alternate_561f88
    duration=(2100 if skill!=0x290 else 1800) if alt else (1600 if skill!=0x290 else 1300)
    if decision.lock_interval_ms!=duration:raise ValueError('mode differs from selection')
    trace=[];writes=[]
    def read(key):
        value=observations.values.get(key)
        if value is None:raise _Missing(key)
        return value
    def call(helper,*args):trace.append((helper,tuple(args)))
    try:
        if not alt:
            gate=read('normal.caller_20_dword');call('0045dc44:caller_root_plus_554020',gate)
            if gate:
                call('00464714')
                byte=read('normal.helper_20_byte')
                if byte>255:raise ValueError('helper_20_byte must be byte')
                call('0045dbdc:helper_root_plus_554020',byte)
                if byte:
                    call('00465f30',0)
                    context=read('normal.context_553e80')
                    call('indirect:00553f50',context,0,1)
        # TEST EAX,EAX clears CF, then JC cannot branch. Do not invent a
        # nonzero-target condition to skip the following preparation.
        call('00462630:initial')
        gate=read('preparation.3c_dword');call('0045dc44:root_plus_55403c',gate)
        if gate:
            target=read('preparation.target_462630');call('00462630:repeat',target)
            call('00465ef8',target,0)
            lookup=read('preparation.lookup_464a10');call('00464a10',target,lookup)
            if lookup:
                context=read('preparation.context_553e80')
                call('indirect:00553ef0',context,0,lookup)
        if alt:
            target=read('alternate.target_562040');call('004655e8',skill,target)
            prefix=read('alternate.prefix_46256c');call('0046256c',prefix)
            argument=(prefix*1000+skill)&0xffffffff
            lookup=read('alternate.lookup_464990');call('00464990',argument,lookup)
            context=read('alternate.context_5540a0')
            call('indirect:00553ee4',context,target,lookup)
            result=read('alternate.return_553ee4')
            if not result:return SpecialExecutionPlan('local_return_zero',tuple(trace),tuple(writes),0)
        writes.append(('00561f80',duration))
        lock_clock=read('clock.lock')
        writes.extend((('00561f84',lock_clock),('00561f7e',1)))
        if not alt:
            pointer=read('normal.target_pointer_56203c')
            call('004dfd7c','source_object',skill,pointer)
            post_clock=read('clock.after_send')
            offsets={0x262:0x54,0x276:0x60,0x28a:0x6c}
            if skill in offsets:writes.append(('object:+%x'%offsets[skill],(post_clock+duration)&0xffffffff))
        return SpecialExecutionPlan('local_return_one',tuple(trace),tuple(writes),1)
    except _Missing as e:
        return SpecialExecutionPlan('needs_observation',tuple(trace),tuple(writes),reason=str(e))
