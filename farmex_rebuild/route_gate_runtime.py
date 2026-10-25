"""Owned FIFO bridge for captured packets and the real gate-record checkbox.

No interception, socket, source helper execution or implicit clock/provider.
100ms polling and FIFO are own single-thread UI policy, not native hook timing.
"""
from dataclasses import dataclass,replace
from route_gate_record import GateRecordFrame,GateRecordObservation

OWN_TIMER_PERIOD_MS=100


@dataclass(frozen=True)
class GateRecordContext:
    invocation:int
    generation:int
    packet:bytes
    phase:str
    needed:object


@dataclass
class _Entry:
    ticket:int
    frame:object
    provider:object
    applied_writes:int=0


class OwnedGateRecording:
    def __init__(self,sink_factory,read_recording):
        self.sink_factory=sink_factory;self.read_recording=read_recording
        self.pending=[];self.provider=None;self.generation=0;self.invocation=0
        self.result=None;self.clock_shadow={};self.busy=False

    def reset(self,reason):
        self.generation+=1
        for entry in self.pending:entry.frame.cancel(reason)
        self.pending.clear();self.provider=None;self.result=None
        # Committed metadata is an own persistent shadow, never game memory.

    def set_provider(self,provider):
        if provider is not None and not callable(provider):raise ValueError('Callable gate-record provider required')
        self.reset('provider_change');self.provider=provider

    def dispatch(self,packet):
        frame=GateRecordFrame(packet,self.sink_factory());self.invocation+=1
        self.pending.append(_Entry(self.invocation,frame,self.provider))
        if not self.busy:self.advance()
        return frame.result

    def advance(self,generation=None):
        if generation is not None and generation!=self.generation:return None
        if self.busy or not self.pending:return None
        self.busy=True;current_generation=self.generation;entry=self.pending[0];frame=entry.frame
        def current():
            return current_generation==self.generation and bool(self.pending) and self.pending[0] is entry
        def apply(result):
            if not current():return
            for address,bits,value in result.writes[entry.applied_writes:]:
                if bits!=32:raise ValueError('Unexpected owned gate-clock write width')
                self.clock_shadow[address]=value;entry.applied_writes+=1
        def recording(capture):
            # Read only when reached, after clock normal return and its writes.
            value=self.read_recording()
            if not current():return None
            if type(value) is not bool:raise ValueError('Own checkbox boolean required')
            return frame.advance(replace(capture,recording_byte=int(value)))
        try:
            result=frame.advance();apply(result)
            if not result.done and frame.phase=='recording':
                result=recording(GateRecordObservation())
                if result is None:return None
                apply(result)
            if not result.done and callable(entry.provider):
                capture=entry.provider(GateRecordContext(entry.ticket,current_generation,frame.packet,frame.phase,result.needed))
                if not current():return None
                if capture is not None:
                    if not isinstance(capture,GateRecordObservation):raise ValueError('Typed gate-record provider output required')
                    capture=replace(capture,recording_byte=None)
                    result=frame.advance(capture);apply(result)
                    if not result.done and frame.phase=='recording':
                        result=recording(capture)
                        if result is None:return None
                        apply(result)
            if not current():return None
            self.result=result
            if result.done:self.pending.pop(0)
            return result
        except (ValueError,OSError) as error:
            if not current():return None
            self.result=frame.hold(error);return self.result
        finally:self.busy=False
