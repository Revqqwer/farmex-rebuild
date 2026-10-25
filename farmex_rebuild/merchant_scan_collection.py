"""Pure004bf040/004bf5d0 merchant queue replay; no live IO or vendor TXT guess."""
import math
from dataclasses import dataclass
from typing import Mapping,Optional,Tuple
from types import MappingProxyType

class _Unknown(Exception):pass
def _need(v,n):
    if v is None:raise _Unknown(n)
    return v
def _dword(v,n,unknown=True):
    if v is None and unknown:return
    if type(v) is not int or not 0<=v<=0xffffffff:raise ValueError(n+' requires DWORD')
def _bool(v,n):
    if v is not None and type(v) is not bool:raise ValueError(n+' requires bool/unknown')

@dataclass(frozen=True)
class MerchantProbe:
    pointer:Optional[int]
    active_byte:Optional[int]=None
    x_float:Optional[float]=None
    y_float:Optional[float]=None
    buy_byte:Optional[int]=None
    distance_after_truncation:Optional[float]=None
    entity_id_dword:Optional[int]=None
    def __post_init__(self):
        _dword(self.pointer,'pointer');_dword(self.entity_id_dword,'entityid')
        for value in (self.active_byte,self.buy_byte):
            if value is not None and (type(value) is not int or not 0<=value<=255):raise ValueError('byte/unknown required')
        for value in (self.x_float,self.y_float,self.distance_after_truncation):
            if value is not None and (type(value) not in (int,float) or not math.isfinite(value)):raise ValueError('finitefloat/unknown required')
        if self.distance_after_truncation is not None and self.distance_after_truncation<0:raise ValueError('distance nonnegative')

@dataclass(frozen=True)
class MerchantRecord:
    entity_id:int
    pointer:int
    buy_flag:int
    def __post_init__(self):
        if type(self.entity_id) is not int or not 0<=self.entity_id<=65535:raise ValueError('WORD id required')
        _dword(self.pointer,'pointer',False)
        if type(self.buy_flag) is not int or self.buy_flag not in (0,1):raise ValueError('source normalizedkind0/1required')

@dataclass(frozen=True)
class MerchantCollectionState:
    queue:Tuple[MerchantRecord,...]=()
    visited_ids:Tuple[int,...]=()
    awaiting_merchant_reply:bool=False # source object+f is local request flag only
    def __post_init__(self):
        if type(self.queue) is not tuple or any(not isinstance(v,MerchantRecord) for v in self.queue):raise ValueError('recordtuple required')
        if type(self.visited_ids) is not tuple or any(type(v) is not int or not 0<=v<=65535 for v in self.visited_ids):raise ValueError('WORDtuple required')
        if type(self.awaiting_merchant_reply) is not bool:raise ValueError('local flagbool required')

@dataclass(frozen=True)
class MerchantCollectionDecision:
    status:str
    state:MerchantCollectionState
    collected_count:int=0
    stopped_probe:Optional[int]=None
    reason:str=''


def collect_merchants(probes,normal_enabled,buy_enabled,state=MerchantCollectionState(),*,_observation_reader=None):
    """Scan explicit lookup observations0..5000 inclusive; clearqueue, retainvisited.

    Coordinates are truncated first; actual00460548 distance is caller observation.
    Missing lookup is unknown; explicitMerchantProbe(pointer=0) means lookupempty.
    Unknown step preserves completed local changes, never fills missing probes.
    """
    if not isinstance(probes,Mapping) or any(type(k) is not int or not 0<=k<=5000 or not isinstance(v,MerchantProbe) for k,v in probes.items()):raise ValueError('probeindexmap required')
    _bool(normal_enabled,'normal');_bool(buy_enabled,'buy')
    if not isinstance(state,MerchantCollectionState):raise ValueError('collectionstate required')
    queue=[];visited=list(state.visited_ids);count=0;index=0
    def read(index,name):
        if _observation_reader is not None:return _observation_reader(index,name)
        if index is None:return normal_enabled if name=='normal_enabled' else buy_enabled
        p=_need(probes.get(index),'lookup:00464a10:%d'%index)
        return getattr(p,name)
    try:
        for index in range(5001):
            pointer=_need(read(index,'pointer'),'pointer:%d'%index)
            if not pointer:continue
            if not _need(read(index,'active_byte'),'byte:554148:%d'%index):continue
            x=math.trunc(_need(read(index,'x_float'),'float:554008:%d'%index));y=math.trunc(_need(read(index,'y_float'),'float:554010:%d'%index))
            if not -0x80000000<=x<=0x7fffffff or not -0x80000000<=y<=0x7fffffff:raise _Unknown('ftol32 overflow:%d'%index)
            buy=1 if _need(read(index,'buy_byte'),'byte:55414c:%d'%index)==1 else 0
            if _need(read(index,'distance_after_truncation'),'00460548:%d'%index)>9.5:continue
            entity=_need(read(index,'entity_id_dword'),'dword:554040:%d'%index)&0xffff
            if entity in visited:continue
            if not buy and not _need(read(None,'normal_enabled'),'flag:+c'):continue
            if buy and not _need(read(None,'buy_enabled'),'flag:+d'):continue
            queue.append(MerchantRecord(entity,pointer,buy));visited.append(entity);count+=1
        return MerchantCollectionDecision('collected',MerchantCollectionState(tuple(queue),tuple(visited),state.awaiting_merchant_reply),count)
    except _Unknown as e:return MerchantCollectionDecision('needs_observation',MerchantCollectionState(tuple(queue),tuple(visited),state.awaiting_merchant_reply),count,index,str(e))


