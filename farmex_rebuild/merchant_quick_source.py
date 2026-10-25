"""Ordered captured actor/item producers for004bfc5c; no process access.

Lookup and float-call normal returns remain explicit observations. Read values
and exact captured copy ranges are consumed, never invented on missing input.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from collections.abc import Mapping
from item_lookup import BaseItemLookupObservation,ExtensionLookupObservation,plan_base_item_lookup,plan_extension_lookup
from merchant_actor_metadata import MerchantActorObservation,MerchantCoordinateObservation
from game_text import npc_text_request,replay_text_copy
from merchant_quick_scan import QuickItemObservation,QuickActorObservation,optional_raw


@dataclass(frozen=True)
class QuickItemSource:
    base:object=None
    resolver_eax:object=None
    extension:object=None
    name_category_eax:object=None
    extension_id_eax:object=None
    name_storage_eax:object=None
    name_data_eax:object=None
    readable:object=None
    captured_bytes:object=None
    stored_category_eax:object=None
    def __post_init__(self):
        for name,kind in (('base',BaseItemLookupObservation),('extension',ExtensionLookupObservation)):
            v=getattr(self,name)
            if v is not None and not isinstance(v,kind):raise ValueError('Typed '+name+' observations required')
        for name in ('resolver_eax','name_category_eax','extension_id_eax','name_storage_eax','name_data_eax','stored_category_eax'):
            optional_raw(getattr(self,name),32,name)
        if self.readable is not None and type(self.readable) is not bool:raise ValueError('Explicit read-probe observation required')
        if self.captured_bytes is not None and type(self.captured_bytes) is not bytes:raise ValueError('Exact immutable copy capture required')


@dataclass(frozen=True)
class QuickItemProduction:
    complete:bool
    status:str
    metadata:QuickItemObservation
    base:object=None
    extension:object=None
    text_request:object=None
    text_copy:object=None
    steps:tuple=()
    native_execution_verified:bool=False


class _Missing(Exception):pass


def need(value,label):
    if value is None:raise _Missing(label)
    return value


def produce_quick_item(item_id,o=None):
    optional_raw(item_id,32,'item ID')
    if item_id is None or item_id==0:raise ValueError('Reached nonzero cached item required')
    o=QuickItemSource() if o is None else o
    if not isinstance(o,QuickItemSource):raise ValueError('Typed quick item source required')
    metadata=QuickItemObservation();steps=[];base=None;extension=None;request=None;copy=None
    def out(ok,status):return QuickItemProduction(ok,status,metadata,base,extension,request,copy,tuple(steps))
    try:
        base=plan_base_item_lookup(item_id,o.base)
        if not base.complete:return out(False,'base:'+base.status)
        lookup=base.result_eax;steps.append(('read_byte','resolver',(lookup+4)&0xffffffff))
        resolver=need(o.resolver_eax,'resolver_eax')
        extension=plan_extension_lookup(item_id,resolver,o.extension)
        if not extension.complete:return out(False,'extension:'+extension.status)
        pointer=extension.result_eax
        steps.append(('read_byte','name_category',(pointer+0x4c)&0xffffffff))
        category=need(o.name_category_eax,'name_category_eax')&255
        metadata=replace(metadata,name_category_byte=category)
        steps.append(('read_dword','extension_id',pointer))
        digit=need(o.extension_id_eax,'extension_id_eax');metadata=replace(metadata,extension_id_dword=digit)
        owner,offset,storage_offset=(lookup,0xc,0x1c) if category in (0,2,5,11) else (pointer,8,0x18)
        steps.append(('read_dword','name_storage',(owner+storage_offset)&0xffffffff))
        storage=need(o.name_storage_eax,'name_storage_eax')
        steps.append(('read_dword','name_data',(owner+offset)&0xffffffff))
        first=need(o.name_data_eax,'name_data_eax') # Always read, even inline.
        request=npc_text_request(owner,offset,storage,first,signed_threshold=False)
        steps.append(('copy_0045dca8',request.address,request.byte_count))
        copy=replay_text_copy(request.byte_count,o.readable,o.captured_bytes)
        if copy.status not in ('complete','needs_codepage'):return out(False,'copy:'+copy.status)
        metadata=replace(metadata,base_name_ansi=copy.ansi_bytes)
        steps.append(('read_byte','stored_category',(pointer+0x4c)&0xffffffff))
        metadata=replace(metadata,stored_category_byte=need(o.stored_category_eax,'stored_category_eax')&255)
        return out(True,'own_quick_item_prepared')
    except _Missing as e:return out(False,'needs_'+str(e))


@dataclass(frozen=True)
class QuickActorSource:
    actor:MerchantActorObservation=field(default_factory=MerchantActorObservation)
    active_offset:object=None
    active_eax:object=None
    first_buy_offset:object=None
    first_buy_eax:object=None
    second_buy_offset:object=None
    second_buy_eax:object=None
    entity_offset:object=None
    entity_eax:object=None
    slot_base_word:object=None
    slot_ids:tuple=()
    items:object=field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.actor,MerchantActorObservation):raise ValueError('Typed actor source required')
        for name in ('active_offset','active_eax','first_buy_offset','first_buy_eax','second_buy_offset','second_buy_eax','entity_offset','entity_eax'):
            optional_raw(getattr(self,name),32,name)
        optional_raw(self.slot_base_word,16,'slot WORD offset')
        if type(self.slot_ids) is not tuple or len(self.slot_ids)>4:raise ValueError('Four ordered cached ID captures required')
        for v in self.slot_ids:optional_raw(v,32,'cached ID')
        if not isinstance(self.items,Mapping) or any(type(k) is not int or not 0<=k<4 or not isinstance(v,QuickItemSource) for k,v in self.items.items()):raise ValueError('Typed quick item sources required')
        object.__setattr__(self,'items',MappingProxyType(dict(self.items)))


@dataclass(frozen=True)
class QuickActorProduction:
    complete:bool
    status:str
    actor_values:QuickActorObservation
    direction_byte:object=None
    steps:tuple=()
    text_request:object=None
    text_copy:object=None
    item_plans:tuple=()
    native_execution_verified:bool=False


def produce_quick_actor(index,o=None,*,initial_direction_byte=None):
    if type(index) is not int or not 1<=index<=5000:raise ValueError('Actor lookup index1..5000 required')
    optional_raw(initial_direction_byte,8,'initial direction')
    o=QuickActorSource() if o is None else o
    if not isinstance(o,QuickActorSource):raise ValueError('Typed quick actor source required')
    a=o.actor;values={};items={};plans=[];steps=[('lookup_00464a10',index)]
    direction=initial_direction_byte;request=None;copy=None
    def out(ok,status):
        return QuickActorProduction(ok,status,QuickActorObservation(**values,items=items),direction,
                                    tuple(steps),request,copy,tuple(plans))
    try:
        if a.lookup_returned is not True:return out(False,'needs_lookup_normal_return')
        pointer=need(a.actor_pointer,'actor_pointer');values['pointer']=pointer
        if pointer==0:return out(True,'empty_lookup')
        def read(field,offset,value):
            at=(pointer+need(offset,field+'_offset'))&0xffffffff;steps.append(('read',field,at))
            return need(value,field+'_eax')
        active=read('active',o.active_offset,o.active_eax);values['active_eax']=active
        if active&255==0:return out(True,'inactive_actor')
        first=read('first_buy',o.first_buy_offset,o.first_buy_eax);values['buy_first_eax']=first
        if first&255==0:direction=0
        second=read('second_buy',o.second_buy_offset,o.second_buy_eax);values['buy_second_eax']=second
        if second&255==1:direction=1
        values['entity_id_eax']=read('entity',o.entity_offset,o.entity_eax)
        for axis in ('x','y'):
            c=getattr(a,axis) or MerchantCoordinateObservation()
            at=(pointer+need(c.offset_dword,axis+'_offset'))&0xffffffff
            steps.append(('float_0045ddb8',axis,at))
            if c.float_reader_returned is not True:raise _Missing(axis+'_float_reader_normal_return')
            steps.append(('ftol',axis))
            if c.ftol_returned is not True:raise _Missing(axis+'_ftol_normal_return')
            values[axis+'_ftol_eax']=need(c.ftol_eax,axis+'_ftol_eax')
        storage=read('seller_storage',a.storage_offset_dword,a.storage_dword)
        first_offset=need(a.initial_name_offset_dword,'initial_name_offset')
        data=read('seller_data',first_offset,a.initial_name_dword)
        offset=need(a.inline_name_offset_dword,'fresh_inline_name_offset') if storage<16 else first_offset
        request=npc_text_request(pointer,offset,storage,data,signed_threshold=False)
        steps.append(('copy_0045dca8',request.address,request.byte_count))
        copy=replay_text_copy(request.byte_count,a.readable,a.copied_bytes)
        if copy.status not in ('complete','needs_codepage'):return out(False,'seller_copy:'+copy.status)
        values['seller_ansi']=copy.ansi_bytes
        offset=need(o.slot_base_word,'slot_base_word');values['slot_base_word']=offset;ids=[]
        for slot in range(4):
            steps.append(('cached_id',slot,(pointer+offset)&0xffffffff))
            ids.append(need(o.slot_ids[slot] if slot<len(o.slot_ids) else None,'slot_id_'+str(slot)))
            values['slot_ids']=tuple(ids);offset=(offset+4)&65535
        for slot,item_id in enumerate(ids):
            if item_id==0:continue
            p=produce_quick_item(item_id,o.items.get(slot));plans.append((slot,p));items[slot]=p.metadata
            if not p.complete:return out(False,'item%d:'%slot+p.status)
            # Source consumes direction only after this slot's metadata stores.
            if direction is None:return out(False,'needs_initial_or_prior_direction_byte')
        return out(True,'own_quick_actor_prepared')
    except _Missing as e:return out(False,'needs_'+str(e))


@dataclass(frozen=True)
class QuickSourceSnapshot:
    actors:object
    code_page:object=None
    initial_direction_byte:object=None
    def __post_init__(self):
        if not isinstance(self.actors,Mapping) or any(type(k) is not int or not 1<=k<=5000 or not isinstance(v,QuickActorSource) for k,v in self.actors.items()):raise ValueError('Typed source actors indexed1..5000 required')
        if self.code_page is not None and (type(self.code_page) is not int or not 1<=self.code_page<=65535):raise ValueError('Explicit nonzero codepage or unknown required')
        optional_raw(self.initial_direction_byte,8,'initial direction')
        object.__setattr__(self,'actors',MappingProxyType(dict(self.actors)))


@dataclass(frozen=True)
class QuickSourceProduction:
    complete:bool
    status:str
    actors:object
    code_page:object
    initial_direction_byte:object
    direction_byte:object
    actor_plans:tuple=()
    native_execution_verified:bool=False


def produce_quick_sources(snapshot):
    if not isinstance(snapshot,QuickSourceSnapshot):raise ValueError('Typed source snapshot required')
    actors={};plans=[];direction=snapshot.initial_direction_byte
    def out(ok,status):return QuickSourceProduction(ok,status,MappingProxyType(dict(actors)),
        snapshot.code_page,snapshot.initial_direction_byte,direction,tuple(plans))
    for index in range(1,5001):
        o=snapshot.actors.get(index)
        if o is None:return out(False,'needs_actor_source:%d'%index)
        p=produce_quick_actor(index,o,initial_direction_byte=direction)
        plans.append((index,p));actors[index]=p.actor_values;direction=p.direction_byte
        if not p.complete:return out(False,'actor%d:'%index+p.status)
    return out(True,'own_source_values_prepared')
