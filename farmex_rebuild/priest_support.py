"""Richard Priest support branch replay. No IO, transport or server success.

Opaque helper checks are caller observations. Plans retain source-local writes,
and are never committed by this module. One DWORD clock models repeated samples.
"""
from dataclasses import dataclass, field
from typing import Mapping, Optional, Tuple


BUFF_AUTO=((78,690,0x2a3),(70,460,0x29e),(57,360,0x291),(54,300,0x28f),
           (42,240,0x282),(33,120,0x279),(24,60,0x270),(15,30,0x267),(6,15,0x25e))
AC_AUTO=((76,300,0x2a2),(60,1500,0x294),(51,100,0x28b),(39,80,0x27f),
         (30,80,0x276),(21,40,0x26d),(12,20,0x264),(3,10,0x25b))
MP_MIN={0x2a3:690,0x2a0:960,0x29e:460,0x291:360,0x290:570,0x28f:300,
        0x28e:240,0x282:240,0x279:120,0x270:60,0x267:30,0x25e:15,
        0x2a2:300,0x2a1:750,0x294:150,0x28b:100,0x27f:80,0x276:80,
        0x26d:40,0x264:20,0x25b:10,0x221:320,0x218:160,0x20f:80,
        0x206:40,0x1fd:20,500:10,5:10,2:5}


def automatic_skill(kind,stat,mp):
    if kind not in ('buff','ac') or type(stat) is not int or type(mp) is not int:
        raise ValueError('kind and raw integer observations required')
    # Highest stat branch wins even when its MP gate fails; no fallback.
    for minimum,cost,skill in BUFF_AUTO if kind=='buff' else AC_AUTO:
        if stat>=minimum:return skill if mp>=cost else 0
    return 0


def selected_skill_available(skill,mp):
    if type(skill) is not int or type(mp) is not int:raise ValueError('raw ints required')
    return skill in MP_MIN and mp>=MP_MIN[skill]


@dataclass(frozen=True)
class PriestPartyRaw:
    actor_id: int
    raw_dword_5695e4: int
    raw_word_5696ac: int
    raw_int_5695c0: int
    buff_last_ms: int
    ac_last_ms: int

    def __post_init__(self):
        for n in ('actor_id','raw_word_5696ac'):
            if type(getattr(self,n)) is not int or not 0<=getattr(self,n)<=0xffff:raise ValueError('WORD required')
        for n in ('raw_dword_5695e4','buff_last_ms','ac_last_ms'):
            if type(getattr(self,n)) is not int or not 0<=getattr(self,n)<=0xffffffff:raise ValueError('DWORD required')
        if type(self.raw_int_5695c0) is not int:raise ValueError('raw signed integer required')


@dataclass(frozen=True)
class PriestSupportSnapshot:
    now_ms: int
    flags: Mapping[int,Optional[bool]] = field(default_factory=dict)
    parameters: Mapping[int,Optional[int]] = field(default_factory=dict)
    stats: Mapping[str,Optional[int]] = field(default_factory=dict)
    timers: Mapping[str,Optional[int]] = field(default_factory=dict)
    checks: Mapping[str,Optional[bool]] = field(default_factory=dict)
    locked: Optional[bool] = None
    attack_enabled: Optional[bool] = None
    alternate: Optional[bool] = None
    self_id: Optional[int] = None
    raw_primary_pointer: Optional[int] = None
    party_count: Optional[int] = None
    party: Optional[Tuple[PriestPartyRaw,...]] = None
    queue_active: Optional[bool] = None
    queue_mode: Optional[int] = None
    queue_target: Optional[int] = None
    queue_party_index: Optional[int] = None
    queue_party_index_after: Optional[int] = None
    target_exists: Optional[bool] = None
    distance_truncated: Optional[int] = None

    def __post_init__(self):
        if type(self.now_ms) is not int or not 0<=self.now_ms<=0xffffffff:raise ValueError('DWORD clock required')
        for m in (self.flags,self.parameters,self.stats,self.timers,self.checks):
            if not isinstance(m,Mapping):raise ValueError('mapping required')
        for v in (*self.flags.values(),*self.checks.values(),self.locked,self.attack_enabled,self.alternate,self.queue_active,self.target_exists):
            if v is not None and type(v) is not bool:raise ValueError('bool or unknown required')
        for v in (*self.parameters.values(),*self.stats.values(),self.self_id,self.raw_primary_pointer,self.party_count,self.queue_mode,self.queue_target,self.queue_party_index,self.queue_party_index_after,self.distance_truncated):
            if v is not None and type(v) is not int:raise ValueError('integer or unknown required')
        for v in self.timers.values():
            if v is not None and (type(v) is not int or not 0<=v<=0xffffffff):raise ValueError('DWORD timer or unknown')
        if self.party is not None and (not isinstance(self.party,tuple) or any(not isinstance(v,PriestPartyRaw) for v in self.party)):raise ValueError('raw party tuple required')


