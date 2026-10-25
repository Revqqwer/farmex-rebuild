"""Richard eight VIP/Inn item helper decisions, native calls only planned.

Metadata and fresh dialog bytes are observations; no vtable ABI is guessed.
The helper's AL return is not a server acknowledgement.
"""
from dataclasses import dataclass
from typing import Optional,Tuple
from npc_sell_filter import SellFilterObservation
from npc_sell_packets import raw
from npc_buy_packets import signed32
from storage_inventory import StorageScanObservation,scan_storage
from storage_native_plans import NativeHelperObservation,plan_native_helper,SLOTS
from native_profile_versions import VersionedNativeObservation,plan_versioned_native

KINDS=('vip_withdraw','inn_deposit','inn_withdraw','vip_deposit','vip_stock_withdraw',
       'vip_ore_deposit','vip_ore_withdraw','vip_list_deposit')

@dataclass(frozen=True)
class StorageSelection(SellFilterObservation):
    strict_byte: int = 0
    list_checked_e2: Optional[bool] = None
    mode2_checked4: Optional[bool] = None
    mode4_name_match: Optional[bool] = None
    mode4_index: Optional[int] = None
    row_e1_byte: Optional[int] = None
    row_e2_byte: Optional[int] = None
    ore_gold_match: Optional[bool] = None
    ore_match: Optional[bool] = None

    def __post_init__(self):
        super().__post_init__();raw(self.strict_byte,255)
        for value in (self.list_checked_e2,self.mode2_checked4,self.mode4_name_match,self.ore_gold_match,self.ore_match):
            if value is not None and type(value) is not bool:raise ValueError('Boolean source observation required')
        if self.mode4_index is not None and (type(self.mode4_index) is not int or not -0x80000000<=self.mode4_index<0x80000000):
            raise ValueError('Signed mode4 lookup index required')
        for value in (self.row_e1_byte,self.row_e2_byte):raw(value,255,optional=True)

@dataclass(frozen=True)
class StorageItemObservation:
    kind: str
    slot_index: int
    selection: StorageSelection
    item_pointer: Optional[int] = None
    open_byte: Optional[int] = None
    available_quantity: Optional[int] = None
    desired_quantity: Optional[int] = None
    existing_quantity: Optional[int] = None
    dialog_bytes: Tuple[Optional[int],Optional[int],Optional[int]] = (None,None,None)
    capacity_full_byte: Optional[int] = None
    inventory_observation: Optional[StorageScanObservation] = None
    source_item_id: Optional[int] = None
    capacity_observation: Optional[StorageScanObservation] = None
    native_observations: Tuple[object,...] = ()

    def __post_init__(self):
        if self.kind not in KINDS or not isinstance(self.selection,StorageSelection):raise ValueError('Typed storage item selection required')
        raw(self.slot_index);raw(self.item_pointer,optional=True);raw(self.open_byte,255,optional=True)
        for value in (self.available_quantity,self.desired_quantity,self.existing_quantity):raw(value,optional=True)
        if len(self.dialog_bytes)!=3:raise ValueError('Three successive source dialog byte observations required')
        for value in self.dialog_bytes:raw(value,255,optional=True)
        raw(self.capacity_full_byte,255,optional=True)
        raw(self.source_item_id,optional=True)
        for value in (self.inventory_observation,self.capacity_observation):
            if value is not None and not isinstance(value,StorageScanObservation):raise ValueError('Typed inventory scan required')
        if any(not isinstance(value,NativeHelperObservation) and not (isinstance(value,VersionedNativeObservation) and value.kind=='storage') for value in self.native_observations):raise ValueError('Typed ordered native storage observations required')
        object.__setattr__(self,'native_observations',tuple(self.native_observations))
        object.__setattr__(self,'dialog_bytes',tuple(self.dialog_bytes))

@dataclass(frozen=True)
class StorageItemCall:
    address: str
    arguments: Tuple[int,...] = ()

@dataclass(frozen=True)
class StorageItemResult:
    status: str
    returned_value: Optional[int] = None
    quantity: Optional[int] = None
    calls: Tuple[StorageItemCall,...] = ()
    reason: str = ''
    inventory_results: Tuple[object,...] = ()
    native_plans: Tuple[object,...] = ()

class _Missing(Exception):pass

