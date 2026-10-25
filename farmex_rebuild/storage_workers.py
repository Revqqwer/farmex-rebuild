"""Richard0046f520 storage priority and004ff918/00470a94 outer workers.

Calls are local intents; eight item helpers support explicit nested observations.
Native metadata/slot readers and vtable action ABI remain unresolved. Advancing
a source counter does not mean an item was transferred successfully.
Optional typed Inn cleanup uses ordered guarded read operands and separate
count/close normal-return receipts; legacy raw helper fixtures remain separate.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from typing import Mapping,Optional,Tuple
from npc_sell_packets import raw
from npc_buy_packets import signed32
from storage_items import StorageItemObservation,plan_storage_item
from storage_inventory import StorageScanObservation,scan_storage
from storage_native_plans import NativeHelperObservation,plan_native_helper
from native_profile_versions import VersionedNativeObservation,plan_versioned_native
from merchant_bank_count import BankCountPlan
from source_inn_cleanup import InnCleanupObservation,plan_inn_cleanup

VIP_BASE=0x5690b8
INN_BASE=0x5690e0

@dataclass(frozen=True)
class StorageObservation:
    now_ms: int
    open_byte: Optional[int] = None
    busy_byte: Optional[int] = None
    secondary_open_byte: Optional[int] = None
    cleanup_open_byte: Optional[int] = None
    helpers: Mapping[str,int] = field(default_factory=dict)
    item_observations: Mapping[str,StorageItemObservation] = field(default_factory=dict)
    scan_observations: Mapping[str,StorageScanObservation] = field(default_factory=dict)
    native_observations: Mapping[str,object] = field(default_factory=dict)
    bank_count_execution: Optional[BankCountPlan] = None
    bank_count_returned: Optional[bool] = None
    cleanup_inputs: Optional[InnCleanupObservation] = None
    cleanup_close_returned: Optional[bool] = None

    def __post_init__(self):
        raw(self.now_ms)
        for value in (self.open_byte,self.busy_byte,self.secondary_open_byte,self.cleanup_open_byte):raw(value,255,optional=True)
        for value in self.helpers.values():raw(value)
        object.__setattr__(self,'helpers',MappingProxyType(dict(self.helpers)))
        if any(not isinstance(value,StorageItemObservation) for value in self.item_observations.values()):raise ValueError('Typed item helper observations required')
        object.__setattr__(self,'item_observations',MappingProxyType(dict(self.item_observations)))
        if any(not isinstance(value,StorageScanObservation) for value in self.scan_observations.values()):raise ValueError('Typed storage count scans required')
        object.__setattr__(self,'scan_observations',MappingProxyType(dict(self.scan_observations)))
        if any(not isinstance(value,NativeHelperObservation) and not (isinstance(value,VersionedNativeObservation) and value.kind=='storage') for value in self.native_observations.values()):raise ValueError('Typed native storage observations required')
        object.__setattr__(self,'native_observations',MappingProxyType(dict(self.native_observations)))
        if self.bank_count_execution is not None and not isinstance(self.bank_count_execution,BankCountPlan):raise ValueError('Typed bank count execution required')
        if self.bank_count_returned is not None and type(self.bank_count_returned) is not bool:raise ValueError('Separate bank count normal return required')
        if self.cleanup_inputs is not None and not isinstance(self.cleanup_inputs,InnCleanupObservation):raise ValueError('Typed Inn cleanup inputs required')
        if self.cleanup_close_returned is not None and type(self.cleanup_close_returned) is not bool:raise ValueError('Separate Inn close normal return required')

@dataclass(frozen=True)
class StorageCall:
    address: str
    arguments: Tuple[int,...] = ()

@dataclass(frozen=True)
class StorageResult:
    status: str
    globals: Mapping[int,int]
    worker: str = ''
    calls: Tuple[StorageCall,...] = ()
    missing: str = ''
    item_plans: Tuple[object,...] = ()
    scan_results: Tuple[object,...] = ()
    native_plans: Tuple[object,...] = ()
    bank_count_plans: Tuple[object,...] = ()
    cleanup_plans: Tuple[object,...] = ()

    def __post_init__(self):object.__setattr__(self,'globals',MappingProxyType(dict(self.globals)))

    def apply_to_npc(self,frame):
        from npc_route_engine import NpcRouteFrame
        if not isinstance(frame,NpcRouteFrame):raise ValueError('Typed NPC frame required')
        merged=dict(frame.globals);merged.update(self.globals)
        return replace(frame,globals=merged)

class _Missing(Exception):pass

def storage_worker_step(base,globals,observation):
    if base not in (VIP_BASE,INN_BASE):raise ValueError('Source worker base required')
    if not isinstance(observation,StorageObservation):raise ValueError('Typed source observations required')
    values=dict(globals);calls=[];plans=[];scans=[];native=[];counts=[];cleanups=[];name='VIP' if base==VIP_BASE else 'Inn'
    if any(type(k) is not int or type(v) is not int for k,v in values.items()):raise ValueError('Raw integer global fields required')
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def g(address):return need(values.get(address),'global%08x'%address)&0xffffffff
    def f(offset):return g(base+offset)
    def call(address,*args):
        calls.append(StorageCall(address,tuple(args)))
        if address in observation.native_observations:
            if address!='0046fdf8':raise ValueError('Outer native helper binding unavailable for this address')
            supplied=observation.native_observations[address]
            versioned=isinstance(supplied,VersionedNativeObservation)
            operand=supplied.observation if versioned else supplied
            if operand.helper!=address or operand.argument!=args[1]:raise ValueError('Native observation differs from source page call')
            wrapped=plan_versioned_native(supplied) if versioned else None
            plan=wrapped.plan if versioned else plan_native_helper(operand);native.append(wrapped if versioned else plan)
            if plan.status!='call_planned':raise _Missing('native:'+plan.status+':'+plan.missing)
            if (versioned or operand.operand_samples is not None) and operand.normal_returned is not True:
                raise _Missing('page helper normal return')
        if address in observation.item_observations:
            kinds={'004ff074':'vip_withdraw','00470584':'inn_deposit','00470124':'inn_withdraw',
                   '004ff600':'vip_deposit','004fed78':'vip_stock_withdraw','004fe5d8':'vip_ore_deposit',
                   '004fe828':'vip_ore_withdraw','004fea78':'vip_list_deposit'}
            if address not in kinds:raise ValueError('Item helper integration unavailable for this address')
            item=observation.item_observations[address]
            if item.kind!=kinds[address] or item.slot_index!=args[1]:raise ValueError('Item helper observation does not match source call')
            if address in ('004ff074','00470584','00470124') and item.selection.mode!=g(0x561f58):
                raise ValueError('Item helper mode differs from raw global mode')
            if address=='004ff074' and item.selection.strict_byte!=args[2]:raise ValueError('VIP selector BYTE differs from source argument')
            plan=plan_storage_item(base,item);plans.append(plan)
            calls.extend(StorageCall(row.address,row.arguments) for row in plan.calls)
            if plan.status=='needs_observation':raise _Missing('item:'+plan.reason)
    def helper(address,*args):
        call(address,*args)
        if address=='0046ff6c' and observation.bank_count_execution is not None:
            if address in observation.helpers or address in observation.scan_observations:raise ValueError('Bound bank count conflicts with raw helper or legacy scan')
            if observation.bank_count_returned is not True:raise _Missing('bank count helper normal return')
            count=observation.bank_count_execution;counts.append(count)
            if not count.complete:raise _Missing('bank count:'+count.missing)
            return need(count.count_dword,'bound bank count EAX')
        if address in observation.scan_observations:
            if address in observation.helpers:raise ValueError('Scan conflicts with separate helper return')
            kinds={'004fe3c4':'vip_full','004fe420':'bag_full','0046ff6c':'inn_free'}
            if address not in kinds:raise ValueError('Scan binding unavailable for this helper')
            scan=observation.scan_observations[address]
            if scan.kind!=kinds[address]:raise ValueError('Scan kind differs from helper call')
            if address=='004fe420' and scan.required_empty_count!=args[1]:raise ValueError('Empty threshold differs from source call')
            value=scan_storage(scan);scans.append(value)
            if value.status!='complete':raise _Missing('scan:'+value.missing)
            return value.returned_value
        return need(observation.helpers.get(address),address+' return')
    def result(status,missing=''):return StorageResult(status,values,name,tuple(calls),missing,tuple(plans),tuple(scans),tuple(native),tuple(counts),tuple(cleanups))
    def elapsed(lo,hi):
        start=(g(hi)<<32)|g(lo)
        delta=(observation.now_ms-start)&0xffffffffffffffff
        return delta-0x10000000000000000 if delta&0x8000000000000000 else delta
    def cleanup():
        if base==VIP_BASE:
            opened=need(observation.cleanup_open_byte,'fresh VIP cleanup byte')
            if opened==1:call('004fe21c',base)
            values.update({base+0x18:observation.now_ms,base+0x1c:0,base+8:0,base:0})
        else:
            if g(0x561f58)==4:values[0x569870]=1
            if f(0x14)==0:values[base+0x14]=helper('0046ff6c',base)
            if observation.cleanup_inputs is not None:
                if observation.cleanup_open_byte is not None:raise ValueError('Bound Inn cleanup conflicts with raw BYTE')
                cleanup=plan_inn_cleanup(observation.cleanup_inputs);cleanups.append(cleanup)
                if not cleanup.complete:raise _Missing('Inn cleanup:'+cleanup.missing)
                opened=cleanup.open_byte
            else:opened=need(observation.cleanup_open_byte,'fresh Inn cleanup byte')
            if opened==1:
                call('0046fd90',base)
                if observation.cleanup_inputs is not None and observation.cleanup_close_returned is not True:
                    raise _Missing('Inn close helper normal return')
            values.update({base:0,base+8:0})
        return result('finished_plan')
    try:
        enabled=g(0x561f60)&255
        if base==VIP_BASE:
            if not enabled or g(0x561f6f)&255 or signed32(helper('004611a0'))<=0:return cleanup()
            if need(observation.open_byte,'VIP open byte')!=1:
                if elapsed(0x56ffe0,0x56ffe4)<5000:return result('waiting_open')
                values.update({0x56ffe0:observation.now_ms,0x56ffe4:0})
                call('004fe1c4',base);return result('open_planned')
            if need(observation.busy_byte,'protected byte at global553ed8')!=0:return result('waiting_busy')
            mode=f(4)
            if mode in (1,4,6):
                full=helper('004fe3c4',base)&255
                limit=signed32(f(0xc))>27 if not full else True
                if limit:
                    if mode==4:
                        values.update({base+4:6,base+0xc:0});return result('mode_changed')
                    return cleanup()
                address={1:'004ff600',4:'004fe5d8',6:'004fea78'}[mode]
                call(address,base,f(0xc));values[base+0xc]=(f(0xc)+1)&0xffffffff
                return result('slot_planned')
            if mode in (2,3,5):
                full=helper('004fe420',base,2 if mode==5 else 0)&255
                limit=signed32(f(0x10))>47 if not full else True
                if limit:
                    if mode==5:
                        values.update({base+4:6,base+0xc:0});return result('mode_changed')
                    return cleanup()
                address={2:'004ff074',3:'004fed78',5:'004fe828'}[mode]
                args=(base,f(0x10),f(9)&255) if mode==2 else (base,f(0x10))
                call(address,*args);values[base+0x10]=(f(0x10)+1)&0xffffffff
                if mode in (2,5):values[base+0x14]=f(0x10)
                return result('slot_planned')
            return result('pending_unknown_mode')
        if enabled:
            if need(observation.open_byte,'Inn open byte')==1:
                if need(observation.busy_byte,'protected byte at global553ed8')!=0:return result('waiting_busy')
                mode=f(4)
                if mode==1:
                    if signed32(f(0xc))>27:
                        if g(0x568cfe)&255==0 or signed32(g(0x5690cc))>47:
                            values[base+4]=2;return result('mode_changed')
                        return cleanup()
                    call('00470584',base,f(0xc));values[base+0xc]=(f(0xc)+1)&0xffffffff
                    return result('slot_planned')
                if mode!=2:return result('pending_unknown_mode')
                if signed32(f(0x10))>191:return cleanup()
                call('00470124',base,f(0x10));values[base+0x10]=(f(0x10)+1)&0xffffffff
                index=signed32(f(0x10))
                if index!=192 and index%24==0:
                    call('0046fdf8',base,2);return result('page_planned')
                return result('slot_planned')
            if need(observation.secondary_open_byte,'secondary Inn byte')==1:
                values[base+0x14]=0;call('0046fc0c',base);return result('secondary_close_planned')
            if elapsed(0x553d40,0x553d44)<5000:return result('waiting_open')
            values.update({0x553d40:observation.now_ms,0x553d44:0})
            npc=g(0x568dac)
            if npc!=0:
                call('0046fb38',base,npc);return result('interaction_planned')
        return cleanup()
    except _Missing as exc:return result('needs_observation',str(exc))

def dispatch_storage_worker(globals,observation):
    """Storage portion of0046f520. Its later non-storage branch is not emulated."""
    for base,name in ((VIP_BASE,'VIP'),(INN_BASE,'Inn')):
        if base not in globals:return StorageResult('needs_observation',globals,missing='global%08x'%base)
        if globals[base]&255:return storage_worker_step(base,globals,observation)
    return StorageResult('inactive',globals)
