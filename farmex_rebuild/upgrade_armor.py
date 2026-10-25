"""4f7210 Armor purchase buffer pair and 463a8c first-zero getter scan.

Standalone local plans; no queue insertion or native/game calls. Source's
uninitialized vendor local is never replaced with an invented default.
"""
from dataclasses import dataclass,field
from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional
from upgrade_packets import UpgradeItemObservation,plan_upgrade_item,_raw
from npc_buy_packets import BUY_VENDORS as VENDORS

TEMPLATE=bytes.fromhex('2101000000000000000001000000000000000000')
FOLLOWUP=bytes.fromhex('6a02')


@dataclass(frozen=True)
class ArmorFreeSlotObservation:
    items:Mapping=field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.items,Mapping) or any(type(k) is not int or not 14<=k<=41 for k in self.items):
            raise ValueError('Per-slot14..41 getter observations required')
        object.__setattr__(self,'items',MappingProxyType(dict(self.items)))


@dataclass(frozen=True)
class ArmorFreeSlotPlan:
    complete:bool
    result_word:Optional[int]=None
    visited_slots:tuple=()
    item_plans:tuple=()
    missing:str=''
    independently_verified:bool=False


def plan_armor_free_slot(observation):
    if not isinstance(observation,ArmorFreeSlotObservation):raise ValueError('Typed first-zero scan required')
    visited=[];plans=[]
    for slot in range(14,42):
        visited.append(slot);value=observation.items.get(slot)
        if isinstance(value,UpgradeItemObservation):
            plan=plan_upgrade_item(slot,value);plans.append((slot,plan))
            if not plan.complete:
                return ArmorFreeSlotPlan(False,visited_slots=tuple(visited),item_plans=tuple(plans),missing=plan.missing)
            value=plan.result_dword
        else:_raw(value)
        if value is None:
            return ArmorFreeSlotPlan(False,visited_slots=tuple(visited),item_plans=tuple(plans),missing='slot%d fresh004634a4 result'%slot)
        if value==0:return ArmorFreeSlotPlan(True,slot-14,tuple(visited),tuple(plans))
    return ArmorFreeSlotPlan(True,255,tuple(visited),tuple(plans))


@dataclass(frozen=True)
class ArmorPacketObservation:
    free_slot_word:Optional[int]=None
    free_scan:Optional[ArmorFreeSlotObservation]=None
    vendor_matches:Mapping=field(default_factory=dict)
    initial_vendor_dword:Optional[int]=None

    def __post_init__(self):
        if self.free_slot_word is not None and (type(self.free_slot_word) is not int or not 0<=self.free_slot_word<=0xffff):
            raise ValueError('Observed free-slot AX WORD required')
        if self.free_scan is not None and not isinstance(self.free_scan,ArmorFreeSlotObservation):
            raise ValueError('Typed free-slot scan required')
        _raw(self.initial_vendor_dword)
        if not isinstance(self.vendor_matches,Mapping):raise ValueError('Vendor comparison observations required')
        object.__setattr__(self,'vendor_matches',MappingProxyType(dict(self.vendor_matches)))


@dataclass(frozen=True)
class ArmorPacketPlan:
    complete:bool
    packets:tuple=()
    calls:tuple=()
    free_plan:Optional[ArmorFreeSlotPlan]=None
    vendor_dword:Optional[int]=None
    missing:str=''
    independently_verified:bool=False
    observed_free_word:Optional[int]=None
    observed_matches:tuple=()


def plan_armor_packet(npc_dword,quantity_dword,item_dword,selector_a_dword,selector_b_dword,observation):
    for value in (npc_dword,quantity_dword,item_dword,selector_a_dword,selector_b_dword):_raw(value)
    if not isinstance(observation,ArmorPacketObservation):raise ValueError('Typed Armor packet observations required')
    o=observation;calls=[];scan=None;vendor=o.initial_vendor_dword;free=None;matches=[]
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    try:
        amount=need(quantity_dword,'quantity stack parameter low WORD')&0xffff
        calls.append(('00463a8c',))
        if o.free_slot_word is not None and o.free_scan is not None:
            raise ValueError('Observed free-slot WORD and bound scan conflict')
        if o.free_scan is not None:
            scan=plan_armor_free_slot(o.free_scan)
            if not scan.complete:raise Missing(scan.missing)
            free=scan.result_word
        else:free=need(o.free_slot_word,'fresh00463a8c AX')
        for name,code in VENDORS:
            calls.append(('00505d20',name))
            match=need(o.vendor_matches.get(name),'fresh vendor comparison: '+name)
            if type(match) is not bool:raise ValueError('Normalized boolean vendor result required')
            matches.append((name,match))
            if match:vendor=code
        if vendor is None:raise Missing('uninitialized vendor local DWORD; no comparison matched')
        payload=bytearray(TEMPLATE)
        payload[2:6]=vendor.to_bytes(4,'little')
        payload[6:10]=need(npc_dword,'NPC DWORD').to_bytes(4,'little')
        payload[11:15]=need(item_dword,'item DWORD').to_bytes(4,'little')
        payload[15]=free&255
        payload[16:18]=amount.to_bytes(2,'little')
        payload[18]=need(selector_a_dword,'selector A low BYTE')&255
        payload[19]=need(selector_b_dword,'selector B low BYTE')&255
        calls.extend((('004c7710',0x561ef8,20,0),('004c911c',0x561ef8),('004c7710',0x561ef8,2,100)))
        return ArmorPacketPlan(True,((bytes(payload),0),(FOLLOWUP,100)),tuple(calls),scan,vendor,
                               observed_free_word=free,observed_matches=tuple(matches))
    except Missing as error:
        return ArmorPacketPlan(False,calls=tuple(calls),free_plan=scan,vendor_dword=vendor,missing=str(error),
                               observed_free_word=free,observed_matches=tuple(matches))
