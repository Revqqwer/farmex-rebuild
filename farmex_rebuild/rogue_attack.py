"""Pure Richard Rogue source replay; no game IO. Numbers are raw helper arguments.

All outputs are plans. Timer writes are source-local, never server acknowledgements.
A single caller clock sample replaces multiple source GetTickCount calls.
"""
import math
from dataclasses import dataclass, field
from typing import Mapping, Optional, Tuple

@dataclass(frozen=True)
class RogueSnapshot:
    now_ms: int
    distance: Optional[float] = None
    configured_range: Optional[int] = None
    mp: Optional[int] = None
    flags: Mapping[int, Optional[bool]] = field(default_factory=dict)
    raw_stats: Mapping[str, Optional[int]] = field(default_factory=dict)
    last_ms_by_offset: Mapping[int, Optional[int]] = field(default_factory=dict)
    locked_561f7e: Optional[bool] = None
    alternate_561f88: Optional[bool] = None
    timestamp_5620a4_5620a8: Optional[int] = None
    helper_bools: Mapping[str, Optional[bool]] = field(default_factory=dict)
    raw_skill_prefix_46256c: Optional[int] = None

    def __post_init__(self):
        if type(self.now_ms) is not int or not 0 <= self.now_ms <= 0xffffffff:
            raise ValueError('now_ms must be a DWORD')
        for value in (self.mp, self.raw_skill_prefix_46256c):
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError('raw integer must be nonnegative or unknown')
        if self.configured_range is not None and (type(self.configured_range) is not int or not -0x80000000 <= self.configured_range <= 0x7fffffff):
            raise ValueError('configured range must be signed DWORD or unknown')
        if self.distance is not None and (type(self.distance) not in (int,float) or not math.isfinite(self.distance) or self.distance < 0):
            raise ValueError('distance must be finite nonnegative or unknown')
        for mapping in (self.flags,self.raw_stats,self.last_ms_by_offset,self.helper_bools):
            if not isinstance(mapping, Mapping): raise ValueError('mappings required')
        for value in (self.locked_561f7e,self.alternate_561f88,*self.flags.values(),*self.helper_bools.values()):
            if value is not None and type(value) is not bool: raise ValueError('bool or unknown required')
        for value in self.raw_stats.values():
            if value is not None and (type(value) is not int or not -0x80000000 <= value <= 0x7fffffff): raise ValueError('signed raw stat required')
        for value in self.last_ms_by_offset.values():
            if value is not None and (type(value) is not int or not 0 <= value <= 0xffffffff): raise ValueError('DWORD timer required')
        t=self.timestamp_5620a4_5620a8
        if t is not None and (type(t) is not int or not 0 <= t <= 0xffffffffffffffff): raise ValueError('QWORD timestamp required')

@dataclass(frozen=True)
class RogueRow:
    flag_offset: int
    stat_reader: Optional[str]
    stat_minimum: Optional[int]
    mp_minimum: Optional[int]
    timer_offset: Optional[int]
    interval_ms: Optional[int]
    skill_number: Optional[int]
    helper: str = '004dfd7c'
    target_source: str = '0056203c'

@dataclass(frozen=True)
class RogueDecision:
    status: str
    row: Optional[RogueRow] = None
    local_timer_updates: Tuple[Tuple[int,int], ...] = ()
    reason: str = ''
    lock_interval_ms: Optional[int] = None
    pending_helpers: Tuple[str,...] = ()

class _Unknown(Exception): pass

def _need(value,name):
    if value is None: raise _Unknown(name)
    return value

def _elapsed(s,offset):
    return (s.now_ms-_need(s.last_ms_by_offset.get(offset),'timer:+%x'%offset)) & 0xffffffff

def _eligible(s,row,timer_first=False):
    if not _need(s.flags.get(row.flag_offset),'flag:+%x'%row.flag_offset): return False
    if timer_first and row.timer_offset is not None and _elapsed(s,row.timer_offset)<row.interval_ms: return False
    if row.stat_reader is not None and _need(s.raw_stats.get(row.stat_reader),'stat:'+row.stat_reader)<row.stat_minimum: return False
    if row.mp_minimum is not None and _need(s.mp,'MP')<row.mp_minimum: return False
    if not timer_first and row.timer_offset is not None and _elapsed(s,row.timer_offset)<row.interval_ms: return False
    return True

MELEE_ROWS = (
    RogueRow(0xdf,'00462e08',80,200,0x108,60100,0x2ad,target_source='read:00553e7c'),
    RogueRow(0x47,'00462e08',75,250,0x80,40100,0x2a8),
    RogueRow(0x46,'00462e08',72,200,0x7c,60100,0x2a3),
    RogueRow(0x45,'00462e08',70,100,0x78,5250,0x29e),
    RogueRow(0x43,'00462e08',55,100,0x70,11250,0x28f),
    RogueRow(0x40,'00462e08',35,50,0x64,10250,0x27b),
    RogueRow(0x3d,'00462e08',15,20,0x58,10250,0x267),
    RogueRow(0x41,'00462e08',40,50,0x68,5250,0x280),
    RogueRow(0x3e,'00462e08',20,20,0x5c,5250,0x26c),
    RogueRow(0x3b,'00462670',10,10,0x50,5250,0x258),
    RogueRow(0x3a,'00462670',7,5,0x4c,5250,7),
    RogueRow(0x39,'00462670',5,5,0x48,5250,5),
    RogueRow(0x38,None,None,2,None,None,None,'004c856c','raw:00462630'),
)

