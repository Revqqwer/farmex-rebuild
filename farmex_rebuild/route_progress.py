"""Reached004eb3ef caller through progress/arrival gates into route_motion."""
from dataclasses import dataclass,field
from route_resume import RouteResumeState
from route_motion import RouteMotionObservation,plan_route_motion
from source_random import SourceRandomObservation,replay_source_random
from source_route_step import SourceRouteStepPlan

def _raw(v,bits=32):
    if v is not None and (type(v) is not int or not 0<=v<1<<bits):raise ValueError('Raw route progress integer required')

def _signed(v,bits=32):return v-(1<<bits) if v&(1<<(bits-1)) else v

@dataclass(frozen=True)
class RouteProgressObservation:
    # Ordered fresh reads: (object/global, offset/address, bit width, value).
    samples:tuple=()
    tick_samples:tuple=()
    request_returns:tuple=() # Separate normal returns for004eaf94 calls.
    step_return_dword:object=None
    anti_result_byte:object=None # Earlier local-31 producer remains external.
    anti_route_span_returned:object=None
    metric_status_ah:object=None
    random_return_dword:object=None
    random_observation:object=None
    motion:RouteMotionObservation=field(default_factory=RouteMotionObservation)
    step_execution:object=None
    def __post_init__(self):
        if type(self.samples) is not tuple or type(self.tick_samples) is not tuple or type(self.request_returns) is not tuple:
            raise ValueError('Ordered immutable progress observations required')
        for row in self.samples:
            if type(row) is not tuple or len(row)!=4:raise ValueError('Typed source read tuple required')
            space,address,bits,value=row
            if space not in ('object','global') or bits not in (8,32):raise ValueError('Known source read space/width required')
            if address is None:raise ValueError('Known source address required')
            _raw(address);_raw(value,bits)
        for v in self.tick_samples:_raw(v)
        for v in self.request_returns:
            if v is not None and type(v) is not bool:raise ValueError('Explicit request helper normal return required')
        _raw(self.step_return_dword);_raw(self.random_return_dword)
        _raw(self.anti_result_byte,8);_raw(self.metric_status_ah,8)
        if self.anti_route_span_returned is not None and type(self.anti_route_span_returned) is not bool:
            raise ValueError('Explicit AntiCR span normal return required')
        if self.random_observation is not None and not isinstance(self.random_observation,SourceRandomObservation):raise ValueError('Typed RNG helper inputs required')
        if not isinstance(self.motion,RouteMotionObservation):raise ValueError('Typed independent motion observations required')
        if self.step_execution is not None and not isinstance(self.step_execution,SourceRouteStepPlan):raise ValueError('Typed source step execution required')

@dataclass(frozen=True)
class RouteProgressDecision:
    complete:bool
    status:str
    state:RouteResumeState
    prospective_state:RouteResumeState
    steps:tuple=()
    reads:tuple=()
    writes:tuple=()
    motion:object=None
    random_plan:object=None
    missing:str=''
    live_compatibility_verified:bool=False
    step_execution:object=None
    entry_queue:object=None
    queue:object=None
    prospective_queue:object=None

