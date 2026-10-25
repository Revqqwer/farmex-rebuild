"""Pure Richard Kurian attack selectors and 0047225c phase replay; no game IO."""
from dataclasses import dataclass,replace
from typing import Optional,Tuple
from rogue_attack import RogueSnapshot,_need,_Unknown

@dataclass(frozen=True)
class KurianAttackRow:
    flag_offset:int
    stat_reader:Optional[str]
    stat_minimum:Optional[int]
    mp_minimum:int
    skill_number:int
    checks_464490:bool=True

KURIAN_ATTACK_ROWS=(
    KurianAttackRow(0x3a,'00462ddc',75,500,0x23c),
    KurianAttackRow(0x39,'00462ddc',66,400,0x236),
    KurianAttackRow(0x38,'00462ddc',63,450,0x233),
    KurianAttackRow(0x37,'00462ddc',60,350,0x230),
    KurianAttackRow(0x36,'00462ddc',57,400,0x22d),
    KurianAttackRow(0x35,'00462ddc',54,350,0x22a),
    KurianAttackRow(0x34,'00462ddc',51,400,0x227),
    KurianAttackRow(0x33,'00462ddc',48,300,0x224),
    KurianAttackRow(0x31,'00462ddc',35,220,0x217),
    KurianAttackRow(0x30,'00462ddc',30,200,0x212),
    KurianAttackRow(0x2f,'00462ddc',25,150,0x20d),
    KurianAttackRow(0x2e,'00462ddc',20,120,0x208),
    KurianAttackRow(0x2d,'00462ddc',18,100,0x206),
    KurianAttackRow(0x2c,'00462ddc',15,90,0x203),
    KurianAttackRow(0x2b,'00462ddc',12,84,0x200),
    KurianAttackRow(0x2a,'00462ddc',6,20,0x1fa),
    KurianAttackRow(0x29,'00462ddc',3,30,0x1f7),
    KurianAttackRow(0x28,None,None,30,500),
    KurianAttackRow(3,'00462670',9,8,9),
    KurianAttackRow(2,'00462670',5,4,5),
    KurianAttackRow(1,'00462670',3,4,3),
    KurianAttackRow(0x32,'00462ddc',40,250,0x21c,False),
    KurianAttackRow(0,None,None,2,1,False),
)
KURIAN_SPECIAL_ROWS=(KurianAttackRow(0xda,'00462e34',50,1,0x2ee),KurianAttackRow(0xd9,'00462e34',20,120,0x2d0),KurianAttackRow(0xd8,'00462e34',7,120,0x2c1))

@dataclass(frozen=True)
class KurianCycleReplay:
    status:str
    cycle:object
    selector:object=None
    independently_verified:bool=False

def replay_kurian_cycle(cycle_snapshot,attack_snapshot,state=None):
    """Compose the source phase0 selector; other phases never call it.

    Cycle/selector snapshots are separate explicit samples. The selector's local
    return replaces caller-supplied AL; unknown helper results do not advance.
    This retains the existing phase model's single-clock approximation.
    """
    if not isinstance(cycle_snapshot,KurianCycleSnapshot):raise ValueError('Typed cycle snapshot required')
    state=KurianCycleState() if state is None else state
    probe=step_kurian_cycle(replace(cycle_snapshot,attack_return_al=None),state)
    if probe.status!='needs_observation' or probe.reason!='AL:0047267c':
        return KurianCycleReplay(probe.status,probe)
    selected=select_kurian_attack(attack_snapshot)
    if selected.source_return is None:
        pending=replace(probe,reason='selector:'+selected.reason)
        return KurianCycleReplay('needs_observation',pending,selected)
    result=step_kurian_cycle(replace(cycle_snapshot,attack_return_al=selected.source_return & 255),state)
    return KurianCycleReplay(result.status,result,selected)

@dataclass(frozen=True)
class KurianAttackDecision:
    status:str
    row:Optional[KurianAttackRow]=None
    calls:Tuple[Tuple[str,Tuple[object,...]],...]=()
    local_writes:Tuple[Tuple[str,int],...]=()
    source_return:Optional[int]=None
    reason:str=''

