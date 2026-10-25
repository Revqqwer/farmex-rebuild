"""Reached SELL setup-result1 caller; opaque helper/span receipts, no actions."""
from dataclasses import dataclass
from merchant_bank_route import MerchantBankRouteInputs,plan_merchant_bank_route
import json

@dataclass(frozen=True)
class SellFailureObservation:
    header_span_returns:tuple=()
    alarm_byte:object=None
    alarm_span_returned:object=None
    policy_results:tuple=()
    status_byte_90:object=None
    setup_gate_byte:object=None
    branch_span_returns:tuple=()
    stop_returned:object=None
    disconnect_returned:object=None
    route_span_returned:object=None
    route_inputs:object=None
    route_inputs_factory:object=None
    def __post_init__(self):
        if self.route_inputs is not None and not isinstance(self.route_inputs,MerchantBankRouteInputs):raise ValueError('Typed merchant bank route inputs required')
        if self.route_inputs_factory is not None and not callable(self.route_inputs_factory):raise ValueError('Own lazy route-input factory required')
        for rows,limit in ((self.header_span_returns,2),(self.branch_span_returns,2)):
            if type(rows) is not tuple or len(rows)>limit:raise ValueError('Two independent normal span receipts maximum')
            for v in rows:
                if v is not None and type(v) is not bool:raise ValueError('Explicit normal span receipt required')
        if type(self.policy_results) is not tuple or len(self.policy_results)>3:raise ValueError('Three ordered policy DWORD samples maximum')
        for v in self.policy_results:
            if v is not None and (type(v) is not int or not 0<=v<1<<32):raise ValueError('Raw policy DWORD sample required')
        for v in (self.alarm_byte,self.status_byte_90,self.setup_gate_byte):
            if v is not None and (type(v) is not int or not 0<=v<256):raise ValueError('Raw failure BYTE required')
        for v in (self.alarm_span_returned,self.stop_returned,self.disconnect_returned,self.route_span_returned):
            if v is not None and type(v) is not bool:raise ValueError('Explicit helper/span normal return required')

@dataclass(frozen=True)
class SellFailurePlan:
    complete:bool
    status:str
    phase_dword:int=2
    prospective_phase_dword:int=2
    setup_gate_byte:object=None
    prospective_setup_gate_byte:object=None
    steps:tuple=()
    writes:tuple=()
    missing:str=''
    independently_verified:bool=False
    route_plan:object=None

def plan_sell_failure(o):
    if not isinstance(o,SellFailureObservation):raise ValueError('Typed SELL failure observations required')
    steps=[];writes=[];phase=2;gate=o.setup_gate_byte;route_plan=None
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def span(receipts,index,begin,end,label):
        steps.append(('normal_span',label,index,begin,end))
        if index>=len(receipts) or receipts[index] is not True:raise Missing(label+' span%d normal return'%index)
    def stop(site):
        steps.append(('0040ae0c',0x561f34,0,site))
        if o.stop_returned is not True:raise Missing('stop helper normal return')
    def policy(index):
        steps.append(('read','+d4',index))
        if index>=len(o.policy_results):raise Missing('fresh policy DWORD read%d'%index)
        return need(o.policy_results[index],'policy DWORD value%d'%index)
    def result(complete,status,missing=''):
        return SellFailurePlan(complete,status,phase if complete else 2,phase,
            gate if complete else o.setup_gate_byte,gate,tuple(steps),tuple(writes),missing,route_plan=route_plan)
    try:
        span(o.header_span_returns,0,'00421360','004213a3','failure status')
        span(o.header_span_returns,1,'004213a6','004213fc','failure status')
        steps.append(('read','+d8'))
        if need(o.alarm_byte,'failure alarm BYTE+d8'):
            steps.append(('normal_span','failure alarm','0042140b','0042144d'))
            if o.alarm_span_returned is not True:raise Missing('failure alarm span normal return')
        if policy(0)==0:
            span(o.branch_span_returns,0,'00421460','004214cc','stop notification')
            stop('004214d6');return result(True,'stop_returned')
        if policy(1)==1:
            stop('004214fa');steps.append(('004c7e0c',0x561ef8))
            if o.disconnect_returned is not True:raise Missing('disconnect helper normal return')
            span(o.branch_span_returns,0,'0042150d','00421579','disconnect notification')
            return result(True,'disconnect_returned')
        if policy(2)!=2:return result(True,'unhandled_policy')
        steps.append(('read','+90'))
        if need(o.status_byte_90,'bank status BYTE+90'):
            span(o.branch_span_returns,0,'004216a1','0042170d','bank unavailable notification')
            stop('00421717');return result(True,'bank_unavailable_stop_returned')
        steps.append(('read','+58'));need(gate,'setup gate BYTE+58')
        if gate==0:gate=1;writes.append((0x58,1,1))
        phase=0;writes.append((4,4,0))
        span(o.branch_span_returns,0,'004215b9','004215fc','bank status')
        span(o.branch_span_returns,1,'004215ff','00421654','bank status')
        steps.append(('normal_span','route string/call/cleanup','00421657','00421699','004ebcbc',0x5687a8,0x50e0b2))
        inputs=o.route_inputs
        if o.route_inputs_factory is not None:
            if inputs is not None:raise ValueError('Raw and lazy bank route inputs conflict')
            inputs=o.route_inputs_factory()
            if inputs is None:raise Missing('own bank route input factory has no observation')
            if not isinstance(inputs,MerchantBankRouteInputs):raise ValueError('Factory must return typed bank route inputs')
        if inputs is not None:
            if inputs.kind!='SMerchant':raise ValueError('SELL bank route requires SMerchant filename')
            route_plan=plan_merchant_bank_route(inputs)
            if not route_plan.complete:raise Missing('local bank route: '+route_plan.missing)
        if o.route_span_returned is not True:raise Missing('bank route/string/helper span normal return')
        if route_plan is not None and route_plan.stop_required:return result(True,'bank_route_error_span_returned')
        return result(True,'bank_route_span_returned')
    except Missing as e:return result(False,'needs_observation',str(e))

