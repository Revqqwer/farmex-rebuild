"""004e8b94/004e8d40 lists and004e8eec/004e9154 cyclic route selection.

No FileExists, route file reads or game IO. Codec helpers here are explicit
owned Windows fixtures, not observed game/RTL codepage or error policies.
Counter updates in incomplete results are prospective source prefixes.
"""
from dataclasses import dataclass,replace
from typing import Optional,Tuple
from collections.abc import Mapping
from name_codec import WindowsNameCodec

LIST_PATHS={'supply':'frmSupplyRoutes/GroupBox1/SupplyRoutesList',
            'return':'frmReturnRoutes/GroupBox1/ReturnRoutesList'}

@dataclass(frozen=True)
class SupplyRouteLists:
    supply:Tuple[Optional[bytes],...]
    returning:Tuple[Optional[bytes],...]
    complete:bool
    missing:tuple=()

def compile_supply_route_lists(lists,*,codec=None):
    if not isinstance(lists,Mapping) or (codec is not None and not isinstance(codec,WindowsNameCodec)):
        raise ValueError('Profile lists and explicit Windows codec fixture required')
    projected={};missing=[]
    for kind,path in LIST_PATHS.items():
        if path not in lists or not isinstance(lists[path],(list,tuple)):raise ValueError('Explicit source route list required: '+path)
        names=[]
        for index,row in enumerate(lists[path]):
            if not isinstance(row,Mapping) or type(row.get('caption')) is not str:raise ValueError('Route list caption required')
            if codec is None:
                names.append(None);missing.append('%s[%d] Unicode->ANSI'%(kind,index))
            else:names.append(codec.encode(row['caption'])[0])
        projected[kind]=tuple(names)
    return SupplyRouteLists(projected['supply'],projected['return'],not missing,tuple(missing))

@dataclass(frozen=True)
class SupplyRouteState:
    supply_counter:int
    return_counter:int

    def __post_init__(self):
        for value in (self.supply_counter,self.return_counter):
            if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Observed raw counter DWORD required')

@dataclass(frozen=True)
class SupplyRouteObservation:
    decoded_name:Optional[str]=None
    first_encoded:Optional[bytes]=None
    prefix:Optional[bytes]=None
    path_unicode:Optional[str]=None
    file_exists_byte:Optional[int]=None
    success_encoded:Optional[bytes]=None

    def __post_init__(self):
        for value in (self.decoded_name,self.path_unicode):
            if value is not None and type(value) is not str:raise ValueError('Explicit Unicode conversion result required')
        for value in (self.first_encoded,self.prefix,self.success_encoded):
            if value is not None and type(value) is not bytes:raise ValueError('Explicit immutable ANSI bytes required')
        if self.file_exists_byte is not None and (type(self.file_exists_byte) is not int or not 0<=self.file_exists_byte<=255):
            raise ValueError('Raw FileExists AL BYTE required')

@dataclass(frozen=True)
class SupplyRouteDecision:
    status:str
    state:SupplyRouteState
    complete:bool
    selected_index:Optional[int]=None
    filename:Optional[bytes]=None
    candidate_path:Optional[bytes]=None
    file_exists_path:Optional[str]=None
    missing:str=''
    independently_verified:bool=False

def plan_supply_route_selection(lists,kind,state,observation=SupplyRouteObservation()):
    if not isinstance(lists,SupplyRouteLists) or not isinstance(state,SupplyRouteState) or not isinstance(observation,SupplyRouteObservation) or kind not in LIST_PATHS:
        raise ValueError('Typed route lists/state/observations and explicit kind required')
    if not lists.complete:return SupplyRouteDecision('needs_route_list_conversion',state,False,missing='; '.join(lists.missing))
    entries=lists.supply if kind=='supply' else lists.returning
    if not entries:return SupplyRouteDecision('empty_route_list',state,True,filename=b'')
    raw=state.supply_counter if kind=='supply' else state.return_counter
    signed=raw-(0x100000000 if raw&0x80000000 else 0)
    # Source signed JGE skips reset for negative counters, then indexes before
    # vector begin. Do not silently modulo, clamp or emulate that memory access.
    if signed<0:return SupplyRouteDecision('unresolved_source_counter',state,False,missing='negative signed route index')
    index=0 if signed>len(entries)-1 else signed
    counter_name='supply_counter' if kind=='supply' else 'return_counter'
    current=replace(state,**{counter_name:index}) # Reset occurs before first decode.
    path=None
    def gap(label):return SupplyRouteDecision('needs_route_observation',current,False,index,
        candidate_path=path,file_exists_path=observation.path_unicode,missing=label)
    if entries[index] is None:return gap('selected stored ANSI string')
    if observation.decoded_name is None:return gap('00403d84 selected ANSI->Unicode')
    current=replace(current,**{counter_name:(index+1)&0xffffffff})
    if observation.first_encoded is None:return gap('004073a0 first Unicode->ANSI')
    if observation.prefix is None:return gap('source field+57c ANSI prefix')
    path=observation.prefix+observation.first_encoded # Source concatenation; no separator normalization.
    if observation.path_unicode is None:return gap('00403d84 FileExists path Unicode')
    if observation.file_exists_byte is None:return gap('FileExists(path,True) AL')
    if not observation.file_exists_byte:
        return SupplyRouteDecision('route_file_missing',current,True,index,b'',path,observation.path_unicode)
    if observation.success_encoded is None:return gap('004073a0 fresh successful filename conversion')
    return SupplyRouteDecision('route_selected',current,True,index,observation.success_encoded,path,observation.path_unicode)

def route_codec_fixture(stored_name,prefix,codec,*,file_exists_byte=None):
    if type(stored_name) is not bytes or type(prefix) is not bytes or not isinstance(codec,WindowsNameCodec):
        raise ValueError('Owned ANSI names/prefix and explicit Windows codec fixture required')
    unicode_name=codec.decode(stored_name)
    first=codec.encode(unicode_name)[0]
    path=codec.decode(prefix+first)
    second=codec.encode(unicode_name)[0]
    return SupplyRouteObservation(unicode_name,first,prefix,path,file_exists_byte,second)