class MerchantCollectionFrame:
    """Own resumable observation replay of one collection invocation.

    Only reached, known scalar observations are frozen. Replaying starts from
    the original state so an already appended entity is neither lost by the
    source queue-clear nor appended twice. No lookup, native helper, queue IO,
    normal-return receipt, or game acquisition is executed by this frame.
    Caller flags are cached per invocation, not a claim of fresh native reads.
    """
    def __init__(self,state=MerchantCollectionState()):
        if not isinstance(state,MerchantCollectionState):raise ValueError('collectionstate required')
        self.initial_state=state;self.state=state;self.last=None
        self.terminal=False;self.abort_reason=None;self._cache={}

    @property
    def consumed_observations(self):return MappingProxyType(dict(self._cache))

    def advance(self,probes=None,normal_enabled=None,buy_enabled=None):
        probes={} if probes is None else probes
        # Validate even terminal calls without changing their frozen outcome.
        if not isinstance(probes,Mapping) or any(type(k) is not int or not 0<=k<=5000 or not isinstance(v,MerchantProbe) for k,v in probes.items()):raise ValueError('probeindexmap required')
        _bool(normal_enabled,'normal');_bool(buy_enabled,'buy')
        if self.terminal:return self.last
        def read(index,name):
            key=(index,name)
            if key in self._cache:return self._cache[key]
            if index is None:value=normal_enabled if name=='normal_enabled' else buy_enabled
            else:
                p=_need(probes.get(index),'lookup:00464a10:%d'%index)
                value=getattr(p,name)
            if value is not None:self._cache[key]=value
            return value
        self.last=collect_merchants(probes,normal_enabled,buy_enabled,self.initial_state,_observation_reader=read)
        self.state=self.last.state;self.terminal=self.last.status=='collected'
        return self.last

    def abort(self,reason):
        if type(reason) is not str or not reason:raise ValueError('explicit abort reason required')
        if not self.terminal:
            self.abort_reason=reason;self.terminal=True
            self.last=MerchantCollectionDecision('aborted',self.state,
                0 if self.last is None else self.last.collected_count,
                None if self.last is None else self.last.stopped_probe,reason)
        return self.last

@dataclass(frozen=True)
class MerchantConsumeDecision:
    status:str
    state:MerchantCollectionState
    record:Optional[MerchantRecord]=None
    request_bytes:Optional[bytes]=None
    target_pointer_offsets:Optional[Tuple[int,int]]=None
    local_target_value:Optional[int]=None
    reason:str=''


def consume_merchant_head(state,normal_enabled,buy_enabled,client_variant=None,queue_count_recheck=None):
    """004bf5d0 consumesFIFO even when type disabled. No timer/timeout here.

    Source target-DWORD write and004c7710 fourbytes are represented as plans.
    Requestsent/+f does not prove merchantreply. Immutablequeue snapshot normally
    makes countrecheck its length; explicit0 models source bounds exception/race.
    """
    if not isinstance(state,MerchantCollectionState):raise ValueError('collectionstate required')
    _bool(normal_enabled,'normal');_bool(buy_enabled,'buy')
    if client_variant is not None and (type(client_variant) is not int or not 0<=client_variant<=255):raise ValueError('variantbyte required')
    if queue_count_recheck is not None and (type(queue_count_recheck) is not int or queue_count_recheck<0):raise ValueError('countinteger required')
    if not state.queue:return MerchantConsumeDecision('queue_empty',state)
    if queue_count_recheck==0:return MerchantConsumeDecision('source_bounds_exception',state,reason='004bf848 throws; does not wrap')
    r=state.queue[0]
    try:
        enabled=_need(buy_enabled if r.buy_flag else normal_enabled,'flag:+d' if r.buy_flag else 'flag:+c')
        if enabled:
            variant=_need(client_variant,'byte:00553e46')
            offsets=(0x698,0x17c) if variant==2 else (0x6ac,0x178)
            data=bytes((0x68,0x51 if r.buy_flag else 0x11,r.entity_id&255,r.entity_id>>8))
            return MerchantConsumeDecision('local_request_plan',MerchantCollectionState(state.queue[1:],state.visited_ids,True),r,data,offsets,r.entity_id)
        return MerchantConsumeDecision('discarded_disabled_kind',MerchantCollectionState(state.queue[1:],state.visited_ids,state.awaiting_merchant_reply),r)
    except _Unknown as e:return MerchantConsumeDecision('needs_observation',state,r,reason=str(e))

@dataclass(frozen=True)
class MerchantExportPlan:
    status:str
    row_count:int
    known_column_indices:Tuple[Tuple[str,int],...]=(('raw_subitem_2',2),('raw_subitem_1',1),('raw_subitem_0',0))
    reason:str='Exact vendor header/filename/row concatenation remains unverified; no TXT serialization is produced'

def plan_vendor_txt_export(rows):
    """004b99f8 static field clues only; deliberately no guessed serializer."""
    if type(rows) is not tuple or any(type(r) is not tuple or any(type(v) is not str for v in r) for r in rows):raise ValueError('synthetic tuple rows ofstrings required')
    return MerchantExportPlan('needs_vendor_format',len(rows))
