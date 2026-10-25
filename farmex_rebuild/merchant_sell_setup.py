"""42060c normal caller: list preparation -> byref cost/count -> coins -> gate.

Cost/count come from explicit outputs or the bound 4203e4 replay, never list length.
"""
from dataclasses import dataclass
from merchant_sell_preparation import SellPreparationState,SellPreparationObservation,replay_sell_preparation
from merchant_sell_cost import SellCostObservation,plan_sell_cost
from merchant_sell_selection import SellPreparedRow

@dataclass(frozen=True)
class SellSetupObservation:
    preparation_inputs:object=None
    preparation_state:SellPreparationState=SellPreparationState()
    preparation_returned:object=None
    cost_qword:object=None
    matched_count_dword:object=None
    coins_dword:object=None
    over_limit_span_returned:object=None
    cost_inputs:object=None
    cost_rows:object=None
    coin_inputs:object=None
    def __post_init__(self):
        if self.coin_inputs is not None:
            from source_coin import SourceCoinObservation
            if not isinstance(self.coin_inputs,SourceCoinObservation):raise ValueError('Typed SELL coin reader inputs required')
            if self.coins_dword is not None:raise ValueError('Bound SELL coin reader conflicts with raw EAX')
        if self.preparation_inputs is not None and not isinstance(self.preparation_inputs,SellPreparationObservation):
            raise ValueError('Typed SELL list observations required')
        if not isinstance(self.preparation_state,SellPreparationState):raise ValueError('Typed SELL vector state required')
        if self.preparation_inputs is not None and self.preparation_returned is not None:
            raise ValueError('Bound list and opaque preparation return conflict')
        for value in (self.preparation_returned,self.over_limit_span_returned):
            if value is not None and type(value) is not bool:raise ValueError('Explicit normal-return observation required')
        for value,bits in ((self.cost_qword,64),(self.matched_count_dword,32),(self.coins_dword,32)):
            if value is not None and (type(value) is not int or not 0<=value<1<<bits):raise ValueError('Raw SELL helper result required')
        if self.cost_inputs is not None:
            if not isinstance(self.cost_inputs,SellCostObservation):raise ValueError('Typed cost-helper observations required')
            if self.cost_qword is not None or self.matched_count_dword is not None:raise ValueError('Bound cost/count conflicts with raw helper outputs')
            if self.cost_inputs.initial_count_dword!=0:raise ValueError('42060c initializes byref count to zero')
        if self.cost_rows is not None:
            if type(self.cost_rows) is not tuple or any(not isinstance(r,SellPreparedRow) for r in self.cost_rows):
                raise ValueError('Immutable explicit prepared cost rows required')
            if self.preparation_inputs is not None:raise ValueError('Bound preparation and explicit cost rows conflict')

@dataclass(frozen=True)
class SellSetupPlan:
    complete:bool
    result_dword:object=None
    calls:tuple=()
    preparation_plan:object=None
    total_qword:object=None
    signed_total:object=None
    missing:str=''
    independently_verified:bool=False
    cost_plan:object=None
    coin_plan:object=None

def plan_sell_setup(observation):
    if not isinstance(observation,SellSetupObservation):raise ValueError('Typed SELL setup observation required')
    o=observation;calls=[];prepared=None;total=None;signed=None;cost_plan=None;coin_plan=None
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def output(complete,result=None,missing=''):
        return SellSetupPlan(complete,result,tuple(calls),prepared,total,signed,missing,cost_plan=cost_plan,coin_plan=coin_plan)
    try:
        calls.append(('0041da48',))
        if o.preparation_inputs is not None:
            prepared=replay_sell_preparation(o.preparation_state,o.preparation_inputs)
            if not prepared.complete:raise Missing('SELL list: '+prepared.missing)
        elif o.preparation_returned is not True:raise Missing('0041da48 normal return')
        calls.append(('004203e4','matched_count initially0'))
        if o.cost_inputs is not None:
            rows=prepared.state.records if prepared is not None else need(o.cost_rows,'prepared cost vector')
            cost_plan=plan_sell_cost(rows,o.cost_inputs)
            if not cost_plan.complete:raise Missing('cost helper: '+cost_plan.missing)
            cost=cost_plan.cost_qword;count=cost_plan.matched_count_dword
        else:
            cost=need(o.cost_qword,'cost EDX:EAX')
            count=need(o.matched_count_dword,'post-helper byref matched count DWORD')
        calls.append(('0046258c',));coins=o.coins_dword
        if o.coin_inputs is not None:
            from source_coin import plan_source_coin
            coin_plan=plan_source_coin(o.coin_inputs)
            if not coin_plan.complete:raise Missing('coin reader: '+coin_plan.missing)
            coins=coin_plan.coins_dword
        coins=need(coins,'fresh coins EAX')
        total=(cost+coins)&0xffffffffffffffff
        signed=total if total<1<<63 else total-(1<<64)
        if count==0:return output(True,1)
        if signed>=0x7d2b74ff:
            calls.append(('normal_span','0042068b','004206e8'))
            if o.over_limit_span_returned is not True:raise Missing('over-limit string/notification span normal return')
            return output(True,2)
        return output(True,0)
    except Missing as error:return output(False,missing=str(error))
