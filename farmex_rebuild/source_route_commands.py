"""Reached004f2a1e Bekle and Otur/Kalk pair; native calls stay observations."""
from dataclasses import dataclass,field
from route_resume import RouteResumeObservation,plan_route_condition
from source_route_gates import SourceRouteGatesObservation,plan_source_route_gates

def _raw(value,bits=32):
    if value is not None and (type(value) is not int or not 0<=value<1<<bits):raise ValueError('Raw route command integer required')

def _signed(v,bits=32):return v-(1<<bits) if v&(1<<(bits-1)) else v

@dataclass(frozen=True)
class SourceRouteCommandsObservation:
    samples:tuple=() # Object(offset,bits,value), only reached reads.
    wait_comparison_returned:object=None
    wait_comparison_al:object=None
    seconds_parse_returned:object=None
    seconds_dword:object=None
    posture_predicate_returned:object=None
    posture_match_byte:object=None # Source OR/SETNZ normalizes this to0/1.
    actor:RouteResumeObservation=field(default_factory=RouteResumeObservation)
    sit_comparison_returned:object=None
    sit_comparison_al:object=None
    sit_returned:object=None
    stand_comparison_returned:object=None
    stand_comparison_al:object=None
    stand_returned:object=None
    tick_dword:object=None
    gates:object=None
    def __post_init__(self):
        if type(self.samples) is not tuple:raise ValueError('Ordered object samples required')
        for row in self.samples:
            if type(row) is not tuple or len(row)!=3 or row[1] not in (8,32):raise ValueError('Object offset/width/value tuple required')
            if row[0] is None:raise ValueError('Known object offset required')
            _raw(row[0]);_raw(row[2],row[1])
        for name in ('wait_comparison_returned','seconds_parse_returned','posture_predicate_returned',
                     'sit_comparison_returned','sit_returned','stand_comparison_returned','stand_returned'):
            v=getattr(self,name)
            if v is not None and type(v) is not bool:raise ValueError('Separate explicit normal-return receipt required')
        for v in (self.wait_comparison_al,self.sit_comparison_al,self.stand_comparison_al):_raw(v,8)
        if self.posture_match_byte is not None and (type(self.posture_match_byte) is not int or self.posture_match_byte not in (0,1)):
            raise ValueError('Normalized posture predicate BYTE0/1 required')
        _raw(self.seconds_dword);_raw(self.tick_dword)
        if not isinstance(self.actor,RouteResumeObservation):raise ValueError('Typed fresh actor condition required')
        if self.gates is not None and not isinstance(self.gates,SourceRouteGatesObservation):raise ValueError('Typed bound gates required')

@dataclass(frozen=True)
class SourceRouteCommandsPlan:
    complete:bool
    status:str
    writes:tuple=()
    steps:tuple=()
    reads:tuple=()
    actor_plan:object=None
    threshold_signed:object=None
    elapsed_signed:object=None
    missing:str=''
    native_execution_verified:bool=False
    gate_plan:object=None

def plan_source_route_commands(o):
    if not isinstance(o,SourceRouteCommandsObservation):raise ValueError('Typed remaining command observations required')
    pos=0;steps=[];reads=[];writes=[];actor=None;threshold=None;elapsed=None;gate_plan=None
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def normal(value,label):
        steps.append(('normal_return',label))
        if value is not True:raise Missing(label)
    def f(address,bits=32):
        nonlocal pos
        steps.append(('object_read',address,bits))
        if pos>=len(o.samples):raise Missing('object sample%d +%x'%(pos,address))
        row=o.samples[pos];pos+=1
        if row[:2]!=(address,bits):raise ValueError('Source route command read order/width mismatch')
        reads.append(row);return need(row[2],'object value+%x'%address)
    def write(address,width,value):
        writes.append(('object',address,width,value));steps.append(('write',address,width,value))
    def tick():
        steps.append(('GetTickCount',));return need(o.tick_dword,'command GetTickCount DWORD')
    def result(complete,status,missing=''):
        return SourceRouteCommandsPlan(complete,status,tuple(writes),tuple(steps),tuple(reads),actor,threshold,elapsed,missing,gate_plan=gate_plan)
    try:
        normal(o.wait_comparison_returned,'004f2a1e..004f2a6c Bekle comparison/string cleanup')
        wait=need(o.wait_comparison_al,'saved Bekle comparison AL')!=0
        if not wait:
            normal(o.posture_predicate_returned,'004f2b1b..004f2bcb Otur-or-Kalk comparison/cleanup')
            if need(o.posture_match_byte,'normalized Otur-or-Kalk match')==0:
                if o.gates is None:return result(False,'needs_command_body',missing='Gate Skill and subsequent command bodies')
                gate_plan=plan_source_route_gates(o.gates);writes.extend(gate_plan.writes)
                return result(gate_plan.complete,gate_plan.status,gate_plan.missing)
        started=f(0x5f4,8)!=0
        if started:
            if wait:
                normal(o.seconds_parse_returned,'004f2a81..004f2a99 fresh index/seconds parse')
                threshold=_signed((need(o.seconds_dword,'seconds parser EAX DWORD')*1000)&0xffffffff)
            else:threshold=2000
            now=tick();low=f(0x5f8);high=f(0x5fc)
            elapsed=_signed((now-((high<<32)|low))&((1<<64)-1),64)
            if elapsed<threshold:return result(True,'command_wait')
            write(0x5f4,1,0);write(0x5e8,1,0)
            return result(True,'command_step_cleared')
        if not wait:
            actor=plan_route_condition(o.actor)
            if not actor.complete:raise Missing('posture actor: '+actor.missing)
            if actor.byte_plan.eax_dword&255:return result(True,'posture_actor_blocked')
            normal(o.sit_comparison_returned,'004f2c5c..004f2caa fresh Otur comparison/cleanup')
            if need(o.sit_comparison_al,'fresh Otur comparison AL'):
                normal(o.sit_returned,'00465de0 normal return')
            normal(o.stand_comparison_returned,'004f2cb4..004f2d02 fresh Kalk comparison/cleanup')
            if need(o.stand_comparison_al,'fresh Kalk comparison AL'):
                normal(o.stand_returned,'00465e50 normal return')
        now=tick();write(0x5f8,4,now);write(0x5fc,4,0);write(0x5f4,1,1)
        return result(True,'command_started')
    except Missing as e:return result(False,'needs_observation',str(e))
