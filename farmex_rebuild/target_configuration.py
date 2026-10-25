"""0040a39c target radio/flags and00409c58 checked caption bridge.

Raw pool selector derives from proven exclusive checkbox states unless overridden.
Modes2/3 have a resolver; modes1/4/5 have explicit helper/write plans.
"""
from dataclasses import dataclass
from typing import Optional
from combat_configuration import compile_bot_combat
from target_resolver import ResolverSettings

BASE='frmMain/MainTab/SheetBot/'
MODE_PATHS=tuple(BASE+'GroupBox5/'+n for n in ('rdmanuelsec','rdismegoresec','rdotosec','rdbaskansec','rdautoz'))
LIST_PATH=BASE+'GroupBox6/lwMobList'
FLAG_PATHS=tuple(BASE+'GroupBox7/'+n for n in ('chrunmob','chmerkezedon','chRunMobBoxWait'))
POOL_PATHS=tuple(BASE+'GroupBox5/'+n for n in ('chOnlyMobSelect','chOnlyPlayerSelect'))
TARGET_PANEL_INPUTS=MODE_PATHS+FLAG_PATHS+(LIST_PATH,)+POOL_PATHS

@dataclass(frozen=True)
class TargetConfiguration:
    status: str
    mode: Optional[int] = None
    settings: Optional[ResolverSettings] = None
    missing: str = ''

def compile_target_configuration(values,lists,*,raw_pool_selector=None,previous_mode=None,mode_byte_override=None):
    if raw_pool_selector is not None and (type(raw_pool_selector) is not int or not 0<=raw_pool_selector<=0xffffffff):raise ValueError('Raw pool selector required')
    if previous_mode is not None and (type(previous_mode) is not int or not 0<=previous_mode<=0xffffffff):raise ValueError('Previous raw source mode required')
    selected=[]
    for index,path in enumerate(MODE_PATHS,1):
        value=values.get(path)
        if type(value) is not bool:raise ValueError('Target radio boolean required: '+path)
        if value:selected.append(index)
    # Source checks radios in this order. No selected radio retains the old field.
    mode=selected[0] if selected else previous_mode
    if mode is None:return TargetConfiguration('needs_previous_mode',missing='source config+30')
    if mode in (1,4,5):return TargetConfiguration('helper_branch_mode',mode)
    if mode not in (2,3):return TargetConfiguration('unsupported_source_mode',mode)
    if raw_pool_selector is None:
        mob,player=(values.get(p) for p in POOL_PATHS)
        if type(mob) is not bool or type(player) is not bool:raise ValueError('Typed pool checkboxes required')
        if mob and player:return TargetConfiguration('needs_pool_event_order',mode,missing='both exclusive source boxes checked')
        raw_pool_selector=2 if mob else 1 if player else 0
    active=compile_bot_combat(values,mode_byte_override=mode_byte_override)
    flags=[]
    for path in FLAG_PATHS:
        value=values.get(path)
        if type(value) is not bool:raise ValueError('Target movement boolean required: '+path)
        flags.append(value)
    rows=lists.get(LIST_PATH)
    if not isinstance(rows,list):raise ValueError('Target caption list required')
    entries=[]
    for row in rows:
        if not isinstance(row,dict) or type(row.get('caption')) is not str or type(row.get('checked')) is not bool:
            raise ValueError('Typed target caption/checked row required')
        if row['checked'] and row['caption']!='':entries.append(row['caption'])
    settings=ResolverSettings(mode,raw_pool_selector,active.target_range,flags[0],flags[1],tuple(entries),
                              active.target_select_ms,flags[2])
    return TargetConfiguration('compiled',mode,settings)
