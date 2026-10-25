"""0046b928 ordered settings body replay; owned scalar/string projections only.

VCL/string/CRT helpers require separate normal receipts. Numeric helper children
reuse captured StrToInt64/catch-landing semantics, never infer a lexical parse.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from source_integer import SourceIntegerFrame,SourceIntegerObservation

# type, source form member, context member, optional default/priority mapping.
OPS=(
 ('flag',0xb28,0x39),('flag',0x748,0x08),('flag',0x754,0x09),
 ('number',0x74c,0x0c,80),('flag',0x750,0x120),('string',0x760,0x24),
 ('flag',0x768,0x14),('enum',((0x758,5),(0x75c,0),(0x76c,1),(0x770,2)),0x10),
 ('flag',0x774,0x18),('flag',0x778,0x19),('flag',0x77c,0x15),
 ('flag',0x780,0x16),('flag',0x784,0x1a),('number',0x788,0x1c,60),
 ('flag',0x78c,0x17),('flag',0x7d8,0x28),('number',0x7dc,0x2c,50),
 ('flag',0x7e0,0x30),('string',0x7f0,0x3c),('flag',0x7f4,0x38),
 ('enum',((0x7ec,0),(0x7e4,1),(0x7e8,2)),0x34),
 ('flag',0x798,0x41),('flag',0x79c,0x43),('flag',0x7a8,0x48),
 ('string',0x7b0,0x54),('number',0x7bc,0x4c,30),
 ('flag',0x7c0,0x50),('flag',0x7c4,0x58),
 ('enum',((0x7a0,0),(0x7cc,4),(0x7a4,1),(0x7ac,2),(0x7b8,3)),0x44),
 ('flag',0x7fc,0x80),('flag',0x814,0x81),('string',0x80c,0x88),
 ('enum',((0x800,0),(0x808,1),(0x818,3),(0x804,4)),0x84),
 ('flag',0xb0c,0xb0),('choice_else',0xb10,0xb4,1,2),
 ('flag',0xb18,0xb8),('flag',0xb1c,0xb9),('flag',0xb20,0xba))

def label(slot):return '%03x'%slot

@dataclass(frozen=True)
class ProtectionSettingsObservation:
    entry_reached:bool=False
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    texts:object=field(default_factory=dict)
    ansi_bytes:object=field(default_factory=dict)
    integer_children:object=field(default_factory=dict)
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit producer entry required')
        values=dict(self.values);normals=dict(self.normal_returns);texts=dict(self.texts)
        ansi=dict(self.ansi_bytes);children=dict(self.integer_children)
        if any(type(v) is not int or not 0<=v<=0xffffffff for v in values.values()):raise ValueError('Raw getter DWORD required')
        if any(type(v) is not bool for v in normals.values()):raise ValueError('Separate producer normal receipts required')
        if any(type(v) is not str for v in texts.values()):raise ValueError('Captured Unicode text required')
        if any(type(v) is not bytes for v in ansi.values()):raise ValueError('Captured ANSI serialization bytes required')
        if any(not isinstance(v,SourceIntegerObservation) for v in children.values()):raise ValueError('Typed numeric child required')
        for key,value in (('values',values),('normal_returns',normals),('texts',texts),('ansi_bytes',ansi),('integer_children',children)):
            object.__setattr__(self,key,MappingProxyType(value))

@dataclass(frozen=True)
class ProtectionSettingsPlan:
    complete:bool
    calls:tuple=()
    stores:tuple=()
    string_assignments:tuple=()
    unchanged_enum_offsets:tuple=()
    children:tuple=()
    next_address:object=None
    missing:str=''
    needed:object=None
    whole_producer_verified:bool=False
    lexical_conversion_verified:bool=False
    string_identity_verified:bool=False
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class _Wait(Exception):
    def __init__(self,kind,name):self.needed=(kind,name);super().__init__(name+' '+kind)

def plan_protection_settings(o,*,context=0x5690f8,_child=None,_ops=OPS,
                             _entry='0046b928',_exit=0x46c18f,_prologue=True):
    if not isinstance(o,ProtectionSettingsObservation):raise ValueError('Typed protection observations required')
    if type(context) is not int or not 0<=context<=0xffffffff:raise ValueError('Raw producer context required')
    calls=[];stores=[];strings=[];unchanged=[];children=[]
    def result(error=None):return ProtectionSettingsPlan(error is None,tuple(calls),tuple(stores),tuple(strings),tuple(unchanged),tuple(children),
        _exit if error is None else None,'' if error is None else str(error),None if error is None else error.needed)
    def normal(key,role,args=()):
        calls.append((role,args,key))
        if o.normal_returns.get(key) is not True:raise _Wait('normal',key)
    def field(kind,key):
        mapping=getattr(o,kind)
        if key not in mapping:raise _Wait(kind,key)
        return mapping[key]
    def checked(slot):
        key='checked_'+label(slot)
        normal(key,'VCL_Checked_getter_span',('form_field',slot))
        return field('values',key)&255
    def store(offset,width,value):stores.append(((context+offset)&0xffffffff,width,value))
    try:
        if not o.entry_reached:raise _Wait('entry',_entry)
        if _prologue:normal('prologue','00504c08_SEH_setup')
        for op in _ops:
            kind,slot,offset=op[:3]
            if kind=='flag':store(offset,1,checked(slot))
            elif kind=='constant':store(offset,1,op[3])
            elif kind=='index':
                key='index_'+label(slot)
                normal(key,'VCL_Index_getter_span',('form_field',slot))
                store(offset,4,field('values',key))
            elif kind=='choice_else':store(offset,4,op[3] if checked(slot) else op[4])
            elif kind=='enum':
                for source,value in slot:
                    if checked(source):store(offset,4,value);break
                else:unchanged.append(offset) #No source store, not a default0.
            else:
                key=label(slot)
                normal('init_'+key,'00404a78 Unicode temporary')
                normal('text_'+key,'VCL_Text_getter_span',('form_field',slot))
                text=field('texts',key)
                if kind in ('number','number64'):
                    child=_child(key,text,op[3]) if _child else SourceIntegerFrame(text,op[3]).advance(o.integer_children.get(key,SourceIntegerObservation()))
                    children.append((key,child))
                    if not child.complete:raise _Wait('child',key)
                    normal('parser_outer_'+key,'0045ef80',(op[3],'captured_text'))
                    store(offset,4,child.low_dword)
                    if kind=='number64':store(offset+4,4,child.high_dword)
                else:
                    normal('ansi_'+key,'004073a0 Unicode-to-ANSI span')
                    data=field('ansi_bytes',key)
                    normal('assign_'+key,'005050e4 string assignment',((context+offset)&0xffffffff,))
                    strings.append(((context+offset)&0xffffffff,data))
                    normal('ansi_cleanup_'+key,'004040f8 ANSI temporary cleanup')
                normal('text_cleanup_'+key,'00505c64 Unicode temporary cleanup')
        return result()
    except _Wait as error:return result(error)

class ProtectionSettingsFrame:
    _planner=staticmethod(plan_protection_settings)
    def __init__(self,*,context=0x5690f8):
        self.context=context;self.observation=ProtectionSettingsObservation();self.frames={};self.final=None
        self._planner(self.observation,context=context)
    def advance(self,incoming):
        if not isinstance(incoming,ProtectionSettingsObservation):raise ValueError('Typed protection observations required')
        if self.final is not None:return self.final
        def child(key,text,default):
            if key not in self.frames:self.frames[key]=SourceIntegerFrame(text,default)
            return self.frames[key].advance(incoming.integer_children.get(key,SourceIntegerObservation()))
        for _ in range(512):
            p=self._planner(self.observation,context=self.context,_child=child)
            if p.complete:self.final=p;return p
            kind,key=p.needed
            if kind=='child':return p
            if kind=='entry':
                if not incoming.entry_reached:return p
                self.observation=replace(self.observation,entry_reached=True)
            elif kind=='normal':
                if incoming.normal_returns.get(key) is not True:return p
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,key:True})
            else:
                fields=getattr(incoming,kind)
                if key not in fields:return p
                self.observation=replace(self.observation,**{kind:{**getattr(self.observation,kind),key:fields[key]}})
        raise AssertionError('Protection producer reached-field budget exceeded')
