"""004db198 local replay. No game IO; calls/writes are ordered plans only.

Finite distance is a supplied source float sample, not a reproduced x87 distance
calculation. Integer-to-float source rounding is outside this model. Separate raw
prefix observations preserve the source's conditional second 0046256c call.
"""
from dataclasses import dataclass, replace
from typing import Mapping, Optional, Tuple
from rogue_attack import RogueSnapshot, BOW_ROWS
from attack_configuration import RogueAlternateBowRanges

@dataclass(frozen=True)
class AlternateBowObservation:
    byte_562011: Optional[int] = None
    byte_562012: Optional[int] = None
    execute_byte: Optional[int] = None
    target_id: Optional[int] = None
    send_return: Optional[int] = None
    prefix_first: Optional[int] = None
    prefix_second: Optional[int] = None
    helper_returns: Mapping[int,Optional[int]] = None

    def __post_init__(self):
        for value in (self.byte_562011,self.byte_562012,self.execute_byte):
            if value is not None and (type(value) is not int or not 0<=value<=255):raise ValueError('BYTE or unknown required')
        values=(self.target_id,self.send_return,self.prefix_first,self.prefix_second)
        if self.helper_returns is not None:
            if not isinstance(self.helper_returns,Mapping):raise ValueError('helper mapping required')
            if any(type(k) is not int or not 0<=k<=0xffffffff for k in self.helper_returns):raise ValueError('DWORD skill keys required')
            values+=tuple(self.helper_returns.values())
        for value in values:
            if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):raise ValueError('DWORD or unknown required')

@dataclass(frozen=True)
class AlternateBowPlan:
    status: str
    skill_number: Optional[int] = None
    category: Optional[int] = None
    source_return: Optional[int] = None
    calls: Tuple[Tuple[str,Tuple[int,...]],...] = ()
    local_writes: Tuple[Tuple[str,int],...] = ()
    reason: str = ''
    independently_verified: bool = False

class _Unknown(Exception):pass

def plan_alternate_bow(snapshot,ranges,observation):
    if not isinstance(snapshot,RogueSnapshot) or not isinstance(ranges,RogueAlternateBowRanges) or not isinstance(observation,AlternateBowObservation):
        raise ValueError('Snapshot, alternate ranges and observations required')
    s=snapshot;o=observation;calls=[];writes=[];skill=None;category=None
    if s.mp is not None and s.mp>0xffffffff:raise ValueError('MP DWORD required')
    def need(value,key):
        if value is None:raise _Unknown(key)
        return value
    def result(status,returned=None,reason=''):
        return AlternateBowPlan(status,skill,category,returned,tuple(calls),tuple(writes),reason)
    def eligible(row):
        if not need(s.flags.get(row.flag_offset),'flag:+%x'%row.flag_offset):return False
        if row.stat_reader is not None and need(s.raw_stats.get(row.stat_reader),'stat:'+row.stat_reader)<row.stat_minimum:return False
        if row.mp_minimum is not None:
            mp=need(s.mp,'MP');mp=mp-0x100000000 if mp & 0x80000000 else mp
            if mp<row.mp_minimum:return False
        return True
    def available(number):
        calls.append(('00464490',(number,)))
        raw=need((o.helper_returns or {}).get(number),'00464490:%x'%number)
        return raw & 255 == 0
    try:
        distance=need(s.distance,'distance')
        limit=min(45,need(s.configured_range,'active_range'))
        if distance>limit:return result('out_of_range',0)
        first=need(o.byte_562011,'byte:00562011')
        combo=bool(first) or bool(need(o.byte_562012,'byte:00562012'))
        # Combo accepts equality and raises quintuple MP150 to200. The separate
        # triple/quintuple distances are strict in the non-combo branch.
        for flag,number,stat,mp,radius,kind in (
                (0x91,0x22b,55,200 if combo else 150,ranges.combo if combo else ranges.quintuple,1),
                (0x89,0x203,15,40,ranges.combo if combo else ranges.triple,2)):
            inside=distance<=radius if combo else distance<radius
            if not inside:continue
            from rogue_attack import RogueRow
            if eligible(RogueRow(flag,'00462ddc',stat,mp,None,None,number)) and available(number):
                skill=number;category=kind;break
        # Outer equality permits multi-arrow candidates but skips all ordinary
        # rows. No cooldown/timer check or internal lock gate occurs here.
        if skill is None and distance<limit:
            for index,original in enumerate(BOW_ROWS):
                row=replace(original,timer_offset=None,interval_ms=None)
                if not eligible(row):continue
                number=row.skill_number
                if row.flag_offset==0x85:
                    calls.append(('0046256c',()))
                    prefix=need(o.prefix_first,'prefix:first')
                    if prefix==102:number=8
                    else:
                        calls.append(('0046256c',()))
                        number=8 if need(o.prefix_second,'prefix:second')==202 else 7
                if (index<11 or row.flag_offset==0x85) and not available(number):continue
                skill=number;category=3;break
        if skill is None:return result('no_eligible_skill',0)
        if need(o.execute_byte,'execute_byte')==0:return result('selected',category)
        writes.append(('00561f7e',1))
        target=need(o.target_id,'target_id')
        calls.append(('004655e8',(skill,target)))
        returned=need(o.send_return,'004655e8:EAX')
        return result('local_send_returned',category if returned else 0)
    except _Unknown as exc:
        return result('needs_observation',reason=str(exc))
