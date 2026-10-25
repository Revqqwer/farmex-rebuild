"""Stable merchant price parser and compare callback result projection.

Native text/StrToInt normal-return values remain explicit observations.
This is not an implementation of the VCL sorting algorithm.
"""
from dataclasses import dataclass
from typing import Optional
from rtl_integer import parse_rtl_integer
from merchant_result_filter import raw
from merchant_result_rows import MerchantResultRow


@dataclass(frozen=True)
class MerchantPriceParse:
    complete: bool
    status: str
    qword: Optional[int] = None
    parser_text: Optional[str] = None
    parser_code: Optional[int] = None
    native_execution_verified: bool = False


def parse_merchant_price_bytes(text):
    """0045edfc whitelist, then 00460fa4 length-dependent dot removal.

    Bytes are an explicit owned ANSI snapshot including its logical length;
    an embedded NUL is not silently treated as the end of this input.
    """
    if type(text) is not bytes:
        raise ValueError('Explicit own ANSI bytes required')
    if any(b not in b'0123456789.' for b in text):
        return MerchantPriceParse(True, 'validator_rejected_zero', 0)
    cleaned = text if len(text) <= 3 else text.replace(b'.', b'')
    unicode_text = cleaned.decode('ascii')
    parsed = parse_rtl_integer(unicode_text)
    if not parsed.accepted:
        return MerchantPriceParse(False, 'needs_native_parser_exception_path',
            parser_text=unicode_text, parser_code=parsed.code)
    return MerchantPriceParse(True, 'parsed', parsed.qword, unicode_text, 0)


@dataclass(frozen=True)
class MerchantCompareObservation:
    compare_text_result: Optional[int] = None
    ansi_compare_text_result: Optional[int] = None
    first_quantity_eax: Optional[int] = None
    second_quantity_eax: Optional[int] = None

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if value is not None:
                raw(value, 32, name)


@dataclass(frozen=True)
class MerchantComparePlan:
    complete: bool
    status: str
    result_dword: Optional[int] = None
    result_written: bool = False
    first_price: Optional[MerchantPriceParse] = None
    second_price: Optional[MerchantPriceParse] = None
    native_execution_verified: bool = False
    sorting_verified: bool = False
    text_policy: Optional[str] = None
    first_quantity: object = None
    second_quantity: object = None
    integer_policy: Optional[str] = None

    @property
    def signed_result(self):
        value = self.result_dword
        return None if value is None else value if value < 0x80000000 else value - 0x100000000


