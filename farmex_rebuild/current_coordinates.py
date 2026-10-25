"""Captured current-coordinate getters004625ac/d8; no process/API execution.

Each axis independently rereads global553e7c, guarded DWORD root and its own
offset, then guarded float and __ftol. Native normal-return receipts and EAX
are explicit; float bits alone never fabricate a conversion/parent return.
"""
from dataclasses import dataclass,replace
from source_coin import GuardedDwordSample,plan_guarded_dword
from merchant_result_rows import format_source_coordinate


def raw(value,optional=True):
    if value is None and optional:return
    if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw coordinate DWORD required')


@dataclass(frozen=True)
class GuardedFloatSample:
    address:int
    protection_return_dword:object=None
    float32_bits:object=None
    def __post_init__(self):
        raw(self.address,False);raw(self.protection_return_dword);raw(self.float32_bits)


@dataclass(frozen=True)
class GuardedFloatPlan:
    complete:bool
    bits:object=None
    steps:tuple=()
    missing:str=''
    native_effects_verified:bool=False


def plan_guarded_float(address,sample=None):
    raw(address,False)
    if sample is not None and not isinstance(sample,GuardedFloatSample):raise ValueError('Typed guarded float sample required')
    if sample is not None and sample.address!=address:raise ValueError('Guarded float address mismatch')
    if address==0:return GuardedFloatPlan(True,0)
    steps=(('VirtualProtect_plan',address,4,0x40),)
    if sample is None or sample.protection_return_dword is None:return GuardedFloatPlan(False,steps=steps,missing='float protection return')
    if sample.protection_return_dword==0:return GuardedFloatPlan(True,0,steps)
    steps+=(('float_read_plan',address,4),)
    if sample.float32_bits is None:return GuardedFloatPlan(False,steps=steps,missing='float32 value bits')
    return GuardedFloatPlan(True,sample.float32_bits,steps)


@dataclass(frozen=True)
class CurrentAxisObservation:
    root_address_dword:object=None
    root_sample:object=None
    root_returned:object=None
    offset_dword:object=None
    float_sample:object=None
    float_returned:object=None
    ftol_returned:object=None
    ftol_eax:object=None
    axis_returned:object=None
    def __post_init__(self):
        for value in (self.root_address_dword,self.offset_dword,self.ftol_eax):raw(value)
        if self.root_sample is not None and not isinstance(self.root_sample,GuardedDwordSample):raise ValueError('Typed root sample required')
        if self.float_sample is not None and not isinstance(self.float_sample,GuardedFloatSample):raise ValueError('Typed float sample required')
        for value in (self.root_returned,self.float_returned,self.ftol_returned,self.axis_returned):
            if value is not None and type(value) is not bool:raise ValueError('Separate normal-return bool required')


@dataclass(frozen=True)
class CurrentAxisPlan:
    complete:bool
    axis:str
    steps:tuple=()
    root:object=None
    address:object=None
    float_bits:object=None
    eax:object=None
    missing:str=''
    native_execution_verified:bool=False
    needed:object=None


def plan_current_axis(axis,o):
    if axis not in ('x','y') or not isinstance(o,CurrentAxisObservation):raise ValueError('Known axis and typed observations required')
    steps=[];root=None;address=None;bits=None;eax=None
    def out(ok,missing='',needed=None):return CurrentAxisPlan(ok,axis,tuple(steps),root,address,bits,eax,missing,needed=needed)
    steps.append(('global',0x553e7c))
    if o.root_address_dword is None:return out(False,'root address global',('root_address_dword',))
    p=plan_guarded_dword(o.root_address_dword,o.root_sample);steps.append(('0045dc44',o.root_address_dword,p))
    if not p.complete:
        field='protection_return_dword' if o.root_sample is None or o.root_sample.protection_return_dword is None else 'value_dword'
        return out(False,p.missing,('root_sample',field))
    if o.root_returned is not True:return out(False,'root helper normal return',('root_returned',))
    root=p.value_dword
    steps.append(('global',0x554008 if axis=='x' else 0x554010))
    if o.offset_dword is None:return out(False,'axis offset global',('offset_dword',))
    address=(root+o.offset_dword)&0xffffffff
    p=plan_guarded_float(address,o.float_sample);steps.append(('0045ddb8',address,p))
    if not p.complete:
        field='protection_return_dword' if o.float_sample is None or o.float_sample.protection_return_dword is None else 'float32_bits'
        return out(False,p.missing,('float_sample',field))
    bits=p.bits
    if o.float_returned is not True:return out(False,'float helper normal return',('float_returned',))
    steps.append(('CC32260MT.DLL:__ftol',bits))
    if o.ftol_returned is not True:return out(False,'ftol normal return',('ftol_returned',))
    if o.ftol_eax is None:return out(False,'ftol EAX lowDWORD',('ftol_eax',))
    eax=o.ftol_eax
    if o.axis_returned is not True:return out(False,'coordinate helper parent return',('axis_returned',))
    return out(True)