def plan_storage_item(base,observation):
    raw(base)
    if not isinstance(observation,StorageItemObservation):raise ValueError('Typed item observations required')
    obs=observation;s=obs.selection;calls=[];scans=[];native=[];quantity=None;binding_identity=[]
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def call(address,*args):
        calls.append(StorageItemCall(address,tuple(args)))
        if obs.native_observations and address in tuple(SLOTS)+('004653a8','00465334'):
            index=len(native)
            if index>=len(obs.native_observations):raise _Missing('native helper observation%d'%index)
            supplied=obs.native_observations[index];argument=args[1] if address in SLOTS else args[0]
            versioned=isinstance(supplied,VersionedNativeObservation)
            operand=supplied.observation if versioned else supplied
            if operand.helper!=address or operand.argument!=argument:raise ValueError('Native observation differs from source helper call/argument')
            identity=(supplied.module_sha256,supplied.profile) if versioned else ('unversioned',)
            if binding_identity and binding_identity[0]!=identity:raise ValueError('Reached native storage observations mix source identities')
            binding_identity[:]=[identity]
            wrapped=plan_versioned_native(supplied) if versioned else None
            plan=wrapped.plan if versioned else plan_native_helper(operand);native.append(wrapped if versioned else plan)
            if plan.status not in ('call_planned','writes_planned','no_call'):
                raise _Missing('native:'+plan.status+':'+plan.missing)
            if (versioned or operand.operand_samples is not None) and operand.normal_returned is not True:
                raise _Missing('native helper normal return%d'%index)
    def result(status,returned=None,reason=''):return StorageItemResult(status,returned,quantity,tuple(calls),reason,tuple(scans),tuple(native))
    def observed_scan(scan):
        value=scan_storage(scan);scans.append(value)
        if value.status!='complete':raise _Missing('inventory:'+value.missing)
        return value.returned_value
    def existing_count(kind):
        if obs.inventory_observation is None:return need(obs.existing_quantity,'existing item quantity DWORD')
        if obs.existing_quantity is not None:raise ValueError('Choose scalar existing quantity or inventory scan')
        scan=obs.inventory_observation
        if scan.kind!=kind:raise ValueError('Inventory kind differs from source count helper')
        if need(scan.target_item_id,'inventory target item ID')!=need(obs.source_item_id,'source item ID for scan binding'):
            raise ValueError('Inventory target differs from source item ID')
        return observed_scan(scan)
    def skip(reason):return result('skip',0,reason)
    def protected():
        if not need(s.protect_grade_5622cf,'grade protection byte'):return False
        minimum=need(s.minimum_grade_5622d0,'minimum grade DWORD')
        grade=need(s.extension_id,'extension ID DWORD')%10
        return grade>=minimum and need(s.type_byte,'metadata type BYTE')!=3
    def normal_list(strict):
        call('0041a5cc')
        if need(s.list_index_41a5cc,'0041a5cc index')<1:return False
        return need(s.list_checked_5622e1 if strict else s.list_checked_e2,'checked row+e1' if strict else 'checked row+e2')
    def mode2_list(strict):
        call('0047677c')
        if need(s.mode2_index_47677c,'0047677c index')<0:return False
        return need(s.mode2_checked if strict else s.mode2_checked4,'mode2 row+6' if strict else 'mode2 row+4')
    try:
        if obs.kind=='inn_withdraw' and s.mode==2:return skip('mode2 source early exit')
        if obs.kind=='vip_deposit':
            call('004fe3c4',base)
            capacity=obs.capacity_full_byte
            if obs.capacity_observation is not None:
                if capacity is not None:raise ValueError('Choose scalar capacity or fresh inventory scan')
                if obs.capacity_observation.kind!='vip_full':raise ValueError('VIP capacity scan required')
                capacity=observed_scan(obs.capacity_observation)
            if need(capacity,'fresh item helper VIP full BYTE')!=0:return skip('VIP capacity full')
        if obs.kind=='inn_deposit' and need(obs.open_byte,'item helper Inn open BYTE')==0:return skip('Inn byte zero')
        if need(obs.item_pointer,'observed item pointer')==0:return skip('empty source slot')
        if obs.kind not in ('vip_withdraw','vip_deposit','inn_deposit'):
            if need(obs.open_byte,'item helper open BYTE')==0:return skip('helper open byte zero')
        if obs.kind in ('vip_ore_deposit','vip_ore_withdraw'):
            call('00505d20:Mysterious gold mine')
            matched=need(s.ore_gold_match,'gold mine name comparison')
            if not matched:
                call('00505d20:Mysterious Ore');matched=need(s.ore_match,'ore name comparison')
            if not matched:return skip('neither ore name matched')
            call('004fe2fc' if obs.kind=='vip_ore_deposit' else '004fe274',base,obs.slot_index)
            return result('native_calls_planned',1)
        if obs.kind=='vip_withdraw':
            call('004e7c60')
            if need(s.excluded_4e7c60,'004e7c60 excluded'):return skip('excluded')
            if s.mode==0:
                protect=protected()
                if s.strict_byte:
                    if protect:return skip('protected grade in strict branch')
                    if not normal_list(True):return skip('strict normal row unselected')
                elif not protect and not normal_list(False):return skip('normal row unselected')
            elif s.mode==2 and not mode2_list(s.strict_byte!=0):return skip('mode2 row unselected')
            quantity=need(obs.available_quantity,'available quantity DWORD')
            call('004fe274',base,obs.slot_index)
        elif obs.kind=='vip_deposit':
            call('004e7c60')
            if need(s.excluded_4e7c60,'004e7c60 excluded'):return skip('excluded')
            call('0041a5cc')
            if need(s.list_index_41a5cc,'0041a5cc index')<1:return skip('normal row absent')
            selected=need(s.row_e2_byte,'row+e2 raw BYTE')==1
            if not selected:selected=need(s.row_e1_byte,'row+e1 raw BYTE')==1
            if not selected:return result('no_native_call',1,reason='source returns1 for present but unchecked row')
            quantity=need(obs.available_quantity,'available quantity DWORD')
            call('004fe2fc',base,obs.slot_index)
        elif obs.kind=='vip_list_deposit':
            call('0047677c')
            if need(s.mode2_index_47677c,'0047677c index')==-1:return skip('mode2 row absent exact-1')
            selected=need(s.mode2_checked4,'mode2 row+4')
            if not selected:selected=need(s.mode2_checked,'mode2 row+6')
            if not selected:return skip('both mode2 columns unchecked')
            quantity=need(obs.available_quantity,'available quantity DWORD')
            call('004fe2fc',base,obs.slot_index)
        elif obs.kind=='vip_stock_withdraw':
            call('004e7be8')
            if need(s.excluded_index_4e7be8,'004e7be8 index')==-1:return skip('desired stock row absent')
            desired=need(obs.desired_quantity,'desired total DWORD')
            call('004fe4a0');existing=existing_count('vip_existing')
            quantity=(desired-existing)&0xffffffff
            if signed32(quantity)<=0:return skip('no positive signed stock deficit')
            quantity=min(quantity,need(obs.available_quantity,'available quantity DWORD'))
            call('004fe274',base,obs.slot_index)
        elif obs.kind=='inn_deposit':
            if s.mode==0:
                call('004e7c60')
                if need(s.excluded_4e7c60,'004e7c60 excluded'):return skip('excluded')
                call('004e7be8')
                if need(s.excluded_index_4e7be8,'004e7be8 index')!=-1:return skip('requested-stock row present')
                if not protected() and not normal_list(False):return skip('normal row unselected')
            elif s.mode==2:
                if not mode2_list(False):return skip('mode2 row unselected')
            elif s.mode==4:
                call('00505d20:mode4-name')
                if not need(s.mode4_name_match,'mode4 name comparison'):return skip('mode4 name mismatch')
                call('0041e148')
                if need(s.mode4_index,'0041e148 index')==-1:return skip('mode4 row absent')
            else:return skip('unsupported deposit mode')
            quantity=need(obs.available_quantity,'available quantity DWORD')
            call('0046fc78',base,obs.slot_index)
        else:
            quantity=0
            if s.mode in (0,4):
                if s.mode==0:
                    call('004e7be8');index=need(s.excluded_index_4e7be8,'004e7be8 index')
                else:
                    call('00505d20:mode4-name')
                    if not need(s.mode4_name_match,'mode4 name comparison'):return skip('mode4 name mismatch')
                    call('0041e0d4');index=need(s.mode4_index,'0041e0d4 index')
                if index==-1:return skip('desired stock row absent')
                desired=need(obs.desired_quantity,'desired total DWORD')
                call('0046ffa4')
                existing=existing_count('inn_existing')
                quantity=(desired-existing)&0xffffffff
                if signed32(quantity)<1:return skip('no positive signed quantity deficit')
                quantity=min(quantity,need(obs.available_quantity,'available quantity DWORD'))
            call('0046fd04',base,obs.slot_index)
        for index in range(3):
            opened=need(obs.dialog_bytes[index],'fresh quantity-dialog byte%d'%(index+1))
            if opened!=1:continue
            if index==2:
                call('00465334',0)
                if obs.kind in ('inn_withdraw','vip_stock_withdraw','vip_list_deposit'):return result('dialog_remaining',0)
            else:
                amount=quantity
                if index==1:
                    if obs.kind in ('inn_withdraw','vip_stock_withdraw'):
                        value=signed32(quantity);amount=(abs(value)//2*(-1 if value<0 else 1))&0xffffffff
                    else:amount=quantity>>1
                call('004653a8',amount);call('00465334',1)
        return result('native_calls_planned',1)
    except _Missing as exc:return result('needs_observation',reason=str(exc))
