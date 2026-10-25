"""00458f98 entry through00459071: NP/coins/level source guard plans.

Later clock/party/alarm branches are excluded. All queries and normal returns
are supplied observations. No game state, stop operation or Town is executed.
"""
import re
from dataclasses import dataclass,field
from types import MappingProxyType

ROOT='frmMain/MainTab/SheetKontrol/GroupBox43/'
FLAG_PATHS={ROOT+'chNPControl':0xbf,ROOT+'chCoinControl':0xc0,ROOT+'chLevelKontrol':0xd0}
NUMBER_PATHS={ROOT+'txtCoinControlValue':(0xc8,64),ROOT+'txtLevelKontrol':(0xd4,32)}
CONTROL_GUARD_INPUTS=tuple(FLAG_PATHS)+tuple(NUMBER_PATHS)

@dataclass(frozen=True)
class ControlGuardConfiguration:
    fields:object
    parser_scope:str='strict_decimal_subset'

    def __post_init__(self):object.__setattr__(self,'fields',MappingProxyType(dict(self.fields)))

def compile_control_guards(values):
    fields={}
    for path,offset in FLAG_PATHS.items():
        value=values.get(path)
        if type(value) is not bool:raise ValueError('Control checkbox required: '+path)
        fields[offset]=int(value)
    for path,(offset,bits) in NUMBER_PATHS.items():
        value=values.get(path)
        if type(value) is not str or not re.fullmatch(r'[+-]?[0-9]+',value.strip()):
            raise ValueError('Strict decimal control parameter required: '+path)
        parsed=int(value.strip())
        if not -(1<<63)<=parsed<(1<<63):raise ValueError('Signed64 control parameter required')
        fields[offset]=parsed&0xffffffff
        if bits==64:fields[offset+4]=(parsed>>32)&0xffffffff
    return ControlGuardConfiguration(fields)

@dataclass(frozen=True)
class ControlGuardObservation:
    np_462718:object=None
    coins_46258c:object=None
    level_462670:object=None
    stop_returned:object=None
    town_returned:object=None

    def __post_init__(self):
        for value in (self.np_462718,self.coins_46258c,self.level_462670):
            if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):raise ValueError('Observed DWORD query required')
        for value in (self.stop_returned,self.town_returned):
            if value is not None and type(value) is not bool:raise ValueError('Observed normal return required')

@dataclass(frozen=True)
class ControlGuardPlan:
    status:str
    complete:bool
    source_return_planned:bool=False
    calls:tuple=()
    missing:str=''
    next_address:object=None
    native_execution_verified:bool=False

class _Missing(Exception):pass

def plan_control_guards(configuration,observation):
    if not isinstance(configuration,ControlGuardConfiguration) or not isinstance(observation,ControlGuardObservation):
        raise ValueError('Typed control config and observations required')
    c=configuration.fields;o=observation;calls=[]
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def f(offset,bits):
        value=need(c.get(offset),'field+%x'%offset)
        if type(value) is not int or not 0<=value<(1<<bits):raise ValueError('Raw control field required')
        return value
    def query(address,value):
        calls.append((address,()))
        return need(value,address+' DWORD return')
    def stop_town(reason):
        calls.append(('0040ae0c',(0x561f34,0)))
        if o.stop_returned is not True:raise _Missing('0040ae0c normal return')
        calls.append(('00465678',()))
        if o.town_returned is not True:raise _Missing('00465678 normal return')
        return ControlGuardPlan(reason,True,True,tuple(calls))
    try:
        if f(0xbf,8)!=0 and query('00462718',o.np_462718)==0:return stop_town('np_zero_stop_town')
        if f(0xc0,8)!=0:
            coins=query('0046258c',o.coins_46258c)
            high=f(0xcc,32)
            # Source reads low threshold only after equal high DWORDs.
            trigger=coins<=f(0xc8,32) if high==0 else high<0x80000000
            if trigger:return stop_town('coins_at_or_below_stop_town')
        if f(0xd0,8)!=0 and query('00462670',o.level_462670)==f(0xd4,32):return stop_town('level_equal_stop_town')
        return ControlGuardPlan('entry_guards_passed',True,False,tuple(calls),next_address=0x459071)
    except _Missing as exc:return ControlGuardPlan('needs_observation',False,calls=tuple(calls),missing=str(exc))