def parse_sell_failure(text):
    """Validate reached JSON operands only; preview planner does no native IO."""
    raw=json.loads(text)
    allowed=set(SellFailureObservation.__dataclass_fields__)-{'route_inputs','route_inputs_factory'}
    if type(raw) is not dict or set(raw)-allowed-{'bank_error_returns'}:
        raise ValueError('SELL başarısızlık gözlemi bilinen alanlarla JSON nesnesi olmalı')
    values={};seen=set()
    for _ in range(32):
        o=SellFailureObservation(**values);p=plan_sell_failure(o)
        if p.complete:return o
        step=p.steps[-1]
        index=None
        if step[0]=='normal_span':
            label=step[1]
            if label=='failure status':key='header_span_returns';index=step[2]
            elif label in ('stop notification','disconnect notification','bank unavailable notification','bank status'):
                key='branch_span_returns';index=step[2]
            elif label=='failure alarm':key='alarm_span_returned'
            elif label=='route string/call/cleanup':key='route_span_returned'
            else:raise ValueError('Unmapped failure span')
        elif step[0]=='read':
            key={'+d8':'alarm_byte','+d4':'policy_results','+90':'status_byte_90','+58':'setup_gate_byte'}[step[1]]
            if step[1]=='+d4':index=step[2]
        elif step[0]=='0040ae0c':key='stop_returned'
        elif step[0]=='004c7e0c':key='disconnect_returned'
        else:raise ValueError('Unmapped failure operand')
        tag=(key,index)
        if tag in seen or key not in raw or raw[key] is None:return o
        seen.add(tag)
        if index is None:values[key]=raw[key]
        else:
            if type(raw[key]) is not list:raise ValueError('SELL sıralı gözlemi JSON listesi olmalı')
            if index>=len(raw[key]):return o
            values[key]=values.get(key,())+(raw[key][index],)
    raise ValueError('Failure parser exceeded its bounded source operands')

def parse_bank_error_returns(text):
    """Only called when the bank-route input factory is reached."""
    data=json.loads(text)
    if type(data) is not dict:raise ValueError('SELL gözlemi JSON nesnesi olmalı')
    raw=data.get('bank_error_returns',{})
    allowed={'error_message_returned','path_cleanup_returned','error_stop_returned',
             'error_notification_returned','error_final_cleanup_returned'}
    if type(raw) is not dict or set(raw)-allowed:raise ValueError('Banka rota hata dönüşleri geçersiz')
    if any(v is not None and type(v) is not bool for v in raw.values()):raise ValueError('Ayrı boolean hata dönüşü gerekli')
    return raw
