"""0047a61c maintenance decision replay. No game IO or native effects.

Query results are fresh per source stage. Region repair rows use recovered
constructor catalog; native pointer blobs/managed string ABI are not executed.
"""
from dataclasses import dataclass
from collections.abc import Mapping
import struct
from mining_configuration import MiningPanelConfiguration
from mining_scheduler import signed_elapsed
from mining_repair_routes import MiningRepairRoutePlan,load_mining_repair_route
from typing import Optional

@dataclass(frozen=True)
class MiningMaintenancePlan:
    status:str
    complete:bool
    calls:tuple=()
    writes:tuple=()
    missing:str=''
    native_execution_verified:bool=False
    server_acknowledged:bool=False
    repair_route:Optional[MiningRepairRoutePlan]=None

class _Missing(Exception):pass

def plan_mining_maintenance(configuration,observations):
    if not isinstance(configuration,MiningPanelConfiguration) or not isinstance(observations,Mapping):raise ValueError('Typed config and explicit observations required')
    calls=[];writes=[];hammer_stamp=None;repair_route=None
    def need(key,bits=32):
        value=observations.get(key)
        if value is None:raise _Missing(key)
        if type(value) is not int or not 0<=value<(1<<bits):raise ValueError('Raw observation required: '+key)
        return value
    def field(offset,bits=8):
        value=configuration.fields.get(offset)
        if value is None:raise _Missing('panel+%x'%offset)
        if type(value) is not int or not 0<=value<(1<<bits):raise ValueError('Raw panel field required')
        return value
    def call(address,*args):
        calls.append((address,args));key='returned:'+address;value=observations.get(key)
        if value is not None and type(value) is not bool:raise ValueError('Explicit normal return required')
        if value is not True:raise _Missing(key)
    def done(status):return MiningMaintenancePlan(status,True,tuple(calls),tuple(writes),repair_route=repair_route)
    def stop(message,title,alarm=None):
        # Symbolic literal labels describe constructed strings, not raw native ABI.
        call('00464d10',('literal',title),('literal',message))
        if alarm is not None:call('00404260',0x569568,('literal',alarm))
        call('0040ae0c',0x561f34,0)
    def signed(raw):return raw-0x100000000 if raw&0x80000000 else raw
    def coordinate(key):return struct.unpack('<f',struct.pack('<f',signed(need(key))))[0]
    try:
        if need('storage_5690b8',8)!=0:return done('storage_active')
        if need('storage_helper_4fe384',8)!=0:return done('storage_helper_active')
        if need('inn_helper_46fe90',8)!=0:return done('inn_helper_active')
        if field(0x603b)!=0:
            match=need('mattock_first_equal',8)!=0
            if not match:match=need('mattock_second_equal',8)!=0
            if (match and need('change_item_4634a4')!=0 and need('change_quantity_46358c')==0):
                slot=need('replacement_slot_477544')
                if slot!=0xffffffff:
                    call('004651bc',slot);return done('change_mattock_planned')
        if (field(0x6038)!=0 and need('hammer_item_4634a4')!=0 and need('hammer_quantity_46358c')==0):
            if need('magic_hammer_present_463950',8)!=0:
                if need('hammer_gate_4631a8',8)==0:
                    if signed_elapsed(need('hammer_tick'),need('hammer_qword',64))>=4000:
                        call('00465640',0x77ada,need('hammer_actor_462650'))
                        hammer_stamp=need('hammer_stamp_tick');writes.append((0x553de0,hammer_stamp,64))
            elif field(0x6039)!=0:
                stop(0x529364,0x52938b);return done('missing_hammer_stop_planned')
        if need('full_463ac0',8)!=0:
            vip=field(0x604c)!=0
            if vip and signed_elapsed(need('vip_tick'),need('vip_qword',64))>1000:
                writes.extend(((0x5690bc,4,32),(0x5690c0,0,8),(0x5690c1,0,8),
                    (0x5690c4,0,32),(0x5690c8,0,32),(0x5690cc,0,32),(0x5690b8,1,8)))
                return done('vip_operation4_planned')
            if field(0x6036)!=0:
                stop(0x529393 if vip else 0x5293b4,0x5293a4 if vip else 0x5293c5,
                     0x5293ac if vip else 0x5293cd)
                return done('full_alarm_stop_planned')
            if field(0x6028)!=0 and signed(need('ore_count_477770'))>0:
                call('004779dc','self');return done('ore_crash_start_planned')
        if need('repair_item_4634a4')!=0 and need('repair_quantity_46358c')==0 and field(0x6037)!=0:
            if field(0x6038)!=0:
                # The previous hammer call may have updated this exact global.
                stamp=hammer_stamp if hammer_stamp is not None else need('repair_hammer_qword',64)
                if signed_elapsed(need('repair_hammer_tick'),stamp)<4000:return done('repair_hammer_retry_wait')
            if field(0x5ff8,32)==3:
                call('004ebca0',0x5687a8,('literal',0x5293d5))
            else:
                for branch in range(1,4):
                    if need('repair_region_'+str(branch)+'_equal',8)!=0:
                        if need('repair_distance_fpu_ah',8)&0x45==0:call('00465678')
                        if need('repair_use_constructor_defaults',8)==0:
                            raise _Missing('fresh_repair_vector_capture')
                        repair_route=load_mining_repair_route(branch)
                        if not repair_route.complete:raise _Missing(repair_route.missing)
                        call('004eb9f4',0x5687a8,repair_route)
                        break
        if need('tail_gate_4631a8',8)!=0:return done('tail_gate_blocked')
        if need('tail_actor_gate_45dc44')!=0:return done('tail_actor_blocked')
        distance=signed(need('tail_distance_ftol_dword')) # observed __ftol result, not invented rounding
        if distance<2:return done('near_start')
        if need('tail_state_4677f0')==0x44:return done('tail_state44')
        if distance<50:call('004646b4',coordinate('start_x_dword'),coordinate('start_y_dword'))
        else:call('00477bd4','self')
        return done('return_start_planned')
    except _Missing as exc:
        return MiningMaintenancePlan('needs_observation',False,tuple(calls),tuple(writes),str(exc),repair_route=repair_route)
