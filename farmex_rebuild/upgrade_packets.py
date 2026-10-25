"""4f714c 57-byte local buffer plan and 4634a4 captured-read item ID replay.

No process access, protection changes, queue insertion, transport or item action.
The two getter invocations have independent observations in source call order.
"""
from dataclasses import dataclass
from typing import Optional

TEMPLATE=bytes.fromhex('5b02018c2700000000000000000000001b00000000ff00000000ff00000000ff00000000ff00000000ff00000000ff00000000ff00000000ff')


def _raw(value):
    if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):
        raise ValueError('Raw DWORD observation required')


@dataclass(frozen=True)
class UpgradeItemObservation:
    global_root_slot:Optional[int]=None
    inventory_offset:Optional[int]=None
    records_offset:Optional[int]=None
    root:Optional[int]=None
    inventory:Optional[int]=None
    record:Optional[int]=None
    base_pointer:Optional[int]=None
    variant_pointer:Optional[int]=None
    base_item:Optional[int]=None
    variant_item:Optional[int]=None

    def __post_init__(self):
        for value in vars(self).values():_raw(value)


@dataclass(frozen=True)
class UpgradeItemPlan:
    complete:bool
    result_dword:Optional[int]=None
    reads:tuple=()
    missing:str=''
    independently_verified:bool=False


def plan_upgrade_item(slot_dword,observation):
    _raw(slot_dword)
    if slot_dword is None or not isinstance(observation,UpgradeItemObservation):
        raise ValueError('Explicit slot and typed captured item fields required')
    o=observation;reads=[]
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def read(address,value,label):
        reads.append(('0045dc44',address&0xffffffff))
        return need(value,label)
    try:
        root=read(need(o.global_root_slot,'global root slot'),o.root,'root')
        inventory=read(root+need(o.inventory_offset,'inventory offset'),o.inventory,'inventory')
        record=read(inventory+need(o.records_offset,'records offset')+((slot_dword*4)&0xffffffff),o.record,'record')
        if record==0:return UpgradeItemPlan(True,0,tuple(reads))
        base_pointer=read(record+0x60,o.base_pointer,'base pointer')
        variant_pointer=read(record+0x64,o.variant_pointer,'variant pointer')
        base=read(base_pointer,o.base_item,'base item')
        variant=read(variant_pointer,o.variant_item,'variant item')
        return UpgradeItemPlan(True,(base+variant%1000)&0xffffffff,tuple(reads))
    except Missing as error:
        return UpgradeItemPlan(False,reads=tuple(reads),missing=str(error))


@dataclass(frozen=True)
class UpgradePacketObservation:
    scroll_item_dword:Optional[int]=None
    target_item_dword:Optional[int]=None
    scroll_item_inputs:Optional[UpgradeItemObservation]=None
    target_item_inputs:Optional[UpgradeItemObservation]=None

    def __post_init__(self):
        _raw(self.scroll_item_dword);_raw(self.target_item_dword)
        for value in (self.scroll_item_inputs,self.target_item_inputs):
            if value is not None and not isinstance(value,UpgradeItemObservation):
                raise ValueError('Typed fresh item-helper observation required')


@dataclass(frozen=True)
class UpgradePacketPlan:
    complete:bool
    payload:Optional[bytes]=None
    calls:tuple=()
    item_plans:tuple=()
    missing:str=''
    queue_delay_ms:int=0
    independently_verified:bool=False
    observed_items:tuple=()


def plan_upgrade_packet(anvil_dword,target_relative_dword,scroll_relative_dword,observation):
    for value in (anvil_dword,target_relative_dword,scroll_relative_dword):_raw(value)
    if not isinstance(observation,UpgradePacketObservation):
        raise ValueError('Typed Upgrade packet observation required')
    calls=[];items=[];resolved=[]
    class Missing(Exception):pass
    def item(relative,observed,bound,label):
        if relative is None:raise Missing(label+' relative slot DWORD')
        slot=(relative+14)&0xffffffff
        calls.append(('004634a4',slot))
        if observed is not None and bound is not None:
            raise ValueError('Observed item ID and bound getter conflict: '+label)
        if bound is not None:
            plan=plan_upgrade_item(slot,bound);items.append((label,plan))
            if not plan.complete:raise Missing(label+': '+plan.missing)
            resolved.append((label,plan.result_dword))
            return plan.result_dword
        if observed is None:raise Missing(label+' fresh004634a4 EAX')
        resolved.append((label,observed))
        return observed
    try:
        scroll=item(scroll_relative_dword,observation.scroll_item_dword,observation.scroll_item_inputs,'scroll')
        target=item(target_relative_dword,observation.target_item_dword,observation.target_item_inputs,'target')
        if anvil_dword is None:raise Missing('anvil DWORD at object+8')
        payload=bytearray(TEMPLATE)
        payload[3:7]=anvil_dword.to_bytes(4,'little')
        payload[7:11]=target.to_bytes(4,'little')
        payload[11]=target_relative_dword&255
        payload[12:16]=scroll.to_bytes(4,'little')
        payload[16]=scroll_relative_dword&255
        calls.append(('004c7710',0x561ef8,57,0))
        return UpgradePacketPlan(True,bytes(payload),tuple(calls),tuple(items),observed_items=tuple(resolved))
    except Missing as error:
        return UpgradePacketPlan(False,calls=tuple(calls),item_plans=tuple(items),missing=str(error),observed_items=tuple(resolved))
