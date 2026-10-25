"""Upgrade source caller -> serializer -> local queue -> normal return/stamp.

No drain, native call or game action. Queue copies and source queue removal are
prospective until the complete local frame is known. This does not roll back
effects in the original program. Partial getter snapshots must describe the
same invocation; completed getter results are retained across later gaps.
"""
from dataclasses import dataclass, field, replace
from collections.abc import Mapping
from operation_engine import UpgradeRunner, UpgradeSnapshot
from upgrade_packets import UpgradePacketObservation, plan_upgrade_packet
from action_queue import QueueState, QueueSample, enqueue
from upgrade_armor import ArmorPacketObservation,plan_armor_packet
from upgrade_packets import _raw


@dataclass(frozen=True)
class ArmorExecutionInputs:
    npc_dword:object=None
    item_dword:object=None
    selector_b_dword:object=None
    packet:ArmorPacketObservation=field(default_factory=ArmorPacketObservation)
    caller_cleanup_returned:object=None

    def __post_init__(self):
        for v in (self.npc_dword,self.item_dword,self.selector_b_dword):_raw(v)
        if not isinstance(self.packet,ArmorPacketObservation):raise ValueError('Typed Armor packet observations required')
        if self.caller_cleanup_returned is not None and type(self.caller_cleanup_returned) is not bool:
            raise ValueError('Explicit Armor caller temporary-cleanup return required')


@dataclass(frozen=True)
class UpgradeExecutionDecision:
    status:str
    complete:bool
    operation:object
    queue:QueueState
    prospective_queue:QueueState
    packet:object=None
    queue_decision:object=None
    missing:str=''
    independently_verified:bool=False
    queue_decisions:tuple=()


