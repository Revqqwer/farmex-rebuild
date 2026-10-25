"""Captured mode2 continuation with branch-specific terminal ordering, no IO to game."""
from dataclasses import dataclass,replace
from upgrade_execution import UpgradeExecution,ArmorExecutionInputs
from upgrade_armor import ArmorPacketObservation
from upgrade_packets import _raw
from action_queue import QueueState


@dataclass(frozen=True)
class ArmorWorkerObservation:
    distance_ftol_dword:object=None
    bag_flag_byte:object=None
    preparation_returned:object=None
    packet:object=None
    queue_samples:object=None
    caller_cleanup_returned:object=None
    message_returned:object=None
    message_cleanup0_returned:object=None
    message_cleanup1_returned:object=None


@dataclass(frozen=True)
class ArmorWorkerResult:
    status:str
    complete:bool=False
    execution:object=None
    needed:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class ArmorWorker:
    def __init__(self,runner,queue_reader,queue_writer):
        self.runner=runner;self.queue_reader=queue_reader;self.queue_writer=queue_writer
        self.phase='clock';self.cache={};self.execution=None;self.decision=None;self.expected=None;self.reason=None
        self.result=ArmorWorkerResult('idle')
    @property
    def pending(self):return self.phase!='clock'
    def out(self,status,complete=False,needed=None):
        self.result=ArmorWorkerResult(status,complete,self.decision,needed);return self.result
    def queue(self):
        value=self.queue_reader()
        if not isinstance(value,QueueState):raise ValueError('Typed shared own queue required')
        return value
    def mode(self,value):
        self.runner.state=value
        fields=dict(getattr(self.runner,'armor_source_fields',{}));fields[0x10]=value
        self.runner.armor_source_fields=fields
    def step(self,snapshot,observation=None,initial_stamp=None):
        o=ArmorWorkerObservation() if observation is None else observation
        if not isinstance(o,ArmorWorkerObservation):raise ValueError('Typed Armor worker observations required')
        class Missing(Exception):pass
        def normal(name):
            if self.cache.get(name) is True:return
            value=getattr(o,name)
            if value is not None and type(value) is not bool:raise ValueError('Explicit normal return required')
            if value is not True:raise Missing((name,))
            self.cache[name]=True
        def raw(name):
            if name not in self.cache:
                value=getattr(o,name);_raw(value)
                if value is None:raise Missing((name,))
                self.cache[name]=value
            return self.cache[name]
        def field(offset):
            key=('field',offset)
            if key not in self.cache:
                value=getattr(self.runner,'armor_source_fields',{}).get(offset);_raw(value)
                if value is None:raise Missing(('cached_field',offset))
                self.cache[key]=value
            return self.cache[key]
        try:
            for _ in range(24):
                if self.phase=='clock':
                    if self.runner.state!=2:return self.out('inactive',True)
                    tick=snapshot.now_ms
                    if type(tick) is not int or not 0<=tick<=0xffffffff:raise ValueError('Raw gate tick DWORD required')
                    stamp=self.runner.armor_stamp_qword
                    if stamp is None:
                        if initial_stamp is None:raise Missing(('initial_armor_stamp_qword',))
                        if type(initial_stamp) is not int or not 0<=initial_stamp<=0xffffffffffffffff:raise ValueError('Raw initial Armor QWORD required')
                        stamp=self.runner.armor_stamp_qword=initial_stamp
                    if type(stamp) is not int or not 0<=stamp<=0xffffffffffffffff:raise ValueError('Raw Armor QWORD required')
                    if self.runner._signed(tick-stamp,64)<200:return self.out('waiting',True)
                    self.decision=None;self.cache['gate_tick']=tick;self.phase='coordinates'
                elif self.phase=='coordinates':field(0x54);field(0x50);self.phase='distance'
                elif self.phase=='distance':
                    if self.runner._signed(raw('distance_ftol_dword'),32)>=10:
                        self.reason='armor_distance';self.mode(0);self.phase='message'
                    else:self.phase='bag'
                elif self.phase=='bag':
                    flag=raw('bag_flag_byte')
                    if flag>255:raise ValueError('Raw bag AL BYTE required')
                    if flag:
                        self.reason='armor_bag';self.mode(0);self.phase='message'
                    else:self.phase='arguments'
                elif self.phase=='arguments':field(0x5c);field(0x58);field(0x4c);self.phase='preparation'
                elif self.phase=='preparation':normal('preparation_returned');self.phase='execute'
                elif self.phase=='execute':
                    if self.execution is None:
                        self.expected=self.queue();self.execution=UpgradeExecution(self.runner,self.expected)
                    if self.queue()!=self.expected:return self.out('queue_conflict',needed=('shared_queue_identity',))
                    packet=o.packet if o.packet is not None else ArmorPacketObservation()
                    inputs=ArmorExecutionInputs(field(0x4c),field(0x58),field(0x5c)&0xffff,packet,o.caller_cleanup_returned)
                    snap=replace(snapshot,now_ms=self.cache['gate_tick'],armor_distance=None,
                        armor_distance_ftol_dword=self.cache['distance_ftol_dword'],armor_blocked=False)
                    self.decision=self.execution.step(snap,armor_inputs=inputs,armor_queue_samples=o.queue_samples)
                    if not self.decision.complete:return self.out(self.decision.status,needed=self.decision.missing)
                    # The legacy execution compresses the limit stop. Preserve
                    # source mode2 until this frame's notice/cleanup0 boundary.
                    self.mode(2)
                    fields=dict(self.runner.armor_source_fields)
                    fields.update({0x60:self.runner.armor_attempts,0x40:self.runner.armor_stamp_qword&0xffffffff,0x44:0})
                    self.runner.armor_source_fields=fields;self.phase='publish'
                    self.cache['limit_exceeded']=self.runner._signed(self.runner.armor_attempts,32)>42
                elif self.phase=='publish':
                    candidate=self.execution.queue;current=self.queue()
                    if current!=self.expected and current!=candidate:return self.out('queue_conflict',needed=('shared_queue_identity',))
                    if current!=candidate:
                        try:self.queue_writer(candidate)
                        except (OSError,ValueError) as error:return self.out('needs_queue_publish',needed=str(error))
                        if self.queue()!=candidate:return self.out('needs_queue_publish',needed=('writer_did_not_retain_queue',))
                    if self.cache['limit_exceeded']:
                        self.reason='armor_attempt_limit';self.phase='message'
                    else:
                        result=self.out('local_armor_frame_complete',True)
                        self.phase='clock';self.cache={};self.execution=None;self.expected=None
                        return result
                elif self.phase=='message':normal('message_returned');self.phase='cleanup0'
                elif self.phase=='cleanup0':
                    normal('message_cleanup0_returned')
                    if self.reason=='armor_attempt_limit':self.mode(0)
                    self.phase='cleanup1'
                elif self.phase=='cleanup1':
                    normal('message_cleanup1_returned');self.runner.reason=self.reason
                    result=self.out('stopped',True,self.reason)
                    self.phase='clock';self.cache={};self.execution=None;self.expected=None;self.reason=None
                    return result
                else:raise ValueError('Unknown Armor worker phase')
            return self.out('continuation',needed=('own_chunk',))
        except Missing as error:return self.out('needs_armor_observation',needed=error.args[0])
