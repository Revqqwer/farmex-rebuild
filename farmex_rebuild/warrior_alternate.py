"""Richard alternate Warrior local replays; no target IO or server ACK.

Helper observations use (flag offset, address, logical skill argument).
The logical argument to00464268 represents prefix*1000+number; the raw
prefix and live call transport remain provider responsibilities.
"""
import math
import struct
from dataclasses import dataclass, replace
from typing import Mapping, Optional, Tuple


def _int(value, name, low=0, high=0xffffffff, optional=False):
    if value is None and optional: return
    if type(value) is not int or not low<=value<=high: raise ValueError(name)


def _bool(value):
    if value is not None and type(value) is not bool: raise ValueError('bool or unknown required')


def elapsed(now, last): return (now-last)&0xffffffff


@dataclass(frozen=True)
class AlternateCall:
    helper: str
    skill_number: Optional[int] = None
    target_reader: Optional[str] = None


@dataclass(frozen=True)
class SupportRow:
    flag: int
    skill: int
    mp_min: Optional[int]
    stat_reader: Optional[str]
    stat_min: Optional[int]
    buffs: Tuple[int, ...]
    gate_64490: bool = True
    attack_only: bool = False
    raw_nonzero_required: bool = False


SUPPORT_ROWS=(
    SupportRow(0x20,2,5,None,None,(2,),raw_nonzero_required=True),
    SupportRow(0x21,7,7,'00462670',4,(7,)),
    SupportRow(0x100,705,10,'00462e34',5,(705,710)),
    SupportRow(0x101,710,50,'00462e34',10,(710,705)),
    SupportRow(0x102,720,60,'00462e34',20,(720,)),
    SupportRow(0x103,730,105,'00462e34',30,(730,750,780)),
    SupportRow(0x104,731,None,'00462e34',30,(),attack_only=True),
    SupportRow(0x105,740,500,'00462e34',40,(),attack_only=True),
    SupportRow(0x106,750,210,'00462e34',50,(730,750,780)),
    SupportRow(0x107,755,150,'00462e34',55,(755,)),
    SupportRow(0x108,770,250,'00462e34',70,(770,)),
    SupportRow(0x109,780,200,'00462e34',80,(730,750,780)),
    SupportRow(0x10a,781,1000,'00462e34',83,(781,),gate_64490=False),
)


@dataclass(frozen=True)
class SupportSnapshot:
    now_ms: int
    flags: Mapping[int, Optional[bool]]
    raw_stats: Mapping[str, Optional[int]]
    mp: Optional[int]
    locked: Optional[bool] = None
    attack_enabled: Optional[bool] = None
    raw_field_554020_nonzero: Optional[bool] = None
    replies: Optional[Mapping[Tuple[int,str,int], Optional[bool]]] = None

    def __post_init__(self):
        _int(self.now_ms,'clock');_int(self.mp,'MP',-0x80000000,0x7fffffff,True)
        for value in (self.locked,self.attack_enabled,self.raw_field_554020_nonzero): _bool(value)
        for mapping in (self.flags,self.raw_stats):
            if not isinstance(mapping,Mapping):raise ValueError('mapping required')
        for value in self.flags.values():_bool(value)
        for value in self.raw_stats.values():_int(value,'stat',-0x80000000,0x7fffffff,True)
        if self.replies is not None:
            if not isinstance(self.replies,Mapping):raise ValueError('reply mapping required')
            for value in self.replies.values():_bool(value)


@dataclass(frozen=True)
class SupportDecision:
    status: str
    calls: Tuple[AlternateCall,...] = ()
    selected_flag: Optional[int] = None
    local_lock_ms: Optional[int] = None
    local_lock_started_ms: Optional[int] = None
    reason: str = ''


