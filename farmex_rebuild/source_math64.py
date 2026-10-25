"""Integer result semantics of source helpers00503e38 and00503e75.

Pure arithmetic, not native register/stack/SEH execution. In particular the
software division helper wraps MIN_INT64/-1 rather than using CPU IDIV64.
"""
from dataclasses import dataclass

MASK64=(1<<64)-1

def _qword(value):
    if type(value) is not int or not 0 <= value <= MASK64:
        raise ValueError('Raw unsigned QWORD required')
    return value

def multiply64_bits(left,right):
    return (_qword(left)*_qword(right))&MASK64

@dataclass(frozen=True)
class Divide64Result:
    complete:bool
    eax:object=None
    edx:object=None
    qword:object=None
    path:str=''
    cpu_divide_error:bool=False
    native_execution_verified:bool=False
    exception_delivery_verified:bool=False

def divide64_bits(dividend,divisor):
    dividend=_qword(dividend);divisor=_qword(divisor)
    nh=dividend>>32;dh=divisor>>32;dl=divisor&0xffffffff
    fast=dh==0 and (nh==0 or dl==0)
    if fast and dl==0:
        return Divide64Result(False,path='source_DIV_EBX',cpu_divide_error=True)
    if fast:
        quotient=(dividend&0xffffffff)//dl
        return Divide64Result(True,quotient,0,quotient,'source_DIV_EBX')
    n=dividend if dividend<1<<63 else dividend-(1<<64)
    d=divisor if divisor<1<<63 else divisor-(1<<64)
    # Nonzero divisor is guaranteed on this source slow path. Magnitude
    # division and two's-complement negation match its64-iteration loop.
    quotient=abs(n)//abs(d)
    if (n<0)!=(d<0):quotient=-quotient
    bits=quotient&MASK64
    return Divide64Result(True,bits&0xffffffff,bits>>32,bits,'source_64_step_loop')

@dataclass(frozen=True)
class SessionRatio:
    complete:bool
    product_bits:int
    division:Divide64Result
    result_byte:object=None
    first_source_getter:str='004626f8 denominator'
    second_source_getter:str='004626d8 numerator'
    getters_verified:bool=False
    native_execution_verified:bool=False

def session_ratio(numerator,denominator):
    product=multiply64_bits(numerator,100)
    result=divide64_bits(product,denominator)
    return SessionRatio(result.complete,product,result,
                        result.eax&255 if result.complete else None)

def build_status_from_ratio(values_without_ratio,serialized_name,*,numerator,denominator,
                            entry_observed=False,transform_length_word=None):
    """Bind derived full EAX into the owned wire serializer; no fault fallback."""
    from session_status_wire import SessionStatusPrepared,build_session_status_wire
    values=dict(values_without_ratio)
    if 'ratio_division_eax' in values:
        raise ValueError('Derived ratio cannot also be supplied as an independent capture')
    ratio=session_ratio(numerator,denominator)
    if not ratio.complete:return ratio,None
    values['ratio_division_eax']=ratio.division.eax
    wire=build_session_status_wire(SessionStatusPrepared(values,serialized_name),
        entry_observed=entry_observed,transform_length_word=transform_length_word)
    return ratio,wire
