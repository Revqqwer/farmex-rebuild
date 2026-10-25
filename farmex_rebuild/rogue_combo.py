"""004db864 source state-machine plans, nested 004db198 replay, no IO.

Clock and raw FPU-status observations are per source step. Helper completion is
explicit. State is a prospective local prefix; callers must not commit an
incomplete plan as a completed invocation. Source EAX on SEH exits is unspecified
here and is never treated as a success result.
"""
from dataclasses import dataclass,field,replace
from typing import Mapping,Optional,Tuple
from rogue_alternate_bow import plan_alternate_bow

def _dword(value):return type(value) is int and 0<=value<=0xffffffff

@dataclass(frozen=True)
class ComboState:
    stage: int = 0                 # 0056fee0
    category: int = 0              # 0056fedc
    start_ms: int = 0              # 0056fee4
    first_ms: int = 0              # 0056feec
    second_ms: int = 0             # 0056fef0
    end_ms: int = 0                # 0056fef4
    pattern_counter: int = 0       # 0054b220

    def __post_init__(self):
        if any(not _dword(v) for v in self.__dict__.values()):raise ValueError('DWORD state fields required')

@dataclass(frozen=True)
class ComboObservation:
    locked_byte: Optional[int] = None
    actor_byte: Optional[int] = None
    actor_float_ah: Optional[int] = None
    byte_562011: Optional[int] = None
    byte_562012: Optional[int] = None
    byte_561ffc: Optional[int] = None
    distance_vs_one_ah: Optional[int] = None
    helper_464564: Optional[int] = None
    actor_state: Optional[int] = None
    interval_ms: Optional[int] = None
    clocks: Mapping[str,Optional[int]] = field(default_factory=dict)
    helper_completed: Mapping[str,Optional[bool]] = field(default_factory=dict)

    def __post_init__(self):
        for value in (self.locked_byte,self.actor_byte,self.actor_float_ah,self.byte_562011,
                      self.byte_562012,self.byte_561ffc,self.distance_vs_one_ah):
            if value is not None and (type(value) is not int or not 0<=value<=255):raise ValueError('BYTE observation required')
        if not isinstance(self.clocks,Mapping) or not isinstance(self.helper_completed,Mapping):raise ValueError('Observation mappings required')
        for value in (self.helper_464564,self.actor_state,self.interval_ms,*self.clocks.values()):
            if value is not None and not _dword(value):raise ValueError('DWORD observation required')
        for value in self.helper_completed.values():
            if value is not None and type(value) is not bool:raise ValueError('Completion bool or unknown required')

@dataclass(frozen=True)
class ComboPlan:
    status: str
    state: ComboState
    complete: bool
    calls: Tuple[Tuple[str,Tuple[int,...]],...] = ()
    local_writes: Tuple[Tuple[str,int],...] = ()
    selector: object = None
    reason: str = ''
    independently_verified: bool = False

class _Missing(Exception):pass

def plan_rogue_combo(state,observation,*,selector_snapshot=None,selector_ranges=None,selector_observation=None):
    if not isinstance(state,ComboState) or not isinstance(observation,ComboObservation):raise ValueError('Typed combo state/observation required')
    st=state;o=observation;calls=[];writes=[];selection=None
    addresses=dict(stage='0056fee0',category='0056fedc',start_ms='0056fee4',first_ms='0056feec',
                   second_ms='0056fef0',end_ms='0056fef4',pattern_counter='0054b220')
    def need(value,key):
        if value is None:raise _Missing(key)
        return value
    def write(name,value):
        nonlocal st
        st=replace(st,**{name:value});writes.append((addresses[name],value))
    def finish(status):return ComboPlan(status,st,True,tuple(calls),tuple(writes),selection)
    def combo():
        return bool(need(o.byte_562011,'byte:00562011')) or bool(need(o.byte_562012,'byte:00562012'))
    def clock(key):return need(o.clocks.get(key),'clock:'+key)
    def elapsed(key,then):return (clock(key)-then)&0xffffffff
    def helper(key,arg):
        calls.append(('00465f30',(arg,)))
        if need(o.helper_completed.get(key),'completed:'+key) is not True:raise _Missing('completed:'+key)
    def select(execute):
        nonlocal selection
        calls.append(('004db198',(execute,)))
        if selector_snapshot is None or selector_ranges is None or selector_observation is None:raise _Missing('selector_inputs')
        selection=plan_alternate_bow(selector_snapshot,selector_ranges,replace(selector_observation,execute_byte=execute))
        writes.extend(selection.local_writes)
        if selection.source_return is None:raise _Missing('selector:'+selection.reason)
        return selection.source_return
    try:
        # Coordinate/target reads precede these gates in the binary, but their
        # unused return values and IO side effects are not simulated here.
        if need(o.locked_byte,'byte:00561f7e'):
            write('stage',0);return finish('reset_locked')
        if need(o.actor_byte,'actor_byte') or need(o.actor_float_ah,'actor_float_ah') & 0x45 == 0:
            write('stage',0);return finish('reset_actor_gate')
        if st.stage==0:
            category=select(1);write('category',category)
            if category>0:
                write('start_ms',clock('start'));write('stage',1)
            return finish('selection_attempt')
        if st.stage==1:
            delay=0
            if combo():
                calls.append(('00464564',()))
                delay=650 if need(o.helper_464564,'00464564:EAX') else 460
            if elapsed('wait1',st.start_ms)<delay:return finish('wait_start')
            write('stage',3);return finish('advance')
        if st.stage==3:
            if not combo():
                write('stage',6);return finish('skip_pattern')
            if st.category==3 and need(o.byte_561ffc,'byte:00561ffc'):
                helper('pattern',2);helper('reset',0)
                write('stage',6);return finish('ordinary_pattern')
            a=need(o.byte_562011,'byte:00562011');b=need(o.byte_562012,'byte:00562012')
            arg=1 if a and not b else 0
            if not a and b:
                # TEST AH,5 / JP: parity even selects1, parity odd selects2.
                masked=need(o.distance_vs_one_ah,'distance_vs_one_ah') & 5
                arg=1 if bin(masked).count('1')%2==0 else 2
            if a and b:
                counter=(st.pattern_counter+1)&0xffffffff
                write('pattern_counter',counter);arg=1 if counter%2==0 else 2
                if counter==10:write('pattern_counter',0)
            helper('first',arg)
            write('stage',4);write('first_ms',clock('stage3'))
            return finish('pattern_started')
        if st.stage==4:
            if combo():
                if elapsed('wait4',st.first_ms)<5:return finish('wait_first')
                helper('second',0);write('second_ms',clock('after4'))
            write('stage',5);return finish('advance')
        if st.stage==5:
            if combo() and elapsed('wait5',st.second_ms)<5:return finish('wait_second')
            write('stage',6);return finish('advance')
        if st.stage==6:
            if combo():
                category=select(0)
                delay=1280 if category==3 else 1000 if category==st.category else 100
                if elapsed('wait6',st.start_ms)<delay:return finish('wait_reselection')
                write('end_ms',clock('after6'))
            else:
                if need(o.actor_state,'actor_state')==6:return finish('wait_actor_state')
                write('end_ms',clock('noncombo6'))
            write('stage',7);return finish('advance')
        if st.stage==7:
            if elapsed('wait7',st.end_ms)<need(o.interval_ms,'interval_ms'):return finish('wait_interval')
            write('stage',0);return finish('cycle_complete')
        return finish('unknown_stage_unchanged')
    except _Missing as exc:
        return ComboPlan('needs_observation',st,False,tuple(calls),tuple(writes),selection,str(exc))
