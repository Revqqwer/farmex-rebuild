"""00465514/00465580 operand and normal-return plans, no native execution."""
from dataclasses import dataclass
from typing import Optional
from merchant_result_filter import raw


def optional(value,bits,name):
    if value is not None:raw(value,bits,name)


@dataclass(frozen=True)
class BaseItemLookupObservation:
    first_variant_byte: Optional[int] = None
    second_variant_byte: Optional[int] = None
    context_pointer: Optional[int] = None
    context_value: Optional[int] = None
    function_target: Optional[int] = None
    call_returned: Optional[bool] = None
    result_eax: Optional[int] = None

    def __post_init__(self):
        for name,value in vars(self).items():
            if name=='call_returned':
                if value is not None and type(value) is not bool:raise ValueError('Separate normal-return observation required')
            else:optional(value,8 if name.endswith('variant_byte') else 32,name)


@dataclass(frozen=True)
class ExtensionLookupObservation:
    table_base: Optional[int] = None
    table_slot_value: Optional[int] = None
    function_target: Optional[int] = None
    call_returned: Optional[bool] = None
    result_eax: Optional[int] = None

    def __post_init__(self):
        for name,value in vars(self).items():
            if name=='call_returned':
                if value is not None and type(value) is not bool:raise ValueError('Separate normal-return observation required')
            else:optional(value,32,name)


@dataclass(frozen=True)
class ItemLookupPlan:
    complete: bool
    status: str
    key: int
    result_eax: Optional[int] = None
    reads: tuple = ()
    target: Optional[int] = None
    ecx: Optional[int] = None
    pushed_args: tuple = ()
    native_execution_verified: bool = False


def plan_base_item_lookup(item_id, observation=None, *, _observation_reader=None):
    raw(item_id,32,'item ID')
    o=BaseItemLookupObservation() if observation is None else observation
    if not isinstance(o,BaseItemLookupObservation):raise ValueError('Typed base lookup observations required')
    read=lambda name:getattr(o,name) if _observation_reader is None else _observation_reader(name)
    key=(item_id//1000)*1000
    reads=[];ecx=None;target=None;args=()
    def out(complete,status,result=None):
        return ItemLookupPlan(complete,status,key,result,tuple(reads),target,ecx,args)
    reads.append((0x553e46,'BYTE:first'))
    first=read('first_variant_byte')
    if first is None:return out(False,'needs_first_variant')
    if first==1:
        # XOR ECX; MOV CL,1; DEC ECX leaves ECX exactly zero at CALL EAX.
        ecx=0
    else:
        reads.append((0x553e46,'BYTE:second'))
        second=read('second_variant_byte')
        if second is None:return out(False,'needs_second_variant')
        if second!=2:return out(True,'unsupported_variant_zero',0)
        reads.append((0x553ec0,'DWORD:context_pointer'))
        pointer=read('context_pointer')
        if pointer is None:return out(False,'needs_context_pointer')
        if pointer==0:return out(False,'unresolved_null_context_dereference')
        reads.append((pointer,'DWORD:context'))
        ecx=read('context_value')
        if ecx is None:return out(False,'needs_context_value')
    reads.append((0x553ec4,'DWORD:function'))
    target=read('function_target')
    if target is None:return out(False,'needs_function_target')
    args=(key,)
    if target==0:return out(False,'unresolved_null_call_target')
    if read('call_returned') is not True:return out(False,'needs_call_normal_return')
    eax=read('result_eax')
    if eax is None:return out(False,'needs_result_eax')
    return out(True,'normal_result',eax)


def plan_extension_lookup(item_id, resolver_type_raw, observation=None, *, _observation_reader=None):
    raw(item_id,32,'item ID');raw(resolver_type_raw,32,'resolver type')
    o=ExtensionLookupObservation() if observation is None else observation
    if not isinstance(o,ExtensionLookupObservation):raise ValueError('Typed extension lookup observations required')
    read=lambda name:getattr(o,name) if _observation_reader is None else _observation_reader(name)
    key=item_id%1000;reads=[];ecx=None;target=None;args=()
    def out(complete,status,result=None):
        return ItemLookupPlan(complete,status,key,result,tuple(reads),target,ecx,args)
    if item_id==0:return out(True,'empty_item_zero',0)
    reads.append((0x553ec8,'DWORD:table_base'))
    table=read('table_base')
    if table is None:return out(False,'needs_table_base')
    slot=(table+((resolver_type_raw&255)<<2))&0xffffffff
    reads.append((slot,'0045dc44:table_slot'))
    ecx=read('table_slot_value')
    if ecx is None:return out(False,'needs_table_slot_value')
    reads.append((0x553ecc,'DWORD:function'))
    target=read('function_target')
    if target is None:return out(False,'needs_function_target')
    args=(key,)
    if target==0:return out(False,'unresolved_null_call_target')
    if read('call_returned') is not True:return out(False,'needs_call_normal_return')
    eax=read('result_eax')
    if eax is None:return out(False,'needs_result_eax')
    return out(True,'normal_result',eax)
