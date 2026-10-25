"""Reached BUY result1 caller4224b4..422a52; observations, no native IO."""
from dataclasses import dataclass
from merchant_setup import MerchantInventoryObservation,plan_merchant_inventory
from merchant_bank_count import BankCountPlan
from merchant_bank_route import MerchantBankRouteInputs,plan_merchant_bank_route
import json

def _raw(v,bits):
    if v is not None and (type(v) is not int or not 0<=v<1<<bits):raise ValueError('Raw unsigned observation required')
def _signed(v):return v-(1<<32) if v&0x80000000 else v

@dataclass(frozen=True)
class BuyFailureObservation:
    inventory_returned:object=None
    free_count_dword:object=None
    inventory_inputs:object=None
    threshold_dword:object=None
    alarm_byte:object=None
    alarm_span_returned:object=None
    policy_results:tuple=()
    branch_span_returns:tuple=()
    stop_returned:object=None
    disconnect_returned:object=None
    bank_count_returned:object=None
    bank_count_dword:object=None
    bank_count_execution:object=None
    setup_gate_byte:object=None
    route_span_returned:object=None
    route_inputs:object=None
    route_inputs_factory:object=None
    def __post_init__(self):
        for v in (self.inventory_returned,self.alarm_span_returned,self.stop_returned,self.disconnect_returned,
                  self.bank_count_returned,self.route_span_returned):
            if v is not None and type(v) is not bool:raise ValueError('Separate normal-return boolean required')
        for v in (self.free_count_dword,self.threshold_dword,self.bank_count_dword):_raw(v,32)
        for v in (self.alarm_byte,self.setup_gate_byte):_raw(v,8)
        if type(self.policy_results) is not tuple or len(self.policy_results)>3:raise ValueError('Three ordered fresh policy samples maximum')
        for v in self.policy_results:_raw(v,32)
        if type(self.branch_span_returns) is not tuple or len(self.branch_span_returns)>2:raise ValueError('Two independent normal spans maximum')
        for v in self.branch_span_returns:
            if v is not None and type(v) is not bool:raise ValueError('Explicit span return required')
        for v,cls in ((self.inventory_inputs,MerchantInventoryObservation),(self.bank_count_execution,BankCountPlan),(self.route_inputs,MerchantBankRouteInputs)):
            if v is not None and not isinstance(v,cls):raise ValueError('Typed bound input required')
        if self.route_inputs_factory is not None and not callable(self.route_inputs_factory):raise ValueError('Own lazy route input factory required')

@dataclass(frozen=True)
class BuyFailurePlan:
    complete:bool
    status:str
    phase_dword:int=2
    prospective_phase_dword:int=2
    setup_gate_byte:object=None
    prospective_setup_gate_byte:object=None
    steps:tuple=()
    writes:tuple=()
    missing:str=''
    inventory_plan:object=None
    bank_count_execution:object=None
    bank_count_after_dec:object=None
    route_plan:object=None
    independently_verified:bool=False

