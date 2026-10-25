"""Own stable raw-reply -> explicit metadata -> result-row composition.

Does not synthesize native helper receipts or replace the interleaved source
parser/append/UI execution with a claimed equivalent runtime.
"""
from dataclasses import dataclass
from typing import Optional, Tuple
from collections.abc import Mapping
from merchant_result_filter import MerchantResultRecord, MerchantFilterSelection, raw
from merchant_result_rows import MerchantDisplayRecord, MerchantRowsPlan, build_merchant_result_rows
from merchant_scan_reply_data import MerchantScanDataPlan, decode_merchant_scan_data


@dataclass(frozen=True)
class MerchantActorMetadata:
    seller: str
    x_dword: int
    y_dword: int

    def __post_init__(self):
        if type(self.seller) is not str:
            raise ValueError('Explicit own decoded seller text required')
        raw(self.x_dword,32,'actor X')
        raw(self.y_dword,32,'actor Y')


@dataclass(frozen=True)
class MerchantItemMetadata:
    base_name: str
    name_category_byte: int
    stored_category_byte: int
    extension_id_dword: int
    normalized_final_name: Optional[bytes] = None
    base_name_ansi: Optional[bytes] = None

    def __post_init__(self):
        if type(self.base_name) is not str:
            raise ValueError('Explicit own decoded item base name required')
        raw(self.name_category_byte,8,'name-time category')
        raw(self.stored_category_byte,8,'record-time category')
        raw(self.extension_id_dword,32,'extension ID')
        if self.normalized_final_name is not None and type(self.normalized_final_name) is not bytes:
            raise ValueError('Explicit normalized final-name bytes required')
        if self.base_name_ansi is not None and type(self.base_name_ansi) is not bytes:
            raise ValueError('Original immutable base-name ANSI bytes required')


@dataclass(frozen=True)
class BoundMerchantRecord:
    slot_index: int
    item_id: int
    extension_digit: int
    final_flag: int
    display: MerchantDisplayRecord


@dataclass(frozen=True)
class MerchantScanResultsPlan:
    complete: bool
    status: str
    raw_data: MerchantScanDataPlan
    records: Tuple[BoundMerchantRecord, ...]
    added_count: int = 0
    stopped_slot: Optional[int] = None
    rows: Optional[MerchantRowsPlan] = None
    native_execution_verified: bool = False
    source_parser_return_verified: bool = False
    live_compatibility_verified: bool = False


def format_scanned_item_name(metadata):
    if not isinstance(metadata,MerchantItemMetadata):
        raise ValueError('Typed item metadata required')
    category=metadata.name_category_byte
    name=metadata.base_name
    if category in (1,2,5,11):
        name+='(+'+str(metadata.extension_id_dword % 10)+')'
    if category in (11,12):
        name+=' (Reverse)'
    return name


def format_scanned_item_ansi(metadata):
    """Keep captured base bytes; append pinned ASCII suffix literals only."""
    if not isinstance(metadata,MerchantItemMetadata):raise ValueError('Typed item metadata required')
    if metadata.base_name_ansi is None:return None
    name=metadata.base_name_ansi
    if metadata.name_category_byte in (1,2,5,11):
        name+=b'(+'+str(metadata.extension_id_dword % 10).encode('ascii')+b')'
    if metadata.name_category_byte in (11,12):name+=b' (Reverse)'
    return name


def project_merchant_scan_results(payload, actor, items, selection, prior_records=()):
    """Compose owned values, keeping appended records even if search is missing.

    Actor X/Y are explicit post-conversion DWORDs; no Python float rounding
    substitutes for the source helper/__ftol. Item categories are two separate
    reads. Existing records are retained in order without guessed deduplication.
    A decoded raw prefix is not a native parse success receipt.
    """
    if actor is not None and not isinstance(actor,MerchantActorMetadata):
        raise ValueError('Typed actor metadata or explicit unknown required')
    if not isinstance(items,Mapping) or any(type(k) is not int or not 0<=k<12 or not isinstance(v,MerchantItemMetadata) for k,v in items.items()):
        raise ValueError('Explicit slot-indexed metadata required')
    if not isinstance(selection,MerchantFilterSelection):
        raise ValueError('Typed stable filter selection required')
    if type(prior_records) is not tuple or any(not isinstance(r,BoundMerchantRecord) for r in prior_records):
        raise ValueError('Immutable own prior records required')
    data=decode_merchant_scan_data(payload)
    records=list(prior_records)
    added=0

    def output(complete,status,stopped=None,with_rows=False):
        rows=build_merchant_result_rows(tuple(r.display for r in records),selection,finalize_rebuild=False) if with_rows else None
        # Completed metadata binding can still encounter a missing search input.
        if rows is not None and not rows.formatting_complete:
            complete=False
            status='rows:'+rows.status
        return MerchantScanResultsPlan(complete,status,data,tuple(records),added,stopped,rows)

    if not data.source_length_gate_passed:
        return output(True,'source_length_rejected')
    for slot in data.slots:
        if slot.item_id==0:
            continue
        if actor is None:
            return output(False,'needs_actor_metadata',slot.index)
        metadata=items.get(slot.index)
        if metadata is None:
            return output(False,'needs_item_metadata',slot.index)
        display=MerchantDisplayRecord(
            MerchantResultRecord(data.direction,metadata.stored_category_byte,
                slot.word_a,slot.word_b,metadata.normalized_final_name,format_scanned_item_ansi(metadata)),
            actor.seller,format_scanned_item_name(metadata),slot.price,
            actor.x_dword,actor.y_dword)
        records.append(BoundMerchantRecord(slot.index,slot.item_id,
            metadata.extension_id_dword % 10,0,display))
        added+=1
    if not data.complete:
        return output(False,'raw_data:'+data.status,data.stopped_slot,True)
    return output(True,'own_records_and_rows_prepared',with_rows=True)
