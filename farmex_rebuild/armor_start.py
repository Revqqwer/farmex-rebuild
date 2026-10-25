"""4f7f74 Armor start and4f74d8 combo mapping; captured observations only.

No process scan, protected read, native floating-point/VCL/alert invocation.
NPC selector reuse consumes supplied iterator rows and explicit completion.
"""
from dataclasses import dataclass,field,replace
from collections.abc import Mapping
from types import MappingProxyType
from upgrade_packets import _raw
from npc_lookup import select_npc

COMBO_PATH='frmMain/MainTab/SheetUpgrade/GroupBox23/cmbUpgArmorList'
ITEM_IDS=(0x0bfb0829,0x0bfb0c11,0x0bfb0ff9,0x0bfb13e1,0x0bfb17c9,0,
          0x0e5d6229,0x0e5d6611,0x0e5d69f9,0x0e5d6de1,0x0e5d71c9,0,
          0x0f8e8f29,0x0f8e9311,0x0f8e96f9,0x0f8e9ae1,0x0f8e9ec9,0,
          0x10bfbc29,0x10bfc011,0x10bfc3f9,0x10bfc7e1,0x10bfcbc9)


def armor_item_id(combo_dword):
    _raw(combo_dword)
    if combo_dword is None:raise ValueError('Observed combo EAX DWORD required')
    return ITEM_IDS[combo_dword] if combo_dword<len(ITEM_IDS) else 0


@dataclass(frozen=True)
class ArmorStartState:
    fields:Mapping=field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.fields,Mapping):raise ValueError('Captured source fields required')
        for k,v in self.fields.items():
            if type(k) is not int or k<0:raise ValueError('Source field offset required')
            _raw(v)
            if v is None:raise ValueError('Known captured field DWORD required')
        object.__setattr__(self,'fields',MappingProxyType(dict(self.fields)))


@dataclass(frozen=True)
class ArmorStartObservation:
    filter_ready_returned:object=None
    npc_id_dword:object=None
    lookup_candidates:object=None
    traversal_complete:object=None
    npc_pointer_dword:object=None
    x_offset_dword:object=None
    y_offset_dword:object=None
    x_ftol_dword:object=None
    y_ftol_dword:object=None
    distance_ftol_dword:object=None
    first_combo_dword:object=None
    second_combo_dword:object=None
    bag_flag_byte:object=None
    message_returns:Mapping=field(default_factory=dict)
    message_cleanup_returns:Mapping=field(default_factory=dict)

    def __post_init__(self):
        for value in (self.npc_id_dword,self.npc_pointer_dword,self.x_offset_dword,self.y_offset_dword,
                      self.x_ftol_dword,self.y_ftol_dword,self.distance_ftol_dword,self.first_combo_dword,self.second_combo_dword):_raw(value)
        if self.bag_flag_byte is not None and (type(self.bag_flag_byte) is not int or not 0<=self.bag_flag_byte<=255):
            raise ValueError('Observed bag helper AL BYTE required')
        for key in ('message_returns','message_cleanup_returns'):
            value=getattr(self,key)
            if not isinstance(value,Mapping):raise ValueError('Per-message observations required')
            object.__setattr__(self,key,MappingProxyType(dict(value)))


@dataclass(frozen=True)
class ArmorStartPlan:
    complete:bool
    armed:bool
    status:str
    input_state:ArmorStartState
    state:ArmorStartState
    prospective_state:ArmorStartState
    calls:tuple=()
    messages:tuple=()
    lookup:object=None
    missing:str=''
    independently_verified:bool=False


