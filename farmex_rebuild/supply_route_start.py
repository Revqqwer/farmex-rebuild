"""004ebca0 Supply/Return filename choice and bounded local import bridge.

Other filename branches live in global_route_choices. Full native phase writes,
bot stop/dialog and movement are not executed. Missing observations expose a
prospective source prefix only.
"""
from dataclasses import dataclass
from typing import Optional
from supply_configuration import SupplyPanelConfiguration
from supply_routes import (SupplyRouteLists,SupplyRouteState,SupplyRouteObservation,
    SupplyRouteDecision,plan_supply_route_selection)
from source_route_ini import SourceRouteImport,SourceRouteLoad,import_source_route
from name_codec import WindowsNameCodec

@dataclass(frozen=True)
class SupplyRouteChoice:
    status:str
    state:SupplyRouteState
    complete:bool
    filename:Optional[bytes]=None
    cyclic:Optional[SupplyRouteDecision]=None
    used_cyclic:bool=False
    missing:str=''
    independently_verified:bool=False
    mine_counter:Optional[int]=None

def plan_panel_route_choice(panel,lists,kind,state,manual_encoded=None,observation=SupplyRouteObservation()):
    if not isinstance(panel,SupplyPanelConfiguration) or not isinstance(lists,SupplyRouteLists) or not isinstance(state,SupplyRouteState) or kind not in ('supply','return'):
        raise ValueError('Typed panel/lists/counters and explicit Supply/Return kind required')
    # The source converts manual Unicode filename before checking change flag,
    # even when a nonempty cyclic result will eventually replace it.
    if manual_encoded is None:
        return SupplyRouteChoice('needs_manual_conversion',state,False,missing='004073a0 field+580/584 Unicode->ANSI')
    if type(manual_encoded) is not bytes:raise ValueError('Explicit immutable manual filename bytes required')
    flag=panel.fields[0x588 if kind=='supply' else 0x589]
    if not flag:return SupplyRouteChoice('manual_route_choice',state,True,manual_encoded)
    cyclic=plan_supply_route_selection(lists,kind,state,observation)
    if not cyclic.complete:
        return SupplyRouteChoice(cyclic.status,cyclic.state,False,manual_encoded,cyclic,missing=cyclic.missing)
    # Source00505138 is NEQ, not EQ; only nonempty cyclic names override.
    use=bool(cyclic.filename)
    return SupplyRouteChoice('cyclic_route_choice' if use else 'manual_route_fallback',cyclic.state,True,
        cyclic.filename if use else manual_encoded,cyclic,use)

@dataclass(frozen=True)
class SupplyRouteStart:
    status:str
    choice:SupplyRouteChoice
    imported:Optional[SourceRouteImport]=None
    ready:bool=False
    stop_required:bool=False
    complete:bool=False
    missing:str=''
    independently_verified:bool=False

def import_panel_route_choice(choice,prefix,codec,*,max_rows=10000):
    if not isinstance(choice,SupplyRouteChoice) or type(prefix) is not bytes or not isinstance(codec,WindowsNameCodec):
        raise ValueError('Typed choice, ANSI prefix and explicit local codec required')
    if not choice.complete:return SupplyRouteStart(choice.status,choice,missing=choice.missing)
    if not choice.filename:return SupplyRouteStart('source_route_unselected',choice,stop_required=True,complete=True)
    imported=import_source_route(codec.decode(prefix+choice.filename),codec,max_rows=max_rows)
    if imported.load.status in ('file_missing_preserve','nonpositive_count_preserve'):
        #004ebca0 execution differs from004e9854 editor's preserve behavior.
        return SupplyRouteStart('source_route_load_error',choice,imported,stop_required=True,complete=True)
    if not imported.complete:return SupplyRouteStart(imported.status,choice,imported,missing=imported.missing)
    return SupplyRouteStart('local_route_ready',choice,imported,ready=True,complete=True)
