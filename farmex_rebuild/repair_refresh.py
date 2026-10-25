"""00467f10 operand plans for the zero-extended561fac BYTE caller.

No memory reads, writes, protection changes or native execution. Ordered input
samples keep repeated root reads independent. Complete means operands known,
not that any requested write succeeded or that the helper returned.
"""
from dataclasses import dataclass,field
from types import MappingProxyType
from storage_native_plans import NativeCallPlan

@dataclass(frozen=True)
class RepairRefreshObservation:
    value:int
    slot:int
    globals:object=field(default_factory=dict)
    protected_samples:tuple=()
    direct_samples:tuple=()
    second_profile_byte:object=None

    def __post_init__(self):
        if type(self.value) is not int or not 0<=self.value<=0xffffffff:raise ValueError('Reply DWORD required')
        if type(self.slot) is not int or not 0<=self.slot<=255:raise ValueError('Source caller slot BYTE required')
        if self.second_profile_byte is not None and (type(self.second_profile_byte) is not int or not 0<=self.second_profile_byte<=255):
            raise ValueError('Fresh second profile BYTE required')
        for k,v in self.globals.items():
            if type(k) is not int or type(v) is not int or not 0<=k<=0xffffffff or not 0<=v<=0xffffffff:
                raise ValueError('Raw DWORD globals required')
        object.__setattr__(self,'globals',MappingProxyType(dict(self.globals)))
        for name in ('protected_samples','direct_samples'):
            rows=tuple(tuple(row) for row in getattr(self,name))
            for row in rows:
                if len(row)!=2 or any(type(v) is not int or not 0<=v<=0xffffffff for v in row):
                    raise ValueError('Ordered address/DWORD samples required')
            object.__setattr__(self,name,rows)

@dataclass(frozen=True)
class RepairRefreshPlan:
    status:str
    complete:bool
    reads:tuple=()
    write_requests:tuple=()
    native_call:object=None
    missing:str=''
    native_execution_verified:bool=False
    memory_effects_verified:bool=False
    helper_return_verified:bool=False

class _Missing(Exception):pass

def plan_repair_refresh(observation):
    if not isinstance(observation,RepairRefreshObservation):raise ValueError('Typed repair refresh observations required')
    obs=observation;reads=[];writes=[];positions={'protected':0,'direct':0};call=None
    def g(address):
        if address not in obs.globals:raise _Missing('global%08x'%address)
        return obs.globals[address]
    def word(address,kind='protected'):
        address&=0xffffffff
        samples=obs.protected_samples if kind=='protected' else obs.direct_samples
        index=positions[kind]
        if index>=len(samples):raise _Missing('%s sample%d DWORD%08x'%(kind,index,address))
        at,value=samples[index]
        if at!=address:raise ValueError('Observed %s sample%d address mismatch: expected%08x, got%08x'%(kind,index,address,at))
        positions[kind]+=1;reads.append((kind,address,value));return value
    def write(address,value,size):
        writes.append(('0045ddf4' if size==4 else '0045de4c',address&0xffffffff,value.to_bytes(size,'little')))
    def result(status,complete=False,missing=''):
        return RepairRefreshPlan(status,complete,tuple(reads),tuple(writes),call,missing)
    try:
        root=word(g(0x553e80))
        inventory=word(root+g(0x5540a8))
        slot_pointer=word(inventory+g(0x5540ac)+(obs.slot*4&0xffffffff))
        fresh_root=word(g(0x553e80))
        fresh_inventory=word(fresh_root+g(0x5540a8))
        scratch=(fresh_inventory+g(0x5540b8))&0xffffffff
        write(scratch+0x20,slot_pointer,4)
        write(scratch+0x24,1 if obs.slot<=13 else 2,4)
        write(scratch+0x28,obs.slot if obs.slot<=13 else obs.slot-14,4)
        profile=g(0x553e46)
        if profile>255:raise ValueError('Source profile BYTE required')
        selected=1 if profile==1 else 0
        if profile!=1:
            if obs.second_profile_byte is None:raise _Missing('second profile BYTE00553e46')
            if obs.second_profile_byte==2:selected=2
        if selected:
            direct_root=word(g(0x553e80),'direct')
            direct_inventory=word(direct_root+g(0x5540a8),'direct')
            context=(direct_inventory+(g(0x5540b8) if selected==1 else 0))&0xffffffff
            call=NativeCallPlan(g(0x553ef8),context,(obs.value,1),True)
        # These writes are requests, not successful VirtualProtect/memcpy effects.
        write(g(0x553ef4),0,1)
        return result('refresh_operands_planned',True)
    except _Missing as exc:return result('needs_observation',missing=str(exc))
