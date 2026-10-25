"""Exact rational SELL x87 arithmetic and disk-CRT __ftol normal subset.

Explicit fully masked, clean x87 context only; no host float arithmetic or IO.
"""
from dataclasses import dataclass
from fractions import Fraction
from crt_rng import CRT_SOURCE_SHA256

COEFFICIENT_BITS=0x3f9eb851eb851eb8
COEFFICIENT=Fraction((1<<52)|(COEFFICIENT_BITS&((1<<52)-1)),1<<58)

@dataclass(frozen=True)
class SellX87Sample:
    control_word:object=None
    clean_context:object=None # Clean status, two free x87 stack slots, stable CW.
    def __post_init__(self):
        if self.control_word is not None and (type(self.control_word) is not int or not 0<=self.control_word<1<<16):
            raise ValueError('Raw x87 control WORD required')
        if self.clean_context is not None and type(self.clean_context) is not bool:raise ValueError('Explicit clean-context observation required')

@dataclass(frozen=True)
class SellX87Plan:
    complete:bool
    net_qword:object=None
    precision_bits:object=None
    rounding_code:object=None
    multiply_fraction:object=None
    subtract_fraction:object=None
    restored_control_word:object=None
    missing:str=''
    source_sha256:str=CRT_SOURCE_SHA256
    loaded_game_runtime_verified:bool=False

def _power2(exponent):
    return Fraction(1<<exponent) if exponent>=0 else Fraction(1,1<<-exponent)

def _round_binary(value,precision,rounding):
    if value==0:return Fraction(0)
    magnitude=abs(value)
    exponent=magnitude.numerator.bit_length()-magnitude.denominator.bit_length()
    if magnitude<_power2(exponent):exponent-=1
    quantum=_power2(exponent-precision+1)
    scaled=value/quantum;floor=scaled.numerator//scaled.denominator
    remainder=scaled.numerator-floor*scaled.denominator
    if rounding==0:
        twice=2*remainder
        increment=twice>scaled.denominator or (twice==scaled.denominator and floor&1)
    elif rounding==1:increment=False # toward -infinity
    elif rounding==2:increment=remainder!=0 # toward +infinity
    else:increment=scaled<0 and remainder!=0 # toward zero
    return (floor+int(increment))*quantum

def plan_sell_x87(total_qword,sample):
    if type(total_qword) is not int or not 0<=total_qword<1<<64 or not isinstance(sample,SellX87Sample):
        raise ValueError('Raw accumulated QWORD and typed x87 context required')
    cw=sample.control_word
    if cw is None:return SellX87Plan(False,missing='source x87 control WORD')
    if sample.clean_context is not True:return SellX87Plan(False,missing='clean source x87 context')
    if cw&0x3f!=0x3f:return SellX87Plan(False,missing='unmasked x87 exceptions outside normal replay subset')
    if cw&0xe080 or not cw&0x40:return SellX87Plan(False,missing='unsupported reserved x87 control bits')
    precision={0:24,2:53,3:64}.get((cw>>8)&3)
    if precision is None:return SellX87Plan(False,missing='reserved precision-control encoding')
    rounding=(cw>>10)&3
    integer=total_qword if total_qword<1<<63 else total_qword-(1<<64)
    # FILD signed64 is exact; PC/RC round each FMUL and FSUBP result separately.
    product=_round_binary(Fraction(integer)*COEFFICIENT,precision,rounding)
    difference=_round_binary(Fraction(integer)-product,precision,rounding)
    converted=(abs(difference.numerator)//difference.denominator)*(-1 if difference<0 else 1)
    if not -(1<<63)<=converted<1<<63:return SellX87Plan(False,missing='FISTP overflow outside normal subset')
    # Disk __ftol ORs0xc01 into CW for FISTP, then FCLEX and restores CW.
    return SellX87Plan(True,converted&0xffffffffffffffff,precision,rounding,
        (product.numerator,product.denominator),(difference.numerator,difference.denominator),cw)
