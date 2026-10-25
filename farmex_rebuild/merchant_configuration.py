"""Merchant scalar projections from common 41fea4; local numeric policies.

No VCL execution, events, native conversion, route loading, or game actions.
"""
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from operation_engine import MerchantSettings,MerchantKind
from merchant_preparation import BUY_LIST_PATH
from merchant_preparation import plan_merchant_price
from merchant_sell_preparation import SELL_LIST_PATH

BASE='frmMain/MainTab/sheetBuyMerchant/'
SELL_START='frmMain/MainTab/sheetSellMerchant/GroupBox24/chStartSellMBot'
BUY_START=BASE+'GroupBox57/chStartBuyMBot'
REOPEN=BASE+'GroupBox57/chBuyMBotReMerchant'
MINUTES=BASE+'GroupBox57/txtBuyMBotReMerchantTime'
EXTRA=BASE+'GroupBox57/txtBuyMBotExtraWait'
STOP=BASE+'GroupBox59/rdBuyMAnyItemStop'
DC=BASE+'GroupBox59/rdBuyMAnyItemDC'
BANK=BASE+'GroupBox59/rdBuyMAnyItemUseBank'
THRESHOLD=BASE+'GroupBox59/txtBuyMInvFullLimit'
ALARM=BASE+'GroupBox59/chBuyMAnyItemAlarm'
MANUAL=BASE+'GroupBox59/chBuyMBotManuelRoute'
ROUTE=BASE+'GroupBox59/cmbBuyMBotManuelRoute'
BUY_MERCHANT_PANEL_INPUTS=(SELL_START,BUY_START,REOPEN,MINUTES,EXTRA,STOP,DC,BANK,THRESHOLD,ALARM,MANUAL,ROUTE,BUY_LIST_PATH)

@dataclass(frozen=True)
class BuyMerchantConfiguration:
    fields:Mapping
    route_text:object
    missing:tuple=()
    native_parser_verified:bool=False
    independently_verified:bool=False

def compile_buy_merchant_panel(values,*,initial_policy_dword=None,route_text=None,numeric_results=None):
    if not isinstance(values,Mapping):raise ValueError('Panel snapshot mapping required')
    if route_text is not None and type(route_text) is not str:raise ValueError('Explicit combo Text required')
    if initial_policy_dword is not None and (type(initial_policy_dword) is not int or not 0<=initial_policy_dword<=0xffffffff):
        raise ValueError('Raw previous policy DWORD required')
    numeric_results={} if numeric_results is None else numeric_results
    if not isinstance(numeric_results,Mapping) or set(numeric_results)-{MINUTES,EXTRA,THRESHOLD}:
        raise ValueError('Only reached numeric helper observations allowed')
    def checked(path):
        value=values.get(path)
        if type(value) is not bool:raise ValueError('Boolean panel value required: '+path)
        return value
    def number(path):
        if path in numeric_results:
            value=numeric_results[path]
            if type(value) is not int or not 0<=value<1<<64:raise ValueError('Observed helper EDX:EAX QWORD required')
        else:
            text=values.get(path)
            if type(text) is not str or not re.fullmatch(r'[+-]?[0-9]+',text.strip()):
                raise ValueError('Local decimal subset required, or explicit helper QWORD: '+path)
            value=int(text.strip())
            if not -(1<<63)<=value<1<<63:raise ValueError('Signed64 decimal subset exceeded')
        return value&0xffffffff
    # Source reads BUY start only if SELL start was false.
    mode=1 if checked(SELL_START) else (2 if checked(BUY_START) else 0)
    fields={0:mode,0x110:int(checked(REOPEN)),0x114:number(MINUTES),0x118:number(EXTRA)}
    policy=initial_policy_dword
    # Separate IFs, not a mutually exclusive validation or first-match chain.
    for path,code in ((STOP,0),(DC,1),(BANK,2)):
        if checked(path):policy=code
    missing=[]
    if policy is None:missing.append('previous policy DWORD+11c (no radio checked)')
    else:fields[0x11c]=policy
    fields.update({0x120:number(THRESHOLD),0x124:int(checked(ALARM)),0x125:int(checked(MANUAL))})
    if route_text is None:missing.append(ROUTE+': GetText')
    return BuyMerchantConfiguration(MappingProxyType(fields),route_text,tuple(missing))

def buy_merchant_settings_from_panel(configuration,*,rows=()):
    if not isinstance(configuration,BuyMerchantConfiguration):raise ValueError('Compiled BUY configuration required')
    f=configuration.fields
    if 0x11c not in f or f[0x11c] not in (0,1,2):raise ValueError('BUY failure policy not resolved')
    # MerchantSettings explicitly restricts its still-monotonic setup timers.
    # Preserve raw fields in configuration; never clamp them to pass validation.
    return MerchantSettings(kind=MerchantKind.BUY,reopen=bool(f[0x110]),reopen_minutes=f[0x114],
        extra_wait_seconds=f[0x118],buy_free_threshold=f[0x120],
        failure_policy=('stop','disconnect','bank_route')[f[0x11c]],rows=rows)

