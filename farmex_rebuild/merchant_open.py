"""42086c BUY opening buffer/write/queue plans. Never performs game writes.

Source protected-zero helper normal return is not proof that its write worked.
Partial native effects are described, not executed or rolled back by this model.
"""
from dataclasses import dataclass,field,replace
from collections.abc import Mapping
from types import MappingProxyType
from merchant_preparation import BuyPreparedRecord
from merchant_setup import MerchantInventoryObservation,plan_merchant_inventory
from action_queue import QueueState,QueueSample,enqueue

PREFIX=bytes.fromhex('6821')

def _raw(value,bits=32):
    if value is not None and (type(value) is not int or not 0<=value<1<<bits):
        raise ValueError('Raw %dbit observation required'%bits)

@dataclass(frozen=True)
class BuyOpenState:
    accumulated_qword:int=0
    def __post_init__(self):
        _raw(self.accumulated_qword,64)
        if self.accumulated_qword is None:raise ValueError('Explicit own accumulator required')

@dataclass(frozen=True)
class BuyOpenObservation:
    initial_global_base:object=None
    free_count:object=None
    inventory_inputs:object=None
    coins_dword:object=None
    records:tuple=()
    stable_records:bool=False
    vector_counts:tuple=()
    fresh_global_bases:Mapping=field(default_factory=dict)
    zero_helper_returns:Mapping=field(default_factory=dict)
    memset_returns:Mapping=field(default_factory=dict)
    def __post_init__(self):
        for value in (self.initial_global_base,self.free_count,self.coins_dword):_raw(value)
        if self.free_count is not None and self.free_count>28:raise ValueError('Free count exceeds28')
        if self.inventory_inputs is not None and not isinstance(self.inventory_inputs,MerchantInventoryObservation):
            raise ValueError('Typed fresh inventory required')
        if type(self.records) is not tuple or any(row is not None and not isinstance(row,BuyPreparedRecord) for row in self.records):
            raise ValueError('Immutable prepared records required')
        if type(self.stable_records) is not bool or type(self.vector_counts) is not tuple:
            raise ValueError('Explicit stability flag and fresh count tuple required')
        for count in self.vector_counts:_raw(count)
        if self.stable_records and self.vector_counts:raise ValueError('Stable/fresh vector counts conflict')
        for name in ('fresh_global_bases','zero_helper_returns','memset_returns'):
            values=getattr(self,name)
            if not isinstance(values,Mapping):raise ValueError('Indexed source observations required')
            values=dict(values)
            for index,value in values.items():
                _raw(index)
                if index is None:raise ValueError('Explicit selected-row ordinal required')
                if name=='fresh_global_bases':_raw(value)
                elif value is not None and type(value) is not bool:raise ValueError('Normal-return observation required')
            object.__setattr__(self,name,MappingProxyType(values))

@dataclass(frozen=True)
class BuyOpenPlan:
    complete:bool
    state:BuyOpenState
    prospective_state:BuyOpenState
    packets:tuple=()
    partial_payload:bytes=b''
    selected_indices:tuple=()
    calls:tuple=()
    write_plans:tuple=()
    remaining_coins:object=None
    remaining_free:object=None
    missing:str=''
    inventory_plan:object=None
    independently_verified:bool=False

