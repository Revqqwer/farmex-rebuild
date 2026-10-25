"""42070c free-slot count and 420740 BUY gate, with optional local 41dec8 plan.

No inventory/process/VCL IO. Raw rows are observations after normal preparation;
the bound alternative derives records through merchant_preparation snapshots.
"""
from dataclasses import dataclass
from typing import Optional, Tuple
from upgrade_packets import UpgradeItemObservation, plan_upgrade_item
from merchant_preparation import (BuyPreparationObservation,BuyPreparationState,replay_buy_preparation)


def _dword(value):
    if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):
        raise ValueError('Raw DWORD observation required')


@dataclass(frozen=True)
class MerchantInventoryObservation:
    # Tuple position zero is absolute inventory slot14. None is an observation
    # gap; an observed zero EAX counts as zero even if its native cause is unknown.
    item_results:Tuple[Optional[int],...]=()
    item_inputs:Tuple[Optional[UpgradeItemObservation],...]=()

    def __post_init__(self):
        for sequence in (self.item_results,self.item_inputs):
            if type(sequence) is not tuple or len(sequence)>28:
                raise ValueError('At most28 immutable slot observations required')
        for value in self.item_results:_dword(value)
        for value in self.item_inputs:
            if value is not None and not isinstance(value,UpgradeItemObservation):
                raise ValueError('Typed captured item reads required')


@dataclass(frozen=True)
class MerchantInventoryPlan:
    complete:bool
    free_count:Optional[int]=None
    calls:tuple=()
    item_plans:tuple=()
    zero_slots:tuple=()
    missing:str=''
    independently_verified:bool=False


def plan_merchant_inventory(observation):
    if not isinstance(observation,MerchantInventoryObservation):
        raise ValueError('Typed inventory observation required')
    calls=[];plans=[];zeros=[]
    for index in range(28):
        slot=14+index;calls.append(('004634a4',slot))
        raw=observation.item_results[index] if index<len(observation.item_results) else None
        bound=observation.item_inputs[index] if index<len(observation.item_inputs) else None
        if raw is not None and bound is not None:
            raise ValueError('Raw item result conflicts with captured reads at slot%d'%slot)
        if bound is not None:
            plan=plan_upgrade_item(slot,bound);plans.append((slot,plan))
            if not plan.complete:
                return MerchantInventoryPlan(False,calls=tuple(calls),item_plans=tuple(plans),
                    zero_slots=tuple(zeros),missing='slot%d: %s'%(slot,plan.missing))
            raw=plan.result_dword
        if raw is None:
            return MerchantInventoryPlan(False,calls=tuple(calls),item_plans=tuple(plans),
                zero_slots=tuple(zeros),missing='slot%d fresh item EAX'%slot)
        if raw==0:zeros.append(slot)
    return MerchantInventoryPlan(True,len(zeros),tuple(calls),tuple(plans),tuple(zeros))


@dataclass(frozen=True)
class BuyPreparedRow:
    item_dword:int
    quantity_dword:int
    price_dword:int

    def __post_init__(self):
        for value in vars(self).values():
            _dword(value)
            if value is None:raise ValueError('Complete observed row DWORDs required')


@dataclass(frozen=True)
class BuySetupObservation:
    preparation_returned:Optional[bool]=None
    free_count:Optional[int]=None
    inventory_inputs:Optional[MerchantInventoryObservation]=None
    coins_dword:Optional[int]=None
    rows:Tuple[Optional[BuyPreparedRow],...]=()
    # Explicit stable snapshot shortcut, or one fresh vector-size result per
    # loop condition. Unknown count does not imply an empty vector.
    stable_rows:Optional[bool]=None
    vector_counts:Optional[Tuple[Optional[int],...]]=None
    preparation_inputs:Optional[BuyPreparationObservation]=None
    preparation_state:BuyPreparationState=BuyPreparationState()
    coin_inputs:object=None

    def __post_init__(self):
        if self.coin_inputs is not None:
            from source_coin import SourceCoinObservation
            if not isinstance(self.coin_inputs,SourceCoinObservation):raise ValueError('Typed BUY coin reader inputs required')
            if self.coins_dword is not None:raise ValueError('Bound BUY coin reader conflicts with raw EAX')
        if self.preparation_inputs is not None and not isinstance(self.preparation_inputs,BuyPreparationObservation):
            raise ValueError('Typed list preparation observation required')
        if not isinstance(self.preparation_state,BuyPreparationState):raise ValueError('Typed initial vector state required')
        for value in (self.preparation_returned,self.stable_rows):
            if value is not None and type(value) is not bool:raise ValueError('Boolean observation required')
        _dword(self.free_count);_dword(self.coins_dword)
        if self.free_count is not None and self.free_count>28:raise ValueError('Free count exceeds28 slots')
        if self.inventory_inputs is not None and not isinstance(self.inventory_inputs,MerchantInventoryObservation):
            raise ValueError('Typed inventory inputs required')
        if type(self.rows) is not tuple or any(row is not None and not isinstance(row,BuyPreparedRow) for row in self.rows):
            raise ValueError('Immutable post-preparation row observations required')
        if self.vector_counts is not None:
            if type(self.vector_counts) is not tuple:raise ValueError('Immutable fresh counts required')
            for value in self.vector_counts:_dword(value)
        if self.stable_rows is True and self.vector_counts is not None:
            raise ValueError('Stable vector and fresh vector counts conflict')