@dataclass(frozen=True)
class PriestSupportAction:
    kind: str
    skill_number: int
    target_argument: int
    helper: str
    target_source: str = 'actor_id'


@dataclass(frozen=True)
class PriestSupportDecision:
    status: str
    actions: Tuple[PriestSupportAction,...] = ()
    timer_updates: Tuple[Tuple[str,int],...] = ()
    mirror_updates: Tuple[Tuple[int,int],...] = ()
    local_lock_ms: Optional[int] = None
    queue_clear: bool = False
    reason: str = ''


class _Unknown(Exception):pass
def _need(value,name):
    if value is None:raise _Unknown(name)
    return value
def _flag(s,o):return _need(s.flags.get(o),'flag:+%x'%o)
def _stat(s,n):return _need(s.stats.get(n),'stat:'+n)
def _check(s,n):return _need(s.checks.get(n),'helper:'+n)
def _elapsed(s,last):return (s.now_ms-last)&0xffffffff
def _timer(s,key):return _elapsed(s,_need(s.timers.get(key),'timer:'+key))
def _guard(s,route=None):
    if _need(s.locked,'00561f7e'):return 'locked'
    if route is not None and not _need(s.attack_enabled,'00561f6c') and _flag(s,route):return 'route_gate'
    return None
def _skill(s,offset,kind):
    chosen=_need(s.parameters.get(offset),'parameter:+%x'%offset)
    if chosen<1:return automatic_skill(kind,_stat(s,'00462e08'),_stat(s,'004611e0'))
    return chosen if selected_skill_available(chosen,_stat(s,'004611e0')) else 0
def _queue_skill(s,offset,kind):
    chosen=_need(s.parameters.get(offset),'parameter:+%x'%offset)
    return chosen if chosen>=1 else automatic_skill(kind,_stat(s,'00462e08'),_stat(s,'004611e0'))
def _attempt(s,action,timer=None,mirrors=(),queue_clear=False):
    alt=_need(s.alternate,'00561f88')
    if alt and not _check(s,'004655e8:'+action.kind+':'+str(action.target_argument)):
        return PriestSupportDecision('local_return_zero',(action,),reason='alternate helper returned0')
    updates=((timer,s.now_ms),) if timer else ()
    return PriestSupportDecision('local_attempt',(action,),updates,tuple(mirrors),2000 if alt else 1500,queue_clear)


