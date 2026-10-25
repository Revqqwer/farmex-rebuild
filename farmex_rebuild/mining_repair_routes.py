"""0047a61c region route vectors -> recovered constructor catalog -> local steps.

This is logical row reconstruction, not a1220-byte native pointer blob. NPC's
unrecovered second field stays None in rows; local NPC adapter ignores it,
matching the004f3704 parameter1-only copy into route+608.
"""
from dataclasses import dataclass
from mining_engine import load_mining_routes,route_records
from routes import RouteStep

REPAIR_ROUTES={1:('EMC',0x4c4,'EMCMiningRoute2',(0x5fa0,0x5fa4)),
               2:('Luferson',0x3df4,'LFCMiningRoute2',(0x5fa8,0x5fac)),
               3:('Moradon',0x2ae4,'MoradonMiningRoute2',(0x5f98,0x5f9c))}

@dataclass(frozen=True)
class MiningRepairRoutePlan:
    status:str
    complete:bool
    branch:int
    region:str
    source_offset:int
    name:str
    coordinate_fields:tuple
    rows:tuple=()
    steps:tuple=()
    unknown_unused_second_fields:tuple=()
    missing:str=''
    native_pointer_blob_reconstructed:bool=False
    independently_verified:bool=False
    constructor_defaults_assumed:bool=True

def load_mining_repair_route(branch,catalog=None):
    if type(branch) is not int or branch not in REPAIR_ROUTES:raise ValueError('Source region branch1/2/3 required')
    region,offset,name,coords=REPAIR_ROUTES[branch]
    return project_mining_constructor_route(name,region,offset,coords,branch,catalog)

def project_mining_constructor_route(name,region,offset,coords,branch,catalog=None):
    """Shared logical projection of source constructor records, never pointers."""
    rows=[];steps=[];unused=[]
    def result(status,complete,missing=''):
        return MiningRepairRoutePlan(status,complete,branch,region,offset,name,coords,
                                     tuple(rows),tuple(steps),tuple(unused),missing)
    catalog=load_mining_routes() if catalog is None else catalog
    if name not in catalog:return result('needs_route_catalog',False,name)
    entry=catalog[name]
    if entry.get('slot_offset')!=hex(offset) or entry.get('purpose_literal')!='Mine':
        return result('route_catalog_binding_mismatch',False,'source offset/purpose')
    try:records=route_records(name,catalog)
    except ValueError as exc:return result('incomplete_source_route',False,str(exc))
    for record in records:
        command,p1,p2=(record.get(key) for key in ('command','parameter_1_text','parameter_2_text'))
        rows.append((command,p1,p2))
        if command=='Koordinat':
            if type(p1) is not str or type(p2) is not str or not p1.isascii() or not p2.isascii() or not p1.isdigit() or not p2.isdigit():
                return result('unresolved_coordinate_literal',False,'row%d'%record['index'])
            steps.append(RouteStep(command,x=float(int(p1)),y=float(int(p2))))
        elif command=='NPC' and type(p1) is str:
            if p2 is None:unused.append(record['index'])
            # Explicit local projection: parameter2 is not consumed by NPC.
            steps.append(RouteStep(command,parameter1=p1,parameter2=''))
        elif command=='Town':
            if p2 is None:unused.append(record['index'])
            steps.append(RouteStep(command,parameter1='',parameter2=''))
        else:return result('unresolved_repair_route_command',False,'row%d'%record['index'])
    return result('logical_repair_route_ready',True)
