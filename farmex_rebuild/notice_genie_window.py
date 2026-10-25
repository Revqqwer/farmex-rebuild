"""Explicitly reached45a38c window; inert calls/stores, no detector or Genie."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from genie_getters import GenieGetterPlan,GetterBindings,retain_getter_snapshot

GETTER_HELPERS={'start_state':'004631c8','remaining':'004631e8','stop_state':'004631c8'}

BYTE_LABELS={'enabled_byte','no_attack_byte','other_stop_flag_2d'}
def signed(value,bits):return value-(1<<bits) if value&(1<<(bits-1)) else value

@dataclass(frozen=True)
class NoticeGenieObservation:
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    getter_executions:object=field(default_factory=dict)
    def __post_init__(self):
        values=dict(self.values);returns=dict(self.normal_returns)
        for key,v in values.items():
            if type(v) is not int or not 0<=v<1<<(8 if key in BYTE_LABELS else 32):raise ValueError('Raw source notice-window observation required')
        if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate notice-window helper normal receipts required')
        object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(returns))
        getters=dict(self.getter_executions)
        if any(not isinstance(v,GenieGetterPlan) for v in getters.values()):raise ValueError('Typed getter child plans required')
        object.__setattr__(self,'getter_executions',MappingProxyType(getters))

@dataclass(frozen=True)
class NoticeGeniePlan:
    complete:bool
    notice_done_local_2e:int
    calls:tuple=()
    stores:tuple=()
    steps:tuple=()
    missing:str=''
    needed:object=None
    source_entry_assumed:bool=True
    whole_worker_verified:bool=False
    native_execution_verified:bool=False
    Genie_effect_verified:bool=False
    getter_executions:tuple=()

class _Missing(Exception):
    def __init__(self,kind,label):self.needed=(kind,label);super().__init__('bound getter: '+label if kind=='getter' else label+(' normal return' if kind=='normal' else ' value'))

def plan_notice_genie_window(o,*,expected_getter_identity=None):
    if not isinstance(o,NoticeGenieObservation):raise ValueError('Typed notice-window observations required')
    done=0;calls=[];stores=[];steps=[];bindings=GetterBindings(o.getter_executions,expected_getter_identity)
    def value(label):
        steps.append(('value',label))
        if label not in o.values:raise _Missing('value',label)
        return o.values[label]
    def call(label,helper,pushes=()):
        calls.append((helper,pushes,label));steps.append(('normal',label))
        if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
    def store(address,width,v):stores.append((address,width,v))
    def getter(label):
        gap=bindings.enter(label,GETTER_HELPERS[label])
        if gap is not None:raise _Missing('getter',label)
        call(label,GETTER_HELPERS[label]);eax=value(label+'_eax');bindings.check_eax(label,eax);return eax
    def tick(label):call(label,'GetTickCount');return value(label)
    def elapsed(prefix,tick_label):
        now=tick(tick_label);lo=value(prefix+'_low');hi=value(prefix+'_high')
        bits=(now-((hi<<32)|lo))&0xffffffffffffffff
        delta=signed(bits,64);steps.append(('signed_QWORD_elapsed',prefix,bits,delta));return delta
    def stamp(label):
        now=tick(label);store(0x553cfc,4,now);store(0x553d00,4,0)
    def finish():
        if done and value('other_stop_flag_2d'):
            state=getter('stop_state')&255
            if state==1 and elapsed('stop_cooldown_stamp','stop_cooldown_tick')>=1000:
                call('genie_stop','00466cc4',(0,));stamp('stop_post_tick')
            store(0x561fa8,1,0)
        call('epilogue','source_normal_epilogue')
    try:
        if value('enabled_byte')==0:done=1
        elif value('mode_dword')!=3:done=1
        else:
            high=value('presence_stamp_high')
            present=(value('presence_stamp_low')>0) if high==0 else signed(high,32)>0
            if not present:done=1
            else:
                delta=elapsed('window_stamp','window_tick')
                threshold=signed((value('minutes_dword')*60000)&0xffffffff,32)
                steps.append(('signed_low32_minute_threshold',threshold))
                if delta>=threshold:done=1
                else:
                    if value('no_attack_byte'):store(0x561fa8,1,1)
                    if getter('start_state')&255==0:
                        if elapsed('start_cooldown_stamp','start_cooldown_tick')>=1000:
                            if getter('remaining')&255:
                                call('genie_start','00466cc4',(1,));stamp('start_post_tick')
        finish()
        return NoticeGeniePlan(True,done,tuple(calls),tuple(stores),tuple(steps),getter_executions=tuple(bindings.used.items()))
    except _Missing as error:
        return NoticeGeniePlan(False,done,tuple(calls),tuple(stores),tuple(steps),str(error),error.needed,getter_executions=tuple(bindings.used.items()))

class NoticeGenieFrame:
    def __init__(self,*,expected_getter_identity=None):self.observation=NoticeGenieObservation();self.final=None;self.expected_getter_identity=expected_getter_identity
    def advance(self,o):
        if not isinstance(o,NoticeGenieObservation):raise ValueError('Typed notice-window observation required')
        if self.final is not None:return self.final
        for _ in range(48):
            p=plan_notice_genie_window(self.observation,expected_getter_identity=self.expected_getter_identity)
            if p.complete:self.final=p;return p
            kind,label=p.needed
            key=label[:-4] if kind=='value' and label.endswith('_eax') else label
            if key in GETTER_HELPERS and key in o.getter_executions:
                child=retain_getter_snapshot(self.observation.getter_executions.get(key),o.getter_executions[key])
                candidate=replace(self.observation,getter_executions={**self.observation.getter_executions,key:child})
                p=plan_notice_genie_window(candidate,expected_getter_identity=self.expected_getter_identity)
                self.observation=candidate
                if p.complete:self.final=p;return p
                kind,label=p.needed
            if kind=='getter':return p
            if kind=='normal':
                if o.normal_returns.get(label) is not True:return p
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
            else:
                if label not in o.values:return p
                self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
        raise ValueError('Notice window exceeded source prefix budget')
