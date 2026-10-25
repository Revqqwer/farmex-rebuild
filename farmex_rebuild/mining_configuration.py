"""004762fc scalar fields; only explicit existing consumers are bridged.

Strict decimal signed64 -> lowDWORD is local parser policy, not full Delphi
fallback/locale emulation. Manual combo filename conversion stays an observation.
"""
import re
from dataclasses import dataclass
from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional
from mining_engine import MiningRunnerConfig

ROOT='frmMain/MainTab/SheetMaden/'
START=ROOT+'GroupBox51/'
ORE=ROOT+'GroupBox61/'
REPAIR=ROOT+'GroupBox62/'
START_MODES=tuple(START+name for name in ('rdMiningStartKord','rdMiningManuelKord','rdMiningManuelRoute'))
SPEED_MODES=tuple(ORE+name for name in ('rdUseSprint','rdUseSwift','rdUseLightFeet'))
FLAG_PATHS={START+'chChangeMiningRoute':0x6000,ORE+'chGoCrash':0x6028,
 ORE+'chGoCrashWait':0x6029,ORE+'chOreCrashWS':0x6034,ORE+'chPitmanFollow':0x6035,
 ORE+'chOreFullAlarm':0x6036,REPAIR+'chMiningGoRPR':0x6037,REPAIR+'chMiningUseMagicHammer':0x6038,
 REPAIR+'chMiningMHBotStop':0x6039,REPAIR+'chDontRPRWithSell':0x603a,REPAIR+'chMiningChangeMattock':0x603b,
 ORE+'chMiningAutoRespawn':0x603c,ORE+'chMiningAutoSell':0x6044,ORE+'chMiningAutoBank':0x6045,
 ORE+'chMattockExtract':0x6046,ORE+'chUseSpeedSkill':0x6047,ORE+'chMiningVipStorage':0x604c}
NUMBER_PATHS={ORE+'txtGoCrashWait':0x602c,ORE+'txtOreCrashSpeed':0x6030,ORE+'txtMiningAutoRespawn':0x6040}
MINING_PANEL_INPUTS=tuple(FLAG_PATHS)+tuple(NUMBER_PATHS)+START_MODES+SPEED_MODES

@dataclass(frozen=True)
class MiningPanelConfiguration:
    status:str
    fields:Mapping
    manual_route_ansi:Optional[bytes]=None
    missing:tuple=()
    independently_verified:bool=False

@dataclass(frozen=True)
class MiningNpcProjection:
    status:str
    globals:Mapping
    complete:bool
    missing:tuple=()
    independently_verified:bool=False

def compile_mining_npc_flags(values):
    """Compile only the two NPC-consumed flags; unrelated numeric edits do not gate NPC steps."""
    if not isinstance(values,Mapping):raise ValueError('Explicit panel values required')
    fields={};missing=[]
    for path,offset in FLAG_PATHS.items():
        if offset not in (0x603a,0x604c):continue
        value=values.get(path)
        if value is None:missing.append(path)
        elif type(value) is not bool:raise ValueError('Mining NPC checkbox required: '+path)
        else:fields[offset]=int(value)
    return MiningPanelConfiguration('needs_npc_flags' if missing else 'npc_flags_compiled',MappingProxyType(fields),missing=tuple(missing))

def project_mining_npc_globals(configuration,runtime_mode=None):
    """Profile->NPC-frame logical projection, not writes to game globals.

    Mode is an independent runtime DWORD. Do not infer2 from a mining profile.
    NPC phase3 skips repair only in mode2 with56fad2 nonzero; VIP56fae4 is
    consumed independently by phases5/8 in the recovered source.
    """
    if not isinstance(configuration,MiningPanelConfiguration):raise ValueError('Typed mining panel required')
    values={};missing=[]
    for offset,address in ((0x603a,0x56fad2),(0x604c,0x56fae4)):
        raw=configuration.fields.get(offset)
        if raw is None:missing.append('panel+%x'%offset);continue
        if type(raw) is not int or not 0<=raw<=255:raise ValueError('Raw mining BYTE required')
        values[address]=raw
    if runtime_mode is None:missing.append('runtime_mode_561f58')
    else:
        if type(runtime_mode) is not int or not 0<=runtime_mode<=0xffffffff:raise ValueError('Raw runtime mode DWORD required')
        values[0x561f58]=runtime_mode
    return MiningNpcProjection('needs_observation' if missing else 'local_npc_globals',MappingProxyType(values),not missing,tuple(missing))

def compile_mining_panel(values,*,previous_start_mode=None,previous_speed_mode=None,manual_route_ansi=None):
    if not isinstance(values,Mapping):raise ValueError('Explicit mining panel mapping required')
    fields={};missing=[]
    def flag(path):
        value=values.get(path)
        if type(value) is not bool:raise ValueError('Mining boolean required: '+path)
        return value
    for path,offset in FLAG_PATHS.items():fields[offset]=int(flag(path))
    for path,offset in NUMBER_PATHS.items():
        text=values.get(path)
        if type(text) is not str or not re.fullmatch(r'[+-]?[0-9]+',text.strip()):raise ValueError('Decimal mining parameter required: '+path)
        number=int(text.strip())
        if not -(1<<63)<=number<(1<<63):raise ValueError('Signed64 mining parameter required: '+path)
        fields[offset]=number&0xffffffff
    for paths,offset,previous in ((START_MODES,0x5ff8,previous_start_mode),(SPEED_MODES,0x6048,previous_speed_mode)):
        if previous is not None and (type(previous) is not int or not 0<=previous<=0xffffffff):raise ValueError('Observed previous mode DWORD required')
        selected=next((i for i,path in enumerate(paths,1) if flag(path)),previous)
        if selected is None:missing.append('previous field+%x'%offset)
        else:fields[offset]=selected
    if manual_route_ansi is not None and type(manual_route_ansi) is not bytes:raise ValueError('Observed manual route ANSI required')
    if manual_route_ansi is None:missing.append('004073a0 manual combo filename+5ffc')
    return MiningPanelConfiguration('needs_mining_observation' if missing else 'compiled_mining_fields',
        MappingProxyType(fields),manual_route_ansi,tuple(missing))

def mining_runner_configuration(configuration):
    if not isinstance(configuration,MiningPanelConfiguration):raise ValueError('Typed mining panel required')
    f=configuration.fields
    return MiningRunnerConfig(bool(f[0x6029]),f[0x602c],bool(f[0x6035]),bool(f[0x604c]))

@dataclass(frozen=True)
class MiningOreSettings:
    interval_seconds:int
    ws_enabled:bool

def mining_ore_settings(configuration):
    if not isinstance(configuration,MiningPanelConfiguration):raise ValueError('Typed mining panel required')
    return MiningOreSettings(configuration.fields[0x6030],bool(configuration.fields[0x6034]))