SELL_BASE='frmMain/MainTab/sheetSellMerchant/'
SELL_ORDER=SELL_BASE+'GroupBox24/chSellMBotInvSort'
SELL_REOPEN=SELL_BASE+'GroupBox24/chSellMBotReMerchant'
SELL_MINUTES=SELL_BASE+'GroupBox24/txtSellMBotReMerchantTime'
SELL_EXTRA=SELL_BASE+'GroupBox24/txtSellMBotExtraWait'
SELL_STOP=SELL_BASE+'GroupBox27/rdSellMAnyItemStop'
SELL_DC=SELL_BASE+'GroupBox27/rdSellMAnyItemDC'
SELL_BANK=SELL_BASE+'GroupBox27/rdSellMAnyItemUseBank'
SELL_ALARM=SELL_BASE+'GroupBox27/chSellMAnyItemAlarm'
SELL_MANUAL=SELL_BASE+'GroupBox27/chSellMBotManuelRoute'
SELL_ROUTE=SELL_BASE+'GroupBox27/cmbSellMBotManuelRoute'
SELL_COIN_ALARM=SELL_BASE+'GroupBox27/chSellMBotChangeCoinAlarm'
SELL_COIN=SELL_BASE+'GroupBox27/txtSellMLastCoin'
SELL_MERCHANT_PANEL_INPUTS=(SELL_START,BUY_START,SELL_ORDER,SELL_REOPEN,SELL_MINUTES,SELL_EXTRA,
    SELL_STOP,SELL_DC,SELL_BANK,SELL_ALARM,SELL_MANUAL,SELL_ROUTE,SELL_COIN_ALARM,SELL_COIN,SELL_LIST_PATH)

def sell_coin_alarm_from_panel(configuration,coins_dword=None,alarm_span_returned=None,*,coin_inputs=None):
    from merchant_sell_coin_alarm import SellCoinAlarmObservation
    if not isinstance(configuration,SellMerchantConfiguration):raise ValueError('Compiled SELL configuration required')
    return SellCoinAlarmObservation(configuration.fields[0xe0],coins_dword,
                                    configuration.fields.get(0xe8),alarm_span_returned,coin_inputs)

@dataclass(frozen=True)
class SellMerchantConfiguration:
    fields:Mapping
    route_text:object
    missing:tuple=()
    coin_plan:object=None
    native_parser_verified:bool=False
    independently_verified:bool=False

def compile_sell_merchant_panel(values,*,initial_policy_dword=None,route_text=None,numeric_results=None,coin_qword=None):
    if not isinstance(values,Mapping):raise ValueError('Panel snapshot mapping required')
    if route_text is not None and type(route_text) is not str:raise ValueError('Explicit combo Text required')
    if initial_policy_dword is not None and (type(initial_policy_dword) is not int or not 0<=initial_policy_dword<=0xffffffff):
        raise ValueError('Raw previous SELL policy DWORD required')
    numeric_results={} if numeric_results is None else numeric_results
    if not isinstance(numeric_results,Mapping) or set(numeric_results)-{SELL_MINUTES,SELL_EXTRA}:
        raise ValueError('Only SELL numeric helper observations allowed')
    def checked(path):
        value=values.get(path)
        if type(value) is not bool:raise ValueError('Boolean panel value required: '+path)
        return value
    def number(path):
        if path in numeric_results:
            value=numeric_results[path]
            if type(value) is not int or not 0<=value<1<<64:raise ValueError('Observed helper QWORD required')
        else:
            text=values.get(path)
            if type(text) is not str or not re.fullmatch(r'[+-]?[0-9]+',text.strip()):
                raise ValueError('Local signed64 decimal subset required: '+path)
            value=int(text.strip())
            if not -(1<<63)<=value<1<<63:raise ValueError('Signed64 decimal subset exceeded')
        return value&0xffffffff
    fields={0:1 if checked(SELL_START) else (2 if checked(BUY_START) else 0),
            0xc8:int(checked(SELL_ORDER)),0xc9:int(checked(SELL_REOPEN)),
            0xcc:number(SELL_MINUTES),0xd0:number(SELL_EXTRA)}
    policy=initial_policy_dword;missing=[]
    for path,code in ((SELL_STOP,0),(SELL_DC,1),(SELL_BANK,2)):
        if checked(path):policy=code
    if policy is None:missing.append('previous policy DWORD+d4 (no radio checked)')
    else:fields[0xd4]=policy
    fields.update({0xd8:int(checked(SELL_ALARM)),0xd9:int(checked(SELL_MANUAL)),0xe0:int(checked(SELL_COIN_ALARM))})
    if route_text is None:missing.append(SELL_ROUTE+': GetText')
    coin_plan=None
    if coin_qword is not None:
        if type(coin_qword) is not int or not 0<=coin_qword<1<<64:raise ValueError('Observed coin helper QWORD required')
        fields[0xe8]=coin_qword
    else:
        text=values.get(SELL_COIN)
        try:ansi=text.encode('ascii') if type(text) is str else None
        except UnicodeEncodeError:ansi=None
        coin_plan=plan_merchant_price(ansi,local_decimal=True)
        if coin_plan.complete:fields[0xe8]=coin_plan.qword
        else:missing.append(SELL_COIN+': '+coin_plan.missing)
    return SellMerchantConfiguration(MappingProxyType(fields),route_text,tuple(missing),coin_plan)

def sell_merchant_settings_from_panel(configuration,*,rows=()):
    if not isinstance(configuration,SellMerchantConfiguration):raise ValueError('Compiled SELL configuration required')
    f=configuration.fields
    if f.get(0xd4) not in (0,1,2):raise ValueError('SELL failure policy not resolved')
    return MerchantSettings(kind=MerchantKind.SELL,reopen=bool(f[0xc9]),reopen_minutes=f[0xcc],extra_wait_seconds=f[0xd0],
        failure_policy=('stop','disconnect','bank_route')[f[0xd4]],sell_inventory_order=bool(f[0xc8]),rows=rows)