BOW_ROWS = (
    RogueRow(0x9a,'00462ddc',80,400,0xd0,61000,0x249),
    RogueRow(0x99,'00462ddc',75,300,0xcc,61000,0x244),
    RogueRow(0x96,'00462ddc',66,200,0xc0,7000,0x236),
    RogueRow(0x95,'00462ddc',62,200,0xbc,7000,0x232),
    RogueRow(0x92,'00462ddc',52,150,0xb8,61000,0x228),
    RogueRow(0x90,'00462ddc',50,50,0xb4,5200,0x226),
    RogueRow(0x8f,'00462ddc',45,50,0xb0,5200,0x221),
    RogueRow(0x8d,'00462ddc',35,30,0xac,5200,0x217),
    RogueRow(0x8c,'00462ddc',30,30,0xa8,5200,0x212),
    RogueRow(0x88,'00462ddc',10,10,0xa0,5200,0x1fe),
    RogueRow(0x87,'00462ddc',5,10,0x9c,5200,0x1f9),
    RogueRow(0x98,'00462ddc',72,200,None,None,0x23f),
    RogueRow(0x97,'00462ddc',70,350,None,None,0x23a),
    RogueRow(0x94,'00462ddc',60,300,None,None,0x230),
    RogueRow(0x93,'00462ddc',57,200,None,None,0x22d),
    RogueRow(0x8e,'00462ddc',40,100,None,None,0x21c),
    RogueRow(0x8b,'00462ddc',25,70,None,None,0x20d),
    RogueRow(0x8a,'00462ddc',20,40,None,None,0x208),
    RogueRow(0x86,'00462670',10,15,None,None,500),
    RogueRow(0x85,'00462670',9,7,None,None,7),
    RogueRow(0x84,'00462670',3,None,None,None,3),
)

def select_rogue_melee(s):
    """004dd780 has no internal lock gate. Source range includes equality."""
    if not isinstance(s,RogueSnapshot): raise ValueError('RogueSnapshot required')
    try:
        if _need(s.distance,'distance') > min(12,_need(s.configured_range,'range')):
            return RogueDecision('out_of_range')
        for row in MELEE_ROWS:
            if not _eligible(s,row,True): continue
            if row.flag_offset==0x3a:
                prefix=_need(s.raw_skill_prefix_46256c,'raw:0046256c')
                from dataclasses import replace
                row=replace(row,skill_number=7 if prefix in (0x66,0xca) else 6)
            updates=((0x20,s.now_ms),)
            if row.timer_offset is not None: updates+=((row.timer_offset,s.now_ms),)
            return RogueDecision('local_attempt',row,updates)
        return RogueDecision('no_eligible_skill')
    except _Unknown as e: return RogueDecision('needs_observation',reason=str(e))

def select_rogue_bow(s):
    """004ddce4 returns a raw skill-number, updating only its row timer."""
    if not isinstance(s,RogueSnapshot): raise ValueError('RogueSnapshot required')
    try:
        if _need(s.distance,'distance') > 50: return RogueDecision('out_of_range')
        for row in BOW_ROWS:
            if not _eligible(s,row): continue
            if row.flag_offset==0x85:
                prefix=_need(s.raw_skill_prefix_46256c,'raw:0046256c')
                from dataclasses import replace
                row=replace(row,skill_number=8 if prefix in (0x66,0xca) else 7)
            updates=() if row.timer_offset is None else ((row.timer_offset,s.now_ms),)
            return RogueDecision('selected',row,updates)
        return RogueDecision('no_eligible_skill')
    except _Unknown as e: return RogueDecision('needs_observation',reason=str(e))

SPECIAL_ROWS = (
    RogueRow(0x3f,'00462e08',30,30,0x60,11001,0x276),
    RogueRow(0x42,'00462e08',50,50,0x6c,61001,0x28a),
    RogueRow(0x3c,'00462e08',10,20,0x54,61001,0x262),
    RogueRow(0x44,'00462e08',63,350,0x74,10301,0x290),
)

