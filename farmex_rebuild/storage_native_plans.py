"""Richard native helper operand/read/write plans; never execute game code.

Protected and direct reads are separate observations, including the second
root read before a vtable call. ABI/target validity is not established here.
"""
from dataclasses import dataclass,field
from types import MappingProxyType
from typing import Mapping,Tuple
from npc_sell_packets import raw
from npc_buy_packets import signed32

SLOTS={'004fe274':(0x554128,0x55412c,False),'004fe2fc':(0x554128,0x554130,False),
       '0046fc78':(0x5540bc,0x5540c4,True),'0046fd04':(0x5540bc,0x5540c0,True)}

@dataclass(frozen=True)
class NativeHelperObservation:
    helper: str
    argument: int
    globals: Mapping[int,int] = field(default_factory=dict)
    protected_words: Mapping[int,int] = field(default_factory=dict)
    direct_words: Mapping[int,int] = field(default_factory=dict)
    source_profile: str = ''
    operand_samples: object = None
    normal_returned: object = None

    def __post_init__(self):
        if self.helper not in tuple(SLOTS)+('004653a8','00465334','0046fdf8'):raise ValueError('Supported source helper required')
        raw(self.argument)
        if self.source_profile not in ('','us','steam'):raise ValueError('Unknown source profile label')
        for name in ('globals','protected_words','direct_words'):
            mapping=getattr(self,name)
            for key,value in mapping.items():raw(key);raw(value)
            object.__setattr__(self,name,MappingProxyType(dict(mapping)))
        if self.normal_returned is not None and type(self.normal_returned) is not bool:raise ValueError('Separate native helper normal return required')
        if self.operand_samples is not None:
            from storage_action_operands import StorageActionSamples
            from storage_quantity_operands import StorageQuantitySamples
            valid=(self.helper in tuple(SLOTS)+('00465334','0046fdf8') and isinstance(self.operand_samples,StorageActionSamples)) or (self.helper=='004653a8' and isinstance(self.operand_samples,StorageQuantitySamples))
            if not valid:
                raise ValueError('Typed ordered storage action inputs required')
            if self.globals or self.protected_words or self.direct_words:raise ValueError('Ordered action inputs conflict with stable map fixtures')

@dataclass(frozen=True)
class NativeCallPlan:
    target: int
    ecx: int
    push_order: Tuple[int,...]
    preserve_gprs_and_flags: bool = False
    abi_verified: bool = False

@dataclass(frozen=True)
class NativeHelperPlan:
    status: str
    globals: Mapping[int,int]
    reads: Tuple[Tuple[str,int],...] = ()
    call: object = None
    memory_writes: Tuple[Tuple[int,bytes],...] = ()
    text: str = ''
    missing: str = ''
    ordered_plan: object = None

    def __post_init__(self):object.__setattr__(self,'globals',MappingProxyType(dict(self.globals)))

class _Missing(Exception):pass

def plan_native_helper(observation):
    if not isinstance(observation,NativeHelperObservation):raise ValueError('Typed native observations required')
    if observation.operand_samples is not None:
        if observation.helper=='004653a8':
            from storage_quantity_operands import plan_storage_quantity
            p=plan_storage_quantity(observation.argument,observation.operand_samples)
            reads=tuple(s for s in p.steps if s[0]=='0045dc44')
            return NativeHelperPlan(p.status,dict(p.global_writes),reads,memory_writes=p.memory_writes,text=p.text,missing=p.missing,ordered_plan=p)
        from storage_action_operands import plan_storage_action
        p=plan_storage_action(observation.helper,observation.argument,observation.operand_samples)
        reads=tuple(s for s in p.steps if s[0] in ('protected','direct'))
        return NativeHelperPlan(p.status,{},reads,p.call,missing=p.missing,ordered_plan=p)
    obs=observation;globals=dict(obs.globals);reads=[];writes=[];text=''
    def g(address):
        if address not in globals:raise _Missing('source global%08x'%address)
        return globals[address]
    def word(address,protected=True):
        address&=0xffffffff;kind='protected' if protected else 'direct'
        reads.append((kind,address));mapping=obs.protected_words if protected else obs.direct_words
        if address not in mapping:raise _Missing(kind+' DWORD%08x'%address)
        return mapping[address]
    def result(status,call=None,missing=''):
        return NativeHelperPlan(status,globals,tuple(reads),call,tuple(writes),text,missing)
    def vcall(root_slot,context_offset,arg,push_constant,preserve=False):
        root=word(root_slot,False)
        context=word(root+context_offset,False) if context_offset is not None else root
        vtable=word(context,False);target=word(vtable+g(0x554200),False)
        return NativeCallPlan(target,context,(push_constant,arg),preserve)
    try:
        if obs.helper in SLOTS:
            context_key,slots_key,preserve=SLOTS[obs.helper]
            slot=g(0x553e80);context_offset=g(context_key)
            root=word(slot);context=word(root+context_offset)
            pointer=word(context+g(slots_key)+(obs.argument*4&0xffffffff))
            if pointer==0:return result('no_call')
            value=word(pointer)
            if value==0:return result('no_call')
            return result('call_planned',vcall(slot,context_offset,value,0x04000000,preserve))
        if obs.helper=='00465334':
            slot=g(0x553f44);dialog=word(slot)
            yes=word(dialog+g(0x554138));no=word(dialog+g(0x55413c))
            value=yes if obs.argument&255 else no
            return result('call_planned',vcall(slot,None,value,1))
        if obs.helper=='0046fdf8':
            slot=g(0x553e80);context_offset=g(0x5540bc)
            root=word(slot);context=word(root+context_offset)
            first=word(context+g(0x5540cc));second=word(context+g(0x5540d0))
            value=first if obs.argument&255==1 else second
            return result('call_planned',vcall(slot,context_offset,value,1))
        text=str(signed32(obs.argument))
        encoded=text.encode('ascii')
        # The source copies into EBP-3c..EBP-35 (8 initialized bytes); EBP-34
        # holds its own source string pointer. Longer text overwrites that pointer.
        if len(encoded)>8:return result('unresolved_stack_buffer_overwrite')
        destination=g(0x553d20)
        if destination==0:
            destination=(word(g(0x553f48))+g(0x554134))&0xffffffff
            globals[0x553d20]=destination
        writes.extend(((destination,b'\0'*14),(destination,encoded),
                       ((destination+0x10)&0xffffffff,bytes((len(encoded),))),
                       ((destination+0x28)&0xffffffff,b'\0')))
        return result('writes_planned')
    except _Missing as exc:return result('needs_observation',missing=str(exc))
