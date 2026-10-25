"""004230d8 outer selector; fresh source observations, no native callback calls."""
from dataclasses import dataclass

@dataclass(frozen=True)
class MerchantCallbackObservation:
    entry_master_byte:object=None
    lock_byte:object=None
    route_pending_byte:object=None
    route_helper_returned:object=None
    post_master_byte:object=None
    post_enable_byte:object=None
    mode_results:tuple=()
    route_execution:object=None
    def __post_init__(self):
        for v in (self.entry_master_byte,self.lock_byte,self.route_pending_byte,self.post_master_byte,self.post_enable_byte):
            if v is not None and (type(v) is not int or not 0<=v<256):raise ValueError('Raw callback BYTE required')
        if self.route_helper_returned is not None and type(self.route_helper_returned) is not bool:raise ValueError('Explicit route helper normal return required')
        if type(self.mode_results) is not tuple or len(self.mode_results)>2:raise ValueError('Two independent callback mode DWORD reads maximum')
        for v in self.mode_results:
            if v is not None and (type(v) is not int or not 0<=v<1<<32):raise ValueError('Raw callback mode DWORD required')
        if self.route_execution is not None:
            from route_entry import RouteEntryDecision
            if not isinstance(self.route_execution,RouteEntryDecision):raise ValueError('Typed bound route entry decision required')

@dataclass(frozen=True)
class MerchantCallbackPlan:
    complete:bool
    status:str
    selected_kind:object=None
    steps:tuple=()
    missing:str=''
    independently_verified:bool=False
    route_execution:object=None

def plan_merchant_callback(o):
    if not isinstance(o,MerchantCallbackObservation):raise ValueError('Typed merchant callback observation required')
    steps=[];bound_route=None
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def byte(v,address,label):
        steps.append(('read',address,'BYTE'));return need(v,label)
    def mode(i):
        steps.append(('read','object+0','DWORD',i))
        if i>=len(o.mode_results):raise Missing('fresh callback mode DWORD read%d'%i)
        return need(o.mode_results[i],'callback mode DWORD value%d'%i)
    def result(complete,status,kind=None,missing=''):
        return MerchantCallbackPlan(complete,status,kind,tuple(steps),missing,route_execution=bound_route)
    try:
        if byte(o.entry_master_byte,0x561f60,'entry master BYTE561f60')==0:return result(True,'entry_disabled')
        if byte(o.lock_byte,0x561f6f,'lock BYTE561f6f'):return result(True,'locked')
        if byte(o.route_pending_byte,0x568d81,'route pending BYTE568d81'):
            steps.append(('004eb2c4',0x5687a8))
            bound_route=o.route_execution
            if bound_route is not None:
                steps.append(('bound_route_model',bound_route.status))
                if not bound_route.complete:raise Missing('route entry: '+bound_route.missing)
            if o.route_helper_returned is not True:raise Missing('route helper normal return')
        if byte(o.post_master_byte,0x561f60,'fresh post-route master BYTE561f60')==0:return result(True,'post_route_disabled')
        if byte(o.post_enable_byte,0x561f6c,'fresh post-route enable BYTE561f6c')==0:return result(True,'merchant_disabled')
        if mode(0)==1:
            steps.append(('00420efc',));return result(True,'selected','sell')
        if mode(1)==2:
            steps.append(('004220c8',));return result(True,'selected','buy')
        return result(True,'unhandled_mode')
    except Missing as e:return result(False,'needs_observation',missing=str(e))

@dataclass(frozen=True)
class MerchantCallbackDecision:
    status:str
    callback:MerchantCallbackPlan
    operation:object=None
    missing:str=''
    native_execution_verified:bool=False

def tick_merchant_callback(runner,observation,snapshot=None):
    """Optional snapshot factory is evaluated only when a source mode reaches it."""
    from operation_engine import MerchantRunner,MerchantSnapshot
    if not isinstance(runner,MerchantRunner):raise ValueError('Typed merchant runner required')
    p=plan_merchant_callback(observation)
    if not p.complete:return MerchantCallbackDecision('needs_adapter',p,missing=p.missing)
    if p.selected_kind is None:return MerchantCallbackDecision('callback_skipped',p)
    if p.selected_kind!=runner.settings.kind.value:raise ValueError('Source callback mode conflicts with bound runner kind')
    if snapshot is None:return MerchantCallbackDecision('needs_adapter',p,missing='phase-specific MerchantSnapshot')
    value=snapshot() if callable(snapshot) else snapshot
    if not isinstance(value,MerchantSnapshot):raise ValueError('Typed reached merchant snapshot required')
    return MerchantCallbackDecision('callback_modeled',p,runner.tick(value))
