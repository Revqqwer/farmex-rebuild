"""Owned active-scan reply composition; no capture, game send, or native ACK.

Decoded metadata is explicit. Own record projection, original parser return,
finish enqueue projection and original finish return are independent gates.
Only the active scan slice is handled; other merchant replies remain external.
"""
from dataclasses import dataclass,field
from types import MappingProxyType
from action_queue import QueueState
from direct_chat_packets import QueueAttempt
from event_packets import EventEnqueueFrame
from merchant_reply import MerchantReplyState,MerchantReplyObservation,plan_merchant_reply
from merchant_scan_results import MerchantActorMetadata,MerchantItemMetadata,project_merchant_scan_results
from merchant_result_filter import MerchantFilterSelection
from merchant_scan_reply_source import ScanReplySource,MerchantReplySourceFrame


@dataclass(frozen=True)
class ScanReplyObservation:
    actor:object=None
    items:object=field(default_factory=dict)
    parse_returned:object=None
    finish_setup_returned:object=None
    finish_returned:object=None
    attempt:QueueAttempt=field(default_factory=QueueAttempt)
    source:object=None
    def __post_init__(self):
        if self.actor is not None and not isinstance(self.actor,MerchantActorMetadata):raise ValueError('Typed decoded actor metadata required')
        items=dict(self.items)
        if any(type(k) is not int or not 0<=k<12 or not isinstance(v,MerchantItemMetadata) for k,v in items.items()):raise ValueError('Typed slot-indexed item metadata required')
        for v in (self.parse_returned,self.finish_setup_returned,self.finish_returned):
            if v is not None and type(v) is not bool:raise ValueError('Independent normal return required')
        if not isinstance(self.attempt,QueueAttempt):raise ValueError('Typed finish queue attempt required')
        if self.source is not None:
            if not isinstance(self.source,ScanReplySource):raise ValueError('Typed source observations required')
            if self.actor is not None or items:raise ValueError('Choose source observations or decoded metadata')
        object.__setattr__(self,'items',MappingProxyType(items))


@dataclass(frozen=True)
class ScanReplyResult:
    complete:bool
    terminal:bool
    status:str
    state:MerchantReplyState
    queue:QueueState
    records:tuple=()
    parser:object=None
    dispatcher:object=None
    needed:object=None
    finish_payload:object=None
    native_execution_verified:bool=False
    delivery_verified:bool=False
    live_compatibility_verified:bool=False
    source_production:object=None


class MerchantScanReplyFrame:
    def __init__(self,payload,state,queue=None):
        if type(payload) is not bytes or not isinstance(state,MerchantReplyState):raise ValueError('Immutable payload and typed reply state required')
        self.payload=payload;self.state=state;self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own shared queue snapshot required')
        self.actor=None;self.items={};self.records=();self.parser=None;self.dispatcher=None
        self.parse_normal=False;self.finish_setup=False;self.enqueue=None;self.final=None
        self.finish_payload=None
        self.input_mode=None;self.source_frame=None;self.source_production=None

    def _result(self,status,needed=None,terminal=False,complete=False):
        result=ScanReplyResult(complete,terminal,status,self.state,self.queue,self.records,
            self.parser,self.dispatcher,needed,self.finish_payload,source_production=self.source_production)
        if terminal:self.final=result
        return result

    def advance(self,o=None):
        o=ScanReplyObservation() if o is None else o
        if not isinstance(o,ScanReplyObservation):raise ValueError('Typed reply observations required')
        if self.final is not None:return self.final
        packet=self.payload
        if not packet or (packet[0]==0x68 and len(packet)<2):
            return self._result('truncated',terminal=True)
        if packet[0]!=0x68 or packet[1] not in (0x27,0x02,0x11,0x05,0x23):
            return self._result('outside_active_scan_scope',terminal=True,complete=True)
        subtype=packet[1]
        if subtype in (0x27,0x02,0x11):
            self.dispatcher=plan_merchant_reply(self.state,packet,MerchantReplyObservation(1))
            self.state=self.dispatcher.state
            return self._result('scan_consumed',terminal=True,complete=True)
        if len(packet)<3:return self._result('truncated',terminal=True)
        if packet[2]==1:
            if self.parser is None or not self.parser.complete:
                mode='source' if o.source is not None else ('decoded' if o.actor is not None or o.items else None)
                if mode is not None:
                    if self.input_mode is not None and self.input_mode!=mode:raise ValueError('Cannot change metadata source during one reply')
                    self.input_mode=mode
                actor=self.actor if self.actor is not None else o.actor
                items={**o.items,**self.items}
                # Metadata projection is neutral; the actual UI applies its
                # current filter/search/sort separately. No source filter or
                # parser normal receipt follows merely from this projection.
                if self.input_mode=='source':
                    if self.source_frame is None:self.source_frame=MerchantReplySourceFrame(packet)
                    self.source_production=self.source_frame.advance(o.source)
                    p=self.source_production.results
                else:
                    p=project_merchant_scan_results(packet,actor,items,
                        MerchantFilterSelection('','',0x808080,0))
                self.parser=p
                self.records=p.records
                if self.input_mode!='source':
                    if actor is not None and any(slot.item_id for slot in p.raw_data.slots):self.actor=actor
                    if p.records:
                        for record in p.records:self.items[record.slot_index]=items[record.slot_index]
                if not p.complete:
                    if not p.raw_data.complete:
                        return self._result('truncated_scan_data',terminal=True)
                    return self._result('needs_metadata',self.source_production.status if self.input_mode=='source' else p.status)
            if not self.parse_normal:
                if o.parse_returned is not True:return self._result('needs_parser_return','004bc650 normal return')
                self.parse_normal=True
        mode=1 if subtype==5 else 2
        self.finish_payload=bytes((0x68,0x08 if mode==1 else 0x27))
        if not self.finish_setup:
            if o.finish_setup_returned is not True:return self._result('needs_finish_setup','00504c08 normal return')
            self.finish_setup=True
        if self.enqueue is None:self.enqueue=EventEnqueueFrame(self.finish_payload,0,self.queue)
        child=self.enqueue.advance(o.attempt);self.queue=child.queue
        if not child.complete:return self._result('needs_finish_enqueue',child.needed)
        if o.finish_returned is not True:return self._result('needs_finish_return','004bf57c normal return')
        self.dispatcher=plan_merchant_reply(self.state,packet,MerchantReplyObservation(1,
            scan_parse_returned=self.parse_normal,scan_finish_returned=True))
        if not self.dispatcher.complete:raise AssertionError('Child-gated scan dispatcher unexpectedly incomplete')
        self.state=self.dispatcher.state
        return self._result('scan_consumed',terminal=True,complete=True)

    def abort(self,reason):
        if type(reason) is not str or not reason:raise ValueError('Explicit abort reason required')
        if self.final is None:return self._result('aborted',reason,terminal=True)
        return self.final
