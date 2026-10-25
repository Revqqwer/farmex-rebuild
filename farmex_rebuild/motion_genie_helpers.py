"""Ordered operand models for4646b4/466cc4; no process access or native calls.

Guarded helper EAX receipts are opaque observations, not emulation of their
VirtualProtect side effect. All writes/calls below are inert plans.
"""
from dataclasses import dataclass, field, replace
from types import MappingProxyType

def _dword(v):
    if type(v) is not int or not 0<=v<=0xffffffff:
        raise ValueError('Raw helper DWORD required')

@dataclass(frozen=True)
class GuardedReadReceipt:
    address:int
    width:int
    eax:int
    normal_returned:bool
    def __post_init__(self):
        _dword(self.address);_dword(self.eax)
        if type(self.width) is not int or self.width not in (1,4) or type(self.normal_returned) is not bool:
            raise ValueError('Exact guarded helper width/normal-return receipt required')
        if self.normal_returned and self.address==0 and self.eax!=0:
            raise ValueError('Source null helper returns zero EAX')

@dataclass(frozen=True)
class MotionGenieObservation:
    global_samples:tuple=()
    guarded_reads:tuple=()
    direct_samples:tuple=()
    normal_returns:object=field(default_factory=dict)
    def __post_init__(self):
        for name in ('global_samples','direct_samples'):
            rows=getattr(self,name)
            if type(rows) is not tuple:raise ValueError('Ordered immutable observations required')
            for row in rows:
                if type(row) is not tuple or len(row)!=2:raise ValueError('Address/value pair required')
                _dword(row[0]);_dword(row[1])
        if type(self.guarded_reads) is not tuple or any(not isinstance(r,GuardedReadReceipt) for r in self.guarded_reads):
            raise ValueError('Ordered opaque guarded helper receipts required')
        returns=dict(self.normal_returns)
        if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate normal-return receipts required')
        object.__setattr__(self,'normal_returns',MappingProxyType(returns))

@dataclass(frozen=True)
class OperandRequest:
    kind:str
    index:int=0
    address:object=None
    label:str=''

@dataclass(frozen=True)
class DirectWritePlan:
    address:int
    width:int
    value:int
    label:str
    normal_return_observed:bool=False

@dataclass(frozen=True)
class IndirectCallPlan:
    target:int
    ecx:int
    push_order:tuple
    normal_return_observed:bool=False
    abi_verified:bool=False

@dataclass(frozen=True)
class MotionGeniePlan:
    helper:str
    push_order:tuple
    complete:bool
    status:str
    writes:tuple=()
    call:object=None
    steps:tuple=()
    missing:str=''
    request:object=None
    native_execution_verified:bool=False
    protection_side_effects_emulated:bool=False
    def __post_init__(self):
        if self.helper not in ('004646b4','00466cc4') or type(self.push_order) is not tuple or len(self.push_order)!=(2 if self.helper=='004646b4' else 1):
            raise ValueError('Known helper and exact physical PUSH arguments required')
        for value in self.push_order:_dword(value)
        if type(self.complete) is not bool or type(self.writes) is not tuple or any(not isinstance(w,DirectWritePlan) for w in self.writes):
            raise ValueError('Typed operand plan required')
        if self.call is not None and not isinstance(self.call,IndirectCallPlan):raise ValueError('Typed indirect call plan required')
        if self.complete and (self.request is not None or self.missing or any(not w.normal_return_observed for w in self.writes) or self.call is not None and not self.call.normal_return_observed):
            raise ValueError('Completed operand plan requires separate observed write/call returns')
    @property
    def key(self):
        return 'return_center' if self.helper=='004646b4' else ('genie_start' if self.push_order[0]&255 else 'genie_stop')

class _Missing(Exception):
    def __init__(self,request,description):self.request=request;super().__init__(description)

class _Planner:
    def __init__(self,o):
        if not isinstance(o,MotionGenieObservation):raise ValueError('Typed helper observations required')
        self.o=o;self.positions={'global':0,'guarded':0,'direct':0};self.steps=[];self.writes=[];self.call=None
    def read(self,kind,address,width=4):
        index=self.positions[kind]
        self.steps.append((kind,index,address,width))
        req=OperandRequest(kind,index,address)
        rows=getattr(self.o,{'global':'global_samples','guarded':'guarded_reads','direct':'direct_samples'}[kind])
        if index>=len(rows):raise _Missing(req,'%s[%d] at %08x'%(kind,index,address))
        row=rows[index]
        if kind=='guarded':
            if row.address!=address or row.width!=width:raise ValueError('Guarded helper address/width differs from source order')
            if not row.normal_returned:raise _Missing(req,'guarded[%d] normal return'%index)
            value=row.eax
        else:
            actual,value=row
            if actual!=address:raise ValueError('%s read address differs from source order'%kind)
        self.positions[kind]+=1
        return value
    def normal(self,label):
        self.steps.append(('normal_return',label))
        if self.o.normal_returns.get(label) is not True:raise _Missing(OperandRequest('normal',label=label),label+' normal return')
    def write(self,address,width,value,label):
        self.writes.append(DirectWritePlan(address,width,value,label,self.o.normal_returns.get(label) is True))
        self.normal(label)
    def indirect(self,target,ecx,pushes):
        self.call=IndirectCallPlan(target,ecx,pushes,self.o.normal_returns.get('indirect_target') is True)
        self.normal('indirect_target')
    def result(self,helper,pushes,error=None):
        return MotionGeniePlan(helper,pushes,error is None,'operand_span_returned' if error is None else 'needs_observation',
                               tuple(self.writes),self.call,tuple(self.steps),'' if error is None else str(error),
                               None if error is None else error.request)

