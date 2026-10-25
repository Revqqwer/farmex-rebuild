"""41dec8 ordered BUY list preparation; private local vectors, no VCL/heap IO.

Numeric replay is an explicit decimal subset of Delphi conversion. Unknown
conversion and helper returns remain gaps, never synthesized failure values.
"""
import re
from dataclasses import dataclass,field,replace
from collections.abc import Mapping
from types import MappingProxyType

BUY_LIST_PATH='frmMain/MainTab/sheetBuyMerchant/GroupBox55/LwAutoBuyMerchant'

def _raw(value,bits):
    if value is not None and (type(value) is not int or not 0<=value<1<<bits):
        raise ValueError('Raw %dbit observation required'%bits)

def _decimal(text):
    if type(text) is not str or re.fullmatch(r'[+-]?[0-9]+',text.strip()) is None:return None
    value=int(text.strip())
    return value&((1<<64)-1) if -(1<<63)<=value<1<<63 else None

@dataclass(frozen=True)
class MerchantPricePlan:
    complete:bool
    qword:object=None
    predicate_result:object=None
    parser_bytes:object=None
    missing:str=''
    independently_verified:bool=False

def plan_merchant_price(ansi,*,parser_qword=None,local_decimal=False):
    _raw(parser_qword,64)
    if type(local_decimal) is not bool:raise ValueError('Explicit decimal replay flag required')
    if ansi is None:return MerchantPricePlan(False,missing='converted price ANSI bytes')
    if type(ansi) is not bytes:raise ValueError('Captured ANSI bytes required')
    valid=all(byte in b'.0123456789' for byte in ansi)
    if not valid:return MerchantPricePlan(True,0,False)
    text=ansi.replace(b'.',b'') if len(ansi)>3 else ansi
    if parser_qword is not None and local_decimal:raise ValueError('Captured and local parser results conflict')
    value=parser_qword
    if value is None and local_decimal:value=_decimal(text.decode('ascii'))
    if value is None:return MerchantPricePlan(False,predicate_result=True,parser_bytes=text,
        missing='price StrToInt64 normal result (decimal subset unsupported or absent)')
    return MerchantPricePlan(True,value,True,text)

@dataclass(frozen=True)
class BuyPreparedRecord:
    item_dword:int
    quantity_dword:int
    price_qword:int

    def __post_init__(self):
        for value,bits in ((self.item_dword,32),(self.quantity_dword,32),(self.price_qword,64)):
            _raw(value,bits)
            if value is None:raise ValueError('Complete prepared record required')

@dataclass(frozen=True)
class BuyPreparationState:
    records:tuple=()

    def __post_init__(self):
        if type(self.records) is not tuple or any(not isinstance(row,BuyPreparedRecord) for row in self.records):
            raise ValueError('Immutable prepared records required')

@dataclass(frozen=True)
class BuyPreparationRow:
    item_text:object=None
    quantity_text:object=None
    price_text:object=None
    price_ansi:object=None
    item_qword:object=None
    quantity_qword:object=None
    price_qword:object=None
    item_cleanup_returned:object=None
    quantity_cleanup_returned:object=None
    ansi_returned:object=None
    price_ansi_cleanup_returned:object=None
    price_unicode_cleanup_returned:object=None

    def __post_init__(self):
        for text in (self.item_text,self.quantity_text,self.price_text):
            if text is not None and type(text) is not str:raise ValueError('Observed Unicode text required')
        if self.price_ansi is not None and type(self.price_ansi) is not bytes:raise ValueError('Observed ANSI bytes required')
        for value in (self.item_qword,self.quantity_qword,self.price_qword):_raw(value,64)
        for value in (self.item_cleanup_returned,self.quantity_cleanup_returned,self.ansi_returned,
                      self.price_ansi_cleanup_returned,self.price_unicode_cleanup_returned):
            if value is not None and type(value) is not bool:raise ValueError('Normal-return observation required')

@dataclass(frozen=True)
class BuyPreparationObservation:
    clear_returned:object=None
    counts:tuple=()
    rows:Mapping=field(default_factory=dict)
    sizes:Mapping=field(default_factory=dict)
    capacities:Mapping=field(default_factory=dict)
    append_returns:Mapping=field(default_factory=dict)
    local_decimal:bool=False

    def __post_init__(self):
        if self.clear_returned is not None and type(self.clear_returned) is not bool:raise ValueError('Normal clear return required')
        if type(self.counts) is not tuple or type(self.local_decimal) is not bool:raise ValueError('Fresh counts and explicit parser policy required')
        for count in self.counts:_raw(count,32)
        for name in ('rows','sizes','capacities','append_returns'):
            mapping=getattr(self,name)
            if not isinstance(mapping,Mapping):raise ValueError('Indexed preparation observations required')
            copied=dict(mapping)
            for index,value in copied.items():
                _raw(index,32)
                if index is None:raise ValueError('Explicit row index required')
                if name=='rows' and not isinstance(value,BuyPreparationRow):raise ValueError('Typed preparation row required')
                if name in ('sizes','capacities'):_raw(value,32)
                if name=='append_returns' and value is not None and type(value) is not bool:raise ValueError('Normal append return required')
            object.__setattr__(self,name,MappingProxyType(copied))

