"""004592a7..00459496 party-help request/timer plans, no messaging IO.

Unicode profile text and observed post-conversion AnsiString bytes are separate.
Complete describes a bounded local plan with explicit normal-return samples;
it does not prove helper execution, native ABI or message delivery.
"""
from dataclasses import dataclass,field
from types import MappingProxyType

ROOT='frmMain/MainTab/SheetDiger/GroupBox9/'
FLAG_PATHS={ROOT+'chHelpChatBuff':0x103,ROOT+'chHelpChatAC':0x104,
 ROOT+'chHelpChatSW':0x105,ROOT+'chHelpChatCure':0x106}
# Follow actual producer getters; published object-field order differs from use order.
TEXT_PATHS={ROOT+'txtHelpChatBuff':0x108,ROOT+'txtHelpChatAC':0x10c,
 ROOT+'txtHelpChatSW':0x110,ROOT+'txtHelpChatCure':0x114}
PARTY_HELP_INPUTS=tuple(FLAG_PATHS)+tuple(TEXT_PATHS)
ROWS=((0x103,0x108,0x553cbc,'004642d0'),(0x104,0x10c,0x553cc4,'00464364'),
      (0x105,0x110,0x553ccc,None),(0x106,0x114,0x553cd4,'004643f8'))

@dataclass(frozen=True)
class PartyHelpConfiguration:
    flags:object
    unicode_texts:object
    ansi_texts:object=field(default_factory=dict)
    def __post_init__(self):
        for name in ('flags','unicode_texts','ansi_texts'):object.__setattr__(self,name,MappingProxyType(dict(getattr(self,name))))

def compile_party_help(values,*,observed_ansi=None):
    flags={};texts={};ansi={}
    for path,offset in FLAG_PATHS.items():
        value=values.get(path)
        if type(value) is not bool:raise ValueError('Party-help checkbox required: '+path)
        flags[offset]=int(value)
    for path,offset in TEXT_PATHS.items():
        text=values.get(path)
        if type(text) is not str:raise ValueError('Party-help Unicode text required: '+path)
        texts[offset]=text
        if observed_ansi is not None and path in observed_ansi:
            value=observed_ansi[path]
            if type(value) is not bytes:raise ValueError('Observed converted AnsiString bytes required')
            ansi[offset]=value
    return PartyHelpConfiguration(flags,texts,ansi)

@dataclass(frozen=True)
class PartyHelpState:
    timers:object=field(default_factory=dict)
    def __post_init__(self):
        if any(type(k) is not int or type(v) is not int or not 0<=v<1<<64 for k,v in self.timers.items()):raise ValueError('Source QWORD timer map required')
        object.__setattr__(self,'timers',MappingProxyType(dict(self.timers)))

@dataclass(frozen=True)
class PartyHelpObservation:
    party_count:object=None
    outer_tick:object=None
    feature_ticks:object=field(default_factory=dict)
    predicate_returns:object=field(default_factory=dict)
    request_returns:object=field(default_factory=dict)
    post_request_ticks:object=field(default_factory=dict)
    final_tick:object=None
    swift_globals:object=field(default_factory=dict)
    swift_samples:tuple=()
    def __post_init__(self):
        def dword(v):
            if v is not None and (type(v) is not int or not 0<=v<=0xffffffff):raise ValueError('Observed DWORD required')
        for v in (self.party_count,self.outer_tick,self.final_tick):dword(v)
        for name in ('feature_ticks','predicate_returns','post_request_ticks','swift_globals'):
            mapping=getattr(self,name)
            for key,value in mapping.items():
                if type(key) is not int:raise ValueError('Raw integer observation key required')
                dword(value)
            object.__setattr__(self,name,MappingProxyType(dict(mapping)))
        for key,value in self.request_returns.items():
            if type(key) is not int or (value is not None and type(value) is not bool):raise ValueError('Independent request normal-return samples required')
        object.__setattr__(self,'request_returns',MappingProxyType(dict(self.request_returns)))
        rows=tuple(tuple(row) for row in self.swift_samples)
        for row in rows:
            if len(row)!=2:raise ValueError('Ordered Swift read samples required')
            for value in row:dword(value)
        object.__setattr__(self,'swift_samples',rows)

