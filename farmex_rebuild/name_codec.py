"""Explicit local Windows codepage conversions, never a game-context claim.

Source-shaped decode/encode/decode chain; API flags0 are our explicit local
conversion policy, not a verified emulation of every rtl260.bpl error/fallback.
No implicit CP_ACP: caller must supply a concrete codepage for the fixture.
"""
import ctypes,sys
from dataclasses import dataclass
from typing import Optional

class WindowsNameCodec:
    def __init__(self,code_page):
        if type(code_page) is not int or not 1<=code_page<=65535:raise ValueError('Explicit nonzero Windows codepage required')
        if sys.platform!='win32':raise OSError('Windows name codec unavailable on this host')
        self.code_page=code_page
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.kernel.IsValidCodePage.argtypes=[ctypes.c_uint];self.kernel.IsValidCodePage.restype=ctypes.c_int
        if not self.kernel.IsValidCodePage(code_page):raise ValueError('Windows does not support this codepage')
        self.kernel.MultiByteToWideChar.argtypes=[ctypes.c_uint,ctypes.c_uint,ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_int]
        self.kernel.MultiByteToWideChar.restype=ctypes.c_int
        self.kernel.WideCharToMultiByte.argtypes=[ctypes.c_uint,ctypes.c_uint,ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p]
        self.kernel.WideCharToMultiByte.restype=ctypes.c_int
    def decode(self,data):
        if type(data) is not bytes:raise ValueError('Immutable ANSI byte string required')
        if not data:return ''
        src=ctypes.create_string_buffer(data)
        count=self.kernel.MultiByteToWideChar(self.code_page,0,src,len(data),None,0)
        if not count:raise ctypes.WinError(ctypes.get_last_error())
        dest=ctypes.create_string_buffer(count*2)
        written=self.kernel.MultiByteToWideChar(self.code_page,0,src,len(data),dest,count)
        if written!=count:raise ctypes.WinError(ctypes.get_last_error())
        return dest.raw.decode('utf-16-le','surrogatepass')
    def encode(self,text):
        if type(text) is not str:raise ValueError('Unicode text required')
        if not text:return b'',False
        raw=text.encode('utf-16-le','surrogatepass');src=ctypes.create_string_buffer(raw+b'\0\0')
        # UTF8/UTF7 APIs forbid default-char/used-default arguments.
        used=ctypes.c_int(0);used_ptr=None if self.code_page in (65000,65001) else ctypes.byref(used)
        count=self.kernel.WideCharToMultiByte(self.code_page,0,src,len(raw)//2,None,0,None,used_ptr)
        if not count:raise ctypes.WinError(ctypes.get_last_error())
        dest=ctypes.create_string_buffer(count);used.value=0
        written=self.kernel.WideCharToMultiByte(self.code_page,0,src,len(raw)//2,dest,count,None,used_ptr)
        if written!=count:raise ctypes.WinError(ctypes.get_last_error())
        return dest.raw,None if used_ptr is None else bool(used.value)

@dataclass(frozen=True)
class NameConversion:
    code_page:int
    first_unicode:str
    cache_ansi:bytes
    compare_unicode:str
    preconversion_nonempty:bool
    used_default:Optional[bool]
    independently_verified:bool=False
    source_context:str='explicit local Windows fixture; game codepage/RTL behavior unverified'

def convert_name_chain(ansi_bytes,code_page):
    codec=WindowsNameCodec(code_page)
    first=codec.decode(ansi_bytes)
    cache,used=codec.encode(first)
    final=codec.decode(cache)
    return NameConversion(code_page,first,cache,final,bool(cache),used)