@dataclass(frozen=True)
class BuyPreparationPlan:
    complete:bool
    state:BuyPreparationState
    prospective_state:BuyPreparationState
    calls:tuple
    missing:str=''
    partial_fields:tuple=()
    price_plan:object=None
    independently_verified:bool=False

def replay_buy_preparation(state,observation):
    return _replay_list_preparation(state,observation,BUY_LIST_PATH)

def _replay_list_preparation(state,observation,list_path):
    if not isinstance(state,BuyPreparationState) or not isinstance(observation,BuyPreparationObservation):
        raise ValueError('Typed BUY preparation state and observations required')
    o=observation;candidate=state;calls=[];partial=[];price=None
    class Missing(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def normal(value,label):
        if value is not True:raise Missing(label+' normal return')
    def integer(text,raw,label):
        need(text,label+' Unicode text')
        if raw is not None and o.local_decimal:raise ValueError('Local and captured parser results conflict')
        value=raw if raw is not None else (_decimal(text) if o.local_decimal else None)
        return need(value,label+' StrToInt64 result')
    try:
        calls.extend((('0041dc78:end',),('0041dc54:begin',),('0041dc9c:erase_range',)))
        normal(o.clear_returned,'begin/end/erase range');candidate=replace(candidate,records=())
        index=0
        while True:
            calls.append(('TListItems.GetCount',list_path))
            count=need(o.counts[index] if index<len(o.counts) else None,'fresh signed GetCount%d'%index)
            signed=count if count<0x80000000 else count-(1<<32)
            if index>=signed:break
            row=need(o.rows.get(index),'row%d'%index);partial=[]
            calls.append(('0045f7f4:caption',index));need(row.item_text,'item Unicode text')
            calls.append(('0045ef80:StrToInt64',0))
            item=integer(row.item_text,row.item_qword,'item')&0xffffffff;partial.append(('item',item))
            calls.append(('00505c48:item_cleanup',));normal(row.item_cleanup_returned,'item cleanup')
            calls.append(('0045f6e0:subitem',index,1));need(row.quantity_text,'quantity Unicode text')
            calls.append(('0045ef80:StrToInt64',0))
            quantity=integer(row.quantity_text,row.quantity_qword,'quantity')&0xffffffff
            partial.append(('quantity',quantity));calls.append(('00505c48:quantity_cleanup',))
            normal(row.quantity_cleanup_returned,'quantity cleanup')
            calls.append(('0045f6e0:subitem',index,2));need(row.price_text,'price Unicode text')
            calls.append(('004073a0:Unicode_to_ANSI',));normal(row.ansi_returned,'price ANSI conversion')
            calls.append(('00460fa4',))
            price=plan_merchant_price(row.price_ansi,parser_qword=row.price_qword,local_decimal=o.local_decimal)
            if not price.complete:raise Missing(price.missing)
            partial.append(('price',price.qword))
            calls.append(('004040f8:price_ANSI_cleanup',));normal(row.price_ansi_cleanup_returned,'price ANSI cleanup')
            calls.append(('00505c48:price_Unicode_cleanup',));normal(row.price_unicode_cleanup_returned,'price Unicode cleanup')
            calls.append(('0041dd4c:size',));size=need(o.sizes.get(index),'vector size%d'%index)
            calls.append(('0041dd74:capacity',));capacity=need(o.capacities.get(index),'vector capacity%d'%index)
            if size<capacity:calls.append(('0041dd9c:inplace_append',index))
            else:calls.extend((('0041dc78:end',),('0041ddfc:grow_append',index)))
            normal(o.append_returns.get(index),'append%d'%index)
            candidate=replace(candidate,records=candidate.records+(BuyPreparedRecord(item,quantity,price.qword),))
            index+=1
        return BuyPreparationPlan(True,candidate,candidate,tuple(calls),partial_fields=tuple(partial),price_plan=price)
    except Missing as error:
        return BuyPreparationPlan(False,state,candidate,tuple(calls),str(error),tuple(partial),price)
