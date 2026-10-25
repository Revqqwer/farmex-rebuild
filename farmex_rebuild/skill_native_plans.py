"""00464990 ->00465640 operand plans. No game calls, reads or writes.

Mode1 leaves ECX inherited; mode2 explicitly reads a context pointer. Caller
expects callee cleanup, which is an assumption, not a verified target ABI.
SOURCE_GLOBALS is historical12f3e2dd fixture data. Source-hash-bound current
tables and factories live in native_profile_versions; no implicit upgrade.
"""
from dataclasses import dataclass,field
from types import MappingProxyType
from typing import Mapping,Optional,Tuple

SOURCE_GLOBALS=MappingProxyType({
    'us':MappingProxyType({0x553e46:1,0x553e80:0x111563c,0x553eb8:0,
                          0x553ebc:0x503be0,0x553ee4:0x886b30,0x5540a0:0x468}),
    'steam':MappingProxyType({0x553e46:2,0x553e80:0x11ebab0,0x553eb8:0x11ea50c,
                             0x553ebc:0x634020,0x553ee4:0x7df190,0x5540a0:0x4a8})})

def _raw(value):
    if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw DWORD required')

@dataclass(frozen=True)
class SkillObservation:
    action_id: int
    actor_id: int
    globals: Mapping[int,int] = field(default_factory=dict)
    direct_words: Mapping[int,int] = field(default_factory=dict)
    lookup_return: Optional[int] = None
    native_return: Optional[int] = None

    def __post_init__(self):
        _raw(self.action_id);_raw(self.actor_id)
        for value in (self.lookup_return,self.native_return):
            if value is not None:_raw(value)
        for name in ('globals','direct_words'):
            values=dict(getattr(self,name))
            for key,value in values.items():_raw(key);_raw(value)
            object.__setattr__(self,name,MappingProxyType(values))
        if 0x553e46 in self.globals and self.globals[0x553e46]>255:raise ValueError('Source mode is a BYTE')

@dataclass(frozen=True)
class SkillCallPlan:
    helper: str
    target: int
    ecx: Optional[int]
    push_order: Tuple[int,...]
    assumed_callee_cleanup_bytes: int
    abi_verified: bool = False

@dataclass(frozen=True)
class SkillPlan:
    status: str
    calls: Tuple[SkillCallPlan,...] = ()
    reads: Tuple[int,...] = ()
    returned_nonzero: Optional[bool] = None
    missing: str = ''
    independently_verified: bool = False

class _Missing(Exception):pass

def plan_alternate_skill(obs,*,dispatch_helper='00465640'):
    if not isinstance(obs,SkillObservation):raise ValueError('Typed skill observations required')
    if dispatch_helper not in ('00465640','004655e8'):raise ValueError('Known audited source dispatch role required')
    calls=[];reads=[]
    def g(address):
        if address not in obs.globals:raise _Missing('source global %08x'%address)
        return obs.globals[address]
    def read(address):
        address&=0xffffffff;reads.append(address)
        if address not in obs.direct_words:raise _Missing('direct DWORD %08x'%address)
        return obs.direct_words[address]
    try:
        mode=g(0x553e46)
        if mode in (1,2):
            ecx=read(g(0x553eb8)) if mode==2 else None
            calls.append(SkillCallPlan('00464990',g(0x553ebc),ecx,(obs.action_id,),4))
            if obs.lookup_return is None:raise _Missing('00464990 native lookup return')
            lookup=obs.lookup_return
        else:
            lookup=0 # Source wrapper initializes result0 and skips other modes.
        root=read(g(0x553e80))
        context=read(root+g(0x5540a0))
        calls.append(SkillCallPlan(dispatch_helper,g(0x553ee4),context,(lookup,obs.actor_id),8))
        return SkillPlan('native_return_observed' if obs.native_return is not None else 'call_planned',
                         tuple(calls),tuple(reads),None if obs.native_return is None else obs.native_return!=0)
    except _Missing as error:
        return SkillPlan('needs_observation',tuple(calls),tuple(reads),missing=str(error))
