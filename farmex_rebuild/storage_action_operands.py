"""Ordered storage action operands; no process reads, calls or ABI certificate."""
from dataclasses import dataclass
from source_coin import SourceCoinObservation,plan_guarded_dword

@dataclass(frozen=True)
class StorageActionSamples:
    global_samples:tuple=()
    guarded_samples:tuple=()
    direct_samples:tuple=()
    def __post_init__(self):
        SourceCoinObservation(self.global_samples,self.guarded_samples)
        SourceCoinObservation(self.direct_samples,())

@dataclass(frozen=True)
class StorageActionPlan:
    complete:bool
    status:str
    steps:tuple=()
    guarded_plans:tuple=()
    call:object=None
    missing:str=''
    independently_verified:bool=False

def plan_storage_action(helper,argument,o):
    from storage_native_plans import SLOTS,NativeCallPlan
    if helper not in tuple(SLOTS)+('00465334','0046fdf8'):raise ValueError('Ordered storage action helper required')
    if type(argument) is not int or not 0<=argument<1<<32 or not isinstance(o,StorageActionSamples):
        raise ValueError('Raw action DWORD and typed ordered samples required')
    steps=[];guards=[];gp=0;sp=0;dp=0
    class Missing(Exception):pass
    def result(ok,status,call=None,missing=''):
        return StorageActionPlan(ok,status,tuple(steps),tuple(guards),call,missing)
    def g(address):
        nonlocal gp
        steps.append(('global',address))
        if gp>=len(o.global_samples):raise Missing('action global at%08x'%address)
        at,value=o.global_samples[gp];gp+=1
        if at!=address:raise ValueError('Reached action global order mismatch')
        if value is None:raise Missing('action global value at%08x'%address)
        return value
    def guarded(address):
        nonlocal sp
        address&=0xffffffff;steps.append(('protected',address));sample=None
        if address:
            sample=o.guarded_samples[sp] if sp<len(o.guarded_samples) else None;sp+=1
        p=plan_guarded_dword(address,sample);guards.append(p)
        if not p.complete:raise Missing(p.missing)
        return p.value_dword
    def direct(address):
        nonlocal dp
        address&=0xffffffff;steps.append(('direct',address))
        if dp>=len(o.direct_samples):raise Missing('direct action DWORD at%08x'%address)
        at,value=o.direct_samples[dp];dp+=1
        if at!=address:raise ValueError('Reached direct action sample order mismatch')
        if value is None:raise Missing('direct action value at%08x'%address)
        return value
    try:
        preserve=False
        if helper in SLOTS:
            context_key,slots_key,preserve=SLOTS[helper]
            root=guarded(g(0x553e80))
            context=guarded(root+g(context_key))
            shift=(argument<<2)&0xffffffff;steps.append(('slot_shift_low32',argument,shift))
            pointer=guarded(shift+g(slots_key)+context)
            if pointer==0:return result(True,'no_call')
            value=guarded(pointer)
            if value==0:return result(True,'no_call')
            if preserve:steps.extend((('PUSHAD',),('PUSHFD',)))
            # Fresh globals and direct memory, never reuse guarded-root values.
            fresh_root=direct(g(0x553e80))
            ecx=direct(fresh_root+g(context_key))
            offset=g(0x554200)
            vtable=direct(ecx);target=direct(vtable+offset)
            pushes=(0x4000000,value)
            steps.extend(('PUSH',v) for v in pushes)
        else:
            is_page=helper=='0046fdf8'
            root_key=0x553e80 if is_page else 0x553f44
            context=guarded(g(root_key))
            if is_page:context=guarded(context+g(0x5540bc))
            first=guarded(context+g(0x5540cc if is_page else 0x554138))
            second=guarded(context+g(0x5540d0 if is_page else 0x55413c))
            choose_first=argument&255==1 if is_page else bool(argument&255)
            value=first if choose_first else second
            steps.append(('select_first',choose_first))
            ecx=direct(g(root_key))
            if is_page:ecx=direct(ecx+g(0x5540bc))
            pushes=(1,value)
            # Button/page callers push before reading dispatch offset/vtable.
            steps.extend(('PUSH',v) for v in pushes)
            offset=g(0x554200)
            vtable=direct(ecx);target=direct(vtable+offset)
        steps.append(('indirect_call_plan',target,ecx))
        if preserve:steps.extend((('POPFD',),('POPAD',)))
        return result(True,'call_planned',NativeCallPlan(target,ecx,pushes,preserve))
    except Missing as error:return result(False,'needs_observation',missing=str(error))
