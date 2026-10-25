"""Scoped RTL260 text/BOM submodels; explicit runtime fields, no BPL loading."""
from dataclasses import dataclass
from source_unicode import utf16_key

def _byte(v):
    if v is not None and (type(v) is not int or not 0<=v<=255):raise ValueError('Raw runtime flags BYTE required')

@dataclass(frozen=True)
class ListTextPlan:
    complete:bool
    status:str
    text:object=None
    rows:object=None
    requested_utf16_units:object=None
    missing:str=''
    native_execution_verified:bool=False

def plan_crlf_set_text(text,line_break):
    """501614a4 common CRLF branch; custom AnsiStrPos branch stays unresolved."""
    if text is None or line_break is None:return ListTextPlan(False,'needs_observation',missing='decoded text and runtime LineBreak')
    encoded=utf16_key(text);delimiter=utf16_key(line_break)
    if delimiter!=b'\r\0\n\0':return ListTextPlan(False,'needs_custom_delimiter_observation',missing='native AnsiStrPos/custom LineBreak branch')
    units=[int.from_bytes(encoded[i:i+2],'little') for i in range(0,len(encoded),2)]
    rows=[];start=0
    while start<len(units) and units[start]!=0:
        end=start
        while end<len(units) and units[end] not in (0,10,13):end+=1
        rows.append(encoded[start*2:end*2].decode('utf-16-le','surrogatepass'))
        start=end
        if start<len(units) and units[start]==13:start+=1
        if start<len(units) and units[start]==10:start+=1
    return ListTextPlan(True,'crlf_rows_modeled',rows=tuple(rows))

def plan_stable_get_text(rows,line_break,flags_byte,*,stable_same_invocation=False):
    """50160b20 two-pass text copy; own explicit stable same-invocation input."""
    _byte(flags_byte)
    if stable_same_invocation is not True:raise ValueError('Explicit stable own two-pass rows required')
    if type(rows) is not tuple:raise ValueError('Immutable Unicode rows required')
    lengths=[len(utf16_key(t))//2 for t in rows]
    if line_break is None or flags_byte is None:return ListTextPlan(False,'needs_observation',missing='runtime LineBreak and flags BYTE')
    width=len(utf16_key(line_break))//2;trailing=bool(flags_byte&4)
    requested=sum(lengths)+width*len(rows)-(0 if trailing else width)
    if requested<0:return ListTextPlan(False,'unresolved_negative_native_length',requested_utf16_units=requested,missing='UStrFromPWCharLen negative length behavior')
    # Overflow/size faults from the native accumulator are not silently clipped.
    if requested>0x7fffffff:return ListTextPlan(False,'unresolved_native_length_overflow',requested_utf16_units=requested)
    text=line_break.join(rows)+(line_break if rows and trailing else '')
    return ListTextPlan(True,'stable_text_modeled',text=text,requested_utf16_units=requested)

@dataclass(frozen=True)
class ListStreamPlan:
    complete:bool
    status:str
    encoding_pointer_dword:object=None
    write_chunks:tuple=()
    payload:object=None
    missing:str=''
    native_execution_verified:bool=False

def plan_list_stream_bytes(encoding_pointer,default_encoding_pointer,flags_byte,encoded_bytes,*,preamble_bytes=None):
    """501612d8 selection and observed GetBytes/preamble order, no codec guess."""
    _byte(flags_byte)
    for v in (encoding_pointer,default_encoding_pointer):
        if v is not None and (type(v) is not int or not 0<=v<1<<32):raise ValueError('Raw encoding object pointer DWORD required')
    for v in (encoded_bytes,preamble_bytes):
        if v is not None and type(v) is not bytes:raise ValueError('Exact observed encoding bytes required')
    selected=default_encoding_pointer if encoding_pointer==0 else encoding_pointer
    if selected is None or selected==0 or flags_byte is None or encoded_bytes is None:
        return ListStreamPlan(False,'needs_observation',selected,missing='selected encoding/runtime flags/GetBytes result')
    chunks=[]
    if flags_byte&2:
        if preamble_bytes is None:return ListStreamPlan(False,'needs_observation',selected,missing='encoding GetPreamble result')
        if preamble_bytes:chunks.append(preamble_bytes)
    chunks.append(encoded_bytes)
    return ListStreamPlan(True,'stream_write_bytes_modeled',selected,tuple(chunks),b''.join(chunks))
