"""41d518 operand plan and phase4 caller replay. No memory IO or native calls."""
from dataclasses import dataclass,replace

def _raw(value,bits,optional=False):
    if optional and value is None:return
    if type(value) is not int or not 0<=value<1<<bits:raise ValueError('Raw SELL opening field required')

@dataclass(frozen=True)
class SellNativeOpenObservation:
    global_samples:tuple=()
    protected_samples:tuple=()
    direct_samples:tuple=()
    def __post_init__(self):
        for name in ('global_samples','protected_samples','direct_samples'):
            rows=getattr(self,name)
            if type(rows) is not tuple:raise ValueError('Immutable ordered opening samples required')
            for row in rows:
                if type(row) is not tuple or len(row)!=2:raise ValueError('Address/value pair required')
                _raw(row[0],32);_raw(row[1],32,True)

@dataclass(frozen=True)
class SellNativeOpenCall:
    target_dword:int
    eax_dword:int
    ecx_dword:int
    edx_dword:int
    push_order:tuple
    stack_arguments:tuple
    required_callee_stack_pop_bytes:int=8
    abi_verified:bool=False
    executable_target_verified:bool=False

@dataclass(frozen=True)
class SellNativeOpenPlan:
    complete:bool
    reads:tuple=()
    native_call:object=None
    missing:str=''
    native_execution_verified:bool=False

def plan_sell_native_open(observation):
    if not isinstance(observation,SellNativeOpenObservation):raise ValueError('Typed ordered opening observations required')
    positions={'global':0,'protected':0,'direct':0};reads=[]
    class Missing(Exception):pass
    def word(address,kind):
        address&=0xffffffff
        sequence=getattr(observation,kind+'_samples');i=positions[kind]
        if i>=len(sequence):raise Missing('%s sample%d DWORD%08x'%(kind,i,address))
        at,value=sequence[i]
        if at!=address:raise ValueError('Opening %s sample%d address mismatch'% (kind,i))
        positions[kind]+=1;reads.append((kind,address,value))
        if value is None:raise Missing('%s sample%d value'% (kind,i))
        return value
    def g(address):return word(address,'global')
    try:
        root=word(g(0x553e80),'protected')
        container=word(root+g(0x554140),'protected')
        argument=word(container+g(0x554144),'protected')
        fresh_root=word(g(0x553e80),'direct')
        context=word(fresh_root+g(0x554140),'direct')
        method_offset=g(0x554200)
        vtable=word(context,'direct')
        target=word(vtable+method_offset,'direct')
        return SellNativeOpenPlan(True,tuple(reads),SellNativeOpenCall(target,method_offset,context,target,
            (1,argument),(argument,1)))
    except Missing as error:return SellNativeOpenPlan(False,tuple(reads),missing=str(error))

@dataclass(frozen=True)
class SellOpeningState:
    phase_dword:int=4
    prepared_slots_dword:int=0
    pending_byte:int=0
    pending_stamp_qword:int=0
    def __post_init__(self):
        for value,bits in ((self.phase_dword,32),(self.prepared_slots_dword,32),(self.pending_byte,8),(self.pending_stamp_qword,64)):_raw(value,bits)

@dataclass(frozen=True)
class SellOpeningObservation:
    opening_tick_dword:object=None
    native_inputs:object=None
    helper_returned:object=None
    empty_span_returned:object=None
    def __post_init__(self):
        _raw(self.opening_tick_dword,32,True)
        if self.native_inputs is not None and not isinstance(self.native_inputs,SellNativeOpenObservation):raise ValueError('Typed opening operands required')
        for value in (self.helper_returned,self.empty_span_returned):
            if value is not None and type(value) is not bool:raise ValueError('Explicit normal-return observations required')

@dataclass(frozen=True)
class SellOpeningDecision:
    complete:bool
    status:str
    state:SellOpeningState
    prospective_state:SellOpeningState
    native_plan:object=None
    calls:tuple=()
    writes:tuple=()
    missing:str=''
    independently_verified:bool=False

def _known(before,after,label):
    if before is None:return after
    if after is not None and before!=after:raise ValueError('Changed known opening observation: '+label)
    return before

def _normal(before,after):
    if before is True and after is False:raise ValueError('Changed completed opening normal return')
    return True if before is True else (after if after is not None else before)

def _merge_inputs(before,after):
    if before is None:return after
    if after is None:return before
    fields={}
    for name in ('global_samples','protected_samples','direct_samples'):
        a=getattr(before,name);b=getattr(after,name);rows=[]
        for i in range(max(len(a),len(b))):
            if i>=len(a):rows.append(b[i])
            elif i>=len(b):rows.append(a[i])
            else:
                if a[i][0]!=b[i][0]:raise ValueError('Changed opening sample address')
                rows.append((a[i][0],_known(a[i][1],b[i][1],name+' value')))
        fields[name]=tuple(rows)
    return SellNativeOpenObservation(**fields)

class SellOpeningFrame:
    def __init__(self,state):
        if not isinstance(state,SellOpeningState) or state.phase_dword!=4:raise ValueError('Reached phase4 opening state required')
        self.entry=state;self.candidate=state;self.observation=SellOpeningObservation()
        self.calls=[];self.writes=[];self.stage=0;self.native_plan=None;self.done=False
        signed=state.prepared_slots_dword if state.prepared_slots_dword<1<<31 else state.prepared_slots_dword-(1<<32)
        self.empty=signed<=0
    def _result(self,missing=''):
        status=('no_sale_slots' if self.empty else 'opening_returned') if self.done else 'needs_observation'
        return SellOpeningDecision(self.done,status,self.candidate if self.done else self.entry,self.candidate,
            self.native_plan,tuple(self.calls),tuple(self.writes),missing)
    def step(self,observation=None):
        if observation is not None and not isinstance(observation,SellOpeningObservation):raise ValueError('Typed opening observation required')
        if self.done:return self._result()
        a=self.observation;b=observation or SellOpeningObservation()
        self.observation=SellOpeningObservation(_known(a.opening_tick_dword,b.opening_tick_dword,'clock'),
            _merge_inputs(a.native_inputs,b.native_inputs),_normal(a.helper_returned,b.helper_returned),
            _normal(a.empty_span_returned,b.empty_span_returned));o=self.observation
        if self.empty:
            if self.stage==0:
                self.calls.extend((('0040ae0c',0x561f34,0),('normal_span','00421bb8','00421c24')));self.stage=1
            if o.empty_span_returned is not True:return self._result('empty-slots stop/string span normal return')
            self.done=True;return self._result()
        if self.stage==0:
            self.candidate=replace(self.candidate,pending_byte=1);self.writes.append((0x48,1,1))
            self.calls.append(('GetTickCount',));self.stage=1
        if self.stage==1:
            if o.opening_tick_dword is None:return self._result('opening GetTickCount')
            self.candidate=replace(self.candidate,pending_stamp_qword=o.opening_tick_dword)
            self.writes.append((0x50,8,o.opening_tick_dword));self.calls.append(('0041d518',));self.stage=2
        if self.stage==2:
            self.native_plan=plan_sell_native_open(o.native_inputs or SellNativeOpenObservation())
            if not self.native_plan.complete:return self._result(self.native_plan.missing)
            self.stage=3
        if self.stage==3:
            if o.helper_returned is not True:return self._result('0041d518 normal return, operand plan is not execution')
            self.candidate=replace(self.candidate,phase_dword=5);self.writes.append((4,4,5));self.done=True
        return self._result()
