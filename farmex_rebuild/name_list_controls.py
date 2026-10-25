"""Own stable UI name-list edits; exact UTF16 policy, not native VCL/RTL proof."""
from dataclasses import dataclass
from source_unicode import utf16_key

ROOT='frmBlackList/grpContainer/'
LIST_PATHS={'white':ROOT+'AntiCRWhiteList','black':ROOT+'AntiCRBlackList'}
TEXT_PATHS={'white':ROOT+'txtAddWhiteList','black':ROOT+'txtAddCrBlackList'}
BUTTON_ACTIONS={ROOT+'btnAddTextWhiteList':('white','add'),ROOT+'btnAddTextBlackList':('black','add'),
                ROOT+'Button1':('white','clear'),ROOT+'Button2':('black','clear')}

@dataclass(frozen=True)
class NameListEdit:
    changed:bool
    kind:str
    action:str
    rows:tuple
    reason:str
    index:object=None
    policy:str='owned_stable_utf16'
    native_execution_verified:bool=False

def edit_name_list(kind,action,rows,*,text=None,selected_index=None):
    if kind not in LIST_PATHS or action not in ('add','remove','clear'):raise ValueError('Known name list/action required')
    if type(rows) is not tuple:raise ValueError('Immutable own Unicode rows required')
    keys=tuple(utf16_key(v) for v in rows)
    if action=='add':
        key=utf16_key(text)
        if text=='':return NameListEdit(False,kind,action,rows,'Boş isim eklenmedi')
        if key in keys:return NameListEdit(False,kind,action,rows,'İsim zaten listede')
        return NameListEdit(True,kind,action,rows+(text,),'İsim eklendi',len(rows))
    if action=='clear':return NameListEdit(bool(rows),kind,action,(),'Liste temizlendi' if rows else 'Liste zaten boş')
    if selected_index is not None and type(selected_index) is not int:raise ValueError('Explicit selected index required')
    if selected_index is None or not 0<=selected_index<len(rows):return NameListEdit(False,kind,action,rows,'Silinecek isim seçilmedi')
    return NameListEdit(True,kind,action,rows[:selected_index]+rows[selected_index+1:],'Seçilen isim silindi',selected_index)