@dataclass(frozen=True)
class CurrentCoordinatesPlan:
    complete:bool
    axes:tuple
    eax_prefix:tuple=()
    parameters:object=None
    missing:str=''
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


def plan_current_coordinates(x=None,y=None):
    """One captured replay, not an asynchronous polling frame or UI binding."""
    axes=[];values=[]
    for axis,o in (('x',x),('y',y)):
        p=plan_current_axis(axis,CurrentAxisObservation() if o is None else o);axes.append(p)
        if not p.complete:return CurrentCoordinatesPlan(False,tuple(axes),tuple(values),missing=axis+': '+p.missing)
        values.append(p.eax)
    return CurrentCoordinatesPlan(True,tuple(axes),tuple(values),tuple(format_source_coordinate(value) for value in values))


class CurrentAxisFrame:
    """One invocation: freeze only demanded values and true normal receipts."""
    def __init__(self,axis):
        if axis not in ('x','y'):raise ValueError('Known current-coordinate axis required')
        self.axis=axis;self.observation=CurrentAxisObservation();self.final=None
    def advance(self,incoming=None):
        if self.final is not None:return self.final
        incoming=CurrentAxisObservation() if incoming is None else incoming
        if not isinstance(incoming,CurrentAxisObservation):raise ValueError('Typed axis capture required')
        for _ in range(20):
            p=plan_current_axis(self.axis,self.observation)
            if p.complete:self.final=p;return p
            path=p.needed
            if path is None:raise ValueError('Unresolved axis phase without demand')
            if len(path)==1:
                field=path[0];value=getattr(incoming,field)
                if value is None or field.endswith('_returned') and value is not True:return p
                self.observation=replace(self.observation,**{field:value})
            else:
                group,field=path;sample=getattr(incoming,group)
                if sample is None:return p
                address=self.observation.root_address_dword if group=='root_sample' else p.address
                if sample.address!=address:raise ValueError('Reached axis sample address mismatch')
                value=getattr(sample,field)
                if value is None:return p
                current=getattr(self.observation,group)
                if current is None:
                    current=GuardedDwordSample(address) if group=='root_sample' else GuardedFloatSample(address)
                self.observation=replace(self.observation,**{group:replace(current,**{field:value})})
        raise ValueError('Own axis advancement budget exhausted')


class CurrentCoordinatesFrame:
    """X before fresh Y; completed X cannot be overwritten while Y waits."""
    def __init__(self):
        self.x=CurrentAxisFrame('x');self.y=CurrentAxisFrame('y');self.final=None
    def advance(self,x=None,y=None):
        if self.final is not None:return self.final
        axes=[];values=[]
        for frame,incoming in ((self.x,x),(self.y,y)):
            p=frame.advance(incoming);axes.append(p)
            if not p.complete:return CurrentCoordinatesPlan(False,tuple(axes),tuple(values),missing=p.axis+': '+p.missing)
            values.append(p.eax)
        self.final=CurrentCoordinatesPlan(True,tuple(axes),tuple(values),tuple(format_source_coordinate(value) for value in values))
        return self.final
