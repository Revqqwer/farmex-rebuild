"""004f3102 Delos Open/Gate caller and local queue; no NPC/game IO."""
from dataclasses import dataclass,field
from action_queue import QueueState,enqueue
from route_resume import RouteResumeObservation,plan_route_condition
from npc_lookup import NpcCandidate,select_npc
from source_route_finish import SourceRouteFinishObservation,plan_source_route_finish

KINDS=('Delos Gate Open','Delos Gate')
TEMPLATE=bytes.fromhex('550010373030315f64756e6765756e2e6c7561')

def _raw(v,bits=32):
    if v is not None and (type(v) is not int or not 0<=v<1<<bits):raise ValueError('Raw Delos observation required')

@dataclass(frozen=True)
class SourceDelosObservation:
    comparisons:tuple=()
    samples:tuple=() # Object(offset,bits,value).
    global_samples:tuple=() # Ordered(address,value), DWORD reads.
    actor:RouteResumeObservation=field(default_factory=RouteResumeObservation)
    interaction_actor:RouteResumeObservation=field(default_factory=RouteResumeObservation)
    lookup_span_returned:object=None
    npc_id_dword:object=None
    lookup_candidates:object=None
    lookup_complete:object=None
    npc_pointer_dword:object=None
    x_float_read_returned:object=None
    y_float_read_returned:object=None
    x_float_bits:object=None
    y_float_bits:object=None
    metric_status_ah:object=None
    move_returned:object=None
    interaction_returned:object=None
    parse_returned:object=None
    parameter_dword:object=None
    copy_returned:object=None
    origin_x_dword:object=None
    origin_y_dword:object=None
    displacement_status_ah:object=None
    queue_gate_dword:object=None
    queue_tick_dword:object=None
    queue_returned:object=None
    caller_tick_dword:object=None
    finish:object=None
    def __post_init__(self):
        if any(type(v) is not tuple for v in (self.comparisons,self.samples,self.global_samples)):raise ValueError('Ordered Delos observations required')
        for row in self.comparisons:
            if type(row) is not tuple or len(row)!=3 or row[0] not in KINDS:raise ValueError('Known Delos comparison tuple required')
            if row[1] is not None and type(row[1]) is not bool:raise ValueError('Explicit comparison return required')
            _raw(row[2],8)
        for row in self.samples:
            if type(row) is not tuple or len(row)!=3 or row[1] not in (8,32):raise ValueError('Object offset/width/value required')
            if row[0] is None:raise ValueError('Known object offset required')
            _raw(row[0]);_raw(row[2],row[1])
        for row in self.global_samples:
            if type(row) is not tuple or len(row)!=2 or row[0] is None:raise ValueError('Global address/value required')
            _raw(row[0]);_raw(row[1])
        for name in ('lookup_span_returned','lookup_complete','x_float_read_returned','y_float_read_returned','move_returned',
                     'interaction_returned','parse_returned','copy_returned','queue_returned'):
            v=getattr(self,name)
            if v is not None and type(v) is not bool:raise ValueError('Independent helper normal return required')
        for name in ('npc_id_dword','npc_pointer_dword','x_float_bits','y_float_bits','parameter_dword','origin_x_dword',
                     'origin_y_dword','queue_gate_dword','queue_tick_dword','caller_tick_dword'):_raw(getattr(self,name))
        _raw(self.metric_status_ah,8);_raw(self.displacement_status_ah,8)
        if self.lookup_candidates is not None and (type(self.lookup_candidates) is not tuple or any(not isinstance(c,NpcCandidate) for c in self.lookup_candidates)):
            raise ValueError('Typed owned NPC iterator rows required')
        if not isinstance(self.actor,RouteResumeObservation) or not isinstance(self.interaction_actor,RouteResumeObservation):raise ValueError('Two independent actor observations required')
        if self.finish is not None and not isinstance(self.finish,SourceRouteFinishObservation):raise ValueError('Typed final command continuation required')

@dataclass(frozen=True)
class SourceDelosPlan:
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
    interaction_actor_plan:object=None
    lookup:object=None
    queue_decision:object=None
    payload:object=None
    missing:str=''
    native_execution_verified:bool=False
    finish_plan:object=None

