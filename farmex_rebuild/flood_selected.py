"""Own selected-message caller: two selection reads, no cycle/enable changes."""
from dataclasses import dataclass
from action_queue import QueueState,enqueue
from message_list_producer import MessageListRow
from flood_runtime import prepare_owned_message,raw_tick

BUTTON_PATH='frmMain/MainTab/sheetFlood/grpFlood/btnChatSelected'

@dataclass(frozen=True)
class SelectedFloodPlan:
    complete:bool
    status:str
    queue:QueueState
    first_index:object=None
    selected_index:object=None
    payload:object=None
    native_execution_verified:bool=False
    delivery_verified:bool=False
    live_compatibility_verified:bool=False

class OwnedSelectedMessageFrame:
    def __init__(self,queue=None):
        self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own queue required')
        self.first=None;self.index=None;self.rows=None;self.packet=None;self.gate=None;self.final=None
    def advance(self,selection_reader,rows_reader,clock,gate_reader):
        if any(not callable(f) for f in (selection_reader,rows_reader,clock,gate_reader)):raise ValueError('Explicit own reader/clock/gate providers required')
        if self.final is not None:return self.final
        def result(complete,status):return SelectedFloodPlan(complete,status,self.queue,self.first,self.index,None if self.packet is None else self.packet.payload)
        def selection():
            value=selection_reader()
            if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw selected EAX required')
            return value
        try:
            if self.first is None:self.first=selection()
            if self.first&0x80000000:
                self.final=result(True,'no_selection');return self.final
            if self.index is None:self.index=selection()
            if self.rows is None:
                rows=rows_reader()
                if type(rows) is not tuple or any(not isinstance(r,MessageListRow) for r in rows):raise ValueError('Current immutable compiled rows required')
                self.rows=rows
            # Source does not recheck the second EAX or compiled count. Our
            # safe boundary stays explicit rather than Python negative index.
            if self.index>=len(self.rows):return result(False,'unresolved_source_index')
            if self.packet is None:self.packet=prepare_owned_message(self.rows[self.index])
            if not self.packet.complete:return result(False,self.packet.status)
            if self.packet.payload is None:
                self.final=result(True,'unknown_channel');return self.final
            if self.gate is None:
                gate=gate_reader()
                if type(gate) is not int or not 0<=gate<=0xffffffff:raise ValueError('Raw own admission gate required')
                self.gate=gate
            tick=raw_tick(clock) if self.gate else None
            decision=enqueue(self.queue,self.packet.payload,len(self.packet.payload),0,self.gate,tick)
            if decision.state is None:return result(False,decision.status)
            self.queue=decision.state;self.final=result(True,decision.status);return self.final
        except (ValueError,OSError,StopIteration) as error:return result(False,'needs_own_observation:'+str(error))
