"""004d8cd5..004d8d4a repair reply branch from supplied bytes, no game IO.

The caller must have reached this dispatch branch; earlier dispatch exits are
outside scope. Source does not bound the reads here. Missing captured bytes
remain unknown instead of reproducing an unsafe native overread.
"""
from dataclasses import dataclass,replace
from typing import Optional,Tuple
from npc_route_engine import NpcRouteFrame
from repair_refresh import RepairRefreshObservation,plan_repair_refresh

@dataclass(frozen=True)
class RepairReplyPlan:
    status:str
    complete:bool
    handled:bool=False
    reply_status:Optional[int]=None
    refresh_value:Optional[int]=None
    calls:Tuple[tuple,...]=()
    global_writes:Tuple[tuple,...]=()
    dispatch_return:Optional[int]=None
    missing:str=''
    native_execution_verified:bool=False
    server_acknowledged:bool=False
    refresh_plan:object=None

@dataclass(frozen=True)
class RepairReplyReplay:
    plan:RepairReplyPlan
    frame:NpcRouteFrame

def plan_repair_reply(captured,repair_active_byte,*,current_slot=None,refresh_returned=None,refresh_observation=None):
    if type(captured) is not bytes:raise ValueError('Immutable supplied reply bytes required')
    for value,label in ((repair_active_byte,'repair active BYTE'),(current_slot,'current slot BYTE')):
        if value is not None and (type(value) is not int or not 0<=value<=255):raise ValueError(label+' required')
    if refresh_returned is not None and type(refresh_returned) is not bool:raise ValueError('Explicit helper normal-return observation required')
    status=None;value=None;calls=[];refresh=None
    def missing(label):return RepairReplyPlan('needs_observation',False,reply_status=status,refresh_value=value,calls=tuple(calls),missing=label,refresh_plan=refresh)
    if not captured:return missing('opcode byte0')
    if captured[0]!=0x3b:return RepairReplyPlan('other_opcode',True)
    if repair_active_byte is None:return missing('global00561faa')
    if repair_active_byte==0:return RepairReplyPlan('repair_inactive',True)
    if len(captured)<2:return missing('reply status byte1')
    status=captured[1]
    if status==1:
        calls.append(('004d804f',(2,)))
        if len(captured)<6:return missing('reply DWORD bytes2..5')
        value=int.from_bytes(captured[2:6],'little')
        if current_slot is None:return missing('global00561fac')
        calls.append(('00467f10',(value,current_slot)))
        if refresh_observation is not None:
            if not isinstance(refresh_observation,RepairRefreshObservation):raise ValueError('Typed refresh observations required')
            if refresh_observation.value!=value or refresh_observation.slot!=current_slot:
                raise ValueError('Refresh observations conflict with reply value/current slot')
            refresh=plan_repair_refresh(refresh_observation)
            if not refresh.complete:return missing('refresh:'+refresh.missing)
        if refresh_returned is not True:return missing('00467f10 normal return')
    return RepairReplyPlan('reply_write_planned',True,True,status,value,tuple(calls),
        ((0x561fb0,status),),0,refresh_plan=refresh)

def replay_repair_reply(frame,captured,*,refresh_returned=None,refresh_observation=None):
    if not isinstance(frame,NpcRouteFrame):raise ValueError('Typed NPC frame required')
    plan=plan_repair_reply(captured,frame.globals.get(0x561faa),
        current_slot=frame.globals.get(0x561fac),refresh_returned=refresh_returned,refresh_observation=refresh_observation)
    accepted=frame
    if plan.complete and plan.handled:
        accepted=replace(frame,globals={**frame.globals,**dict(plan.global_writes)})
    return RepairReplyReplay(plan,accepted)
