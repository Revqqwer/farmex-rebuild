"""Own stable UI rows -> source-shaped byte records, with explicit local codec.

No invented native helper receipts/addresses. Normal source value behavior is
implemented directly; native VCL/vector/CRT lifetime and game encoding remain
separate from this independent container.
"""
from dataclasses import dataclass
from flood_editor import FloodRow
from message_list_producer import MessageListRow
from rtl_integer import rtl_integer_or_default
from name_codec import WindowsNameCodec

LIST_PATH='frmMain/MainTab/sheetFlood/grpFlood/lwFlooding'

@dataclass(frozen=True)
class FloodCompilation:
    complete:bool
    snapshot:tuple
    code_page:int
    rows:tuple=()
    conversions:tuple=()
    fallback_rows:tuple=()
    failed_row:object=None
    error:str=''
    native_codec_equivalence_verified:bool=False
    native_vector_verified:bool=False
    live_compatibility_verified:bool=False

def compile_flood_rows(snapshot,code_page,*,codec_factory=WindowsNameCodec):
    if type(snapshot) is not tuple or any(not isinstance(r,FloodRow) for r in snapshot):raise ValueError('Immutable own Flood rows required')
    if type(code_page) is not int or not 1<=code_page<=65535:raise ValueError('Explicit nonzero Windows codepage required')
    rows=[];conversions=[];fallback=[];codec=None
    for index,row in enumerate(snapshot):
        try:
            if len(row.subitems)<2:raise ValueError('Mesaj ve bekleme sütunları gerekli')
            if codec is None:codec=codec_factory(code_page)
            converted=[]
            for role,text in (('channel',row.caption),('message',row.subitems[0])):
                result=codec.encode(text)
                if type(result) is not tuple or len(result)!=2 or type(result[0]) is not bytes or (result[1] is not None and type(result[1]) is not bool):raise ValueError('Explicit local codec result required')
                data,used_default=result;converted.append(data)
                conversions.append((index,role,data,used_default))
            parsed=rtl_integer_or_default(row.subitems[1],10)
            if parsed.used_default:fallback.append(index)
            # No min5 rule here: profile rows enter producer independently.
            delay=((parsed.result_qword&0xffffffff)*1000)&0xffffffff
            rows.append(MessageListRow(converted[0],converted[1],delay,index))
        except (ValueError,OSError,UnicodeError) as error:
            return FloodCompilation(False,snapshot,code_page,tuple(rows),tuple(conversions),tuple(fallback),index,str(error))
    return FloodCompilation(True,snapshot,code_page,tuple(rows),tuple(conversions),tuple(fallback))