def plan_buy_open(state,observation):
    if not isinstance(state,BuyOpenState) or not isinstance(observation,BuyOpenObservation):
        raise ValueError('Typed BUY opening state and observations required')
    o=observation;candidate=state;calls=[];writes=[];selected=[];payload=bytearray();coins=None;free=None;inventory=None
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def normal(value,label):
        if value is not True:raise Missing(label+' normal return')
    def output(complete,missing=''):
        packets=()
        if complete and selected:
            payload[2]=len(selected)
            packets=((PREFIX,0),(bytes(payload),1000))
        return BuyOpenPlan(complete,candidate if complete else state,candidate,packets,bytes(payload),tuple(selected),
                           tuple(calls),tuple(writes),coins,free,missing,inventory)
    try:
        base=need(o.initial_global_base,'initial value(global553f4c)')
        calls.append(('0042070c',))
        if o.free_count is not None and o.inventory_inputs is not None:raise ValueError('Free result and bound inventory conflict')
        if o.inventory_inputs is not None:
            inventory=plan_merchant_inventory(o.inventory_inputs)
            if not inventory.complete:raise Missing(inventory.missing)
            free=inventory.free_count
        else:free=need(o.free_count,'fresh free-count EAX')
        calls.append(('0046258c',));coins=need(o.coins_dword,'fresh coins EAX')
        payload.extend(b'\x68\x22\x00')
        calls.extend((('0041d42b',0x68),('0041d42b',0x22),('0041d42b',0)))
        index=0
        while True:
            if o.stable_records:count=len(o.records)
            else:count=need(o.vector_counts[index] if index<len(o.vector_counts) else None,
                           'fresh vector count%d'%index)
            if index>=count or free<=0 or len(selected)>=12:break
            row=need(o.records[index] if index<len(o.records) else None,'prepared row%d'%index)
            price=row.price_qword&0xffffffff
            cost=(row.quantity_dword*price)&0xffffffff
            if cost<=coins:
                calls.extend((('0041d490',row.item_dword),('0041d46e',row.quantity_dword&0xffff),('0041d490',price)))
                payload.extend(row.item_dword.to_bytes(4,'little'))
                payload.extend((row.quantity_dword&0xffff).to_bytes(2,'little'))
                payload.extend(price.to_bytes(4,'little'))
                coins-=cost;free-=1;ordinal=len(selected);selected.append(index)
                candidate=replace(candidate,accumulated_qword=(candidate.accumulated_qword+cost)&((1<<64)-1))
                fresh=need(o.fresh_global_bases.get(ordinal),'fresh value(global553f4c) for selected%d'%ordinal)
                address=(fresh-0x28)&0xffffffff
                calls.append(('0045ddf4',address,0));writes.append(('protected_zero_helper',address,b'\0'*4))
                normal(o.zero_helper_returns.get(ordinal),'selected%d protected-zero helper'%ordinal)
                address=(base+ordinal*0x28)&0xffffffff
                calls.append(('memset',address,0,0x23));writes.append(('memset_plan',address,b'\0'*0x23))
                normal(o.memset_returns.get(ordinal),'selected%d memset'%ordinal)
            index+=1
        if selected:
            calls.extend((('004c7710',0x561ef8,2,0),('004c7710',0x561ef8,len(payload),1000)))
        return output(True)
    except Missing as error:return output(False,str(error))

@dataclass(frozen=True)
class BuyOpenExecution:
    complete:bool
    state:BuyOpenState
    prospective_state:BuyOpenState
    queue:QueueState
    prospective_queue:QueueState
    source:BuyOpenPlan
    queue_decisions:tuple=()
    missing:str=''
    independently_verified:bool=False

def compose_buy_open(state,observation,queue,samples):
    if not isinstance(queue,QueueState) or not isinstance(samples,Mapping):raise ValueError('Typed queue and per-packet samples required')
    source=plan_buy_open(state,observation);prospective=queue;decisions=[]
    if not source.complete:
        return BuyOpenExecution(False,state,source.prospective_state,queue,queue,source,missing=source.missing)
    for index,(payload,delay) in enumerate(source.packets):
        sample=samples.get(index)
        if sample is None:
            return BuyOpenExecution(False,state,source.state,queue,prospective,source,tuple(decisions),'enqueue%d sample'%index)
        if not isinstance(sample,QueueSample):raise ValueError('Typed per-enqueue sample required')
        decision=enqueue(prospective,payload,len(payload),delay,sample.connection_gate,sample.tick)
        decisions.append(decision)
        if decision.state is None:
            return BuyOpenExecution(False,state,source.state,queue,prospective,source,tuple(decisions),decision.missing or decision.status)
        prospective=decision.state
    return BuyOpenExecution(True,source.state,source.state,prospective,prospective,source,tuple(decisions))
