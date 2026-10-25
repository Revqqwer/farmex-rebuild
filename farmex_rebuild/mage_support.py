"""Richard Mage support and TP scheduling, pure local plans without game IO.

Helper replies are observations, not guessed success. Static addresses identify
source fields/physical timer slots; they are not verified runtime addresses.
"""
import math
import struct
from dataclasses import dataclass
from typing import Mapping, Optional, Tuple


def _i(v,name,lo=0,hi=0xffffffff,optional=False):
    if v is None and optional:return
    if type(v)is not int or not lo<=v<=hi:raise ValueError(name)


def _b(v):
    if v is not None and type(v)is not bool:raise ValueError('boolean or unknown required')


def _f(v):
    if v is None:return
    if type(v)not in (int,float) or not math.isfinite(v) or abs(v)>3.4028234663852886e38:raise ValueError('finite float32 required')


def f32(v):return struct.unpack('<f',struct.pack('<f',v))[0]
def elapsed(now,last):return (now-last)&0xffffffff
def signed32(v):return ((v+0x80000000)&0xffffffff)-0x80000000
def trunc_div(a,b):return (abs(a)//abs(b))*(-1 if (a<0)!=(b<0) else 1)


class _Unknown(Exception):pass
def need(value,name):
    if value is None:raise _Unknown(name)
    return value


@dataclass(frozen=True)
class MageSupportCall:
    helper:str
    skill_number:Optional[int]=None
    target_id:Optional[int]=None
    index:Optional[int]=None


@dataclass(frozen=True)
class MageBuffRow:
    flag:int
    skill:int
    mp_min:int
    stat_reader:str
    stat_min:int
    cast_ms:int
    buffs:Tuple[int,...]
    gate_64490:bool=False
    string_queries:int=0


MAGE_BUFF_ROWS=(
    MageBuffRow(0x1d7,802,240,'00462e60',2,0,(802,),string_queries=2),
    MageBuffRow(0x1d9,826,0,'00462e60',23,1200,(),True),
    MageBuffRow(0x1d8,815,150,'00462e60',12,2000,(815,),True),
    MageBuffRow(0x1d1,654,120,'00462e08',54,2000,(654,630,612)),
    MageBuffRow(0x1cf,630,80,'00462e08',30,2000,(654,630,612)),
    MageBuffRow(0x1cd,612,40,'00462e08',12,2000,(654,630,612)),
    MageBuffRow(0x1d6,773,250,'00462e34',75,2000,(773,),True,1),
    MageBuffRow(0x1d5,748,80,'00462e34',48,2000,(748,)),
    MageBuffRow(0x1d4,724,50,'00462e34',24,2000,(724,)),
    MageBuffRow(0x1d3,706,15,'00462e34',6,2000,(706,)),
    MageBuffRow(0x1d2,673,250,'00462e08',75,2000,(673,),True,1),
    MageBuffRow(0x1d0,648,80,'00462e08',48,2000,(648,)),
    MageBuffRow(0x1ce,624,50,'00462e08',24,2000,(624,)),
    MageBuffRow(0x1cc,606,15,'00462e08',6,2000,(606,)),
    MageBuffRow(0x1cb,573,250,'00462ddc',75,2000,(573,),True,1),
    MageBuffRow(0x1ca,548,80,'00462ddc',48,2000,(548,)),
    MageBuffRow(0x1c9,524,50,'00462ddc',24,2000,(524,)),
    MageBuffRow(0x1c8,506,15,'00462ddc',6,2000,(506,)),
)


@dataclass(frozen=True)
class MageBuffSnapshot:
    now_ms:int
    flags:Mapping[int,Optional[bool]]
    raw_stats:Mapping[str,Optional[int]]
    mp:Optional[int]
    locked:Optional[bool]=None
    fast_mode:Optional[bool]=None #00561f88
    helper_replies:Optional[Mapping[Tuple[int,str,int],Optional[bool]]]=None
    metric_460548:Optional[float]=None
    timer_553e08:Optional[int]=None #signed64 pair
    raw_field_554020_nonzero:Optional[bool]=None
    raw_field_55403c_nonzero:Optional[bool]=None
    helper_655e8_nonzero:Optional[bool]=None
    def __post_init__(self):
        _i(self.now_ms,'clock');_i(self.mp,'MP',-0x80000000,0x7fffffff,True)
        _i(self.timer_553e08,'signed64 timer',-(1<<63),(1<<63)-1,True);_f(self.metric_460548)
        for v in (self.locked,self.fast_mode,self.raw_field_554020_nonzero,self.raw_field_55403c_nonzero,self.helper_655e8_nonzero):_b(v)
        for m in (self.flags,self.raw_stats):
            if not isinstance(m,Mapping):raise ValueError('mapping required')
        for v in self.flags.values():_b(v)
        for v in self.raw_stats.values():_i(v,'stat',-0x80000000,0x7fffffff,True)
        if self.helper_replies is not None:
            if not isinstance(self.helper_replies,Mapping):raise ValueError('reply mapping required')
            for v in self.helper_replies.values():_b(v)


@dataclass(frozen=True)
class MageSupportDecision:
    status:str
    calls:Tuple[MageSupportCall,...]=()
    skill_number:Optional[int]=None
    target_id:Optional[int]=None
    local_timer_updates:Tuple[Tuple[int,int],...]=()
    local_lock_ms:Optional[int]=None
    local_lock_started_ms:Optional[int]=None
    clear_pending:bool=False
    reason:str=''


def select_mage_buff(s:MageBuffSnapshot)->MageSupportDecision:
    if not isinstance(s,MageBuffSnapshot):raise ValueError('MageBuffSnapshot required')
    calls=[];updates=[];selected=None
    def result(status,reason='',lock=None):
        return MageSupportDecision(status,tuple(calls),selected.skill if selected else None,
                                   local_timer_updates=tuple(updates),local_lock_ms=lock,
                                   local_lock_started_ms=s.now_ms if lock is not None else None,reason=reason)
    try:
        if need(s.locked,'DAT_00561f7e'):return result('locked')
        for r in MAGE_BUFF_ROWS:
            if not need(s.flags.get(r.flag),'flag:+%x'%r.flag):continue
            if need(s.mp,'MP')<r.mp_min:continue
            if need(s.raw_stats.get(r.stat_reader),'stat:'+r.stat_reader)<r.stat_min:continue
            if r.flag==0x1d9:
                metric=need(s.metric_460548,'metric:00460548')
                integer=math.trunc(metric)
                if not -0x80000000<=integer<=0x7fffffff:return result('needs_observation','metric outside supported signed32 FTOL result')
                if integer>=51:continue
            blocked=False
            for skill in r.buffs:
                calls.append(MageSupportCall('00464268',skill))
                if need((s.helper_replies or {}).get((r.flag,'00464268',skill)),'helper:00464268:+%x:%d'%(r.flag,skill)):
                    blocked=True;break
            if blocked:continue
            if r.gate_64490:
                calls.append(MageSupportCall('00464490',r.skill))
                if need((s.helper_replies or {}).get((r.flag,'00464490',r.skill)),'helper:00464490:+%x'%r.flag):continue
            for ordinal in range(r.string_queries):
                calls.append(MageSupportCall('00463950',index=ordinal))
                if not need((s.helper_replies or {}).get((r.flag,'00463950',ordinal)),'helper:00463950:+%x:%d'%(r.flag,ordinal)):
                    blocked=True;break
            if blocked:continue
            if r.flag==0x1d7:
                if need(s.fast_mode,'DAT_00561f88'):
                    calls.append(MageSupportCall('00464490',802))
                    if need((s.helper_replies or {}).get((r.flag,'00464490',802)),'helper:00464490:+1d7'):continue
                else:
                    delta=s.now_ms-need(s.timer_553e08,'timer:00553e08/0c')
                    delta=((delta+(1<<63))&((1<<64)-1))-(1<<63)
                    if delta<60000:continue
                    updates.append((0x553e08,s.now_ms))
            selected=r;break
        if selected is None:return result('no_eligible_skill')
        fast=need(s.fast_mode,'DAT_00561f88')
        if not fast and need(s.raw_field_554020_nonzero,'raw:+DAT_00554020'):
            calls.append(MageSupportCall('00464714'))
        if need(s.raw_field_55403c_nonzero,'raw:+DAT_0055403c'):
            calls.append(MageSupportCall('00465ef8'))
        if fast:
            calls.append(MageSupportCall('004655e8',selected.skill))
            if not need(s.helper_655e8_nonzero,'return:004655e8'):return result('local_return_zero')
            return result('local_return_nonzero',lock=selected.cast_ms)
        if selected.skill==802:
            calls.append(MageSupportCall('0049e82c',802))
            return result('local_helper_plan')
        calls.append(MageSupportCall('0049e630',selected.skill))
        return result('local_helper_plan',lock=selected.cast_ms)
    except _Unknown as e:return result('needs_observation',str(e))


@dataclass(frozen=True)
class MagePartyMember:
    index:int #source one-based
    actor_id:int
    hp:int
    hp_max:int
    name:Optional[str]=None
    lookup_64a10_zero:Optional[bool]=None
    distance:Optional[float]=None
    def __post_init__(self):
        _i(self.index,'one-based member',1,8);_i(self.actor_id,'WORD id',0,65535)
        _i(self.hp,'HP',-0x80000000,0x7fffffff);_i(self.hp_max,'max HP',-0x80000000,0x7fffffff)
        if self.name is not None and not isinstance(self.name,str):raise ValueError('name must be str or unknown')
        _b(self.lookup_64a10_zero);_f(self.distance)


@dataclass(frozen=True)
class MageTPSnapshot:
    now_ms:int
    members:Tuple[MagePartyMember,...]
    party_count:Optional[int]
    level_462670:Optional[int]
    mp:Optional[int]
    timer_slots:Mapping[int,Optional[int]]
    locked:Optional[bool]=None
    fast_mode:Optional[bool]=None
    low_hp_enabled:Optional[bool]=None
    threshold:Optional[int]=None
    named_enabled:Optional[bool]=None
    target_name:Optional[str]=None
    self_id:Optional[int]=None
    raw_field_554020_nonzero:Optional[bool]=None
    raw_field_55403c_nonzero:Optional[bool]=None
    helper_655e8_nonzero:Optional[bool]=None
    pending:Optional[bool]=None
    pending_mode:Optional[int]=None
    pending_target_id:Optional[int]=None
    def __post_init__(self):
        _i(self.now_ms,'clock');_i(self.party_count,'party count',0,8,True)
        for v in (self.level_462670,self.mp,self.threshold,self.pending_mode):_i(v,'signed DWORD',-0x80000000,0x7fffffff,True)
        for v in (self.locked,self.fast_mode,self.low_hp_enabled,self.named_enabled,self.raw_field_554020_nonzero,self.raw_field_55403c_nonzero,self.helper_655e8_nonzero,self.pending):_b(v)
        _i(self.self_id,'self ID',0,65535,True);_i(self.pending_target_id,'pending ID',optional=True)
        if self.target_name is not None and not isinstance(self.target_name,str):raise ValueError('target name must be str or unknown')
        if type(self.members)is not tuple or any(not isinstance(m,MagePartyMember)for m in self.members):raise ValueError('member tuple required')
        if len({m.index for m in self.members})!=len(self.members):raise ValueError('duplicate member indices')
        if not isinstance(self.timer_slots,Mapping):raise ValueError('timer mapping required')
        for key,val in self.timer_slots.items():_i(key,'timer address');_i(val,'timer DWORD',optional=True)


def _party(s):
    count=need(s.party_count,'party count')
    mapping={m.index:m for m in s.members}
    if any(i not in mapping for i in range(1,count+1)):raise _Unknown('complete ordered party slots')
    return tuple(mapping[i]for i in range(1,count+1))


def _tp_after(s,member,timer_write=None,pending=False):
    calls=[]
    def result(status,reason='',lock=None):
        updates=((timer_write,s.now_ms),)if timer_write is not None and lock is not None else ()
        return MageSupportDecision(status,tuple(calls),4,member.actor_id,updates,lock,
                                   s.now_ms if lock is not None else None,
                                   pending and lock is not None,reason)
    try:
        if need(s.raw_field_554020_nonzero,'raw:+DAT_00554020'):calls.append(MageSupportCall('00464714'))
        if need(s.raw_field_55403c_nonzero,'raw:+DAT_0055403c'):calls.append(MageSupportCall('00465ef8'))
        calls.append(MageSupportCall('00464650',index=member.index-1))
        if need(s.fast_mode,'DAT_00561f88'):
            calls.append(MageSupportCall('004655e8',4,member.actor_id))
            if not need(s.helper_655e8_nonzero,'return:004655e8'):return result('local_return_zero')
            return result('local_return_nonzero',lock=2000)
        calls.append(MageSupportCall('0049e8c8',4,member.actor_id))
        return result('local_helper_plan',lock=1500)
    except _Unknown as e:return result('needs_observation',str(e))


def select_mage_tp(s:MageTPSnapshot)->MageSupportDecision:
    if not isinstance(s,MageTPSnapshot):raise ValueError('MageTPSnapshot required')
    try:
        if need(s.locked,'DAT_00561f7e'):return MageSupportDecision('locked')
        low=need(s.low_hp_enabled,'flag:+3')
        if not low and not need(s.named_enabled,'flag:+8'):return MageSupportDecision('disabled')
        if need(s.party_count,'party count')<2 or need(s.level_462670,'stat:00462670')<10 or need(s.mp,'MP')<5:return MageSupportDecision('entry_gate')
        members=_party(s)
        selected=None
        if low:
            threshold=need(s.threshold,'parameter:+4')
            if not 0<threshold<100:return MageSupportDecision('threshold_gate')
            lowest=50000
            for member in members:
                if member.actor_id==need(s.self_id,'self ID'):continue
                address=0x56972c+member.index*4
                if elapsed(s.now_ms,need(s.timer_slots.get(address),'timer:%08x'%address))<2500:continue
                limit=trunc_div(signed32(member.hp_max*threshold),100)
                if member.hp<=0 or member.hp>limit:continue
                zero=need(member.lookup_64a10_zero,'helper:00464a10:member%d'%member.index)
                if not zero and f32(need(member.distance,'distance:member%d'%member.index))<=20:continue
                if member.hp<=lowest:selected=member;lowest=member.hp
            if selected is None:return MageSupportDecision('no_eligible_member')
            return _tp_after(s,selected,0x56972c+selected.index*4)
        name=need(s.target_name,'target name')
        if not name:return MageSupportDecision('empty_name')
        # Delphi UStrEqual compares exact UTF-16, without case folding.
        key=name.encode('utf-16-le',errors='surrogatepass')
        for member in members:
            value=need(member.name,'name:member%d'%member.index)
            if value.encode('utf-16-le',errors='surrogatepass')==key:selected=member;break
        if selected is None:return MageSupportDecision('name_not_found')
        zero_index=selected.index-1
        read_address=0x569730+zero_index*4
        if elapsed(s.now_ms,need(s.timer_slots.get(read_address),'timer:%08x'%read_address))<3001:return MageSupportDecision('wait_named_timer')
        if not need(selected.lookup_64a10_zero,'helper:00464a10:member%d'%selected.index) and f32(need(selected.distance,'distance:member%d'%selected.index))<=20:return MageSupportDecision('named_distance_gate')
        fast=need(s.fast_mode,'DAT_00561f88')
        write_address=(0x569730 if fast else 0x56972c)+zero_index*4
        return _tp_after(s,selected,write_address)
    except _Unknown as e:return MageSupportDecision('needs_observation',reason=str(e))


def replay_pending_mage_tp(s:MageTPSnapshot)->MageSupportDecision:
    if not isinstance(s,MageTPSnapshot):raise ValueError('MageTPSnapshot required')
    try:
        if not need(s.pending,'DAT_005693a0'):return MageSupportDecision('no_pending')
        if need(s.locked,'DAT_00561f7e'):return MageSupportDecision('locked')
        if need(s.pending_mode,'DAT_005693a4')!=1:return MageSupportDecision('pending_mode_gate')
        if need(s.level_462670,'stat:00462670')<10 or need(s.mp,'MP')<5 or need(s.party_count,'party count')<2:return MageSupportDecision('entry_gate')
        target=need(s.pending_target_id,'DAT_005693a8')
        member=next((m for m in _party(s)if m.actor_id==target),None)
        if member is None:return MageSupportDecision('pending_not_in_party')
        return _tp_after(s,member,pending=True)
    except _Unknown as e:return MageSupportDecision('needs_observation',reason=str(e))
