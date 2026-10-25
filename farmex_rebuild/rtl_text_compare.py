"""Pinned RTL CompareText values and explicit local Windows collation policy."""
from dataclasses import dataclass
import ctypes,sys

RTL_SHA256='7d98acb8fade7f0920c0f544eaf5525afaf8c8c1afb82e77544cf29ac75eddd8'


def utf16_data(text):
    if text is None:return b''
    if type(text) is not str:raise ValueError('Immutable Unicode or explicit null required')
    data=text.encode('utf-16-le',errors='surrogatepass')
    if len(data)//2>0x7fffffff:raise ValueError('Supported managed length exceeded')
    return data


def compare_text_pinned(first,second):
    """5009280c: ASCII folding and paired UTF16 reads, including odd tail.

    Well-formed immutable UnicodeStrings with a zero UTF16 terminator only;
    no native heap/alias or mutable length metadata is reconstructed.
    """
    a=utf16_data(first);b=utf16_data(second)
    la,lb=len(a)//2,len(b)//2
    count=min(la,lb)
    if count==0:return la-lb
    aa=a+b'\0\0';bb=b+b'\0\0'
    def fold(unit):return unit-32 if 97<=unit<=122 else unit
    # Source reads a DWORD per iteration. With an odd minimum length it also
    # compares the shorter string's terminator against the longer next unit.
    for index in range(0,count+(count&1)):
        x=aa[index*2]|aa[index*2+1]<<8
        y=bb[index*2]|bb[index*2+1]<<8
        difference=fold(x)-fold(y)
        if difference:return difference
    return la-lb


@dataclass(frozen=True)
class LocalAnsiCompare:
    signed_result: int
    win32_result: int
    last_error: int
    acp: int
    thread_lcid: int
    user_lcid: int
    locale: int = 0x400
    flags: int = 1
    native_game_abi_verified: bool = False


def ansi_compare_text_local(first,second):
    """50092a18 policy: CompareStringW(0x400,1,...,explicit lengths)-2.

    Calls standard Windows NLS only in our process. It does not load bot RTL,
    select a locale or certify that the game uses the same runtime/NLS state.
    """
    a=utf16_data(first);b=utf16_data(second)
    if sys.platform!='win32':raise OSError('Local Windows collation unavailable')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CompareStringW.argtypes=[ctypes.c_uint,ctypes.c_uint,ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_int]
    kernel.CompareStringW.restype=ctypes.c_int
    for name in ('GetACP','GetThreadLocale','GetUserDefaultLCID'):
        fn=getattr(kernel,name);fn.argtypes=[];fn.restype=ctypes.c_uint
    left=ctypes.create_string_buffer(a+b'\0\0');right=ctypes.create_string_buffer(b+b'\0\0')
    ctypes.set_last_error(0)
    value=kernel.CompareStringW(0x400,1,left,len(a)//2,right,len(b)//2)
    error=ctypes.get_last_error() if value==0 else 0
    # Preserve source subtraction even if the API returned error zero.
    return LocalAnsiCompare(value-2,value,error,kernel.GetACP(),kernel.GetThreadLocale(),kernel.GetUserDefaultLCID())
