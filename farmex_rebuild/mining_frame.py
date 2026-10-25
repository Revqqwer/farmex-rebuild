"""Pure0047b7fc ->00479d70 ->ore/name/request/queue composition.

complete is a local plan under existing normal-helper-return assumptions.
No native callback return, context preparation, send or ACK is verified.
Input state is the explicit route-helper entry state, after preceding helpers;
their state mutations are not derived from their return markers.
"""
from dataclasses import dataclass,replace
from typing import Optional
from collections.abc import Mapping
from types import MappingProxyType
from mining_configuration import MiningPanelConfiguration
from mining_scheduler import MiningSchedulePlan,plan_mining_schedule
from mining_speed import MiningSpeedPlan,plan_mining_speed
from mining_maintenance import MiningMaintenancePlan,plan_mining_maintenance
from mining_pipeline import (MiningPipelineState,MiningPipelineObservation,
    MiningPipelineDecision,replay_mining_pipeline)
from mining_slot_name import SlotNameObservation,SlotNameRequestPlan,plan_slot_name_request
from mining_requests import OreRequestQueuePlan,enqueue_ore_request
from action_queue import QueueState,QueueSample
from mining_effects import MiningEffectObservation,MiningEffectPlan,plan_mining_effect,apply_start_write_prefix

ROUTE_RETURN='returned:00479d70'
SPEED_RETURN='returned:0047b384'
MAINTENANCE_RETURN='returned:0047a61c'

@dataclass(frozen=True)
class MiningFrameState:
    pipeline:MiningPipelineState
    queue:QueueState=QueueState()

    def __post_init__(self):
        if not isinstance(self.pipeline,MiningPipelineState) or not isinstance(self.queue,QueueState):
            raise ValueError('Typed route-entry state and local queue required')

@dataclass(frozen=True)
class MiningFrameObservation:
    scheduler:Mapping
    pipeline:Optional[MiningPipelineObservation]=None
    name:Optional[SlotNameObservation]=None
    queue_samples:tuple=()
    speed:Optional[Mapping]=None
    maintenance:Optional[Mapping]=None
    post_maintenance_lock_byte:Optional[int]=None
    maintenance_effects:Optional[MiningEffectObservation]=None
    route_effects:Optional[MiningEffectObservation]=None

    def __post_init__(self):
        if not isinstance(self.scheduler,Mapping):raise ValueError('Explicit scheduler observations required')
        object.__setattr__(self,'scheduler',MappingProxyType(dict(self.scheduler)))
        object.__setattr__(self,'queue_samples',tuple(self.queue_samples))
        if any(key in self.scheduler for key in (ROUTE_RETURN,SPEED_RETURN,MAINTENANCE_RETURN)):
            raise ValueError('Route/speed/maintenance return is derived from nested local plan only')
        if self.speed is not None:
            if not isinstance(self.speed,Mapping):raise ValueError('Explicit speed observations required')
            object.__setattr__(self,'speed',MappingProxyType(dict(self.speed)))
        if self.maintenance is not None:
            if not isinstance(self.maintenance,Mapping):raise ValueError('Explicit maintenance observations required')
            object.__setattr__(self,'maintenance',MappingProxyType(dict(self.maintenance)))
            if any(key in self.maintenance for key in ('returned:004779dc','returned:00477bd4')):
                raise ValueError('Start/return helper completion is derived from nested effect plan')
        for value in (self.maintenance_effects,self.route_effects):
            if value is not None and not isinstance(value,MiningEffectObservation):raise ValueError('Separate typed effect observations required per call site')
        if self.post_maintenance_lock_byte is not None and (type(self.post_maintenance_lock_byte) is not int or not 0<=self.post_maintenance_lock_byte<=255):
            raise ValueError('Fresh post-maintenance lock BYTE required')
        if self.pipeline is not None and not isinstance(self.pipeline,MiningPipelineObservation):raise ValueError('Typed nested observation required')
        if self.name is not None and not isinstance(self.name,SlotNameObservation):raise ValueError('Typed fresh name observation required')
        if any(not isinstance(s,QueueSample) for s in self.queue_samples):raise ValueError('Typed per-enqueue observations required')

@dataclass(frozen=True)
class MiningFrameDecision:
    status:str
    complete:bool
    state:MiningFrameState
    prospective_state:MiningFrameState
    scheduler:MiningSchedulePlan
    pipeline:Optional[MiningPipelineDecision]=None
    request:Optional[SlotNameRequestPlan]=None
    queue:Optional[OreRequestQueuePlan]=None
    missing:tuple=()
    route_return_assumed_from_local_plan:bool=False
    native_execution_verified:bool=False
    server_acknowledged:bool=False
    speed:Optional[MiningSpeedPlan]=None
    speed_return_assumed_from_local_plan:bool=False
    maintenance:Optional[MiningMaintenancePlan]=None
    maintenance_return_assumed_from_local_plan:bool=False
    maintenance_effect:Optional[MiningEffectPlan]=None
    route_effect:Optional[MiningEffectPlan]=None

