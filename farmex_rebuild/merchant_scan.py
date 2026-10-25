"""004bf9dc merchant scan route/scheduling replay, without merchant/game IO.

State-changing helper normal returns are independent observations, not ACKs.
The caller supplies consistent vector counts; memory layouts are not dereferenced.
Our active guard prevents calling the native consumer outside a started run.
"""
import math
import itertools
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Optional, Tuple


@dataclass(frozen=True)
class ScanState:
    route_index: int = 0
    last_scan_qword: int = 0
    active: bool = True

    def __post_init__(self):
        if type(self.route_index) is not int or not 0 <= self.route_index <= 0xffffffff:
            raise ValueError('route index must be DWORD')
        if type(self.last_scan_qword) is not int or not 0 <= self.last_scan_qword < 1 << 64:
            raise ValueError('scan timestamp must be raw QWORD')
        if type(self.active) is not bool:
            raise ValueError('active must be bool')


@dataclass(frozen=True)
class ScanSnapshot:
    now_ms: Optional[int] = None
    route_enabled: Optional[bool] = None
    busy_0f: Optional[bool] = None
    pending_count: Optional[int] = None
    route_count: Optional[int] = None
    selected_point_distance: Optional[float] = None
    actor_raw_byte_554020: Optional[int] = None
    collect_return_4bf040: Optional[int] = None
    save_on_finish_0e: Optional[bool] = None
    route_count_after_collect: Optional[int] = None
    post_consume_now_ms: Optional[int] = None
    distance_status_word: Optional[int] = None
    distance_returned: Optional[bool] = None
    move_returned: Optional[bool] = None
    collect_returned: Optional[bool] = None
    consume_returned: Optional[bool] = None
    export_returned: Optional[bool] = None
    stop_returned: Optional[bool] = None

    def __post_init__(self):
        for value in (self.now_ms,self.post_consume_now_ms):
            if value is not None and (type(value) is not int or not 0 <= value <= 0xffffffff):
                raise ValueError('clock must be explicit DWORD or unknown')
        for value in (self.route_enabled, self.busy_0f, self.save_on_finish_0e,self.distance_returned,
                      self.move_returned,self.collect_returned,self.consume_returned,self.export_returned,self.stop_returned):
            if value is not None and type(value) is not bool:
                raise ValueError('bool or unknown required')
        for value in (self.pending_count, self.route_count,self.route_count_after_collect,self.collect_return_4bf040):
            if value is not None and (type(value) is not int or not 0 <= value <= 0xffffffff):
                raise ValueError('DWORD observation or unknown required')
        if self.actor_raw_byte_554020 is not None and (type(self.actor_raw_byte_554020) is not int or not 0<=self.actor_raw_byte_554020<=255):
            raise ValueError('Explicit actor state BYTE required')
        if self.distance_status_word is not None and (type(self.distance_status_word) is not int or not 0<=self.distance_status_word<=65535):
            raise ValueError('Explicit FNSTSW WORD required')
        value = self.selected_point_distance
        if value is not None:
            if type(value) not in (int,float):raise ValueError('Numeric distance or unknown required')
            if self.distance_status_word is None and (not math.isfinite(value) or value<0):
                raise ValueError('Finite nonnegative distance required without explicit FNSTSW')


@dataclass(frozen=True)
class ScanDecision:
    status: str
    state: ScanState
    calls: Tuple[str, ...] = ()
    reason: str = ''
    native_execution_verified: bool = False
    live_compatibility_verified: bool = False


class _Missing(Exception):
    pass