def compare_merchant_rows(first, second, column, observation=None, previous_result=None, *, use_owned_text_model=False, use_owned_integer_model=False):
    """Normal-value callback result, preserving DWORD SUB and unwritten cases.

    CompareText/AnsiCompareText observations refer to first versus second.
    Quantity EAX observations are reached in first-then-second order. Price
    parsing reuses the verified own scalar model on explicit ASCII row text.
    """
    if not isinstance(first, MerchantResultRow) or not isinstance(second, MerchantResultRow):
        raise ValueError('Typed own result rows required')
    raw(column, 32, 'column')
    if type(use_owned_text_model) is not bool:
        raise ValueError('Explicit own text model selection required')
    if type(use_owned_integer_model) is not bool:
        raise ValueError('Explicit own integer model selection required')
    if previous_result is not None:
        raw(previous_result, 32, 'previous comparison result')
    if observation is None:
        observation = MerchantCompareObservation()
    if not isinstance(observation, MerchantCompareObservation):
        raise ValueError('Typed independent comparison observations required')
    if column not in (0, 1, 2, 3):
        return MerchantComparePlan(True, 'result_unchanged', previous_result)
    if column in (0, 1):
        name = 'compare_text_result' if column == 0 else 'ansi_compare_text_result'
        value = getattr(observation, name)
        if value is None and use_owned_text_model:
            from rtl_text_compare import compare_text_pinned, ansi_compare_text_local
            if column==0:
                value=compare_text_pinned(first.caption,second.caption)&0xffffffff
                return MerchantComparePlan(True,'own_text_result',value,True,text_policy='pinned_RTL_ASCII_fold_UTF16_pair')
            if not first.subitems or not second.subitems:
                return MerchantComparePlan(False,'needs_item_name_subitem',previous_result)
            try:
                result=ansi_compare_text_local(first.subitems[0],second.subitems[0])
            except OSError:
                return MerchantComparePlan(False,'needs_local_Windows_collation',previous_result)
            return MerchantComparePlan(True,'own_text_result',result.signed_result&0xffffffff,True,text_policy='local_Windows_CompareStringW_locale0400_flags1')
        if value is None:
            return MerchantComparePlan(False, 'needs_' + name, previous_result)
        return MerchantComparePlan(True, 'normal_result', value, True)
    if column == 2:
        values=[];parsed=[]
        for label,row,captured in [('first',first,observation.first_quantity_eax),('second',second,observation.second_quantity_eax)]:
            if captured is not None:
                values.append(captured);parsed.append(None);continue
            if not use_owned_integer_model:
                return MerchantComparePlan(False,'needs_'+label+'_StrToInt_return',previous_result)
            if len(row.subitems)<2:
                return MerchantComparePlan(False,'needs_'+label+'_quantity_subitem',previous_result,
                    first_quantity=parsed[0] if parsed else None)
            from rtl_integer32 import parse_rtl_integer32
            item=parse_rtl_integer32(row.subitems[1]);parsed.append(item)
            if not item.accepted:
                return MerchantComparePlan(False,label+'_quantity:needs_native_StrToInt_exception_path',previous_result,
                    first_quantity=parsed[0],second_quantity=parsed[1] if len(parsed)>1 else None)
            values.append(item.dword)
        value=(values[0]-values[1])&0xffffffff
        return MerchantComparePlan(True,'normal_result',value,True,
            first_quantity=parsed[0],second_quantity=parsed[1],
            integer_policy='pinned_RTL_ValLong_scalar' if any(item is not None for item in parsed) else None)
    if len(first.subitems) < 3 or len(second.subitems) < 3:
        return MerchantComparePlan(False, 'needs_price_subitem', previous_result)
    try:
        first_bytes = first.subitems[2].encode('ascii')
    except UnicodeEncodeError:
        return MerchantComparePlan(False, 'needs_first_native_ANSI_conversion', previous_result)
    a = parse_merchant_price_bytes(first_bytes)
    if not a.complete:
        return MerchantComparePlan(False, 'first_price:' + a.status, previous_result, first_price=a)
    try:
        second_bytes = second.subitems[2].encode('ascii')
    except UnicodeEncodeError:
        return MerchantComparePlan(False, 'needs_second_native_ANSI_conversion', previous_result, first_price=a)
    b = parse_merchant_price_bytes(second_bytes)
    if not b.complete:
        return MerchantComparePlan(False, 'second_price:' + b.status, previous_result, first_price=a, second_price=b)
    # Source ignores parser EDX and performs SUB EBX,EAX, not a signed64 cmp.
    value = ((a.qword & 0xffffffff) - (b.qword & 0xffffffff)) & 0xffffffff
    return MerchantComparePlan(True, 'normal_result', value, True, a, b)


@dataclass(frozen=True)
class MerchantAlphaSortPlan:
    complete: bool
    status: str
    send_requested: bool = False
    hwnd: Optional[int] = None
    message: int = 0x1030
    wparam: int = 0
    callback_va: int = 0x50d8de0c
    result_bool: Optional[bool] = None
    sorted_order_verified: bool = False
    native_execution_verified: bool = False


def plan_merchant_alpha_sort(handle_allocated=None, hwnd=None, message_result=None):
    """Pinned vcl260 AlphaSort normal return; produce no actual message.

    Callback VA is specific to vcl260 SHA84ea9ebb... and is never invoked.
    A nonzero SendMessage result proves only its own BOOL conversion, not an
    order certificate. No Python algorithm substitutes for the native sort.
    """
    if handle_allocated is not None and type(handle_allocated) is not bool:
        raise ValueError('Explicit HandleAllocated bool observation required')
    if hwnd is not None:
        raw(hwnd, 32, 'own handle observation')
    if message_result is not None:
        raw(message_result, 32, 'SendMessage return')
    if handle_allocated is None:
        return MerchantAlphaSortPlan(False, 'needs_HandleAllocated')
    if not handle_allocated:
        return MerchantAlphaSortPlan(True, 'no_allocated_handle', result_bool=False)
    if hwnd is None:
        return MerchantAlphaSortPlan(False, 'needs_handle_return')
    if message_result is None:
        return MerchantAlphaSortPlan(False, 'needs_SendMessage_return', True, hwnd)
    return MerchantAlphaSortPlan(True, 'normal_result', True, hwnd, result_bool=message_result != 0)
