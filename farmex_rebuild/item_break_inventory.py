"""Inventory-space loop, item-break guard and own caller composition.

Inventory slot getters, named-item lookup and managed string/notice effects
remain explicit captured normal-return boundaries. No process/game I/O.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from item_break_cycle import ItemBreakCycleFrame,ItemBreakCycleObservation,_raw,_receipts

@dataclass(frozen=True)
class InventorySpaceObservation:
    entry_reached:bool=False
    returned:object=field(default_factory=dict)
    pointers:object=field(default_factory=dict)
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit inventory scan entry required')
        returned=dict(self.returned);pointers=dict(self.pointers)
        for key,value in returned.items():
            if type(key) is not int or not 14<=key<=41 or type(value) is not bool:raise ValueError('Reached slot return required')
        for key,value in pointers.items():
            if type(key) is not int or not 14<=key<=41:raise ValueError('Inventory slot14..41 required')
            _raw(value,32)
            if value is None:raise ValueError('Explicit raw slot pointer required')
        object.__setattr__(self,'returned',MappingProxyType(returned))
        object.__setattr__(self,'pointers',MappingProxyType(pointers))

@dataclass(frozen=True)
class InventorySpacePlan:
    complete:bool
    calls:tuple=()
    needed:object=None
    empty_count:int=0
    result_eax:object=None
    native_execution_verified:bool=False

def _space_plan(o,threshold):
    calls=[];count=0
    if not o.entry_reached:return InventorySpacePlan(False,needed=('entry',None))
    signed_threshold=threshold if threshold<0x80000000 else threshold-(1<<32)
    for slot in range(14,42):
        calls.append(('004634a4',(slot,)))
        if o.returned.get(slot) is not True:return InventorySpacePlan(False,tuple(calls),('normal',slot),count)
        if slot not in o.pointers:return InventorySpacePlan(False,tuple(calls),('pointer',slot),count)
        eax=o.pointers[slot]
        if eax==0:count+=1
        if count>signed_threshold:return InventorySpacePlan(True,tuple(calls),empty_count=count,result_eax=0)
    return InventorySpacePlan(True,tuple(calls),empty_count=count,result_eax=(eax&0xffffff00)|1)

class InventorySpaceFrame:
    def __init__(self,threshold=0):
        _raw(threshold,32)
        if threshold is None:raise ValueError('Explicit source threshold required')
        self.threshold=threshold;self.observation=InventorySpaceObservation();self.final=None
    def advance(self,incoming):
        if not isinstance(incoming,InventorySpaceObservation):raise ValueError('Typed inventory-space observations required')
        if self.final is not None:return self.final
        for _ in range(60):
            plan=_space_plan(self.observation,self.threshold)
            if plan.complete:self.final=plan;return plan
            kind,slot=plan.needed
            if kind=='entry':
                if not incoming.entry_reached:return plan
                self.observation=replace(self.observation,entry_reached=True)
            elif kind=='normal':
                if incoming.returned.get(slot) is not True:return plan
                self.observation=replace(self.observation,returned={**self.observation.returned,slot:True})
            else:
                if slot not in incoming.pointers:return plan
                self.observation=replace(self.observation,pointers={**self.observation.pointers,slot:incoming.pointers[slot]})
        raise AssertionError('Inventory scan capture budget exceeded')

@dataclass(frozen=True)
class ItemBreakInventoryObservation:
    entry_reached:bool=False
    inventory_inputs:object=None
    inventory_returned:object=None
    mode_dword:object=None
    gem_text_created:object=None
    gem_lookup_returned:object=None
    gem_lookup_eax:object=None
    gem_text_cleanup_returned:object=None
    stop_returned:object=None
    full_notice_returned:object=None
    gem_notice_returned:object=None
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit guard post-prologue entry required')
        if self.inventory_inputs is not None and not isinstance(self.inventory_inputs,InventorySpaceObservation):raise ValueError('Typed inventory scan required')
        _raw(self.mode_dword,32);_raw(self.gem_lookup_eax,32)
        _receipts(self.inventory_returned,self.gem_text_created,self.gem_lookup_returned,
                  self.gem_text_cleanup_returned,self.stop_returned,self.full_notice_returned,self.gem_notice_returned)

@dataclass(frozen=True)
class ItemBreakInventoryPlan:
    complete:bool
    status:str
    calls:tuple=()
    needed:object=None
    next_address:object=None
    inventory:object=None
    whole_function_verified:bool=False
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class _Wait(Exception):pass

def _guard_plan(o,scan):
    calls=[];child=None
    def result(status,needed=None,exit_address=0x4710c6):
        return ItemBreakInventoryPlan(needed is None,status,tuple(calls),needed,
            exit_address if needed is None else None,child)
    def normal(key,target,args=()):
        calls.append((target,args,key))
        if getattr(o,key) is not True:raise _Wait(key)
    try:
        if not o.entry_reached:raise _Wait('entry_reached')
        calls.append(('00463ac0',(0,),'inventory_returned'))
        child=scan()
        if not child.complete:raise _Wait('inventory_inputs')
        if o.inventory_returned is not True:raise _Wait('inventory_returned')
        if child.result_eax&255:
            normal('stop_returned','0040ae0c',(0x561f34,0))
            normal('full_notice_returned','00470f97..00470ff7',
                   ('Inventory Doldu , Bot Durduruldu !','Bilgi'))
            return result('inventory_full_stop_notice_returned',exit_address=0x4710d0)
        if o.mode_dword is None:raise _Wait('mode_dword')
        if o.mode_dword!=0:return result('nonzero_mode_skips_gem')
        normal('gem_text_created','UnicodeString_from_literal',('Abyss Gem',))
        normal('gem_lookup_returned','00463950',('Abyss Gem',))
        if o.gem_lookup_eax is None:raise _Wait('gem_lookup_eax')
        absent=(o.gem_lookup_eax&255)==0
        normal('gem_text_cleanup_returned','00505c64',('gem_text',))
        if not absent:return result('gem_present')
        normal('stop_returned','0040ae0c',(0x561f34,0))
        normal('gem_notice_returned','00471066..004710c6',
               ('Abyss Gem Bitti , Bot Durduruldu !','Bilgi'))
        return result('gem_missing_stop_notice_returned')
    except _Wait as wait:return result('needs_observation',str(wait))

class ItemBreakInventoryFrame:
    def __init__(self):
        self.observation=ItemBreakInventoryObservation();self.inventory=InventorySpaceFrame(0);self.final=None
    def advance(self,incoming):
        if not isinstance(incoming,ItemBreakInventoryObservation):raise ValueError('Typed item-break inventory observations required')
        if self.final is not None:return self.final
        for _ in range(12):
            plan=_guard_plan(self.observation,lambda:self.inventory.advance(incoming.inventory_inputs or InventorySpaceObservation()))
            if plan.complete:self.final=plan;return plan
            if plan.needed=='inventory_inputs':return plan
            value=getattr(incoming,plan.needed)
            if value is None or value is False:return plan
            self.observation=replace(self.observation,**{plan.needed:value})
        raise AssertionError('Item-break inventory capture budget exceeded')

@dataclass(frozen=True)
class ItemBreakInventoryCyclePlan:
    complete:bool
    caller:object
    inventory_guard:object=None
    needed:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class ItemBreakInventoryCycleFrame:
    """Typed child binding; post-guard work byte stays an independent capture."""
    def __init__(self,*,context=0x569a20):
        self.caller=ItemBreakCycleFrame(context=context);self.guard=ItemBreakInventoryFrame()
        self.guard_result=None;self.parent_returned=False
    def advance(self,caller,guard=None,*,guard_parent_returned=None):
        if not isinstance(caller,ItemBreakCycleObservation):raise ValueError('Typed caller required')
        if caller.inventory_guard_returned is not None:raise ValueError('Typed child owns guard parent-return binding')
        if guard is not None and not isinstance(guard,ItemBreakInventoryObservation):raise ValueError('Typed guard required')
        _receipts(guard_parent_returned)
        plan=self.caller.advance(replace(caller,inventory_guard_returned=True if self.parent_returned else None))
        if plan.needed=='inventory_guard_returned':
            self.guard_result=self.guard.advance(guard or ItemBreakInventoryObservation())
            if not self.guard_result.complete:
                return ItemBreakInventoryCyclePlan(False,plan,self.guard_result,('inventory_guard',self.guard_result.needed))
            if guard_parent_returned is not True:
                return ItemBreakInventoryCyclePlan(False,plan,self.guard_result,'guard_parent_returned')
            self.parent_returned=True
            plan=self.caller.advance(replace(caller,inventory_guard_returned=True))
        return ItemBreakInventoryCyclePlan(plan.complete,plan,self.guard_result,plan.needed)
