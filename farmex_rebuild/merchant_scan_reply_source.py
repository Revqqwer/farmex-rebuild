"""Demand-only captured actor/item producers for one immutable reply.

No native reads/calls. Only reached known scalar observations, successful
normal receipts and complete required byte ranges are retained across polls.
Windows decoding uses an explicit codepage and is an own conversion policy.
"""
from dataclasses import dataclass,field
from types import MappingProxyType
from merchant_actor_metadata import MerchantActorObservation,plan_merchant_actor_metadata
from merchant_item_metadata import MerchantItemObservation,plan_merchant_item_metadata
from merchant_scan_reply_data import decode_merchant_scan_data
from merchant_scan_results import project_merchant_scan_results
from merchant_result_filter import MerchantFilterSelection
from name_codec import WindowsNameCodec


@dataclass(frozen=True)
class ScanReplySource:
    actor:object=None
    items:object=field(default_factory=dict)
    code_page:object=None
    def __post_init__(self):
        if self.actor is not None and not isinstance(self.actor,MerchantActorObservation):raise ValueError('Typed captured actor observations required')
        items=dict(self.items)
        if any(type(k) is not int or not 0<=k<12 or not isinstance(v,MerchantItemObservation) for k,v in items.items()):raise ValueError('Typed captured item observations required')
        if self.code_page is not None and (type(self.code_page) is not int or not 1<=self.code_page<=65535):raise ValueError('Explicit Windows codepage or unknown required')
        object.__setattr__(self,'items',MappingProxyType(items))


@dataclass(frozen=True)
class ScanReplySourceResult:
    complete:bool
    status:str
    results:object
    actor_plan:object=None
    item_plans:tuple=()
    consumed_observations:object=None
    native_execution_verified:bool=False
    native_text_conversion_verified:bool=False
    source_parser_return_verified:bool=False
    live_compatibility_verified:bool=False


class MerchantReplySourceFrame:
    def __init__(self,payload,*,codec_factory=WindowsNameCodec):
        if type(payload) is not bytes or not callable(codec_factory):raise ValueError('Immutable reply and own codec factory required')
        self.payload=payload;self.data=decode_merchant_scan_data(payload)
        self.codec_factory=codec_factory;self.codec=None;self.cache={}
        self.actor=None;self.actor_plan=None;self.items={};self.item_plans={};self.last=None

    def _read(self,root,prefix,path,required_count=None):
        key=prefix+path
        if key in self.cache:return self.cache[key]
        value=root
        for field_name in path:
            if value is None:break
            value=getattr(value,field_name)
        if value is None:return None
        if path[-1].endswith('_returned'):
            if value is True:self.cache[key]=True
        elif required_count is not None:
            # Actor copies require the exact captured range; item-name helpers
            # accept a larger supplied capture but consume only the prefix.
            exact=path[-1]=='copied_bytes'
            if type(value) is bytes and (len(value)==required_count if exact else len(value)>=required_count):
                self.cache[key]=value[:required_count]
        else:self.cache[key]=value
        return self.cache.get(key,value)

    def advance(self,source=None):
        source=ScanReplySource() if source is None else source
        if not isinstance(source,ScanReplySource):raise ValueError('Typed source snapshot required')
        if self.last is not None and self.last.complete:return self.last
        def decode(data):
            if not data:return ''
            key=('code_page',)
            cp=self.cache.get(key)
            if cp is None:
                cp=source.code_page
                if cp is None:raise ValueError('Explicit source codepage required')
                self.cache[key]=cp
            if self.codec is None:self.codec=self.codec_factory(cp)
            return self.codec.decode(data)
        pending=None
        nonempty=tuple(s for s in self.data.slots if s.item_id)
        if self.data.source_length_gate_passed and nonempty:
            if self.actor is None:
                self.actor_plan=plan_merchant_actor_metadata(self.data.entity_id,source.actor,decode,
                    _observation_reader=lambda path,count=None:self._read(source.actor,('actor',),path,count))
                if self.actor_plan.complete:self.actor=self.actor_plan.metadata
                else:pending='actor:'+self.actor_plan.status
            if self.actor is not None:
                for slot in nonempty:
                    if slot.index in self.items:continue
                    item=source.items.get(slot.index)
                    plan=plan_merchant_item_metadata(slot.item_id,item,decode,
                        _observation_reader=lambda path,count=None,item=item,index=slot.index:
                            self._read(item,('item',index),path,count))
                    self.item_plans[slot.index]=plan
                    if not plan.complete:
                        pending='item:%d:%s'%(slot.index,plan.status);break
                    self.items[slot.index]=plan.metadata
        results=project_merchant_scan_results(self.payload,self.actor,self.items,
            MerchantFilterSelection('','',0x808080,0))
        self.last=ScanReplySourceResult(results.complete and pending is None,
            pending or results.status,results,self.actor_plan,tuple(self.item_plans.items()),
            MappingProxyType(dict(self.cache)))
        return self.last
