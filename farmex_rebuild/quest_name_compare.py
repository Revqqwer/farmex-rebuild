"""Pinned ANSI LStrCmp -> SETA/SETC -> compare -> equality wrapper.

Separate helper calls can observe different strings/flags. No Unicode decoding,
native RTL execution or implicit codepage is used. Owned byte order is opt-in.
"""
from dataclasses import dataclass,field
from collections.abc import Mapping


@dataclass(frozen=True)
class AnsiCompareSample:
    carry_flag:object=None
    zero_flag:object=None
    use_owned_bytes:bool=False
    left_bytes:object=None
    right_bytes:object=None


@dataclass(frozen=True)
class QuestNameCompareObservation:
    greater:object=None
    less:object=None
    normal_returns:object=field(default_factory=dict)


@dataclass(frozen=True)
class QuestNameComparePlan:
    complete:bool
    status:str
    eax:object=None
    compare_eax:object=None
    needed:object=None
    calls:tuple=()
    comparisons:tuple=()
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class QuestNameCompareFrame:
    def __init__(self):
        self.phase='greater_flags';self.normal=set();self.called=set();self.calls=[]
        self.comparisons=[];self.flags={};self.flag_values={};self.policies={};self.operands={}
        self.compare_eax=None;self.final=None

    def out(self,status,needed=None,complete=False):
        p=QuestNameComparePlan(complete,status,
            int(self.compare_eax==0) if complete else None,self.compare_eax,
            needed,tuple(self.calls),tuple(self.comparisons))
        if complete:self.final=p
        return p

    def advance(self,observation=None):
        if self.final is not None:return self.final
        o=QuestNameCompareObservation() if observation is None else observation
        if not isinstance(o,QuestNameCompareObservation) or not isinstance(o.normal_returns,Mapping):
            raise ValueError('Typed ANSI comparison observations required')
        class Missing(Exception):pass
        def normal(label,helper):
            if label not in self.called:self.called.add(label);self.calls.append((label,helper))
            if label not in self.normal:
                receipt=o.normal_returns.get(label)
                if receipt is not None and type(receipt) is not bool:raise ValueError('Explicit helper return required')
                if receipt is not True:raise Missing(('normal',label))
                self.normal.add(label)
        def flag(value,label):
            if label not in self.flag_values:
                if value is None:raise Missing(('flag',label))
                if type(value) is not bool:raise ValueError('Normalized source flag boolean required')
                self.flag_values[label]=value
            return self.flag_values[label]
        def compare(stage):
            normal(stage+'_compare','rtl260.bpl!@System@@LStrCmp$qqrv')
            sample=getattr(o,stage)
            if not isinstance(sample,AnsiCompareSample):raise Missing(('sample',stage))
            if type(sample.use_owned_bytes) is not bool:raise ValueError('Explicit owned-byte policy required')
            if stage not in self.policies:self.policies[stage]=sample.use_owned_bytes
            if self.policies[stage]!=sample.use_owned_bytes:raise ValueError('Comparison policy changed during one helper call')
            if sample.use_owned_bytes:
                if sample.carry_flag is not None or sample.zero_flag is not None:
                    raise ValueError('Owned byte order conflicts with captured flags')
                for role,raw in (('left',sample.left_bytes),('right',sample.right_bytes)):
                    token=(stage,role)
                    if token not in self.operands:
                        if raw is None:raise Missing(('bytes',stage))
                        if type(raw) is not bytes:raise ValueError('Immutable post-load ANSI data required')
                        self.operands[token]=raw
                left=self.operands[(stage,'left')];right=self.operands[(stage,'right')]
                cf=left<right;zf=left==right
                provenance='owned_unsigned_byte_order'
            else:
                cf=flag(sample.carry_flag,stage+'_CF')
                # SETC uses no ZF. For SETA, CF1 already proves AL0.
                zf=flag(sample.zero_flag,stage+'_ZF') if stage=='greater' and not cf else None
                provenance='captured_flags'
            self.flags[stage]=(cf,zf)
            self.comparisons.append((stage,cf,zf,provenance,
                self.operands[(stage,'left')] if sample.use_owned_bytes else None,
                self.operands[(stage,'right')] if sample.use_owned_bytes else None))
        try:
            while True:
                if self.phase=='greater_flags':
                    compare('greater');self.phase='greater_return'
                elif self.phase=='greater_return':
                    normal('greater_return','00402e18 SETA wrapper')
                    cf,zf=self.flags['greater']
                    if not cf and not zf:self.compare_eax=1;self.phase='compare_return'
                    else:self.phase='less_flags'
                elif self.phase=='less_flags':
                    compare('less');self.phase='less_return'
                elif self.phase=='less_return':
                    normal('less_return','00402e30 SETC wrapper')
                    self.compare_eax=0xffffffff if self.flags['less'][0] else 0
                    self.phase='compare_return'
                elif self.phase=='compare_return':
                    normal('compare_return','signed comparison wrapper (current00505174)')
                    self.phase='equal_return'
                elif self.phase=='equal_return':
                    normal('equal_return','SETZ AL; AND EAX,1 wrapper (current00505134)')
                    return self.out('comparison_ready',complete=True)
                else:raise AssertionError('Unknown name comparison phase')
        except Missing as error:return self.out('needs_observation',error.args[0])