def self_cure_disease(s):
    """004d0c18 disease first, then cure; no route gate in this source consumer."""
    attempted=[]
    try:
        guard=_guard(s)
        if guard:return PriestSupportDecision(guard)
        for flag,statmin,key,ready,skill,kind,helper in (
                (0xfa,35,'0056fb60','00464444',535,'self_disease','004d3690'),
                (0xf9,25,'0056fb5c','004643f8',525,'self_cure','004d3674')):
            if not _flag(s,flag) or _stat(s,'00462ddc')<statmin or _timer(s,key)<2000 or not _check(s,ready):continue
            alt=_need(s.alternate,'00561f88')
            if alt and _check(s,'00464490:'+kind):continue
            action=PriestSupportAction(kind,skill,_need(s.self_id,'00462650'),helper)
            result=_attempt(s,action,key)
            if result.status=='local_attempt':
                return PriestSupportDecision(result.status,tuple(attempted)+result.actions,result.timer_updates,local_lock_ms=result.local_lock_ms)
            attempted.extend(result.actions)
        return PriestSupportDecision('local_return_zero' if attempted else 'no_action',tuple(attempted))
    except _Unknown as e:return PriestSupportDecision('needs_observation',tuple(attempted),reason=str(e))


def buff_ac(s):
    """004cfc74 self buff/AC, then source-index party buff/AC, with mirror plans."""
    mirrors=[];attempted=[]
    try:
        guard=_guard(s,0x12e)
        if guard:return PriestSupportDecision(guard)
        self_id=_need(s.self_id,'00462650')
        if _flag(s,0xe8) or _flag(s,0xf0):
            buff,ac=_skill(s,0xec,'buff'),_skill(s,0xf4,'ac')
            for flag,skill,key,ready,kind in ((0xe8,buff,'0056fb54','004642d0','self_buff'),(0xf0,ac,'0056fb58','00464364','self_ac')):
                if not _flag(s,flag) or _timer(s,key)<3000 or skill==0 or not _check(s,ready):continue
                result=_attempt(s,PriestSupportAction(kind,skill,self_id,'004d3568'),key)
                if result.status=='local_attempt':
                    return PriestSupportDecision(result.status,tuple(attempted)+result.actions,result.timer_updates,result.mirror_updates,result.local_lock_ms)
                attempted.extend(result.actions)
        count=_need(s.party_count,'004645e4')
        if count>1 and (_flag(s,0xfb) or _flag(s,0x100)):
            buff,ac=_skill(s,0xfc,'buff'),_skill(s,0x104,'ac')
            if buff or ac:
                party=_need(s.party,'raw party arrays')
                if len(party)!=count:raise _Unknown('complete source-index party snapshot')
                for index,member in enumerate(party,1):
                    if member.actor_id==self_id:continue
                    if _flag(s,0xfb) and buff:
                        differs=member.raw_word_5696ac!=member.raw_dword_5695e4
                        elapsed=_elapsed(s,member.buff_last_ms)
                        if differs and member.raw_int_5695c0>0 and elapsed>=2500:
                            result=_attempt(s,PriestSupportAction('party_buff',buff,member.actor_id,'004d3568'),
                                            'party:%d:5696e4'%index,mirrors)
                            if result.status=='local_attempt':
                                return PriestSupportDecision(result.status,tuple(attempted)+result.actions,result.timer_updates,result.mirror_updates,result.local_lock_ms)
                            attempted.extend(result.actions)
                        # This source mutation occurs even if an alternate send returns0.
                        if elapsed<3000 and differs:mirrors.append((index,member.raw_dword_5695e4&0xffff))
                    if _flag(s,0x100) and ac and _elapsed(s,member.ac_last_ms)>603000:
                        result=_attempt(s,PriestSupportAction('party_ac',ac,member.actor_id,'004d3568'),
                                        'party:%d:569708'%index,mirrors)
                        if result.status=='local_attempt':
                            return PriestSupportDecision(result.status,tuple(attempted)+result.actions,result.timer_updates,result.mirror_updates,result.local_lock_ms)
                        attempted.extend(result.actions)
        return PriestSupportDecision('local_return_zero' if attempted else 'no_action',tuple(attempted),mirror_updates=tuple(mirrors))
    except _Unknown as e:return PriestSupportDecision('needs_observation',tuple(attempted),mirror_updates=tuple(mirrors),reason=str(e))