def plan_movement_helper(x_bits,y_bits,o):
    """Stack args are X,Y; physical caller PUSH order is Y,X."""
    _dword(x_bits);_dword(y_bits);p=_Planner(o);pushes=(y_bits,x_bits)
    try:
        slot=p.read('global',0x553e7c)
        root=p.read('guarded',slot)
        offset=p.read('global',0x554014);p.write((root+offset)&0xffffffff,1,1,'write_moving')
        offset=p.read('global',0x554018);p.write((root+offset)&0xffffffff,4,x_bits,'write_x')
        offset=p.read('global',0x55401c);p.write((root+offset)&0xffffffff,4,y_bits,'write_y')
        offset=p.read('global',0x554020)
        state=p.read('guarded',(root+offset)&0xffffffff,1)&255
        if state!=2:
            slot=p.read('global',0x553e80)
            ecx=p.read('direct',slot)
            target=p.read('global',0x553f50)
            p.indirect(target,ecx,(1,1)) #465f30 receives1, then pushes literal1 and argument1.
        return p.result('004646b4',pushes)
    except _Missing as error:return p.result('004646b4',pushes,error)

def plan_genie_helper(argument_dword,o):
    _dword(argument_dword);p=_Planner(o);pushes=(argument_dword,)
    try:
        slot=p.read('global',0x553e80)
        root=p.read('guarded',slot)
        offset=p.read('global',0x554178)
        obj=p.read('guarded',(root+offset)&0xffffffff)
        offset=p.read('global',0x55417c)
        first=p.read('guarded',(obj+offset)&0xffffffff)
        offset=p.read('global',0x554180)
        second=p.read('guarded',(obj+offset)&0xffffffff)
        selected=first if argument_dword&255 else second
        # These are new, unchecked direct reads, not reuse of guarded EAX values.
        slot=p.read('global',0x553e80)
        root2=p.read('direct',slot)
        offset2=p.read('global',0x554178)
        ecx=p.read('direct',(root2+offset2)&0xffffffff)
        vtable_offset=p.read('global',0x554200)
        vtable=p.read('direct',ecx)
        target=p.read('direct',(vtable+vtable_offset)&0xffffffff)
        p.indirect(target,ecx,(1,selected))
        return p.result('00466cc4',pushes)
    except _Missing as error:return p.result('00466cc4',pushes,error)

class MotionGenieFrame:
    """Retain only consumed observations for one invocation, including write receipts."""
    def __init__(self,helper,push_order):
        if type(push_order) is not tuple:raise ValueError('Stable immutable physical PUSH order required')
        if helper not in ('004646b4','00466cc4') or len(push_order)!=(2 if helper=='004646b4' else 1):
            raise ValueError('Known motion/Genie helper and exact argument count required')
        for value in push_order:_dword(value)
        self.helper=helper;self.push_order=push_order;self.observation=MotionGenieObservation();self.final=None
    def _plan(self):
        if self.helper=='004646b4':return plan_movement_helper(self.push_order[1],self.push_order[0],self.observation)
        return plan_genie_helper(self.push_order[0],self.observation)
    def advance(self,o):
        if not isinstance(o,MotionGenieObservation):raise ValueError('Typed helper observations required')
        if self.final is not None:return self.final
        for _ in range(40):
            p=self._plan()
            if p.complete:self.final=p;return p
            req=p.request
            if req.kind=='normal':
                if o.normal_returns.get(req.label) is not True:return p
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,req.label:True})
            else:
                name={'global':'global_samples','guarded':'guarded_reads','direct':'direct_samples'}[req.kind]
                supplied=getattr(o,name)
                if req.index>=len(supplied):return p
                row=supplied[req.index]
                if req.kind=='guarded' and not row.normal_returned:return p
                cached=getattr(self.observation,name)
                assert req.index==len(cached)
                self.observation=replace(self.observation,**{name:cached+(row,)})
        raise ValueError('Motion/Genie frame exceeded source prefix budget')
