"""SELL phase6 caller 421eb8..42209d; supplied observations, no native UI."""
from dataclasses import dataclass

def _signed32(value):
    value &= 0xffffffff
    return value if value < 0x80000000 else value-(1<<32)

def _idiv1000(value):
    return (abs(value)//1000)*(-1 if value<0 else 1)

@dataclass(frozen=True)
class SellMonitorObservation:
    reopen_byte:object=None
    minutes_dword:object=None
    established_stamp_qword:object=None
    tick_dword:object=None
    display_span_returned:object=None
    def __post_init__(self):
        for name,bits in (('reopen_byte',8),('minutes_dword',32),
                          ('established_stamp_qword',64),('tick_dword',32)):
            value=getattr(self,name)
            if value is not None and (type(value) is not int or not 0<=value<1<<bits):
                raise ValueError('Raw SELL monitor %dbit field required'%bits)
        if self.display_span_returned is not None and type(self.display_span_returned) is not bool:
            raise ValueError('Explicit countdown span normal return required')

@dataclass(frozen=True)
class SellMonitorPlan:
    complete:bool
    phase_dword:int=6
    prospective_phase_dword:int=6
    timer_due:object=None
    interval_signed:object=None
    elapsed_signed:object=None
    display_seconds_signed:object=None
    steps:tuple=()
    writes:tuple=()
    missing:str=''
    independently_verified:bool=False

def plan_sell_monitor(observation):
    if not isinstance(observation,SellMonitorObservation):raise ValueError('Typed SELL monitor observation required')
    o=observation;phase=6;due=None;interval=None;elapsed=None;seconds=None;steps=[];writes=[]
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def result(complete,missing=''):
        return SellMonitorPlan(complete,phase if complete else 6,phase,due,interval,elapsed,seconds,
                               tuple(steps),tuple(writes),missing)
    try:
        steps.append(('read','+c9'))
        if need(o.reopen_byte,'reopen BYTE+c9')==0:return result(True)
        steps.append(('read','+cc'))
        interval=_signed32(need(o.minutes_dword,'minutes DWORD+cc')*60000)
        steps.append(('GetTickCount',))
        tick=need(o.tick_dword,'fresh monitor tick EAX')
        steps.append(('read','+10','lowDWORD'))
        stamp=need(o.established_stamp_qword,'established QWORD+10 (only low DWORD consumed)')
        elapsed=_signed32(tick-(stamp&0xffffffff))
        due=elapsed>=interval
        if due:
            phase=0;writes.append((4,0,'timer'));return result(True)
        # Source performs two independent signed IDIVs before subtraction.
        seconds=_signed32(_idiv1000(interval)-_idiv1000(elapsed))
        steps.append(('normal_span','00421f47','0042209d'))
        if o.display_span_returned is not True:raise Missing('countdown VCL/string span normal return')
        return result(True)
    except Missing as error:return result(False,str(error))
