"""Reached004f28f9 coordinate comparison/body, captured local float bits."""
from dataclasses import dataclass
from source_coin import GuardedDwordSample,plan_guarded_dword

def _raw(value,bits=32):
    if value is not None and (type(value) is not int or not 0<=value<1<<bits):raise ValueError('Raw coordinate observation required')

@dataclass(frozen=True)
class RouteCoordinateObservation:
    comparison_span_returned:object=None
    comparison_al:object=None
    global_samples:tuple=() # Ordered(address,width,value).
    root_sample:object=None
    value_sample:object=None
    parse_span_returned:object=None
    x_float_bits:object=None
    y_float_bits:object=None
    metric_status_ah:object=None
    move_returned:object=None
    def __post_init__(self):
        if type(self.global_samples) is not tuple:raise ValueError('Ordered global samples required')
        for row in self.global_samples:
            if type(row) is not tuple or len(row)!=3 or row[1] not in (8,32):raise ValueError('Address/width/value global tuple required')
            if row[0] is None:raise ValueError('Known source address required')
            _raw(row[0]);_raw(row[2],row[1])
        for value in (self.comparison_span_returned,self.parse_span_returned,self.move_returned):
            if value is not None and type(value) is not bool:raise ValueError('Explicit coordinate helper/span normal return required')
        for value in (self.root_sample,self.value_sample):
            if value is not None and not isinstance(value,GuardedDwordSample):raise ValueError('Typed guarded DWORD sample required')
        for value in (self.comparison_al,self.metric_status_ah):_raw(value,8)
        _raw(self.x_float_bits);_raw(self.y_float_bits)

@dataclass(frozen=True)
class RouteCoordinatePlan:
    complete:bool
    status:str
    clear_processing:bool=False
    steps:tuple=()
    reads:tuple=()
    guarded_plans:tuple=()
    missing:str=''
    native_execution_verified:bool=False

def plan_route_coordinate(o):
    if not isinstance(o,RouteCoordinateObservation):raise ValueError('Typed coordinate observations required')
    steps=[];reads=[];guards=[];pos=0
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def normal(value,label):
        steps.append(('normal_return',label))
        if value is not True:raise Missing(label)
    def g(address,bits=32):
        nonlocal pos
        steps.append(('global_read',address,bits))
        if pos>=len(o.global_samples):raise Missing('coordinate global sample%d at%08x'%(pos,address))
        row=o.global_samples[pos];pos+=1
        if row[:2]!=(address,bits):raise ValueError('Coordinate global read order/width mismatch')
        reads.append(row);return need(row[2],'coordinate global value at%08x'%address)
    def guarded(address,sample):
        p=plan_guarded_dword(address&0xffffffff,sample);guards.append(p);steps.append(('0045dc44',address&0xffffffff))
        if not p.complete:raise Missing(p.missing)
        return p.value_dword
    def result(complete,status,clear=False,missing=''):
        return RouteCoordinatePlan(complete,status,clear,tuple(steps),tuple(reads),tuple(guards),missing)
    try:
        normal(o.comparison_span_returned,'004f28f9..004f2947 coordinate comparison/string cleanup span')
        if need(o.comparison_al,'saved coordinate comparison AL')==0:
            return result(False,'needs_command_body',missing='dispatcher/body after coordinate comparison')
        if g(0x561f7e,8):return result(True,'coordinate_locked')
        root=guarded(g(0x553e7c),o.root_sample)
        value=guarded((root+g(0x554034))&0xffffffff,o.value_sample)
        if value==6:return result(True,'coordinate_field_exact6')
        normal(o.parse_span_returned,'004f29a7..004f29da fresh indices/text/float conversion span')
        x=need(o.x_float_bits,'captured local x float bits');y=need(o.y_float_bits,'captured local y float bits')
        steps.append(('00460548','physical_push_y_x_float_bits',y,x))
        ah=need(o.metric_status_ah,'coordinate metric comparison AH against2.0')
        if ah&0x45:
            return result(True,'coordinate_step_clear',True)
        # Same captured stack locals feed movement. Unlike route_motion,
        # source does not reread coordinate strings after the metric helper.
        steps.append(('004646b4','physical_push_y_x_float_bits',y,x))
        normal(o.move_returned,'004646b4 coordinate normal return')
        return result(True,'coordinate_move_returned')
    except Missing as e:return result(False,'needs_observation',missing=str(e))
