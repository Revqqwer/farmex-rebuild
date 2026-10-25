"""Owned raw-row .R writer using Windows A profile APIs.

The source004ea01c repeats Count/Value before each row's ISLEM/Sub1/Sub2.
It ignores remove and profile-write results. We retain that call order while
reporting observed BOOLs separately from completion. Full source callback,
managed-string/codepage/error and UI semantics remain outside this adapter.
"""
from dataclasses import dataclass
from pathlib import Path
import ctypes
import ntpath
import sys

from name_codec import WindowsNameCodec


@dataclass(frozen=True)
class SourceRouteWriteCall:
    section:bytes
    key:bytes
    value:bytes
    result:object=None


@dataclass(frozen=True)
class SourceRouteSave:
    status:str
    complete:bool
    calls:tuple=()
    remove_result:object=None
    writes_succeeded:object=None
    error:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


def _validate_rows(rows):
    if type(rows) is not tuple or len(rows)>0x7fffffff:
        raise ValueError('Immutable raw route rows and signed positive count range required')
    for row in rows:
        if type(row) is not tuple or len(row)!=3 or any(type(value) is not bytes for value in row):
            raise ValueError('Three raw ANSI byte strings per route row required')


def write_source_route_calls(filename,rows,remove,write):
    """Lower adapter for explicit raw captured rows and injected API boundary.

    Row capture is own immutable-input policy, not a claim about native fresh
    UI reads. Embedded NUL is retained here; a real A API observes its prefix.
    BOOL0 does not stop later calls. A Python backend exception is incomplete,
    not proof of the source's SEH behavior.
    """
    _validate_rows(rows)
    return write_source_route_dynamic_calls(filename,len(rows),lambda index:rows[index],remove,write)


def write_source_route_dynamic_calls(filename,count,read_row,remove,write):
    """Read each reached raw row after remove; retain the entry count."""
    if type(count) is not int or not 0<=count<=0x7fffffff:raise ValueError('Nonnegative signed route count required')
    if not callable(read_row):raise ValueError('Reached route row reader required')
    if type(filename) is not bytes or not filename or b'\0' in filename:
        raise ValueError('Explicit nonempty NUL-free ANSI filename required')
    if not callable(remove) or not callable(write):raise ValueError('Explicit API boundary required')
    if not count:return SourceRouteSave('empty_rows_preserve',True)
    calls=[];removed=None
    try:
        removed=remove(filename) # CRT remove result is not a source branch.
        count_bytes=str(count).encode('ascii')
        for index in range(count):
            row=read_row(index);_validate_rows((row,))
            command,first,second=row
            suffix=str(index).encode('ascii')
            for section,key,value in ((b'Count',b'Value',count_bytes),
                (b'ROUTE',b'ISLEM'+suffix,command),
                (b'ROUTE',b'Sub1'+suffix,first),(b'ROUTE',b'Sub2'+suffix,second)):
                calls.append(SourceRouteWriteCall(section,key,value))
                result=write(section,key,value,filename)
                if type(result) not in (int,bool):raise ValueError('Observed Windows BOOL required')
                calls[-1]=SourceRouteWriteCall(section,key,value,result)
        return SourceRouteSave('write_calls_completed',True,tuple(calls),removed,
            all(bool(call.result) for call in calls))
    except (OSError,ValueError,IndexError) as error:
        return SourceRouteSave('backend_incomplete',False,tuple(calls),removed,None,str(error))


def write_source_route_ini(path,rows):
    """Write an explicit absolute local path; no native path/name inference.

    Parent existence and host-ACP filename validation are own policy. No
    directory creation, name trimming or source success notification occurs.
    Original bot files/packages are never loaded by this adapter.
    """
    _validate_rows(rows)
    return write_source_route_rows(path,len(rows),lambda index:rows[index])


def write_source_route_rows(path,count,read_row):
    """Actual A API adapter for a cached count and fresh reached row reader."""
    if type(count) is not int or not 0<=count<=0x7fffffff:raise ValueError('Nonnegative signed route count required')
    if not callable(read_row):raise ValueError('Reached route row reader required')
    if type(path) is not str or not ntpath.isabs(path) or '\0' in path:
        raise ValueError('Explicit absolute NUL-free local route path required')
    if not count:return SourceRouteSave('empty_rows_preserve',True)
    if sys.platform!='win32':raise OSError('Windows profile APIs required')
    if not Path(path).parent.is_dir():return SourceRouteSave('parent_missing',True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetACP.argtypes=[];kernel.GetACP.restype=ctypes.c_uint
    encoded,used=WindowsNameCodec(kernel.GetACP()).encode(path)
    if used:raise ValueError('Route filename cannot be represented by host ACP')
    kernel.WritePrivateProfileStringA.argtypes=[ctypes.c_char_p]*4
    kernel.WritePrivateProfileStringA.restype=ctypes.c_int
    crt=ctypes.CDLL('msvcrt',use_errno=True)
    crt.remove.argtypes=[ctypes.c_char_p];crt.remove.restype=ctypes.c_int
    return write_source_route_dynamic_calls(encoded,count,read_row,crt.remove,kernel.WritePrivateProfileStringA)