@dataclass(frozen=True)
class PartyHelpPlan:
    status:str
    complete:bool
    state:PartyHelpState
    prospective_state:PartyHelpState
    calls:tuple=()
    requests:tuple=()
    writes:tuple=()
    missing:str=''
    next_address:object=None
    native_execution_verified:bool=False
    messages_sent:bool=False

class _Missing(Exception):pass

def plan_party_help(configuration,state,observation):
    if not isinstance(configuration,PartyHelpConfiguration) or not isinstance(state,PartyHelpState) or not isinstance(observation,PartyHelpObservation):
        raise ValueError('Typed party-help config/state/observations required')
    c=configuration;o=observation;times=dict(state.timers);calls=[];requests=[];writes=[]
    def need(v,label):
        if v is None:raise _Missing(label)
        return v
    def tick(v,label):
        calls.append(('005074da',()))
        return need(v,label)
    def elapsed(now,address):
        last=need(times.get(address),'QWORD timer%08x'%address)
        value=(now-last)&0xffffffffffffffff
        return value-(1<<64) if value&(1<<63) else value
    def stamp(address,value):times[address]=value;writes.append((address,value,0))
    def result(status,complete=False,missing=''):
        prospective=PartyHelpState(times)
        return PartyHelpPlan(status,complete,prospective if complete else state,prospective,
            tuple(calls),tuple(requests),tuple(writes),missing,0x459496 if complete else None)
    def swift_predicate():
        root_slot=need(o.swift_globals.get(0x553e7c),'global00553e7c')
        def word(index,address):
            address&=0xffffffff;calls.append(('0045dc44',(address,)))
            if index>=len(o.swift_samples):raise _Missing('Swift read%d DWORD%08x'%(index,address))
            actual,value=o.swift_samples[index]
            if actual!=address:raise ValueError('Swift source address mismatch')
            return need(value,'Swift DWORD return')
        root=word(0,root_slot)
        offset=need(o.swift_globals.get(0x553fe4),'global00553fe4')
        return word(1,root+offset)==0x3f80
    try:
        calls.append(('004645e4',()))
        count=need(o.party_count,'004645e4 DWORD count')
        if (count-(1<<32) if count&0x80000000 else count)<2:return result('party_too_small',True)
        now=tick(o.outer_tick,'outer GetTickCount DWORD')
        if elapsed(now,0x553cb4)<5000:return result('outer_timer_wait',True)
        for flag,text,timer,predicate in ROWS:
            enabled=need(c.flags.get(flag),'field+%x'%flag)
            if type(enabled) is not int or not 0<=enabled<=255:raise ValueError('Raw help flag BYTE required')
            if not enabled:continue
            now=tick(o.feature_ticks.get(flag),'feature%x GetTickCount DWORD'%flag)
            if elapsed(now,timer)<10000:continue
            if predicate is None:match=swift_predicate()
            else:
                calls.append((predicate,()))
                match=need(o.predicate_returns.get(flag),predicate+' EAX')&255!=0
            if not match:continue
            ansi=need(c.ansi_texts.get(text),'observed AnsiString field+%x'%text)
            if type(ansi) is not bytes:raise ValueError('Converted AnsiString bytes required')
            calls.append(('004c9b74',(0x561ef8,2,('ansi',ansi))));requests.append((flag,ansi))
            if o.request_returns.get(flag) is not True:raise _Missing('feature%x 004c9b74 normal return'%flag)
            stamp(timer,tick(o.post_request_ticks.get(flag),'feature%x fresh post-request GetTickCount DWORD'%flag))
        stamp(0x553cb4,tick(o.final_tick,'fresh final GetTickCount DWORD'))
        return result('party_help_planned',True)
    except _Missing as exc:return result('needs_observation',missing=str(exc))
