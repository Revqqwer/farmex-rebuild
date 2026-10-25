"""00477bd4 auto-sell/bank return selection. Pure plans, no route/native IO.

Both candidate helper AL results precede mode selection. Distance inputs are
observed signed __ftol DWORDs and raw FPU AH, not a guessed game geometry model.
Constructor route defaults require explicit opt-in; EMC route4 stays incomplete.
"""
from dataclasses import dataclass
from typing import Optional
from collections.abc import Mapping
from mining_configuration import MiningPanelConfiguration
from mining_repair_routes import MiningRepairRoutePlan,project_mining_constructor_route
from mining_engine import load_mining_routes

@dataclass(frozen=True)
class MiningReturnPlan:
    status:str
    complete:bool
    selector:int=0
    family:str=''
    calls:tuple=()
    route:Optional[MiningRepairRoutePlan]=None
    missing:str=''
    native_execution_verified:bool=False
    server_acknowledged:bool=False

class _Missing(Exception):pass

def plan_mining_return(configuration,observations,catalog=None):
    if not isinstance(configuration,MiningPanelConfiguration) or not isinstance(observations,Mapping):raise ValueError('Typed config and observations required')
    selector=0;family='';calls=[];route=None
    def need(key,bits=32):
        value=observations.get(key)
        if value is None:raise _Missing(key)
        if type(value) is not int or not 0<=value<(1<<bits):raise ValueError('Raw observation required: '+key)
        return value
    def field(offset,bits=8):
        value=configuration.fields.get(offset)
        if value is None:raise _Missing('panel+%x'%offset)
        if type(value) is not int or not 0<=value<(1<<bits):raise ValueError('Raw panel field required')
        return value
    def call(address,*args):
        calls.append((address,args));key='returned:'+address;value=observations.get(key)
        if value is not None and type(value) is not bool:raise ValueError('Explicit normal return required')
        if value is not True:raise _Missing(key)
    def done(status):return MiningReturnPlan(status,True,selector,family,tuple(calls),route)
    def signed(raw):return raw-0x100000000 if raw&0x80000000 else raw
    try:
        sell=need('sell_476c7c',8)!=0;bank=need('bank_476d44',8)!=0
        if field(0x5ff8,32)==3:
            call('004ebca0',0x5687a8,('literal',0x5292b0))
            # Source continues through zone/distance/town even with selector0.
        elif not sell and not bank:selector=4
        else:
            auto_sell=field(0x6044)!=0
            if auto_sell:
                if field(0x6045)!=0:selector=1 if sell and bank else 2 if sell else 3
                elif sell:selector=2
            elif field(0x6045)!=0 and bank:selector=3
        region=0
        for index in range(1,4):
            if need('region_'+str(index)+'_equal',8)!=0:region=index;break
        if not region:return done('no_region_match')
        if region in (1,2):
            first=signed(need('distance_first_ftol'));second=signed(need('distance_second_ftol'))
            use_r=second<first
            family=('EMCRMiningRoute' if use_r else 'EMCMiningRoute') if region==1 else ('LFCRMiningRoute' if use_r else 'LFCMiningRoute')
            group=(4 if use_r else 0) if region==1 else (16 if use_r else 12)
        else:family='MoradonMiningRoute';group=8
        if need('distance_fpu_ah',8)&0x45==0:call('00465678')
        if selector==0:return done('no_builtin_route_selected')
        if need('use_constructor_defaults',8)==0:raise _Missing('fresh_return_route_vector')
        name=family+str(selector);offset=(group+selector-1)*0x4c4
        coords={1:(0x5fa0,0x5fa4),2:(0x5fa8,0x5fac),3:(0x5f98,0x5f9c)}[region]
        route=project_mining_constructor_route(name,{1:'EMC',2:'Luferson',3:'Moradon'}[region],offset,coords,region,catalog)
        if not route.complete:raise _Missing(route.missing)
        call('004eb9f4',0x5687a8,route)
        return done('return_route_planned')
    except _Missing as exc:
        return MiningReturnPlan('needs_observation',False,selector,family,tuple(calls),route,str(exc))
