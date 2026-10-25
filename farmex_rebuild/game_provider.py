"""Read-only game candidate provider. Does not send actions or change protection.

Profile constants come from Richard initialization tables, not a generic scan.
Passing bounds is structural evidence only, not independent game verification.
"""
from dataclasses import dataclass, field
import ctypes
import hashlib
import os
import time
from pathlib import Path
from ctypes import wintypes
from process_access import query_granted_access


GAME_PATH = r'C:\NTTGame\KnightOnlineEn\KnightOnLine.exe'
# Same previously recorded disk identity as native/vitals_bridge.c. This is a
# build gate, not proof that either candidate offset profile matches live data.
KNOWN_GAME_IMAGE_SIZE = 7009936
KNOWN_GAME_IMAGE_SHA256 = 'adeccdc66814422e47ffc66b9a5659a2f9487aad6d4a5289a78261d94a3e700a'
SOURCE_PROFILES = {
    'us': {'root_slot': 0x1115574, 'hp': 0x6d8, 'hp_max': 0x6d4, 'mp': 0xbf0, 'mp_max': 0xbec},
    'steam': {'root_slot': 0x11ea638, 'hp': 0x6d8, 'hp_max': 0x6d4, 'mp': 0xd60, 'mp_max': 0xd5c},
}
REFRESHED_GAME_IMAGE_SIZE = 7008392
REFRESHED_GAME_IMAGE_SHA256 = 'ca69cecebdefd82b409ca8cf041655da53cb97113b068a086c5f7a6ef7e952a9'
# Refreshed module febdac80...45759 initializers004fd640/004e4398.
# Source initializer operands are verified; live field meanings remain candidates.
REFRESHED_SOURCE_PROFILES = {
    'us': {'root_slot': 0x11289c0, 'hp': 0x6d8, 'hp_max': 0x6d4, 'mp': 0xd60, 'mp_max': 0xd5c},
    'steam': {'root_slot': 0x11e9638, 'hp': 0x6d8, 'hp_max': 0x6d4, 'mp': 0xd60, 'mp_max': 0xd5c},
}
GAME_IMAGE_PROFILES = {
    (KNOWN_GAME_IMAGE_SIZE, KNOWN_GAME_IMAGE_SHA256): SOURCE_PROFILES,
    (REFRESHED_GAME_IMAGE_SIZE, REFRESHED_GAME_IMAGE_SHA256): REFRESHED_SOURCE_PROFILES,
}


@dataclass(frozen=True)
class Observation:
    status: str
    pid: int = 0
    timestamp_ms: int = 0
    image_sha256: str = ''
    fields: dict = field(default_factory=dict)
    error: str = ''
    independently_verified: bool = False
    bytes_read: int = 0
    failed_operation: str = ''
    error_code: int = 0
    granted_access: object = None
    disk_identity_verified: bool = False


def validate_vitals(fields):
    if set(fields) != {'hp', 'hp_max', 'mp', 'mp_max'}:
        raise ValueError('HP/MP alanları eksik')
    if any(type(value) is not int for value in fields.values()):
        raise ValueError('HP/MP tam sayı olmalı')
    for current, maximum in [('hp', 'hp_max'), ('mp', 'mp_max')]:
        if not 0 < fields[maximum] < 10000000 or not 0 <= fields[current] <= fields[maximum]:
            raise ValueError('HP/MP sınırları geçersiz')
    return dict(fields)


