"""00471134 manual path and Button5 caller; owned NPC/request children only.

No automatic-cycle work/enable gates, inventory-full test or cooldown are
inserted. Notice/managed helper returns remain captured opaque boundaries.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState
from item_break_cycle import _raw,_receipts
from item_break_npc import ItemBreakNpcObservation,ItemBreakNpcFrame
from item_break_requests import ItemBreakRequestObservation,ItemBreakRequestFrame

@dataclass(frozen=True)
class ItemBreakManualObservation:
    entry_reached:bool=False
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    npc_inputs:object=None
    request_inputs:object=None
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit manual post-prologue entry required')
        values=dict(self.values);normals=dict(self.normal_returns)
        for value in values.values():
            _raw(value,32)
            if value is None:raise ValueError('Explicit manual operand required')
        if any(type(v) is not bool for v in normals.values()):raise ValueError('Separate manual helper normal receipts required')
        if self.npc_inputs is not None and not isinstance(self.npc_inputs,ItemBreakNpcObservation):raise ValueError('Typed manual NPC child required')
        if self.request_inputs is not None and not isinstance(self.request_inputs,ItemBreakRequestObservation):raise ValueError('Typed manual request child required')
        object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(normals))

@dataclass(frozen=True)
class ItemBreakManualPlan:
    complete:bool
    status:str
    queue:QueueState
    calls:tuple=()
    npc:object=None
    request:object=None
    needed:object=None
    next_address:object=None
    whole_function_verified:bool=False
    native_execution_verified:bool=False
    delivery_verified:bool=False
    live_compatibility_verified:bool=False

class _Wait(Exception):
    def __init__(self,kind,key):self.needed=(kind,key);super().__init__(key)

def _plan(o,context,npc_child,request_child,queue):
    calls=[];npc=request=None
    def result(status,wait=None):
        return ItemBreakManualPlan(wait is None,status,queue(),tuple(calls),npc,request,
            None if wait is None else wait.needed,0x471276 if wait is None else None)
    def normal(key,target,args=()):
        calls.append((target,args,key))
        if o.normal_returns.get(key) is not True:raise _Wait('normal',key)
    def value(key):
        if key not in o.values:raise _Wait('value',key)
        return o.values[key]
    try:
        if not o.entry_reached:raise _Wait('entry','00471144')
        calls.append(('00470d98',(context,),'npc_parent'))
        npc=npc_child()
        if not npc.complete:raise _Wait('npc','npc_selection')
        if o.normal_returns.get('npc_parent') is not True:raise _Wait('normal','npc_parent')
        if npc.result_eax&255==0:
            normal('npc_notice','00471216..00471276',('NPC Yakininda Olmalisiniz !','Bilgi'))
            return result('npc_zero_notice_returned')
        # This source read occurs AFTER the NPC helper and may differ from its
        # earlier mode capture. It is never derived from that child snapshot.
        if value('fresh_mode_dword')!=0:return result('nonzero_mode_skips_manual_action')
        normal('gem_text_created','UnicodeString_from_literal',('Abyss Gem',))
        normal('gem_lookup','00463950',('opaque_managed_gem_text',))
        absent=(value('gem_lookup_eax')&255)==0
        normal('gem_text_cleanup','00505c64',('gem_text',))
        if absent:
            normal('gem_notice','004711a7..00471209',('Cantanizda Abbys Gem Yok !','Bilgi'))
            return result('gem_zero_notice_returned')
        calls.append(('004ca9b0',(0x561ef8,),'request_parent'))
        request=request_child()
        if not request.complete:raise _Wait('request','item_break_requests')
        if o.normal_returns.get('request_parent') is not True:raise _Wait('normal','request_parent')
        return result('request_child_returned')
    except _Wait as wait:return result('needs_observation',wait)

class ItemBreakManualFrame:
    def __init__(self,queue=None,*,context=0x569a20):
        _raw(context,32)
        if context is None:raise ValueError('Explicit source manual context required')
        self.context=context;self.npc=ItemBreakNpcFrame(context=context);self.request=ItemBreakRequestFrame(queue)
        self.observation=ItemBreakManualObservation();self.final=None
    def advance(self,incoming):
        if not isinstance(incoming,ItemBreakManualObservation):raise ValueError('Typed manual observations required')
        if self.final is not None:return self.final
        for _ in range(12):
            plan=_plan(self.observation,self.context,
                lambda:self.npc.advance(incoming.npc_inputs or ItemBreakNpcObservation()),
                lambda:self.request.advance(incoming.request_inputs or ItemBreakRequestObservation()),
                lambda:self.request.queue)
            if plan.complete:self.final=plan;return plan
            kind,key=plan.needed
            if kind in ('npc','request'):return plan
            if kind=='entry':
                if not incoming.entry_reached:return plan
                self.observation=replace(self.observation,entry_reached=True)
            elif kind=='normal':
                if incoming.normal_returns.get(key) is not True:return plan
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,key:True})
            else:
                if key not in incoming.values:return plan
                self.observation=replace(self.observation,values={**self.observation.values,key:incoming.values[key]})
        raise AssertionError('Manual reached capture budget exceeded')

@dataclass(frozen=True)
class ItemBreakManualClickPlan:
    complete:bool
    manual:object=None
    needed:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class ItemBreakManualClickFrame:
    """One owned Button5 invocation; source callback has no561f55 gate."""
    def __init__(self,queue=None):
        self.manual=ItemBreakManualFrame(queue);self.clicked=False;self.final=None
    def advance(self,observation=None,*,clicked=False,handler_returned=None):
        if type(clicked) is not bool:raise ValueError('Explicit callback entry required')
        _receipts(handler_returned)
        if observation is not None and not isinstance(observation,ItemBreakManualObservation):raise ValueError('Typed manual child required')
        if self.final is not None:return self.final
        if not self.clicked:
            if not clicked:return ItemBreakManualClickPlan(False,needed='callback_entry')
            self.clicked=True
        plan=self.manual.advance(observation or ItemBreakManualObservation())
        if not plan.complete:return ItemBreakManualClickPlan(False,plan,('manual',plan.needed))
        if handler_returned is not True:return ItemBreakManualClickPlan(False,plan,'handler_returned')
        self.final=ItemBreakManualClickPlan(True,plan);return self.final
