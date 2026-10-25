"""SELL phase1 close-pending wait at42104f..42111a; no helper execution."""
from dataclasses import dataclass
from merchant_open_clock import MerchantWaitClockSample,plan_merchant_open_wait

@dataclass(frozen=True)
class SellCloseWaitObservation:
    pending_byte:object=None
    close_stamp_qword:object=None
    tick_dword:object=None
    message_span_returned:object=None
    stop_returned:object=None
    def __post_init__(self):
        for value,bits in ((self.pending_byte,8),(self.close_stamp_qword,64),(self.tick_dword,32)):
            if value is not None and (type(value) is not int or not 0<=value<1<<bits):raise ValueError('Raw close-wait field required')
        for value in (self.message_span_returned,self.stop_returned):
            if value is not None and type(value) is not bool:raise ValueError('Explicit close timeout normal return required')

@dataclass(frozen=True)
class SellCloseWaitPlan:
    complete:bool
    status:str
    phase_dword:int=1
    clock_plan:object=None
    steps:tuple=()
    writes:tuple=()
    missing:str=''
    independently_verified:bool=False

def plan_sell_close_wait(o):
    if not isinstance(o,SellCloseWaitObservation):raise ValueError('Typed SELL close wait required')
    steps=[('read','+18')];clock=None
    def result(complete,status,missing=''):
        clear=complete and status=='pending_cleared'
        return SellCloseWaitPlan(complete,status,2 if clear else 1,clock,tuple(steps),((4,4,2),) if clear else (),missing)
    if o.pending_byte is None:return result(False,'needs_observation','close pending BYTE+18')
    if o.pending_byte==0:return result(True,'pending_cleared')
    steps.append(('GetTickCount',))
    if o.tick_dword is None:return result(False,'needs_observation','fresh close wait tick EAX')
    steps.append(('read','+20','QWORD'))
    if o.close_stamp_qword is None:return result(False,'needs_observation','close pending stamp QWORD+20')
    clock=plan_merchant_open_wait(o.pending_byte,MerchantWaitClockSample(o.tick_dword,o.close_stamp_qword))
    if not clock.timeout_due:return result(True,'waiting')
    steps.append(('normal_span','00421091','004210fd'))
    if o.message_span_returned is not True:return result(False,'needs_observation','close timeout message/cleanup span normal return')
    steps.append(('0040ae0c',0x561f34,0))
    if o.stop_returned is not True:return result(False,'needs_observation','close timeout stop helper normal return')
    return result(True,'timed_out')
