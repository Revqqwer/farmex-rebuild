"""Explicit own Windows policy matching pinned standard-RTL normal text paths.

Query: CharUpperBuffW over explicit UTF16 length, then codepage conversion.
Record name: CharUpperBuffA over explicit ANSI byte length. These operations
are intentionally distinct. No display-text re-encoding invents source bytes.
"""
import ctypes
import sys
from dataclasses import dataclass
from typing import Optional
from name_codec import WindowsNameCodec


@dataclass(frozen=True)
class MerchantTextNormalization:
    complete: bool
    status: str
    operation: str
    output_bytes: bytes
    upper_unicode: Optional[str]
    processed_units: int
    code_page: int
    host_acp: int
    thread_lcid: int
    user_lcid: int
    used_default: Optional[bool]=None
    source_runtime_verified: bool=False
    live_compatibility_verified: bool=False


class WindowsMerchantText:
    def __init__(self, query_code_page):
        self.codec=WindowsNameCodec(query_code_page)
        self.kernel=self.codec.kernel
        for name in ('GetACP','GetThreadLocale','GetUserDefaultLCID'):
            f=getattr(self.kernel,name);f.argtypes=[];f.restype=ctypes.c_uint
        self.user=ctypes.WinDLL('user32',use_last_error=True)
        for name in ('CharUpperBuffW','CharUpperBuffA'):
            f=getattr(self.user,name);f.argtypes=[ctypes.c_void_p,ctypes.c_uint];f.restype=ctypes.c_uint

    def _result(self, operation, output, upper, processed, expected, code_page, used=None):
        return MerchantTextNormalization(processed==expected,
            'own_local_normalized' if processed==expected else 'local_upper_count_unexpected',
            operation,output,upper,processed,code_page,int(self.kernel.GetACP()),
            int(self.kernel.GetThreadLocale()),int(self.kernel.GetUserDefaultLCID()),used)

    def query(self, text):
        if type(text) is not str:raise ValueError('Explicit own Unicode query required')
        raw=text.encode('utf-16-le','surrogatepass');count=len(raw)//2
        if count>0x7fffffff:raise ValueError('Signed Unicode length exceeded')
        buffer=ctypes.create_string_buffer(raw+b'\0\0')
        processed=int(self.user.CharUpperBuffW(buffer,count)) if count else 0
        upper=buffer.raw[:len(raw)].decode('utf-16-le','surrogatepass')
        output,used=self.codec.encode(upper)
        return self._result('unicode_query',output,upper,processed,count,self.codec.code_page,used)

    def ansi_name(self, data):
        if type(data) is not bytes:raise ValueError('Original immutable ANSI bytes required')
        if len(data)>0x7fffffff:raise ValueError('Signed ANSI length exceeded')
        buffer=ctypes.create_string_buffer(data+b'\0')
        processed=int(self.user.CharUpperBuffA(buffer,len(data))) if data else 0
        return self._result('ansi_name',buffer.raw[:len(data)],None,processed,len(data),int(self.kernel.GetACP()))
