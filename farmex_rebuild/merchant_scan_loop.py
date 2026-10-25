"""Owned scan lifecycle and single-threaded timer adapter; no game acquisition.

The timer cadence is an own UI policy, not a recovered source timer period.
Capture providers still supply independent helper returns and actor observations.
Only newly appended child records are published into the latest shared queue,
with fresh own IDs, so interleaved Flood/PM appends are preserved.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState,publish_appended_records
from merchant_scan import ScanState,ScanSnapshot
from merchant_scan_control import ScanControlState
from merchant_scan_collection import MerchantCollectionState,MerchantProbe
from merchant_scan_pipeline import MerchantScanPipeline,ScanConsumeObservation
from flood_runtime import raw_tick
from merchant_reply import MerchantReplyState
from merchant_scan_reply_frame import MerchantScanReplyFrame,ScanReplyObservation

OWN_TIMER_PERIOD_MS=100


@dataclass(frozen=True)
class ScanLoopInput:
    snapshot:ScanSnapshot=field(default_factory=ScanSnapshot)
    probes:object=field(default_factory=dict)
    consume:object=None
    reply:object=None
    def __post_init__(self):
        if not isinstance(self.snapshot,ScanSnapshot):raise ValueError('Typed scan snapshot required')
        probes=dict(self.probes)
        if any(type(k) is not int or not 0<=k<=5000 or not isinstance(v,MerchantProbe) for k,v in probes.items()):raise ValueError('Typed indexed merchant probes required')
        if self.consume is not None and not isinstance(self.consume,ScanConsumeObservation):raise ValueError('Typed consume observation required')
        if self.reply is not None and not isinstance(self.reply,ScanReplyObservation):raise ValueError('Typed reply observation required')
        object.__setattr__(self,'probes',MappingProxyType(probes))


@dataclass(frozen=True)
class ScanLoopContext:
    generation:int
    control:ScanControlState
    state:ScanState
    collection:MerchantCollectionState
    queue:QueueState
    pending:object=None
    reply:object=None


@dataclass(frozen=True)
class PendingScanReply:
    ticket:tuple
    payload:bytes
    pending:object=None


@dataclass(frozen=True)
class ScanLoopResult:
    status:str
    active:bool
    control:ScanControlState
    queue:QueueState
    invocation:object=None
    published_record_ids:tuple=()
    error:object=None
    added_records:tuple=()
    reply:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class OwnedMerchantScanLoop:
    def __init__(self):
        self.state=ScanState(active=False);self.collection=MerchantCollectionState()
        self.generation=0;self.pipeline=None;self._published=0;self.last=None
        self._replies=[];self._reply_number=0;self._reply_frame=None
        self._reply_queue_published=0;self._reply_records_published=0;self._reply_last=None

    def _clear_replies(self,reason):
        if self._reply_frame is not None:self._reply_frame.abort(reason)
        self._replies=[];self._reply_frame=None;self._reply_last=None
        self._reply_queue_published=0;self._reply_records_published=0

    def enqueue_reply(self,payload):
        if type(payload) is not bytes:raise ValueError('Immutable captured reply bytes required')
        if not self.state.active:return None
        self._reply_number+=1
        request=PendingScanReply((self.generation,self._reply_number),payload)
        self._replies.append(request)
        return request.ticket

    def restart(self,control):
        if not isinstance(control,ScanControlState):raise ValueError('Typed own scan control required')
        collection=MerchantCollectionState(control.vector_58,control.vector_78,bool(control.busy_byte_0f))
        if self.pipeline is not None:self.pipeline.abort('own_scan_restart')
        self._clear_replies('own_scan_restart')
        self.generation+=1;self.pipeline=None;self._published=0;self.last=None
        self.state=ScanState(control.route_index_dword,self.state.last_scan_qword,bool(control.active_byte))
        self.collection=collection

    def stop(self,reason='own_scan_stop'):
        if type(reason) is not str or not reason:raise ValueError('Explicit stop reason required')
        if self.pipeline is not None:self.pipeline.abort(reason)
        self._clear_replies(reason)
        self.generation+=1;self.pipeline=None;self._published=0
        self.state=replace(self.state,active=False)
        self.collection=replace(self.collection,awaiting_merchant_reply=False)

    def context(self,control,queue):
        if not isinstance(control,ScanControlState) or not isinstance(queue,QueueState):raise ValueError('Typed own control/queue required')
        reply=None
        if self.pipeline is None and self._replies:
            reply=replace(self._replies[0],pending=self._reply_last)
        return ScanLoopContext(self.generation,control,self.state,self.collection,queue,
            None if self.pipeline is None else self.pipeline.last,reply)

    @staticmethod
    def _publish(queue,records,published):
        return publish_appended_records(queue,records,published)

    def _advance_reply(self,control,queue,observation):
        if self._reply_frame is None:
            self._reply_frame=MerchantScanReplyFrame(self._replies[0].payload,
                MerchantReplyState(scan_pending_byte=int(self.collection.awaiting_merchant_reply)),queue)
            self._reply_queue_published=len(queue.records);self._reply_records_published=0
        p=self._reply_frame.advance(observation);self._reply_last=p
        queue,ids,self._reply_queue_published=self._publish(queue,p.queue.records,self._reply_queue_published)
        added=tuple(r.display for r in p.records[self._reply_records_published:])
        self._reply_records_published=len(p.records)
        self.collection=replace(self.collection,awaiting_merchant_reply=bool(p.state.scan_pending_byte))
        control=replace(self._control(control),result_records=control.result_records+added)
        status='reply_'+p.status
        if p.terminal:
            self._replies.pop(0);self._reply_frame=None;self._reply_last=None
            self._reply_queue_published=0;self._reply_records_published=0
            # A malformed supplied packet retains busy and scanning. It is
            # neither fabricated into success nor a reason to discard later
            # queued replies. This is an explicit owned bounded-read policy.
        self.last=ScanLoopResult(status,self.state.active,control,queue,
            published_record_ids=ids,added_records=added,reply=p)
        return self.last

    def _control(self,control):
        return replace(control,active_byte=int(self.state.active),
            busy_byte_0f=int(self.collection.awaiting_merchant_reply),
            route_index_dword=self.state.route_index,
            vector_58=self.collection.queue,vector_78=self.collection.visited_ids)

    def advance(self,control,queue,inputs=None,*,clock):
        if not isinstance(control,ScanControlState) or not isinstance(queue,QueueState):raise ValueError('Typed own control/queue required')
        inputs=ScanLoopInput() if inputs is None else inputs
        if not isinstance(inputs,ScanLoopInput) or not callable(clock):raise ValueError('Typed captures and own clock required')
        if not self.state.active:
            self.last=ScanLoopResult('inactive',False,self._control(control),queue)
            return self.last
        # Own single-thread policy: replies wait for an in-flight scheduler
        # invocation to return, then are processed FIFO before the next tick.
        # This deliberately does not model native hook/thread races.
        if self.pipeline is None and self._replies:
            return self._advance_reply(control,queue,inputs.reply)
        if self.pipeline is None:
            self.pipeline=MerchantScanPipeline(self.state,self.collection,queue)
            self._published=len(queue.records)
        s=inputs.snapshot
        own=dict(route_enabled=bool(control.options.route_byte),route_count=len(control.route_points),
            route_count_after_collect=len(control.route_points),save_on_finish_0e=bool(control.options.save_byte))
        for name,value in own.items():
            supplied=getattr(s,name)
            if supplied is not None and supplied!=value:raise ValueError('Capture conflicts with own control: '+name)
        s=replace(s,**own)
        def step(snapshot):
            return self.pipeline.advance(snapshot,probes=inputs.probes,
                normal_enabled=bool(control.options.sell_byte),buy_enabled=bool(control.options.buy_byte),
                consume=inputs.consume)
        p=step(s)
        # Read the real own DWORD clock only at a reached source clock gap.
        # Pre and post calls are distinct; neither is a helper-return receipt.
        error=None
        for label,field_name in (('pre_consume_GetTickCount','now_ms'),
                                  ('post_consume_GetTickCount','post_consume_now_ms')):
            if not p.terminal and p.needed==label:
                try:tick=raw_tick(clock)
                except (OSError,ValueError) as exc:
                    # Retain/publish reached child effects across clock failure.
                    error=str(exc);break
                s=replace(s,**{field_name:tick})
                p=step(s)
        self.state=p.scheduler.state;self.collection=p.collection
        queue,ids,self._published=self._publish(queue,p.packet_queue.records,self._published)
        if p.terminal:
            self.pipeline=None;self._published=0
            if not p.complete:self.state=replace(self.state,active=False)
        self.last=ScanLoopResult('own_clock_error' if error is not None else p.status,
            self.state.active,self._control(control),queue,p,ids,error)
        return self.last
