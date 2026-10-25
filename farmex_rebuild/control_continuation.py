"""00459071..004592a7 clock/party plans; mode!=0 continues at00459519.

No clock query, process termination, game operation or alarm is executed.
Party counts are separate ordered DWORD samples, not a stable-list assumption.
"""
import re
from dataclasses import dataclass,field
from types import MappingProxyType
from control_guards import ROOT,ControlGuardConfiguration,plan_control_guards

FLAG_PATHS={ROOT+'chGameCloseClock':0xd8,ROOT+'chPartyCountBotStop':0xe8,
 ROOT+'chPartyCountAlarm':0xe9,ROOT+'chPartyNotPriestBotStop':0xea,ROOT+'chPartyNotPriestAlarm':0xeb}
NUMBER_PATHS={ROOT+'txtGameCloseHour':0xdc,ROOT+'txtGameCloseMinute':0xe0,ROOT+'txtPartyControlCount':0xe4}
CONTROL_CONTINUATION_INPUTS=tuple(FLAG_PATHS)+tuple(NUMBER_PATHS)

def compile_control_continuation(values):
    fields={}
    for path,offset in FLAG_PATHS.items():
        value=values.get(path)
        if type(value) is not bool:raise ValueError('Control checkbox required: '+path)
        fields[offset]=int(value)
    for path,offset in NUMBER_PATHS.items():
        value=values.get(path)
        if type(value) is not str or not re.fullmatch(r'[+-]?[0-9]+',value.strip()):raise ValueError('Strict decimal control parameter required: '+path)
        parsed=int(value.strip())
        if not -(1<<63)<=parsed<(1<<63):raise ValueError('Signed64 control parameter required')
        fields[offset]=parsed&0xffffffff
    return ControlGuardConfiguration(fields)

@dataclass(frozen=True)
class ControlContinuationObservation:
    local_hour:object=None
    local_minute:object=None
    runtime_mode:object=None
    current_process_handle:object=None
    party_count_samples:tuple=()
    priest_matches:object=field(default_factory=dict)
    stop_returned:object=None
    town_returned:object=None
    alarm_returned:object=None

    def __post_init__(self):
        for v in (self.local_hour,self.local_minute,self.runtime_mode,self.current_process_handle)+tuple(self.party_count_samples):
            if v is not None and (type(v) is not int or not 0<=v<=0xffffffff):raise ValueError('Observed DWORD required')
        for v in (self.stop_returned,self.town_returned,self.alarm_returned):
            if v is not None and type(v) is not bool:raise ValueError('Observed normal return required')
        for k,v in self.priest_matches.items():
            if type(k) is not int or k<1 or (v is not None and type(v) is not bool):raise ValueError('Indexed source comparison observations required')
        object.__setattr__(self,'party_count_samples',tuple(self.party_count_samples))
        object.__setattr__(self,'priest_matches',MappingProxyType(dict(self.priest_matches)))

@dataclass(frozen=True)
class ControlContinuationPlan:
    status:str
    complete:bool
    source_return_planned:bool=False
    termination_call_planned:bool=False
    calls:tuple=()
    missing:str=''
    next_address:object=None
    native_execution_verified:bool=False

@dataclass(frozen=True)
class ControlChainPlan:
    status:str
    complete:bool
    entry:object
    continuation:object=None
    calls:tuple=()
    next_address:object=None
    native_execution_verified:bool=False

class _Missing(Exception):pass

def plan_control_continuation(configuration,observation):
    if not isinstance(configuration,ControlGuardConfiguration) or not isinstance(observation,ControlContinuationObservation):
        raise ValueError('Typed continuation config and observations required')
    c=configuration.fields;o=observation;calls=[];count_index=0
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def f(offset,bits):
        value=need(c.get(offset),'field+%x'%offset)
        if type(value) is not int or not 0<=value<(1<<bits):raise ValueError('Raw control field required')
        return value
    def signed(value):return value-(1<<32) if value&0x80000000 else value
    def count():
        nonlocal count_index
        calls.append(('004645e4',()))
        i=count_index;count_index+=1
        if i>=len(o.party_count_samples):raise _Missing('004645e4 count sample%d'%i)
        return signed(need(o.party_count_samples[i],'004645e4 count sample%d'%i))
    def response(reason,stop,alarm,literal):
        if stop:
            calls.append(('0040ae0c',(0x561f34,0)))
            if o.stop_returned is not True:raise _Missing('0040ae0c normal return')
            calls.append(('00465678',()))
            if o.town_returned is not True:raise _Missing('00465678 normal return')
        if alarm:
            calls.append(('00404260',(0x569568,('literal',literal))))
            if o.alarm_returned is not True:raise _Missing('00404260 normal return')
        return ControlContinuationPlan(reason,True,True,calls=tuple(calls))
    try:
        if f(0xd8,8)!=0:
            calls.extend((('00507984',()),('0050791e',())))
            if need(o.local_hour,'localtime hour DWORD')==f(0xdc,32):
                if need(o.local_minute,'localtime minute DWORD')==f(0xe0,32):
                    calls.append(('0050749e',()))
                    handle=need(o.current_process_handle,'GetCurrentProcess handle')
                    calls.append(('0050755e',(handle,0)))
                    # A planned TerminateProcess call is not proof it returned or terminated.
                    return ControlContinuationPlan('termination_call_planned',True,termination_call_planned=True,calls=tuple(calls))
        mode=need(o.runtime_mode,'global00561f58')
        if mode!=0:return ControlContinuationPlan('mode_skips_party_section',True,calls=tuple(calls),next_address=0x459519)
        if f(0xe8,8)!=0 or f(0xe9,8)!=0:
            if count()<signed(f(0xe4,32)):
                return response('party_count_below',f(0xe8,8)!=0,f(0xe9,8)!=0,0x52139c)
        if f(0xea,8)!=0 or f(0xeb,8)!=0:
            found=False
            if count()>=2:
                index=1
                while count()>=index:
                    calls.append(('00505d20',(('party_text',0x569650+index*4),('literal',0x5213a4))))
                    if need(o.priest_matches.get(index),'00505d20 member%d'%index):found=True;break
                    index+=1
            if not found:return response('party_priest_not_found',f(0xea,8)!=0,f(0xeb,8)!=0,0x5213ab)
        return ControlContinuationPlan('clock_party_prefix_passed',True,calls=tuple(calls),next_address=0x4592a7)
    except _Missing as exc:return ControlContinuationPlan('needs_observation',False,calls=tuple(calls),missing=str(exc))

def replay_control_chain(entry_config,entry_observation,continuation_config,continuation_observation):
    entry=plan_control_guards(entry_config,entry_observation)
    if not entry.complete or entry.source_return_planned:
        return ControlChainPlan(entry.status,entry.complete,entry,calls=entry.calls,next_address=entry.next_address)
    follow=plan_control_continuation(continuation_config,continuation_observation)
    return ControlChainPlan(follow.status,follow.complete,entry,follow,entry.calls+follow.calls,follow.next_address)
