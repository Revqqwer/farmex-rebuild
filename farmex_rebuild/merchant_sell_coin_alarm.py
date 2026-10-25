"""420f33..420f9b coin-alarm caller prefix; supplied helper/span results only."""
from dataclasses import dataclass
from source_coin import SourceCoinObservation,plan_source_coin

@dataclass(frozen=True)
class SellCoinAlarmObservation:
    enabled_byte:object=None
    coins_dword:object=None
    reference_qword:object=None
    alarm_span_returned:object=None
    coin_inputs:object=None
    def __post_init__(self):
        for v,bits in ((self.enabled_byte,8),(self.coins_dword,32),(self.reference_qword,64)):
            if v is not None and (type(v) is not int or not 0<=v<1<<bits):raise ValueError('Raw coin alarm field required')
        if self.alarm_span_returned is not None and type(self.alarm_span_returned) is not bool:raise ValueError('Explicit coin alarm normal return required')
        if self.coin_inputs is not None:
            if not isinstance(self.coin_inputs,SourceCoinObservation):raise ValueError('Typed source coin inputs required')
            if self.coins_dword is not None:raise ValueError('Source coin inputs conflict with raw helper EAX')

@dataclass(frozen=True)
class SellCoinAlarmPlan:
    complete:bool
    status:str
    mismatch:object=None
    steps:tuple=()
    missing:str=''
    independently_verified:bool=False
    coin_plan:object=None

def plan_sell_coin_alarm(o):
    if not isinstance(o,SellCoinAlarmObservation):raise ValueError('Typed coin alarm required')
    steps=[('read','+e0')];mismatch=None;coin_plan=None
    def result(complete,status,missing=''):
        return SellCoinAlarmPlan(complete,status,mismatch,tuple(steps),missing,coin_plan=coin_plan)
    if o.enabled_byte is None:return result(False,'needs_observation','coin alarm BYTE+e0')
    if o.enabled_byte==0:return result(True,'disabled')
    steps.append(('0046258c',))
    coins=o.coins_dword
    if o.coin_inputs is not None:
        coin_plan=plan_source_coin(o.coin_inputs)
        if not coin_plan.complete:return result(False,'needs_observation','coin reader: '+coin_plan.missing)
        coins=coin_plan.coins_dword
    if coins is None:return result(False,'needs_observation','fresh coin helper EAX')
    steps.append(('read','+ec','highDWORD'))
    if o.reference_qword is None:return result(False,'needs_observation','reference coin QWORD+e8')
    if o.reference_qword>>32:mismatch=True
    else:
        steps.append(('read','+e8','lowDWORD'))
        mismatch=coins!=(o.reference_qword&0xffffffff)
    if not mismatch:return result(True,'unchanged')
    steps.append(('normal_span','00420f59','00420f9b','00404260',0x569568))
    if o.alarm_span_returned is not True:return result(False,'needs_observation','coin alarm string/call/cleanup span normal return')
    # Source does not update the reference here. Repeated callbacks can plan the alarm again.
    return result(True,'alarm_span_returned')
