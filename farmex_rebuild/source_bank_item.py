"""0046fed8 normal guarded slot-ID operands; no memory/protection/native IO."""
from dataclasses import dataclass
from source_coin import SourceCoinObservation,plan_guarded_dword

@dataclass(frozen=True)
class BankItemObservation:
    global_samples:tuple=()
    guarded_samples:tuple=()
    def __post_init__(self):
        # Reuse the sample carrier's type/order validation, not coin globals.
        SourceCoinObservation(self.global_samples,self.guarded_samples)

@dataclass(frozen=True)
class BankItemPlan:
    complete:bool
    slot_dword:int
    result_dword:object=None
    steps:tuple=()
    guarded_plans:tuple=()
    missing:str=''
    independently_verified:bool=False

def plan_bank_item(slot_dword,o):
    if type(slot_dword) is not int or not 0<=slot_dword<1<<32 or not isinstance(o,BankItemObservation):
        raise ValueError('Raw slot DWORD and typed bank item observations required')
    steps=[];guards=[];gp=0;sp=0
    class Missing(Exception):pass
    def g(address):
        nonlocal gp
        steps.append(('global',address))
        if gp>=len(o.global_samples):raise Missing('global sample at%08x'%address)
        at,value=o.global_samples[gp];gp+=1
        if at!=address:raise ValueError('Reached bank-item global order mismatch')
        if value is None:raise Missing('global value at%08x'%address)
        return value
    def read(address):
        nonlocal sp
        address&=0xffffffff;sample=None
        steps.append(('0045dc44',address))
        if address:
            sample=o.guarded_samples[sp] if sp<len(o.guarded_samples) else None;sp+=1
        p=plan_guarded_dword(address,sample);guards.append(p)
        if not p.complete:raise Missing(p.missing)
        return p.value_dword
    def result(ok,value=None,missing=''):
        return BankItemPlan(ok,slot_dword,value,tuple(steps),tuple(guards),missing)
    try:
        root=read(g(0x553e80))
        records=read(root+g(0x5540bc))
        offset=g(0x5540c0)
        shifted=(slot_dword<<2)&0xffffffff
        steps.append(('slot_shift_low32',slot_dword,shifted))
        record=read(records+offset+shifted)
        if record==0:return result(True,0)
        # Source obtains both pointers before dereferencing either item value.
        base_pointer=read(record+0x60)
        variant_pointer=read(record+0x64)
        base=read(base_pointer)
        variant=read(variant_pointer)
        remainder=variant%1000;value=(base+remainder)&0xffffffff
        steps.append(('unsigned_DIV1000_ADD_low32',base,variant,remainder,value))
        return result(True,value)
    except Missing as error:return result(False,missing=str(error))
