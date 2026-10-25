"""SMerchant/BMerchant filename -> own local import; no native route start."""
from dataclasses import dataclass
from global_route_choices import ROUTE_GLOBALS,plan_global_route_choice,compile_panel_route_name
from supply_routes import SupplyRouteState
from supply_route_start import import_panel_route_choice
from name_codec import WindowsNameCodec
from route_start_state import RouteStartDecision
from source_unicode import utf16_key
import ntpath

@dataclass(frozen=True)
class MerchantBankRouteInputs:
    filename_ansi:object=None
    prefix_ansi:object=None
    codec:object=None
    # Own bookkeeping only; SMerchant does not read either cyclic counter.
    state:SupplyRouteState=SupplyRouteState(0,0)
    max_rows:int=10000
    error_message_returned:object=None
    path_cleanup_returned:object=None
    error_stop_returned:object=None
    error_notification_returned:object=None
    error_final_cleanup_returned:object=None
    prestart_span_returned:object=None
    start_execution:object=None
    kind:str='SMerchant'
    def __post_init__(self):
        if self.kind not in ('SMerchant','BMerchant'):raise ValueError('Merchant bank filename kind required')
        for value in (self.filename_ansi,self.prefix_ansi):
            if value is not None and type(value) is not bytes:raise ValueError('Explicit observed ANSI route bytes required')
        if self.codec is not None and not isinstance(self.codec,WindowsNameCodec):raise ValueError('Explicit own Windows codec required')
        if not isinstance(self.state,SupplyRouteState):raise ValueError('Typed own route counter state required')
        if type(self.max_rows) is not int or self.max_rows<1:raise ValueError('Explicit positive row budget required')
        for value in (self.error_message_returned,self.path_cleanup_returned,self.error_stop_returned,
                      self.error_notification_returned,self.error_final_cleanup_returned,self.prestart_span_returned):
            if value is not None and type(value) is not bool:raise ValueError('Separate route-error normal receipts required')
        if self.start_execution is not None and not isinstance(self.start_execution,RouteStartDecision):raise ValueError('Typed route-start execution required')

def merchant_bank_route_inputs_from_panel(combo_texts,directory,codec,*,state=SupplyRouteState(0,0),max_rows=10000,kind='SMerchant'):
    """Known own merchant combo Text and chosen directory; no file IO/receipts.

    Directory None remains an unknown prefix. Empty filename still belongs to
    the existing unselected branch, independently of filename conversion.
    """
    if kind not in ('SMerchant','BMerchant'):raise ValueError('Merchant bank filename kind required')
    filename=compile_panel_route_name(kind,combo_texts,codec)[ROUTE_GLOBALS[kind]]
    prefix=None
    if filename and directory is not None:
        if type(directory) is not str or not ntpath.isabs(directory):raise ValueError('Mutlak rota klasörü gerekli')
        text=directory.rstrip('\\/')+'\\';prefix,used=codec.encode(text)
        if used or utf16_key(codec.decode(prefix))!=utf16_key(text):
            raise ValueError('Rota klasörü seçilen kod sayfasında kayıpsız temsil edilemiyor')
    return MerchantBankRouteInputs(filename,prefix,codec,state=state,max_rows=max_rows,kind=kind)

@dataclass(frozen=True)
class MerchantBankRoutePlan:
    ready:bool
    status:str
    filename_global:int=0x5698bc
    choice:object=None
    imported_start:object=None
    missing:str=''
    native_helper_executed:bool=False
    live_compatibility_verified:bool=False
    complete:bool=False
    stop_required:bool=False
    error_kind:object=None
    steps:tuple=()
    start_execution:object=None
    kind:str='SMerchant'

def plan_merchant_bank_route(o):
    if not isinstance(o,MerchantBankRouteInputs):raise ValueError('Typed bank route inputs required')
    def plan_result(*args,**kwargs):return MerchantBankRoutePlan(*args,filename_global=ROUTE_GLOBALS[o.kind],kind=o.kind,**kwargs)
    choice=plan_global_route_choice(o.kind,{} if o.filename_ansi is None else
        {ROUTE_GLOBALS[o.kind]:o.filename_ansi},o.state)
    if not choice.complete:return plan_result(False,'needs_observation',choice=choice,missing=choice.missing)
    def error(kind,started=None):
        # These are own caller plans. Source/native helper side effects remain unexecuted.
        ranges={'unselected':('004ed23d','004ed2c9'),'file_missing':('004ed0cf','004ed214'),
                'nonpositive_count':('004ecf79','004ed0be')}
        steps=[]
        def result(complete,missing=''):
            return plan_result(False,'source_error_returned' if complete else 'source_error_needs_observation',
                choice=choice,imported_start=started,missing=missing,complete=complete,stop_required=True,
                error_kind=kind,steps=tuple(steps))
        steps.append(('normal_span','error message construction',*ranges[kind]))
        if o.error_message_returned is not True:return result(False,'route error-message construction span normal return')
        if kind!='unselected':
            steps.append(('normal_span','path cleanup','004ed217','004ed22c'))
            if o.path_cleanup_returned is not True:return result(False,'route path-cleanup span normal return')
        steps.append(('0040ae0c',0x561f34,0,'004ed2d3'))
        if o.error_stop_returned is not True:return result(False,'route error stop helper normal return')
        steps.append(('normal_span','error notification','004ed2db','004ed336'))
        if o.error_notification_returned is not True:return result(False,'route error notification span normal return')
        steps.append(('normal_span','final cleanup','004ed339','004ed38a'))
        if o.error_final_cleanup_returned is not True:return result(False,'route final-cleanup span normal return')
        return result(True)
    if not choice.filename:
        return error('unselected')
    if o.prefix_ansi is None:return plan_result(False,'needs_observation',choice=choice,missing='observed route object+57c ANSI prefix')
    if o.codec is None:return plan_result(False,'needs_observation',choice=choice,missing='explicit own codec for local route file')
    started=import_panel_route_choice(choice,o.prefix_ansi,o.codec,max_rows=o.max_rows)
    if not started.ready:
        if started.imported is not None:
            load_status=started.imported.load.status
            if load_status=='file_missing_preserve':return error('file_missing',started)
            if load_status=='nonpositive_count_preserve':return error('nonpositive_count',started)
        return plan_result(False,started.status,choice=choice,imported_start=started,
            missing=started.missing or 'native route error/stop effects remain unmodeled')
    if o.start_execution is not None:
        d=o.start_execution;missing=''
        if o.prestart_span_returned is not True:missing='route prestart query/copy/classifier span normal return'
        elif d.entry_state.fields.get(0x88)!=started.imported.load.count_dword:raise ValueError('Route-start entry count conflicts with imported count')
        elif not d.complete:missing='route start: '+d.missing
        elif d.state.fields[0x5f0]!=started.imported.load.count_dword:missing='route changed at fresh start-count read; concurrent bridge unmodeled'
        if missing:return plan_result(True,'start_needs_observation',choice=choice,imported_start=started,
            missing=missing,start_execution=d)
        return plan_result(True,'local_route_start_modeled',choice=choice,imported_start=started,
            complete=True,start_execution=d)
    return plan_result(True,'local_route_imported',choice=choice,imported_start=started,complete=True)