class ReadOnlyGameProvider:
    def __init__(self, path=GAME_PATH, profile='us'):
        if profile not in SOURCE_PROFILES:
            raise ValueError('Bilinmeyen oyun sürümü')
        self.path = os.path.normcase(os.path.abspath(path))
        self.profile = profile

    def observe(self, pid):
        if type(pid) is not int or pid <= 0:
            raise ValueError('Geçerli süreç kimliği gerekli')
        now = int(time.monotonic() * 1000)
        if os.name != 'nt':
            return Observation('unavailable', pid, now, error='Windows gerekli')
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                     wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        kernel.ReadProcessMemory.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                                             ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        handle = kernel.OpenProcess(0x1000, False, pid)
        read_handle = None
        digest, bytes_read = '', 0
        granted_access = None
        disk_identity_verified = False
        operation = 'OpenProcess(QUERY_LIMITED_INFORMATION)'
        try:
            if not handle:
                raise ctypes.WinError(ctypes.get_last_error())
            name = ctypes.create_unicode_buffer(32768)
            length = wintypes.DWORD(len(name))
            operation = 'QueryFullProcessImageNameW'
            if not kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(length)):
                raise ctypes.WinError(ctypes.get_last_error())
            operation = 'validate_process_path'
            if os.path.normcase(os.path.abspath(name.value)) != self.path:
                raise ValueError('Seçilen süreç oyun dosyasıyla eşleşmiyor')
            operation = 'validate_disk_image'
            data = Path(self.path).read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            pe = int.from_bytes(data[0x3c:0x40], 'little')
            if data[:2] != b'MZ' or data[pe:pe+4] != b'PE\0\0' or int.from_bytes(data[pe+4:pe+6], 'little') != 0x14c:
                raise ValueError('Oyun dosyası x86 PE değil')
            if int.from_bytes(data[pe+52:pe+56], 'little') != 0x400000:
                raise ValueError('Görüntü tabanı kaynak tablosuyla eşleşmiyor')
            # Refuse dynamic-base binaries rather than inventing a relocation delta.
            if int.from_bytes(data[pe+94:pe+96], 'little') & 0x40:
                raise ValueError('Dinamik görüntü tabanı bağımsız doğrulama gerektiriyor')
            operation = 'validate_disk_identity'
            profiles = GAME_IMAGE_PROFILES.get((len(data), digest))
            if profiles is None:
                raise ValueError('Oyun dosyası kayıtlı sürümle eşleşmiyor; adres profili yeniden doğrulanmalı')
            disk_identity_verified = True
            operation = 'OpenProcess(PROCESS_VM_READ)'
            read_handle = kernel.OpenProcess(0x10, False, pid)
            if not read_handle:
                raise ctypes.WinError(ctypes.get_last_error())
            operation = 'validate_vm_read_handle_access'
            granted_access = query_granted_access(read_handle)
            if granted_access is not None and not granted_access & 0x10:
                raise ValueError('İşlem handle\'ında PROCESS_VM_READ hakkı yok; bellek okunmadı')
            def dword(address, field_name):
                nonlocal bytes_read, operation
                operation = 'ReadProcessMemory(' + field_name + ')'
                value, count = wintypes.DWORD(), ctypes.c_size_t()
                success = kernel.ReadProcessMemory(read_handle, ctypes.c_void_p(address), ctypes.byref(value), 4, ctypes.byref(count))
                # Include reported partial transfers without accepting their value.
                bytes_read += min(count.value, 4)
                if not success:
                    raise ctypes.WinError(ctypes.get_last_error())
                if count.value != 4:
                    raise ValueError('Eksik veri okuması')
                return value.value
            table = profiles[self.profile]
            root = dword(table['root_slot'], 'character_root')
            operation = 'validate_character_root'
            if not 0x10000 <= root <= 0xffff0000 or root % 4:
                raise ValueError('Karakter kökü geçersiz')
            fields = {key: dword(root + table[key], key) for key in ['hp', 'hp_max', 'mp', 'mp_max']}
            repeated_root = dword(table['root_slot'], 'character_root_recheck')
            operation = 'validate_snapshot_consistency'
            if root != repeated_root:
                raise ValueError('Okuma sırasında karakter kökü değişti')
            operation = 'validate_vitals'
            fields = validate_vitals(fields)
            return Observation('candidate', pid, now, digest, fields, bytes_read=bytes_read,
                               granted_access=granted_access,disk_identity_verified=disk_identity_verified)
        except (OSError, ValueError) as error:
            return Observation('unavailable', pid, now, digest, error=str(error), bytes_read=bytes_read,
                               failed_operation=operation, error_code=getattr(error, 'winerror', 0) or 0,
                               granted_access=granted_access,disk_identity_verified=disk_identity_verified)
        finally:
            if read_handle:
                kernel.CloseHandle(read_handle)
            if handle:
                kernel.CloseHandle(handle)

    def submit(self, intent):
        # No known writable provider/transport ABI is bound to this reader.
        return {'status': 'unavailable', 'reason': 'Canlı eylem sağlayıcısı doğrulanmadı'}


@dataclass(frozen=True)
class ProcessDiscovery:
    status: str
    pids: tuple = ()
    scanned_count: int = 0
    enumeration_complete: bool = False
    failed_operation: str = ''
    error_code: int = 0
    error: str = ''


class ProcessDiscoveryError(OSError):
    def __init__(self, result):
        super().__init__(result.error_code, result.error)
        self.winerror = result.error_code
        self.failed_operation = result.failed_operation
        self.discovery = result


def discover_game_processes():
    """Read-only names/PIDs; partial or failed enumeration is never absence."""
    if os.name != 'nt':
        return ProcessDiscovery('unsupported', error='Windows gerekli')
    class ProcessEntry(ctypes.Structure):
        _fields_ = [('dwSize', wintypes.DWORD), ('cntUsage', wintypes.DWORD),
                    ('th32ProcessID', wintypes.DWORD), ('th32DefaultHeapID', ctypes.c_size_t),
                    ('th32ModuleID', wintypes.DWORD), ('cntThreads', wintypes.DWORD),
                    ('th32ParentProcessID', wintypes.DWORD), ('pcPriClassBase', wintypes.LONG),
                    ('dwFlags', wintypes.DWORD), ('szExeFile', wintypes.WCHAR * 260)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.Process32FirstW.restype = wintypes.BOOL
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
    kernel.Process32NextW.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateToolhelp32Snapshot(2, 0)
    if not handle or handle == ctypes.c_void_p(-1).value:
        code=ctypes.get_last_error()
        return ProcessDiscovery('unavailable',failed_operation='CreateToolhelp32Snapshot',error_code=code,
                                error=str(ctypes.WinError(code)) if code else 'Süreç snapshotı açılamadı; Windows hata kodu sağlanmadı')
    matches = []
    scanned = 0
    operation = 'Process32FirstW'
    try:
        entry = ProcessEntry()
        entry.dwSize = ctypes.sizeof(entry)
        function = kernel.Process32FirstW
        while True:
            ctypes.set_last_error(0)
            if not function(handle,ctypes.byref(entry)):
                code=ctypes.get_last_error() # capture before CloseHandle may overwrite it
                if code==18: # ERROR_NO_MORE_FILES is the documented normal terminator.
                    return ProcessDiscovery('complete',tuple(matches),scanned,True)
                message=str(ctypes.WinError(code)) if code else 'Süreç listeleme başarısız; Windows hata kodu sağlanmadı'
                return ProcessDiscovery('unavailable',tuple(matches),scanned,False,operation,code,message)
            scanned+=1
            if entry.szExeFile.casefold() == 'knightonline.exe':
                matches.append(int(entry.th32ProcessID))
            operation='Process32NextW';function=kernel.Process32NextW
    finally:
        kernel.CloseHandle(handle)


def find_game_processes():
    """Legacy list interface; a failed/partial snapshot raises with its stage."""
    result=discover_game_processes()
    if result.status=='unsupported':return []
    if not result.enumeration_complete:raise ProcessDiscoveryError(result)
    return list(result.pids)
