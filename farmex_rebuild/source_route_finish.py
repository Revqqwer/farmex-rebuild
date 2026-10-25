"""004f350f Change Camp/NPC/final unknown-command caller, no native IO."""
from dataclasses import dataclass,field,replace
from route_resume import RouteResumeObservation,plan_route_condition
from npc_route_engine import NpcRouteObservation

KINDS=('Change Camp','NPC')

def _raw(v,bits=32):
    if v is not None and (type(v) is not int or not 0<=v<1<<bits):raise ValueError('Raw final route observation required')

def _signed(v):return v-(1<<32) if v&(1<<31) else v

@dataclass(frozen=True)
class SourceRouteFinishObservation:
    comparisons:tuple=()
    samples:tuple=()
    reset_returned:object=None
    max_hp_dword:object=None
    hp_dword:object=None
    random_comparison_returned:object=None
    random_comparison_al:object=None
    random_helper_returned:object=None
    number_parse_returned:object=None
    number_dword:object=None
    number_helper_returned:object=None
    actor:RouteResumeObservation=field(default_factory=RouteResumeObservation)
    caller_tick_dword:object=None
    npc_copy_returned:object=None
    npc_parameter_text:object=None
    npc_return_al:object=None
    npc_observation:object=None
    def __post_init__(self):
        if type(self.comparisons) is not tuple or type(self.samples) is not tuple:raise ValueError('Ordered final-route observations required')
        for row in self.comparisons:
            if type(row) is not tuple or len(row)!=3 or row[0] not in KINDS:raise ValueError('Known final comparison tuple required')
            if row[1] is not None and type(row[1]) is not bool:raise ValueError('Explicit comparison span return required')
            _raw(row[2],8)
        for row in self.samples:
            if type(row) is not tuple or len(row)!=3 or row[1] not in (8,32):raise ValueError('Object offset/width/value required')
            if row[0] is None:raise ValueError('Known field offset required')
            _raw(row[0]);_raw(row[2],row[1])
        for name in ('reset_returned','random_comparison_returned','random_helper_returned','number_parse_returned',
                     'number_helper_returned','npc_copy_returned'):
            v=getattr(self,name)
            if v is not None and type(v) is not bool:raise ValueError('Explicit separate helper return required')
        for v in (self.max_hp_dword,self.hp_dword,self.number_dword,self.caller_tick_dword):_raw(v)
        _raw(self.random_comparison_al,8);_raw(self.npc_return_al,8)
        if self.npc_parameter_text is not None and type(self.npc_parameter_text) is not str:raise ValueError('Captured Unicode NPC parameter required')
        if self.npc_observation is not None and not isinstance(self.npc_observation,NpcRouteObservation):raise ValueError('Typed bound NPC observation required')
        if not isinstance(self.actor,RouteResumeObservation):raise ValueError('Typed NPC actor observation required')

@dataclass(frozen=True)
class SourceRouteFinishPlan:
    complete:bool
    status:str
    kind:object=None
    writes:tuple=()
    steps:tuple=()
    reads:tuple=()
    actor_plan:object=None
    npc_result:object=None
    copied_text:object=None
    health_threshold_signed:object=None
    missing:str=''
    native_execution_verified:bool=False

def plan_source_route_finish(o):
    if not isinstance(o,SourceRouteFinishObservation):raise ValueError('Typed final-route observations required')
    pos=0;kind=None;steps=[];reads=[];writes=[];actor=None;npc=None;text=None;threshold=None
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
        if pos>=len(o.samples):raise Missing('final-route object sample%d +%x'%(pos,a))
        row=o.samples[pos];pos+=1
        if row[:2]!=(a,bits):raise ValueError('Final-route object read order/width mismatch')
        reads.append(row);return need(row[2],'object value+%x'%a)
    def write(a,width,v):writes.append(('object',a,width,v));steps.append(('write',a,width,v))
    def clock():
        steps.append(('caller GetTickCount',));return need(o.caller_tick_dword,'final-route caller GetTickCount DWORD')
    def result(complete,status,missing=''):
        return SourceRouteFinishPlan(complete,status,kind,tuple(writes),tuple(steps),tuple(reads),actor,npc,text,threshold,missing)
    try:
        for i,name in enumerate(KINDS):
            if i>=len(o.comparisons):raise Missing('fresh '+name+' comparison span/AL')
            observed,returned,al=o.comparisons[i]
            if observed!=name:raise ValueError('Final route comparison order mismatch')
            normal(returned,name+' comparison/string cleanup span')
            if need(al,name+' saved AL'):
                kind=name;break
        if kind is None:
            write(0x5e8,1,0)
            return result(True,'unknown_command_processing_cleared')
        started=f(0x5f4,8)!=0
        if kind=='Change Camp':
            if started:
                now=clock();low=f(0x5f8);high=f(0x5fc)
                delta=(now-((high<<32)|low))&((1<<64)-1)
                if delta&(1<<63):delta-=1<<64
                if delta<2000:return result(True,'camp_wait')
                write(0x5f4,1,0);write(0x5e8,1,0)
                return result(True,'camp_step_cleared')
            normal(o.reset_returned,'00464714 normal return')
            steps.append(('004611c0',));product=_signed((need(o.max_hp_dword,'max HP EAX DWORD')*50)&0xffffffff)
            threshold=abs(product)//100*(-1 if product<0 else 1)
            steps.append(('004611a0',))
            if _signed(need(o.hp_dword,'HP EAX DWORD'))<threshold:return result(True,'camp_health_wait')
            normal(o.random_comparison_returned,'004f35e6..004f3633 fresh parameter/Randomize comparison cleanup')
            if need(o.random_comparison_al,'saved Randomize comparison AL'):
                normal(o.random_helper_returned,'004c8a98(00561ef8) normal return')
            else:
                normal(o.number_parse_returned,'0045ef80 fresh parameter/default0 parse normal return')
                number=need(o.number_dword,'camp parser EAX DWORD')
                if number:normal(o.number_helper_returned,'004c8698(00561ef8,%d) normal return'%number)
        elif started:
            normal(o.npc_copy_returned,'004f370c..004f3730 fresh index/Unicode608 assignment')
            text=o.npc_parameter_text
            steps.append(('004f11bc','route_object'))
            returned=o.npc_return_al
            if o.npc_observation is not None:
                if returned is not None:raise ValueError('Bound NPC helper conflicts with raw AL')
                copied=need(text,'copied Unicode NPC parameter for bound helper')
                entry=o.npc_observation.frame
                bound=replace(entry,texts={**dict(entry.texts),0x608:copied})
                npc=replace(o.npc_observation,frame=bound).step()
                if npc.status=='needs_observation':raise Missing('NPC helper: '+npc.missing)
                returned=1 if npc.returned_true else 0
            if need(returned,'NPC helper normal-return AL')==0:return result(True,'npc_pending')
            write(0x5f4,1,0);write(0x5e8,1,0)
            return result(True,'npc_step_cleared')
        else:
            actor=plan_route_condition(o.actor)
            if not actor.complete:raise Missing('NPC entry actor: '+actor.missing)
            if actor.byte_plan.eax_dword&255:return result(True,'npc_actor_blocked')
        now=clock();write(0x5f8,4,now);write(0x5fc,4,0);write(0x5f4,1,1)
        if kind=='NPC':write(0x600,4,1)
        return result(True,'npc_started' if kind=='NPC' else 'camp_started')
    except Missing as e:return result(False,'needs_observation',str(e))
