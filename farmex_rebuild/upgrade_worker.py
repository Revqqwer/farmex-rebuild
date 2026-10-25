"""Owned captured Upgrade worker: shared cached state/queue, no game IO.

The existing execution model keeps queue/source effects prospective until its
local return/stamp frame completes. Writer conflict/publish retry and FIFO are
own policies; they do not reproduce native queue concurrency or exceptions.
"""
from dataclasses import dataclass
from action_queue import QueueState
from operation_engine import UpgradeSnapshot
from upgrade_execution import UpgradeExecution
from upgrade_parameter_frame import UpgradeParameterState
from upgrade_start_frame import UpgradeStartFrame
from upgrade_packets import _raw
from armor_worker import ArmorWorker


@dataclass(frozen=True)
class UpgradeWorkerInput:
    snapshot:object
    packet:object=None
    queue_sample:object=None
    initial_stamp_qword:object=None
    stop_prefix_returned:object=None
    stop_observation:object=None
    stop_suffix_returned:object=None
    armor:object=None


@dataclass(frozen=True)
class UpgradeWorkerContext:
    generation:int
    mode:int
    phase:str
    needed:object=None


@dataclass(frozen=True)
class UpgradeWorkerResult:
    status:str
    complete:bool=False
    execution:object=None
    needed:object=None
    error:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False


class OwnedUpgradeWorker:
    def __init__(self,runner,parameters,sink,queue_reader,queue_writer):
        if not isinstance(parameters,UpgradeParameterState):raise ValueError('Shared cached parameters required')
        if not callable(queue_reader) or not callable(queue_writer):raise ValueError('Shared own queue reader/writer required')
        self.runner=runner;self.parameters=parameters;self.sink=sink
        self.queue_reader=queue_reader;self.queue_writer=queue_writer
        self.execution=UpgradeExecution(runner,self._queue(),anvil_reader=lambda:self.parameters.anvil_dword)
        self.stop_frame=None;self.stop_operation=None;self.stop_prefix=False
        self.publication=None;self.result=UpgradeWorkerResult('idle')
        self.armor_worker=ArmorWorker(runner,queue_reader,queue_writer)

    @property
    def pending(self):
        return self.runner.source_pending is not None or self.stop_frame is not None or self.publication is not None or self.armor_worker.pending

    def _queue(self):
        value=self.queue_reader()
        if not isinstance(value,QueueState):raise ValueError('Typed shared queue required')
        return value

    def _out(self,status,complete=False,execution=None,needed=None):
        self.result=UpgradeWorkerResult(status,complete,execution,needed);return self.result

    def hold(self,error):
        self.result=UpgradeWorkerResult('needs_observation',execution=self.result.execution,
            needed=self.result.needed,error=str(error))
        return self.result

    @staticmethod
    def _normal(value,name):
        if value is not None and type(value) is not bool:raise ValueError('Explicit normal receipt required: '+name)
        return value is True

    def _publish(self):
        expected,candidate,decision=self.publication
        current=self._queue()
        if current!=expected and current!=candidate:return self._out('queue_conflict',execution=decision,needed=('shared_queue_identity',))
        if current!=candidate:
            try:self.queue_writer(candidate)
            except (OSError,ValueError) as error:return self._out('needs_queue_publish',execution=decision,needed=str(error))
            if self._queue()!=candidate:return self._out('needs_queue_publish',execution=decision,needed=('writer_did_not_retain_queue',))
        self.publication=None
        return self._out(decision.status,decision.complete,decision)

    def _stop(self,capture):
        if not self.stop_prefix:
            if not self._normal(capture.stop_prefix_returned,'stop_prefix'):
                return self._out('needs_stop_prefix',execution=self.stop_operation,needed=('pre_stop_helper_span',))
            self.stop_prefix=True
        p=self.stop_frame.advance(capture.stop_observation)
        if not p.complete:return self._out('needs_stop_effects',execution=self.stop_operation,needed=p.needed)
        if not self._normal(capture.stop_suffix_returned,'stop_suffix'):
            return self._out('needs_stop_suffix',execution=self.stop_operation,needed=('post_stop_cleanup_span',))
        decision=self.stop_operation
        self.stop_frame=None;self.stop_operation=None;self.stop_prefix=False
        return self._out('stopped',True,decision)

    def step(self,capture):
        if not isinstance(capture,UpgradeWorkerInput) or not isinstance(capture.snapshot,UpgradeSnapshot):
            raise ValueError('Typed captured worker input/snapshot required')
        if self.publication is not None:return self._publish()
        if self.stop_frame is not None:return self._stop(capture)
        if self.runner.state==2 or self.armor_worker.pending:
            p=self.armor_worker.step(capture.snapshot,capture.armor,capture.initial_stamp_qword)
            return self._out(p.status,p.complete,p.execution,p.needed)
        if self.runner.state==1 and self.runner.source_pending is None:
            interval=self.parameters.interval_dword;_raw(interval)
            if interval is None:return self._out('needs_interval',needed=('cached_interval_dword',))
            self.runner.interval_ms=interval
            if self.runner.queue_stamp_qword is None:
                stamp=capture.initial_stamp_qword
                if stamp is not None:
                    if type(stamp) is not int or not 0<=stamp<=0xffffffffffffffff:raise ValueError('Raw initial QWORD stamp required')
                    self.runner.queue_stamp_qword=stamp
        current=self._queue()
        if self.runner.source_pending is not None:
            if current!=self.execution.queue:return self._out('queue_conflict',needed=('shared_queue_identity',))
        else:self.execution.bind_queue(current)
        mode=self.runner.state
        decision=self.execution.step(capture.snapshot,capture.packet,capture.queue_sample)
        if decision.status=='stopped' and decision.operation.reason in ('queue_empty','scroll_unavailable'):
            # The existing runner abstracts the stop call. Restore mode until
            # the captured pre-helper span has returned, then run the inner
            # helper entry (which has no callback561f55 gate) and its UI effects.
            self.runner.state=mode
            self.stop_frame=UpgradeStartFrame('stop',self.runner,self.parameters,self.sink,entry='helper')
            self.stop_operation=decision;self.stop_prefix=False
            return self._stop(capture)
        if self.execution.queue!=current:
            self.publication=(current,self.execution.queue,decision)
            return self._publish()
        return self._out(decision.status,decision.complete,decision,decision.missing or None)
