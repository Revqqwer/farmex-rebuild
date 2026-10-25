"""Selection prefixes of 420aac(list order)/420ca8(inventory order).

No packet emission, pending writes, price accumulation, native FPU or queue tail.
"""
from dataclasses import dataclass
from typing import Tuple,Optional

def _raw(value,bits):
    if value is not None and (type(value) is not int or not 0<=value<1<<bits):raise ValueError('Raw source field required')

def _signed(value):return value if value<0x80000000 else value-(1<<32)

@dataclass(frozen=True)
class SellPreparedRow:
    item_dword:int
    quantity_dword:int
    price_qword:int
    def __post_init__(self):
        for value,bits in ((self.item_dword,32),(self.quantity_dword,32),(self.price_qword,64)):
            _raw(value,bits)
            if value is None:raise ValueError('Complete observed prepared row required')

@dataclass(frozen=True)
class SellSelectionObservation:
    # Explicit stable snapshot of the prepared vector, not live ListView rows.
    rows:Tuple[SellPreparedRow,...]=()
    stable_rows:Optional[bool]=None
    item_results:tuple=()
    used_bytes:tuple=()
    quantity_results:tuple=()
    inventory_slot_dword:int=14
    list_index_dword:int=0
    def __post_init__(self):
        if type(self.rows) is not tuple or any(not isinstance(r,SellPreparedRow) for r in self.rows):
            raise ValueError('Immutable prepared rows required')
        if self.stable_rows is not None and type(self.stable_rows) is not bool:raise ValueError('Stable vector contract required')
        for sequence,bits,maximum in ((self.item_results,32,28),(self.used_bytes,8,28),(self.quantity_results,32,2)):
            if type(sequence) is not tuple or len(sequence)>maximum:raise ValueError('Immutable reached observations required')
            for value in sequence:_raw(value,bits)
        _raw(self.inventory_slot_dword,32);_raw(self.list_index_dword,32)
        if self.inventory_slot_dword is None or self.list_index_dword is None:raise ValueError('Explicit caller counters required')

@dataclass(frozen=True)
class SellSelectionPlan:
    complete:bool
    status:str
    inventory_slot:object=None
    row_index:object=None
    item_dword:object=None
    quantity_dword:object=None
    price_dword:object=None
    calls:tuple=()
    missing:str=''
    requires_tail_return:bool=False
    independently_verified:bool=False

def plan_sell_selection(inventory_order,observation):
    if type(inventory_order) is not bool or not isinstance(observation,SellSelectionObservation):
        raise ValueError('Explicit order and typed selection observation required')
    o=observation;calls=[];slot=None;index=None;row=None;quantity=None
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def observed(sequence,index,label):return need(sequence[index] if index<len(sequence) else None,label)
    def item(at):
        calls.append(('004634a4',at))
        return observed(o.item_results,at-14,'slot%d fresh item EAX'%at)
    def used(at):return observed(o.used_bytes,at-14,'slot%d used BYTE'%at)
    def stable():
        if o.stable_rows is not True:raise Missing('stable prepared vector snapshot')
    def output(complete,status,missing=''):
        return SellSelectionPlan(complete,status,slot,index,row.item_dword if row else None,quantity,
            row.price_qword&0xffffffff if row else None,tuple(calls),missing,complete and status=='selected')
    try:
        if inventory_order:
            slot=o.inventory_slot_dword
            if not 14<=slot<42:raise ValueError('Caller must gate inventory slot14..41')
            item_id=item(slot)
            if item_id==0:return output(True,'unmatched') # Source short-circuits used-byte read.
            if used(slot)!=0:return output(True,'unmatched')
            stable()
            index=next((i for i,r in enumerate(o.rows) if r.item_dword==item_id),None)
            if index is None:return output(True,'unmatched')
            row=o.rows[index]
        else:
            stable();index=o.list_index_dword
            if index>=len(o.rows):raise ValueError('Caller must gate prepared row index')
            row=o.rows[index]
            for candidate in range(14,42):
                # Used byte is read only after an item ID match.
                if item(candidate)==row.item_dword and used(candidate)==0:
                    slot=candidate;break
            if slot is None:return output(True,'unmatched')
        quantity=row.quantity_dword
        calls.append(('00463538',slot))
        first=observed(o.quantity_results,0,'first fresh quantity EAX')
        if _signed(first)<_signed(quantity):
            calls.append(('00463538',slot))
            quantity=observed(o.quantity_results,1,'second fresh quantity EAX')
        return output(True,'selected')
    except Missing as error:return output(False,'needs_observation',str(error))