def select_rogue_special(s):
    """004dd2e0 selection only. Preparation helpers and alternate send unresolved.

    Explicit helper_bools key '00464490:<hex-number>' is AL-nonzero; source
    requires FALSE. '00463924:160ddbd8' requires TRUE. No local lock/timer commit until
    opaque preparation and alternate 004655e8 return are independently supplied.
    """
    if not isinstance(s,RogueSnapshot): raise ValueError('RogueSnapshot required')
    try:
        if _need(s.locked_561f7e,'lock:00561f7e'): return RogueDecision('locked')
        d=_need(s.distance,'distance')
        if d>28: return RogueDecision('out_of_range')
        alt=_need(s.alternate_561f88,'mode:00561f88')
        r=min(12,_need(s.configured_range,'range'))
        for index,row in enumerate(SPECIAL_ROWS):
            if index<3 and d>r: continue
            if index in (1,2):
                # Source signed QWORD subtraction zero-extends current DWORD.
                timestamp=_need(s.timestamp_5620a4_5620a8,'timestamp:005620a4/a8')
                delta=(s.now_ms-timestamp)&0xffffffffffffffff
                if delta & (1<<63): delta-=1<<64
                if delta<=60000: continue
            # In this selector stat/MP precede per-row timer/helper.
            from dataclasses import replace
            untimed=replace(row,timer_offset=None,interval_ms=None)
            if not _eligible(s,untimed): continue
            if alt:
                if _need(s.helper_bools.get('00464490:%x'%row.skill_number),'00464490:%x'%row.skill_number): continue
            elif _elapsed(s,row.timer_offset)<row.interval_ms: continue
            if index==3 and not _need(s.helper_bools.get('00463924:160ddbd8'),'00463924:160ddbd8'): continue
            duration=(2100 if index<3 else 1800) if alt else (1600 if index<3 else 1300)
            return RogueDecision('selected_requires_helpers',row,reason='preparation helper observations required',lock_interval_ms=duration,
                pending_helpers=('00462630','0045dc44','00465ef8','004655e8') if alt else ('0045dc44','00464714','00462630','00465ef8','004dfd7c'))
        return RogueDecision('no_eligible_skill')
    except _Unknown as e: return RogueDecision('needs_observation',reason=str(e))


@dataclass(frozen=True)
class RogueVolleyDecision:
    status: str
    calls: Tuple[Tuple[str,Optional[int]],...] = ()
    local_timer_updates: Tuple[Tuple[int,int],...] = ()
    reason: str = ''

def plan_rogue_volley(s, interval_ms, range_10=None, range_14=None,
                      client_variant_553e46=None, flag_553e44=None,
                      raw_float_553f38=None):
    """004de224: bow, 004de710 and 004dedec may all run in one invocation.

    One snapshot approximates source re-reads by 004ddce4. Unknown dependencies
    stop further planning; already established bow timer plans remain visible,
    without applying them. No partially evaluated action is executed. The optional
    source speed writes remain explicit plan calls and never touch game memory.
    """
    if not isinstance(s,RogueSnapshot): raise ValueError('RogueSnapshot required')
    if type(interval_ms) is not int or not 0 <= interval_ms <= 0xffffffff: raise ValueError('DWORD interval required')
    for value in (range_10,range_14):
        if value is not None and (type(value) is not int or not -0x80000000<=value<=0x7fffffff): raise ValueError('signed range required')
    if flag_553e44 is not None and type(flag_553e44) is not bool: raise ValueError('flag bool required')
    if client_variant_553e46 is not None and (type(client_variant_553e46) is not int or not 0<=client_variant_553e46<=255): raise ValueError('variant byte required')
    if raw_float_553f38 is not None and (type(raw_float_553f38) not in (int,float) or not math.isfinite(raw_float_553f38)): raise ValueError('finite float required')
    updates=[]
    try:
        if _need(s.locked_561f7e,'lock:00561f7e'): return RogueVolleyDecision('locked')
        d=_need(s.distance,'distance')
        if d>min(50,_need(s.configured_range,'range')): return RogueVolleyDecision('out_of_range')
        calls=[]; updates=[]; bow=None
        if _elapsed(s,0x2c)>=interval_ms:
            bow=select_rogue_bow(s)
            if bow.status=='needs_observation': raise _Unknown('004ddce4:'+bow.reason)
            updates.extend(bow.local_timer_updates)
        eligible=[]
        for flag,timer,rng,stat,mp,helper in ((0x89,0x30,range_10,15,40,'004de710'),(0x91,0x34,range_14,55,150,'004dedec')):
            if d>_need(rng,'range:+%x'%(0x10 if flag==0x89 else 0x14)): continue
            if _elapsed(s,timer)<interval_ms: continue
            if not _need(s.flags.get(flag),'flag:+%x'%flag): continue
            if _need(s.raw_stats.get('00462ddc'),'stat:00462ddc')<stat: continue
            if _need(s.mp,'MP')<mp: continue
            eligible.append((timer,helper))
        if bow is not None and bow.status=='selected' or eligible:
            calls.append(('00464714',None))
        if bow is not None and bow.status=='selected':
            updates.append((0x2c,s.now_ms)); calls.append(('004df6f0',bow.row.skill_number))
        if eligible:
            variant=_need(client_variant_553e46,'byte:00553e46')
            if variant==2 and _need(flag_553e44,'flag:00553e44'):
                if _need(raw_float_553f38,'float:00553f38')>0.2:
                    calls.extend((('0045ddf4',None),('0045de78',None)))
        for timer,helper in eligible:
            updates.append((timer,s.now_ms)); calls.append((helper,None))
        return RogueVolleyDecision('local_attempt' if calls else 'no_eligible_skill',tuple(calls),tuple(updates))
    except _Unknown as e: return RogueVolleyDecision('needs_observation',local_timer_updates=tuple(updates),reason=str(e))
