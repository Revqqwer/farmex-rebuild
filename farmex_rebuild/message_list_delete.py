"""Source Flood DeleteSelected/Clear callers; inert UI call and typed rebuild."""
from dataclasses import dataclass,replace
from message_list_producer import MessageListFrame,MessageListObservation

CALLBACKS={
 'selected':('004b14a4','004b14b0',0x148,'DeleteSelected',0x4b14d7),
 'clear':('004b14dc','004b14e8',0x13c,'Clear',0x4b150f),
}
LIST_PATH='frmMain/MainTab/sheetFlood/grpFlood/lwFlooding'

@dataclass(frozen=True)
class MessageListDeleteObservation:
    entry_reached:bool=False
    mutation_returned:object=None
    compile_gate_byte:object=None
    producer:object=None
    producer_parent_returned:object=None
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit callback entry required')
        for value in (self.mutation_returned,self.producer_parent_returned):
            if value is not None and type(value) is not bool:raise ValueError('Separate normal-return receipts required')
        if self.compile_gate_byte is not None and (type(self.compile_gate_byte) is not int or not 0<=self.compile_gate_byte<=255):raise ValueError('Fresh raw compile gate BYTE required')
        if self.producer is not None and not isinstance(self.producer,MessageListObservation):raise ValueError('Typed list compiler child required')

@dataclass(frozen=True)
class MessageListDeletePlan:
    complete:bool
    action:str
    calls:tuple=()
    producer:object=None
    needed:object=None
    next_address:object=None
    whole_function_verified:bool=False
    native_mutation_verified:bool=False
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class MessageListDeleteFrame:
    def __init__(self,action):
        if action not in CALLBACKS:raise ValueError('Source selected/clear action required')
        self.action=action;self.observation=MessageListDeleteObservation();self.child=MessageListFrame();self.final=None
    def advance(self,incoming):
        if not isinstance(incoming,MessageListDeleteObservation):raise ValueError('Typed delete callback observations required')
        if self.final is not None:return self.final
        address,entry,slot,method,end=CALLBACKS[self.action]
        calls=[];producer=None
        def plan(needed=None):return MessageListDeletePlan(needed is None,self.action,tuple(calls),producer,needed,end if needed is None else None)
        if not self.observation.entry_reached:
            if not incoming.entry_reached:return plan(('entry',entry))
            self.observation=replace(self.observation,entry_reached=True)
        calls.append(('VCL_TCustomListView_'+method,(LIST_PATH,slot),'ui_mutation'))
        if self.observation.mutation_returned is not True:
            if incoming.mutation_returned is not True:return plan(('normal','mutation_returned'))
            self.observation=replace(self.observation,mutation_returned=True)
        if self.observation.compile_gate_byte is None:
            if incoming.compile_gate_byte is None:return plan(('value','compile_gate_byte'))
            self.observation=replace(self.observation,compile_gate_byte=incoming.compile_gate_byte)
        if self.observation.compile_gate_byte!=0:
            calls.append(('0045c488',(0x569910,),'typed_producer'))
            producer=self.child.advance(incoming.producer or MessageListObservation())
            if not producer.complete:return plan(('producer',producer.needed))
            if self.observation.producer_parent_returned is not True:
                if incoming.producer_parent_returned is not True:return plan(('normal','producer_parent_returned'))
                self.observation=replace(self.observation,producer_parent_returned=True)
        self.final=plan();return self.final
