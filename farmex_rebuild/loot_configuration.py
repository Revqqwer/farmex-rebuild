"""0041a084 panel fields. Item-name/cache classification stays unresolved.

Decimal signed32 parsing is our policy; NPC price removes dots for strings of
length>=4, bounded signed64, then preserves the stored low DWORD. Original Delphi
conversion/exception/fallback behavior is not fully emulated. Source reads wait
text twice; a single stable local profile sample is used here.
"""
import re
from dataclasses import dataclass
from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional
from operation_engine import LootMode,LootSettings

ROOT='frmMain/MainTab/SheetItem/'
GENERAL=ROOT+'GroupBox10/'
FILTER=ROOT+'GroupBox26/'
MODE_PATHS=tuple(GENERAL+n for n in ('rdAllAutoLoot','rdOnlyCoinsLoot','rdItemListLoot'))
FLAG_PATHS={GENERAL+'chAutoLoot':0,GENERAL+'chLootBeforeWait':8,
    FILTER+'chLootNpcPrice':0x11,FILTER+'chLootUpgrade':0x18,FILTER+'chLootUpgradeBank':0x23,
    FILTER+'chLootUnique':0x20,FILTER+'chLootCountable':0x21}
NUMBER_PATHS={GENERAL+'txtLootBeforeWait':0xc,FILTER+'txtLootNpcPrice':0x14,
    FILTER+'txtLootUpgrade':0x1c,FILTER+'txtLootUpgradeBank':0x24}
LOOT_PANEL_INPUTS=tuple(FLAG_PATHS)+MODE_PATHS+tuple(NUMBER_PATHS)

@dataclass(frozen=True)
class LootPanelConfiguration:
    status:str
    settings:Optional[LootSettings]
    fields:Mapping
    reason:str=''

def compile_loot_panel(values,*,previous_mode=None):
    if not isinstance(values,Mapping):raise ValueError('Panel mapping required')
    if previous_mode is not None and not isinstance(previous_mode,LootMode):raise ValueError('Known prior LootMode required')
    def flag(path):
        value=values.get(path)
        if type(value) is not bool:raise ValueError('Missing/invalid loot checkbox: '+path)
        return value
    fields={offset:int(flag(path)) for path,offset in FLAG_PATHS.items()}
    mode=previous_mode
    # Separate source IFs: last checked radio wins; none retains prior field.
    for path,choice in zip(MODE_PATHS,LootMode):
        if flag(path):mode=choice
    for path,offset in NUMBER_PATHS.items():
        value=values.get(path)
        if not isinstance(value,str):raise ValueError('Loot integer text required: '+path)
        text=value.strip()
        if offset==0x14 and len(text)>=4:text=text.replace('.','')
        if not re.fullmatch(r'[+-]?[0-9]+',text):raise ValueError('Decimal loot integer required: '+path)
        number=int(text);bits=64 if offset==0x14 else 32
        if not -(1<<(bits-1))<=number<(1<<(bits-1)):raise ValueError('Loot integer outside local parsing policy')
        fields[offset]=number&0xffffffff
    if mode is None:
        return LootPanelConfiguration('needs_previous_mode',None,MappingProxyType(fields),'No source radio checked; prior field unknown')
    fields[4]=mode.value
    settings=LootSettings(bool(fields[0]),mode,bool(fields[8]),fields[0xc],
        extended_filters=mode==LootMode.LIST)
    return LootPanelConfiguration('needs_item_classifier' if mode==LootMode.LIST else 'compiled',
        settings,MappingProxyType(fields),
        'List row ordinals are not item IDs; source lookup/cache and filter consumer unresolved' if mode==LootMode.LIST else '')