def plan_buy_failure(o):
    if not isinstance(o,BuyFailureObservation):raise ValueError('Typed reached BUY failure observations required')
    steps=[];writes=[];phase=2;gate=o.setup_gate_byte;inventory=None;count_plan=None;after=None;route=None
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def normal(v,label):
        steps.append(('normal_return',label))
        if v is not True:raise Missing(label)
    def span(index,begin,end,label):
        steps.append(('normal_span',label,index,begin,end))
        if index>=len(o.branch_span_returns) or o.branch_span_returns[index] is not True:raise Missing(label+' span normal return')
    def stop(site):
        steps.append(('0040ae0c',site))
        normal(o.stop_returned,'stop helper normal return')
    def policy(index):
        steps.append(('read','+11c',index))
        if index>=len(o.policy_results):raise Missing('fresh policy%d'%index)
        return need(o.policy_results[index],'policy%d DWORD'%index)
    def result(ok,status,missing=''):
        return BuyFailurePlan(ok,status,phase if ok else 2,phase,gate if ok else o.setup_gate_byte,gate,
            tuple(steps),tuple(writes),missing,inventory,count_plan,after,route)
    try:
        steps.append(('0042070c','fresh failure inventory'))
        normal(o.inventory_returned,'failure inventory helper normal return')
        steps.append(('read_result','inventory'))
        if o.inventory_inputs is not None:
            if o.free_count_dword is not None:raise ValueError('Bound failure inventory conflicts with raw count')
            inventory=plan_merchant_inventory(o.inventory_inputs)
            if not inventory.complete:raise Missing('failure inventory: '+inventory.missing)
            free=inventory.free_count
        else:free=need(o.free_count_dword,'fresh failure inventory EAX')
        steps.append(('read','+120'))
        threshold=need(o.threshold_dword,'fresh alarm threshold DWORD')
        if _signed(free)<=_signed(threshold):
            steps.append(('read','+124'))
            if need(o.alarm_byte,'failure alarm BYTE'):
                steps.append(('normal_span','failure alarm','004224e9','0042252b'))
                normal(o.alarm_span_returned,'failure alarm normal return')
        if policy(0)==0:
            span(0,'0042253e','00422670','stop notification');stop('0042267a')
            return result(True,'stop_returned')
        if policy(1)==1:
            stop('0042269e');steps.append(('004c7e0c',0x561ef8))
            normal(o.disconnect_returned,'disconnect helper normal return')
            span(0,'004226b1','004227e3','disconnect notification')
            return result(True,'disconnect_returned')
        if policy(2)!=2:return result(True,'unhandled_policy')
        steps.append(('0046ff6c',0x5690e0))
        normal(o.bank_count_returned,'bank count helper normal return')
        steps.append(('read_result','bank count'))
        count_plan=o.bank_count_execution
        if count_plan is not None:
            if o.bank_count_dword is not None:raise ValueError('Bound bank count conflicts with raw EAX')
            if not count_plan.complete:raise Missing('bank count: '+count_plan.missing)
            count=need(count_plan.count_dword,'bound bank count EAX')
        else:count=need(o.bank_count_dword,'bank count EAX')
        after=(count-1)&0xffffffff;steps.append(('DEC_EAX_signed_JL',count,after))
        if after&0x80000000:
            stop('004229db');span(0,'004229e3','00422a4f','bank unavailable notification')
            return result(True,'bank_unavailable_stop_returned')
        steps.append(('read','+58'));need(gate,'setup gate BYTE')
        if gate==0:gate=1;writes.append((0x58,1,1))
        phase=0;writes.append((4,4,0))
        span(0,'00422825','0042292e','bank status assembly')
        span(1,'00422931','00422987','bank status UI')
        steps.append(('normal_span','route string/call/cleanup','0042298a','004229cc','BMerchant'))
        inputs=o.route_inputs
        if o.route_inputs_factory is not None:
            if inputs is not None:raise ValueError('Raw/lazy bank route inputs conflict')
            inputs=o.route_inputs_factory()
            if inputs is None:raise Missing('own bank route factory observation')
            if not isinstance(inputs,MerchantBankRouteInputs):raise ValueError('Typed bank route factory result required')
        if inputs is not None:
            if inputs.kind!='BMerchant':raise ValueError('BUY failure requires BMerchant filename')
            route=plan_merchant_bank_route(inputs)
            if not route.complete:raise Missing('BUY bank route: '+route.missing)
        normal(o.route_span_returned,'outer BUY route/string/helper normal return')
        return result(True,'bank_route_error_span_returned' if route is not None and route.stop_required else 'bank_route_span_returned')
    except Missing as error:return result(False,'needs_observation',str(error))

def parse_buy_failure(text):
    """Own raw JSON operands, validated only as reached; no IO in preview."""
    raw=json.loads(text)
    excluded={'inventory_inputs','bank_count_execution','route_inputs','route_inputs_factory'}
    allowed=set(BuyFailureObservation.__dataclass_fields__)-excluded
    if type(raw) is not dict or set(raw)-allowed-{'bank_error_returns'}:
        raise ValueError('BUY başarısızlık gözlemi bilinen alanlarla JSON nesnesi olmalı')
    values={};seen=set()
    normal_keys={'failure inventory helper normal return':'inventory_returned',
        'failure alarm normal return':'alarm_span_returned','stop helper normal return':'stop_returned',
        'disconnect helper normal return':'disconnect_returned','bank count helper normal return':'bank_count_returned',
        'outer BUY route/string/helper normal return':'route_span_returned'}
    for _ in range(32):
        o=BuyFailureObservation(**values);p=plan_buy_failure(o)
        if p.complete:return o
        step=p.steps[-1];index=None
        if step[0]=='normal_return':key=normal_keys[step[1]]
        elif step[0]=='read_result':key='free_count_dword' if step[1]=='inventory' else 'bank_count_dword'
        elif step[0]=='read':
            key={'+120':'threshold_dword','+124':'alarm_byte','+11c':'policy_results','+58':'setup_gate_byte'}[step[1]]
            if step[1]=='+11c':index=step[2]
        elif step[0]=='normal_span':key='branch_span_returns';index=step[2]
        else:raise ValueError('Unmapped BUY failure operand')
        tag=(key,index)
        if tag in seen or key not in raw or raw[key] is None:return o
        seen.add(tag)
        if index is None:values[key]=raw[key]
        else:
            if type(raw[key]) is not list:raise ValueError('BUY sıralı gözlem JSON listesi olmalı')
            if index>=len(raw[key]):return o
            values[key]=values.get(key,())+(raw[key][index],)
    raise ValueError('BUY failure parser exceeded bounded operands')
