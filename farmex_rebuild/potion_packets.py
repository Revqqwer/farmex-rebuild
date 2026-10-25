"""004c84e4 direct potion serializer, with fresh explicit actor observation.

Template at005476c0 is30bytes. Action ID is not inventory ID. The actor's
lowWORD is copied twice. Alternate00465640 remains a native call, not a packet.
"""
from dataclasses import dataclass
from typing import Optional
from potion_engine import PotionIntent
from action_queue import QueueDecision, enqueue
from skill_native_plans import SkillObservation, plan_alternate_skill
from native_profile_versions import VersionedNativeObservation,plan_versioned_native

TEMPLATE=bytes.fromhex('3103'+'00'*28)


@dataclass(frozen=True)
class PotionPacketPlan:
    status: str
    payload: Optional[bytes] = None
    queue_delay_ms: int = 0
    missing: str = ''


def plan_potion_packet(intent,actor_id=None):
    if not isinstance(intent,PotionIntent):raise ValueError('Typed potion intent required')
    if intent.kind not in ('hp','mp','special'):raise ValueError('Source potion kind required')
    if type(intent.action_id) is not int or not 0<=intent.action_id<=0xffffffff:
        raise ValueError('Raw DWORD action ID required')
    if intent.action_path=='alternate':
        return PotionPacketPlan('needs_native_call',missing='00465640 target/ABI')
    if intent.action_path!='direct':raise ValueError('Explicit direct/alternate path required')
    if actor_id is None:return PotionPacketPlan('needs_observation',missing='fresh 00462650 actor ID')
    if type(actor_id) is not int or not 0<=actor_id<=0xffffffff:raise ValueError('Raw DWORD actor ID required')
    payload=bytearray(TEMPLATE)
    payload[2:6]=intent.action_id.to_bytes(4,'little')
    actor=(actor_id&0xffff).to_bytes(2,'little')
    payload[6:8]=actor;payload[10:12]=actor
    return PotionPacketPlan('local_packet_plan',bytes(payload))


def enqueue_potion_intent(state,intent,actor_id,connection_gate,tick=None):
    plan=plan_potion_packet(intent,actor_id)
    if plan.payload is None:return QueueDecision(plan.status,None,missing=plan.missing)
    return enqueue(state,plan.payload,len(plan.payload),plan.queue_delay_ms,connection_gate,tick)


def plan_alternate_potion(intent,observation):
    if not isinstance(intent,PotionIntent) or intent.action_path!='alternate':
        raise ValueError('Explicit alternate potion intent required')
    if isinstance(observation,VersionedNativeObservation):
        if observation.kind!='skill' or observation.observation.action_id!=intent.action_id:
            raise ValueError('Versioned skill observation must match potion action ID')
        return plan_versioned_native(observation)
    if not isinstance(observation,SkillObservation) or observation.action_id!=intent.action_id:
        raise ValueError('Native action observation must match potion action ID')
    return plan_alternate_skill(observation)
