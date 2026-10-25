"""DC/stand own queue seeds and fixed /Town data/stub construction plans.

Never calls Windows allocation/thread APIs, executes code or sends a packet.
Town's opaque thread-helper return is not proof its callback ran successfully.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from action_queue import QueueState,QueueDecision,enqueue

COMMAND_SEEDS=MappingProxyType({'disconnect':b'\x00','stand':b'\x12\x01'})
TOWN_TEXT=b'/Town'
TOWN_STUB=bytes.fromhex('608b0d00000000bf0000000057bf00000000ffd761c3')

def _dword(v,optional=False):
    if optional and v is None:return
    if type(v) is not int or not 0<=v<=0xffffffff:raise ValueError('Raw command helper DWORD required')

@dataclass(frozen=True)
class CommandQueuePlan:
    complete:bool
    key:str
    payload:bytes
    decision:object=None
    missing:str=''
    native_execution_verified:bool=False
    def __post_init__(self):
        if type(self.complete) is not bool or self.key not in COMMAND_SEEDS or self.payload!=COMMAND_SEEDS[self.key] or type(self.payload) is not bytes:
            raise ValueError('Exact typed source command seed required')
        if self.complete and (not isinstance(self.decision,QueueDecision) or self.decision.state is None):
            raise ValueError('Known own enqueue outcome required')
        if self.complete:
            if self.decision.status not in ('locally_enqueued','not_enqueued'):
                raise ValueError('Known source enqueue branch required')
            if self.decision.status=='locally_enqueued' and (not self.decision.events or any(e.payload!=self.payload for e in self.decision.events)):
                raise ValueError('Own enqueue bytes differ from source command seed')

class CommandQueueFrame:
    def __init__(self,key,queue=None):
        if key not in COMMAND_SEEDS:raise ValueError('Source DC/stand queue helper required')
        self.key=key;self.queue=QueueState() if queue is None else queue
        if not isinstance(self.queue,QueueState):raise ValueError('Own command queue required')
        self.gate=None;self.final=None
    def advance(self,gate=None,tick=None):
        if self.final is not None:return self.final
        if self.gate is None:
            _dword(gate,True)
            if gate is not None:self.gate=gate
        payload=COMMAND_SEEDS[self.key]
        d=enqueue(self.queue,payload,len(payload),0,self.gate,tick)
        p=CommandQueuePlan(d.state is not None,self.key,payload,d,d.missing or ('' if d.state is not None else d.status))
        if d.state is not None:self.queue=d.state;self.final=p
        return p

@dataclass(frozen=True)
class TownObservation:
    buffer_address:object=None
    global_samples:tuple=()
    helper_returns:object=field(default_factory=dict)
    def __post_init__(self):
        _dword(self.buffer_address,True)
        if type(self.global_samples) is not tuple:raise ValueError('Ordered Town source globals required')
        for row in self.global_samples:
            if type(row) is not tuple or len(row)!=2:raise ValueError('Town global address/value pair required')
            _dword(row[0]);_dword(row[1])
        returns=dict(self.helper_returns)
        if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate Town normal-return receipts required')
        object.__setattr__(self,'helper_returns',MappingProxyType(returns))

@dataclass(frozen=True)
class TownPlan:
    complete:bool
    status:str
    buffer_address:object=None
    record_image:object=None
    stub_image:object=None
    steps:tuple=()
    missing:str=''
    native_execution_verified:bool=False
    thread_callback_verified:bool=False
    def __post_init__(self):
        if type(self.complete) is not bool:raise ValueError('Known Town plan completion required')
        _dword(self.buffer_address,True)
        if self.record_image is not None and (type(self.record_image) is not bytes or len(self.record_image)!=80):
            raise ValueError('Bounded immutable Town record required')
        if self.stub_image is not None:
            if type(self.stub_image) is not bytes or len(self.stub_image)!=22:
                raise ValueError('Exact bounded Town stub required')
            mutable=set(range(3,7))|set(range(8,12))|set(range(14,18))
            if any(self.stub_image[i]!=TOWN_STUB[i] for i in range(22) if i not in mutable):
                raise ValueError('Town stub opcode differs from source template')
        if self.complete and (type(self.record_image) is not bytes or len(self.record_image)!=0x50 or type(self.stub_image) is not bytes or len(self.stub_image)!=22 or not self.buffer_address or self.missing):
            raise ValueError('Complete bounded Town record/stub construction required')
        if self.complete:
            expected=bytearray(80);expected[:5]=TOWN_TEXT;expected[16]=5;expected[20]=15
            if self.record_image!=bytes(expected) or self.stub_image[8:12]!=self.buffer_address.to_bytes(4,'little'):
                raise ValueError('Town record/stub argument differs from fixed source construction')

def plan_town_helper(o):
    """Fixed /Town scope, observing opaque allocation/copy/thread/cleanup returns."""
    if not isinstance(o,TownObservation):raise ValueError('Typed Town observations required')
    steps=[];record=None;stub=None;index=0
    class Missing(Exception):pass
    def normal(label):
        steps.append(('normal_return',label))
        if o.helper_returns.get(label) is not True:raise Missing(label+' normal return')
    def g(address):
        nonlocal index
        steps.append(('global',address))
        if index>=len(o.global_samples):raise Missing('Town source global%08x'%address)
        actual,value=o.global_samples[index]
        if actual!=address:raise ValueError('Town global read order differs from source')
        index+=1;return value
    def result(ok,status,missing=''):
        return TownPlan(ok,status,o.buffer_address,None if record is None else bytes(record),None if stub is None else bytes(stub),tuple(steps),missing)
    try:
        normal('town_string_construct')
        normal('text_string_lifetime')
        steps.append(('VirtualAlloc_plan',0,0x50,0x1000,0x40));normal('allocate_record')
        if o.buffer_address is None:raise Missing('Town buffer allocation EAX')
        # Source does not test this allocation result before memset/memcpy.
        if o.buffer_address==0:return result(False,'unchecked_null_allocation','native null-buffer fault path unresolved')
        steps.append(('strlen_plan',TOWN_TEXT));normal('strlen')
        steps.append(('memset_plan',o.buffer_address,0,0x50));normal('zero_record');record=bytearray(0x50)
        steps.append(('memcpy_text_plan',o.buffer_address,TOWN_TEXT,len(TOWN_TEXT)));normal('copy_text');record[:5]=TOWN_TEXT
        steps.append(('memcpy_length_BYTE_plan',(o.buffer_address+0x10)&0xffffffff,5));normal('copy_length');record[0x10]=5
        steps.append(('memcpy_type_BYTE_plan',(o.buffer_address+0x14)&0xffffffff,0xf));normal('copy_type');record[0x14]=0xf
        stub=bytearray(TOWN_STUB)
        root_slot=g(0x553e80);normal('patch_root');stub[3:7]=root_slot.to_bytes(4,'little')
        normal('patch_buffer');stub[8:12]=o.buffer_address.to_bytes(4,'little')
        target=g(0x553eec);normal('patch_target');stub[14:18]=target.to_bytes(4,'little')
        steps.append(('00464740_opaque_thread_helper',bytes(stub),22));normal('thread_helper')
        steps.append(('VirtualFree_plan',o.buffer_address,0,0x8000));normal('free_record')
        normal('text_cleanup');normal('text_helper');normal('town_cleanup')
        return result(True,'bounded_town_span_returned')
    except Missing as error:return result(False,'needs_observation',str(error))

class TownFrame:
    def __init__(self):self.observation=TownObservation();self.final=None
    def advance(self,o):
        if not isinstance(o,TownObservation):raise ValueError('Typed Town observations required')
        if self.final is not None:return self.final
        for _ in range(32):
            p=plan_town_helper(self.observation)
            if p.complete:self.final=p;return p
            if p.missing.endswith(' normal return'):
                label=p.missing[:-14]
                if o.helper_returns.get(label) is not True:return p
                self.observation=replace(self.observation,helper_returns={**self.observation.helper_returns,label:True});continue
            if p.missing=='Town buffer allocation EAX':
                if o.buffer_address is None:return p
                self.observation=replace(self.observation,buffer_address=o.buffer_address);continue
            if p.missing.startswith('Town source global'):
                i=len(self.observation.global_samples)
                if i>=len(o.global_samples):return p
                self.observation=replace(self.observation,global_samples=self.observation.global_samples+(o.global_samples[i],));continue
            return p
        raise ValueError('Town frame exceeded source prefix budget')
