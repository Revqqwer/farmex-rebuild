"""Captured-buffer replay of004142f4/00414748; no live hook or network IO.

Declared source length and captured backing bytes are independent. The source
helpers read unchecked; missing backing bytes stop our model with a prospective
known prefix, never invented zeroes. Source done writes are not independent
proof that any item was transferred by the real server.
"""
from dataclasses import dataclass,replace
from typing import Optional,Tuple
from collections.abc import Mapping
from operation_engine import LootRecord

@dataclass(frozen=True)
class LootReplyDecision:
    status:str
    records:Tuple[LootRecord,...]
    complete:bool
    reference:Optional[str]=None
    source_marked_slot:Optional[int]=None
    nonzero_count:Optional[int]=None
    quantities:Tuple[int,...]=()
    missing:str=''
    independently_verified:bool=False

def replay_loot_reply(records,bundle_ids,captured,declared_length,enabled_byte):
    records=tuple(records)
    if any(not isinstance(r,LootRecord) for r in records) or not isinstance(bundle_ids,Mapping):
        raise ValueError('Typed records and explicit bundle ID observations required')
    if type(captured) is not bytes:raise ValueError('Immutable captured backing bytes required')
    if type(declared_length) is not int or not 0<=declared_length<=0xffffffff:
        raise ValueError('Raw DWORD declared length required')
    if type(enabled_byte) is not int or not 0<=enabled_byte<=255:raise ValueError('Raw dispatch BYTE required')
    updated=list(records);reference=None;quantities=[]
    class Missing(Exception):pass
    def read(at,size):
        if len(captured)<at+size:raise Missing('captured bytes[%d:%d]'%(at,at+size))
        return int.from_bytes(captured[at:at+size],'little')
    def result(status,complete=True,**kw):
        return LootReplyDecision(status,tuple(updated),complete,reference=reference,
            quantities=tuple(quantities),**kw)
    def find(bundle):
        for i,r in enumerate(records):
            observed=bundle_ids.get(r.reference)
            if observed is None:raise Missing(r.reference+': record+0 bundle DWORD')
            if type(observed) is not int or not 0<=observed<=0xffffffff:raise ValueError('Raw bundle DWORD required')
            if observed==bundle:return i
        return None
    try:
        opcode=read(0,1)
        if opcode not in (0x24,0x26):return result('not_loot_opcode')
        if not enabled_byte:return result('dispatch_disabled')
        if opcode==0x26 and declared_length==2:return result('take_length2_ignored')
        if opcode==0x24:
            bundle=read(1,4);index=find(bundle)
            if index is None:return result('bundle_not_found')
            record=updated[index];reference=record.reference
            signed_length=declared_length-(0x100000000 if declared_length&0x80000000 else 0)
            if signed_length<=6:
                flags=list(record.disposed_flags);flags[1]=True # source+32
                updated[index]=replace(record,item_phase=True,disposed_flags=tuple(flags))
                return result('open_short_marked')
            read(5,1) # Source consumes this byte but does not branch on its value.
            ids=list(record.item_ids);count=0
            for slot in range(8):
                ids[slot]=read(6+6*slot,4)
                count+=int(ids[slot]!=0)
                updated[index]=replace(updated[index],item_ids=tuple(ids))
                q=read(10+6*slot,2);quantities.append(q-(0x10000 if q&0x8000 else 0))
            flags=list(record.disposed_flags)
            if not count:flags[1]=True # Existing+32 is never cleared on nonempty reply.
            updated[index]=replace(updated[index],item_phase=True,disposed_flags=tuple(flags))
            return result('open_items_loaded',nonzero_count=count)
        status=read(1,1);bundle=read(2,4)
        # Status1/2 advances one extra byte. Status3 uses the unshifted layout.
        item=read(7 if status in (1,2) else 6,4)
        if status not in (1,2,3):return result('take_status_ignored')
        index=find(bundle)
        if index is None:return result('bundle_not_found')
        record=updated[index];reference=record.reference
        # Source00414204 matches the first equal item ID, including zero and
        # already-done slots. It does not use a slot number supplied by reply.
        slot=next((i for i,value in enumerate(record.item_ids) if value==item),None)
        if slot is None:return result('item_not_found')
        done=list(record.slot_done);done[slot]=True
        updated[index]=replace(record,slot_done=tuple(done))
        return result('source_done_marked',source_marked_slot=slot)
    except Missing as exc:
        return result('needs_capture_observation',False,missing=str(exc))
