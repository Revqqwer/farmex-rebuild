"""Richard004edf34 repair orchestration from explicit raw helper observations."""
from dataclasses import dataclass,replace
from types import MappingProxyType
from typing import Optional, Tuple
from repair_packets import repair_payload
from repair_inventory import count_repair_candidates,RepairInventoryObservation


@dataclass(frozen=True)
class RepairObservation:
    now_ms: int
    current_target: Optional[int] = None
    candidate_count_4edc40: Optional[int] = None
    item_id_4634a4: Optional[int] = None
    durability_46358c: Optional[int] = None
    maximum_4635e0: Optional[int] = None
    mode0_cache_match: Optional[bool] = None
    mode2_type_matches: Tuple[Optional[bool],Optional[bool]] = (None,None)
    producer_item_id_4634a4: Optional[int] = None
    candidate_inventory: object = None

    def __post_init__(self):
        if type(self.now_ms) is not int or not 0<=self.now_ms<=0xffffffff:raise ValueError('DWORD clock required')
        for value in (self.current_target,self.candidate_count_4edc40,self.item_id_4634a4,
                      self.durability_46358c,self.maximum_4635e0,self.producer_item_id_4634a4):
            if value is not None and (type(value) is not int or not 0<=value<=0xffffffff):
                raise ValueError('Observed DWORD helper return required')
        if len(self.mode2_type_matches)!=2:raise ValueError('Two source type comparisons required')
        for value in (self.mode0_cache_match,)+tuple(self.mode2_type_matches):
            if value is not None and type(value) is not bool:raise ValueError('Observed bool or unknown required')


@dataclass(frozen=True)
class RepairResult:
    status: str
    fields: object
    globals: object
    returned_phase: Optional[int] = None
    calls: Tuple[str,...] = ()
    missing: str = ''
    queue_payloads: Tuple[bytes,...] = ()


class _Missing(Exception):pass


def repair_step(source_fields,source_globals,observation):
    if not isinstance(observation,RepairObservation):raise ValueError('Typed repair observation required')
    fields,globals=dict(source_fields),dict(source_globals);calls=[];packets=[]
    if any(type(k) is not int or type(v) is not int for mapping in (fields,globals) for k,v in mapping.items()):
        raise ValueError('Raw integer field/global maps required')
    def need(value,name):
        if value is None:raise _Missing(name)
        return value
    def f(offset):return need(fields.get(offset),'field+%x'%offset)
    def g(address):return need(globals.get(address),'global%08x'%address)
    def signed(value):
        value &= 0xffffffff
        return value-0x100000000 if value&0x80000000 else value
    def result(status,missing=''):
        return RepairResult(status,MappingProxyType(dict(fields)),MappingProxyType(dict(globals)),
                            fields.get(0x640),tuple(calls),missing,tuple(packets))
    def advance(wait=False):
        phase=f(0x640)&0xffffffff
        steps={1:4,4:6,6:8,8:10,10:12,12:13}
        if wait and phase==0:fields[0x640]=1
        elif phase in steps:fields[0x640]=steps[phase]
        elif signed(phase)>12:fields[0x640]=(phase+1)&0xffffffff
    def begin():
        fields.update({0x644:1,0x648:observation.now_ms,0x64c:0})
        return result('waiting')
    def repair(kind):
        globals.update({0x561fb0:0xffffffff,0x561fab:kind,0x561fac:f(0x640)&255})
        calls.append('004c8fdc' if kind==1 else '004c9078')
        # Producer performs a separate item-ID read; never reuse the earlier gate value.
        calls.append('004634a4:producer')
        item_id=need(observation.producer_item_id_4634a4,'producer004634a4 item ID')
        packets.append(repair_payload(kind,f(0x604)&0xffffffff,globals[0x561fac],item_id))
        calls.append('004c7710')
        return begin()
    try:
        if f(0x644)!=0:
            wait=200 if g(0x553e44)!=0 else 1000
            start=((f(0x64c)&0xffffffff)<<32)|(f(0x648)&0xffffffff)
            elapsed=(observation.now_ms-start)&0xffffffffffffffff
            if elapsed&0x8000000000000000:elapsed-=0x10000000000000000
            if elapsed<wait:return result('waiting')
            if (g(0x561fb0)&0xffffffff)!=0xffffffff:
                fields.update({0x644:0,0x648:0,0x64c:0});advance(True)
                return result('advanced')
            return result('waiting_ack')
        phase=f(0x640)&0xffffffff
        # Source queries current target before testing phase0.
        current=need(observation.current_target,'00462630 current target')
        if current!=(f(0x604)&0xffffffff) or phase==0:
            calls.append('004edc40')
            if observation.candidate_inventory is not None:
                if not isinstance(observation.candidate_inventory,RepairInventoryObservation):
                    raise ValueError('Typed repair candidate inventory required')
                if observation.candidate_count_4edc40 is not None:raise ValueError('Candidate inventory conflicts with separate count')
                inventory=observation.candidate_inventory
                if inventory.bag_enabled is None:
                    # Same short-circuit source gate, from this explicit raw frame.
                    enabled=f(0x555)!=0 or g(0x56fad3)!=0 or g(0x56fade)!=0
                    inventory=replace(inventory,bag_enabled=enabled)
                if inventory.mode is None and 0x561f58 in globals:
                    inventory=replace(inventory,mode=globals[0x561f58]&0xffffffff)
                counted=count_repair_candidates(inventory)
                if counted.status!='complete':raise _Missing('004edc40:'+counted.missing)
                candidate_count=counted.count
            else:candidate_count=need(observation.candidate_count_4edc40,'004edc40 candidates')
            if candidate_count==0:
                fields[0x640]=42;return result('advanced')
            f(0x60c);calls.extend(('0046493c','0046fb38'))
            return begin()
        calls.append('004634a4')
        if need(observation.item_id_4634a4,'004634a4 item ID')!=0:
            calls.extend(('0046358c','004635e0'))
            current_durability=need(observation.durability_46358c,'0046358c durability')
            maximum=need(observation.maximum_4635e0,'004635e0 maximum')
            if current_durability<maximum:
                if signed(phase)<14:return repair(1)
                if f(0x555)==0 and g(0x56fad3)==0 and g(0x56fade)==0:
                    fields[0x640]=41;return begin()
                mode=g(0x561f58)&0xffffffff
                if mode==0:
                    if need(observation.mode0_cache_match,'mode0 ordered cache comparison'):return repair(2)
                elif mode==2:
                    for match in observation.mode2_type_matches:
                        if need(match,'00463670 type comparison'):return repair(2)
                # Damaged inventory item not selected: source increments directly.
                fields[0x640]=(phase+1)&0xffffffff
                return result('advanced')
        advance()
        return result('advanced' if fields[0x640]!=phase else 'pending')
    except _Missing as exc:return result('needs_observation',str(exc))
