"""Owned stable route-directory projection of pinned source filename policy.

The planner has no IO. A separate explicit local directory adapter is below;
neither executes native code. Prefix is never a full catalog.
"""
from dataclasses import dataclass,replace
import os
from pathlib import Path
from source_unicode import utf16_key

PLACEHOLDER='Rota Seciniz !'
ROUTE_COMBO_PATHS={'supply':'frmMain/MainTab/SheetTedarik/grptedarik/cmbTedarikRoutes',
    'return':'frmMain/MainTab/SheetKontrol/GroupBox28/cmbReturnRoutes',
    'Mine':'frmMain/MainTab/SheetMaden/GroupBox51/cmbMiningRoutes',
    'SMerchant':'frmMain/MainTab/sheetSellMerchant/GroupBox27/cmbSellMBotManuelRoute',
    'BMerchant':'frmMain/MainTab/sheetBuyMerchant/GroupBox59/cmbBuyMBotManuelRoute',
    'AntiCR':'frmMain/MainTab/SheetKoruma/grpAntiCRSlot/cmbanticr',
    'Enemy':'frmMain/MainTab/SheetKoruma/grpAntiEnemy/cmbantienemy',
    'Notice':'frmMain/MainTab/SheetKoruma/grpNoticeKontrol/cmbnoticerota',
    'PMKONTROL':'frmMain/MainTab/SheetKoruma/grpPMKontrol/cmbpmkontrol',
    'Relog':'frmMain/MainTab/SheetKontrol/GroupBox32/cmbRelogAfterReturnRouteName'}

@dataclass(frozen=True)
class RouteCatalogEntry:
    ansi_name:bytes
    unicode_name:object=None
    conversion_returned:object=None
    def __post_init__(self):
        if type(self.ansi_name) is not bytes or b'\0' in self.ansi_name:
            raise ValueError('Captured C-string name bytes before NUL required')
        if self.unicode_name is not None:utf16_key(self.unicode_name)
        if self.conversion_returned is not None and type(self.conversion_returned) is not bool:
            raise ValueError('Explicit conversion normal return required')

@dataclass(frozen=True)
class RouteCatalogPlan:
    complete:bool
    ansi_names:tuple
    rows:tuple
    examined:int
    missing:str=''
    policy:str='owned_stable_source_filename_projection'
    native_execution_verified:bool=False
    enumeration_verified:bool=False
    termination:str=''
    local_error:str=''
    failed_operation:str=''

def route_filename_accepted(name):
    """Source signed length>=3, exact two-byte suffix against .R."""
    if type(name) is not bytes or b'\0' in name:raise ValueError('Exact C-string name bytes required')
    if len(name)>=1<<31:raise ValueError('Signed native string length outside own budget')
    return len(name)>=3 and name[-2:]==b'.R'

def plan_route_catalog(entries,*,enumeration_complete=None,terminal_reason=None):
    if type(entries) is not tuple or any(not isinstance(e,RouteCatalogEntry) for e in entries):
        raise ValueError('Ordered immutable directory entries required')
    if enumeration_complete is not None and type(enumeration_complete) is not bool:
        raise ValueError('Explicit enumeration completion required')
    if terminal_reason not in (None,'open_failed','read_stopped'):raise ValueError('Known directory termination required')
    if terminal_reason=='open_failed' and (entries or enumeration_complete is True):
        raise ValueError('Failed directory open cannot yield entries or certify enumeration')
    accepted=[];rows=[];examined=0
    def result(complete,missing=''):
        return RouteCatalogPlan(complete,tuple(accepted),tuple(rows),examined,missing,
            enumeration_verified=enumeration_complete is True,
            termination=terminal_reason or ('verified_enumeration' if enumeration_complete is True else ''))
    # Generation precedes combo Clear/population. An observed prefix is useful
    # evidence but cannot certify a complete directory or a placeholder choice.
    for e in entries:
        examined+=1
        if not route_filename_accepted(e.ansi_name):continue
        accepted.append(e.ansi_name)
        if e.conversion_returned is not True:return result(False,'ANSI to Unicode normal return')
        if e.unicode_name is None:return result(False,'post-conversion Unicode name')
        rows.append(e.unicode_name)
    if enumeration_complete is not True and terminal_reason is None:return result(False,'directory enumeration completion')
    if not accepted:rows.append(PLACEHOLDER)
    return result(True)

def read_local_route_catalog(directory,codec,*,max_entries=10000):
    """User-selected local Unicode directory adapter; not CRT readdir emulation.

    Preserve OS enumeration order and apply the verified byte suffix predicate.
    Reject lossy local encoding rather than selecting a different filename.
    """
    if type(directory) is not str or not Path(directory).is_absolute():raise ValueError('Mutlak rota klasörü gerekli')
    if type(max_entries) is not int or max_entries<1:raise ValueError('Positive local entry budget required')
    entries=[]
    try:iterator=os.scandir(directory)
    except OSError as error:
        # Own adapter analogue of source opendir(NULL): reset then placeholder.
        # This certifies the display projection, not a healthy directory scan.
        return replace(plan_route_catalog((),terminal_reason='open_failed'),
            local_error=str(error),failed_operation='scandir_open')
    scan_error=None
    with iterator:
        while True:
            try:entry=next(iterator)
            except StopIteration:break
            except OSError as error:
                scan_error=error;break
            if len(entries)>=max_entries:raise ValueError('Rota klasörü yerel kayıt sınırını aşıyor')
            name,used=codec.encode(entry.name)
            if used or utf16_key(codec.decode(name))!=utf16_key(entry.name):
                raise ValueError('Rota dosya adı seçilen kod sayfasında kayıpsız temsil edilemiyor')
            entries.append(RouteCatalogEntry(name,codec.decode(name),True))
    return replace(plan_route_catalog(tuple(entries),enumeration_complete=scan_error is None,
        terminal_reason='read_stopped'),local_error='' if scan_error is None else str(scan_error),
        failed_operation='' if scan_error is None else 'scandir_next')
