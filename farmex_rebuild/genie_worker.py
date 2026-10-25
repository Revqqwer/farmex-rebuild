"""0045a05c normal prefix + explicit Notice tail; no game effects executed."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from notice_genie_window import NoticeGenieFrame,NoticeGenieObservation,signed
from genie_getters import GenieGetterPlan,GetterBindings,retain_getter_snapshot
from genie_recovery import GenieRecoveryObservation,GenieRecoveryFrame
from action_queue import QueueState

GETTER_HELPERS={'initial_remaining':'004631e8','always_state':'004631c8','always_remaining':'004631e8','general_remaining':'004631e8'}

@dataclass(frozen=True)
class GenieWorkerObservation:
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    getter_executions:object=field(default_factory=dict)
    recovery_observation:object=None
    def __post_init__(self):
        values=dict(self.values);returns=dict(self.normal_returns)
        for label,value in values.items():
            bits=8 if label.endswith('_byte') else 32
            if type(value) is not int or not 0<=value<1<<bits:raise ValueError('Raw general-Genie observation required')
        if any(type(value) is not bool for value in returns.values()):raise ValueError('Separate Genie helper normal receipts required')
        object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(returns))
        getters=dict(self.getter_executions)
        if any(not isinstance(v,GenieGetterPlan) for v in getters.values()):raise ValueError('Typed getter child plans required')
        object.__setattr__(self,'getter_executions',MappingProxyType(getters))
        if self.recovery_observation is not None and not isinstance(self.recovery_observation,GenieRecoveryObservation):raise ValueError('Typed recovery child observation required')

@dataclass(frozen=True)
class GeniePrefixPlan:
    complete:bool
    status:str
    general_stop_flag_2d:object=None
    calls:tuple=()
    stores:tuple=()
    steps:tuple=()
    missing:str=''
    needed:object=None
    native_execution_verified:bool=False
    getter_executions:tuple=()
    recovery_execution:object=None

class _Missing(Exception):
    def __init__(self,kind,label):self.needed=(kind,label);super().__init__('bound getter: '+label if kind=='getter' else label+(' normal return' if kind=='normal' else ' value'))

def plan_genie_prefix(o,*,_recovery=None):
    if not isinstance(o,GenieWorkerObservation):raise ValueError('Typed general-Genie observations required')
    calls=[];stores=[];steps=[];flag=None;bindings=GetterBindings(o.getter_executions);recovery=None
    def result(status,error=None):return GeniePrefixPlan(error is None,status,flag,tuple(calls),tuple(stores),tuple(steps),'' if error is None else str(error),None if error is None else error.needed,getter_executions=tuple(bindings.used.items()),recovery_execution=recovery)
    def value(label):
        steps.append(('value',label))
        if label not in o.values:raise _Missing('value',label)
        return o.values[label]
    def call(label,helper,pushes=()):
        calls.append((helper,pushes,label));steps.append(('normal',label))
        if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
    def store(address,width,value):stores.append((address,width,value))
    def getter(label):
        gap=bindings.enter(label,GETTER_HELPERS[label])
        if gap is not None:raise _Missing('getter',label)
        call(label,GETTER_HELPERS[label]);eax=value(label+'_eax');bindings.check_eax(label,eax);return eax
    def tick(label):call(label,'GetTickCount');return value(label)
    def elapsed(prefix):
        now=tick(prefix+'_tick');lo=value(prefix+'_low');hi=value(prefix+'_high')
        delta=signed((now-((hi<<32)|lo))&0xffffffffffffffff,64)
        steps.append(('signed_QWORD_elapsed',prefix,delta));return delta
    def stamp(prefix,low):
        now=tick(prefix+'_post_tick');store(low,4,now);store(low+4,4,0)
    def finish(status):call('epilogue','source_normal_epilogue');return result(status)
    def stop_town(prefix):
        call(prefix+'_bot_stop','0040ae0c',(0,0x561f34));call(prefix+'_town','00465678')
        return finish('early_stop_town')
    def alarm(label,literal):
        steps.append(('opaque_alarm_literal',literal,b'Default'))
        call(label,'opaque_alarm_string_and_cleanup_span')
    try:
        call('frame_setup','opaque_504c08')
        if value('initial_bb_byte') or value('initial_bc_byte') or value('initial_ba_byte'):
            if getter('initial_remaining')&255==0:
                if value('recovery_ba_byte'):
                    if elapsed('recovery_probe')>=5000:
                        if _recovery is not None:recovery=_recovery()
                        elif o.recovery_observation is not None:recovery=GenieRecoveryFrame(0x561ef8).advance(o.recovery_observation)
                        if recovery is not None and not recovery.complete:raise _Missing('recovery','recovery_probe')
                        call('recovery_probe','004ca588',(0x561ef8,));eax=value('recovery_probe_eax')
                        if recovery is not None:
                            if eax&255!=recovery.return_low_al:raise ValueError('Recovery parent AL differs from completed child')
                            if recovery.source_return_eax is not None and eax!=recovery.source_return_eax:raise ValueError('Recovery parent EAX differs from known full child return')
                        store(0x553cf0,1,eax&255)
                        stamp('recovery_probe',0x553cf4)
                    elif value('cached_probe_byte')==0:
                        if value('retry_bc_byte'):alarm('retry_alarm_span',0x521483)
                        if value('retry_bb_byte'):return stop_town('retry')
                else:
                    if value('empty_bc_byte'):alarm('empty_alarm_span',0x52148b)
                    if value('empty_bb_byte'):return stop_town('empty')
        flag=0 #Source local2d/2e zero stores dominate Notice entry.
        if value('always_b8_byte'):
            if getter('always_state')&255==0 and elapsed('always_cooldown')>=1000:
                if getter('always_remaining')&255:
                    call('always_start','00466cc4',(1,));stamp('always',0x553cfc)
            return finish('early_always_on')
        if value('general_enabled_byte')==0:flag=1
        elif value('general_mode_dword')!=2:flag=1
        elif value('general_genie_byte')==0:flag=1
        elif value('general_active_byte'):
            if value('general_no_attack_byte'):store(0x561fa8,1,1)
            if elapsed('general_cooldown')>=1000:
                if getter('general_remaining')&255:
                    call('general_start','00466cc4',(1,));stamp('general',0x553cfc)
                    store(0x561fa4,4,tick('general_activity_tick'))
                    return finish('early_general_start')
        elif value('resume_delay_byte')==0:flag=1
        else:
            delta=elapsed('resume_delay');threshold=signed((value('resume_seconds_dword')*1000)&0xffffffff,32)
            steps.append(('signed_low32_second_threshold',threshold))
            if delta>threshold:flag=1
        return result('notice_entry_reached')
    except _Missing as error:return result('needs_observation',error)

class GeniePrefixFrame:
    def __init__(self,queue=None):
        self.observation=GenieWorkerObservation();self.final=None;self.recovery_frame=None
        self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own Genie queue required')
    def advance(self,o):
        if not isinstance(o,GenieWorkerObservation):raise ValueError('Typed general-Genie observations required')
        if self.final is not None:return self.final
        def recovery():
            if self.recovery_frame is None:
                if self.observation.normal_returns.get('recovery_probe') is True:
                    if o.recovery_observation is not None:raise ValueError('Cannot retroactively bind consumed recovery call')
                    return None
                if o.recovery_observation is None:return None
                self.recovery_frame=GenieRecoveryFrame(0x561ef8,self.queue)
            child=self.recovery_frame.advance(o.recovery_observation or GenieRecoveryObservation())
            self.queue=self.recovery_frame.queue
            return child
        for _ in range(64):
            p=plan_genie_prefix(self.observation,_recovery=recovery)
            if p.complete:self.final=p;return p
            kind,label=p.needed
            key=label[:-4] if kind=='value' and label.endswith('_eax') else label
            if key in GETTER_HELPERS and key in o.getter_executions:
                child=retain_getter_snapshot(self.observation.getter_executions.get(key),o.getter_executions[key])
                candidate=replace(self.observation,getter_executions={**self.observation.getter_executions,key:child})
                p=plan_genie_prefix(candidate,_recovery=recovery)
                self.observation=candidate
                if p.complete:self.final=p;return p
                kind,label=p.needed
            if kind in ('getter','recovery'):return p
            if kind=='normal':
                if o.normal_returns.get(label) is not True:return p
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
            else:
                if label not in o.values:return p
                self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
        raise ValueError('Genie prefix exceeded source observation budget')

@dataclass(frozen=True)
class GenieWorkerPlan:
    complete:bool
    prefix:GeniePrefixPlan
    notice:object=None
    calls:tuple=()
    stores:tuple=()
    missing:str=''
    native_execution_verified:bool=False
    Genie_effect_verified:bool=False
    whole_worker_verified:bool=False
    queue:object=None

class GenieWorkerFrame:
    def __init__(self,queue=None):
        self.prefix=GeniePrefixFrame(queue);self.queue=self.prefix.queue;self.notice=NoticeGenieFrame();self.final=None
    def advance(self,o=None,notice=None):
        if self.final is not None:return self.final
        p=self.prefix.advance(GenieWorkerObservation() if o is None else o)
        self.queue=self.prefix.queue
        if not p.complete:return GenieWorkerPlan(False,p,calls=p.calls,stores=p.stores,missing=p.missing,queue=self.queue)
        if p.status!='notice_entry_reached':
            self.final=GenieWorkerPlan(True,p,calls=p.calls,stores=p.stores,queue=self.queue);return self.final
        n=NoticeGenieObservation() if notice is None else notice
        if not isinstance(n,NoticeGenieObservation):raise ValueError('Reached typed Notice tail required')
        if 'other_stop_flag_2d' in n.values and n.values['other_stop_flag_2d']!=p.general_stop_flag_2d:
            raise ValueError('Notice general stop flag differs from bound source prefix')
        if p.getter_executions:
            child=p.getter_executions[0][1]
            self.notice.expected_getter_identity=(child.module_sha256,child.profile)
        q=self.notice.advance(replace(n,values={**n.values,'other_stop_flag_2d':p.general_stop_flag_2d}))
        result=GenieWorkerPlan(q.complete,p,q,p.calls+q.calls,p.stores+q.stores,q.missing,queue=self.queue)
        if q.complete:self.final=result
        return result