def select_kurian_attack(s):
    """0047267c 23 priority rows, configured min8; caller must supply send return."""
    return _select(s,False)

def select_kurian_special(s):
    """00472b90 three fixed32-range rows, preparation then conditional2000 lock."""
    return _select(s,True)

def _select(s,special):
    if not isinstance(s,RogueSnapshot):raise ValueError('RogueSnapshot required')
    calls=[];writes=[];selected=None
    try:
        if _need(s.locked_561f7e,'lock:00561f7e'):return KurianAttackDecision('locked',source_return=0)
        distance=_need(s.distance,'distance')
        limit=32 if special else min(8,_need(s.configured_range,'range'))
        if distance>limit:return KurianAttackDecision('out_of_range',source_return=0)
        for row in KURIAN_SPECIAL_ROWS if special else KURIAN_ATTACK_ROWS:
            if not _need(s.flags.get(row.flag_offset),'flag:+%x'%row.flag_offset):continue
            if row.stat_reader is not None and _need(s.raw_stats.get(row.stat_reader),'stat:'+row.stat_reader)<row.stat_minimum:continue
            if _need(s.mp,'MP')<row.mp_minimum:continue
            if row.checks_464490:
                calls.append(('00464490',(row.skill_number,)))
                if _need(s.helper_bools.get('00464490:%x'%row.skill_number),'00464490:%x'%row.skill_number):continue
            selected=row;break
        if selected is None:return KurianAttackDecision('no_eligible_skill',calls=tuple(calls),source_return=0)
        if special:
            calls.append(('00462630:initial',()))
            # TEST EAX,EAX thenJC clears carry: target0 does not skip gate.
            gate=_need(s.raw_stats.get('preparation.3c_dword'),'preparation.3c_dword')
            if gate:
                target=_need(s.raw_stats.get('preparation.target_462630'),'preparation.target_462630')
                calls.extend((('00462630:repeat',()),('00465ef8',(target,0))))
        calls.append(('004655e8',(selected.skill_number,'00562040')))
        result=_need(s.helper_bools.get('004655e8:%x'%selected.skill_number),'004655e8:%x'%selected.skill_number)
        if not result:return KurianAttackDecision('local_return_zero',selected,tuple(calls),(),0)
        if special:writes.extend((('00561f80',2000),('00561f84',s.now_ms),('00561f7e',1)))
        return KurianAttackDecision('local_return_one',selected,tuple(calls),tuple(writes),1)
    except _Unknown as e:return KurianAttackDecision('needs_observation',selected,tuple(calls),tuple(writes),reason=str(e))

@dataclass(frozen=True)
class KurianCycleState:
    phase:int=0
    attack_return_al:int=0
    start_ms:int=0
    target_change_ms:int=0
    mode_start_ms:int=0
    mode_stop_ms:int=0
    alternate_counter:int=0
    def __post_init__(self):
        for name in self.__dataclass_fields__:
            value=getattr(self,name)
            if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('DWORD state fields required')
        if self.attack_return_al>255:raise ValueError('AL byte required')

@dataclass(frozen=True)
class KurianCycleSnapshot:
    now_ms:int
    distance:Optional[float]=None
    configured_range:Optional[int]=None
    locked_561f7e:Optional[bool]=None
    enabled_561fcc:Optional[bool]=None
    mode_562011:Optional[bool]=None
    mode_562012:Optional[bool]=None
    attack_return_al:Optional[int]=None
    target_462630:Optional[int]=None
    def __post_init__(self):
        RogueSnapshot(self.now_ms,self.distance,self.configured_range,locked_561f7e=self.locked_561f7e)
        for value in (self.enabled_561fcc,self.mode_562011,self.mode_562012):
            if value is not None and type(value) is not bool:raise ValueError('bool/unknown required')
        for value in (self.attack_return_al,self.target_462630):
            if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):raise ValueError('DWORD/unknown required')
        if self.attack_return_al is not None and self.attack_return_al>255:raise ValueError('AL byte required')

