"""004e764c scalar panel projection and004ed384 weight branch only.

Own strict decimal signed64 parsing preserves lowDWORD; full Delphi parser,
fallback/exception policy, list builders and runtime gates are unimplemented.
Route combo Text must be observed separately from stored ItemIndex.
"""
import re
from dataclasses import dataclass
from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional

ROOT='frmMain/MainTab/'
SUPPLY=ROOT+'SheetTedarik/'
GROUP=SUPPLY+'grptedarik/'
TRIGGERS=GROUP+'GroupBox2/'
RESPAWN=ROOT+'SheetKontrol/GroupBox28/'
FLAG_PATHS={
 SUPPLY+'GroupBox17/chTedarikBankadanAl':0x54c,SUPPLY+'GroupBox17/chTedarikVipAl':0x54d,
 SUPPLY+'GroupBox31/chotohammer':0x54e,SUPPLY+'GroupBox31/chmhz\u00c4\u00b1rh':0x554,
 SUPPLY+'GroupBox31/chweaponchange':0x555,SUPPLY+'GroupBox25/chvipstorageat':0x556,
 SUPPLY+'GroupBox25/chMSBag':0x557,SUPPLY+'GroupBox25/chMStoEXP':0x558,
 TRIGGERS+'chrprgit':0x559,TRIGGERS+'chnomh':0x55a,TRIGGERS+'chinvfull':0x55b,
 TRIGGERS+'chTedarikWeight':0x55c,TRIGGERS+'chitemal':0x564,TRIGGERS+'chSupplyTownAlarm':0x565,
 GROUP+'chtedarikchat':0x566,GROUP+'chtedarikpm':0x567,
 ROOT+'SheetBot/grpSlotSetting/chlastkordmerkez':0x574,GROUP+'chinslotchat':0x576,
 GROUP+'chChangeSupplyRoute':0x588,RESPAWN+'chChangeReturnRoute':0x589,
 RESPAWN+'chAutoRespawn':0x58a,RESPAWN+'chSpawnAfterReturn':0x58b,RESPAWN+'chDeadAlarm':0x590}
NUMBER_PATHS={TRIGGERS+'txtTedarikWeightLimit':0x560,RESPAWN+'txtAutoRespawnWait':0x58c}
TEXT_PATHS={GROUP+'txttedarikchat':0x568,GROUP+'txttedarikchat2':0x56c,
 GROUP+'txttedarikpm':0x570,GROUP+'txtinslotchat':0x578}
COMBO_TEXT_PATHS={GROUP+'cmbTedarikRoutes':0x580,RESPAWN+'cmbReturnRoutes':0x584}
HAMMER_PATH=SUPPLY+'GroupBox31/rdmagichammer'
SUPPLY_PANEL_INPUTS=tuple(FLAG_PATHS)+tuple(NUMBER_PATHS)+tuple(TEXT_PATHS)+(HAMMER_PATH,)
SUPPLY_SOURCE_CONTROLS=SUPPLY_PANEL_INPUTS+tuple(COMBO_TEXT_PATHS)

@dataclass(frozen=True)
class SupplyPanelConfiguration:
    fields:Mapping
    texts:Mapping
    missing:tuple=()
    status:str='compiled_scalars'
    independently_verified:bool=False

def compile_supply_panel(values,*,combo_texts=None):
    if not isinstance(values,Mapping) or (combo_texts is not None and not isinstance(combo_texts,Mapping)):
        raise ValueError('Panel values and explicit combo text mappings required')
    def boolean(path):
        value=values.get(path)
        if type(value) is not bool:raise ValueError('Missing/invalid supply checkbox: '+path)
        return value
    fields={offset:int(boolean(path)) for path,offset in FLAG_PATHS.items()}
    fields[0x550]=1 if boolean(HAMMER_PATH) else 2 # Source does not read genie radio.
    for path,offset in NUMBER_PATHS.items():
        value=values.get(path)
        if type(value) is not str or not re.fullmatch(r'[+-]?[0-9]+',value.strip()):
            raise ValueError('Decimal supply parameter required: '+path)
        parsed=int(value.strip())
        if not -(1<<63)<=parsed<(1<<63):raise ValueError('Signed64 supply parameter required: '+path)
        fields[offset]=parsed&0xffffffff
    texts={}
    for path,offset in TEXT_PATHS.items():
        value=values.get(path)
        if type(value) is not str:raise ValueError('Supply Unicode text required: '+path)
        texts[offset]=value
    missing=[]
    for path,offset in COMBO_TEXT_PATHS.items():
        text=None if combo_texts is None else combo_texts.get(path)
        if text is None:missing.append(path+': GetText')
        elif type(text) is not str:raise ValueError('Observed combo Text must be Unicode')
        else:texts[offset]=text
    return SupplyPanelConfiguration(MappingProxyType(fields),MappingProxyType(texts),tuple(missing),
        'needs_combo_text' if missing else 'compiled_scalars')

def _signed(value):
    if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw DWORD required')
    return value-(0x100000000 if value&0x80000000 else 0)

def weight_percent_dword(current,maximum):
    """00460624 signed IMUL lowDWORD then signed IDIV truncating toward zero."""
    numerator=_signed(current);denominator=_signed(maximum)
    if denominator<=0:return 0
    product=_signed((numerator*100)&0xffffffff)
    quotient=abs(product)//denominator
    return (-quotient if product<0 else quotient)&0xffffffff

@dataclass(frozen=True)
class SupplyWeightDecision:
    status:str
    due:Optional[bool]=None
    action:Optional[str]=None
    missing:str=''
    independently_verified:bool=False

def plan_supply_weight(configuration,percentage_dword=None,*,branch_reached=None):
    if not isinstance(configuration,SupplyPanelConfiguration):raise ValueError('Typed supply panel required')
    if branch_reached is not None and type(branch_reached) is not bool:raise ValueError('Explicit branch reachability required')
    if branch_reached is None:return SupplyWeightDecision('needs_branch_observation',missing='earlier004ed384 gates')
    if not branch_reached:return SupplyWeightDecision('weight_branch_not_reached',False)
    if not configuration.fields[0x55c]:return SupplyWeightDecision('weight_disabled',False)
    if percentage_dword is None:return SupplyWeightDecision('needs_weight_observation',missing='00461260 EAX')
    due=_signed(percentage_dword)>=_signed(configuration.fields[0x560])
    return SupplyWeightDecision('weight_due' if due else 'weight_below_threshold',due,
        ('town_alarm' if configuration.fields[0x565] else 'supply_route') if due else None)
