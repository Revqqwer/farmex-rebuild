"""Coin and guarded DWORD/BYTE own replay; never executes VirtualProtect/reads."""
from dataclasses import dataclass

def _raw(value,optional=False):
    if optional and value is None:return
    if type(value) is not int or not 0<=value<1<<32:raise ValueError('Raw source coin DWORD required')

@dataclass(frozen=True)
class GuardedDwordSample:
    address:int
    protection_return_dword:object=None
    value_dword:object=None
    def __post_init__(self):
        _raw(self.address);_raw(self.protection_return_dword,True);_raw(self.value_dword,True)

@dataclass(frozen=True)
class GuardedDwordPlan:
    complete:bool
    status:str
    value_dword:object=None
    steps:tuple=()
    missing:str=''
    native_effects_verified:bool=False

def plan_guarded_dword(address,sample=None):
    _raw(address)
    if sample is not None and not isinstance(sample,GuardedDwordSample):raise ValueError('Typed guarded sample required')
    if sample is not None and sample.address!=address:raise ValueError('Guarded DWORD sample address mismatch')
    if address==0:return GuardedDwordPlan(True,'null_returns_zero',0)
    steps=(('VirtualProtect_plan',address,4,0x40),)
    if sample is None or sample.protection_return_dword is None:
        return GuardedDwordPlan(False,'needs_observation',steps=steps,missing='VirtualProtect raw return for%08x'%address)
    if sample.protection_return_dword==0:return GuardedDwordPlan(True,'protection_failure_returns_zero',0,steps)
    steps+=(('read_plan',address,4),)
    if sample.value_dword is None:return GuardedDwordPlan(False,'needs_observation',steps=steps,missing='guarded DWORD value for%08x'%address)
    return GuardedDwordPlan(True,'value_observed',sample.value_dword,steps)

@dataclass(frozen=True)
class GuardedByteSample:
    address:int
    protection_return_dword:object=None
    value_byte:object=None
    def __post_init__(self):
        _raw(self.address);_raw(self.protection_return_dword,True)
        if self.value_byte is not None and (type(self.value_byte) is not int or not 0<=self.value_byte<256):raise ValueError('Raw guarded BYTE required')

@dataclass(frozen=True)
class GuardedBytePlan:
    complete:bool
    status:str
    eax_dword:object=None
    value_byte:object=None
    steps:tuple=()
    missing:str=''
    native_effects_verified:bool=False

def plan_guarded_byte(address,sample=None):
    _raw(address)
    if sample is not None and not isinstance(sample,GuardedByteSample):raise ValueError('Typed guarded byte sample required')
    if sample is not None and sample.address!=address:raise ValueError('Guarded BYTE sample address mismatch')
    if address==0:return GuardedBytePlan(True,'null_returns_zero',0)
    steps=(('VirtualProtect_plan',address,1,0x40),)
    if sample is None or sample.protection_return_dword is None:
        return GuardedBytePlan(False,'needs_observation',steps=steps,missing='byte VirtualProtect raw return for%08x'%address)
    if sample.protection_return_dword==0:return GuardedBytePlan(True,'protection_failure_returns_zero',0,steps=steps)
    steps+=(('read_plan',address,1),)
    if sample.value_byte is None:return GuardedBytePlan(False,'needs_observation',steps=steps,missing='guarded BYTE value for%08x'%address)
    # MOV AL,[ECX] retains the upper24bits of the API return in EAX.
    eax=(sample.protection_return_dword&0xffffff00)|sample.value_byte
    return GuardedBytePlan(True,'value_observed',eax,sample.value_byte,steps)

@dataclass(frozen=True)
class SourceCoinObservation:
    global_samples:tuple=()
    guarded_samples:tuple=()
    def __post_init__(self):
        if type(self.global_samples) is not tuple or type(self.guarded_samples) is not tuple:raise ValueError('Ordered immutable coin samples required')
        for row in self.global_samples:
            if type(row) is not tuple or len(row)!=2:raise ValueError('Coin global address/value pair required')
            _raw(row[0]);_raw(row[1],True)
        if any(not isinstance(s,GuardedDwordSample) for s in self.guarded_samples):raise ValueError('Typed guarded DWORD samples required')

@dataclass(frozen=True)
class SourceCoinPlan:
    complete:bool
    coins_dword:object=None
    global_reads:tuple=()
    helper_calls:tuple=()
    guarded_plans:tuple=()
    missing:str=''
    independently_verified:bool=False

def plan_source_coin(o):
    if not isinstance(o,SourceCoinObservation):raise ValueError('Typed source coin observation required')
    globals_read=[];calls=[];plans=[];gpos=0;spos=0
    class Missing(Exception):pass
    def g(address):
        nonlocal gpos
        if gpos>=len(o.global_samples):raise Missing('coin global sample%d at%08x'%(gpos,address))
        at,value=o.global_samples[gpos];gpos+=1
        if at!=address:raise ValueError('Coin global sample address mismatch')
        globals_read.append((at,value))
        if value is None:raise Missing('coin global value at%08x'%at)
        return value
    def guarded(address):
        nonlocal spos
        address&=0xffffffff;calls.append(('0045dc44',address))
        sample=None
        # A null helper argument returns0 before the API and consumes no API observation.
        if address:
            sample=o.guarded_samples[spos] if spos<len(o.guarded_samples) else None;spos+=1
        p=plan_guarded_dword(address,sample);plans.append(p)
        if not p.complete:raise Missing(p.missing)
        return p.value_dword
    try:
        root=guarded(g(0x553e7c))
        value=guarded((root+g(0x553ff0))&0xffffffff)
        return SourceCoinPlan(True,value,tuple(globals_read),tuple(calls),tuple(plans))
    except Missing as e:return SourceCoinPlan(False,None,tuple(globals_read),tuple(calls),tuple(plans),str(e))
