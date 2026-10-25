"""0047b7fc ordered caller replay. Explicit observations, no game IO.

Fresh stage keys model re-reads after helper calls. Calls must have explicit
normal-return observations before following source effects can be planned.
Incomplete writes/calls are a prospective prefix, not a committed invocation.
"""
from dataclasses import dataclass
from collections.abc import Mapping
from mining_configuration import MiningPanelConfiguration

@dataclass(frozen=True)
class MiningSchedulePlan:
    status:str
    complete:bool
    calls:tuple=()
    writes:tuple=()
    missing:str=''
    native_execution_verified:bool=False
    server_acknowledged:bool=False

class _Missing(Exception):pass

def signed_elapsed(tick,stamp):
    """Source zero-extended DWORD minus QWORD, interpreted as signed64."""
    value=(tick-stamp)&0xffffffffffffffff
    return value-(1<<64) if value&(1<<63) else value

def plan_mining_schedule(configuration,observations):
    if not isinstance(configuration,MiningPanelConfiguration) or not isinstance(observations,Mapping):
        raise ValueError('Typed config and explicit per-stage observations required')
    calls=[];writes=[]
    def need(key,bits=32):
        value=observations.get(key)
        if value is None:raise _Missing(key)
        if type(value) is not int or not 0<=value<(1<<bits):raise ValueError('Raw value required: '+key)
        return value
    def field(offset,bits=8):
        value=configuration.fields.get(offset)
        if value is None:raise _Missing('panel+%x'%offset)
        if type(value) is not int or not 0<=value<(1<<bits):raise ValueError('Raw panel field required')
        return value
    def call(address,*args):
        calls.append((address,args))
        key='returned:'+address
        value=observations.get(key)
        if value is not None and type(value) is not bool:raise ValueError('Explicit normal return required')
        if value is not True:raise _Missing(key)
    def done(status):return MiningSchedulePlan(status,True,tuple(calls),tuple(writes))
    def due(prefix,threshold):
        return signed_elapsed(need(prefix+'_tick'),need(prefix+'_qword',64))>=threshold
    def stamp(prefix,address):writes.append((address,need(prefix+'_stamp_tick'),0))
    try:
        if need('active_initial',8)==0:return done('inactive')
        if need('dead',8)!=0:
            if field(0x603c)==0:return done('dead_respawn_disabled')
            death=need('death_qword',64)
            if death==0:return done('dead_no_timestamp')
            threshold=(field(0x6040,32)*1000+3000)&0xffffffff
            threshold-=0x100000000 if threshold&0x80000000 else 0
            if signed_elapsed(need('respawn_wait_tick'),death)<threshold:return done('respawn_wait')
            if not due('respawn_retry',1000):return done('respawn_retry_wait')
            call('004c8d48',0x561ef8);stamp('respawn',0x553df0)
            return done('respawn_planned')
        if field(0x6047)!=0:call('0047b384','self')
        if need('merchant_after_speed',8)!=0:call('004eb2a8',0x5687a8)
        if need('mining_after_merchant',8)!=0:call('0047a61c','self')
        if need('route_after_mining',8)!=0:call('00479d70','self')
        if need('active_after_route',8)==0:return done('inactive_after_helpers')
        if need('mining_after_route',8)==0:return done('mining_inactive_after_helpers')
        if need('actor_gate_45dc44')!=0:return done('actor_gate_nonzero')
        if need('helper_4631a8',8)!=0:return done('helper_gate_nonzero')
        if need('control_5fe0_25',8)!=0 and need('helper_463950',8)!=0:
            if not due('item_retry',2000):return done('item_retry_wait')
            call('004c8290',0x561ef8);stamp('item',0x553df8)
            return done('item_planned')
        if not due('normal_retry',5000):return done('normal_retry_wait')
        if (need('helper_4634a4')!=0 and need('helper_46358c')!=0
                and need('helper_463ac0',8)==0 and need('helper_4677f0')==0x44):
            call('004c806c',0x561ef8,1)
        # The source stamps this five-second check even if a predicate fails.
        stamp('normal',0x553e00)
        return done('normal_check_planned')
    except _Missing as exc:
        return MiningSchedulePlan('needs_observation',False,tuple(calls),tuple(writes),str(exc))