def replay_armor_start(state,observation):
    if not isinstance(state,ArmorStartState) or not isinstance(observation,ArmorStartObservation):
        raise ValueError('Typed Armor start state and observations required')
    o=observation;fields=dict(state.fields);calls=[];messages=[];lookup=None
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def normal(value,label):
        if value is not None and type(value) is not bool:raise ValueError('Explicit normal-return boolean required')
        if value is not True:raise Missing(label+' normal return')
    def s32(value):return value-0x100000000 if value&0x80000000 else value
    def finish(status,armed=False):
        result=ArmorStartState(fields)
        return ArmorStartPlan(True,armed,status,state,result,result,tuple(calls),tuple(messages),lookup)
    def message(reason,literal):
        messages.append(reason);calls.append(('00464d10',reason,literal))
        normal(o.message_returns.get(reason),reason+' message')
        calls.append(('004040f8:message_temporaries',reason))
        normal(o.message_cleanup_returns.get(reason),reason+' temporary cleanup')
        return finish(reason)
    try:
        calls.append(('filter_construct',b'Armor Merchant'))
        normal(o.filter_ready_returned,'filter construction')
        calls.append(('00465960',b'Armor Merchant'))
        npc=o.npc_id_dword
        if o.lookup_candidates is not None:
            if npc is not None:raise ValueError('Raw NPC result and bound selector conflict')
            lookup=select_npc(o.lookup_candidates,b'Armor Merchant',traversal_complete=o.traversal_complete)
            if lookup.status!='complete':raise Missing(lookup.missing)
            npc=lookup.candidate_id
        fields[0x4c]=need(npc,'NPC lookup result DWORD')
        if npc==0:return message('npc_missing',0x551093)
        calls.append(('00464a10',npc))
        pointer=fields[0x48]=need(o.npc_pointer_dword,'NPC pointer DWORD')
        if pointer==0:return finish('npc_pointer_zero')
        calls.append(('0045ddb8', (pointer+need(o.x_offset_dword,'NPC x offset'))&0xffffffff))
        fields[0x50]=need(o.x_ftol_dword,'NPC x __ftol EAX')
        calls.append(('0045ddb8', (pointer+need(o.y_offset_dword,'NPC y offset'))&0xffffffff))
        fields[0x54]=need(o.y_ftol_dword,'NPC y __ftol EAX')
        # Native int->float argument conversion is not emulated. Its helper's
        # final __ftol result is a separate captured observation.
        calls.append(('00460548',('source int fields',0x50,0x54)))
        if s32(need(o.distance_ftol_dword,'fresh distance __ftol EAX'))>=10:
            return message('too_far',0x5510bc)
        calls.append(('GetItemIndex:first',COMBO_PATH))
        first=need(o.first_combo_dword,'first combo EAX DWORD')
        calls.append(('004f74d8',first))
        fields[0x58]=armor_item_id(first)
        if fields[0x58]==0:return message('item_missing',0x5510e5)
        calls.append(('GetItemIndex:second',COMBO_PATH))
        fields[0x5c]=need(o.second_combo_dword,'fresh second combo EAX DWORD')
        calls.append(('00463ac0',0))
        if need(o.bag_flag_byte,'fresh bag helper AL')!=0:return message('bag_full',0x55110a)
        fields[0x60]=0;fields[0x10]=2
        return finish('armor_armed',True)
    except Missing as error:
        return ArmorStartPlan(False,False,'needs_observation',state,state,ArmorStartState(fields),
                              tuple(calls),tuple(messages),lookup,str(error))


def capture_armor_start_state(runner):
    fields=dict(getattr(runner,'armor_source_fields',{}))
    fields.update({0x10:runner.state,0x60:runner.armor_attempts})
    return ArmorStartState(fields)


def apply_armor_start(runner,plan):
    if not isinstance(plan,ArmorStartPlan) or not plan.complete:raise ValueError('Complete local Armor start plan required')
    if not runner.source_clock or runner.source_pending is not None:raise ValueError('Idle source-clock runner required')
    if capture_armor_start_state(runner)!=plan.input_state:raise ValueError('Armor start input state changed')
    fields=plan.state.fields
    runner.state=fields[0x10];runner.armor_attempts=fields[0x60]
    runner.armor_source_fields=fields
    runner.reason=''