def queued_support(s):
    """004cee18 modes1..6; raw lookup/distance outputs explicitly observed."""
    try:
        if not _need(s.queue_active,'005693a0'):return PriestSupportDecision('no_action')
        if _need(s.locked,'00561f7e'):return PriestSupportDecision('locked')
        # Both auto lookups are called before the mode switch, even for cure.
        buff,ac=_queue_skill(s,0xfc,'buff'),_queue_skill(s,0x104,'ac')
        mode=_need(s.queue_mode,'005693a4')
        if mode not in range(1,7):return PriestSupportDecision('no_action')
        minimum={3:('00462e08',54),4:('00462670',4),5:('00462ddc',25),6:('00462ddc',35)}
        if mode in minimum:
            stat,threshold=minimum[mode]
            if _stat(s,stat)<threshold:return PriestSupportDecision('queue_cancel',queue_clear=True,reason='stat gate')
        if mode in (1,3):
            if _need(s.party_count,'004645e4')<2:return PriestSupportDecision('queue_cancel',queue_clear=True,reason='party gate')
            if _need(s.queue_party_index,'004cb898')<0:return PriestSupportDecision('queue_cancel',queue_clear=True,reason='party lookup')
        exists=_need(s.target_exists,'00464a10')
        if not exists and mode not in (1,3):return PriestSupportDecision('queue_cancel',queue_clear=True,reason='target lookup')
        if exists and _need(s.distance_truncated,'00460548 -> __ftol')>28:
            return PriestSupportDecision('queue_cancel',queue_clear=True,reason='distance gate')
        target=_need(s.queue_target,'005693a8/party resolver')
        skill={1:buff,2:ac,3:0x28e,4:4,5:525,6:535}[mode]
        kind='queued:%d'%mode
        result=_attempt(s,PriestSupportAction(kind,skill,target,'004d36ac' if mode==4 else '004d3568'),queue_clear=True)
        if result.status=='local_attempt':
            if _need(s.alternate,'00561f88') and mode in (2,4,5,6):
                index=_need(s.queue_party_index_after,'post-send004cb898')
                if index>=0:return PriestSupportDecision(result.status,result.actions,(('queue_party:%d:56970c'%index,s.now_ms),),local_lock_ms=result.local_lock_ms,queue_clear=True)
            return result
        return PriestSupportDecision('local_return_zero',result.actions,reason='alternate helper returned0; queue remains active')
    except _Unknown as e:return PriestSupportDecision('needs_observation',reason=str(e))


HEAL_SUPPORT_ROWS=((0xb4,80,1400,0x244),(0xb3,75,1200,0x23f),(0xb2,70,1000,0x23a),
                   (0xb1,48,625,0x224),(0xb0,39,375,0x21b),(0xaf,30,200,0x212),
                   (0xae,21,100,0x209),(0xad,12,30,0x200),(0xac,3,25,0x1f7))


def _none_effect(s,group,count):
    # Each invocation is distinct; preserve early true short-circuit.
    return all(not _check(s,'00464268:%s:%d'%(group,i)) for i in range(count))


