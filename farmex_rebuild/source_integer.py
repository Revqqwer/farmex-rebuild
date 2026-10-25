"""0045ef80 captured normal/catch-landing replay; external RTL is not emulated."""
from dataclasses import dataclass,replace

def raw(value,bits):
    if value is not None and (type(value) is not int or not 0<=value<1<<bits):raise ValueError('Raw integer operand required')

@dataclass(frozen=True)
class SourceIntegerObservation:
    text_copy_returned:object=None
    route:object=None
    parser_returned:object=None
    parser_qword:object=None
    catch_landing_returned:object=None
    cleanup_returned:object=None
    def __post_init__(self):
        for v in (self.text_copy_returned,self.parser_returned,self.catch_landing_returned,self.cleanup_returned):
            if v is not None and type(v) is not bool:raise ValueError('Separate integer helper receipts required')
        if self.route is not None and self.route not in ('normal','catch_landing'):raise ValueError('Explicit reached integer route required')
        raw(self.parser_qword,64)

@dataclass(frozen=True)
class SourceIntegerPlan:
    complete:bool
    default_qword:int
    result_qword:object=None
    low_dword:object=None
    high_dword:object=None
    calls:tuple=()
    missing:str=''
    needed:object=None
    lexical_conversion_verified:bool=False
    native_execution_verified:bool=False

def plan_source_integer(text,default_dword,o):
    if type(text) is not str or not isinstance(o,SourceIntegerObservation):raise ValueError('Immutable Unicode text and typed conversion observations required')
    raw(default_dword,32)
    if default_dword is None:raise ValueError('Explicit fallback DWORD required')
    default=(default_dword if default_dword<1<<31 else default_dword-(1<<32))&((1<<64)-1)
    calls=[];result=None
    def finish(ok,missing='',needed=None):
        return SourceIntegerPlan(ok,default,result,result&0xffffffff if result is not None else None,result>>32 if result is not None else None,tuple(calls),missing,needed)
    calls.append('UnicodeString_copy')
    if o.text_copy_returned is not True:return finish(False,'text copy normal return','text_copy_returned')
    if o.route is None:return finish(False,'reached parser normal or catch landing route','route')
    calls.append('rtl260.bpl:StrToInt64')
    if o.route=='normal':
        if o.parser_returned is not True:return finish(False,'StrToInt64 normal return','parser_returned')
        if o.parser_qword is None:return finish(False,'StrToInt64 EDX:EAX','parser_qword')
        result=o.parser_qword
    else:
        # Explicit landing-path receipt, not inferred from invalid/empty text.
        calls.append('CC32260MT.DLL:_CatchCleanup')
        if o.catch_landing_returned is not True:return finish(False,'catch landing cleanup normal return','catch_landing_returned')
        result=default
    calls.append('UnicodeString_cleanup_preserving_EDX_EAX')
    if o.cleanup_returned is not True:return finish(False,'argument cleanup normal return','cleanup_returned')
    return finish(True)

class SourceIntegerFrame:
    def __init__(self,text,default_dword):
        self.text=text;self.default=default_dword;self.observation=SourceIntegerObservation();self.final=None
        plan_source_integer(text,default_dword,self.observation)
    def advance(self,o):
        if not isinstance(o,SourceIntegerObservation):raise ValueError('Typed conversion observations required')
        if self.final is not None:return self.final
        for _ in range(8):
            p=plan_source_integer(self.text,self.default,self.observation)
            if p.complete:self.final=p;return p
            field=p.needed;value=getattr(o,field)
            if value is None or (field.endswith('_returned') and value is not True):return p
            self.observation=replace(self.observation,**{field:value})
        raise ValueError('Source integer observation budget exceeded')
