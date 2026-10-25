"""Reached45730e normal cleanup projections; no frees or FS writes executed."""
from dataclasses import dataclass,field
from types import MappingProxyType

@dataclass(frozen=True)
class ChatCleanupArgs:
    ebp_dword:int
    local_fefc:int
    local_fef8:int
    local_ff0c:int
    local_ff34:int
    saved_fs_ff18:int
    def __post_init__(self):
        for value in self.__dict__.values():
            if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw fixed cleanup DWORD snapshot required')

@dataclass(frozen=True)
class ChatCleanupObservation:
    normal_returns:object=field(default_factory=dict)
    def __post_init__(self):
        values=dict(self.normal_returns)
        if any(type(v) is not bool for v in values.values()):raise ValueError('Separate cleanup normal receipts required')
        object.__setattr__(self,'normal_returns',MappingProxyType(values))

@dataclass(frozen=True)
class ChatCleanupPlan:
    complete:bool
    args:ChatCleanupArgs
    calls:tuple=()
    stores:tuple=()
    fs_store:object=None
    missing:str=''
    needed:object=None
    returned_EAX_verified:bool=False
    heap_effect_verified:bool=False
    native_execution_verified:bool=False

def plan_chat_cleanup(args,o):
    if not isinstance(args,ChatCleanupArgs) or not isinstance(o,ChatCleanupObservation):raise ValueError('Typed cleanup snapshots required')
    calls=[];stores=[];fs=None;counter=args.local_ff34;counter_address=(args.ebp_dword-0xcc)&0xffffffff
    class Missing(Exception):pass
    def normal(label,helper,pushes):
        calls.append((helper,pushes,label))
        if o.normal_returns.get(label) is not True:raise Missing(label)
    def subtract(n):
        nonlocal counter
        counter=(counter-n)&0xffffffff;stores.append((counter_address,4,counter))
    try:
        for label,pointer in (('free_fefc',args.local_fefc),('free_fef8',args.local_fef8),('free_ff0c',args.local_ff0c)):
            normal(label,'CRT:_free',(pointer,))
        subtract(2)
        normal('helper_4040f8','004040f8',(2,(args.ebp_dword-0x54)&0xffffffff))
        subtract(1)
        normal('reset_local_50','00403860',(0,1,(args.ebp_dword-0x50)&0xffffffff))
        subtract(1)
        normal('reset_local_28','00403860',(0,1,(args.ebp_dword-0x28)&0xffffffff))
        fs=('FS:0',4,args.saved_fs_ff18)
        if o.normal_returns.get('epilogue') is not True:raise Missing('epilogue')
        return ChatCleanupPlan(True,args,tuple(calls),tuple(stores),fs)
    except Missing as error:
        return ChatCleanupPlan(False,args,tuple(calls),tuple(stores),fs,str(error)+' normal return',str(error))

class ChatCleanupFrame:
    def __init__(self,args):
        plan_chat_cleanup(args,ChatCleanupObservation())
        self.args=args;self.returns={};self.final=None
    def advance(self,o):
        if not isinstance(o,ChatCleanupObservation):raise ValueError('Typed cleanup observations required')
        if self.final is not None:return self.final
        for _ in range(8):
            p=plan_chat_cleanup(self.args,ChatCleanupObservation(self.returns))
            if p.complete:self.final=p;return p
            if o.normal_returns.get(p.needed) is not True:return p
            self.returns[p.needed]=True
        raise ValueError('Cleanup exceeded normal-path call budget')
