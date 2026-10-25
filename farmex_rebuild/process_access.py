"""Optional metadata for an already-open handle; no memory or privilege action."""
import ctypes
import os
from ctypes import wintypes as w

class _ObjectBasic(ctypes.Structure):
    _fields_=[('attributes',w.DWORD),('granted_access',w.DWORD),
              ('handle_count',w.DWORD),('pointer_count',w.DWORD),('reserved',w.DWORD*10)]

def query_granted_access(handle):
    """Return observed access bits, or None when metadata is unavailable.

    NtQueryObject is optional and may change on future Windows versions.
    The caller owns the handle. This function neither opens nor closes it.
    """
    if os.name!='nt':return None
    try:
        query=ctypes.WinDLL('ntdll',use_last_error=True).NtQueryObject
        query.argtypes=[w.HANDLE,ctypes.c_int,ctypes.c_void_p,w.DWORD,ctypes.POINTER(w.DWORD)]
        query.restype=w.LONG
        value=_ObjectBasic();length=w.DWORD()
        status=query(handle,0,ctypes.byref(value),ctypes.sizeof(value),ctypes.byref(length))
        if status!=0 or length.value!=ctypes.sizeof(value):return None
        return int(value.granted_access)
    except (AttributeError,OSError):return None
