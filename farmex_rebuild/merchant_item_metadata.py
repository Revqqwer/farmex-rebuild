"""Compose source lookup plans and existing captured-byte item-name model."""
from dataclasses import dataclass
from typing import Optional
from collections.abc import Mapping
from item_lookup import BaseItemLookupObservation, ExtensionLookupObservation, plan_base_item_lookup, plan_extension_lookup
from item_name import ItemNameObservation, plan_item_name
from merchant_result_filter import raw
from merchant_scan_reply_data import decode_merchant_scan_data
from merchant_scan_results import MerchantItemMetadata, project_merchant_scan_results


@dataclass(frozen=True)
class MerchantItemObservation:
    base: Optional[BaseItemLookupObservation] = None
    resolver_type_raw: Optional[int] = None
    extension: Optional[ExtensionLookupObservation] = None
    name_category_byte: Optional[int] = None
    extension_id_dword: Optional[int] = None
    name: Optional[ItemNameObservation] = None
    stored_category_byte: Optional[int] = None
    normalized_final_name: Optional[bytes] = None

    def __post_init__(self):
        for name,kind in [('base',BaseItemLookupObservation),('extension',ExtensionLookupObservation),('name',ItemNameObservation)]:
            value=getattr(self,name)
            if value is not None and not isinstance(value,kind):raise ValueError('Typed '+name+' observation required')
        for name,bits in [('resolver_type_raw',32),('name_category_byte',8),('extension_id_dword',32),('stored_category_byte',8)]:
            value=getattr(self,name)
            if value is not None:raw(value,bits,name)
        if self.normalized_final_name is not None and type(self.normalized_final_name) is not bytes:
            raise ValueError('Explicit normalized final name bytes required')


@dataclass(frozen=True)
class MerchantMetadataPlan:
    complete: bool
    status: str
    metadata: object = None
    base: object = None
    extension: object = None
    name: object = None
    reads: tuple = ()
    native_execution_verified: bool = False
    native_text_conversion_verified: bool = False


def plan_merchant_item_metadata(item_id, observation=None, decode_name=None,*,_observation_reader=None):
    """Own stable producer; decoder is an explicit local conversion policy.

    Every ItemNameObservation field belongs to the fresh name-helper invocation,
    not to earlier lookup reads. Zero provided pointers may make that helper
    perform its own new lookup; the existing model preserves that behavior.
    """
    raw(item_id,32,'item ID')
    o=MerchantItemObservation() if observation is None else observation
    if not isinstance(o,MerchantItemObservation):raise ValueError('Typed merchant item observations required')
    def read(path,required_count=None):
        path=(path,) if type(path) is str else path
        if _observation_reader is not None:return _observation_reader(path,required_count)
        node=o
        for name in path:
            if node is None:return None
            node=getattr(node,name)
        return node
    base=plan_base_item_lookup(item_id,o.base,_observation_reader=lambda name:read(('base',name)))
    extension=None;name=None;reads=[]
    def out(complete,status,metadata=None):
        return MerchantMetadataPlan(complete,status,metadata,base,extension,name,tuple(reads))
    if not base.complete:return out(False,'base:'+base.status)
    lookup=base.result_eax
    reads.append(((lookup+4)&0xffffffff,'0045dbdc:resolver_type'))
    resolver=read('resolver_type_raw')
    if resolver is None:return out(False,'needs_resolver_type')
    extension=plan_extension_lookup(item_id,resolver,o.extension,_observation_reader=lambda name:read(('extension',name)))
    if not extension.complete:return out(False,'extension:'+extension.status)
    pointer=extension.result_eax
    reads.append(((pointer+0x4c)&0xffffffff,'0045dbdc:name_category'))
    category=read('name_category_byte')
    if category is None:return out(False,'needs_name_category')
    reads.append((pointer,'0045dc44:extension_id'))
    extension_id=read('extension_id_dword')
    if extension_id is None:return out(False,'needs_extension_id')
    name=plan_item_name(item_id,o.name or ItemNameObservation(),provided_lookup=lookup,provided_metadata=pointer,
        _observation_reader=lambda field,count=None:read(('name',field),count))
    if name.ansi_bytes is None:return out(False,'name:'+name.status)
    if not callable(decode_name):return out(False,'needs_explicit_own_name_decoder')
    try:
        text=decode_name(name.ansi_bytes)
        if type(text) is not str:raise ValueError('Decoder must return Unicode text')
    except (ValueError,OSError) as error:
        return out(False,'needs_own_name_conversion:'+str(error))
    reads.append(((pointer+0x4c)&0xffffffff,'0045dbdc:stored_category'))
    stored_category=read('stored_category_byte')
    if stored_category is None:return out(False,'needs_stored_category')
    metadata=MerchantItemMetadata(text,category,stored_category,
        extension_id,read('normalized_final_name'),name.ansi_bytes)
    return out(True,'own_metadata_prepared',metadata)


@dataclass(frozen=True)
class MerchantLookupResultsPlan:
    complete: bool
    status: str
    results: object
    item_plans: tuple = ()
    native_execution_verified: bool = False
    source_parser_return_verified: bool = False


def project_merchant_scan_with_lookups(payload,actor,items,selection,decode_name=None,prior_records=()):
    """Join reached slot IDs to metadata producers and the own row pipeline.

    Uses immutable own snapshots; it is not a resumable native event frame.
    Missing metadata preserves earlier projected records without completing
    dispatcher helper receipts or creating game/UI side effects.
    """
    if not isinstance(items,Mapping) or any(type(k) is not int or not 0<=k<12 or not isinstance(v,MerchantItemObservation) for k,v in items.items()):
        raise ValueError('Slot-indexed typed item observations required')
    data=decode_merchant_scan_data(payload)
    metadata={};plans=[];pending=None
    # Actor production precedes per-slot item production in source. Do not
    # consume item observations when an actor needed by a record is unknown.
    if actor is not None and data.source_length_gate_passed:
        for slot in data.slots:
            if slot.item_id==0:continue
            plan=plan_merchant_item_metadata(slot.item_id,items.get(slot.index),decode_name)
            plans.append((slot.index,plan))
            if not plan.complete:
                pending=plan.status
                break
            metadata[slot.index]=plan.metadata
    results=project_merchant_scan_results(payload,actor,metadata,selection,prior_records)
    return MerchantLookupResultsPlan(results.complete and pending is None,
        'item_metadata:'+pending if pending else results.status,results,tuple(plans))
