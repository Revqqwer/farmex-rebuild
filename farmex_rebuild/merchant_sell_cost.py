"""4203e4 cost/count normal replay with stable rows and fresh helper sequences.

No inventory IO. Used-byte writes are prospective local plans only.
"""
from dataclasses import dataclass
from merchant_sell_selection import SellPreparedRow

def _raw(value,bits):
    if value is not None and (type(value) is not int or not 0<=value<1<<bits):raise ValueError('Raw cost-helper observation required')

def _signed(value):return value if value<0x80000000 else value-(1<<32)

@dataclass(frozen=True)
class SellCostObservation:
    inventory_order_byte:object=None
    stable_rows:object=None
    item_results:tuple=()
    quantity_results:tuple=()
    initial_count_dword:int=0
    def __post_init__(self):
        _raw(self.inventory_order_byte,8);_raw(self.initial_count_dword,32)
        if self.initial_count_dword is None:raise ValueError('Explicit initial byref counter required')
        if self.stable_rows is not None and type(self.stable_rows) is not bool:raise ValueError('Stable-row contract required')
        for sequence in (self.item_results,self.quantity_results):
            if type(sequence) is not tuple:raise ValueError('Immutable fresh-call sequence required')
            for value in sequence:_raw(value,32)

@dataclass(frozen=True)
class SellCostPlan:
    complete:bool
    cost_qword:object=None
    matched_count_dword:object=None
    prospective_cost_qword:int=0
    prospective_matched_count_dword:int=0
    prospective_used_bytes:tuple=()
    calls:tuple=()
    writes:tuple=()
    matches:tuple=() # (row index, absolute slot, chosen quantity, lowDWORD cost)
    missing:str=''
    independently_verified:bool=False

def plan_sell_cost(records,observation):
    if type(records) is not tuple or any(not isinstance(r,SellPreparedRow) for r in records) or not isinstance(observation,SellCostObservation):
        raise ValueError('Immutable prepared SELL records and typed cost observations required')
    o=observation;used=[0]*28;cost=0;count=o.initial_count_dword;calls=[];matches=[]
    writes=[(0x59+slot,0) for slot in range(14,42)]
    item_index=0;quantity_index=0
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def item(slot):
        nonlocal item_index
        i=item_index;item_index+=1;calls.append(('004634a4',slot,i))
        return need(o.item_results[i] if i<len(o.item_results) else None,'item result#%d slot%d'%(i,slot))
    def quantity(slot):
        nonlocal quantity_index
        i=quantity_index;quantity_index+=1;calls.append(('00463538',slot,i))
        return need(o.quantity_results[i] if i<len(o.quantity_results) else None,'quantity result#%d slot%d'%(i,slot))
    def size():
        calls.append(('vector_count',))
        if o.stable_rows is not True:raise Missing('stable prepared-vector snapshot')
        return len(records)
    def match(index,slot):
        nonlocal cost,count
        row=records[index];chosen=row.quantity_dword;first=quantity(slot)
        if _signed(first)<_signed(chosen):chosen=quantity(slot)
        used[slot-14]=1;writes.append((0x59+slot,1))
        low=(chosen*(row.price_qword&0xffffffff))&0xffffffff
        cost=(cost+low)&0xffffffffffffffff;count=(count+1)&0xffffffff
        matches.append((index,slot,chosen,low))
    def result(complete,missing=''):
        return SellCostPlan(complete,cost if complete else None,count if complete else None,cost,count,
            tuple(used),tuple(calls),tuple(writes),tuple(matches),missing)
    try:
        order=need(o.inventory_order_byte,'inventory-order BYTE+c8')
        if order:
            for slot in range(14,42):
                value=item(slot)
                if value==0:continue
                index=0
                while index<size():
                    if records[index].item_dword==value:
                        match(index,slot);break
                    index+=1
        else:
            index=0
            while index<size():
                row=records[index]
                for slot in range(14,42):
                    if item(slot)==row.item_dword and used[slot-14]==0:
                        match(index,slot);break
                index+=1
        return result(True)
    except Missing as error:return result(False,str(error))