@dataclass(frozen=True)
class KurianCycleDecision:
    status:str
    state:KurianCycleState
    calls:Tuple[Tuple[str,Tuple[object,...]],...]=()
    reason:str=''

def step_kurian_cycle(s,state=KurianCycleState()):
    """0047225c seven phases. Opaque helper return register is NOT a success.

    Caller-supplied AL result controls phase1delay; helper execution remains a
    trace only. Multiple source clocks use one sample. No target-mode name is
    guessed. Original SEH/FS restoration is compiler scaffolding, not game state.
    """
    if not isinstance(s,KurianCycleSnapshot) or not isinstance(state,KurianCycleState):raise ValueError('cycle snapshot/state required')
    calls=[];next_state=state
    def elapsed(last):return (s.now_ms-last)&0xffffffff
    def modes():return _need(s.mode_562011,'mode:00562011'),_need(s.mode_562012,'mode:00562012')
    def change(value):
        calls.append(('00462630',()))
        target=_need(s.target_462630,'raw:00462630')
        calls.append(('00465ef8',(target,value)))
    try:
        if _need(s.distance,'distance')>min(10,_need(s.configured_range,'range')):return KurianCycleDecision('out_of_range',state)
        if _need(s.locked_561f7e,'lock:00561f7e'):return KurianCycleDecision('locked_reset',replace(state,phase=0))
        phase=state.phase
        if phase==0:
            calls.append(('0047267c',()))
            result=_need(s.attack_return_al,'AL:0047267c')
            next_state=replace(state,phase=1,attack_return_al=result,start_ms=s.now_ms)
        elif phase==1:
            if state.attack_return_al>0 and elapsed(state.start_ms)<50:return KurianCycleDecision('waiting',state)
            if _need(s.enabled_561fcc,'flag:00561fcc'):
                change(1);next_state=replace(state,target_change_ms=s.now_ms)
            next_state=replace(next_state,phase=2)
        elif phase==2:
            enabled=_need(s.enabled_561fcc,'flag:00561fcc')
            if enabled:
                if elapsed(state.target_change_ms)<200:return KurianCycleDecision('waiting',state)
                a=_need(s.mode_562011,'mode:00562011')
                if not a and not _need(s.mode_562012,'mode:00562012'):change(0)
            next_state=replace(state,phase=3)
        elif phase==3:
            a,b=modes()
            if a or b:
                value=1 if a and not b else (2 if s.distance<1 else 1)
                if a and b:
                    counter=(state.alternate_counter+1)&0xffffffff
                    value=1 if not counter&1 else 2
                    next_state=replace(state,alternate_counter=0 if counter==10 else counter)
                calls.append(('00465f30',(value,)))
                next_state=replace(next_state,mode_start_ms=s.now_ms)
            next_state=replace(next_state,phase=4)
        elif phase==4:
            a=_need(s.mode_562011,'mode:00562011')
            if a or _need(s.mode_562012,'mode:00562012'):
                if elapsed(state.mode_start_ms)<20:return KurianCycleDecision('waiting',state)
                calls.append(('00465f30',(0,)));next_state=replace(state,mode_stop_ms=s.now_ms)
            next_state=replace(next_state,phase=5)
        elif phase==5:
            a=_need(s.mode_562011,'mode:00562011')
            if a or _need(s.mode_562012,'mode:00562012'):
                if elapsed(state.mode_stop_ms)<20:return KurianCycleDecision('waiting',state)
                if _need(s.enabled_561fcc,'flag:00561fcc'):change(0)
            next_state=replace(state,phase=6)
        elif phase==6:
            if elapsed(state.start_ms)<900:return KurianCycleDecision('waiting',state)
            next_state=replace(state,phase=0)
        else:return KurianCycleDecision('unhandled_source_phase',state)
        return KurianCycleDecision('advanced',next_state,tuple(calls))
    except _Unknown as e:return KurianCycleDecision('needs_observation',next_state,tuple(calls),str(e))
