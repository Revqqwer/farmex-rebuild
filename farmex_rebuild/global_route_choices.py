"""Other8 filename branches of004ebca0; trigger detection is not implemented.

ANSI globals are explicit observations, not guessed from combo ItemIndex. Mine
reuses the verified cyclic algorithm with a separate counter and prefix sample.
An own known-Text projector below labels eight fields without native writes.
The internal selector's counter slot is a proxy; choice.mine_counter is the
mining counter, and choice.state retains the real Supply/Return model state.
"""
from dataclasses import dataclass,replace
from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional
from supply_routes import SupplyRouteLists,SupplyRouteState,SupplyRouteObservation,plan_supply_route_selection
from supply_route_start import SupplyRouteChoice
from name_codec import WindowsNameCodec
from source_unicode import utf16_key
from route_catalog import ROUTE_COMBO_PATHS

ROUTE_GLOBALS=MappingProxyType({'Mine':0x56fa94,'SMerchant':0x5698bc,'BMerchant':0x569908,
    'AntiCR':0x56911c,'Enemy':0x569134,'Notice':0x56914c,'PMKONTROL':0x569180,'Relog':0x562230})
MINE_CHANGE_PATH='frmMain/MainTab/SheetMaden/GroupBox51/chChangeMiningRoute'
MINE_LIST_PATH='frmMiningRoutes/GroupBox1/MiningRoutesList'

def compile_panel_route_name(kind,combo_texts,codec):
    """Own known combo Text -> source-address-labelled ANSI field; no writes.

    Only the requested filename is consumed. This does not certify native
    GetText/conversion/assignment helper returns or their enclosing settings.
    """
    if kind not in ROUTE_GLOBALS or not isinstance(combo_texts,Mapping) or not isinstance(codec,WindowsNameCodec):
        raise ValueError('Known global route kind, own Text snapshot and explicit codec required')
    text=combo_texts.get(ROUTE_COMBO_PATHS[kind])
    if type(text) is not str:raise ValueError('Seçilen rota için panel Text gözlemi gerekli')
    encoded,used=codec.encode(text)
    if used or utf16_key(codec.decode(encoded))!=utf16_key(text):
        raise ValueError('Rota adı seçilen kod sayfasında kayıpsız temsil edilemiyor')
    return MappingProxyType({ROUTE_GLOBALS[kind]:encoded})

@dataclass(frozen=True)
class MiningRouteInputs:
    change_byte:int
    names:tuple

def compile_mining_route_inputs(values,lists,codec):
    if not isinstance(values,Mapping) or not isinstance(lists,Mapping) or not isinstance(codec,WindowsNameCodec):
        raise ValueError('Explicit panel/list/owned codec fixture required')
    flag=values.get(MINE_CHANGE_PATH)
    if type(flag) is not bool:raise ValueError('Mining change-route boolean required')
    rows=lists.get(MINE_LIST_PATH)
    if not isinstance(rows,(list,tuple)):raise ValueError('Explicit MiningRoutesList required')
    names=[]
    for row in rows:
        if not isinstance(row,Mapping) or type(row.get('caption')) is not str:raise ValueError('Mining list caption required')
        names.append(codec.encode(row['caption'])[0])
    return MiningRouteInputs(int(flag),tuple(names))

def plan_global_route_choice(kind,global_names,state,*,mine_change_byte=None,mine_names=None,
                             mine_counter=None,observation=SupplyRouteObservation()):
    if kind not in ROUTE_GLOBALS or not isinstance(global_names,Mapping) or not isinstance(state,SupplyRouteState):
        raise ValueError('Exact source kind, observed ANSI globals and typed counters required')
    name=global_names.get(ROUTE_GLOBALS[kind])
    if name is None:return SupplyRouteChoice('needs_global_route_observation',state,False,
        missing='ANSI string at%08x'%ROUTE_GLOBALS[kind],mine_counter=mine_counter)
    if type(name) is not bytes:raise ValueError('Observed immutable ANSI global required')
    if kind!='Mine':return SupplyRouteChoice('global_route_choice',state,True,name)
    if mine_change_byte is None:return SupplyRouteChoice('needs_mining_change_observation',state,False,name,
        missing='0056fa98 BYTE',mine_counter=mine_counter)
    if type(mine_change_byte) is not int or not 0<=mine_change_byte<=255:raise ValueError('Raw mining change BYTE required')
    if not mine_change_byte:return SupplyRouteChoice('mining_manual_route_choice',state,True,name,mine_counter=mine_counter)
    if mine_names is None:return SupplyRouteChoice('needs_mining_list_observation',state,False,name,
        missing='source mining vector+6018/601c',mine_counter=mine_counter)
    if type(mine_names) is not tuple or any(type(v) is not bytes for v in mine_names):raise ValueError('Observed mining ANSI vector required')
    if not mine_names:return SupplyRouteChoice('mining_manual_fallback',state,True,name,mine_counter=mine_counter)
    if mine_counter is None:return SupplyRouteChoice('needs_mining_counter_observation',state,False,name,
        missing='00553da4 DWORD',mine_counter=mine_counter)
    # Shared verified algorithm; prefix observation belongs to568d24 here,
    # not the supply object's57c prefix used by the eventual route loader.
    proxy=SupplyRouteState(mine_counter,0)
    cyclic=plan_supply_route_selection(SupplyRouteLists(mine_names,(),True),'supply',proxy,observation)
    if not cyclic.complete:return SupplyRouteChoice(cyclic.status,state,False,name,cyclic,
        missing=cyclic.missing,mine_counter=cyclic.state.supply_counter)
    use=bool(cyclic.filename)
    return SupplyRouteChoice('mining_cyclic_route_choice' if use else 'mining_manual_fallback',state,True,
        cyclic.filename if use else name,cyclic,use,mine_counter=cyclic.state.supply_counter)
