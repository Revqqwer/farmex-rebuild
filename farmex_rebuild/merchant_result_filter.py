"""Stable normal-value merchant result filtering from 004bad1c.

Normalization bytes are explicit inputs. Native locale conversion, vector
mutation, managed lifetimes and actual VCL sorting are not simulated here.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

CATEGORY_CODES = {
    'Magic Item': 1, 'Rare Item': 2, 'Craft Item': 3,
    'Unique Item': 4, 'Upgrade Item': 5,
    'Rebirth Item': 11, 'Rebirth Unique Item': 12,
}


def raw(value, bits, name):
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError(name + ' requires raw unsigned value')
    return value


@dataclass(frozen=True)
class MerchantResultRecord:
    direction_0c: int
    category_1c: int
    amount_20: int
    alternate_amount_24: int
    normalized_name: Optional[bytes] = None
    original_name_ansi: Optional[bytes] = None

    def __post_init__(self):
        raw(self.direction_0c, 8, 'direction')
        raw(self.category_1c, 8, 'category')
        raw(self.amount_20, 32, 'amount')
        raw(self.alternate_amount_24, 32, 'alternate amount')
        if self.normalized_name is not None and type(self.normalized_name) is not bytes:
            raise ValueError('Explicit normalized byte name required')
        if self.original_name_ansi is not None and type(self.original_name_ansi) is not bytes:
            raise ValueError('Original immutable ANSI name required')


@dataclass(frozen=True)
class MerchantFilterSelection:
    kind_text: str
    category_text: str
    search_font_color: Optional[int] = None
    search_length_dword: Optional[int] = None
    normalized_search: Optional[bytes] = None

    def __post_init__(self):
        if type(self.kind_text) is not str or type(self.category_text) is not str:
            raise ValueError('Own stable control text required')
        if self.search_font_color is not None:
            raw(self.search_font_color, 32, 'font color')
        if self.search_length_dword is not None:
            raw(self.search_length_dword, 32, 'Unicode length')
        if self.normalized_search is not None and type(self.normalized_search) is not bytes:
            raise ValueError('Explicit normalized search bytes required')

    @property
    def direction(self):
        # Default is zero; only the Buying Merchant comparison sets one.
        return int(self.kind_text == 'Buying Merchant')

    @property
    def category(self):
        # Tumu and every unmatched literal retain the source -1 sentinel.
        return CATEGORY_CODES.get(self.category_text, -1)


@dataclass(frozen=True)
class MerchantResultMatch:
    record_index: int
    amount: int
    amount_field: str


@dataclass(frozen=True)
class MerchantFilterPlan:
    complete: bool
    status: str
    matches: Tuple[MerchantResultMatch, ...] = ()
    stopped_index: Optional[int] = None
    clear_requested: bool = True
    final_sort_column: Optional[int] = None
    alpha_sort_requested: bool = False
    native_execution_verified: bool = False
    ui_execution_verified: bool = False
    live_compatibility_verified: bool = False


def filter_merchant_results(records, selection):
    """Project an immutable own snapshot; retain prefix on missing input.

    Explicit normalized bytes preserve source CString NUL termination and
    case-sensitive byte search. This function never guesses locale uppercase.
    Source callbacks' initialization gate is outside this normal-value API.
    """
    if type(records) is not tuple or any(not isinstance(r, MerchantResultRecord) for r in records):
        raise ValueError('Immutable typed own records required')
    if not isinstance(selection, MerchantFilterSelection):
        raise ValueError('Typed filter selection required')
    matches = []
    for index, record in enumerate(records):
        if record.direction_0c != selection.direction:
            continue
        if selection.category != -1 and record.category_1c != selection.category:
            continue
        def missing(name):
            return MerchantFilterPlan(False, 'needs_' + name, tuple(matches), index)
        if selection.search_font_color is None:
            return missing('search_font_color')
        if selection.search_font_color == 0:
            length = selection.search_length_dword
            if length is None:
                return missing('search_length')
            # Source SETG checks a signed 32-bit Unicode length.
            if 0 < length < 0x80000000:
                if selection.normalized_search is None:
                    return missing('normalized_search')
                if record.normalized_name is None:
                    return missing('normalized_name')
                needle = selection.normalized_search.split(b'\0', 1)[0]
                haystack = record.normalized_name.split(b'\0', 1)[0]
                if haystack.find(needle) == -1:
                    continue
        if record.category_1c == 0 and record.alternate_amount_24 > 1:
            amount, field = record.alternate_amount_24, '+0x24'
        else:
            amount, field = record.amount_20, '+0x20'
        matches.append(MerchantResultMatch(index, amount, field))
    return MerchantFilterPlan(True, 'projected', tuple(matches), final_sort_column=3, alpha_sort_requested=True)
