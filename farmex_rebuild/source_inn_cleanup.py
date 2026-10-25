"""00470c7f..00470caa fresh Inn cleanup byte operands; no native IO."""
from dataclasses import dataclass
from source_coin import SourceCoinObservation,GuardedByteSample,plan_guarded_dword,plan_guarded_byte

@dataclass(frozen=True)
class InnCleanupObservation:
    global_samples:tuple=()
    guarded_samples:tuple=()
    byte_sample:object=None
    def __post_init__(self):
        SourceCoinObservation(self.global_samples,self.guarded_samples)
        if self.byte_sample is not None and not isinstance(self.byte_sample,GuardedByteSample):
            raise ValueError('Typed Inn cleanup BYTE observation required')

@dataclass(frozen=True)
class InnCleanupPlan:
    complete:bool
    open_byte:object=None
    steps:tuple=()
    guarded_plans:tuple=()
    byte_plan:object=None
    missing:str=''
    independently_verified:bool=False

def plan_inn_cleanup(o):
    if not isinstance(o,InnCleanupObservation):raise ValueError('Typed Inn cleanup observations required')
    steps=[];plans=[];byte=None;gp=0;sp=0
    class Missing(Exception):pass
    def g(address):
        nonlocal gp
        steps.append(('global',address))
        if gp>=len(o.global_samples):raise Missing('Inn cleanup global at%08x'%address)
        at,value=o.global_samples[gp];gp+=1
        if at!=address:raise ValueError('Reached Inn cleanup global order mismatch')
        if value is None:raise Missing('Inn cleanup global value at%08x'%address)
        return value
    def read(address):
        nonlocal sp
        address&=0xffffffff;steps.append(('0045dc44',address));sample=None
        if address:
            sample=o.guarded_samples[sp] if sp<len(o.guarded_samples) else None;sp+=1
        p=plan_guarded_dword(address,sample);plans.append(p)
        if not p.complete:raise Missing(p.missing)
        return p.value_dword
    def result(complete,value=None,missing=''):
        return InnCleanupPlan(complete,value,tuple(steps),tuple(plans),byte,missing)
    try:
        root=read(g(0x553e80))
        context=read(root+g(0x5540bc))
        address=(context+g(0x5541fc))&0xffffffff
        steps.append(('0045dbdc',address))
        byte=plan_guarded_byte(address,o.byte_sample)
        if not byte.complete:raise Missing(byte.missing)
        value=byte.eax_dword&255
        steps.append(('MOV_CL_DEC_JNZ',value,(value-1)&0xffffffff))
        return result(True,value)
    except Missing as error:return result(False,missing=str(error))
