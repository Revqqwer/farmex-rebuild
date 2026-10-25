"""SELL phase3 ready/item wait gates, 42192c..4219fe and421aba..421b60."""
from dataclasses import dataclass
import json
from merchant_open_clock import MerchantWaitClockSample,plan_merchant_open_wait

@dataclass(frozen=True)
class SellPrepareWaitObservation:
    ready_byte:object=None
    item_pending_byte:object=None
    session_stamp_qword:object=None
    item_stamp_qword:object=None
    tick_dword:object=None
    message_span_returned:object=None
    stop_returned:object=None
    def __post_init__(self):
        for name,bits in (('ready_byte',8),('item_pending_byte',8),('session_stamp_qword',64),
                          ('item_stamp_qword',64),('tick_dword',32)):
            value=getattr(self,name)
            if value is not None and (type(value) is not int or not 0<=value<1<<bits):
                raise ValueError('Raw SELL preparation-wait field required: '+name)
        for value in (self.message_span_returned,self.stop_returned):
            if value is not None and type(value) is not bool:raise ValueError('Explicit normal return required')

@dataclass(frozen=True)
class SellPrepareWaitPlan:
    complete:bool
    status:str
    branch:str=''
    clock_plan:object=None
    steps:tuple=()
    missing:str=''
    independently_verified:bool=False

def plan_sell_prepare_wait(observation):
    if not isinstance(observation,SellPrepareWaitObservation):raise ValueError('Typed SELL preparation-wait required')
    o=observation;steps=[('read','+38')];branch='';clock=None
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def result(complete,status,missing=''):
        return SellPrepareWaitPlan(complete,status,branch,clock,tuple(steps),missing)
    try:
        if need(o.ready_byte,'ready BYTE+38')==0:
            branch='session';stamp=o.session_stamp_qword;offset='+40'
            span=('00421ae2','00421b4e');stop_site='00421b58'
        else:
            steps.append(('read','+28'))
            if need(o.item_pending_byte,'item pending BYTE+28')==0:
                return result(True,'selection_path')
            branch='item';stamp=o.item_stamp_qword;offset='+30'
            span=('0042197b','004219e7');stop_site='004219f1'
        steps.append(('GetTickCount',))
        tick=need(o.tick_dword,'fresh '+branch+' wait tick EAX')
        steps.append(('read',offset,'QWORD'))
        stamp=need(stamp,branch+' wait stamp QWORD'+offset)
        clock=plan_merchant_open_wait(1,MerchantWaitClockSample(tick,stamp))
        if not clock.timeout_due:return result(True,'waiting')
        # Both source branches show/clean the timeout message BEFORE stop.
        steps.append(('normal_span',*span))
        if o.message_span_returned is not True:raise Missing(branch+' timeout message/cleanup span normal return')
        steps.append(('0040ae0c',0x561f34,0,stop_site))
        if o.stop_returned is not True:raise Missing(branch+' timeout stop helper normal return')
        return result(True,'timed_out')
    except Missing as error:return result(False,'needs_observation',str(error))

def parse_sell_prepare_wait(text):
    """Workbench JSON; validate only fields reached by the source branch."""
    raw=json.loads(text)
    if type(raw) is not dict:raise ValueError('SELL bekleme gözlemi JSON nesnesi olmalı')
    unknown=set(raw)-set(SellPrepareWaitObservation.__dataclass_fields__)
    if unknown:raise ValueError('Bilinmeyen SELL bekleme alanı: '+','.join(sorted(unknown)))
    reached={'ready_byte':raw.get('ready_byte')}
    o=SellPrepareWaitObservation(**reached)
    if o.ready_byte is None:return o
    if o.ready_byte:
        reached['item_pending_byte']=raw.get('item_pending_byte')
        o=SellPrepareWaitObservation(**reached)
        if o.item_pending_byte is None or o.item_pending_byte==0:return o
    stamp='session_stamp_qword' if o.ready_byte==0 else 'item_stamp_qword'
    reached['tick_dword']=raw.get('tick_dword')
    o=SellPrepareWaitObservation(**reached)
    if o.tick_dword is None:return o
    reached[stamp]=raw.get(stamp)
    o=SellPrepareWaitObservation(**reached)
    p=plan_sell_prepare_wait(o)
    if p.clock_plan is None or not p.clock_plan.timeout_due:return o
    reached['message_span_returned']=raw.get('message_span_returned')
    o=SellPrepareWaitObservation(**reached)
    if o.message_span_returned is not True:return o
    reached['stop_returned']=raw.get('stop_returned')
    return SellPrepareWaitObservation(**reached)
