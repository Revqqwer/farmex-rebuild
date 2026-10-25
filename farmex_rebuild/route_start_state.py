"""004ead88 normal-path own state replay; helper calls remain observations."""
from dataclasses import dataclass,field
from collections.abc import Mapping
from types import MappingProxyType

RESETS=((0x5d8,1,0),(0x5d9,1,0),(0x5e0,4,0),(0x5e4,4,0),(0x5e8,1,0),
 (0x5ec,4,0xffffffff),(0x5f0,4,0),(0x5f4,1,0),(0x5f8,4,0),(0x5fc,4,0),
 (0x614,1,0),(0x618,4,14),(0x620,4,0),(0x624,4,0),(0x628,1,0),
 (0x630,4,0),(0x634,4,0),(0x638,4,0),(0x650,1,0),(0x654,4,13),
 (0x658,1,0),(0x660,4,0),(0x664,4,0),(0x688,1,0),(0x689,1,0),
 (0x68c,4,0),(0x690,4,0xffffffff),(0x694,1,0),(0x698,4,0),(0x69c,4,0),
 (0x6c0,1,0),(0x6c4,4,0),(0x6c8,1,0),(0x6d0,4,0),(0x6d4,4,0),
 (0x6d8,1,0),(0x6d9,1,0),(0x6da,1,0))
GLOBAL_RESETS=((0x561f6c,1,0),(0x56204c,1,0),(0x56203c,4,0),(0x562040,4,0))

def _dword(v,optional=False):
    if optional and v is None:return
    if type(v) is not int or not 0<=v<1<<32:raise ValueError('Raw route-start DWORD required')

@dataclass(frozen=True)
class RouteStartState:
    fields:Mapping=field(default_factory=dict)
    globals:Mapping=field(default_factory=dict)
    def __post_init__(self):
        for name,widths in (('fields',{a:w for a,w,_ in RESETS}),('globals',{a:w for a,w,_ in GLOBAL_RESETS})):
            values=getattr(self,name)
            if not isinstance(values,Mapping):raise ValueError('Own route-state mapping required')
            for a,v in values.items():
                _dword(a);_dword(v)
                if widths.get(a)==1 and v>255:raise ValueError('Raw route-state BYTE required')
            object.__setattr__(self,name,MappingProxyType(dict(values)))

@dataclass(frozen=True)
class RouteStartObservation:
    first_helper_returned:object=None
    reset_helper_returned:object=None
    tick_dword:object=None
    count_dword:object=None
    def __post_init__(self):
        for v in (self.first_helper_returned,self.reset_helper_returned):
            if v is not None and type(v) is not bool:raise ValueError('Explicit route helper normal return required')
        _dword(self.tick_dword,True);_dword(self.count_dword,True)

@dataclass(frozen=True)
class RouteStartDecision:
    complete:bool
    state:RouteStartState
    prospective_state:RouteStartState
    entry_state:RouteStartState
    steps:tuple=()
    writes:tuple=()
    missing:str=''
    independently_verified:bool=False

class RouteStartFrame:
    def __init__(self,state):
        if not isinstance(state,RouteStartState):raise ValueError('Typed own route-start state required')
        self.entry=state;self.fields=dict(state.fields);self.globals=dict(state.globals)
        self.observation=RouteStartObservation();self.stage=0;self.steps=[('004ca4c4',0x561ef8,0)]
        self.writes=[];self.done=False
    def result(self,missing=''):
        candidate=RouteStartState(self.fields,self.globals)
        return RouteStartDecision(self.done,candidate if self.done else self.entry,candidate,self.entry,
                                  tuple(self.steps),tuple(self.writes),missing)
    def step(self,o=None):
        if o is not None and not isinstance(o,RouteStartObservation):raise ValueError('Typed route-start observation required')
        if self.done:return self.result()
        a=self.observation;b=o or RouteStartObservation()
        values={}
        for name in ('first_helper_returned','reset_helper_returned','tick_dword','count_dword'):
            before=getattr(a,name);after=getattr(b,name)
            if name.endswith('returned'):
                if before is True and after is False:raise ValueError('Changed completed route helper return')
                values[name]=after if after is not None else before
            else:
                if before is not None and after is not None and before!=after:raise ValueError('Changed known route-start value')
                values[name]=before if before is not None else after
        self.observation=RouteStartObservation(**values);o=self.observation
        def write(space,address,width,value):
            (self.fields if space=='object' else self.globals)[address]=value
            self.writes.append((space,address,width,value))
        if self.stage==0:
            if o.first_helper_returned is not True:return self.result('004ca4c4 normal return')
            for address,width,value in GLOBAL_RESETS:write('global',address,width,value)
            self.steps.append(('00464714',));self.stage=1
        if self.stage==1:
            if o.reset_helper_returned is not True:return self.result('00464714 normal return')
            for address,width,value in RESETS:write('object',address,width,value)
            self.steps.append(('GetTickCount',));self.stage=2
        if self.stage==2:
            if o.tick_dword is None:return self.result('route start GetTickCount')
            write('object',0x5e0,4,o.tick_dword);write('object',0x5e4,4,0)
            self.steps.append(('read','object+88','fresh DWORD'));self.stage=3
        if o.count_dword is None:return self.result('fresh route count DWORD+88')
        write('object',0x5f0,4,o.count_dword);write('object',0x5d9,1,1)
        self.done=True;return self.result()
