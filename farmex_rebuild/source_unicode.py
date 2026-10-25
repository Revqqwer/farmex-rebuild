"""Unicode equality SETZ wrapper and explicit own UTF16 model, no RTL loading."""
from dataclasses import dataclass

def utf16_key(value):
    if type(value) is not str:raise ValueError('Post-conversion Unicode text required')
    return value.encode('utf-16-le','surrogatepass')

@dataclass(frozen=True)
class UnicodeEqualityObservation:
    helper_returned:object=None
    zero_flag:object=None
    post_helper_eax_dword:object=None
    use_owned_text_model:bool=False
    left_text:object=None
    right_text:object=None
    def __post_init__(self):
        if self.helper_returned is not None and type(self.helper_returned) is not bool:raise ValueError('Explicit UStrEqual normal return required')
        if self.zero_flag is not None and type(self.zero_flag) is not bool:raise ValueError('Observed zero flag boolean required')
        v=self.post_helper_eax_dword
        if v is not None and (type(v) is not int or not 0<=v<1<<32):raise ValueError('Raw post-helper EAX DWORD required')
        if type(self.use_owned_text_model) is not bool:raise ValueError('Explicit own text-model selection required')
        for value in (self.left_text,self.right_text):
            if value is not None:utf16_key(value)

@dataclass(frozen=True)
class UnicodeEqualityPlan:
    complete:bool
    status:str
    al:object=None
    eax_dword:object=None
    zero_flag:object=None
    provenance:str='unavailable'
    left_utf16:object=None
    right_utf16:object=None
    missing:str=''
    native_runtime_verified:bool=False

def plan_unicode_equality(o):
    if not isinstance(o,UnicodeEqualityObservation):raise ValueError('Typed Unicode equality inputs required')
    if o.helper_returned is not True:return UnicodeEqualityPlan(False,'needs_observation',missing='UStrEqual normal return')
    left=None;right=None
    if o.use_owned_text_model:
        if o.zero_flag is not None:raise ValueError('Owned text equality conflicts with supplied zero flag')
        if o.left_text is None or o.right_text is None:
            return UnicodeEqualityPlan(False,'needs_observation',provenance='owned_utf16_model',missing='both post-conversion Unicode texts')
        left=utf16_key(o.left_text);right=utf16_key(o.right_text);zf=left==right;provenance='owned_utf16_model'
    else:
        if o.zero_flag is None:return UnicodeEqualityPlan(False,'needs_observation',missing='post-UStrEqual zero flag')
        zf=o.zero_flag;provenance='explicit_zero_flag'
    al=1 if zf else 0
    eax=None if o.post_helper_eax_dword is None else (o.post_helper_eax_dword&0xffffff00)|al
    return UnicodeEqualityPlan(True,'setz_al_planned',al,eax,zf,provenance,left,right)
