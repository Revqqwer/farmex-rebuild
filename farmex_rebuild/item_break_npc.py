"""Captured normal-path NPC selection and typed item-break caller composition.

FSTP binary32 captures and FNSTSW AX captures stay separate. Managed-string,
lookup, coordinate, distance and selection helper effects remain opaque.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from item_break_cycle import ItemBreakCycleObservation,_raw,_receipts
from item_break_inventory import ItemBreakInventoryCycleFrame,ItemBreakInventoryObservation

@dataclass(frozen=True)
class ItemBreakNpcObservation:
    entry_reached:bool=False
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit post-prologue NPC entry required')
        values=dict(self.values);normals=dict(self.normal_returns)
        for key,value in values.items():
            _raw(value,16 if key.endswith('_ax') else 32)
            if value is None:raise ValueError('Explicit reached NPC operand required')
        if any(type(v) is not bool for v in normals.values()):raise ValueError('Separate NPC helper normal receipts required')
        object.__setattr__(self,'values',MappingProxyType(values))
        object.__setattr__(self,'normal_returns',MappingProxyType(normals))

@dataclass(frozen=True)
class ItemBreakNpcPlan:
    complete:bool
    status:str
    calls:tuple=()
    reads:tuple=()
    stores:tuple=()
    needed:object=None
    result_eax:object=None
    next_address:object=None
    lookup_name:bytes=b''
    whole_function_verified:bool=False
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class _Wait(Exception):
    def __init__(self,kind,key):self.needed=(kind,key);super().__init__(key)

def _plan(o,context):
    calls=[];reads=[];stores=[];eax=None;name=b''
    def result(status,wait=None):
        return ItemBreakNpcPlan(wait is None,status,tuple(calls),tuple(reads),tuple(stores),
            None if wait is None else wait.needed,eax,0x470f5e if wait is None else None,name)
    def value(key):
        if key not in o.values:raise _Wait('value',key)
        return o.values[key]
    def read(key,address):
        reads.append((address&0xffffffff,4,key));return value(key)
    def normal(key,target,args=()):
        calls.append((target,args,key))
        if o.normal_returns.get(key) is not True:raise _Wait('normal',key)
    def fail(status):
        nonlocal eax
        eax=0
        normal('failure_cleanup','00403860',('owned_name_temporary',1,0))
        return result(status)
    try:
        if not o.entry_reached:raise _Wait('entry','00470da8')
        normal('empty_name_setup','00470da8..00470df8',(b'',))
        if read('mode_dword',context+0xc)==0:
            name=b'Moira';normal('moira_assignment','004038e4',(b'Moira',))
        normal('lookup_argument_setup','00470e12..00470e6e',('managed_argument_copy',))
        normal('npc_lookup','00465960',('opaque_managed_argument_from_setup',))
        npc=value('npc_id_eax')
        if npc==0:return fail('npc_id_zero')
        normal('npc_object','00464a10',(npc,))
        pointer=value('npc_object_eax')
        if pointer==0:return fail('npc_object_zero')
        offset=read('first_offset',0x554008)
        normal('first_coordinate','0045ddb8',((pointer+offset)&0xffffffff,))
        first=value('first_coordinate_float_bits')
        offset=read('second_offset',0x554010)
        normal('second_coordinate','0045ddb8',((pointer+offset)&0xffffffff,))
        second=value('second_coordinate_float_bits')
        normal('distance','00460548',(second,first))
        value('distance_float_bits') #FSTP32 capture; not an emulation of helper/x87 state.
        zero_ax=value('zero_compare_ax');reads.append(('FNSTSW_AX',16,'zero_compare_ax',zero_ax))
        if (zero_ax>>8)&5:return fail('distance_zero_compare_rejected')
        ten_ax=value('ten_compare_ax');reads.append(('FNSTSW_AX',16,'ten_compare_ax',ten_ax))
        if bin((ten_ax>>8)&0x41).count('1')%2==0:return fail('distance_ten_compare_rejected')
        normal('selected_npc','00462630')
        selected=value('selected_npc_eax')
        changed=selected!=npc
        if changed:normal('select_npc','0046493c',(pointer,))
        stores.append(((context+8)&0xffffffff,4,npc))
        # The selection callee may leave arbitrary upper EAX; only AL is set
        # by this caller. Record the store before requesting the return bits.
        eax=((value('select_npc_eax') if changed else selected)&0xffffff00)|1
        normal('success_cleanup','00403860',('owned_name_temporary',1,0))
        return result('selected_npc_changed' if changed else 'selected_npc_already_matches')
    except _Wait as wait:return result('needs_observation',wait)

class ItemBreakNpcFrame:
    def __init__(self,*,context=0x569a20):
        _raw(context,32)
        if context is None:raise ValueError('Explicit NPC context required')
        self.context=context;self.observation=ItemBreakNpcObservation();self.final=None
    def advance(self,incoming):
        if not isinstance(incoming,ItemBreakNpcObservation):raise ValueError('Typed NPC observations required')
        if self.final is not None:return self.final
        for _ in range(40):
            plan=_plan(self.observation,self.context)
            if plan.complete:self.final=plan;return plan
            kind,key=plan.needed
            if kind=='entry':
                if not incoming.entry_reached:return plan
                self.observation=replace(self.observation,entry_reached=True)
            elif kind=='normal':
                if incoming.normal_returns.get(key) is not True:return plan
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,key:True})
            else:
                if key not in incoming.values:return plan
                self.observation=replace(self.observation,values={**self.observation.values,key:incoming.values[key]})
        raise AssertionError('NPC reached capture budget exceeded')

@dataclass(frozen=True)
class ItemBreakNpcCyclePlan:
    complete:bool
    caller:object
    npc:object=None
    needed:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class ItemBreakNpcCycleFrame:
    def __init__(self,*,context=0x569a20):
        self.caller=ItemBreakInventoryCycleFrame(context=context);self.npc=ItemBreakNpcFrame(context=context)
        self.npc_result=None;self.parent_returned=False
    def advance(self,caller,npc=None,guard=None,*,guard_parent_returned=None,npc_parent_returned=None):
        if not isinstance(caller,ItemBreakCycleObservation):raise ValueError('Typed caller required')
        if caller.npc_returned is not None or caller.npc_eax is not None:raise ValueError('Typed NPC child owns parent-return and result binding')
        if npc is not None and not isinstance(npc,ItemBreakNpcObservation):raise ValueError('Typed NPC child required')
        if guard is not None and not isinstance(guard,ItemBreakInventoryObservation):raise ValueError('Typed inventory guard required')
        _receipts(npc_parent_returned)
        bound=replace(caller,npc_returned=True,npc_eax=self.npc_result.result_eax) if self.parent_returned else caller
        plan=self.caller.advance(bound,guard,guard_parent_returned=guard_parent_returned)
        if plan.needed=='npc_returned':
            self.npc_result=self.npc.advance(npc or ItemBreakNpcObservation())
            if not self.npc_result.complete:
                return ItemBreakNpcCyclePlan(False,plan,self.npc_result,('npc',self.npc_result.needed))
            if npc_parent_returned is not True:
                return ItemBreakNpcCyclePlan(False,plan,self.npc_result,'npc_parent_returned')
            self.parent_returned=True
            plan=self.caller.advance(replace(caller,npc_returned=True,npc_eax=self.npc_result.result_eax),
                guard,guard_parent_returned=guard_parent_returned)
        return ItemBreakNpcCyclePlan(plan.complete,plan,self.npc_result,plan.needed)
