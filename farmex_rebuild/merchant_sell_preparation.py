"""41da48 SELL normal list preparation, sharing the proved BUY algorithm."""
from dataclasses import dataclass
from merchant_preparation import (BuyPreparedRecord,BuyPreparationState,BuyPreparationRow,
    BuyPreparationObservation,_replay_list_preparation)
from merchant_sell_selection import SellPreparedRow

SELL_LIST_PATH='frmMain/MainTab/sheetSellMerchant/GroupBox19/LwAutoSellMerchant'
# Both source bodies use the same per-row normal helper/cleanup observation contract.
SellPreparationRow=BuyPreparationRow
SellPreparationObservation=BuyPreparationObservation

@dataclass(frozen=True)
class SellPreparationState:
    records:tuple=()
    def __post_init__(self):
        if type(self.records) is not tuple or any(not isinstance(r,SellPreparedRow) for r in self.records):
            raise ValueError('Immutable observed SELL prepared records required')

@dataclass(frozen=True)
class SellPreparationPlan:
    complete:bool
    state:SellPreparationState
    prospective_state:SellPreparationState
    calls:tuple
    missing:str=''
    partial_fields:tuple=()
    price_plan:object=None
    independently_verified:bool=False

def replay_sell_preparation(state,observation):
    if not isinstance(state,SellPreparationState) or not isinstance(observation,SellPreparationObservation):
        raise ValueError('Typed SELL state and common list observations required')
    temporary=BuyPreparationState(tuple(BuyPreparedRecord(r.item_dword,r.quantity_dword,r.price_qword) for r in state.records))
    plan=_replay_list_preparation(temporary,observation,SELL_LIST_PATH)
    def convert(s):return SellPreparationState(tuple(SellPreparedRow(r.item_dword,r.quantity_dword,r.price_qword) for r in s.records))
    return SellPreparationPlan(plan.complete,convert(plan.state),convert(plan.prospective_state),plan.calls,
                               plan.missing,plan.partial_fields,plan.price_plan)
