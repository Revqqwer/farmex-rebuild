"""004f276c cursor/Town/coordinate/Bekle/posture/Gate scopes; no native IO."""
from dataclasses import dataclass
from route_start_state import RouteStartState
from source_route_coordinate import RouteCoordinateObservation,plan_route_coordinate
from source_route_commands import SourceRouteCommandsObservation,plan_source_route_commands

def _raw(value,bits=32):
    if value is not None and (type(value) is not int or not 0<=value<1<<bits):raise ValueError('Raw route-step integer required')

def _signed(value,bits=32):return value-(1<<bits) if value&(1<<(bits-1)) else value

@dataclass(frozen=True)
class SourceRouteStepObservation:
    samples:tuple=() # Fresh object reads (offset,bits,value), including return index.
    comparison_span_returned:object=None
    comparison_al:object=None
    reset_helper_returned:object=None
    max_hp_dword:object=None
    hp_dword:object=None
    town_helper_returned:object=None
    tick_dword:object=None
    coordinate:object=None
    commands:object=None
    def __post_init__(self):
        if type(self.samples) is not tuple:raise ValueError('Ordered route object samples required')
        for row in self.samples:
            if type(row) is not tuple or len(row)!=3 or row[1] not in (8,32):raise ValueError('Object offset/width/value tuple required')
            if row[0] is None:raise ValueError('Known object offset required')
            _raw(row[0]);_raw(row[2],row[1])
        for value in (self.comparison_span_returned,self.reset_helper_returned,self.town_helper_returned):
            if value is not None and type(value) is not bool:raise ValueError('Separate explicit helper normal return required')
        _raw(self.comparison_al,8)
        for value in (self.max_hp_dword,self.hp_dword,self.tick_dword):_raw(value)
        if self.coordinate is not None and not isinstance(self.coordinate,RouteCoordinateObservation):raise ValueError('Typed bound coordinate inputs required')
        if self.commands is not None and not isinstance(self.commands,SourceRouteCommandsObservation):raise ValueError('Typed bound remaining commands required')

@dataclass(frozen=True)
class SourceRouteStepPlan:
    complete:bool
    status:str
    entry_state:RouteStartState
    state:RouteStartState
    prospective_state:RouteStartState
    return_dword:object=None
    steps:tuple=()
    reads:tuple=()
    writes:tuple=()
    health_threshold_signed:object=None
    missing:str=''
    native_execution_verified:bool=False
    coordinate_plan:object=None
    command_plan:object=None
    entry_queue:object=None
    queue:object=None
    prospective_queue:object=None

def plan_source_route_step(state,o):
    if not isinstance(state,RouteStartState) or not isinstance(o,SourceRouteStepObservation):raise ValueError('Typed route step state/observations required')
    fields=dict(state.fields);globals_state=dict(state.globals);pos=0;steps=[];reads=[];writes=[];threshold=None;coordinate_plan=None;command_plan=None
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def f(offset,bits=32):
        nonlocal pos
        steps.append(('object_read',offset,bits))
        if pos>=len(o.samples):raise Missing('fresh object sample%d +%x'%(pos,offset))
        row=o.samples[pos];pos+=1
        if row[:2]!=(offset,bits):raise ValueError('Source route object read order/width mismatch')
        reads.append(row);return need(row[2],'object value+%x'%offset)
    def normal(value,label):
        steps.append(('normal_return',label))
        if value is not True:raise Missing(label)
    def write(offset,width,value):
        fields[offset]=value;writes.append(('object',offset,width,value));steps.append(('write',offset,width,value))
    def result(complete,status,value=None,missing=''):
        candidate=RouteStartState(fields,globals_state)
        gate=command_plan.gate_plan if command_plan is not None else None
        return SourceRouteStepPlan(complete,status,state,candidate if complete else state,candidate,value,
            tuple(steps),tuple(reads),tuple(writes),threshold,missing,coordinate_plan=coordinate_plan,command_plan=command_plan,
            entry_queue=gate.entry_queue if gate is not None else None,
            queue=(gate.queue if complete else gate.entry_queue) if gate is not None else None,
            prospective_queue=gate.prospective_queue if gate is not None else None)
    def finish(status):
        # Both early cursor return and common epilogue perform a fresh read.
        return result(True,status,f(0x5ec))
    try:
        if f(0x5e8,8)==0:
            last=(f(0x5f0)-1)&0xffffffff
            if last==f(0x5ec):return finish('cursor_at_last')
            index=(f(0x5ec)+1)&0xffffffff # INC reads memory independently.
            write(0x5ec,4,index);write(0x5e8,1,1);write(0x5f4,1,0)
            write(0x5f8,4,0);write(0x5fc,4,0)
            return finish('cursor_armed')
        normal(o.comparison_span_returned,'004f27f9..004f2846 Town string/comparison/cleanup span')
        if need(o.comparison_al,'saved Town comparison AL')==0:
            if o.coordinate is None:return result(False,'needs_command_body',missing='non-Town command dispatcher/body')
            coordinate_plan=plan_route_coordinate(o.coordinate)
            if not coordinate_plan.complete:
                if coordinate_plan.status!='needs_command_body' or o.commands is None:
                    return result(False,coordinate_plan.status,missing='coordinate: '+coordinate_plan.missing)
                command_plan=plan_source_route_commands(o.commands)
                for space,offset,width,value in command_plan.writes:
                    if space=='object':write(offset,width,value)
                    elif space=='global':
                        globals_state[offset]=value;writes.append((space,offset,width,value));steps.append(('global_write',offset,width,value))
                    else:raise ValueError('Unknown source command write space')
                if not command_plan.complete:return result(False,command_plan.status,missing='commands: '+command_plan.missing)
                return finish(command_plan.status)
            if coordinate_plan.clear_processing:write(0x5e8,1,0)
            return finish(coordinate_plan.status)
        if f(0x5f4,8):
            steps.append(('GetTickCount',))
            tick=need(o.tick_dword,'Town wait GetTickCount DWORD')
            low=f(0x5f8);high=f(0x5fc)
            delta=_signed((tick-((high<<32)|low))&((1<<64)-1),64)
            if delta<2000:return finish('town_wait')
            write(0x5f4,1,0);write(0x5e8,1,0)
            return finish('town_step_cleared')
        normal(o.reset_helper_returned,'00464714 normal return')
        steps.append(('004611c0',))
        product=_signed((need(o.max_hp_dword,'max HP helper EAX DWORD')*50)&0xffffffff)
        threshold=abs(product)//100*(-1 if product<0 else 1)
        steps.append(('004611a0',))
        if _signed(need(o.hp_dword,'HP helper EAX DWORD'))<threshold:return finish('town_health_wait')
        normal(o.town_helper_returned,'004c8604(00561ef8) normal return')
        steps.append(('GetTickCount',))
        write(0x5f8,4,need(o.tick_dword,'Town start GetTickCount DWORD'));write(0x5fc,4,0)
        write(0x5f4,1,1)
        return finish('town_started')
    except Missing as e:return result(False,'needs_observation',missing=str(e))
