"""Independent offline Unicode Flood list editor; no native VCL/game effects.

This UI implementation consumes the proven add threshold and list layout. It
does not claim native StrToInt64/ANSI, virtual mutation or worker equivalence.
"""
from dataclasses import dataclass
from rtl_integer import rtl_integer_or_default

PREFIX='frmMain/MainTab/sheetFlood/grpFlood/'
LIST_PATH=PREFIX+'lwFlooding'
CHANNEL_PATH=PREFIX+'GroupBox49/cmbAddFloodList'
MESSAGE_PATH=PREFIX+'GroupBox49/txtAddFloodList'
DELAY_PATH=PREFIX+'GroupBox49/txtAddFloodingWait'
BUTTON_ACTIONS={PREFIX+'GroupBox49/btnAddFloodList':'add',
                PREFIX+'btnRemoveFloodList':'selected',PREFIX+'btnClearFloodList':'clear'}

@dataclass(frozen=True)
class FloodRow:
    caption:str
    subitems:tuple
    checked:bool=False
    def __post_init__(self):
        if type(self.caption) is not str or type(self.subitems) is not tuple or any(type(s) is not str for s in self.subitems) or type(self.checked) is not bool:raise ValueError('Geçerli Flood satırı gerekli')

@dataclass(frozen=True)
class FloodEdit:
    changed:bool
    status:str
    rows:tuple
    selected_index:object=None
    source_native_equivalence_verified:bool=False
    live_compatibility_verified:bool=False

def read_rows(rows):
    if type(rows) is not list:raise ValueError('Flood listesi gerekli')
    result=[]
    for row in rows:
        if type(row) is not dict or set(row)!= {'caption','subitems','checked'} or type(row['subitems']) is not list:raise ValueError('Flood satır yapısı geçersiz')
        result.append(FloodRow(row['caption'],tuple(row['subitems']),row['checked']))
    return tuple(result)

def write_rows(rows):
    return [dict(caption=r.caption,subitems=list(r.subitems),checked=r.checked) for r in rows]

def flood_delay(text):
    """Source-derived scalar parsing with independent fallback10 policy."""
    if type(text) is not str:raise ValueError('Bekleme süresi metni gerekli')
    number=rtl_integer_or_default(text,10)
    low=number.result_qword&0xffffffff
    return low if low<0x80000000 else low-(1<<32)

# Preserve the earlier internal API name; accepted syntax is now broader.
decimal_delay=flood_delay

def edit_flood(action,rows,*,channels=(),channel_index=None,message='',delay_text='',selected_index=None):
    if type(rows) is not tuple or any(not isinstance(r,FloodRow) for r in rows):raise ValueError('Bağımsız Flood satırları gerekli')
    if action=='clear':return FloodEdit(bool(rows),'cleared' if rows else 'already_empty',())
    if action=='selected':
        if selected_index is not None and type(selected_index) is not int:raise ValueError('Seçili Flood indeksi geçersiz')
        if selected_index is None or not 0<=selected_index<len(rows):return FloodEdit(False,'no_selection',rows)
        return FloodEdit(True,'removed',rows[:selected_index]+rows[selected_index+1:])
    if action!='add':raise ValueError('Bilinmeyen Flood işlemi')
    if type(channels) is not tuple or any(type(s) is not str for s in channels) or type(channel_index) is not int or not 0<=channel_index<len(channels):raise ValueError('Mesaj kanalını seçin')
    if type(message) is not str:raise ValueError('Mesaj metni gerekli')
    delay=flood_delay(delay_text)
    if delay<5:return FloodEdit(False,'delay_rejected',rows)
    return FloodEdit(True,'added',rows+(FloodRow(channels[channel_index],(message,str(delay))),),len(rows))
