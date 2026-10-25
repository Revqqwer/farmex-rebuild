"""One-way read-only native HP/MP frames. No VM_READ, loader or actions.

PID fields/name consistency is not authentication of a mapping creator.
Even accepted game-origin frames remain independently unverified candidates.
"""
import ctypes,re,struct,time
from ctypes import wintypes
from dataclasses import dataclass,field
from types import MappingProxyType
from typing import Mapping
from game_provider import Observation, validate_vitals

FRAME=struct.Struct('<21I')
MAGIC=0x31565846

def mapping_name(pid,nonce):
    if type(pid) is not int or not 0<pid<=0xffffffff:raise ValueError('Expected positive DWORD PID')
    if type(nonce) is not str or re.fullmatch('[0-9a-f]{32}',nonce) is None:raise ValueError('32 lowercase hex nonce required')
    return 'Local\\FarmexVitals.%d.%s'%(pid,nonce)

@dataclass(frozen=True)
class NativeIpcResult:
    status: str
    fields: Mapping[str,int] = field(default_factory=dict)
    pid: int = 0
    sequence: int = 0
    source_kind: int = 0
    profile: int = 0
    native_status: int = 0
    win_error: int = 0
    failed_step: int = 0
    native_bytes_read: int = 0
    error: str = ''
    independently_verified: bool = False

    def __post_init__(self):object.__setattr__(self,'fields',MappingProxyType(dict(self.fields)))

def decode_frame(data,sequence_before,sequence_after,*,expected_pid,expected_profile,expected_source,now_tick,max_age_ms=1000):
    mapping_name(expected_pid,'0'*32)
    if expected_profile not in (1,2) or type(expected_profile) is not int or expected_source not in (1,2) or type(expected_source) is not int:
        raise ValueError('Explicit native profile and origin required')
    for value in (sequence_before,sequence_after,now_tick,max_age_ms):
        if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw DWORD required')
    if type(data) is not bytes or len(data)!=84:return NativeIpcResult('invalid_frame',error='Frame must be84bytes')
    words=FRAME.unpack(data)
    magic,abi,size,seq,pid,origin,payload_size,reserved=words[:8]
    if seq==0 or seq&1 or seq!=sequence_before or seq!=sequence_after:return NativeIpcResult('updating',error='Unstable native sequence')
    if (magic,abi,size,payload_size,reserved)!=(MAGIC,1,84,52,0):return NativeIpcResult('invalid_frame',error='Native header mismatch')
    pabi,psize,native_status,win_error,byte_count,ppid,tick,profile,failed,hp,hp_max,mp,mp_max=words[8:]
    if pid!=expected_pid or ppid!=expected_pid:return NativeIpcResult('identity_mismatch',error='Declared PID mismatch')
    if origin!=expected_source:return NativeIpcResult('origin_mismatch',error='Fixture/game source kind differs')
    if profile!=expected_profile:return NativeIpcResult('profile_mismatch',error='Native profile differs')
    if pabi!=1 or psize!=52 or native_status>9 or byte_count>24:return NativeIpcResult('invalid_frame',error='Payload ABI/status/count mismatch')
    if (now_tick-tick)&0xffffffff>max_age_ms:return NativeIpcResult('stale',pid=pid,sequence=seq,error='Native sample expired')
    args=dict(pid=pid,sequence=seq,source_kind=origin,profile=profile,native_status=native_status,
              win_error=win_error,failed_step=failed,native_bytes_read=byte_count)
    if native_status:
        if any((hp,hp_max,mp,mp_max)):return NativeIpcResult('invalid_frame',error='Error payload exposed vitals')
        return NativeIpcResult('native_error',**args)
    if byte_count!=24 or win_error or failed:return NativeIpcResult('invalid_frame',error='Candidate read metadata mismatch')
    try:fields=validate_vitals({'hp':hp,'hp_max':hp_max,'mp':mp,'mp_max':mp_max})
    except ValueError as error:return NativeIpcResult('invalid_frame',error=str(error))
    return NativeIpcResult('fixture_candidate' if origin==1 else 'candidate_unverified',fields,**args)

