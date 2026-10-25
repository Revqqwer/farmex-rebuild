"""Own source-panel save orchestration; source RTL/notice effects unverified."""
from dataclasses import dataclass
from pathlib import Path
import ntpath
from name_codec import WindowsNameCodec
from source_route_save import write_source_route_rows

NAME_PATH='frmMain/RotaPanel/GroupBox21/txtrotaname'
BUTTON_PATH='frmMain/RotaPanel/GroupBox21/Button27'
LIST_PATH='frmMain/RotaPanel/lstRota'


@dataclass(frozen=True)
class RouteSaveContext:
    directory:str
    codec:WindowsNameCodec


@dataclass(frozen=True)
class RouteSaveResult:
    status:str
    path:object=None
    write:object=None
    notice_name:object=None
    error:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


def save_source_route_panel(read_name,read_count,read_context,read_row,writer=write_source_route_rows):
    """Three fresh name reads; cached count; reached row provider to writer.

    Selected own directory/codec and basename confinement are explicit local
    policies. The writer reads each row only when reached, after file removal.
    Count0 exits before directory lookup. No trim or extension deduplication.
    """
    path=None;write=None
    try:
        def name():
            value=read_name()
            if type(value) is not str:raise ValueError('Current route name text required')
            return value
        if name()=='':return RouteSaveResult('name_required')
        count=read_count()
        if type(count) is not int or not 0<=count<=0x7fffffff:raise ValueError('Current route list count required')
        if count==0:return RouteSaveResult('empty_rows_preserve')
        context=read_context()
        if not isinstance(context,RouteSaveContext) or not isinstance(context.codec,WindowsNameCodec):
            raise ValueError('Selected route directory and explicit Windows codec required')
        directory=context.directory
        if type(directory) is not str or not directory or '\0' in directory or not ntpath.isabs(directory):
            return RouteSaveResult('directory_required')
        if not Path(directory).is_dir():return RouteSaveResult('directory_missing')
        filename=name()+'.R'
        if ntpath.basename(filename)!=filename or any(c in filename for c in '<>:"/\\|?*\0'):
            raise ValueError('Route name must stay inside selected directory')
        path=str(Path(directory)/filename)
        def row(index):
            values=read_row(index)
            if type(values) is not tuple or len(values)!=3 or any(type(v) is not str for v in values):
                raise ValueError('Current caption and two route subitems required')
            return tuple(context.codec.encode(value)[0] for value in values)
        write=writer(path,count,row)
        if not write.complete:return RouteSaveResult('write_incomplete',path,write,error=write.error)
        if write.status!='write_calls_completed':return RouteSaveResult(write.status,path,write)
        # This is the own status/notice text capture, not a native message box.
        notice=name()
        return RouteSaveResult('write_calls_completed',path,write,notice)
    except (OSError,ValueError,IndexError) as error:
        return RouteSaveResult('save_incomplete',path,write,error=str(error))
