"""Own hidden Windows ListView sorting with source-shaped value comparisons.

Never accepts an external HWND/PID. No original VCL object or game is touched.
"""
from dataclasses import dataclass,replace
from pathlib import Path
import ctypes,hashlib,sys,threading
from merchant_result_rows import MerchantResultRow,MerchantRowsPlan
from merchant_result_compare import compare_merchant_rows
from merchant_result_filter import raw


@dataclass(frozen=True)
class WindowsSortComparison:
    first: int
    second: int
    complete: bool
    status: str
    result_dword: object = None


@dataclass(frozen=True)
class WindowsSortPlan:
    complete: bool
    status: str
    order: tuple = ()
    rows: tuple = ()
    comparisons: tuple = ()
    native_control_executed: bool = False
    local_order_observed: bool = False
    cleanup_verified: bool = True
    created_windows: int = 0
    destroyed_windows: int = 0
    pointer_bits: int = ctypes.sizeof(ctypes.c_void_p)*8
    comctl_identity: object = None
    source_VCL_callback_executed: bool = False
    live_compatibility_verified: bool = False


class _Init(ctypes.Structure):
    _fields_=[('size',ctypes.c_uint32),('classes',ctypes.c_uint32)]


class _Version(ctypes.Structure):
    _fields_=[('size',ctypes.c_uint32),('major',ctypes.c_uint32),('minor',ctypes.c_uint32),('build',ctypes.c_uint32),('platform',ctypes.c_uint32)]


class _Item(ctypes.Structure):
    _fields_=[('mask',ctypes.c_uint32),('index',ctypes.c_int),('subitem',ctypes.c_int),
        ('state',ctypes.c_uint32),('state_mask',ctypes.c_uint32),('text',ctypes.c_void_p),
        ('text_max',ctypes.c_int),('image',ctypes.c_int),('param',ctypes.c_ssize_t),
        ('indent',ctypes.c_int),('group_id',ctypes.c_int),('column_count',ctypes.c_uint32),
        ('columns',ctypes.c_void_p),('formats',ctypes.c_void_p),('group',ctypes.c_int)]


class _Api:
    def __init__(self):
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.user=ctypes.WinDLL('user32',use_last_error=True)
        self.kernel.GetSystemDirectoryW.argtypes=[ctypes.c_void_p,ctypes.c_uint];self.kernel.GetSystemDirectoryW.restype=ctypes.c_uint
        self.kernel.GetModuleFileNameW.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_uint];self.kernel.GetModuleFileNameW.restype=ctypes.c_uint
        buffer=ctypes.create_unicode_buffer(32768)
        count=self.kernel.GetSystemDirectoryW(buffer,len(buffer))
        if not 0<count<len(buffer):raise ctypes.WinError(ctypes.get_last_error())
        self.comctl=ctypes.WinDLL(str(Path(buffer.value)/'comctl32.dll'),use_last_error=True)
        self.comctl.InitCommonControlsEx.argtypes=[ctypes.POINTER(_Init)];self.comctl.InitCommonControlsEx.restype=ctypes.c_int
        init=_Init(ctypes.sizeof(_Init),1)
        if not self.comctl.InitCommonControlsEx(ctypes.byref(init)):raise ctypes.WinError(ctypes.get_last_error())
        self.user.CreateWindowExW.argtypes=[ctypes.c_uint32,ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint32,
            ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_void_p]
        self.user.CreateWindowExW.restype=ctypes.c_void_p
        self.user.SendMessageW.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_size_t,ctypes.c_ssize_t]
        self.user.SendMessageW.restype=ctypes.c_ssize_t
        self.user.DestroyWindow.argtypes=[ctypes.c_void_p];self.user.DestroyWindow.restype=ctypes.c_int
        self.user.IsWindowVisible.argtypes=[ctypes.c_void_p];self.user.IsWindowVisible.restype=ctypes.c_int
        buffer=ctypes.create_unicode_buffer(32768)
        count=self.kernel.GetModuleFileNameW(self.comctl._handle,buffer,len(buffer))
        if not 0<count<len(buffer):raise ctypes.WinError(ctypes.get_last_error())
        path=Path(buffer.value);version=_Version();version.size=ctypes.sizeof(version)
        self.comctl.DllGetVersion.argtypes=[ctypes.POINTER(_Version)];self.comctl.DllGetVersion.restype=ctypes.c_long
        if self.comctl.DllGetVersion(ctypes.byref(version))!=0:raise OSError('Common-controls version query failed')
        self.identity=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            version=[version.major,version.minor,version.build],LVITEM_size=ctypes.sizeof(_Item))


_api=None
_lock=threading.Lock()


def _get_api():
    global _api
    with _lock:
        if _api is None:_api=_Api()
    return _api


