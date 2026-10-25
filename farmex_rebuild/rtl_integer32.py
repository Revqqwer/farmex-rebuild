"""Pinned 5005dd64 ValLong scalar model; native exception/unwind not emulated."""
from dataclasses import dataclass


@dataclass(frozen=True)
class RtlInteger32Result:
    dword: int
    code: int
    radix: int = 10
    negative: bool = False

    @property
    def accepted(self):return self.code==0
    @property
    def signed(self):return self.dword if self.dword<0x80000000 else self.dword-0x100000000


def parse_rtl_integer32(text):
    if text is None:return RtlInteger32Result(0,1)
    if type(text) is not str:raise ValueError('Immutable Unicode or explicit null required')
    data=text.encode('utf-16-le',errors='surrogatepass')
    units=[data[i]|data[i+1]<<8 for i in range(0,len(data),2)]+[0]
    cursor=0;value=0;negative=False;radix=10
    def read():
        nonlocal cursor
        unit=units[cursor];cursor+=1;return unit
    def result(code):return RtlInteger32Result(value,code,radix,negative)
    ch=read()
    while ch==0x20:ch=read()
    if ch in (0x2b,0x2d):negative=ch==0x2d;ch=read()
    hex_mode=ch in (0x24,0x78,0x58)
    if ch==0x30:
        ch=read()
        hex_mode=ch in (0x78,0x58)
        if ch==0:return result(0)
    if hex_mode:
        radix=16;ch=read()
        if ch==0:return result(cursor+1) # Source adds one more UTF16 unit.
        while True:
            folded=ch-0x20 if ch>=0x61 else ch
            digit=folded-0x30
            if not 0<=digit<=9:
                digit-=0x11
                if not 0<=digit<=5:return result(cursor)
                digit+=10
            if value>0x0fffffff:return result(cursor)
            value=((value<<4)+digit)&0xffffffff
            ch=read()
            if ch==0:break
        if negative:value=(-value)&0xffffffff
        return result(0)
    if ch==0:return result(cursor)
    while True:
        digit=ch-0x30
        if not 0<=digit<=9 or value>0x0ccccccc:return result(cursor)
        value=(value*10+digit)&0xffffffff
        ch=read()
        if ch==0:break
    if negative:
        value=(-value)&0xffffffff
        return result(0 if value==0 or value>=0x80000000 else cursor)
    return result(0 if value<0x80000000 else cursor)
