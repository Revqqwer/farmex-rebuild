"""00467cc4 arithmetic using observed clock/CRT results; no RNG execution."""
from dataclasses import dataclass
from crt_rng import replay_crt_seeded_pair

def _dword(value):
    if value is not None and (type(value) is not int or not 0<=value<1<<32):
        raise ValueError('Raw DWORD required')

def _signed(value):
    value&=0xffffffff
    return value-(1<<32) if value&0x80000000 else value

@dataclass(frozen=True)
class SourceRandomObservation:
    tick:object=None
    srand_returned:object=None
    rand_eax:object=None
    disk_crt_replay:bool=False
    same_thread_context:object=None
    def __post_init__(self):
        _dword(self.tick);_dword(self.rand_eax)
        if self.srand_returned is not None and type(self.srand_returned) is not bool:
            raise ValueError('Explicit srand normal-return observation required')
        if type(self.disk_crt_replay) is not bool:raise ValueError('Explicit disk CRT replay choice required')
        if self.same_thread_context is not None and type(self.same_thread_context) is not bool:
            raise ValueError('Explicit stable thread-context contract required')

@dataclass(frozen=True)
class SourceRandomPlan:
    status:str
    complete:bool
    result_dword:object=None
    divisor_signed:object=None
    quotient_signed:object=None
    remainder_signed:object=None
    calls:tuple=()
    missing:str=''
    native_execution_verified:bool=False
    crt_replay:object=None
    rand_source:str='unavailable'

def replay_source_random(lower,upper,observation):
    _dword(lower);_dword(upper)
    if lower is None or upper is None or not isinstance(observation,SourceRandomObservation):
        raise ValueError('Explicit bounds and typed random observations required')
    o=observation;calls=[('005074da',())];divisor=None;quotient=None;remainder=None
    crt_replay=None;rand_source='unavailable'
    def result(status,complete=False,value=None,missing=''):
        return SourceRandomPlan(status,complete,value,divisor,quotient,remainder,tuple(calls),missing,
                                crt_replay=crt_replay,rand_source=rand_source)
    if o.tick is None:return result('needs_random_observation',missing='random helper GetTickCount DWORD')
    calls.append(('00507966',(o.tick,)))  # historical import identity _srand
    if o.srand_returned is not True:
        return result('needs_random_observation',missing='random helper srand normal return')
    calls.append(('00507942',()))         # historical import identity _rand
    if o.disk_crt_replay:
        if o.rand_eax is not None:raise ValueError('Disk CRT replay cannot also assert observed rand EAX')
        if o.same_thread_context is not True:
            return result('needs_random_observation',missing='disk CRT replay stable thread context')
        crt_replay=replay_crt_seeded_pair(o.tick)
        rand_eax=crt_replay.output.result_eax;rand_source='local_disk_crt_replay'
    else:
        if o.rand_eax is None:return result('needs_random_observation',missing='random helper rand EAX DWORD')
        rand_eax=o.rand_eax;rand_source='observed_crt_eax'
    divisor=_signed(upper-lower+1)
    if divisor==0:return result('integer_divide_by_zero')
    dividend=_signed(rand_eax)
    quotient=abs(dividend)//abs(divisor)
    if (dividend<0)!=(divisor<0):quotient=-quotient
    if not -(1<<31)<=quotient<(1<<31):return result('integer_divide_overflow')
    remainder=dividend-quotient*divisor
    return result('random_return_planned',True,(remainder+lower)&0xffffffff)