def plan_route_progress(state,o):
    if not isinstance(state,RouteResumeState) or not isinstance(o,RouteProgressObservation):raise ValueError('Typed route progress inputs required')
    pos=0;clock_pos=0;request_pos=0;steps=[];reads=[];writes=[];candidate=state;motion=None;random_plan=None;step_reached=False
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def read(space,address,bits=32):
        nonlocal pos
        steps.append(('read',space,address,bits))
        if pos>=len(o.samples):raise Missing('read sample%d %s+%x'%(pos,space,address))
        row=o.samples[pos];pos+=1
        if row[:3]!=(space,address,bits):raise ValueError('Route progress source read order/width mismatch')
        reads.append(row);return need(row[3],'read value %s+%x'%(space,address))
    def f(address,bits=32):return read('object',address,bits)
    def g(address,bits=32):return read('global',address,bits)
    def write(space,address,width,value):
        writes.append((space,address,width,value));steps.append(('write',space,address,width,value))
    def tick():
        nonlocal clock_pos
        steps.append(('GetTickCount',clock_pos))
        if clock_pos>=len(o.tick_samples):raise Missing('fresh GetTickCount sample%d'%clock_pos)
        v=o.tick_samples[clock_pos];clock_pos+=1;return need(v,'GetTickCount DWORD')
    def elapsed():
        now=tick();low=g(0x56ff94);high=g(0x56ff98)
        return _signed((now-((high<<32)|low))&((1<<64)-1),64)
    def request():
        nonlocal request_pos
        steps.append(('004eaf94','route_object',request_pos))
        if request_pos>=len(o.request_returns) or o.request_returns[request_pos] is not True:
            raise Missing('004eaf94 normal return%d'%request_pos)
        request_pos+=1
        now=tick();write('global',0x56ff94,4,now);write('global',0x56ff98,4,0)
    def result(complete,status,missing=''):
        execution=o.step_execution if step_reached else None
        return RouteProgressDecision(complete,status,candidate if complete else state,candidate,
            tuple(steps),tuple(reads),tuple(writes),motion,random_plan,missing,step_execution=execution,
            entry_queue=execution.entry_queue if execution is not None else None,
            queue=(execution.queue if complete else execution.entry_queue) if execution is not None else None,
            prospective_queue=execution.prospective_queue if execution is not None else None)
    def into_motion():
        nonlocal candidate,motion
        steps.append(('004eb6a6',))
        motion=plan_route_motion(state,o.motion);candidate=motion.prospective_state
        writes.extend(motion.writes)
        if not motion.complete:raise Missing('motion: '+motion.missing)
        return result(True,'motion_modeled')
    def either_flag():return f(0x566,8)!=0 or f(0x567,8)!=0
    try:
        # The guard and comparison read index5ec independently.
        if either_flag() and _signed(f(0x5ec))>=0:
            index=_signed(f(0x5ec));limit=_signed(f(0x544))
            if index>limit and f(0x6d9,8)==0 and f(0x6da,8)==0:
                write('object',0x6d9,1,1)
                if elapsed()>=5000:request()
        steps.append(('004f276c','route_object'))
        step_reached=True
        returned=o.step_return_dword
        if o.step_execution is not None:
            if returned is not None:raise ValueError('Bound route step conflicts with raw helper return')
            writes.extend(o.step_execution.writes)
            if not o.step_execution.complete:raise Missing('route step: '+o.step_execution.missing)
            returned=o.step_execution.return_dword
        returned=need(returned,'route-step helper normal-return EAX DWORD')
        last=(f(0x5f0)-1)&0xffffffff
        if returned!=last:return result(True,'step_not_last_no_motion')
        if f(0x5e8,8):return result(True,'step_processing_no_motion')
        if g(0x561f58)!=0:return into_motion()
        if g(0x569100,8) and g(0x569108)==0 and need(o.anti_result_byte,'earlier local-31 BYTE'):
            steps.append(('normal_span','004eb4dc..004eb513','AntiCR'))
            if o.anti_route_span_returned is not True:raise Missing('AntiCR route/reload cleanup span normal return')
            return result(True,'anti_cr_route_returned')
        if not either_flag():
            write('global',0x56ff9c,4,0);write('global',0x56ffa0,4,0);write('global',0x56ffa4,4,0)
            return into_motion()
        if f(0x6d9,8):
            if f(0x6da,8):return into_motion()
            # FILD/FSTP argument conversion and metric helper remain opaque;
            # supplied AH is after comparison with exact disk constant50.0.
            y=g(0x562004);x=g(0x562000)
            steps.append(('00460548/FUCOMPP50','physical_push_y_x_signed_dwords',_signed(y),_signed(x)))
            ah=need(o.metric_status_ah,'metric FUCOMPP status AH')
            if ah&0x45==0:
                if elapsed()>=5000:request()
                return result(True,'metric_greater_wait_return')
            write('object',0x6d9,1,0);write('object',0x6da,1,1)
            now=tick();write('global',0x56ff9c,4,now);write('global',0x56ffa0,4,0)
            steps.append(('00467cc4',2000,7000))
            value=o.random_return_dword
            if o.random_observation is not None:
                if value is not None:raise ValueError('Bound random helper conflicts with raw return')
                random_plan=replay_source_random(2000,7000,o.random_observation)
                if not random_plan.complete:raise Missing('arrival RNG: '+(random_plan.missing or random_plan.status))
                value=random_plan.result_dword
            write('global',0x56ffa4,4,need(value,'arrival random helper EAX DWORD'))
            return result(True,'arrival_delay_armed')
        if f(0x6da,8):return into_motion()
        write('object',0x6d9,1,1)
        if elapsed()>=5000:request()
        return result(True,'request_wait_return')
    except Missing as e:return result(False,'needs_observation',str(e))
