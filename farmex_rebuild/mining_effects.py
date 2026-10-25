"""Compose source4779dc/477bd4 intents with their captured-data planners.

No native calls, game state commits, queue drain or ACK. Candidate snapshots
are separate per helper; supplying both a result and producer is rejected.
"""
from dataclasses import dataclass,replace
from typing import Optional
from collections.abc import Mapping
from types import MappingProxyType
from mining_transitions import MiningOreStartPlan,MiningCandidatePlan,plan_mining_ore_start,plan_mining_candidates
from mining_return import MiningReturnPlan,plan_mining_return
from mining_pipeline import MiningPipelineState
from mining_configuration import MiningPanelConfiguration

@dataclass(frozen=True)
class MiningEffectObservation:
    start:Optional[Mapping]=None
    returning:Optional[Mapping]=None
    sell_slots:Optional[Mapping]=None
    bank_slots:Optional[Mapping]=None

    def __post_init__(self):
        for name in ('start','returning','sell_slots','bank_slots'):
            value=getattr(self,name)
            if value is not None:
                if not isinstance(value,Mapping):raise ValueError('Explicit effect observations required')
                object.__setattr__(self,name,MappingProxyType(dict(value)))

@dataclass(frozen=True)
class MiningEffectPlan:
    source_address:str
    status:str
    complete:bool
    start:Optional[MiningOreStartPlan]=None
    returning:Optional[MiningReturnPlan]=None
    sell:Optional[MiningCandidatePlan]=None
    bank:Optional[MiningCandidatePlan]=None
    missing:str=''
    native_execution_verified:bool=False
    server_acknowledged:bool=False

def plan_mining_effect(address,configuration,observation=None):
    if not isinstance(configuration,MiningPanelConfiguration):raise ValueError('Typed mining panel required')
    if address not in ('004779dc','00477bd4'):raise ValueError('Known start/return source intent required')
    if observation is None:observation=MiningEffectObservation()
    if not isinstance(observation,MiningEffectObservation):raise ValueError('Typed effect observations required')
    if address=='004779dc':
        if observation.start is None:return MiningEffectPlan(address,'needs_start_observation',False,missing='start')
        plan=plan_mining_ore_start(configuration,observation.start)
        return MiningEffectPlan(address,plan.status,plan.complete,start=plan,missing=plan.missing)
    if observation.returning is None:return MiningEffectPlan(address,'needs_return_observation',False,missing='returning')
    values=dict(observation.returning);sell=None;bank=None
    for kind,slots in (('sell',observation.sell_slots),('bank',observation.bank_slots)):
        key='sell_476c7c' if kind=='sell' else 'bank_476d44'
        if slots is None:
            raw=values.get(key)
            if raw is None:return MiningEffectPlan(address,'needs_candidate_observation',False,sell=sell,bank=bank,missing=key)
            if type(raw) is not int or not 0<=raw<=255:raise ValueError('Raw observed candidate AL required')
            continue
        if key in values:raise ValueError('Choose observed candidate AL or its producer, not both')
        plan=plan_mining_candidates(kind,configuration,slots)
        if kind=='sell':sell=plan
        else:bank=plan
        if not plan.complete:return MiningEffectPlan(address,'needs_candidate_observation',False,sell=sell,bank=bank,missing=kind+'.'+plan.missing)
        values[key]=int(plan.available)
    plan=plan_mining_return(configuration,values)
    return MiningEffectPlan(address,plan.status,plan.complete,returning=plan,sell=sell,bank=bank,missing=plan.missing)

def apply_start_write_prefix(state,plan):
    """Reduce known execution fields only; physical inventory/name writes remain plans."""
    if not isinstance(state,MiningPipelineState) or not isinstance(plan,MiningOreStartPlan):raise ValueError('Typed start state/plan required')
    names={'object+5f54':'route_active','object+5f58':'phase','object+5f68':'item_index','object+5f60':'started_ms'}
    execution=state.execution
    for address,value,width in plan.writes:
        if address in names:
            execution=replace(execution,**{names[address]:bool(value) if address=='object+5f54' else value})
    return MiningPipelineState(execution,replace(state.ore,item_index=execution.item_index))
