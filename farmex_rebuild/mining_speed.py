"""0047b384 pure speed decision replay; no native calls or memory IO.

Rogue predicate supplies three fresh class DWORDs. Warrior fallback skips their
initialization in source: reached buff checks require captured stack DWORDs.
Predicate literals are known, their live string producers remain observations.
"""
from dataclasses import dataclass
from collections.abc import Mapping
from mining_configuration import MiningPanelConfiguration
from mining_scheduler import signed_elapsed

@dataclass(frozen=True)
class MiningSpeedPlan:
    status:str
    complete:bool
    calls:tuple=()
    checks:tuple=()
    writes:tuple=()
    missing:str=''
    native_execution_verified:bool=False
    server_acknowledged:bool=False

class _Missing(Exception):pass

def plan_mining_speed(configuration,observations):
    if not isinstance(configuration,MiningPanelConfiguration) or not isinstance(observations,Mapping):
        raise ValueError('Typed mining config and explicit observations required')
    calls=[];checks=[];writes=[]
    def need(key,bits=32):
        value=observations.get(key)
        if value is None:raise _Missing(key)
        if type(value) is not int or not 0<=value<(1<<bits):raise ValueError('Raw observation required: '+key)
        return value
    def done(status):return MiningSpeedPlan(status,True,tuple(calls),tuple(checks),tuple(writes))
    def call(address,*args):
        calls.append((address,args));key='returned:'+address;value=observations.get(key)
        if value is not None and type(value) is not bool:raise ValueError('Explicit normal return required')
        if value is not True:raise _Missing(key)
    def gate(skill):
        checks.append(('00464490',skill));return need('gate_464490',8)!=0
    def due():return signed_elapsed(need('retry_tick'),need('retry_qword',64))>=2000
    def buff(index,skill):
        checks.append(('00464268',skill));return need('buff_'+str(index),8)!=0
    def stamp():writes.append((0x553de8,need('retry_stamp_tick'),64))
    try:
        if need('lock_561f7e',8)!=0:return done('locked')
        if need('dead_561f6f',8)!=0:return done('actor_state_blocked')
        if need('ready_561f6e',8)==0:return done('actor_state_blocked')
        if need('blocked_561f70',8)!=0:return done('actor_state_blocked')
        if need('merchant_568d81',8)==0 and need('route_5f54',8)==0:return done('no_active_route')
        if need('actor_gate_initial')==0:return done('actor_gate_zero')
        rogue=need('rogue_predicate_505d20',8)!=0
        if rogue:
            # Source computes all three before inspecting the panel mode.
            ids=tuple((need('class_'+str(i))*1000+offset)&0xffffffff
                      for i,offset in enumerate((2,10,725),1))
            mode=configuration.fields.get(0x6048)
            if mode is None:raise _Missing('panel+6048')
            if type(mode) is not int or not 0<=mode<=0xffffffff:raise ValueError('Raw speed mode required')
            if mode==1:
                skill=2
                if gate(skill):return done('skill_gate_blocked')
            elif mode==2:
                level=need('stat_462670');level-=0x100000000 if level&0x80000000 else 0
                if level<10:return done('swift_stat_low')
                for i,value in enumerate(ids,1):
                    if buff(i,value):return done('buff_present')
                if not due():return done('retry_wait')
                if need('actor_gate_refresh')!=0:call('00464714')
                need('target_462630_first') # TEST clears CF; following JC cannot skip the next read.
                if need('target_gate_45dc44')!=0:
                    call('00465ef8',need('target_462630_second'),0)
                call('004655e8',10,need('actor_462650'))
                if need('cast_result')==0:return done('swift_cast_failed')
                writes.append((0x561f80,2000,32))
                writes.append((0x561f84,need('lock_stamp_tick'),32))
                writes.append((0x561f7e,1,8));stamp()
                return done('swift_planned')
            elif mode==3:
                level=need('stat_462e34');level-=0x100000000 if level&0x80000000 else 0
                if level<25:return done('lightfeet_stat_low')
                skill=725
                if gate(skill):return done('skill_gate_blocked')
            else:return done('unknown_mode_no_action')
        else:
            if need('warrior_predicate_505d20',8)==0:return done('no_supported_predicate')
            skill=2;ids=None
            if gate(skill):return done('skill_gate_blocked')
        if not due():return done('retry_wait')
        count=1 if rogue and mode==3 else 3
        for i in range(1,count+1):
            value=ids[i-1] if ids is not None else need('stack_uninitialized_'+str(i))
            if buff(i,value):return done('buff_present')
        call('004655e8',skill,need('actor_462650'))
        stamp() # Sprint/LightFeet/fallback ignore numeric cast return.
        return done('speed_planned')
    except _Missing as exc:
        return MiningSpeedPlan('needs_observation',False,tuple(calls),tuple(checks),tuple(writes),str(exc))