def merchant_scan_step(s: ScanSnapshot, state=ScanState(), *, _observation_reader=None):
    if not isinstance(s, ScanSnapshot) or not isinstance(state, ScanState):
        raise ValueError('typed snapshot/state required')
    st, calls = state, []
    def observation(name):
        return getattr(s,name) if _observation_reader is None else _observation_reader(name)

    def need(value, name):
        if value is None:
            raise _Missing(name)
        return value

    def result(status, reason=''):
        return ScanDecision(status, st, tuple(calls), reason)

    def normal(value,label):
        if value is not True:raise _Missing('normal_return:'+label)

    def consume_pending():
        nonlocal st
        now=need(observation('now_ms'),'pre_consume_GetTickCount')
        delta = (now - st.last_scan_qword) & ((1 << 64) - 1)
        if delta >= 1 << 63:
            delta -= 1 << 64
        if delta < 50:
            return result('waiting', '50ms')
        calls.append('004bf5d0')
        normal(observation('consume_returned'),'004bf5d0')
        post=need(observation('post_consume_now_ms'),'post_consume_GetTickCount')
        st = replace(st, last_scan_qword=post)
        return result('local_step')

    try:
        if not st.active:
            return result('idle')
        if not need(observation('route_enabled'), 'route_enabled'):
            if need(observation('busy_0f'), 'busy:+f'):
                return result('busy')
            if need(observation('pending_count'), 'pending_count') == 0:
                calls.append('004bf040')
                normal(observation('collect_returned'),'004bf040')
                return result('local_step')
            return consume_pending()
        count = need(observation('route_count'), 'route_count')
        if st.route_index >= count:
            #004b9174 builds/throws a bounds exception; it is not a wrap/reset.
            calls.append('004b9174')
            return result('source_bounds_exception')
        normal(observation('distance_returned'),'00460548')
        word=observation('distance_status_word')
        move=(word&0x4500)==0 if word is not None else need(observation('selected_point_distance'),'selected_point_distance')>1.5
        if move:
            calls.append('004646b4')
            normal(observation('move_returned'),'004646b4')
            return result('local_step', 'move_to_route_point')
        if need(observation('actor_raw_byte_554020'), 'actor_raw_byte_554020') != 0 or need(observation('busy_0f'), 'busy:+f'):
            return result('actor_or_busy_gate')
        if need(observation('pending_count'), 'pending_count') != 0:
            return consume_pending()
        calls.append('004bf040')
        normal(observation('collect_returned'),'004bf040')
        if need(observation('collect_return_4bf040'), 'return:004bf040') != 0:
            return result('local_step')
        st = replace(st, route_index=(st.route_index + 1) & 0xffffffff)
        count=need(observation('route_count_after_collect'),'fresh_route_count_after_collect')
        if st.route_index >= count:
            if need(observation('save_on_finish_0e'), 'save_on_finish'):
                calls.append('004b99f8')
                normal(observation('export_returned'),'004b99f8')
            calls.append('004be6dc:stop_completed')
            normal(observation('stop_returned'),'004be6dc')
            st = replace(st, active=False)
            return result('completed')
        return result('local_step', 'next_route_point')
    except _Missing as error:
        return result('needs_observation', str(error))


@dataclass(frozen=True)
class ScanReturnRequest:
    token:tuple
    target:str
    kind:str='normal_return_observation'
    executable_native_command:bool=False


@dataclass(frozen=True)
class ScanFrameResult:
    complete:bool
    terminal:bool
    status:str
    state:ScanState
    decision:object
    pending_return:object=None
    new_return_requests:tuple=()
    new_logical_call_intents:tuple=()
    consumed_observations:object=None
    abort_reason:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


_scan_frame_numbers=itertools.count(1)


class MerchantScanFrame:
    """One source invocation, with demand-only frozen observations.

    Requests ask for return observations, not executable native calls or ABI
    operands. Caller/queue/helper execution and child partial effects are out
    of scope. A fresh source tick needs a fresh frame after terminal return.
    """
    def __init__(self,state=ScanState()):
        if not isinstance(state,ScanState):raise ValueError('Typed initial scan state required')
        self.frame_number=next(_scan_frame_numbers)
        self.initial_state=state;self.state=state;self._cache={};self._requests={}
        self._calls=();self._decision=None;self._terminal=False;self._abort=None;self.last=None

    def _result(self,new_requests=(),new_calls=()):
        p=self._decision;pending=None
        if not self._terminal and p is not None and p.reason.startswith('normal_return:'):
            pending=self._requests[p.reason.split(':',1)[1]]
        status='aborted' if self._abort is not None else (p.status if p is not None else 'not_started')
        complete=self._terminal and self._abort is None and p is not None and p.status!='source_bounds_exception'
        self.last=ScanFrameResult(complete,self._terminal,status,self.state,p,pending,tuple(new_requests),
            tuple(new_calls),MappingProxyType(dict(self._cache)),self._abort)
        return self.last

    def advance(self,snapshot=None):
        snapshot=ScanSnapshot() if snapshot is None else snapshot
        if not isinstance(snapshot,ScanSnapshot):raise ValueError('Typed scan observations required')
        if self._terminal:return self._result()
        def read(name):
            if name in self._cache:return self._cache[name]
            value=getattr(snapshot,name)
            if name.endswith('_returned'):
                if value is True:self._cache[name]=True
            elif value is not None:
                self._cache[name]=value
                # Freeze the scalar fallback choice only once a scalar value
                # was actually consumed. Earlier unknown WORD is not frozen.
                if name=='selected_point_distance':self._cache['distance_status_word']=None
            return value
        p=merchant_scan_step(snapshot,self.initial_state,_observation_reader=read)
        if p.calls[:len(self._calls)]!=self._calls:raise AssertionError('Consumed scan path retracted')
        new_calls=p.calls[len(self._calls):];self._calls=p.calls
        self._decision=p;self.state=p.state;new_requests=[]
        if p.status=='needs_observation' and p.reason.startswith('normal_return:'):
            target=p.reason.split(':',1)[1]
            if target not in self._requests:
                request=ScanReturnRequest((self.frame_number,target),target)
                self._requests[target]=request;new_requests.append(request)
        self._terminal=p.status!='needs_observation'
        return self._result(new_requests,new_calls)

    def abort(self,reason):
        if type(reason) is not str or not reason:raise ValueError('Explicit abort reason required')
        if not self._terminal:self._abort=reason;self._terminal=True
        return self._result()