def select_warrior_support(s:SupportSnapshot)->SupportDecision:
    if not isinstance(s,SupportSnapshot):raise ValueError('SupportSnapshot required')
    calls=[]
    def missing(reason):return SupportDecision('needs_observation',tuple(calls),reason=reason)
    if s.locked is None:return missing('DAT_00561f7e')
    if s.locked:return SupportDecision('locked')
    for r in SUPPORT_ROWS:
        if r.attack_only:
            if s.attack_enabled is None:return missing('DAT_00561f6c')
            if not s.attack_enabled:continue
        enabled=s.flags.get(r.flag)
        if enabled is None:return missing('flag:+%x'%r.flag)
        if not enabled:continue
        if r.raw_nonzero_required:
            if s.raw_field_554020_nonzero is None:return missing('raw:+DAT_00554020')
            if not s.raw_field_554020_nonzero:continue
        # +21 level check precedes MP; other support rows use MP before stat.
        if r.flag==0x21:
            stat=s.raw_stats.get(r.stat_reader)
            if stat is None:return missing('stat:'+r.stat_reader)
            if stat<r.stat_min:continue
        if r.mp_min is not None:
            if s.mp is None:return missing('MP')
            if s.mp<r.mp_min:continue
        if r.stat_reader and r.flag!=0x21:
            stat=s.raw_stats.get(r.stat_reader)
            if stat is None:return missing('stat:'+r.stat_reader)
            if stat<r.stat_min:continue
        gates=([('00464490',r.skill)] if r.gate_64490 else [])+[('00464268',b) for b in r.buffs]
        blocked=False
        for helper,arg in gates:
            calls.append(AlternateCall(helper,arg))
            value=(s.replies or {}).get((r.flag,helper,arg))
            if value is None:return missing('helper:%s:%x:%d'%(helper,r.flag,arg))
            if value:blocked=True;break
        if blocked:continue
        calls.append(AlternateCall('004655e8',r.skill,'00462650'))
        reply=(s.replies or {}).get((r.flag,'004655e8',r.skill))
        if reply is None:return missing('return:004655e8:+%x'%r.flag)
        if reply:
            return SupportDecision('local_return_nonzero',tuple(calls),r.flag,
                                   1500 if r.flag==0x10a else None,
                                   s.now_ms if r.flag==0x10a else None)
    return SupportDecision('no_local_nonzero_return',tuple(calls))


@dataclass(frozen=True)
class ProvokeState:
    start_ms:int=0 #0057000c
    reset_ms:int=0 #00570010
    last_skill_ms:int=0 #00570014
    last_64b2c_ms:int=0 #00570008
    used:Tuple[bool,...]=(False,False,False,False) #18..1b
    def __post_init__(self):
        for name in ('start_ms','reset_ms','last_skill_ms','last_64b2c_ms'):_int(getattr(self,name),name)
        if type(self.used) is not tuple or len(self.used)!=4 or any(type(v)is not bool for v in self.used):raise ValueError('four used bools required')


@dataclass(frozen=True)
class ProvokeSnapshot:
    now_ms:int
    flags:Mapping[int,Optional[bool]]
    raw_stats:Mapping[str,Optional[int]]
    mp:Optional[int]
    window_seconds:int
    start_delay_seconds:int
    skill_delay_seconds:int
    caller_flag_198:Optional[bool]=None
    raw_field_554020:Optional[int]=None
    replies:Optional[Mapping[Tuple[int,str,int],Optional[bool]]]=None
    def __post_init__(self):
        SupportSnapshot(self.now_ms,self.flags,self.raw_stats,self.mp,replies=self.replies)
        _bool(self.caller_flag_198)
        _int(self.raw_field_554020,'raw field',optional=True)
        for n in ('window_seconds','start_delay_seconds','skill_delay_seconds'):_int(getattr(self,n),n,-0x80000000,0x7fffffff)


@dataclass(frozen=True)
class ProvokeDecision:
    status:str
    state:ProvokeState
    calls:Tuple[AlternateCall,...]=()
    selected_flag:Optional[int]=None
    reason:str=''