def support_skills(s,alternate_consumer=False):
    """004d0eb0 normal /004d20b0 alternate support priority and multiple attempts.

    004d0eb0 does not consult global alternate mode, while004d20b0 is
    a separately selected consumer. Caller supplies post-lookup opaque checks.
    """
    actions,updates=[],[]
    try:
        guard=_guard(s,0x12f)
        if guard:return PriestSupportDecision(guard)
        # Source eagerly samples all four stats and MP before checking flags.
        stats={name:_stat(s,name) for name in ('00462ddc','00462e08','00462e34','00462670')}
        mp=_stat(s,'004611e0');chosen=0
        master=_flag(s,0x8e) or _flag(s,0x8d)
        if master and _none_effect(s,'master',2):
            if _flag(s,0x8e) and stats['00462670']>=20:
                selected=(0x8e,20,0x98)
            elif _flag(s,0x8d) and stats['00462670']>=10:
                selected=(0x8d,12,0x94)
            else:selected=None
            if selected:
                flag,skill,timer=selected
                eligible=not _check(s,'00464490:master:%x'%flag) if alternate_consumer else _timer(s,'+%x'%timer)>=5500
                if eligible and _check(s,'00463924:master:%x'%flag):
                    target=_need(s.self_id if alternate_consumer else s.raw_primary_pointer,'support master target argument')
                    actions.append(PriestSupportAction('support_master',skill,target,'004655e8' if alternate_consumer else '004d2ee8','actor_id' if alternate_consumer else 'raw_pointer:00553e7c'))
                    if not alternate_consumer:updates.append(('+%x'%timer,s.now_ms))
        resistance=any(_flag(s,f) for f in (0x8f,0x90,0x91,0x8c))
        if resistance and (alternate_consumer or _timer(s,'+a8')>=3000) and _none_effect(s,'resistance',4):
            selected=None
            for flag,reader,skill,timer in ((0x8f,'00462ddc',0x211,0x9c),(0x90,'00462e08',0x275,0xa0),(0x91,'00462e34',0x2d9,0xa4)):
                if _flag(s,flag) and stats[reader]>=30 and mp>=80:
                    selected=(flag,skill,timer);break
            if selected:
                flag,skill,timer=selected
                eligible=not _check(s,'00464490:resistance:%x'%flag) if alternate_consumer else _timer(s,'+%x'%timer)>=1000
                if eligible:
                    target=_need(s.self_id if alternate_consumer else s.raw_primary_pointer,'support resistance target argument')
                    actions.append(PriestSupportAction('support_resistance',skill,target,'004655e8' if alternate_consumer else '004d2ee8','actor_id' if alternate_consumer else 'raw_pointer:00553e7c'))
                    if not alternate_consumer:updates.append(('+%x'%timer,s.now_ms))
            elif _flag(s,0x8c) and stats['00462670']>=4 and mp>=10:
                chosen=4  # source goto bypasses following heal selection
        if chosen==0 and any(_flag(s,f) for f in range(0xac,0xb5)) and (alternate_consumer or _timer(s,'+bc')>=3000) and _none_effect(s,'heal',9):
            for flag,minimum,cost,skill in HEAL_SUPPORT_ROWS:
                if _flag(s,flag) and stats['00462ddc']>=minimum and mp>=cost:
                    if flag==0xb4:
                        eligible=not _check(s,'00464490:heal:b4') if alternate_consumer else _timer(s,'+b8')>=120000
                        if eligible:chosen=skill
                    else:chosen=skill
                    break  # highest enabled qualified branch cannot fall back on timer failure
        if chosen:
            target=_need(s.self_id,'00462650')
            kind='support_heal' if chosen!=4 else 'support_basic4'
            action=PriestSupportAction(kind,chosen,target,'004655e8' if alternate_consumer else ('004d36ac' if chosen==4 else '004d336c'))
            if alternate_consumer:
                if not _check(s,'004655e8:'+kind+':'+str(target)):
                    return PriestSupportDecision('local_return_zero',tuple(actions),tuple(updates),reason='alternate selected helper returned0')
                actions.append(action)
                return PriestSupportDecision('local_attempt',tuple(actions),tuple(updates),local_lock_ms=2000)
            actions.append(action)
            # 0x244 is in first group, so later +b8 update branch is unreachable.
            updates.append(('+a8' if chosen==4 else '+bc',(s.now_ms+1500)&0xffffffff))
            return PriestSupportDecision('local_attempt',tuple(actions),tuple(updates),local_lock_ms=1500)
        return PriestSupportDecision('local_return_zero' if actions else 'no_action',tuple(actions),tuple(updates))
    except _Unknown as e:return PriestSupportDecision('needs_observation',tuple(actions),tuple(updates),reason=str(e))
