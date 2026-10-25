"""004e9854 INI import via the same local Windows A profile APIs.

Absolute path validation, row budget and atomic RouteStep adaptation are own
workbench policy. No game actions. Explicit text codec is not a claim about
the original process's RTL codepage/locale/exception behavior.
"""
import ctypes,sys,ntpath,re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from name_codec import WindowsNameCodec
from routes import RouteStep
from special_routes import SPECIAL_COMMANDS
from supply_routes import SupplyRouteDecision

@dataclass(frozen=True)
class SourceRouteLoad:
    status:str
    rows:tuple=()
    changed:bool=False
    complete:bool=True
    count_dword:Optional[int]=None
    missing:str=''
    independently_verified:bool=False

def read_source_route_ini(path,*,max_rows=10000):
    if sys.platform!='win32':raise OSError('Windows profile APIs required')
    if type(path) is not str or not ntpath.isabs(path) or '\0' in path:
        raise ValueError('Explicit absolute local route file path required')
    if type(max_rows) is not int or max_rows<1:raise ValueError('Positive local row budget required')
    if not Path(path).is_file():return SourceRouteLoad('file_missing_preserve')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetACP.argtypes=[];kernel.GetACP.restype=ctypes.c_uint
    # A API filename follows our host's measured ACP; never guess from UTF8.
    encoded,used=WindowsNameCodec(kernel.GetACP()).encode(path)
    if used:raise ValueError('Route filename cannot be represented by host ACP')
    kernel.GetPrivateProfileIntA.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p]
    kernel.GetPrivateProfileIntA.restype=ctypes.c_uint
    kernel.GetPrivateProfileStringA.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,
        ctypes.c_void_p,ctypes.c_uint,ctypes.c_char_p]
    kernel.GetPrivateProfileStringA.restype=ctypes.c_uint
    count=kernel.GetPrivateProfileIntA(b'Count',b'Value',0,encoded)
    signed=count-(0x100000000 if count&0x80000000 else 0)
    if signed<=0:return SourceRouteLoad('nonpositive_count_preserve',count_dword=count)
    if signed>max_rows:return SourceRouteLoad('local_row_budget',complete=False,count_dword=count,
        missing='source count exceeds explicit local budget')
    rows=[]
    for index in range(signed):
        values=[]
        for prefix in (b'ISLEM',b'Sub1',b'Sub2'):
            buffer=ctypes.create_string_buffer(256)
            kernel.GetPrivateProfileStringA(b'ROUTE',prefix+str(index).encode('ascii'),b'',buffer,255,encoded)
            values.append(buffer.value) # Source PChar constructor stops at first NUL.
        rows.append(tuple(values))
    return SourceRouteLoad('source_rows_loaded',tuple(rows),True,True,count)

@dataclass(frozen=True)
class SourceRouteImport:
    status:str
    load:SourceRouteLoad
    steps:tuple=()
    complete:bool=False
    changed:bool=False
    missing:str=''

def adapt_source_route(load,codec):
    if not isinstance(load,SourceRouteLoad) or not isinstance(codec,WindowsNameCodec):
        raise ValueError('Typed source load and explicit local codec required')
    if not load.complete:return SourceRouteImport(load.status,load,missing=load.missing)
    if not load.changed:return SourceRouteImport(load.status,load,complete=True)
    steps=[]
    for index,raw in enumerate(load.rows):
        if type(raw) is not tuple or len(raw)!=3 or any(type(v) is not bytes for v in raw):
            raise ValueError('Three raw ANSI source row strings required')
        command,p1,p2=(codec.decode(codec.encode(codec.decode(v))[0]) for v in raw)
        try:
            if command=='Koordinat':step=RouteStep(command,x=float(p1),y=float(p2))
            elif command=='Bekle':
                if not re.fullmatch(r'[+-]?[0-9]+',p1.strip()):raise ValueError('Decimal seconds required')
                step=RouteStep(command,seconds=int(p1.strip()))
            elif command in SPECIAL_COMMANDS:step=RouteStep(command,parameter1=p1,parameter2=p2)
            else:raise ValueError('Unsupported source command: '+command)
        except ValueError as exc:
            return SourceRouteImport('unresolved_source_row',load,tuple(steps),missing='row%d: %s'%(index,exc))
        steps.append(step)
    return SourceRouteImport('route_imported',load,tuple(steps),True,True)

def import_source_route(path,codec,*,max_rows=10000):
    return adapt_source_route(read_source_route_ini(path,max_rows=max_rows),codec)

def import_selected_source_route(selection,prefix,codec,*,max_rows=10000):
    if not isinstance(selection,SupplyRouteDecision) or type(prefix) is not bytes or not isinstance(codec,WindowsNameCodec):
        raise ValueError('Typed route selection, explicit ANSI prefix and local codec required')
    if not selection.complete or selection.status!='route_selected':
        load=SourceRouteLoad('selection_not_ready',complete=False,missing=selection.status)
        return SourceRouteImport(load.status,load,missing=load.missing)
    # Successful filename is fresh; do not reuse the first FileExists path.
    return import_source_route(codec.decode(prefix+selection.filename),codec,max_rows=max_rows)