def plan_source_delos(queue,o):
    if not isinstance(queue,QueueState) or not isinstance(o,SourceDelosObservation):raise ValueError('Typed own queue/Delos observations required')
    pos=0;gpos=0;kind=None;steps=[];reads=[];writes=[];actor=None;interaction=None;lookup=None;queued=None;payload=None;candidate=queue;finish=None
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
        if pos>=len(o.samples):raise Missing('Delos object sample%d +%x'%(pos,a))
        row=o.samples[pos];pos+=1
        if row[:2]!=(a,bits):raise ValueError('Delos object read order/width mismatch')
        reads.append(('object',)+row);return need(row[2],'object value+%x'%a)
    def g(a):
        nonlocal gpos
        steps.append(('global_read',a,32))
        if gpos>=len(o.global_samples):raise Missing('Delos global sample%d at%08x'%(gpos,a))
        row=o.global_samples[gpos];gpos+=1
        if row[0]!=a:raise ValueError('Delos global read order mismatch')
        reads.append(('global',a,32,row[1]));return need(row[1],'global value at%08x'%a)
    def write(space,a,width,v):writes.append((space,a,width,v));steps.append(('write',space,a,width,v))
    def clock():
        steps.append(('caller GetTickCount',));return need(o.caller_tick_dword,'Delos caller GetTickCount DWORD')
    def result(complete,status,missing=''):
        return SourceDelosPlan(complete,status,queue,candidate if complete else queue,candidate,kind,
            tuple(writes),tuple(steps),tuple(reads),actor,interaction,lookup,queued,payload,missing,finish_plan=finish)
    try:
        for i,name in enumerate(KINDS):
            if i>=len(o.comparisons):raise Missing('fresh '+name+' comparison span/AL')
            observed,returned,al=o.comparisons[i]
            if observed!=name:raise ValueError('Delos comparison order mismatch')
            normal(returned,name+' comparison/string cleanup span')
            if need(al,name+' saved AL'):
                kind=name;break
        if kind is None:
            if o.finish is None:return result(False,'needs_command_body','Change Camp and subsequent command bodies')
            finish=plan_source_route_finish(o.finish);kind=finish.kind;actor=finish.actor_plan;writes.extend(finish.writes)
            return result(finish.complete,finish.status,finish.missing)
        if f(0x5f4,8):
            if kind=='Delos Gate':
                y=g(0x56ffbc);x=g(0x56ffb8)
                steps.append(('00460548/FUCOMPP10','signed origin DWORD y/x',
                    y-(1<<32) if y&(1<<31) else y,x-(1<<32) if x&(1<<31) else x))
                mask=need(o.displacement_status_ah,'displacement comparison AH')&0x41
                # TEST AH,41 sets parity. JP accepts greater AND unordered.
                if bin(mask).count('1')%2:return result(True,'displacement_wait_no_clock')
            now=clock();low=f(0x5f8);high=f(0x5fc)
            delta=(now-((high<<32)|low))&((1<<64)-1)
            if delta&(1<<63):delta-=1<<64
            if delta<(1000 if kind=='Delos Gate Open' else 3000):return result(True,'delos_wait')
            write('object',0x5f4,1,0);write('object',0x5e8,1,0)
            return result(True,'delos_step_cleared')
        actor=plan_route_condition(o.actor)
        if not actor.complete:raise Missing('Delos actor: '+actor.missing)
        if actor.byte_plan.eax_dword&255:return result(True,'delos_actor_blocked')
        if kind=='Delos Gate Open':
            normal(o.lookup_span_returned,'004f31e1..004f3235 Teleport Gate filter/lookup stack span')
            npc=o.npc_id_dword
            if o.lookup_candidates is not None:
                if npc is not None:raise ValueError('Bound NPC lookup conflicts with raw ID')
                lookup=select_npc(o.lookup_candidates,b'[Teleport Gate]',traversal_complete=o.lookup_complete)
                if lookup.status!='complete':raise Missing('NPC lookup: '+lookup.missing)
                npc=lookup.candidate_id
            npc=need(npc,'NPC selector EAX DWORD')
            if npc:
                steps.append(('00464a10',npc));pointer=need(o.npc_pointer_dword,'NPC pointer EAX DWORD')
                if pointer:
                    steps.append(('0045ddb8',(pointer+g(0x554008))&0xffffffff))
                    normal(o.x_float_read_returned,'NPC x getter/FSTP normal return');x=need(o.x_float_bits,'captured NPC x float bits')
                    steps.append(('0045ddb8',(pointer+g(0x554010))&0xffffffff))
                    normal(o.y_float_read_returned,'NPC y getter/FSTP normal return');y=need(o.y_float_bits,'captured NPC y float bits')
                    steps.append(('00460548','physical_push_y_x_float_bits',y,x))
                    if need(o.metric_status_ah,'NPC distance comparison AH against9')&5:
                        interaction=plan_route_condition(o.interaction_actor)
                        if not interaction.complete:raise Missing('fresh interaction actor: '+interaction.missing)
                        if interaction.byte_plan.eax_dword&255:return result(True,'interaction_actor_blocked')
                        normal(o.interaction_returned,'004c8f7c(00561ef8,NPC%d) normal return'%npc)
                    else:
                        steps.append(('004646b4','physical_push_y_x_float_bits',y,x))
                        normal(o.move_returned,'004646b4 Delos NPC normal return')
        else:
            normal(o.parse_returned,'004f3485..004f349d fresh index/parameter parse')
            value=need(o.parameter_dword,'Delos parameter EAX DWORD')
            payload=TEMPLATE[:1]+bytes((value&255,))+TEMPLATE[2:]
            normal(o.copy_returned,'memcpy low parameter BYTE to19byte local template normal return')
            steps.append(('004625ac',));write('global',0x56ffb8,4,need(o.origin_x_dword,'origin x EAX DWORD'))
            steps.append(('004625d8',));write('global',0x56ffbc,4,need(o.origin_y_dword,'origin y EAX DWORD'))
            steps.append(('004c7710',payload,19,1000))
            queued=enqueue(queue,payload,19,1000,o.queue_gate_dword,o.queue_tick_dword)
            if queued.state is None:raise Missing('Delos queue: '+(queued.missing or queued.status))
            candidate=queued.state;normal(o.queue_returned,'004c7710 Delos normal return')
        now=clock();write('object',0x5f8,4,now);write('object',0x5fc,4,0);write('object',0x5f4,1,1)
        return result(True,'delos_started')
    except Missing as e:return result(False,'needs_observation',str(e))
