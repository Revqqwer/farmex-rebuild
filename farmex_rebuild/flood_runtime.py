"""Independent stable-state Flood clock/channel/packet/own-queue loop.

Only local preview records. No native helper receipts, process access, sender,
or server acknowledgement. Unresolved source stack/index cases stay explicit.
"""
import ctypes
from dataclasses import dataclass,replace
from action_queue import QueueState,enqueue
from message_list_producer import MessageListRow
from message_channels import CHANNELS
from message_serializer import WIRE_MODES,COUNTER_OFFSET
from message_toggle import START_CAPTION,STOP_CAPTION

TOGGLE_PATH='frmMain/MainTab/sheetFlood/grpFlood/btnAutoFlood'
START_TEXT=START_CAPTION.decode('ascii');STOP_TEXT=STOP_CAPTION.decode('ascii')

def windows_tick_count():
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetTickCount.argtypes=[];kernel.GetTickCount.restype=ctypes.c_uint32
    return kernel.GetTickCount()

def raw_tick(clock):
    value=clock()
    if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw DWORD clock required')
    return value

def signed(value,bits):return value if value<1<<(bits-1) else value-(1<<bits)

@dataclass(frozen=True)
class FloodRuntimeState:
    enabled:bool=False
    index:int=0
    timestamp:int=0
    caption:str=START_TEXT
    def __post_init__(self):
        if type(self.enabled) is not bool or type(self.index) is not int or not 0<=self.index<=0xffffffff or type(self.timestamp) is not int or not 0<=self.timestamp<(1<<64) or type(self.caption) is not str:raise ValueError('Explicit own Flood state required')

@dataclass(frozen=True)
class FloodRuntimePlan:
    complete:bool
    status:str
    state:FloodRuntimeState
    queue:QueueState
    payload:object=None
    elapsed:object=None
    ticks:tuple=()
    native_execution_verified:bool=False
    delivery_verified:bool=False
    live_compatibility_verified:bool=False

@dataclass(frozen=True)
class OwnedMessagePacket:
    complete:bool
    status:str
    payload:object=None

def prepare_owned_message(row):
    if not isinstance(row,MessageListRow) or type(row.channel_bytes) is not bytes or type(row.message_bytes) is not bytes:raise ValueError('Immutable own channel/message bytes required')
    mode=next((mode for key,literal,mode in CHANNELS if row.channel_bytes==literal),None)
    if mode is None:return OwnedMessagePacket(True,'unknown_channel')
    data=row.message_bytes.split(b'\0',1)[0]
    if 4+len(data)>COUNTER_OFFSET:return OwnedMessagePacket(False,'unresolved_source_stack_alias')
    return OwnedMessagePacket(True,'prepared',bytes((0x10,WIRE_MODES[mode]))+len(data).to_bytes(2,'little')+data)

class OwnedFloodSession:
    def __init__(self):
        self.state=FloodRuntimeState();self.queue=QueueState();self.pending=None
    def toggle(self,caption=None):
        text=self.state.caption if caption is None else caption
        if type(text) is not str:raise ValueError('Own button Text required')
        enabled=text==START_TEXT
        self.state=FloodRuntimeState(enabled,0,0,STOP_TEXT if enabled else START_TEXT)
        self.pending=None
        return self.state
    def advance(self,rows,clock,gate_reader):
        if type(rows) is not tuple or any(not isinstance(r,MessageListRow) for r in rows):raise ValueError('Immutable own compiled records required')
        if not callable(clock) or not callable(gate_reader):raise ValueError('Explicit own clock/gate providers required')
        p=self.pending
        def result(complete,status,payload=None,elapsed=None,ticks=()):
            return FloodRuntimePlan(complete,status,self.state,self.queue,payload,elapsed,tuple(ticks))
        if not self.state.enabled:return result(True,'inactive')
        if p is not None and p['rows']!=rows:return result(False,'changed_during_tick',p.get('payload'),p['elapsed'],p['ticks'])
        try:
            if p is None:
                if not rows:return result(True,'empty')
                first=raw_tick(clock)
                if not 0<=self.state.index<len(rows):return result(False,'unresolved_source_index',ticks=(first,))
                row=rows[self.state.index]
                if type(row.delay_dword) is not int or not 0<=row.delay_dword<=0xffffffff or type(row.channel_bytes) is not bytes or type(row.message_bytes) is not bytes:raise ValueError('Raw own row operands required')
                elapsed=signed((first-self.state.timestamp)&((1<<64)-1),64)
                if elapsed<signed(row.delay_dword,32):return result(True,'waiting',elapsed=elapsed,ticks=(first,))
                packet=prepare_owned_message(row)
                if not packet.complete:return result(False,packet.status,elapsed=elapsed,ticks=(first,))
                p={'rows':rows,'elapsed':elapsed,'ticks':[first],'stage':'post','payload':None,'status':'unknown_channel'}
                if packet.payload is not None:p.update(payload=packet.payload,stage='gate')
                self.pending=p
            if p['stage']=='gate':
                gate=gate_reader()
                if type(gate) is not int or not 0<=gate<=0xffffffff:raise ValueError('Raw local preview admission gate required')
                p['gate']=gate;p['stage']='enqueue'
            if p['stage']=='enqueue':
                tick=raw_tick(clock) if p['gate'] else None
                if tick is not None:p['ticks'].append(tick)
                decision=enqueue(self.queue,p['payload'],len(p['payload']),0,p['gate'],tick)
                if decision.state is None:return result(False,decision.status,p['payload'],p['elapsed'],p['ticks'])
                self.queue=decision.state;p['status']=decision.status;p['stage']='post'
            stamp=raw_tick(clock);p['ticks'].append(stamp)
            index=(self.state.index+1)&0xffffffff
            if index==len(rows):index=0 # Source equality-only reset.
            self.state=replace(self.state,index=index,timestamp=stamp)
            self.pending=None
            return result(True,p['status'],p['payload'],p['elapsed'],p['ticks'])
        except (ValueError,OSError,StopIteration) as error:
            return result(False,'needs_own_observation:'+str(error),None if p is None else p.get('payload'),None if p is None else p['elapsed'],() if p is None else p['ticks'])