@dataclass(frozen=True)
class BuySetupPlan:
    complete:bool
    result_dword:Optional[int]=None
    calls:tuple=()
    inventory_plan:Optional[MerchantInventoryPlan]=None
    row_costs:tuple=()
    affordable_indices:tuple=()
    remaining_coins:Optional[int]=None
    remaining_free:Optional[int]=None
    missing:str=''
    independently_verified:bool=False
    preparation_plan:object=None
    coin_plan:object=None


def plan_buy_setup(threshold_dword,observation):
    _dword(threshold_dword)
    if threshold_dword is None or not isinstance(observation,BuySetupObservation):
        raise ValueError('Explicit DWORD threshold and typed BUY setup observation required')
    o=observation;calls=[('0041dec8',)];inventory=None;costs=[];accepted=[];coins=None;free=None;preparation=None;rows=o.rows;coin_plan=None
    def result(complete,code=None,missing=''):
        return BuySetupPlan(complete,code,tuple(calls),inventory,tuple(costs),tuple(accepted),coins,free,missing,
                            preparation_plan=preparation,coin_plan=coin_plan)
    if o.preparation_inputs is not None:
        if o.preparation_returned is not None or rows:raise ValueError('Captured preparation result/rows conflict with bound preparation')
        preparation=replay_buy_preparation(o.preparation_state,o.preparation_inputs)
        if not preparation.complete:return result(False,missing=preparation.missing)
        rows=tuple(BuyPreparedRow(row.item_dword,row.quantity_dword,row.price_qword&0xffffffff)
                   for row in preparation.state.records)
    elif o.preparation_returned is not True:
        return result(False,missing='0041dec8 normal return')
    calls.append(('0042070c',))
    if o.free_count is not None and o.inventory_inputs is not None:
        raise ValueError('Free-count result and bound inventory conflict')
    if o.inventory_inputs is not None:
        inventory=plan_merchant_inventory(o.inventory_inputs)
        if not inventory.complete:return result(False,missing=inventory.missing)
        free=inventory.free_count
    else:free=o.free_count
    if free is None:return result(False,missing='0042070c free-count EAX')
    calls.append(('0046258c',))
    coins=o.coins_dword
    if o.coin_inputs is not None:
        from source_coin import plan_source_coin
        coin_plan=plan_source_coin(o.coin_inputs)
        if not coin_plan.complete:return result(False,missing='coin reader: '+coin_plan.missing)
        coins=coin_plan.coins_dword
    if coins is None:return result(False,missing='0046258c coins EAX')
    threshold=threshold_dword if threshold_dword<0x80000000 else threshold_dword-(1<<32)
    if free<=threshold:return result(True,1)
    index=0
    while True:
        if o.stable_rows is True:count=len(rows)
        elif o.vector_counts is not None and index<len(o.vector_counts):count=o.vector_counts[index]
        else:count=None
        if count is None:return result(False,missing='fresh vector count at iteration%d'%index)
        # Source count/JA is reached before the remaining-free signed gate.
        if index>=count or free<=0:break
        if index>=len(rows) or rows[index] is None:
            return result(False,missing='post-preparation row%d'%index)
        row=rows[index]
        # IMUL generates EDX:EAX but the source immediately zeroes EDX.
        # Thus cost is the lowDWORD zero-extended, even on signed overflow.
        cost=(row.quantity_dword*row.price_dword)&0xffffffff
        costs.append((index,cost))
        if cost<=coins:
            coins-=cost;free-=1;accepted.append(index)
        index+=1
    return result(True,0 if accepted else 2)