def sort_merchant_rows_windows(rows,column):
    """Observe an own control's order; failures never publish partial order.

    Comparison gaps return neutral zero only to finish our disposable control;
    that resulting order is discarded. This is not source exception recovery.
    No ListView messages are sent from the comparison callback.
    """
    if type(rows) is not tuple or any(not isinstance(r,MerchantResultRow) for r in rows):
        raise ValueError('Immutable own result rows required')
    raw(column,32,'column')
    if len(rows)>0x7fffffff:raise ValueError('Native signed item count exceeded')
    if sys.platform!='win32':return WindowsSortPlan(False,'local_Windows_control_unavailable')
    api=_get_api();parent=None;child=None;created=0;destroyed=0;events=[];failure=[]
    plan=WindowsSortPlan(False,'not_started',comctl_identity=api.identity)
    callback_type=ctypes.WINFUNCTYPE(ctypes.c_int,ctypes.c_ssize_t,ctypes.c_ssize_t,ctypes.c_ssize_t)
    def compare(first,second,parameter):
        a,b=int(first)-1,int(second)-1
        try:
            if parameter!=0 or not 0<=a<len(rows) or not 0<=b<len(rows):raise ValueError('Own item token mismatch')
            result=compare_merchant_rows(rows[a],rows[b],column,use_owned_text_model=True,use_owned_integer_model=True)
            valid=result.complete and result.result_written
            events.append(WindowsSortComparison(a,b,valid,result.status,result.result_dword))
            if not valid:
                failure.append(result.status);return 0
            return result.signed_result
        except Exception as error:
            failure.append('callback_boundary:'+str(error))
            events.append(WindowsSortComparison(a,b,False,failure[-1]));return 0
    callback=callback_type(compare)
    try:
        parent=api.user.CreateWindowExW(0,'STATIC','',0x80000000,0,0,1,1,None,None,None,None)
        if not parent:raise ctypes.WinError(ctypes.get_last_error())
        created+=1
        child=api.user.CreateWindowExW(0,'SysListView32','',0x40000001,0,0,1,1,parent,None,None,None)
        if not child:raise ctypes.WinError(ctypes.get_last_error())
        created+=1
        if api.user.IsWindowVisible(parent) or api.user.IsWindowVisible(child):raise OSError('Own sort windows unexpectedly visible')
        empty=ctypes.create_unicode_buffer('')
        for index in range(len(rows)):
            item=_Item();item.mask=5;item.index=index;item.param=index+1;item.text=ctypes.addressof(empty)
            if api.user.SendMessageW(child,0x104d,0,ctypes.addressof(item))!=index:raise OSError('Own ListView insert failed')
        result=api.user.SendMessageW(child,0x1030,0,ctypes.cast(callback,ctypes.c_void_p).value)
        plan=replace(plan,native_control_executed=True)
        if failure:
            plan=replace(plan,status='comparison_unresolved:'+failure[0])
        elif not result:
            plan=replace(plan,status='native_sort_returned_false')
        else:
            if api.user.SendMessageW(child,0x1004,0,0)!=len(rows):raise OSError('Own sorted item count mismatch')
            order=[]
            for index in range(len(rows)):
                item=_Item();item.mask=4;item.index=index
                if not api.user.SendMessageW(child,0x104b,0,ctypes.addressof(item)):raise OSError('Own sorted token read failed')
                order.append(int(item.param)-1)
            if sorted(order)!=list(range(len(rows))):raise OSError('Own sorted tokens are not a permutation')
            plan=replace(plan,complete=True,status='own_native_order_observed',order=tuple(order),
                rows=tuple(rows[i] for i in order),local_order_observed=True)
    except (OSError,ValueError) as error:
        plan=replace(plan,complete=False,status='own_control_error:'+str(error),order=(),rows=(),local_order_observed=False)
    finally:
        if child and api.user.DestroyWindow(child):destroyed+=1
        if parent and api.user.DestroyWindow(parent):destroyed+=1
    clean=created==destroyed
    plan=replace(plan,comparisons=tuple(events),created_windows=created,destroyed_windows=destroyed,cleanup_verified=clean)
    if not clean:plan=replace(plan,complete=False,status='own_window_cleanup_unverified',order=(),rows=(),local_order_observed=False)
    return plan


def sort_prepared_merchant_rows(prepared,column=None):
    """Consume rebuild sort intent or an explicit later column-click request.

    Incoming reply rows do not implicitly acquire a clear/reset/sort action.
    """
    if not isinstance(prepared,MerchantRowsPlan):raise ValueError('Typed prepared row plan required')
    if not prepared.formatting_complete:
        return WindowsSortPlan(False,'needs_complete_row_preparation')
    if column is None:
        if not prepared.filter_plan.alpha_sort_requested:
            return WindowsSortPlan(True,'sort_not_requested',tuple(range(len(prepared.rows))),prepared.rows)
        column=prepared.filter_plan.final_sort_column
        if column is None:return WindowsSortPlan(False,'needs_source_sort_column')
    return sort_merchant_rows_windows(prepared.rows,column)
