"""00479d70 ->00479698 local plan composition, never a native execution claim.

complete means required model observations supplied. Existing leaf intent/state
plans assume normal helper returns, not observed native callback return or ACK.
Incomplete state is a prospective prefix; callers must not commit/re-dispatch
it as a completed invocation. The clock remains the explicit local frame model.
"""
from dataclasses import dataclass,replace
from typing import Optional
from mining_configuration import MiningPanelConfiguration,mining_runner_configuration,mining_ore_settings
from mining_engine import (MiningRunner,MiningExecutionState,MiningSnapshot,MiningTick,
    OreSlotState,OreSlotSnapshot,OreSlotTick,process_ore_slot)

@dataclass(frozen=True)
class MiningPipelineState:
    execution:MiningExecutionState
    ore:OreSlotState

    def __post_init__(self):
        if not isinstance(self.execution,MiningExecutionState) or not isinstance(self.ore,OreSlotState):raise ValueError('Typed mining state required')
        if self.execution.item_index!=self.ore.item_index:raise ValueError('One shared source item index required')

@dataclass(frozen=True)
class MiningPipelineObservation:
    outer:MiningSnapshot
    ore:Optional[OreSlotSnapshot]=None

    def __post_init__(self):
        if not isinstance(self.outer,MiningSnapshot) or (self.ore is not None and not isinstance(self.ore,OreSlotSnapshot)):
            raise ValueError('Typed outer and per-invocation ore observations required')

@dataclass(frozen=True)
class MiningPipelineDecision:
    status:str
    state:MiningPipelineState
    outer:MiningTick
    ore:Optional[OreSlotTick]
    complete:bool
    intents:tuple=()
    required_observations:tuple=()
    normal_helper_returns_assumed:bool=True
    native_callback_return_verified:bool=False
    server_acknowledged:bool=False
    independently_verified:bool=False

def replay_mining_pipeline(configuration,state,observation,now_ms):
    if not isinstance(configuration,MiningPanelConfiguration) or not isinstance(state,MiningPipelineState) or not isinstance(observation,MiningPipelineObservation):
        raise ValueError('Typed mining config/state/observation required')
    outer=MiningRunner(mining_runner_configuration(configuration)).tick(state.execution,observation.outer,now_ms)
    ore_state=replace(state.ore,item_index=outer.state.item_index)
    combined=MiningPipelineState(outer.state,ore_state)
    if outer.required_observations:
        return MiningPipelineDecision('needs_outer_observation',combined,outer,None,False,outer.intents,outer.required_observations)
    reached=any(i.source_address=='00479698' for i in outer.intents)
    if not reached:return MiningPipelineDecision('outer_phase_planned',combined,outer,None,True,outer.intents)
    settings=mining_ore_settings(configuration)
    child=process_ore_slot(ore_state,observation.ore or OreSlotSnapshot(),now_ms,settings.interval_seconds,settings.ws_enabled)
    execution=replace(outer.state,item_index=child.state.item_index)
    outer=replace(outer,state=execution)
    complete=not child.required_observations
    return MiningPipelineDecision('ore_slot_planned' if complete else 'needs_ore_observation',
        MiningPipelineState(execution,child.state),outer,child,complete,outer.intents+child.intents,
        tuple('ore.'+name for name in child.required_observations))
