"""One scheduler invocation composed with owned collection/consume children.

Pure captures and an inert own packet queue only. Parent normal returns are
independent receipts, never inferred from successful child projections. This
is not a native dispatcher, game sender, timer, or full helper/SEH certificate.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState
from direct_chat_packets import QueueAttempt
from event_packets import EventEnqueueFrame
from merchant_scan import MerchantScanFrame,ScanSnapshot,ScanState
from merchant_scan_collection import (
    MerchantCollectionState,MerchantCollectionFrame,consume_merchant_head,
)


@dataclass(frozen=True)
class ScanConsumeObservation:
    normal_enabled:object=None
    buy_enabled:object=None
    client_variant:object=None
    queue_count_recheck:object=None
    normal_returns:object=field(default_factory=dict)
    attempt:QueueAttempt=field(default_factory=QueueAttempt)

    def __post_init__(self):
        for v in (self.normal_enabled,self.buy_enabled):
            if v is not None and type(v) is not bool:raise ValueError('Explicit kind boolean required')
        if self.client_variant is not None and (type(self.client_variant) is not int or not 0<=self.client_variant<=255):raise ValueError('Variant BYTE required')
        if self.queue_count_recheck is not None and (type(self.queue_count_recheck) is not int or self.queue_count_recheck<0):raise ValueError('Nonnegative queue count required')
        returns=dict(self.normal_returns)
        if any(type(v) is not bool for v in returns.values()):raise ValueError('Independent normal receipts required')
        if not isinstance(self.attempt,QueueAttempt):raise ValueError('Own enqueue attempt required')
        object.__setattr__(self,'normal_returns',MappingProxyType(returns))


@dataclass(frozen=True)
class ScanConsumeResult:
    complete:bool
    terminal:bool
    status:str
    state:MerchantCollectionState
    queue:QueueState
    plan:object=None
    needed:object=None
    completed_boundaries:tuple=()
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class MerchantConsumeFrame:
    """Owned FIFO prefix with explicit source-boundary receipts.

    target_write covers the external pointer/read/write chain as a boundary,
    not a verification of its operands. Packet copy and vector erase helpers
    also require independent receipts. The local EventEnqueueFrame may append
    before its normal receipt; retrying never appends a second copy.
    """
    def __init__(self,state=MerchantCollectionState(),queue=None):
        if not isinstance(state,MerchantCollectionState):raise ValueError('Own collection state required')
        self.initial_state=state;self.state=state
        self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own packet queue required')
        self.values={};self.normals=[];self.plan=None;self.enqueue=None;self.final=None

    def advance(self,o=None):
        o=ScanConsumeObservation() if o is None else o
        if not isinstance(o,ScanConsumeObservation):raise ValueError('Typed consume observations required')
        if self.final is not None:return self.final
        def result(status,needed=None,terminal=False):
            return ScanConsumeResult(terminal and status!='source_bounds_exception',terminal,
                status,self.state,self.queue,self.plan,needed,tuple(self.normals))
        def normal(label):
            if label in self.normals:return True
            if o.normal_returns.get(label) is not True:return False
            self.normals.append(label);return True
        def value(name):
            if name not in self.values:
                v=getattr(o,name)
                if v is not None:self.values[name]=v
            return self.values.get(name)
        if self.plan is None:
            if not self.initial_state.queue:
                self.final=result('queue_empty',terminal=True);return self.final
            if 'queue_count_recheck' not in self.values:
                self.values['queue_count_recheck']=(len(self.initial_state.queue)
                    if o.queue_count_recheck is None else o.queue_count_recheck)
            count=self.values['queue_count_recheck']
            if count==0:
                self.final=result('source_bounds_exception',terminal=True);return self.final
            if not normal('head_capture'):return result('needs_observation',('normal','head_capture'))
            r=self.initial_state.queue[0]
            key='buy_enabled' if r.buy_flag else 'normal_enabled'
            enabled=value(key)
            if enabled is None:return result('needs_observation',('value',key))
            variant=value('client_variant') if enabled else None
            if enabled and variant is None:return result('needs_observation',('value','client_variant'))
            self.plan=consume_merchant_head(self.initial_state,
                enabled if not r.buy_flag else None,enabled if r.buy_flag else None,variant,count)
        if self.plan.status=='local_request_plan':
            if not normal('target_write'):return result('needs_observation',('normal','target_write'))
            if not normal('packet_copy'):return result('needs_observation',('normal','packet_copy'))
            if self.enqueue is None:self.enqueue=EventEnqueueFrame(self.plan.request_bytes,0,self.queue)
            child=self.enqueue.advance(o.attempt);self.queue=child.queue
            if not child.complete:return result('needs_observation',('enqueue',child.needed))
            # Source sets +f after enqueue returns, before vector erase.
            self.state=replace(self.state,awaiting_merchant_reply=True)
        for label in ('erase_iterator','erase_move','erase_tail'):
            if not normal(label):return result('needs_observation',('normal',label))
        # Source decrements end only after erase-tail helper normal return.
        self.state=replace(self.state,queue=self.initial_state.queue[1:])
        if not normal('iterator_cleanup'):return result('needs_observation',('normal','iterator_cleanup'))
        self.final=result('own_consume_projected',terminal=True)
        return self.final


@dataclass(frozen=True)
class ScanPipelineResult:
    complete:bool
    terminal:bool
    status:str
    scheduler:object
    collection:MerchantCollectionState
    packet_queue:QueueState
    child:object=None
    needed:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class MerchantScanPipeline:
    """One owned invocation; a new timer tick needs a new pipeline instance.

    Pending count/busy are read from the immutable own collection at entry.
    Collection EAX is supplied by its completed child model. Other scheduler
    values and every parent normal return remain explicit caller observations.
    """
    def __init__(self,state=ScanState(),collection=MerchantCollectionState(),queue=None):
        if not isinstance(collection,MerchantCollectionState):raise ValueError('Own collection state required')
        self.parent=MerchantScanFrame(state);self.collection=collection
        self.initial_collection=collection;self.packet_queue=QueueState() if queue is None else queue
        if not isinstance(self.packet_queue,QueueState):raise ValueError('Own packet queue required')
        self.child=None;self.child_target=None;self.child_result=None;self.last=None

    def _result(self,parent,status=None,needed=None):
        self.last=ScanPipelineResult(parent.complete,parent.terminal,status or parent.status,
            parent,self.collection,self.packet_queue,self.child_result,needed)
        return self.last

    def advance(self,snapshot=None,*,probes=None,normal_enabled=None,buy_enabled=None,consume=None):
        snapshot=ScanSnapshot() if snapshot is None else snapshot
        if not isinstance(snapshot,ScanSnapshot):raise ValueError('Typed scheduler observations required')
        if consume is not None and not isinstance(consume,ScanConsumeObservation):raise ValueError('Typed consume observations required')
        if self.last is not None and self.last.terminal:return self.last
        count=len(self.initial_collection.queue);busy=self.initial_collection.awaiting_merchant_reply
        if snapshot.pending_count is not None and snapshot.pending_count!=count:raise ValueError('Pending count conflicts with own entry collection')
        if snapshot.busy_0f is not None and snapshot.busy_0f!=busy:raise ValueError('Busy flag conflicts with own entry collection')
        # Never let a supplied parent return bypass the child projection.
        s=replace(snapshot,pending_count=count,busy_0f=busy,collect_returned=None,
            collect_return_4bf040=None,consume_returned=None)
        parent=self.parent.advance(s)
        if parent.terminal:return self._result(parent)
        pending=parent.pending_return
        if pending is None or pending.target not in ('004bf040','004bf5d0'):
            return self._result(parent,needed=parent.decision.reason)
        target=pending.target
        if self.child is None:
            self.child_target=target
            self.child=(MerchantCollectionFrame(self.collection) if target=='004bf040'
                else MerchantConsumeFrame(self.collection,self.packet_queue))
        if target!=self.child_target:raise AssertionError('Unexpected child replacement')
        if target=='004bf040':
            self.child_result=self.child.advance(probes,normal_enabled,buy_enabled)
            self.collection=self.child_result.state
            if self.child_result.status!='collected':
                return self._result(parent,'needs_child_observation',self.child_result.reason)
            eax=self.child_result.collected_count
            if snapshot.collect_return_4bf040 is not None and snapshot.collect_return_4bf040!=eax:
                raise ValueError('Observed collection EAX conflicts with child result')
            if snapshot.collect_returned is not True:
                return self._result(parent,'needs_parent_return',pending)
            parent=self.parent.advance(replace(s,collect_returned=True,collect_return_4bf040=eax))
        else:
            self.child_result=self.child.advance(consume)
            self.collection=self.child_result.state;self.packet_queue=self.child_result.queue
            if not self.child_result.complete:
                if self.child_result.terminal:
                    parent=self.parent.abort('consume child: '+self.child_result.status)
                    return self._result(parent,'child_failed',self.child_result.status)
                return self._result(parent,'needs_child_observation',self.child_result.needed)
            if snapshot.consume_returned is not True:
                return self._result(parent,'needs_parent_return',pending)
            parent=self.parent.advance(replace(s,consume_returned=True))
        return self._result(parent,needed=None if parent.terminal else parent.decision.reason)

    def abort(self,reason):
        if self.last is not None and self.last.terminal:return self.last
        if isinstance(self.child,MerchantCollectionFrame):self.child_result=self.child.abort(reason)
        return self._result(self.parent.abort(reason),'aborted',reason)
