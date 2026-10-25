"""Own captured-value actor producer for merchant reply 004bc650."""
from dataclasses import dataclass
from typing import Optional
from game_text import npc_text_request, replay_text_copy
from merchant_result_filter import raw
from merchant_scan_results import MerchantActorMetadata
from merchant_scan_reply_data import decode_merchant_scan_data
from merchant_item_metadata import project_merchant_scan_with_lookups


@dataclass(frozen=True)
class MerchantCoordinateObservation:
    offset_dword: Optional[int] = None
    float_reader_returned: Optional[bool] = None
    ftol_returned: Optional[bool] = None
    ftol_eax: Optional[int] = None

    def __post_init__(self):
        for name,value in vars(self).items():
            if value is None:continue
            if name.endswith('returned'):
                if type(value) is not bool:raise ValueError('Separate normal-return bool required')
            else:raw(value,32,name)


@dataclass(frozen=True)
class MerchantActorObservation:
    lookup_returned: Optional[bool] = None
    actor_pointer: Optional[int] = None
    x: Optional[MerchantCoordinateObservation] = None
    y: Optional[MerchantCoordinateObservation] = None
    storage_offset_dword: Optional[int] = None
    storage_dword: Optional[int] = None
    initial_name_offset_dword: Optional[int] = None
    initial_name_dword: Optional[int] = None
    inline_name_offset_dword: Optional[int] = None
    readable: Optional[bool] = None
    copied_bytes: Optional[bytes] = None

    def __post_init__(self):
        for name,value in vars(self).items():
            if value is None:continue
            if name in ('lookup_returned','readable'):
                if type(value) is not bool:raise ValueError('Explicit bool observation required')
            elif name in ('x','y'):
                if not isinstance(value,MerchantCoordinateObservation):raise ValueError('Typed coordinate observation required')
            elif name=='copied_bytes':
                if type(value) is not bytes:raise ValueError('Immutable captured name bytes required')
            else:raw(value,32,name)


@dataclass(frozen=True)
class MerchantActorPlan:
    complete: bool
    status: str
    metadata: object = None
    steps: tuple = ()
    coordinate_eax_prefix: tuple = ()
    text_request: object = None
    text_copy: object = None
    native_execution_verified: bool = False
    native_text_conversion_verified: bool = False


def plan_merchant_actor_metadata(entity_id,observation=None,decode_name=None,*,_observation_reader=None):
    raw(entity_id,16,'entity WORD')
    o=MerchantActorObservation() if observation is None else observation
    if not isinstance(o,MerchantActorObservation):raise ValueError('Typed actor observation required')
    def read(path,required_count=None):
        path=(path,) if type(path) is str else path
        if _observation_reader is not None:return _observation_reader(path,required_count)
        node=o
        for name in path:
            if node is None:return None
            node=getattr(node,name)
        return node
    steps=[('00464a10',entity_id)];coords=[];request=None;copy=None
    class Missing(Exception):pass
    def need(value,name):
        if value is None:raise Missing(name)
        return value
    def out(complete,status,metadata=None):
        return MerchantActorPlan(complete,status,metadata,tuple(steps),tuple(coords),request,copy)
    try:
        if read('lookup_returned') is not True:return out(False,'needs_lookup_normal_return')
        pointer=need(read('actor_pointer'),'actor_pointer')
        if pointer==0:
            return out(False,'unresolved_missing_actor_coordinate_locals')
        for axis,address in [('x',0x554008),('y',0x554010)]:
            steps.append(('global',address))
            offset=need(read((axis,'offset_dword')),axis+'_offset')
            steps.append(('0045ddb8',(pointer+offset)&0xffffffff))
            if read((axis,'float_reader_returned')) is not True:raise Missing(axis+'_float_reader_normal_return')
            steps.append(('CC32260MT.DLL:__ftol',axis))
            if read((axis,'ftol_returned')) is not True:raise Missing(axis+'_ftol_normal_return')
            coords.append(need(read((axis,'ftol_eax')),axis+'_ftol_eax'))
        steps.append(('global',0x553fec))
        offset=need(read('storage_offset_dword'),'storage_offset')
        steps.append(('0045dc44',(pointer+offset)&0xffffffff))
        storage=need(read('storage_dword'),'storage_dword')
        steps.append(('global:first',0x553fe8))
        first_offset=need(read('initial_name_offset_dword'),'initial_name_offset')
        steps.append(('0045dc44',(pointer+first_offset)&0xffffffff))
        first=need(read('initial_name_dword'),'initial_name_dword')
        final_offset=first_offset
        if storage<16:
            steps.append(('global:second',0x553fe8))
            final_offset=need(read('inline_name_offset_dword'),'inline_name_offset')
        request=npc_text_request(pointer,final_offset,storage,first,signed_threshold=False)
        steps.append(('0045dca8',request.address,request.byte_count))
        readable=read('readable')
        copied=read('copied_bytes',request.byte_count) if readable is True and request.byte_count<=512 else None
        copy=replay_text_copy(request.byte_count,readable,copied)
        if copy.status not in ('complete','needs_codepage'):
            return out(False,'name_copy:'+copy.status)
        if not copy.ansi_bytes:
            seller=''
        else:
            if not callable(decode_name):return out(False,'needs_explicit_own_name_decoder')
            try:
                seller=decode_name(copy.ansi_bytes)
                if type(seller) is not str:raise ValueError('Decoder must return Unicode text')
            except (ValueError,OSError) as error:
                return out(False,'needs_own_name_conversion:'+str(error))
        return out(True,'own_actor_metadata_prepared',MerchantActorMetadata(seller,*coords))
    except Missing as error:
        return out(False,'needs_'+str(error))


@dataclass(frozen=True)
class MerchantReplyValuesPlan:
    complete: bool
    status: str
    actor: object
    lookup_results: object
    native_execution_verified: bool = False
    source_parser_return_verified: bool = False


def project_merchant_reply_values(payload,actor_observation,items,selection,decode_name=None,prior_records=()):
    """Stable supplied reply -> actor/item producers -> own records/rows."""
    data=decode_merchant_scan_data(payload)
    actor=None
    if data.source_length_gate_passed and any(s.item_id for s in data.slots):
        actor=plan_merchant_actor_metadata(data.entity_id,actor_observation,decode_name)
    result=project_merchant_scan_with_lookups(payload,
        actor.metadata if actor is not None and actor.complete else None,
        items,selection,decode_name,prior_records)
    pending=actor is not None and not actor.complete
    return MerchantReplyValuesPlan(result.complete and not pending,
        'actor:'+actor.status if pending else result.status,actor,result)
