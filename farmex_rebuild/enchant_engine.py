"""Richard004f035c local enchant orchestration; queues are plans, not sends."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Optional, Tuple
from zone_names import zone_name_ansi

TEMPLATE=bytes.fromhex('55001233313530005f4b456e6368616e742e6c7561')


@dataclass(frozen=True)
class EnchantObservation:
    now_ms: int
    parameter_ansi: Optional[bytes] = None
    parsed_parameter: Optional[int] = None
    zone_ansi: Optional[bytes] = None
    current_target: Optional[int] = None
    raw_level_462670: Optional[int] = None
    raw_zone_id: Optional[int] = None

    def __post_init__(self):
        if type(self.now_ms) is not int or not 0<=self.now_ms<=0xffffffff:
            raise ValueError('DWORD clock required')
        for name in ('parameter_ansi','zone_ansi'):
            value=getattr(self,name)
            if value is not None and type(value) is not bytes:raise ValueError('Observed ANSI bytes required')
        for name in ('parsed_parameter','raw_level_462670'):
            value=getattr(self,name)
            if value is not None and (type(value) is not int or not -0x80000000<=value<0x80000000):
                raise ValueError('Observed signed32 helper result required')
        if self.current_target is not None and (type(self.current_target) is not int or not 0<=self.current_target<=0xffffffff):
            raise ValueError('DWORD target required')
        if self.raw_zone_id is not None:zone_name_ansi(self.raw_zone_id)
        if self.zone_ansi is not None and self.raw_zone_id is not None:
            raise ValueError('Choose observed zone bytes or zone ID, not both')


@dataclass(frozen=True)
class EnchantResult:
    status: str
    fields: Mapping[int,int]
    returned_phase: Optional[int] = None
    calls: Tuple[str,...] = ()
    queue_payloads: Tuple[bytes,...] = ()
    missing: str = ''


class _Missing(Exception):pass


def enchant_step(source_fields, observation):
    if not isinstance(observation,EnchantObservation):raise ValueError('Typed enchant observation required')
    fields=dict(source_fields);calls=[];packets=[]
    if any(type(k) is not int or type(v) is not int for k,v in fields.items()):
        raise ValueError('Raw integer source fields required')
    def need(value,label):
        if value is None:raise _Missing(label)
        return value
    def f(offset):return need(fields.get(offset),'field+%x'%offset)
    def result(status,missing=''):
        return EnchantResult(status,MappingProxyType(dict(fields)),fields.get(0x6c4),tuple(calls),tuple(packets),missing)
    def wait_start():
        fields.update({0x6c8:1,0x6d0:observation.now_ms,0x6d4:0})
        return result('waiting')
    try:
        # Native parses the route parameter before every branch, including wait.
        parsed=need(observation.parsed_parameter,'StrToInt route parameter')
        phase=f(0x6c4)&0xffffffff
        if f(0x6c8)!=0:
            start=((f(0x6d4)&0xffffffff)<<32)|(f(0x6d0)&0xffffffff)
            elapsed=(observation.now_ms-start)&0xffffffffffffffff
            if elapsed&0x8000000000000000:elapsed-=0x10000000000000000
            if elapsed<500:return result('waiting')
            fields.update({0x6c8:0,0x6d0:0,0x6d4:0,0x6c4:(phase+1)&0xffffffff})
            return result('advanced')
        if phase==0 or need(observation.current_target,'00462630 target')!=(f(0x604)&0xffffffff):
            f(0x60c);calls.append('0046493c')
            return wait_start()
        if phase==7:return wait_start()
        zone=zone_name_ansi(observation.raw_zone_id) if observation.raw_zone_id is not None else need(observation.zone_ansi,'004620bc zone ANSI text')
        packet=bytearray(TEMPLATE)
        if zone in (b'Karus Eslant',b'Luferson'):packet[7],packet[9]=0x35,0x4b
        elif zone in (b'Human Eslant',b'EMC'):packet[7],packet[9]=0x37,0x45
        elif zone==b'Moradon':packet[7],packet[9]=0x38,0x4e
        # Unmatched source zone retains template bytes; no invented rejection.
        if phase==1:
            calls.append('0046fb38')
            return wait_start()
        if phase not in (2,3,4,5,6):return result('pending')
        option=need(observation.parameter_ansi,'route parameter ANSI text')
        if option in (b'0',b'1',b'2',b'3'):
            if phase==6:packet[1]=parsed&255
        elif option==b'4':
            if phase==2:packet[1]=3
            elif phase==3:packet[1]=int(need(observation.raw_level_462670,'00462670 level')>35)
            else:
                fields[0x6c4]=(phase+1)&0xffffffff
                return result('advanced')
        else:return result('pending')
        packets.append(bytes(packet));calls.append('004c7710')
        return wait_start()
    except _Missing as exc:return result('needs_observation',str(exc))
