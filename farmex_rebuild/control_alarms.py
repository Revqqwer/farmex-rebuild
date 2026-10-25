"""Scoped00459496/00459519 alarm tail and004d8808 opcode23 activity writes.

No clock, game read, alarm or network IO. The caller supplies reached entry and
fresh final AnsiString bytes per source comparison; no codepage is guessed.
"""
from dataclasses import dataclass,field
from types import MappingProxyType
from control_guards import ControlGuardConfiguration

ROOT='frmMain/MainTab/SheetKontrol/GroupBox41/'
FLAG_PATHS={ROOT+'chNoLootedItemAlarm':0xee,ROOT+'chDevilItemAlarm':0xec}
CONTROL_ALARM_INPUTS=tuple(FLAG_PATHS)
DEVIL_LITERALS=((0x5213bb,b'Teeth of Devil'),(0x5213ca,b'Claw of Devil'),
 (0x5213d8,b'Vein of Devil'),(0x5213e6,b'Bone of Devil'),(0x5213f4,b'Horn of Devil'),
 (0x521402,b'Heart of Devil'),(0x521411,b'Skull of Devil'),(0x521420,b'Wings of Devil'))

def compile_control_alarms(values):
    fields={}
    for path,offset in FLAG_PATHS.items():
        value=values.get(path)
        if type(value) is not bool:raise ValueError('Control alarm checkbox required: '+path)
        fields[offset]=int(value)
    return ControlGuardConfiguration(fields)

@dataclass(frozen=True)
class LootActivityState:
    last_activity_qword:object=None
    def __post_init__(self):
        v=self.last_activity_qword
        if v is not None and (type(v) is not int or not 0<=v<1<<64):raise ValueError('Observed source activity QWORD required')

@dataclass(frozen=True)
class LootActivityPlan:
    status:str
    complete:bool
    calls:tuple=()
    global_writes:tuple=()
    missing:str=''
    native_execution_verified:bool=False

def plan_loot_activity(captured,dispatch_tick=None):
    if type(captured) is not bytes:raise ValueError('Immutable supplied dispatch bytes required')
    if dispatch_tick is not None and (type(dispatch_tick) is not int or not 0<=dispatch_tick<=0xffffffff):raise ValueError('Independent dispatch GetTickCount DWORD required')
    if not captured:return LootActivityPlan('needs_observation',False,missing='opcode byte0')
    if captured[0]!=0x23:return LootActivityPlan('other_opcode',True)
    calls=(('005074da',()),)
    if dispatch_tick is None:return LootActivityPlan('needs_observation',False,calls,missing='dispatch GetTickCount DWORD')
    return LootActivityPlan('activity_writes_planned',True,calls,((0x562284,dispatch_tick),(0x562288,0)))

def apply_loot_activity(state,plan):
    if not isinstance(state,LootActivityState) or not isinstance(plan,LootActivityPlan):raise ValueError('Typed activity state and plan required')
    if not plan.complete:raise ValueError('Complete local activity plan required')
    if plan.status=='activity_writes_planned':return LootActivityState(dict(plan.global_writes)[0x562284])
    return state

@dataclass(frozen=True)
class ControlAlarmObservation:
    now_tick:object=None
    name_samples:object=field(default_factory=dict)
    alarm_returns:object=field(default_factory=dict)
    def __post_init__(self):
        if self.now_tick is not None and (type(self.now_tick) is not int or not 0<=self.now_tick<=0xffffffff):raise ValueError('Observed GetTickCount DWORD required')
        for key,value in self.name_samples.items():
            if (type(key) is not tuple or len(key)!=2 or any(type(v) is not int for v in key)
                    or not 14<=key[0]<=41 or not 0<=key[1]<8 or (value is not None and type(value) is not bytes)):
                raise ValueError('Fresh (slot,comparison-index) AnsiString byte samples required')
        for key,value in self.alarm_returns.items():
            if key not in ('no_loot','devil_item') or (value is not None and type(value) is not bool):raise ValueError('Separate alarm normal-return samples required')
        object.__setattr__(self,'name_samples',MappingProxyType(dict(self.name_samples)))
        object.__setattr__(self,'alarm_returns',MappingProxyType(dict(self.alarm_returns)))

@dataclass(frozen=True)
class ControlAlarmPlan:
    status:str
    complete:bool
    calls:tuple=()
    alarm_requests:tuple=()
    visited:tuple=()
    matching_sample:object=None
    missing:str=''
    source_return_planned:bool=False
    native_execution_verified:bool=False

class _Missing(Exception):pass

def plan_control_alarm_tail(configuration,state,observation,*,entry_address):
    if not isinstance(configuration,ControlGuardConfiguration) or not isinstance(state,LootActivityState) or not isinstance(observation,ControlAlarmObservation):
        raise ValueError('Typed alarm config/state/observations required')
    if entry_address not in (0x459496,0x459519):raise ValueError('Observed/reached alarm-tail entry required')
    c=configuration.fields;o=observation;calls=[];alarms=[];visited=[];hit=None
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def flag(offset):
        value=need(c.get(offset),'field+%x'%offset)
        if type(value) is not int or not 0<=value<=255:raise ValueError('Raw alarm flag BYTE required')
        return value!=0
    def alarm(reason,literal):
        calls.append(('00404260',(0x569568,('literal',literal))))
        alarms.append(reason)
        if o.alarm_returns.get(reason) is not True:raise _Missing(reason+' 00404260 normal return')
    def result(status,complete=False,missing=''):
        return ControlAlarmPlan(status,complete,tuple(calls),tuple(alarms),tuple(visited),hit,missing,complete)
    try:
        if entry_address==0x459496 and flag(0xee):
            last=need(state.last_activity_qword,'source last-activity QWORD')
            if last!=0:
                calls.append(('005074da',()))
                now=need(o.now_tick,'alarm GetTickCount DWORD')
                elapsed=(now-last)&0xffffffffffffffff
                if elapsed&(1<<63):elapsed-=1<<64
                if elapsed>=600000:alarm('no_loot',0x5213b3)
        if flag(0xec):
            for slot in range(14,42):
                for index,(literal,expected) in enumerate(DEVIL_LITERALS):
                    calls.append(('00463670',(slot,)));visited.append((slot,index))
                    name=need(o.name_samples.get((slot,index)),'fresh name slot%d comparison%d'%(slot,index))
                    calls.append(('00505118',(('literal',literal),('captured_ansi',name))))
                    if name==expected:hit=(slot,index);break
                if hit is not None:break
            if hit is not None:alarm('devil_item',0x52142f)
        return result('alarm_tail_return_planned',True)
    except _Missing as exc:return result('needs_observation',missing=str(exc))
