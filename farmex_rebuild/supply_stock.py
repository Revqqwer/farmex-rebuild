"""004e74e8 list overlay ->004f38dc stock scan. No inventory or game IO.

Source catalog ordinals are not item IDs. Inventory observations are fresh per
enabled row and source slot14..41. Last matching slot wins, with signed quantity
comparison; quantities and desired totals are never summed by this trigger.
"""
import json,re
from pathlib import Path
from dataclasses import dataclass,replace
from collections.abc import Mapping
from types import MappingProxyType
from typing import Optional,Tuple
from npc_buy_engine import NpcBuyRouteRow
from npc_buy_packets import NpcBuyRecord

BUY_LIST_PATH='frmMain/MainTab/SheetTedarik/GroupBox17/BuyList'

def _raw(value,maximum=0xffffffff):
    if type(value) is not int or not 0<=value<=maximum:raise ValueError('Raw unsigned source field required')

@dataclass(frozen=True)
class SupplyCatalogRow:
    name:str
    item_id:int
    enabled:int=0
    desired:int=0
    source_fields:tuple=()

    def __post_init__(self):
        if type(self.name) is not str:raise ValueError('Source Unicode catalog name required')
        _raw(self.item_id);_raw(self.enabled,255);_raw(self.desired)

_CATALOG_DATA=json.loads(Path(__file__).with_name('supply_catalog.json').read_text(encoding='utf8'))
SOURCE_CATALOG=tuple(SupplyCatalogRow(e['name'],e['item_id'],source_fields=tuple(
    sorted((int(k),v) for k,v in e['fields'].items() if int(k) not in (4,28,32)))) for e in _CATALOG_DATA['entries'])

@dataclass(frozen=True)
class SupplyListConfiguration:
    status:str
    rows:Tuple[SupplyCatalogRow,...]
    complete:bool
    missing:str=''
    independently_verified:bool=False

@dataclass(frozen=True)
class SupplyBuyRowsPlan:
    status:str
    rows:Tuple[NpcBuyRouteRow,...]
    complete:bool
    missing:str=''

def plan_supply_buy_rows(configuration):
    """004efa84 catalog ->20-byte batch projection; no target/vendor guessing."""
    if not isinstance(configuration,SupplyListConfiguration):raise ValueError('Typed supply list required')
    if not configuration.complete:return SupplyBuyRowsPlan(configuration.status,(),False,configuration.missing)
    rows=[]
    for index,row in enumerate(configuration.rows):
        fields=dict(row.source_fields)
        if any(offset not in fields for offset in (8,12,16,20,24)):
            return SupplyBuyRowsPlan('needs_catalog_observation',tuple(rows),False,'row%d source fields8/c/10/14/18'%index)
        for value in fields.values():_raw(value)
        record=NpcBuyRecord(row.item_id,row.desired&0xffff,fields[8]&255,fields[12]&255,fields[20],fields[24])
        rows.append(NpcBuyRouteRow(row.enabled,fields[16],record))
    return SupplyBuyRowsPlan('local_buy_rows_plan',tuple(rows),True)

def compile_supply_list(lists,*,catalog=SOURCE_CATALOG):
    if not isinstance(lists,Mapping) or BUY_LIST_PATH not in lists:raise ValueError('Explicit BuyList profile required')
    if type(catalog) is not tuple or any(not isinstance(r,SupplyCatalogRow) for r in catalog):
        raise ValueError('Typed source catalog tuple required')
    # Source first resets the entire catalog, including previously enabled rows.
    rows=[replace(r,enabled=0,desired=0) for r in catalog]
    profile_rows=lists[BUY_LIST_PATH]
    if not isinstance(profile_rows,(list,tuple)):raise ValueError('BuyList rows required')
    def decimal(text):
        if type(text) is not str or not re.fullmatch(r'[+-]?[0-9]+',text.strip()):raise ValueError('Decimal signed32 list field required')
        value=int(text.strip())
        if not -(1<<31)<=value<(1<<31):raise ValueError('Signed32 list field required')
        return value
    for row_no,row in enumerate(profile_rows):
        if not isinstance(row,Mapping) or not isinstance(row.get('subitems'),(tuple,list)) or len(row['subitems'])<2:
            raise ValueError('BuyList quantity/index subitems required')
        index=decimal(row['subitems'][1]);quantity=decimal(row['subitems'][0])
        if not 0<=index<len(rows):
            return SupplyListConfiguration('unresolved_source_index',tuple(rows),False,
                'row%d index%d outside observed catalog; source has no bounds check'%(row_no,index))
        rows[index]=replace(rows[index],enabled=1,desired=quantity&0xffffffff)
    return SupplyListConfiguration('compiled_buy_list',tuple(rows),True)

@dataclass(frozen=True)
class SupplyStockObservation:
    item_ids:Mapping
    quantities:Mapping

    def __post_init__(self):
        for mapping in (self.item_ids,self.quantities):
            if not isinstance(mapping,Mapping):raise ValueError('Per-row/slot observations required')
            for key,value in mapping.items():
                if type(key) is not tuple or len(key)!=2 or type(key[0]) is not int or key[0]<0 or type(key[1]) is not int or not 14<=key[1]<=41:
                    raise ValueError('Explicit catalog row and source slot14..41 required')
                if value is not None:_raw(value)
        object.__setattr__(self,'item_ids',MappingProxyType(dict(self.item_ids)))
        object.__setattr__(self,'quantities',MappingProxyType(dict(self.quantities)))

@dataclass(frozen=True)
class SupplyStockDecision:
    status:str
    due:Optional[bool]
    row_index:Optional[int]=None
    matched_slot:Optional[int]=None
    calls:tuple=()
    missing:str=''
    independently_verified:bool=False

def plan_supply_stock(configuration,observation):
    if not isinstance(configuration,SupplyListConfiguration) or not isinstance(observation,SupplyStockObservation):
        raise ValueError('Typed supply list and stock observations required')
    if not configuration.complete:return SupplyStockDecision(configuration.status,None,missing=configuration.missing)
    calls=[]
    for row_index,row in enumerate(configuration.rows):
        if not row.enabled:continue
        matched=None
        for slot in range(14,42):
            calls.append(('004634a4',row_index,slot))
            item=observation.item_ids.get((row_index,slot))
            if item is None:return SupplyStockDecision('needs_inventory_observation',None,row_index,matched,tuple(calls),
                'row%d slot%d itemID'%(row_index,slot))
            if item==row.item_id:matched=slot
        if matched is None:return SupplyStockDecision('stock_item_absent',True,row_index,None,tuple(calls))
        calls.append(('00463538',row_index,matched))
        quantity=observation.quantities.get((row_index,matched))
        if quantity is None:return SupplyStockDecision('needs_inventory_observation',None,row_index,matched,tuple(calls),
            'row%d slot%d quantity'%(row_index,matched))
        signed=quantity-(0x100000000 if quantity&0x80000000 else 0)
        # Exact source name comparison; desired total has no role here.
        arrow=row.name.encode('utf-16-le','surrogatepass')==b'A\0r\0r\0o\0w\0'
        if signed<=(10 if arrow else 2):
            return SupplyStockDecision('stock_quantity_low',True,row_index,matched,tuple(calls))
    return SupplyStockDecision('stock_sufficient',False,calls=tuple(calls))
