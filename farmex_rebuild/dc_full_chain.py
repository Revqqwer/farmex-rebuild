"""Explicit periodic -> consumer -> sender -> inner helper control composition."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from jail_protection import JailObservation
from dc_propagation import DCPeriodicFrame
from dc_sender_template import DCSenderObservation,DCSenderConsumerFrame

@dataclass(frozen=True)
class DCFullChainObservation:
    parent: JailObservation=field(default_factory=JailObservation)
    action: DCSenderObservation=field(default_factory=DCSenderObservation)
    def __post_init__(self):
        if not isinstance(self.parent,JailObservation) or not isinstance(self.action,DCSenderObservation):
            raise ValueError('Typed periodic and bound sender observations required')

@dataclass(frozen=True)
class DCFullChainPlan:
    complete: bool
    parent: object
    action: object=None
    needed: object=None
    whole_function_verified: bool=False
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False
    @property
    def payload_intents(self):return () if self.action is None else self.action.consumer.payload_intents
    @property
    def write_intents(self):
        return () if self.action is None else tuple((label,)+intent for label,p in self.action.transfers.items() for intent in p.write_intents)
    @property
    def stubs(self):
        return MappingProxyType({} if self.action is None else {k:p.stub_bytes for k,p in self.action.transfers.items()})

class DCFullChainFrame:
    def __init__(self,*,context=0x562194):
        self.parent=DCPeriodicFrame(context=context);self.action=None;self.action_plan=None;self.final=None
    def _result(self,p,needed=None):return DCFullChainPlan(p.complete,p,self.action_plan,needed)
    def advance(self,o):
        if not isinstance(o,DCFullChainObservation):raise ValueError('Typed full DC observation required')
        if self.final is not None:return self.final
        normals=dict(o.parent.normal_returns)
        if self.action is None or self.action.final is None:normals['consumer']=False
        p=self.parent.advance(replace(o.parent,normal_returns=normals))
        if p.complete:
            self.final=self._result(p);return self.final
        if p.needed!=('normal','consumer'):return self._result(p,('parent',p.needed))
        if self.action is None:
            helper,args,_=p.calls[-1]
            if helper not in ('0046dd70','0046d904'):raise AssertionError('Unexpected periodic helper')
            self.action=DCSenderConsumerFrame('list' if helper=='0046dd70' else 'scan',context=args[0])
        action_o=replace(o.action,consumer=replace(o.action.consumer,entry_reached=True))
        self.action_plan=self.action.advance(action_o)
        if not self.action_plan.complete:return self._result(p,('action',self.action_plan.needed))
        p=self.parent.advance(o.parent)
        result=self._result(p,None if p.complete else ('parent',p.needed))
        if p.complete:self.final=result
        return result
