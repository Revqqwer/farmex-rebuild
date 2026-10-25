"""Own checkbox-driven polling of the captured item-break worker chain.

The checkbox controls only this own timer. Source enable/work/gate/clock reads
and all child/parent returns remain explicit captures. No native execution or
automatic game inventory/NPC reads are performed.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState,publish_appended_records
from item_break_cycle import ItemBreakCycleObservation,ItemBreakClockObservation
from item_break_inventory import ItemBreakInventoryObservation
from item_break_npc import ItemBreakNpcObservation
from item_break_requests import ItemBreakRequestCycleFrame,ItemBreakRequestObservation

ENABLE_PATH='frmMain/MainTab/sheetCrash/GroupBox20/chAutoCrashItems'
OWN_TIMER_PERIOD_MS=100


@dataclass(frozen=True)
class AutoBreakInput:
    caller:ItemBreakCycleObservation=field(default_factory=ItemBreakCycleObservation)
    request:object=None
    npc:object=None
    guard:object=None
    guard_parent_returned:object=None
    npc_parent_returned:object=None
    action_parent_returned:object=None
    def __post_init__(self):
        if not isinstance(self.caller,ItemBreakCycleObservation):raise ValueError('Typed automatic caller required')
        for value,kind in ((self.request,ItemBreakRequestObservation),(self.npc,ItemBreakNpcObservation),
                           (self.guard,ItemBreakInventoryObservation)):
            if value is not None and not isinstance(value,kind):raise ValueError('Typed automatic child observations required')
        for value in (self.guard_parent_returned,self.npc_parent_returned,self.action_parent_returned):
            if value is not None and type(value) is not bool:raise ValueError('Separate child-parent return required')
        if self.caller.inventory_guard_returned is not None or self.caller.npc_returned is not None or self.caller.npc_eax is not None:
            raise ValueError('Typed children own caller guard/NPC bindings')
        if self.caller.clock_inputs is not None and self.caller.clock_inputs.action_returned is not None:
            raise ValueError('Typed request child owns action binding')


@dataclass(frozen=True)
class AutoBreakContext:
    generation:int
    invocation:int
    pending:object
    queue:QueueState
    scalar_state:object
    configuration:object


@dataclass(frozen=True)
class AutoBreakResult:
    enabled:bool
    complete:bool
    status:str
    queue:QueueState
    invocation:int
    plan:object=None
    published_record_ids:tuple=()
    scalar_state:object=None
    native_execution_verified:bool=False
    delivery_verified:bool=False
    live_compatibility_verified:bool=False


class OwnedAutoItemBreak:
    def __init__(self,scalar_state=None):
        if scalar_state is not None and type(scalar_state) is not dict:raise ValueError('Own scalar shadow dictionary required')
        self.enabled=False;self.generation=0;self.invocation=0
        self.frame=None;self._published=0;self.last=None
        self.scalar_state={} if scalar_state is None else scalar_state
        self._npc_applied=();self._clock_applied=()

    def configure(self,enabled):
        if type(enabled) is not bool:raise ValueError('Own auto checkbox boolean required')
        if self.enabled!=enabled:
            self.generation+=1;self.enabled=enabled
            self.frame=None;self._published=0;self.last=None
        return self.enabled

    def reset(self):
        self.generation+=1;self.enabled=False;self.frame=None;self._published=0
        self.scalar_state.clear();self.last=None

    def context(self,queue,configuration):
        if not isinstance(queue,QueueState):raise ValueError('Own shared queue required')
        return AutoBreakContext(self.generation,self.invocation+(self.frame is None),
            None if self.frame is None or self.last is None else self.last.plan,
            queue,MappingProxyType(dict(self.scalar_state)),MappingProxyType(dict(configuration)))

    def advance(self,queue,inputs=None):
        if not isinstance(queue,QueueState):raise ValueError('Own shared queue required')
        inputs=AutoBreakInput() if inputs is None else inputs
        if not isinstance(inputs,AutoBreakInput):raise ValueError('Typed automatic input required')
        if not self.enabled:
            return AutoBreakResult(False,True,'inactive',queue,self.invocation,
                scalar_state=MappingProxyType(dict(self.scalar_state)))
        if self.frame is None:
            self.invocation+=1;self.frame=ItemBreakRequestCycleFrame(queue)
            self._published=len(queue.records)
            self._npc_applied=();self._clock_applied=()
        caller=inputs.caller;conflict=None
        known_stamp=all(address in self.scalar_state for address in (0x553d50,0x553d54))
        if known_stamp:
            # Do not consume a stale provider stamp before validating it at the
            # actual read boundary. Own committed clock writes survive ticks.
            caller=replace(caller,clock_inputs=replace(caller.clock_inputs or ItemBreakClockObservation(),
                last_tick_low=None,last_tick_high=None))
        def step(c):
            return self.frame.advance(c,inputs.request,inputs.npc,inputs.guard,
                guard_parent_returned=inputs.guard_parent_returned,
                npc_parent_returned=inputs.npc_parent_returned,
                action_parent_returned=inputs.action_parent_returned)
        p=step(caller)
        if known_stamp:
            for name,address in (('last_tick_low',0x553d50),('last_tick_high',0x553d54)):
                clock=p.caller.caller.caller.clock
                if p.needed=='clock_inputs' and clock is not None and clock.needed==name:
                    expected=self.scalar_state[address][1]
                    supplied=None if inputs.caller.clock_inputs is None else getattr(inputs.caller.clock_inputs,name)
                    if supplied is not None and supplied!=expected:
                        conflict=name;break
                    caller=replace(caller,clock_inputs=replace(caller.clock_inputs,**{name:expected}))
                    p=step(caller)
        queue,ids,self._published=publish_appended_records(queue,p.queue.records,self._published)
        if p.caller.npc is not None:
            stores=p.caller.npc.stores
            if stores[:len(self._npc_applied)]!=self._npc_applied:raise AssertionError('NPC store prefix retracted')
            for address,width,value in stores[len(self._npc_applied):]:self.scalar_state[address]=(width,value)
            self._npc_applied=stores
        cycle=p.caller.caller.caller
        if cycle.clock is not None:
            stores=cycle.clock.stores
            if stores[:len(self._clock_applied)]!=self._clock_applied:raise AssertionError('Clock store prefix retracted')
            for address,width,value in stores[len(self._clock_applied):]:self.scalar_state[address]=(width,value)
            self._clock_applied=stores
        status=cycle.status if p.complete else 'needs_observation'
        if conflict is not None:status='conflicting_clock_observation'
        if p.complete and cycle.clock is not None:status=cycle.clock.status
        self.last=AutoBreakResult(self.enabled,p.complete,status,queue,self.invocation,p,ids,
            MappingProxyType(dict(self.scalar_state)))
        if p.complete:self.frame=None;self._published=0
        return self.last
