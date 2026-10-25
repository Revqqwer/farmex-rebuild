"""00464918 operand and normal-return plans; never invokes a target.

Static initializer literals are not loaded-game observations or callable ABIs.
PUSHAD/POPAD preserve caller EAX: a native return is not a send-success result.
"""
from dataclasses import dataclass
from types import MappingProxyType

SOURCE_SENDER_DEFAULTS = MappingProxyType({
    'current_us': ((0x553e84,0x1128a94),(0x553e90,0x70b360)),
    'current_steam': ((0x553e84,0x11eaa84),(0x553e90,0x6241a0)),
})

def _dword(value,optional=False):
    if optional and value is None:return
    if type(value) is not int or not 0<=value<=0xffffffff:
        raise ValueError('Raw sender DWORD required')

@dataclass(frozen=True)
class SenderObservation:
    buffer_pointer_dword: object = None
    observed_payload: object = None
    global_samples: tuple = ()
    direct_samples: tuple = ()
    native_normal_returned: object = None

    def __post_init__(self):
        _dword(self.buffer_pointer_dword,True)
        if self.observed_payload is not None and type(self.observed_payload) is not bytes:
            raise ValueError('Immutable bound payload snapshot required')
        for name in ('global_samples','direct_samples'):
            rows=getattr(self,name)
            if type(rows) is not tuple:
                raise ValueError('Ordered immutable sender observations required')
            for row in rows:
                if type(row) is not tuple or len(row)!=2:
                    raise ValueError('Sender address/value pair required')
                _dword(row[0]);_dword(row[1])
        if self.native_normal_returned is not None and type(self.native_normal_returned) is not bool:
            raise ValueError('Separate native call normal-return receipt required')

@dataclass(frozen=True)
class SenderCallPlan:
    target: int
    ecx: int
    push_order: tuple
    assumed_callee_cleanup_bytes: int = 8
    source_preserves_caller_registers: bool = True
    source_preserves_caller_flags: bool = True
    abi_verified: bool = False

@dataclass(frozen=True)
class SourceSenderPlan:
    complete: bool
    status: str
    call: object = None
    steps: tuple = ()
    missing: str = ''
    native_execution_verified: bool = False
    acknowledgement_verified: bool = False

def plan_source_sender(length_dword,observation,*,expected_payload=None):
    _dword(length_dword)
    if not isinstance(observation,SenderObservation):
        raise ValueError('Typed sender operand observations required')
    if expected_payload is not None and (type(expected_payload) is not bytes or len(expected_payload)!=length_dword):
        raise ValueError('Bound own payload must match source length argument')
    o=observation;steps=[];call=None;positions={'global':0,'direct':0}
    class Missing(Exception):pass
    def read(kind,address):
        rows=o.global_samples if kind=='global' else o.direct_samples
        index=positions[kind];steps.append((kind,address))
        if index>=len(rows):raise Missing('%s DWORD %08x'%(kind,address))
        actual,value=rows[index]
        if actual!=address:raise ValueError('Sender %s read %d address differs from source order'%(kind,index))
        positions[kind]+=1
        return value
    def result(ok,status,missing=''):
        return SourceSenderPlan(ok,status,call,tuple(steps),missing)
    try:
        slot=read('global',0x553e84)
        context=read('direct',slot) # Source has no null guard here.
        if o.buffer_pointer_dword is None:raise Missing('sender payload pointer DWORD')
        # This comparison is an own binding/provenance gate, not a vendor read.
        if expected_payload is not None:
            if o.observed_payload is None:raise Missing('bound payload byte snapshot')
            if o.observed_payload!=expected_payload:raise ValueError('Bound sender payload differs from queued record')
        steps.append(('push_length_then_pointer',length_dword,o.buffer_pointer_dword))
        target=read('global',0x553e90)
        call=SenderCallPlan(target,context,(length_dword,o.buffer_pointer_dword))
        if o.native_normal_returned is not True:raise Missing('indirect sender target normal return')
        return result(True,'source_sender_span_returned')
    except Missing as error:
        return result(False,'needs_observation',str(error))