PROVOKE_ROWS=((0x19d,779,75,500,3),(0x19c,760,60,400,2),
              (0x19b,735,35,300,1),(0x19a,725,25,100,0))


def replay_warrior_provoke(s:ProvokeSnapshot, st:ProvokeState=ProvokeState())->ProvokeDecision:
    if not isinstance(s,ProvokeSnapshot) or not isinstance(st,ProvokeState):raise ValueError('invalid provoke input')
    calls=[]
    def result(status,reason='',flag=None):return ProvokeDecision(status,st,tuple(calls),flag,reason)
    def need(v,name):
        if v is None:raise _Unknown(name)
        return v
    try:
        if not need(s.caller_flag_198,'caller:+198'):return result('caller_disabled')
        if elapsed(s.now_ms,st.start_ms)>=(s.window_seconds*1000)&0xffffffff:
            if elapsed(s.now_ms,st.reset_ms)<300000:return result('wait_reset')
            if need(s.raw_stats.get('00462e08'),'stat:00462e08')<45:return result('reset_stat_gate')
            if need(s.mp,'MP')<60:return result('reset_MP_gate')
            st=replace(st,start_ms=s.now_ms,reset_ms=s.now_ms,used=(False,)*4)
            calls.append(AlternateCall('0050378c'))
            return result('local_reset_helper_plan')
        if elapsed(s.now_ms,st.reset_ms)<(s.start_delay_seconds*1000)&0xffffffff:return result('wait_start_delay')
        if need(s.raw_field_554020,'raw:+DAT_00554020')==6:return result('raw_state_gate')
        if elapsed(s.now_ms,st.last_skill_ms)<(s.skill_delay_seconds*1000)&0xffffffff:return result('wait_skill_delay')
        if elapsed(s.now_ms,st.last_64b2c_ms)>=500:
            calls.append(AlternateCall('00464b2c'))
            st=replace(st,last_64b2c_ms=s.now_ms)
        for flag,skill,stat_min,mp_min,index in PROVOKE_ROWS:
            if st.used[index]:continue
            if not need(s.flags.get(flag),'flag:+%x'%flag):continue
            if need(s.raw_stats.get('00462e34'),'stat:00462e34')<stat_min:continue
            if need(s.mp,'MP')<mp_min:continue
            calls.append(AlternateCall('00464490',skill))
            if need((s.replies or {}).get((flag,'00464490',skill)),'helper:00464490:+%x'%flag):continue
            calls.append(AlternateCall('004655e8',skill,'00462630'))
            if need((s.replies or {}).get((flag,'004655e8',skill)),'return:004655e8:+%x'%flag):
                used=list(st.used);used[index]=True
                st=replace(st,last_skill_ms=s.now_ms,used=tuple(used))
                return result('local_return_nonzero',flag=flag)
        return result('no_local_nonzero_return')
    except _Unknown as e:return result('needs_observation',str(e))


class _Unknown(Exception):pass


@dataclass(frozen=True)
class AlternateAttackState:
    phase:int=0
    initial_reply_byte:int=0
    initial_ms:int=0
    clear_ms:int=0
    repeat_ms:int=0
    second_repeat_ms:int=0
    counter:int=0
    def __post_init__(self):
        for n in ('phase','initial_ms','clear_ms','repeat_ms','second_repeat_ms','counter'):_int(getattr(self,n),n)
        _int(self.initial_reply_byte,'initial reply',0,255)


@dataclass(frozen=True)
class AlternateAttackSnapshot:
    now_ms:int
    distance:Optional[float]
    configured_range:Optional[int]
    locked:Optional[bool]=None
    flag_561fcc:Optional[bool]=None
    flag_562011:Optional[bool]=None
    flag_562012:Optional[bool]=None
    helper_501f3c_byte:Optional[int]=None
    def __post_init__(self):
        _int(self.now_ms,'clock');_int(self.configured_range,'range',-0x80000000,0x7fffffff,True)
        _int(self.helper_501f3c_byte,'helper byte',0,255,True)
        for v in (self.locked,self.flag_561fcc,self.flag_562011,self.flag_562012):_bool(v)
        if self.distance is not None and (type(self.distance)not in (int,float) or not math.isfinite(self.distance) or self.distance<0 or self.distance>3.4028234663852886e38):raise ValueError('finite float32 distance required')


