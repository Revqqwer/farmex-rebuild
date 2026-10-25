"""Actual owned manual-click lifecycle over the existing captured source frame.

One Tk-thread FIFO invocation per physical click, no automatic-cycle gates,
native call execution, game send or invented helper returns. Polling100ms is
an own asynchronous UI policy, not an original timer period.
"""
from dataclasses import dataclass,field
from types import MappingProxyType
from action_queue import QueueState,publish_appended_records
from item_break_manual import ItemBreakManualClickFrame,ItemBreakManualObservation

BUTTON_PATH='frmMain/MainTab/sheetCrash/GroupBox14/Button5'
OWN_TIMER_PERIOD_MS=100


@dataclass(frozen=True)
class ManualBreakInput:
    observation:ItemBreakManualObservation=field(default_factory=ItemBreakManualObservation)
    handler_returned:object=None
    def __post_init__(self):
        if not isinstance(self.observation,ItemBreakManualObservation):raise ValueError('Typed manual-break observations required')
        if self.handler_returned is not None and type(self.handler_returned) is not bool:raise ValueError('Separate callback return required')


@dataclass(frozen=True)
class ManualBreakContext:
    ticket:tuple
    pending:object
    queue:QueueState
    scalar_state:object
    queued_invocations:int


@dataclass(frozen=True)
class ManualBreakResult:
    status:str
    complete:bool
    ticket:object
    queue:QueueState
    plan:object=None
    published_record_ids:tuple=()
    scalar_state:object=None
    queued_invocations:int=0
    native_execution_verified:bool=False
    delivery_verified:bool=False
    live_compatibility_verified:bool=False


class OwnedManualItemBreak:
    def __init__(self,scalar_state=None):
        if scalar_state is not None and type(scalar_state) is not dict:raise ValueError('Own scalar shadow dictionary required')
        self.generation=0;self._number=0;self.tickets=[]
        self.frame=None;self._published=0;self.last=None
        self.scalar_state={} if scalar_state is None else scalar_state
        self._npc_applied=()

    def click(self):
        self._number+=1;ticket=(self.generation,self._number)
        self.tickets.append(ticket)
        return ticket

    @property
    def pending(self):return bool(self.tickets)

    def reset(self):
        self.generation+=1;self.tickets=[];self.frame=None;self._published=0
        self.last=None;self.scalar_state.clear();self._npc_applied=()

    def context(self,queue):
        if not isinstance(queue,QueueState):raise ValueError('Own shared queue required')
        if not self.tickets:return None
        pending=None if self.frame is None or self.last is None else self.last.plan
        return ManualBreakContext(self.tickets[0],pending,queue,
            MappingProxyType(dict(self.scalar_state)),len(self.tickets))

    def advance(self,queue,inputs=None):
        if not isinstance(queue,QueueState):raise ValueError('Own shared queue required')
        inputs=ManualBreakInput() if inputs is None else inputs
        if not isinstance(inputs,ManualBreakInput):raise ValueError('Typed manual-break input required')
        if not self.tickets:
            return ManualBreakResult('idle',True,None,queue,scalar_state=MappingProxyType(dict(self.scalar_state)))
        ticket=self.tickets[0]
        if self.frame is None:
            self.frame=ItemBreakManualClickFrame(queue);self._published=len(queue.records);self._npc_applied=()
        p=self.frame.advance(inputs.observation,clicked=True,handler_returned=inputs.handler_returned)
        # Click entry is an actual own UI event. Post-prologue helper entry and
        # every source boundary receipt still come from the explicit provider.
        manual=p.manual
        if manual is not None:
            queue,ids,self._published=publish_appended_records(queue,manual.queue.records,self._published)
            if manual.npc is not None:
                stores=manual.npc.stores
                if stores[:len(self._npc_applied)]!=self._npc_applied:raise AssertionError('NPC store prefix retracted')
                for address,width,value in stores[len(self._npc_applied):]:self.scalar_state[address]=(width,value)
                self._npc_applied=stores
        else:ids=()
        status=manual.status if p.complete and manual is not None else 'needs_observation'
        if p.complete:
            self.tickets.pop(0);self.frame=None;self._published=0
        self.last=ManualBreakResult(status,p.complete,ticket,queue,p,ids,
            MappingProxyType(dict(self.scalar_state)),len(self.tickets))
        return self.last
