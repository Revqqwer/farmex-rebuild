"""Explicit local CFG codec from scoped RTL text/default evidence; no BPL IO.

Valid Unicode/BOM and roundtrippable MBCS data only. Invalid/fallback/runtime
codec paths are reported unresolved rather than silently emulated.
"""
from dataclasses import dataclass
from pathlib import Path
import os,tempfile,ntpath
import ctypes,sys
from name_codec import WindowsNameCodec
from delphi_list_text import plan_crlf_set_text,plan_stable_get_text,plan_list_stream_bytes

PREAMBLES=((65001,b'\xef\xbb\xbf'),(1200,b'\xff\xfe'),(1201,b'\xfe\xff'))
RUNTIME_DEFAULT_FLAGS=0x0e

def local_codepage():
    """Measure only this Windows host; not the game's cached encoding object."""
    if sys.platform!='win32':raise OSError('Windows ACP query unavailable')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetACP.argtypes=[];kernel.GetACP.restype=ctypes.c_uint
    value=kernel.GetACP();_codepage(value)
    return value

def _codepage(v):
    if type(v) is not int or not 1<=v<=65535:raise ValueError('Explicit nonzero local codepage required')

@dataclass(frozen=True)
class NameCfgDocument:
    rows:tuple
    encoding_codepage:int
    flags_byte:int=RUNTIME_DEFAULT_FLAGS
    line_break:str='\r\n'
    def __post_init__(self):
        from source_unicode import utf16_key
        if type(self.rows) is not tuple:raise ValueError('Immutable Unicode rows required')
        for row in self.rows:utf16_key(row)
        _codepage(self.encoding_codepage)
        if type(self.flags_byte) is not int or not 0<=self.flags_byte<=255:raise ValueError('Raw runtime flags BYTE required')
        utf16_key(self.line_break)

@dataclass(frozen=True)
class NameCfgCodecResult:
    complete:bool
    status:str
    document:object=None
    payload:object=None
    preamble_size:int=0
    missing:str=''
    source_context:str='explicit local codec; loaded game runtime and fallback behavior unverified'
    native_execution_verified:bool=False

def _decode(data,codepage):
    if codepage in (1200,1201):return data.decode('utf-16-le' if codepage==1200 else 'utf-16-be',errors='strict')
    if codepage==65001:data.decode('utf-8',errors='strict')
    codec=WindowsNameCodec(codepage);text=codec.decode(data);encoded,used=codec.encode(text)
    if used or encoded!=data:raise UnicodeError('Local codec is not byte-roundtrippable')
    return text

def _encode(text,codepage):
    if codepage in (1200,1201):return text.encode('utf-16-le' if codepage==1200 else 'utf-16-be',errors='strict')
    if codepage==65001:text.encode('utf-8',errors='strict')
    codec=WindowsNameCodec(codepage);data,used=codec.encode(text)
    if used or codec.decode(data).encode('utf-16-le','surrogatepass')!=text.encode('utf-16-le','surrogatepass'):
        raise UnicodeError('Local codec loses Unicode text')
    return data

def decode_name_cfg(data,default_codepage,*,explicit_codepage=None,flags_byte=RUNTIME_DEFAULT_FLAGS,line_break='\r\n'):
    if type(data) is not bytes:raise ValueError('Exact CFG bytes required')
    _codepage(default_codepage)
    if explicit_codepage is not None:_codepage(explicit_codepage)
    selected=explicit_codepage or default_codepage;skip=0
    for cp,preamble in PREAMBLES:
        if (explicit_codepage is None or explicit_codepage==cp) and data.startswith(preamble):
            selected=cp;skip=len(preamble);break
    # Validate metadata even when the file decodes to an empty row set.
    NameCfgDocument((),selected,flags_byte,line_break)
    try:text=_decode(data[skip:],selected)
    except (UnicodeError,OSError,LookupError) as e:return NameCfgCodecResult(False,'unresolved_codec_conversion',missing=str(e))
    parsed=plan_crlf_set_text(text,line_break)
    if not parsed.complete:return NameCfgCodecResult(False,parsed.status,missing=parsed.missing)
    return NameCfgCodecResult(True,'cfg_rows_decoded',NameCfgDocument(parsed.rows,selected,flags_byte,line_break),preamble_size=skip)

def encode_name_cfg(document):
    if not isinstance(document,NameCfgDocument):raise ValueError('Typed CFG document required')
    text=plan_stable_get_text(document.rows,document.line_break,document.flags_byte,stable_same_invocation=True)
    if not text.complete:return NameCfgCodecResult(False,text.status,document,missing=text.missing)
    try:data=_encode(text.text,document.encoding_codepage)
    except (UnicodeError,OSError,LookupError) as e:return NameCfgCodecResult(False,'unresolved_codec_conversion',document,missing=str(e))
    preamble=next((p for cp,p in PREAMBLES if cp==document.encoding_codepage),b'')
    # Only bytes/order are modeled here;1 is an own nonnull token,not a native
    # encoding object pointer or assertion that the original helper executed.
    stream=plan_list_stream_bytes(1,None,document.flags_byte,data,preamble_bytes=preamble)
    return NameCfgCodecResult(stream.complete,'cfg_bytes_encoded',document,stream.payload,len(preamble) if document.flags_byte&2 else 0,stream.missing)

def _path(path):
    if type(path) is not str or not ntpath.isabs(path) or '\0' in path:raise ValueError('Explicit absolute local CFG path required')
    return Path(path)

def read_name_cfg(path,default_codepage,*,max_bytes=1048576,**kwargs):
    p=_path(path);_codepage(default_codepage)
    if type(max_bytes) is not int or max_bytes<1:raise ValueError('Positive own file budget required')
    try:
        with p.open('rb') as stream:data=stream.read(max_bytes+1)
    except OSError as e:return NameCfgCodecResult(False,'file_unreadable',missing=str(e))
    if len(data)>max_bytes:return NameCfgCodecResult(False,'local_file_budget',missing='CFG exceeds explicit own read budget')
    return decode_name_cfg(data,default_codepage,**kwargs)

def write_name_cfg(path,document):
    """Own atomic explicit-path write; no original Farmex folder discovery."""
    p=_path(path);encoded=encode_name_cfg(document)
    if not encoded.complete:return encoded
    fd,scratch=tempfile.mkstemp(prefix='.name-cfg-',dir=str(p.parent))
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(encoded.payload);stream.flush();os.fsync(stream.fileno())
        os.replace(scratch,str(p))
    finally:
        if os.path.exists(scratch):os.unlink(scratch)
    return encoded
