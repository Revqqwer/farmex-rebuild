"""00463670 captured DWORD replay composed with00467908. No memory IO.

All observations belong to one fresh invocation after context preparation.
Addresses describe reads only. Missing values never mean zero/empty inventory.
"""
from dataclasses import dataclass
from typing import Optional
from item_name import ItemNameObservation,ItemNamePlan,plan_item_name
from mining_engine import OreSlotTick
from mining_requests import OreRequestPlan,plan_ore_request_name

def _raw(value):
    if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):
        raise ValueError('Raw DWORD observation required')

@dataclass(frozen=True)
class SlotNameObservation:
    global_553e80:Optional[int]=None
    offset_5540a8:Optional[int]=None
    offset_5540ac:Optional[int]=None
    root:Optional[int]=None
    inventory:Optional[int]=None
    record:Optional[int]=None
    lookup_pointer:Optional[int]=None
    metadata_pointer:Optional[int]=None
    base_item:Optional[int]=None
    variant_item:Optional[int]=None
    name:Optional[ItemNameObservation]=None

    def __post_init__(self):
        for key,value in vars(self).items():
            if key!='name':_raw(value)
        if self.name is not None and not isinstance(self.name,ItemNameObservation):
            raise ValueError('Typed name observation required')

@dataclass(frozen=True)
class SlotNamePlan:
    status:str
    ansi_bytes:Optional[bytes]=None
    item_id:Optional[int]=None
    reads:tuple=()
    name_plan:Optional[ItemNamePlan]=None
    missing:str=''
    independently_verified:bool=False

class _Missing(Exception):pass

def plan_slot_name(slot,observation,*,_observation_reader=None):
    _raw(slot)
    if slot is None or not isinstance(observation,SlotNameObservation):raise ValueError('Typed slot/name observation required')
    o=observation;reads=[];item=None
    get=lambda name:getattr(o,name) if _observation_reader is None else _observation_reader(name,None)
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def read(address,value,label):
        reads.append(('0045dc44',address&0xffffffff))
        return need(value,label)
    try:
        root=read(need(get('global_553e80'),'global_553e80'),get('root'),'root')
        inventory=read(root+need(get('offset_5540a8'),'offset_5540a8'),get('inventory'),'inventory')
        record=read(inventory+need(get('offset_5540ac'),'offset_5540ac')+((slot<<2)&0xffffffff),get('record'),'record')
        if record==0:return SlotNamePlan('empty_slot',b'',reads=tuple(reads))
        lookup=read(record+0x60,get('lookup_pointer'),'lookup_pointer')
        metadata=read(record+0x64,get('metadata_pointer'),'metadata_pointer')
        base=read(lookup,get('base_item'),'base_item')
        variant=read(metadata,get('variant_item'),'variant_item')
        item=(base+variant%1000)&0xffffffff # unsigned DIV then ADD, not signed modulo
        reader=None if _observation_reader is None else lambda name,count:_observation_reader('name.'+name,count)
        name=plan_item_name(item,(o.name or ItemNameObservation()) if reader is None else ItemNameObservation(),provided_lookup=lookup,provided_metadata=metadata,_observation_reader=reader)
        return SlotNamePlan('slot_name_resolved' if name.ansi_bytes is not None else name.status,
                            name.ansi_bytes,item,tuple(reads),name,name.reason)
    except _Missing as exc:
        return SlotNamePlan('needs_slot_name_observation',item_id=item,reads=tuple(reads),missing=str(exc))

@dataclass(frozen=True)
class SlotNameRequestPlan:
    request:OreRequestPlan
    name:Optional[SlotNamePlan]=None

def plan_slot_name_request(slot_tick,observation=None):
    if not isinstance(slot_tick,OreSlotTick):raise ValueError('Typed ore slot result required')
    reached=[i for i in slot_tick.intents if i.name=='ore_crash_request_attempt']
    if not reached:return SlotNameRequestPlan(OreRequestPlan('request_not_reached',complete=True))
    if len(reached)!=1:raise ValueError('One child request per invocation required')
    name=plan_slot_name(reached[0].value,observation or SlotNameObservation())
    return SlotNameRequestPlan(plan_ore_request_name(name.ansi_bytes),name)