@dataclass(frozen=True)
class AlternateAttackDecision:
    status:str
    state:AlternateAttackState
    calls:Tuple[AlternateCall,...]=()
    reason:str=''


def replay_warrior_alternate_attack(s:AlternateAttackSnapshot,st:AlternateAttackState=AlternateAttackState())->AlternateAttackDecision:
    if not isinstance(s,AlternateAttackSnapshot)or not isinstance(st,AlternateAttackState):raise ValueError('invalid alternate attack input')
    calls=[]
    def result(status,reason=''):return AlternateAttackDecision(status,st,tuple(calls),reason)
    def need(v,name):
        if v is None:raise _Unknown(name)
        return v
    def both_flags():return need(s.flag_562011,'DAT_00562011'),need(s.flag_562012,'DAT_00562012')
    def any_flags():return need(s.flag_562011,'DAT_00562011') or need(s.flag_562012,'DAT_00562012')
    def clear():calls.append(AlternateCall('00465ef8',target_reader='00462630'))
    def repeat():calls.append(AlternateCall('00465f30'))
    try:
        distance=struct.unpack('<f',struct.pack('<f',need(s.distance,'distance')))[0]
        # FUCOMPP/TEST AH,0x45/JNZ accepts equality; decompiler gate is wrong.
        if distance>min(10,need(s.configured_range,'range')):return result('out_of_range')
        if need(s.locked,'DAT_00561f7e'):
            st=replace(st,phase=0);return result('locked_reset')
        if st.phase==0:
            calls.append(AlternateCall('00501f3c'))
            reply=need(s.helper_501f3c_byte,'return-byte:00501f3c')
            st=replace(st,phase=1,initial_reply_byte=reply,initial_ms=s.now_ms)
        elif st.phase==1:
            if st.initial_reply_byte>=1 and elapsed(s.now_ms,st.initial_ms)<=49:return result('wait_50ms')
            if need(s.flag_561fcc,'DAT_00561fcc'):
                clear();st=replace(st,clear_ms=s.now_ms)
            st=replace(st,phase=2)
        elif st.phase==2:
            if not need(s.flag_561fcc,'DAT_00561fcc'):st=replace(st,phase=3)
            elif elapsed(s.now_ms,st.clear_ms)<200:return result('wait_200ms')
            else:
                if not any_flags():clear()
                st=replace(st,phase=3)
        elif st.phase==3:
            a=need(s.flag_562011,'DAT_00562011')
            b=need(s.flag_562012,'DAT_00562012')
            if a or b:
                if a and b:
                    counter=(st.counter+1)&0xffffffff
                    st=replace(st,counter=0 if counter==10 else counter)
                repeat();st=replace(st,phase=4,repeat_ms=s.now_ms)
            else:st=replace(st,phase=4)
        elif st.phase==4:
            if any_flags():
                if elapsed(s.now_ms,st.repeat_ms)<20:return result('wait_20ms')
                repeat();st=replace(st,second_repeat_ms=s.now_ms)
            st=replace(st,phase=5)
        elif st.phase==5:
            if any_flags():
                if elapsed(s.now_ms,st.second_repeat_ms)<20:return result('wait_second_20ms')
                if need(s.flag_561fcc,'DAT_00561fcc'):clear()
            st=replace(st,phase=6)
        elif st.phase==6:
            if elapsed(s.now_ms,st.initial_ms)<900:return result('wait_900ms')
            st=replace(st,phase=0)
        else:return result('unhandled_source_phase')
        return result('local_phase_advance')
    except _Unknown as e:return result('needs_observation',str(e))
