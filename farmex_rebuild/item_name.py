"""00467908 ->0045dca8 captured-byte replay; no process reads or native calls.

Raw storage DWORD selects inline/pointer and supplies copy count; its SDK member
name is unverified. Result is ANSI bytes, not guessed Unicode/codepage text.
"""
from dataclasses import dataclass
from typing import Optional,Tuple
from loot_classifier import raw

@dataclass(frozen=True)
class ItemNameObservation:
    lookup_result:Optional[int]=None
    resolver_type_raw:Optional[int]=None
    metadata_result:Optional[int]=None
    metadata_category:Optional[int]=None
    storage_dword:Optional[int]=None
    pointer_dword:Optional[int]=None
    bad_read_result:Optional[int]=None
    captured:Optional[bytes]=None

    def __post_init__(self):
        for v in (self.lookup_result,self.resolver_type_raw,self.metadata_result,
                  self.storage_dword,self.pointer_dword,self.bad_read_result):raw(v,0xffffffff,True)
        raw(self.metadata_category,255,True)
        if self.captured is not None and type(self.captured) is not bytes:raise ValueError('Immutable captured bytes required')

@dataclass(frozen=True)
class ItemNamePlan:
    status:str
    ansi_bytes:Optional[bytes]=None
    family:Optional[str]=None
    read_address:Optional[int]=None
    read_count:Optional[int]=None
    # Logical helper/field plans, not executable ABI calls.
    calls:Tuple[Tuple[str,Tuple[int,...]],...]=()
    reason:str=''
    independently_verified:bool=False

class _Missing(Exception):pass

def plan_item_name(item_id,observation,*,provided_lookup=0,provided_metadata=0,_observation_reader=None):
    raw(item_id,0xffffffff);raw(provided_lookup,0xffffffff);raw(provided_metadata,0xffffffff)
    if not isinstance(observation,ItemNameObservation):raise ValueError('Typed name observations required')
    o=observation;calls=[];family=None;address=None;count=None
    read=lambda name,count=None:getattr(o,name) if _observation_reader is None else _observation_reader(name,count)
    def need(v,label):
        if v is None:raise _Missing(label)
        return v
    def add(a,*args):calls.append((a,tuple(args)))
    def result(status,data=None,reason=''):
        return ItemNamePlan(status,data,family,address,count,tuple(calls),reason)
    try:
        if item_id==0:return result('empty_item',b'')
        lookup=provided_lookup
        if lookup==0:
            add('00465514',item_id);lookup=need(read('lookup_result'),'lookup_result')
        if lookup==0:return result('empty_lookup',b'')
        metadata=provided_metadata
        if metadata==0:
            add('0045dbdc:resolver_type',(lookup+4)&0xffffffff)
            kind=need(read('resolver_type_raw'),'resolver_type_raw')
            add('00465580',item_id,kind);metadata=need(read('metadata_result'),'metadata_result')
        if metadata==0:return result('empty_metadata',b'')
        add('0045dbdc:name_category',(metadata+0x44)&0xffffffff)
        category=need(read('metadata_category'),'metadata_category')
        if category in (0,1,2,5,11):family='lookup';root=lookup;storage_offset=0x18;data_offset=8
        else:family='metadata';root=metadata;storage_offset=0x14;data_offset=4
        add('0045dc44:storage',(root+storage_offset)&0xffffffff)
        storage=need(read('storage_dword'),'storage_dword')
        # Source reads the first DWORD even for the inline branch.
        add('0045dc44:buffer',(root+data_offset)&0xffffffff)
        pointer=need(read('pointer_dword'),'pointer_dword')
        address=pointer if storage>=16 else (root+data_offset)&0xffffffff
        count=storage if storage>=16 else 255
        add('IsBadReadPtr',address,count)
        if need(read('bad_read_result'),'IsBadReadPtr:EAX')!=0:return result('read_rejected_empty',b'')
        # Source memcpy has a512-byte zero-template local buffer. Preserve the
        # unresolved unsafe source path rather than silently truncating count.
        if count>512:return result('unresolved_source_stack_overflow',reason='Source copy exceeds512-byte template')
        captured=need(read('captured',count),'complete_captured_bytes')
        if len(captured)<count:raise _Missing('complete_captured_bytes:%d'%count)
        add('memcpy:source_buffer',address,count)
        buffer=captured[:count]+b'\0'*(512-count)
        stop=buffer.find(b'\0')
        if stop<0:return result('unresolved_unterminated_source_buffer',reason='Source ANSI constructor reads beyond captured local buffer')
        return result('captured_ansi_name',buffer[:stop])
    except _Missing as exc:
        return result('needs_observation',reason=str(exc))
