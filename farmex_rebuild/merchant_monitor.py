"""BUY phase5 normal-path planner, 422e9f..4230ac. Supplied observations only."""
from dataclasses import dataclass
from merchant_setup import MerchantInventoryObservation,plan_merchant_inventory

def _raw(value,bits):
    if value is not None and (type(value) is not int or not 0<=value<1<<bits):
        raise ValueError('Raw %dbit observation required'%bits)

def _signed(value):
    value&=0xffffffff
    return value if value<0x80000000 else value-(1<<32)

def _div1000(value):
    return (abs(value)//1000)*(1 if value>=0 else -1)

@dataclass(frozen=True)
class BuyMonitorObservation:
    reopen_byte:object=None
    minutes_dword:object=None
    established_stamp_qword:object=None
    tick_dword:object=None
    threshold_dword:object=None
    free_count_dword:object=None
    inventory_inputs:object=None
    display_span_returned:object=None
    def __post_init__(self):
        for name,bits in (('reopen_byte',8),('minutes_dword',32),('established_stamp_qword',64),
                          ('tick_dword',32),('threshold_dword',32),('free_count_dword',32)):
            _raw(getattr(self,name),bits)
        if self.display_span_returned is not None and type(self.display_span_returned) is not bool:
            raise ValueError('Explicit normal display-span return required')
        if self.inventory_inputs is not None and not isinstance(self.inventory_inputs,MerchantInventoryObservation):
            raise ValueError('Typed fresh inventory required')
        if self.inventory_inputs is not None and self.free_count_dword is not None:
            raise ValueError('Inventory observations conflict with raw helper EAX')

@dataclass(frozen=True)
class BuyMonitorPlan:
    complete:bool
    phase_dword:int=5
    prospective_phase_dword:int=5
    timer_due:object=None
    free_due:object=None
    interval_signed:object=None
    elapsed_signed:object=None
    display_seconds_signed:object=None
    steps:tuple=()
    writes:tuple=()
    inventory_plan:object=None
    missing:str=''
    independently_verified:bool=False

def plan_buy_monitor(observation):
    if not isinstance(observation,BuyMonitorObservation):raise ValueError('Typed BUY monitor observation required')
    o=observation;phase=5;timer_due=None;free_due=None;interval=None;elapsed=None;seconds=None
    steps=[];writes=[];inventory=None
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def result(complete,missing=''):
        return BuyMonitorPlan(complete,phase if complete else 5,phase,timer_due,free_due,interval,elapsed,seconds,
                              tuple(steps),tuple(writes),inventory,missing)
    try:
        steps.append(('read','+110'))
        if need(o.reopen_byte,'reopen BYTE+110'):
            interval=_signed(need(o.minutes_dword,'minutes DWORD+114')*60000)
            steps.append(('GetTickCount',));tick=need(o.tick_dword,'fresh monitor tick EAX')
            stamp=need(o.established_stamp_qword,'established QWORD+10')
            elapsed=_signed(tick-(stamp&0xffffffff))
            timer_due=elapsed>=interval
            if timer_due:
                phase=0;writes.append((4,0,'timer'))
            else:
                # Two distinct IDIV instructions, not division of the difference.
                seconds=_signed(_div1000(interval)-_div1000(elapsed))
                steps.append(('normal_span','00422eff','0042307b'))
                if o.display_span_returned is not True:raise Missing('countdown VCL/string span normal return')
        steps.append(('0042070c',)) # Always follows timer branch, including timer_due.
        count=o.free_count_dword
        if o.inventory_inputs is not None:
            inventory=plan_merchant_inventory(o.inventory_inputs)
            if not inventory.complete:raise Missing('inventory: '+inventory.missing)
            count=inventory.free_count
        count=need(count,'fresh inventory helper EAX')
        threshold=need(o.threshold_dword,'free threshold DWORD+120')
        free_due=_signed(count)<=_signed(threshold)
        if free_due:
            phase=0;writes.append((4,0,'free_threshold'))
        return result(True)
    except Missing as error:return result(False,str(error))