class ReadOnlyNativeMap:
    def __init__(self,pid,nonce,*,profile,source_kind):
        self.pid=pid;self.name=mapping_name(pid,nonce);self.profile=profile;self.source_kind=source_kind
        self.handle=None;self.view=None
        self.kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        self.kernel.OpenFileMappingW.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.LPCWSTR]
        self.kernel.OpenFileMappingW.restype=wintypes.HANDLE
        self.kernel.MapViewOfFile.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.DWORD,wintypes.DWORD,ctypes.c_size_t]
        self.kernel.MapViewOfFile.restype=ctypes.c_void_p
        self.kernel.UnmapViewOfFile.argtypes=[ctypes.c_void_p]
        self.kernel.CloseHandle.argtypes=[wintypes.HANDLE]
        self.kernel.GetTickCount.restype=wintypes.DWORD

    def open(self):
        if self.handle:raise ValueError('Reader already open')
        self.handle=self.kernel.OpenFileMappingW(4,False,self.name) # FILE_MAP_READ only
        if not self.handle:raise ctypes.WinError(ctypes.get_last_error())
        self.view=self.kernel.MapViewOfFile(self.handle,4,0,0,84)
        if not self.view:
            error=ctypes.get_last_error();self.close();raise ctypes.WinError(error)
        return self

    def read(self,max_age_ms=1000):
        if not self.view:raise ValueError('Reader closed')
        before=struct.unpack('<I',ctypes.string_at(self.view+12,4))[0]
        data=ctypes.string_at(self.view,84)
        after=struct.unpack('<I',ctypes.string_at(self.view+12,4))[0]
        return decode_frame(data,before,after,expected_pid=self.pid,expected_profile=self.profile,
                            expected_source=self.source_kind,now_tick=self.kernel.GetTickCount(),max_age_ms=max_age_ms)

    def close(self):
        if self.view:self.kernel.UnmapViewOfFile(self.view)
        if self.handle:self.kernel.CloseHandle(self.handle)
        self.view=None;self.handle=None

    def __enter__(self):return self.open()
    def __exit__(self,*args):self.close()


class NativeVitalsProvider:
    """Explicit session binding; does not discover, load or trust a publisher."""
    def __init__(self, pid, nonce, *, profile='us', source_kind=2, max_age_ms=1000):
        mapping_name(pid, nonce)
        if profile not in ('us', 'steam'):
            raise ValueError('Bilinmeyen oyun sürümü')
        if type(source_kind) is not int or source_kind not in (1, 2):
            raise ValueError('Açık kaynak türü gerekli')
        if type(max_age_ms) is not int or not 0 < max_age_ms <= 0xffffffff:
            raise ValueError('Pozitif DWORD örnek süresi gerekli')
        self.pid, self.nonce = pid, nonce
        self.profile = 1 if profile == 'us' else 2
        self.source_kind, self.max_age_ms = source_kind, max_age_ms

    def observe(self, pid):
        if type(pid) is not int or pid != self.pid:
            raise ValueError('Süreç kimliği bağlı yayıncıyla eşleşmiyor')
        now = int(time.monotonic() * 1000)
        operation = 'OpenFileMapping(FILE_MAP_READ)'
        try:
            with ReadOnlyNativeMap(self.pid, self.nonce, profile=self.profile,
                                   source_kind=self.source_kind) as reader:
                operation = 'ReadNativeFrame'
                result = reader.read(max_age_ms=self.max_age_ms)
            if result.status in ('fixture_candidate', 'candidate_unverified'):
                # No image identity or live verification is inferred from the frame.
                return Observation(result.status, pid, now, fields=dict(result.fields))
            diagnostic = result.error or ('Native status %d; WinError %d; aşama %d' %
                         (result.native_status, result.win_error, result.failed_step))
            return Observation(result.status, pid, now, error=diagnostic,
                               failed_operation=operation, error_code=result.win_error)
        except OSError as error:
            return Observation('unavailable', pid, now, error=str(error),
                               failed_operation=operation,
                               error_code=getattr(error, 'winerror', 0) or 0)

    def submit(self, intent):
        return {'status': 'unavailable', 'reason': 'Canlı eylem sağlayıcısı doğrulanmadı'}
