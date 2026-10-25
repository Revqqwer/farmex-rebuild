"""00414938/00414984 immutable serializers. No game IO, send or ACK.

Bundle IDs are observed DWORDs at source record+0, never inferred from local
reference strings. Batch completion means serialization only; the lifecycle
may expose a prospective prefix before a missing producer/clock observation.
"""
from dataclasses import dataclass
from typing import Optional,Tuple
from collections.abc import Mapping
from operation_engine import OperationIntent,LootDecision
from action_queue import QueueDecision,enqueue

TAKE_TEMPLATE=bytes.fromhex('2600000000000000000000')

def _dword(value):
    if type(value) is not int or not 0<=value<=0xffffffff:
        raise ValueError('Raw DWORD required')

@dataclass(frozen=True)
class LootPacketPlan:
    status:str
    reference:str
    source_helper:str
    payload:Optional[bytes]=None
    queue_delay_ms:int=0
    missing:str=''

@dataclass(frozen=True)
class LootPacketBatch:
    status:str
    plans:Tuple[LootPacketPlan,...]
    complete:bool
    lifecycle_status:str
    missing:str=''
    independently_verified:bool=False

def plan_loot_packet(intent,bundle_id=None):
    if not isinstance(intent,OperationIntent) or intent.kind not in ('loot_open','loot_item'):
        raise ValueError('Typed loot intent required')
    helper='00414938' if intent.kind=='loot_open' else '00414984'
    if intent.kind=='loot_item':
        _dword(intent.item_id);_dword(intent.slot)
    if bundle_id is None:
        return LootPacketPlan('needs_bundle_id',intent.reference,helper,missing='record+0 bundle DWORD')
    _dword(bundle_id)
    if intent.kind=='loot_open':payload=b'\x24'+bundle_id.to_bytes(4,'little')
    else:
        packet=bytearray(TAKE_TEMPLATE)
        packet[1:5]=bundle_id.to_bytes(4,'little')
        packet[5:9]=intent.item_id.to_bytes(4,'little')
        packet[9]=intent.slot&0xff # Source memcpy copies one byte from DWORD arg.
        payload=bytes(packet)
    return LootPacketPlan('local_packet_plan',intent.reference,helper,payload)

def plan_loot_intents(lifecycle,bundle_ids):
    if not isinstance(lifecycle,LootDecision) or not isinstance(bundle_ids,Mapping):
        raise ValueError('Typed lifecycle and explicit bundle observations required')
    plans=[]
    for intent in lifecycle.intents:
        plan=plan_loot_packet(intent,bundle_ids.get(intent.reference))
        if plan.payload is None:
            return LootPacketBatch(plan.status,tuple(plans),False,lifecycle.status,
                intent.reference+': '+plan.missing)
        plans.append(plan)
    return LootPacketBatch('locally_serialized',tuple(plans),True,lifecycle.status)

def enqueue_loot_intent(state,intent,bundle_id,connection_gate,tick=None):
    plan=plan_loot_packet(intent,bundle_id)
    if plan.payload is None:return QueueDecision(plan.status,None,missing=plan.missing)
    return enqueue(state,plan.payload,len(plan.payload),plan.queue_delay_ms,connection_gate,tick)
