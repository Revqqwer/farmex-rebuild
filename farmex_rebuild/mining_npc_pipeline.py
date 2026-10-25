"""Profile flags + independent mode -> existing NPC source-step replay.

Unknown projection values remove stale globals; only globals actually read by
the reached source path gate that step. complete describes one local invocation,
not the entire NPC task or any server acknowledgement.
"""
from dataclasses import dataclass,replace
from mining_configuration import MiningPanelConfiguration,MiningNpcProjection,project_mining_npc_globals
from npc_route_engine import NpcRouteFrame,NpcRouteObservation,NpcRouteResult

@dataclass(frozen=True)
class MiningNpcDecision:
    status:str
    complete:bool
    frame:NpcRouteFrame
    prospective_frame:NpcRouteFrame
    projection:MiningNpcProjection
    result:NpcRouteResult
    missing:str=''
    native_execution_verified:bool=False
    server_acknowledged:bool=False

def replay_mining_npc(configuration,observation,runtime_mode=None):
    if not isinstance(configuration,MiningPanelConfiguration) or not isinstance(observation,NpcRouteObservation):raise ValueError('Typed NPC profile and source observation required')
    projection=project_mining_npc_globals(configuration,runtime_mode)
    globals=dict(observation.frame.globals)
    for address in (0x561f58,0x56fad2,0x56fae4):globals.pop(address,None)
    globals.update(projection.globals)
    bound=replace(observation.frame,globals=globals)
    result=replace(observation,frame=bound).step()
    complete=result.status!='needs_observation'
    return MiningNpcDecision('npc_step_planned' if complete else 'needs_npc_observation',complete,
        result.frame if complete else observation.frame,result.frame,projection,result,result.missing)
