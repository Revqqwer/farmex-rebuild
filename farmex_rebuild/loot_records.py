"""00413f18 creation plan and source84-byte record capture decoding.

No memory access or allocator emulation. Creation needs explicit lookup and
clock observations. Three source stack padding bytes are uninitialized; callers
must supply them before materializing an image. Distance is a separate helper
observation, not inferred from lookup pointer or source ID.
"""
from dataclasses import dataclass
from typing import Optional
from operation_engine import LootRecord
from loot_classifier import LootListState

SIZE=0x54
PADDING_OFFSETS=(0x45,0x46,0x47)

def _dword(value):
    if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Raw DWORD required')

@dataclass(frozen=True)
class LootCreationPlan:
    status:str
    bundle_id:Optional[int]=None
    source_id:Optional[int]=None
    lookup_result:Optional[int]=None
    created_tick:Optional[int]=None
    missing:str=''
    independently_verified:bool=False

@dataclass(frozen=True)
class DecodedLootRecord:
    raw:bytes
    bundle_id:int
    source_id:int
    lookup_result:int
    nonzero_count:int
    model:LootRecord
    independently_verified:bool=False

def plan_loot_creation(captured,enabled_byte,*,lookup_result=None,created_tick=None):
    if type(captured) is not bytes:raise ValueError('Immutable captured bytes required')
    if type(enabled_byte) is not int or not 0<=enabled_byte<=255:raise ValueError('Raw dispatch BYTE required')
    if not captured:return LootCreationPlan('needs_capture_observation',missing='opcode byte0')
    if captured[0]!=0x23:return LootCreationPlan('not_creation_opcode')
    if not enabled_byte:return LootCreationPlan('dispatch_disabled')
    if len(captured)<10:return LootCreationPlan('needs_capture_observation',missing='creation guard byte9')
    if not captured[9]:return LootCreationPlan('creation_guard_zero')
    # Source reads ID at+1 first; local record base isEBP-5c, this field-58.
    source_id=int.from_bytes(captured[1:5],'little')
    bundle=int.from_bytes(captured[5:9],'little')
    if lookup_result is None:
        return LootCreationPlan('needs_lookup_observation',bundle,source_id,missing='00464a10(source_id) EAX')
    _dword(lookup_result)
    if created_tick is None:
        return LootCreationPlan('needs_clock_observation',bundle,source_id,lookup_result,missing='creation GetTickCount')
    _dword(created_tick)
    return LootCreationPlan('local_append_plan',bundle,source_id,lookup_result,created_tick)

def materialize_created_record(plan,padding):
    if not isinstance(plan,LootCreationPlan) or plan.status!='local_append_plan':
        raise ValueError('Complete local creation plan required')
    if type(padding) is not bytes or len(padding)!=3:raise ValueError('Explicit three source padding bytes required')
    for value in (plan.bundle_id,plan.source_id,plan.lookup_result,plan.created_tick):_dword(value)
    raw=bytearray(SIZE)
    for at,value in ((0,plan.bundle_id),(4,plan.source_id),(8,plan.lookup_result),(0x48,plan.created_tick)):
        raw[at:at+4]=value.to_bytes(4,'little')
    raw[0x45:0x48]=padding
    return bytes(raw)

def decode_loot_record(captured,reference,*,distance):
    if type(captured) is not bytes or len(captured)!=SIZE:raise ValueError('Exactly84 captured source bytes required')
    def dword(at):return int.from_bytes(captured[at:at+4],'little')
    state=LootListState(captured[0x33],captured[0x34],tuple(captured[0x35:0x3d]),tuple(captured[0x3d:0x45]))
    model=LootRecord(reference,dword(0x48),item_ids=tuple(dword(0xc+4*i) for i in range(8)),
        slot_done=tuple(bool(v) for v in state.done),item_phase=bool(captured[0x30]),
        disposed_flags=tuple(bool(captured[i]) for i in (0x31,0x32,0x34)),
        open_attempt_ms=dword(0x4c),item_attempt_ms=dword(0x50),distance=distance,list_state=state)
    return DecodedLootRecord(captured,dword(0),dword(4),dword(8),dword(0x2c),model)
