"""Own stable merchant result columns, before unverified native sorting."""
from dataclasses import dataclass, replace
from typing import Tuple
from merchant_result_filter import MerchantResultRecord, MerchantFilterSelection, MerchantFilterPlan, filter_merchant_results, raw


@dataclass(frozen=True)
class MerchantDisplayRecord:
    filter_record: MerchantResultRecord
    seller: str
    item_name: str
    price_14: int
    x_04: int
    y_08: int

    def __post_init__(self):
        if not isinstance(self.filter_record, MerchantResultRecord):
            raise ValueError('Typed filter record required')
        if type(self.seller) is not str or type(self.item_name) is not str:
            raise ValueError('Explicit own decoded display text required')
        for name in ('price_14', 'x_04', 'y_08'):
            raw(getattr(self, name), 32, name)


@dataclass(frozen=True)
class MerchantResultRow:
    record_index: int
    caption: str
    subitems: Tuple[str, ...]


@dataclass(frozen=True)
class MerchantRowsPlan:
    filter_plan: MerchantFilterPlan
    rows: Tuple[MerchantResultRow, ...]
    status: str
    formatting_complete: bool
    sorting_verified: bool = False
    ui_execution_verified: bool = False
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False


def format_source_price(value):
    """Normal zero-extended DWORD path of 0046063c; fixed dot groups."""
    raw(value, 32, 'price')
    digits = str(value)
    groups = []
    while digits:
        groups.append(digits[-3:])
        digits = digits[:-3]
    return '.'.join(reversed(groups))


def format_source_coordinate(value):
    """00407360 uses UTF16 %i: interpret raw DWORD as signed int32."""
    raw(value, 32, 'coordinate')
    return str(value if value < 0x80000000 else value - 0x100000000)


def build_merchant_result_rows(records, selection, finalize_rebuild=True):
    """Build source-shaped columns in snapshot order; never fake AlphaSort.

    Decoded seller and item strings are explicit own inputs. Actual native
    conversion and lifetime are not reconstructed by this formatting API.
    """
    if type(records) is not tuple or any(not isinstance(r, MerchantDisplayRecord) for r in records):
        raise ValueError('Immutable typed display records required')
    if not isinstance(selection, MerchantFilterSelection):
        raise ValueError('Typed filter selection required')
    if type(finalize_rebuild) is not bool:
        raise ValueError('Explicit rebuild finalization bool required')
    filtered = filter_merchant_results(tuple(r.filter_record for r in records), selection)
    if not finalize_rebuild:
        # Reply parser appends inline; it does not clear or invoke AlphaSort.
        filtered = replace(filtered, clear_requested=False, final_sort_column=None,
            alpha_sort_requested=False)
    rows = []
    for match in filtered.matches:
        record = records[match.record_index]
        rows.append(MerchantResultRow(match.record_index, record.seller, (
            record.item_name, str(match.amount), format_source_price(record.price_14),
            'PM', 'GİT', format_source_coordinate(record.x_04), format_source_coordinate(record.y_08),
        )))
    return MerchantRowsPlan(filtered, tuple(rows),
        ('rows_prepared_sort_pending' if finalize_rebuild else 'rows_prepared') if filtered.complete else filtered.status,
        filtered.complete)
