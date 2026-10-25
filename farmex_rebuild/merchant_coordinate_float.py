"""Canonical signed-DWORD result-column text -> own IEEE754 binary32 policy.

This deliberately does not implement general Delphi StrToFloat, locale or
arbitrary edited UI text. Source FPU mode/extended value/lifetime stay separate.
"""
from dataclasses import dataclass
from merchant_result_rows import format_source_coordinate


@dataclass(frozen=True)
class MerchantCoordinateFloat:
    complete: bool
    status: str
    text: str
    signed_value: object=None
    float32_bits: object=None
    rounding_policy: str='own_nearest_even'
    native_source_execution_verified: bool=False
    live_compatibility_verified: bool=False


def _integer_binary32(value):
    if value==0:return 0
    sign=0x80000000 if value<0 else 0
    magnitude=abs(value);exponent=magnitude.bit_length()-1
    if exponent<=23:significand=magnitude<<(23-exponent)
    else:
        shift=exponent-23
        significand=magnitude>>shift;remainder=magnitude&((1<<shift)-1)
        half=1<<(shift-1)
        if remainder>half or (remainder==half and significand&1):significand+=1
        if significand==1<<24:significand>>=1;exponent+=1
    return sign|((exponent+127)<<23)|(significand&0x7fffff)


def plan_merchant_coordinate_float(text,*,rounding_policy='own_nearest_even'):
    if type(text) is not str:raise ValueError('Own canonical result-column Unicode text required')
    if rounding_policy!='own_nearest_even':
        return MerchantCoordinateFloat(False,'unsupported_rounding_policy',text,rounding_policy=rounding_policy)
    if not 1<=len(text)<=11:
        return MerchantCoordinateFloat(False,'outside_canonical_int32_format',text)
    try:value=int(text,10)
    except ValueError:return MerchantCoordinateFloat(False,'outside_canonical_int32_format',text)
    if not -0x80000000<=value<=0x7fffffff or str(value)!=text:
        return MerchantCoordinateFloat(False,'outside_canonical_int32_format',text)
    return MerchantCoordinateFloat(True,'own_integer_float32_prepared',text,value,_integer_binary32(value))


def merchant_coordinate_float_from_dword(value):
    return plan_merchant_coordinate_float(format_source_coordinate(value))