def replay_mining_frame(configuration,state,observation,now_ms):
    if not isinstance(configuration,MiningPanelConfiguration) or not isinstance(state,MiningFrameState) or not isinstance(observation,MiningFrameObservation):
        raise ValueError('Typed mining frame inputs required')
    if type(now_ms) is not int or now_ms<0:raise ValueError('Explicit nonnegative local frame clock required')
    schedule=plan_mining_schedule(configuration,observation.scheduler)
    candidate=state;pipeline=None;request=None;queue=None;assumed=False;speed=None;speed_assumed=False
    maintenance=None;maintenance_assumed=False
    maintenance_effect=None;route_effect=None;entry=state
    resumed=dict(observation.scheduler)
    def result(status,complete,missing=()):
        return MiningFrameDecision(status,complete,candidate if complete else state,candidate,
            schedule,pipeline,request,queue,tuple(missing),assumed,
            speed=speed,speed_return_assumed_from_local_plan=speed_assumed,
            maintenance=maintenance,maintenance_return_assumed_from_local_plan=maintenance_assumed,
            maintenance_effect=maintenance_effect,route_effect=route_effect)
    if schedule.missing==SPEED_RETURN:
        if observation.speed is None:return result('needs_speed_observation',False,('speed',))
        speed=plan_mining_speed(configuration,observation.speed)
        if not speed.complete:return result('needs_speed_observation',False,('speed.'+speed.missing,))
        resumed[SPEED_RETURN]=True;speed_assumed=True
        schedule=plan_mining_schedule(configuration,resumed)
    if schedule.missing==MAINTENANCE_RETURN:
        if observation.maintenance is None:return result('needs_maintenance_observation',False,('maintenance',))
        maintenance_values=dict(observation.maintenance)
        maintenance=plan_mining_maintenance(configuration,maintenance_values)
        if maintenance.missing in ('returned:004779dc','returned:00477bd4'):
            address=maintenance.missing.split(':')[1]
            maintenance_effect=plan_mining_effect(address,configuration,observation.maintenance_effects)
            if maintenance_effect.start is not None:
                entry=MiningFrameState(apply_start_write_prefix(entry.pipeline,maintenance_effect.start),entry.queue)
                candidate=entry
            if not maintenance_effect.complete:
                return result('needs_maintenance_effect',False,('maintenance_effect.'+maintenance_effect.missing,))
            maintenance_values['returned:'+address]=True
            maintenance=plan_mining_maintenance(configuration,maintenance_values)
        if not maintenance.complete:return result('needs_maintenance_observation',False,('maintenance.'+maintenance.missing,))
        resumed[MAINTENANCE_RETURN]=True;maintenance_assumed=True
        schedule=plan_mining_schedule(configuration,resumed)
    if (maintenance_effect is not None and maintenance_effect.start is not None and maintenance_effect.complete
            and resumed.get('route_after_mining')==0):
        return result('needs_post_start_route_flag',False,('post-start route BYTE conflicts with known route-active write',))
    if schedule.missing!=ROUTE_RETURN:
        return result('scheduler_planned' if schedule.complete else 'needs_scheduler_observation',
                      schedule.complete,() if schedule.complete else ('scheduler.'+schedule.missing,))
    if maintenance_effect is not None and maintenance_effect.start is not None:
        if now_ms>0xffffffff or entry.pipeline.execution.started_ms>now_ms:
            return result('needs_start_clock_binding',False,('source start DWORD and local frame clock',))
    if not entry.pipeline.execution.route_active:
        return result('route_entry_state_mismatch',False,('route-active source BYTE and route-entry state disagree',))
    if observation.pipeline is None:return result('needs_pipeline_observation',False,('pipeline',))
    nested=observation.pipeline
    if maintenance is not None:
        if observation.post_maintenance_lock_byte is None:
            return result('needs_post_maintenance_lock',False,('post_maintenance_lock_byte',))
        nested=replace(nested,outer=replace(nested.outer,blocked_561f7e=bool(observation.post_maintenance_lock_byte)))
    if (speed is not None and (0x561f7e,1,8) in speed.writes
            and resumed.get('merchant_after_speed')==0 and resumed.get('mining_after_merchant')==0):
        # No intervening effect helper in this observed source path: Swift's
        # known lock write reaches the route helper in the same invocation.
        nested=replace(nested,outer=replace(nested.outer,blocked_561f7e=True))
    pipeline=replay_mining_pipeline(configuration,entry.pipeline,nested,now_ms)
    candidate=MiningFrameState(pipeline.state,entry.queue)
    if not pipeline.complete:return result('needs_nested_observation',False,pipeline.required_observations)
    if any(i.name=='return_route_477bd4' for i in pipeline.intents):
        route_effect=plan_mining_effect('00477bd4',configuration,observation.route_effects)
        if not route_effect.complete:return result('needs_route_effect',False,('route_effect.'+route_effect.missing,))
    if pipeline.ore is not None:
        request=plan_slot_name_request(pipeline.ore,observation.name)
        if not request.request.complete:
            return result('needs_fresh_name_observation',False,('name.'+(request.name.missing if request.name else request.request.missing),))
        queue=enqueue_ore_request(entry.queue,request.request,observation.queue_samples)
        candidate=MiningFrameState(pipeline.state,queue.state)
        if not queue.complete:return result('needs_queue_observation',False,('queue.'+queue.missing,))
    # Replaying pure scheduler evaluation consumes no side effects twice. The
    # marker is a local normal-return assumption, not measured game execution.
    resumed[ROUTE_RETURN]=True
    schedule=plan_mining_schedule(configuration,resumed);assumed=True
    return result('frame_planned' if schedule.complete else 'needs_post_route_observation',
                  schedule.complete,() if schedule.complete else ('scheduler.'+schedule.missing,))
