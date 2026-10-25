"""Own streaming source route load: preserve absent/nonpositive, clear then add.

Own API and sink boundaries expose completed prefixes; native RTL/VCL/SEH,
directory context and codepage identity are not certified.
"""
from dataclasses import dataclass
from pathlib import Path
import ctypes,ntpath,sys
from name_codec import WindowsNameCodec
from route_save_runtime import RouteSaveContext

EDITOR_PATH='frmMain/RotaPanel/cmbRouteEdit'
LIST_PATH='frmMain/RotaPanel/lstRota'


@dataclass(frozen=True)
class RouteLoadResult:
    status:str
    complete:bool
    path:object=None
    count_dword:object=None
    cleared:bool=False
    completed_rows:int=0
    phase:str='entry'
    error:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class WindowsRouteReader:
    """Explicit local path, host-ACP filename and real Windows A profile API."""
    def __init__(self,path):
        if sys.platform!='win32':raise OSError('Windows profile APIs required')
        self.path=path
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.kernel.GetACP.argtypes=[];self.kernel.GetACP.restype=ctypes.c_uint
        self.filename,used=WindowsNameCodec(self.kernel.GetACP()).encode(path)
        if used:raise ValueError('Route filename cannot be represented by host ACP')
        self.kernel.GetPrivateProfileIntA.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p]
        self.kernel.GetPrivateProfileIntA.restype=ctypes.c_uint
        self.kernel.GetPrivateProfileStringA.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_uint,ctypes.c_char_p]
        self.kernel.GetPrivateProfileStringA.restype=ctypes.c_uint
    def exists(self):return Path(self.path).is_file()
    def count(self):return self.kernel.GetPrivateProfileIntA(b'Count',b'Value',0,self.filename)
    def value(self,index,prefix):
        buffer=ctypes.create_string_buffer(256)
        self.kernel.GetPrivateProfileStringA(b'ROUTE',prefix+str(index).encode('ascii'),b'',buffer,255,self.filename)
        return buffer.value


def stream_source_route(reader,codec,sink,*,path=None,max_rows=10000):
    """Clear only after positive signed count; add before caption conversion.

    sink has clear(), add_row(), set_caption(token,text), add_subitem(token,text).
    A row's three raw fields are fetched before its add. Conversion/setter errors
    retain blank/partial rows already reached. Row budget is own bounded policy.
    """
    if type(max_rows) is not int or max_rows<1:raise ValueError('Positive own route row budget required')
    count=None;cleared=False;completed=0;phase='exists'
    def result(status,complete,error=None):return RouteLoadResult(status,complete,path,count,cleared,completed,phase,error)
    try:
        if reader.exists() is not True:return result('file_missing_preserve',True)
        phase='count';count=reader.count()
        if type(count) is not int or not 0<=count<=0xffffffff:raise ValueError('Observed count DWORD required')
        signed=count-(0x100000000 if count&0x80000000 else 0)
        if signed<=0:return result('nonpositive_count_preserve',True)
        if signed>max_rows:return result('local_row_budget',False,'source count exceeds own row budget')
        phase='clear';sink.clear();cleared=True
        for index in range(signed):
            raw=[]
            for prefix in (b'ISLEM',b'Sub1',b'Sub2'):
                phase='read_%s_%d'%(prefix.decode('ascii'),index)
                value=reader.value(index,prefix)
                if type(value) is not bytes:raise ValueError('Raw source row ANSI bytes required')
                raw.append(value)
            phase='add_%d'%index;token=sink.add_row()
            phase='caption_%d'%index;sink.set_caption(token,codec.decode(raw[0]))
            phase='sub1_%d'%index;sink.add_subitem(token,codec.decode(raw[1]))
            phase='sub2_%d'%index;sink.add_subitem(token,codec.decode(raw[2]))
            completed+=1
        phase='returned';return result('rows_loaded',True)
    except (OSError,ValueError,IndexError) as error:return result('load_incomplete',False,str(error))


def load_source_route_choice(selected,context,sink,*,reader_factory=WindowsRouteReader,max_rows=10000):
    path=None
    try:
        if type(selected) is not str:raise ValueError('Current route combo text required')
        if not isinstance(context,RouteSaveContext) or not isinstance(context.codec,WindowsNameCodec):
            raise ValueError('Selected own directory and explicit Windows codec required')
        directory=context.directory
        if type(directory) is not str or not directory or '\0' in directory or not ntpath.isabs(directory):
            return RouteLoadResult('directory_required',False)
        if selected in ('.','..') or ntpath.basename(selected)!=selected or any(c in selected for c in '<>:"/\\|?*\0'):
            raise ValueError('Route selection must stay inside selected directory')
        path=str(Path(directory)/selected)
        return stream_source_route(reader_factory(path),context.codec,sink,path=path,max_rows=max_rows)
    except (OSError,ValueError,IndexError) as error:return RouteLoadResult('load_incomplete',False,path,error=str(error))
