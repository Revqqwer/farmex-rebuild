"""Reached SELL phase2 clock gate; UI spans are opaque supplied receipts."""
from dataclasses import dataclass

@dataclass(frozen=True)
class SellSetupDelayObservation:
    extra_wait_dword:object=None
    started_stamp_qword:object=None
    tick_dword:object=None
    waiting_span_returned:object=None
    ready_span_returns:tuple=()
    def __post_init__(self):
        for name,bits in (('extra_wait_dword',32),('started_stamp_qword',64),('tick_dword',32)):
            value=getattr(self,name)
            if value is not None and (type(value) is not int or not 0<=value<1<<bits):raise ValueError('Raw setup-delay field required: '+name)
        if type(self.ready_span_returns) is not tuple or len(self.ready_span_returns)>2:raise ValueError('Two separate ready UI spans maximum')
        for value in (self.waiting_span_returned,)+self.ready_span_returns:
            if value is not None and type(value) is not bool:raise ValueError('Explicit UI span normal return required')

@dataclass(frozen=True)
class SellSetupDelayPlan:
    complete:bool
    status:str
    interval_signed:object=None
    elapsed_signed:object=None
    delay_due:object=None
    remaining_ms:object=None
    steps:tuple=()
    missing:str=''
    independently_verified:bool=False

def plan_sell_setup_delay(observation):
    if not isinstance(observation,SellSetupDelayObservation):raise ValueError('Typed SELL setup-delay required')
    o=observation;interval=None;elapsed=None;due=None;remaining=None;steps=[]
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def result(complete,status,missing=''):
        return SellSetupDelayPlan(complete,status,interval,elapsed,due,remaining,tuple(steps),missing)
    try:
        steps.append(('read','+d0'))
        seconds=(need(o.extra_wait_dword,'extra wait DWORD+d0')+61)&0xffffffff
        steps.append(('GetTickCount',))
        tick=need(o.tick_dword,'fresh phase2 tick EAX')
        steps.append(('read','+8','QWORD'))
        stamp=need(o.started_stamp_qword,'started QWORD+8')
        bits=(seconds*1000)&0xffffffff
        interval=bits if bits<1<<31 else bits-(1<<32)
        bits=(tick-stamp)&0xffffffffffffffff
        elapsed=bits if bits<1<<63 else bits-(1<<64)
        due=elapsed>=interval
        if not due:
            remaining=interval-elapsed
            steps.append(('normal_span','004217d7','00421924'))
            if o.waiting_span_returned is not True:raise Missing('waiting countdown/string/UI span normal return')
            return result(True,'waiting')
        for i,span in enumerate((('0042117e','004211c1'),('004211c4','0042121a'))):
            steps.append(('normal_span',i,*span))
            if i>=len(o.ready_span_returns) or o.ready_span_returns[i] is not True:
                raise Missing('ready UI/string span%d normal return'%i)
        steps.append(('0042060c',))
        return result(True,'setup_helper_reached')
    except Missing as error:return result(False,'needs_observation',str(error))
