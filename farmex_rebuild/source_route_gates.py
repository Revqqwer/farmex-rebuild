"""004f2d31 Gate Skill/Open/Gate scoped queue/caller replay; no game IO."""
from dataclasses import dataclass,field
from action_queue import QueueState,enqueue
from route_resume import RouteResumeObservation,plan_route_condition
from source_route_delos import SourceDelosObservation,plan_source_delos

KINDS=('Gate Skill','Gate Open','Gate')
WAITS={'Gate Skill':3000,'Gate Open':1500,'Gate':3000}

def _raw(value,bits=32):
    if value is not None and (type(value) is not int or not 0<=value<1<<bits):raise ValueError('Raw gate observation required')

@dataclass(frozen=True)
class SourceRouteGatesObservation:
    comparisons:tuple=() # Ordered(kind,span normal-return,saved AL).
    samples:tuple=() # Object(offset,bits,value).
    actor:RouteResumeObservation=field(default_factory=RouteResumeObservation)
    helper_returned:object=None
    parse_returned:object=None
    parameter_dword:object=None
    copy_returned:object=None
    queue_state:QueueState=field(default_factory=QueueState)
    queue_gate_dword:object=None
    queue_tick_dword:object=None
    queue_returned:object=None
    caller_tick_dword:object=None
    delos:object=None
    def __post_init__(self):
        if type(self.comparisons) is not tuple or type(self.samples) is not tuple:raise ValueError('Ordered gate observations required')
        for row in self.comparisons:
            if type(row) is not tuple or len(row)!=3 or row[0] not in KINDS:raise ValueError('Typed gate comparison tuple required')
            if row[1] is not None and type(row[1]) is not bool:raise ValueError('Explicit comparison span normal return required')
            _raw(row[2],8)
        for row in self.samples:
            if type(row) is not tuple or len(row)!=3 or row[1] not in (8,32):raise ValueError('Object offset/width/value required')
            if row[0] is None:raise ValueError('Known field offset required')
            _raw(row[0]);_raw(row[2],row[1])
        for value in (self.helper_returned,self.parse_returned,self.copy_returned,self.queue_returned):
            if value is not None and type(value) is not bool:raise ValueError('Independent gate helper normal return required')
        for value in (self.parameter_dword,self.queue_gate_dword,self.queue_tick_dword,self.caller_tick_dword):_raw(value)
        if not isinstance(self.actor,RouteResumeObservation) or not isinstance(self.queue_state,QueueState):raise ValueError('Typed actor and owned queue required')
        if self.delos is not None and not isinstance(self.delos,SourceDelosObservation):raise ValueError('Typed Delos continuation required')

@dataclass(frozen=True)
class SourceRouteGatesPlan:
    complete:bool
    status:str
    entry_queue:QueueState
    queue:QueueState
    prospective_queue:QueueState
    kind:object=None
    writes:tuple=()
    steps:tuple=()
    reads:tuple=()
    actor_plan:object=None
    queue_decision:object=None
    payload:object=None
    missing:str=''
    native_execution_verified:bool=False
    delos_plan:object=None

def plan_source_route_gates(o):
    if not isinstance(o,SourceRouteGatesObservation):raise ValueError('Typed gate inputs required')
    pos=0;steps=[];reads=[];writes=[];kind=None;actor=None;queued=None;payload=None;candidate=o.queue_state;delos=None
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def normal(v,label):
        steps.append(('normal_return',label))
        if v is not True:raise Missing(label)
    def f(a,bits=32):
        nonlocal pos
        steps.append(('object_read',a,bits))
        if pos>=len(o.samples):raise Missing('gate object sample%d +%x'%(pos,a))
        row=o.samples[pos];pos+=1
        if row[:2]!=(a,bits):raise ValueError('Gate object read order/width mismatch')
        reads.append(row);return need(row[2],'object value+%x'%a)
    def write(a,width,value):
        writes.append(('object',a,width,value));steps.append(('write',a,width,value))
    def clock():
        steps.append(('caller GetTickCount',));return need(o.caller_tick_dword,'gate caller GetTickCount DWORD')
    def result(complete,status,missing=''):
        return SourceRouteGatesPlan(complete,status,o.queue_state,candidate if complete else o.queue_state,candidate,
            kind,tuple(writes),tuple(steps),tuple(reads),actor,queued,payload,missing,delos_plan=delos)
    try:
        for i,name in enumerate(KINDS):
            steps.append(('comparison_span',name))
            if i>=len(o.comparisons):raise Missing('fresh '+name+' comparison span/AL')
            observed,returned,al=o.comparisons[i]
            if observed!=name:raise ValueError('Source gate comparison order mismatch')
            normal(returned,name+' comparison/string cleanup span')
            if need(al,name+' saved comparison AL'):
                kind=name;break
        if kind is None:
            if o.delos is None:return result(False,'needs_command_body','Delos Gate Open and subsequent commands')
            delos=plan_source_delos(o.queue_state,o.delos);candidate=delos.prospective_queue;writes.extend(delos.writes)
            kind=delos.kind;actor=delos.actor_plan;queued=delos.queue_decision;payload=delos.payload
            return result(delos.complete,delos.status,delos.missing)
        if f(0x5f4,8):
            now=clock();low=f(0x5f8);high=f(0x5fc)
            delta=(now-((high<<32)|low))&((1<<64)-1)
            if delta&(1<<63):delta-=1<<64
            if delta<WAITS[kind]:return result(True,'gate_wait')
            write(0x5f4,1,0);write(0x5e8,1,0)
            return result(True,'gate_step_cleared')
        actor=plan_route_condition(o.actor)
        if not actor.complete:raise Missing('gate actor: '+actor.missing)
        if actor.byte_plan.eax_dword&255:return result(True,'gate_actor_blocked')
        if kind=='Gate Skill':
            normal(o.helper_returned,'004c8d84(00561ef8) normal return')
        else:
            normal(o.parse_returned,kind+' fresh index/parameter parser normal return')
            value=need(o.parameter_dword,kind+' parameter EAX DWORD')
            payload=(b'\x33' if kind=='Gate Open' else b'\x4b')+value.to_bytes(4,'little')
            normal(o.copy_returned,'memcpy parameter DWORD to5byte local template normal return')
            steps.append(('004c7710',payload,5,0))
            queued=enqueue(o.queue_state,payload,5,0,o.queue_gate_dword,o.queue_tick_dword)
            if queued.state is None:raise Missing('gate queue: '+(queued.missing or queued.status))
            candidate=queued.state
            normal(o.queue_returned,'004c7710 gate normal return')
        now=clock();write(0x5f8,4,now);write(0x5fc,4,0);write(0x5f4,1,1)
        return result(True,'gate_started')
    except Missing as e:return result(False,'needs_observation',str(e))
