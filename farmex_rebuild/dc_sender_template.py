"""Inert normal control model of00464834/004647b8; never calls remote APIs."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
import struct
from jail_protection import JailObservation
from jail_preload import JailPreloadFrame,MASK
from dc_propagation import DCConsumerFrame

SENDER_TEMPLATE=bytes.fromhex('60 8b 0d 00 00 00 00 68 00 00 00 00 68 00 00 00 00 bf 00 00 00 00 ff d7 61 c3')

def patched_sender_template(root_slot,length,pointer,target):
    values=(root_slot,length,pointer,target)
    if any(type(v) is not int or not 0<=v<=MASK for v in values):raise ValueError('Raw copied DWORD fields required')
    out=bytearray(SENDER_TEMPLATE)
    for at,value in zip((3,8,13,18),values):struct.pack_into('<I',out,at,value)
    return bytes(out)

@dataclass(frozen=True)
class DCTransferPlan:
    complete: bool
    calls: tuple=()
    write_intents: tuple=()
    stub_bytes: object=None
    patches: tuple=()
    needed: object=None
    whole_function_verified: bool=False
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False

class DCTransferFrame(JailPreloadFrame):
    def __init__(self,handle,payload):
        if type(handle) is not int or not 0<=handle<=MASK or type(payload) is not bytes or len(payload)>MASK:
            raise ValueError('Raw handle and immutable owned DWORD-length payload required')
        self.handle=handle;self.payload=payload;self.stub=None;self.patches=[];self.writes=[]
        super().__init__()
    def _plan(self,complete=False):
        return DCTransferPlan(complete,tuple(self.calls),tuple(self.writes),None if self.stub is None else bytes(self.stub),
                              tuple(self.patches),None if complete else self._needed)
    def _patch(self,at,value,label):
        struct.pack_into('<I',self.stub,at,value);self.patches.append((at,value,label))
    def _child(self,stub):
        yield from self._call('stub.prologue','source004647b8_prologue_span')
        yield from self._call('stub.allocate','VirtualAllocEx',(0x40,0x1000,26,0,self.handle))
        address=yield from self._value('stub_allocation_eax')
        if address:
            self.writes.append(('stub',address,stub))
            yield from self._call('stub.write','WriteProcessMemory',(0,26,('owned_stub_bytes',stub),address,self.handle))
            yield from self._call('stub.thread','CreateRemoteThread',(0,0,0,address,0,0,self.handle))
            thread=yield from self._value('thread_eax')
            if thread:yield from self._call('stub.wait','WaitForSingleObject',(MASK,thread))
            # The source closes even a zero CreateRemoteThread result.
            yield from self._call('stub.close','CloseHandle',(thread,))
            yield from self._call('stub.free','VirtualFreeEx',(0x8000,0,address,self.handle))
        yield from self._call('stub.epilogue','source004647b8_stack_return_span')
    def _run(self):
        yield ('entry','00464834')
        yield from self._call('prologue','source_SEH_prologue_span')
        yield from self._call('template_copy','source26byte_local_template_copy')
        self.stub=bytearray(SENDER_TEMPLATE)
        yield from self._call('payload.allocate','VirtualAllocEx',(0x40,0x1000,len(self.payload),0,self.handle))
        address=yield from self._value('payload_allocation_eax')
        if address:
            self.writes.append(('payload',address,self.payload))
            yield from self._call('payload.write','WriteProcessMemory',
                                  (0,len(self.payload),('owned_payload_bytes',self.payload),address,self.handle))
            yield from self._call('copy.root','_memcpy',(4,('global',0x553e84),('local_stub',3)))
            root=yield from self._value('copied_root_dword');self._patch(3,root,'copied_root_dword')
            yield from self._call('copy.length','_memcpy',(4,'source_length_argument',('local_stub',8)))
            self._patch(8,len(self.payload),'length')
            yield from self._call('copy.pointer','_memcpy',(4,'source_allocation_local',('local_stub',13)))
            self._patch(13,address,'payload_allocation')
            yield from self._call('copy.target','_memcpy',(4,('global',0x553e90),('local_stub',18)))
            target=yield from self._value('copied_target_dword');self._patch(18,target,'copied_target_dword')
            stub=bytes(self.stub)
            self.calls.append(('004647b8',(26,('local_stub_bytes',stub),self.handle),'stub_outer'))
            yield from self._child(stub)
            # Complete child still needs its separate parent normal-return receipt.
            yield ('normal','stub_outer')
            yield from self._call('payload.free','VirtualFreeEx',(0x8000,0,address,self.handle))
        yield from self._call('epilogue','source_FS_restore_stack_return_span')

@dataclass(frozen=True)
class DCSenderObservation:
    consumer: JailObservation=field(default_factory=JailObservation)
    transfers: object=field(default_factory=dict)
    def __post_init__(self):
        if not isinstance(self.consumer,JailObservation):raise ValueError('Typed consumer observation required')
        transfers=dict(self.transfers)
        if any(type(k) is not str or not isinstance(v,JailObservation) for k,v in transfers.items()):
            raise ValueError('Reached sender labels must have typed observations')
        object.__setattr__(self,'transfers',MappingProxyType(transfers))

@dataclass(frozen=True)
class DCSenderPlan:
    complete: bool
    consumer: object
    transfers: object=field(default_factory=dict)
    needed: object=None
    native_execution_verified: bool=False
    live_compatibility_verified: bool=False
    def __post_init__(self):object.__setattr__(self,'transfers',MappingProxyType(dict(self.transfers)))

class DCSenderConsumerFrame:
    """Bind each reached source sender call; don't bypass child/outer receipts."""
    def __init__(self,kind,*,context=0x5690f8):
        self.consumer=DCConsumerFrame(kind,context=context)
        self.children={};self.plans={};self.returned=set();self.final=None
    def advance(self,o):
        if not isinstance(o,DCSenderObservation):raise ValueError('Typed sender binding required')
        if self.final is not None:return self.final
        while True:
            normals=dict(o.consumer.normal_returns)
            for key in normals:
                if key.endswith('.send') and key not in self.returned:normals[key]=False
            p=self.consumer.advance(replace(o.consumer,normal_returns=normals))
            if p.complete:
                self.final=DCSenderPlan(True,p,self.plans);return self.final
            kind,label=p.needed
            if kind!='normal' or not label.endswith('.send'):
                return DCSenderPlan(False,p,self.plans,('consumer',p.needed))
            if label not in self.children:
                helper,args,_=p.calls[-1];handle,payload=p.payload_intents[-1]
                if helper!='00464834' or args[0]!=len(payload) or args[-1]!=handle:
                    raise AssertionError('Reached source sender arguments disagree')
                self.children[label]=DCTransferFrame(handle,payload)
            child=self.children[label].advance(replace(o.transfers.get(label,JailObservation()),entry_reached=True))
            self.plans[label]=child
            if not child.complete:return DCSenderPlan(False,p,self.plans,('sender',label,child.needed))
            if o.consumer.normal_returns.get(label) is not True:
                return DCSenderPlan(False,p,self.plans,('consumer',p.needed))
            self.consumer.advance(JailObservation(normal_returns={label:True}))
            self.returned.add(label)
