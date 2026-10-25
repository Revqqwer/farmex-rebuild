"""004eb2c4 entry clocks/query outputs/Enemy gate -> existing route progress."""
from dataclasses import dataclass,field,replace
from route_resume import RouteResumeState
from route_progress import RouteProgressObservation,plan_route_progress
from route_query import RouteQueryPlan

def _raw(v,bits=32):
    if v is not None and (type(v) is not int or not 0<=v<1<<bits):raise ValueError('Raw route-entry integer required')

@dataclass(frozen=True)
class RouteEntryObservation:
    samples:tuple=() # Ordered(space,address/offset,bits,value).
    tick_samples:tuple=()
    query_returned:object=None
    query_output_bytes:tuple=(None,None,None) # locals-31,-32,-33 AFTER query.
    enemy_span_returned:object=None
    progress:RouteProgressObservation=field(default_factory=RouteProgressObservation)
    query_execution:object=None
    def __post_init__(self):
        if type(self.samples) is not tuple or type(self.tick_samples) is not tuple:raise ValueError('Ordered route-entry observations required')
        for row in self.samples:
            if type(row) is not tuple or len(row)!=4 or row[0] not in ('object','global') or row[2] not in (8,32):raise ValueError('Source space/address/width/value tuple required')
            if row[1] is None:raise ValueError('Known source address required')
            _raw(row[1]);_raw(row[3],row[2])
        for v in self.tick_samples:_raw(v)
        if type(self.query_output_bytes) is not tuple or len(self.query_output_bytes)!=3:raise ValueError('Three optional query output BYTEs required')
        for v in self.query_output_bytes:_raw(v,8)
        for v in (self.query_returned,self.enemy_span_returned):
            if v is not None and type(v) is not bool:raise ValueError('Explicit entry helper/span normal return required')
        if not isinstance(self.progress,RouteProgressObservation):raise ValueError('Typed independent progress observations required')
        if self.query_execution is not None and not isinstance(self.query_execution,RouteQueryPlan):raise ValueError('Typed bound query execution required')

@dataclass(frozen=True)
class RouteEntryDecision:
    complete:bool
    status:str
    entry_state:RouteResumeState
    state:RouteResumeState
    prospective_state:RouteResumeState
    local_bytes:tuple=(0,0,0)
    query_called:bool=False
    steps:tuple=()
    reads:tuple=()
    writes:tuple=()
    progress:object=None
    entry_queue:object=None
    queue:object=None
    prospective_queue:object=None
    missing:str=''
    native_execution_verified:bool=False
    query_execution:object=None

def plan_route_entry(state,o):
    if not isinstance(state,RouteResumeState) or not isinstance(o,RouteEntryObservation):raise ValueError('Typed route-entry state/observations required')
    pos=0;clock_pos=0;locals_=(0,0,0);queried=False;steps=[('initialize_local_bytes',0,0,0)]
    reads=[];writes=[];candidate=state;progress=None
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def read(space,a,bits=32):
        nonlocal pos
        steps.append(('read',space,a,bits))
        if pos>=len(o.samples):raise Missing('entry sample%d %s+%x'%(pos,space,a))
        row=o.samples[pos];pos+=1
        if row[:3]!=(space,a,bits):raise ValueError('Route-entry read order/width mismatch')
        reads.append(row);return need(row[3],'entry value %s+%x'%(space,a))
    def g(a,bits=32):return read('global',a,bits)
    def f(a):return read('object',a)
    def tick():
        nonlocal clock_pos
        steps.append(('GetTickCount',clock_pos))
        if clock_pos>=len(o.tick_samples):raise Missing('entry fresh GetTickCount%d'%clock_pos)
        v=o.tick_samples[clock_pos];clock_pos+=1;return need(v,'entry clock DWORD')
    def delta(now,low,high):
        value=(now-((high<<32)|low))&((1<<64)-1)
        return value-(1<<64) if value&(1<<63) else value
    def write(a,width,v):
        writes.append(('global',a,width,v));steps.append(('write','global',a,width,v))
    def result(complete,status,missing=''):
        entry_queue=progress.entry_queue if progress is not None else None
        return RouteEntryDecision(complete,status,state,candidate if complete else state,candidate,locals_,queried,
            tuple(steps),tuple(reads),tuple(writes),progress,entry_queue,
            (progress.queue if complete else entry_queue) if progress is not None else None,
            progress.prospective_queue if progress is not None else None,missing,
            query_execution=o.query_execution if queried else None)
    try:
        eligible=False
        if g(0x569100,8):
            if g(0x569108)==0:eligible=True
        if not eligible:
            if g(0x569120,8) and g(0x569130,8):eligible=True
        if eligible:
            now=tick();low=f(0x5e0);high=f(0x5e4)
            start_delta=delta(now,low,high);steps.append(('start_elapsed_signed',start_delta))
            if start_delta>=10000:
                now=tick();low=g(0x56ff8c);high=g(0x56ff90)
                poll_delta=delta(now,low,high);steps.append(('poll_elapsed_signed',poll_delta))
                if poll_delta>1000:
                    enemy_parameter=g(0x569124);anti_parameter=g(0x569104)
                    steps.append(('0046cfcc','physical_push',('local-33 ref','local-32 ref',enemy_parameter,'local-31 ref',anti_parameter,0x5690f8)))
                    queried=True;locals_=(None,None,None)
                    if o.query_execution is not None:
                        q=o.query_execution
                        if any(v is not None for v in o.query_output_bytes):raise ValueError('Bound query conflicts with raw query outputs')
                        if q.anti_radius_dword is not None and q.anti_radius_dword!=anti_parameter:raise ValueError('Bound query anti argument mismatch')
                        if q.enemy_radius_dword is not None and q.enemy_radius_dword!=enemy_parameter:raise ValueError('Bound query enemy argument mismatch')
                        if not q.complete:raise Missing('query execution: '+q.missing)
                    if o.query_returned is not True:raise Missing('0046cfcc normal return')
                    locals_=o.query_execution.output_bytes if o.query_execution is not None else o.query_output_bytes
                    now=tick();write(0x56ff8c,4,now);write(0x56ff90,4,0)
        # Source rereads both Enemy globals; earlier query eligibility values
        # cannot substitute for the later branch.
        if g(0x569120,8) and g(0x569130,8) and need(locals_[1],'query/local-32 BYTE'):
            steps.append(('normal_span','004eb3a6..004eb3dd','Enemy reload/cleanup'))
            if o.enemy_span_returned is not True:raise Missing('Enemy route reload/cleanup span normal return')
            return result(True,'enemy_reload_span_returned')
        if o.progress.anti_result_byte is not None:raise ValueError('Entry-bound local-31 conflicts with raw progress anti result')
        steps.append(('004eb3ef',))
        progress=plan_route_progress(state,replace(o.progress,anti_result_byte=locals_[0]))
        candidate=progress.prospective_state;writes.extend(progress.writes)
        if not progress.complete:raise Missing('route progress: '+progress.missing)
        return result(True,'route_entry_modeled')
    except Missing as e:return result(False,'needs_observation',str(e))
