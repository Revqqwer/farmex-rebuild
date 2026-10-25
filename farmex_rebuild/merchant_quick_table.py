"""Owned captured quick-scan -> explicit Windows text decode -> table records.

No default empty lookup, host codepage fallback or native completion receipt.
"""
from dataclasses import dataclass
from collections.abc import Mapping
from types import MappingProxyType
from merchant_quick_scan import QuickActorObservation,project_quick_scan,optional_raw
from merchant_result_filter import MerchantResultRecord
from merchant_result_rows import MerchantDisplayRecord
from name_codec import WindowsNameCodec
from merchant_quick_source import QuickSourceSnapshot,produce_quick_sources


@dataclass(frozen=True)
class QuickScanSnapshot:
    actors:object
    code_page:object=None
    initial_direction_byte:object=None
    def __post_init__(self):
        if not isinstance(self.actors,Mapping) or any(type(k) is not int or not 1<=k<=5000 or not isinstance(v,QuickActorObservation) for k,v in self.actors.items()):raise ValueError('Typed lookup snapshot1..5000 required')
        if self.code_page is not None and (type(self.code_page) is not int or not 1<=self.code_page<=65535):raise ValueError('Explicit nonzero Windows codepage or unknown required')
        optional_raw(self.initial_direction_byte,8,'captured initial direction byte')
        object.__setattr__(self,'actors',MappingProxyType(dict(self.actors)))


@dataclass(frozen=True)
class QuickTableProjection:
    complete:bool
    status:str
    quick_values:object=None
    display_records:tuple=()
    code_page:object=None
    failed_record:object=None
    error:object=None
    source_helper_returns_verified:bool=False
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False
    source_production:object=None


def prepare_quick_table(snapshot,*,codec_factory=WindowsNameCodec):
    if snapshot is None:return QuickTableProjection(False,'needs_quick_scan_provider')
    source=None
    if isinstance(snapshot,QuickSourceSnapshot):
        source=produce_quick_sources(snapshot)
        snapshot=QuickScanSnapshot(source.actors,source.code_page,source.initial_direction_byte)
    if not isinstance(snapshot,QuickScanSnapshot):raise ValueError('Typed quick-scan snapshot required')
    q=project_quick_scan(snapshot.actors,initial_direction_byte=snapshot.initial_direction_byte)
    records=[];index=None
    def result(ok,status,error=None):
        return QuickTableProjection(ok,status,q,tuple(records),snapshot.code_page,index if not ok else None,error,source_production=source)
    if source is not None and not source.complete:return result(False,'needs_source_production')
    if not q.complete:return result(False,'needs_quick_values')
    if not q.records:return result(True,'own_table_records_prepared')
    if snapshot.code_page is None:return result(False,'needs_explicit_codepage')
    try:
        codec=codec_factory(snapshot.code_page)
        for index,r in enumerate(q.records):
            seller=codec.decode(r.seller_ansi);name=codec.decode(r.item_name_ansi)
            records.append(MerchantDisplayRecord(
                MerchantResultRecord(r.direction_byte,r.category_byte,r.amount_dword,
                    r.alternate_amount_dword,None,r.item_name_ansi),
                seller,name,r.price_dword,r.x_dword,r.y_dword))
    except (ValueError,OSError) as e:return result(False,'own_decode_failed',str(e))
    return result(True,'own_table_records_prepared')