class UpgradeExecution:
    def __init__(self, runner, queue=None, *, anvil_reader=None):
        if not isinstance(runner,UpgradeRunner) or not runner.source_clock:
            raise ValueError('Source-clock Upgrade runner required')
        if runner.source_pending is not None:
            raise ValueError('Bind before a source helper is in flight')
        if queue is not None and not isinstance(queue,QueueState):
            raise ValueError('Typed local queue required')
        if anvil_reader is not None and not callable(anvil_reader):
            raise ValueError('Callable cached Anvil reader required')
        self.runner=runner;self.queue=queue if queue is not None else QueueState()
        self.anvil_reader=anvil_reader if anvil_reader is not None else lambda:self.runner.anvil_id
        self._clear()

    def bind_queue(self,queue):
        if not isinstance(queue,QueueState):raise ValueError('Typed local queue required')
        if self.runner.source_pending is not None or self._runner_pending is not None:
            raise ValueError('Cannot rebind an in-flight source helper')
        self.queue=queue;self._clear()

    def _clear(self):
        self._runner_pending=None;self._queue_before=None
        self._inputs=UpgradePacketObservation();self._frozen={}
        self._packet=None;self._enqueue=None;self._arguments=None;self._anvil=None
        self._queue_gates={};self._queues=[];self._queue_index=0;self._packets=None
        self._armor_inputs=ArmorExecutionInputs();self._armor_matches={};self._armor_free=None
        self._armor_helper_returned=False
        self.prospective_queue=self.queue

    def _merge(self, incoming):
        if incoming is None:return
        if not isinstance(incoming,UpgradePacketObservation):raise ValueError('Typed packet observation required')
        updates={}
        for label in ('scroll','target'):
            raw=label+'_item_dword';bound=label+'_item_inputs'
            value=getattr(incoming,raw);inputs=getattr(incoming,bound)
            if label in self._frozen:
                if value is not None and value!=self._frozen[label]:
                    raise ValueError('Completed getter result changed: '+label)
                continue
            if value is not None or inputs is not None:updates.update({raw:value,bound:inputs})
        self._inputs=replace(self._inputs,**updates)

    def _merge_armor(self,incoming,cleanup_only=False):
        if incoming is None:return
        if not isinstance(incoming,ArmorExecutionInputs):raise ValueError('Typed Armor execution inputs required')
        if cleanup_only:
            if incoming.caller_cleanup_returned is not None and self._armor_inputs.caller_cleanup_returned is not True:
                self._armor_inputs=replace(self._armor_inputs,caller_cleanup_returned=incoming.caller_cleanup_returned)
            return
        updates={}
        for key in ('npc_dword','item_dword','selector_b_dword'):
            value=getattr(incoming,key);old=getattr(self._armor_inputs,key)
            if value is not None:
                if old is not None and value!=old:raise ValueError('Armor helper argument changed: '+key)
                updates[key]=value
        old=self._armor_inputs.packet;new=incoming.packet;packet_updates={}
        matches=dict(old.vendor_matches)
        for key,value in new.vendor_matches.items():
            if key in self._armor_matches and value!=self._armor_matches[key]:raise ValueError('Reached Armor comparison changed')
            matches[key]=value
        packet_updates['vendor_matches']=matches
        if self._armor_free is not None:
            if new.free_slot_word is not None and new.free_slot_word!=self._armor_free:raise ValueError('Completed free-slot result changed')
        elif new.free_slot_word is not None or new.free_scan is not None:
            packet_updates.update(free_slot_word=new.free_slot_word,free_scan=new.free_scan)
        if new.initial_vendor_dword is not None:
            if old.initial_vendor_dword is not None and old.initial_vendor_dword!=new.initial_vendor_dword:
                raise ValueError('Initial vendor observation changed')
            packet_updates['initial_vendor_dword']=new.initial_vendor_dword
        updates['packet']=replace(old,**packet_updates)
        if incoming.caller_cleanup_returned is not None and self._armor_inputs.caller_cleanup_returned is not True:
            updates['caller_cleanup_returned']=incoming.caller_cleanup_returned
        self._armor_inputs=replace(self._armor_inputs,**updates)

    def step(self, snapshot, packet_observation=None, queue_sample=None,*,armor_inputs=None,armor_queue_samples=None):
        if not isinstance(snapshot,UpgradeSnapshot):raise ValueError('Typed Upgrade snapshot required')
        if self._runner_pending is not None:
            if self.runner.source_pending is not self._runner_pending or self.queue!=self._queue_before:
                raise ValueError('In-flight source/queue snapshot changed')
        # A legacy normal-return marker cannot bypass the packet/queue stages.
        operation=self.runner.tick(replace(snapshot,source_helper_returned=None,source_stamp_tick_dword=None))
        pending=self.runner.source_pending
        if pending is None:
            self._clear()
            return UpgradeExecutionDecision(operation.status,not operation.status.startswith('needs_'),
                                             operation,self.queue,self.queue,missing=operation.reason)
        if self._runner_pending is None:
            self._queue_before=self.queue
            scroll=self.runner.source_scroll_index
            self._arguments=(None,pending.intent.item_id,
                             None if scroll is None else scroll&0xffffffff)
        self._runner_pending=pending

        def result(status,complete=False,missing=''):
            return UpgradeExecutionDecision(status,complete,operation,self.queue,self.prospective_queue,
                                             self._packet,self._enqueue,missing,queue_decisions=tuple(self._queues))

        armor=pending.intent.kind=='armor_purchase'
        if armor:
            self._merge_armor(armor_inputs,cleanup_only=self._packet is not None and self._packet.complete)
            if self._packet is None or not self._packet.complete:
                a=self._armor_inputs
                self._packet=plan_armor_packet(a.npc_dword,1,a.item_dword,0,a.selector_b_dword,a.packet)
                if self._packet.observed_free_word is not None:
                    self._armor_free=self._packet.observed_free_word
                    self._armor_inputs=replace(self._armor_inputs,packet=replace(a.packet,free_slot_word=self._armor_free,free_scan=None))
                self._armor_matches.update(self._packet.observed_matches)
                if not self._packet.complete:return result('needs_armor_packet',missing=self._packet.missing)
                self._packets=self._packet.packets
        elif self._packet is None or not self._packet.complete:
            self._merge(packet_observation)
            self._packet=plan_upgrade_packet(*self._arguments,self._inputs)
            for label,value in self._packet.observed_items:
                self._frozen[label]=value
                self._inputs=replace(self._inputs,**{label+'_item_dword':value,label+'_item_inputs':None})
            # Source copies object+8 only AFTER both independent item getters.
            # Unknown cached data is a gap, not the runner constructor default.
            if len(self._frozen)==2:
                if self._anvil is None:
                    value=self.anvil_reader();_raw(value)
                    if value is not None:self._anvil=value
                if self._anvil is not None:
                    self._packet=plan_upgrade_packet(self._anvil,*self._arguments[1:],self._inputs)
            if not self._packet.complete:return result('needs_packet_observation',missing=self._packet.missing)
            self._packets=((self._packet.payload,0),)
        while self._queue_index<len(self._packets):
            index=self._queue_index
            if armor:
                if armor_queue_samples is not None and not isinstance(armor_queue_samples,Mapping):
                    raise ValueError('Independent indexed Armor enqueue samples required')
                sample=None if armor_queue_samples is None else armor_queue_samples.get(index)
            else:sample=queue_sample
            sample=sample if sample is not None else QueueSample()
            if not isinstance(sample,QueueSample):raise ValueError('Typed enqueue sample required')
            gate=self._queue_gates.get(index)
            if gate is None:gate=sample.connection_gate;self._queue_gates[index]=gate
            elif sample.connection_gate is not None and sample.connection_gate!=gate:
                raise ValueError('Reached enqueue connection gate changed')
            payload,delay=self._packets[index]
            self._enqueue=enqueue(self.prospective_queue,payload,len(payload),delay,gate,sample.tick)
            if self._enqueue.state is None:
                return result('needs_queue_observation',missing=self._enqueue.missing or self._enqueue.status)
            self.prospective_queue=self._enqueue.state
            self._queues.append(self._enqueue);self._queue_index+=1
        if armor:
            if snapshot.source_helper_returned is True:self._armor_helper_returned=True
            if not self._armor_helper_returned:
                return result('helper_did_not_return' if snapshot.source_helper_returned is False else 'needs_helper_return',
                              missing='Armor helper normal return')
            if self._armor_inputs.caller_cleanup_returned is not True:
                return result('needs_armor_caller_cleanup',missing='caller00505c48 temporary cleanup normal return')
            snapshot=replace(snapshot,source_helper_returned=True)
        operation=self.runner.tick(snapshot)
        self._runner_pending=self.runner.source_pending
        if operation.status!='attempt':return result(operation.status,missing=operation.reason)
        self.queue=self.prospective_queue
        completed=result('local_armor_frame_complete' if armor else 'local_upgrade_frame_complete',True)
        self._clear()
        return completed
