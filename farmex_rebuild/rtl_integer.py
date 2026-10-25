"""Pinned _ValInt64 scalar path for immutable, well-formed UTF16 strings.

Reconstructs result bits and Code, including invalid partial results. Does not
execute native code, raise Delphi exceptions, or emulate string lifetime.
"""
from dataclasses import dataclass

MASK64=(1<<64)-1

@dataclass(frozen=True)
class RtlIntegerResult:
    qword:int
    code:int
    radix:int=10
    negative:bool=False
    @property
    def accepted(self):return self.code==0
    @property
    def signed(self):return self.qword if self.qword<1<<63 else self.qword-(1<<64)

@dataclass(frozen=True)
class RtlDefaultIntegerResult:
    parser:RtlIntegerResult
    result_qword:int
    used_default:bool
    native_bot_catch_verified:bool=False

def rtl_integer_or_default(text,default_dword):
    """Independent wrapper policy; does not synthesize a native EH receipt."""
    if type(default_dword) is not int or not 0<=default_dword<=0xffffffff:raise ValueError('Raw fallback DWORD required')
    parser=parse_rtl_integer(text)
    default=default_dword if default_dword<1<<31 else default_dword-(1<<32)
    return RtlDefaultIntegerResult(parser,parser.qword if parser.accepted else default&MASK64,not parser.accepted)

def parse_rtl_integer(text):
    if text is None:return RtlIntegerResult(0,1)
    if type(text) is not str:raise ValueError('Immutable Unicode string or explicit null required')
    raw=text.encode('utf-16-le',errors='surrogatepass')
    units=[raw[i]|raw[i+1]<<8 for i in range(0,len(raw),2)]
    length=len(units);units.append(0)
    index=0
    while units[index]==0x20:index+=1
    negative=units[index]==0x2d
    if units[index] in (0x2b,0x2d):index+=1
    # Managed string length participates only in the 0x lookahead gate.
    hex_mode=(units[index]==0x30 and length>index+1 and units[index+1] in (0x58,0x78)) or units[index] in (0x24,0x58,0x78)
    radix=16 if hex_mode else 10
    if hex_mode:
        if units[index]==0x30:index+=1
        index+=1
    result=0;no_digits=True
    threshold=0x0fffffffffffffff if hex_mode else 0x0ccccccccccccccc
    while True:
        unit=units[index]
        digit=unit-0x30 if 0x30<=unit<=0x39 else (unit-0x41+10 if hex_mode and 0x41<=unit<=0x46 else (unit-0x61+10 if hex_mode and 0x61<=unit<=0x66 else None))
        if digit is None:break
        # Both source high-DWORD guards are signed; test before consuming digit.
        if result>=1<<63 or result>threshold:break
        result=(result*radix+digit)&MASK64
        index+=1;no_digits=False
    if negative:result=(-result)&MASK64
    if not hex_mode and result!=0 and bool(result&(1<<63))!=negative:
        index-=1
    code=index+1 if no_digits or units[index]!=0 else 0
    return RtlIntegerResult(result,code,radix,negative)
