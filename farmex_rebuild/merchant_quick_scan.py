"""004bfc5c stable helper-output projection; no memory reads or native receipts.

Four cached IDs, index1..5000, independently observed buy-byte reads. Source
normal helper completion, vector allocation and final VCL rebuild are not run.
"""
from dataclasses import dataclass,field
from collections.abc import Mapping
from types import MappingProxyType
from merchant_result_filter import raw


def optional_raw(value,bits,label):
    if value is not None:raw(value,bits,label)


@dataclass(frozen=True)
class QuickItemObservation:
    name_category_byte:object=None
    stored_category_byte:object=None
    extension_id_dword:object=None
    base_name_ansi:object=None
    def __post_init__(self):
        optional_raw(self.name_category_byte,8,'name category')
        optional_raw(self.stored_category_byte,8,'fresh stored category')
        optional_raw(self.extension_id_dword,32,'extension ID')
        if self.base_name_ansi is not None and type(self.base_name_ansi) is not bytes:raise ValueError('Explicit copied ANSI item name required')
    @property
    def name_family(self):
        return None if self.name_category_byte is None else ('lookup' if self.name_category_byte in (0,2,5,11) else 'extension')


def format_quick_item_name(category,base,extension_id):
    raw(category,8,'name category');raw(extension_id,32,'extension ID')
    if type(base) is not bytes:raise ValueError('Explicit ANSI copy output required')
    name=base
    if category in (2,5,11):name+=b'(+'+str(extension_id%10).encode('ascii')+b')'
    if category in (11,12):name+=b' (Reverse)'
    return name


@dataclass(frozen=True)
class QuickActorObservation:
    pointer:object=None
    active_eax:object=None
    buy_first_eax:object=None
    buy_second_eax:object=None
    entity_id_eax:object=None
    x_ftol_eax:object=None
    y_ftol_eax:object=None
    seller_ansi:object=None
    slot_base_word:object=None
    slot_ids:tuple=()
    items:object=field(default_factory=dict)
    def __post_init__(self):
        for v in (self.pointer,self.active_eax,self.buy_first_eax,self.buy_second_eax,self.entity_id_eax,self.x_ftol_eax,self.y_ftol_eax):optional_raw(v,32,'quick helper EAX')
        optional_raw(self.slot_base_word,16,'cached slot WORD offset')
        if self.seller_ansi is not None and type(self.seller_ansi) is not bytes:raise ValueError('Explicit seller ANSI copy output required')
        if type(self.slot_ids) is not tuple or len(self.slot_ids)>4:raise ValueError('Up to four ordered cached ID observations required')
        for v in self.slot_ids:optional_raw(v,32,'cached item ID')
        if not isinstance(self.items,Mapping) or any(type(k) is not int or not 0<=k<4 or not isinstance(v,QuickItemObservation) for k,v in self.items.items()):raise ValueError('Typed metadata per cached slot required')
        object.__setattr__(self,'items',MappingProxyType(dict(self.items)))


@dataclass(frozen=True)
class QuickRecord:
    actor_index:int
    slot_index:int
    item_id:int
    seller_ansi:bytes
    item_name_ansi:bytes
    direction_byte:int
    category_byte:int
    extension_digit:int
    x_dword:int
    y_dword:int
    amount_dword:int=0
    alternate_amount_dword:int=0
    price_dword:int=0
    final_flag:int=0


@dataclass(frozen=True)
class QuickScanProjection:
    complete:bool
    status:str
    records:tuple=()
    direction_byte:object=None
    needed:object=None
    steps:tuple=()
    clear_intents:tuple=('result_vector_98','result_list')
    rebuild_requested:bool=False
    source_helper_returns_verified:bool=False
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class _Missing(Exception):
    def __init__(self,label):self.label=label


def project_quick_scan(actors,*,initial_direction_byte=None):
    """Missing mapping entry is unknown, not a fabricated empty lookup.

    Fresh calls start a new projection. This is not a resumable native frame.
    Four IDs are fetched before the first metadata lookup for each actor.
    """
    if not isinstance(actors,Mapping) or any(type(k) is not int or not 1<=k<=5000 or not isinstance(v,QuickActorObservation) for k,v in actors.items()):raise ValueError('Explicit lookup observations indexed1..5000 required')
    optional_raw(initial_direction_byte,8,'observed initial stack byte')
    records=[];steps=[];direction=initial_direction_byte
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def out(ok,needed=None):
        return QuickScanProjection(ok,'own_quick_values_projected' if ok else 'needs_observation',
            tuple(records),direction,needed,tuple(steps),rebuild_requested=ok)
    try:
        for index in range(1,5001):
            steps.append(('lookup',index));a=need(actors.get(index),('lookup',index))
            pointer=need(a.pointer,(index,'pointer'))
            if pointer==0:continue
            if need(a.active_eax,(index,'active_eax'))&255==0:continue
            first=need(a.buy_first_eax,(index,'buy_first_eax'))&255
            if first==0:direction=0
            second=need(a.buy_second_eax,(index,'buy_second_eax'))&255
            if second==1:direction=1
            # No else-normalization: source leaves the stack byte unchanged.
            need(a.entity_id_eax,(index,'entity_id_eax')) # Read even though row does not use it.
            x=need(a.x_ftol_eax,(index,'x_ftol_eax'));y=need(a.y_ftol_eax,(index,'y_ftol_eax'))
            seller=need(a.seller_ansi,(index,'seller_ansi'))
            offset=need(a.slot_base_word,(index,'slot_base_word'));ids=[]
            for slot in range(4):
                steps.append(('read_cached_id',index,slot,(pointer+offset)&0xffffffff))
                item_id=need(a.slot_ids[slot] if slot<len(a.slot_ids) else None,(index,'slot_id',slot))
                ids.append(item_id);offset=(offset+4)&65535
            for slot,item_id in enumerate(ids):
                if item_id==0:continue
                m=need(a.items.get(slot),(index,'metadata',slot))
                category=need(m.name_category_byte,(index,slot,'name_category_byte'))
                extension=need(m.extension_id_dword,(index,slot,'extension_id_dword'))
                steps.append(('name_family',index,slot,m.name_family))
                base=need(m.base_name_ansi,(index,slot,'base_name_ansi'))
                name=format_quick_item_name(category,base,extension)
                stored=need(m.stored_category_byte,(index,slot,'stored_category_byte'))
                flag=need(direction,(index,slot,'initial_or_prior_direction_byte'))
                records.append(QuickRecord(index,slot,item_id,seller,name,flag,stored,extension%10,x,y))
        return out(True)
    except _Missing as e:return out(False,e.label)
