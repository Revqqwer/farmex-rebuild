"""Normal-path own state/write plans for40ac18 +40ae0c; never executes calls.

UI/string, coordinate-helper and subordinate action spans are explicit opaque
normal-return boundaries. Projected stores are inert, not native write receipts.
"""
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from genie_getters import GenieGetterPlan,GetterBindings,retain_getter_snapshot

BASE_RESETS=((0x74,1,0),(0x75,1,0),(0x49,1,0),(0x70,4,0),(0x90,1,0),(0x94,4,0))
STOP_CONTEXT_RESETS=((0x38,1,0),(0x118,1,0),(0x108,4,0),(0x10c,4,0))
STOP_GLOBAL_RESETS=(
 (0x568d80,1,0),(0x568d81,1,0),(0x568d88,4,0),(0x568d8c,4,0),
 (0x568d90,1,0),(0x568d94,4,0xffffffff),(0x568d98,4,0),(0x568d9c,1,0),
 (0x568da0,4,0),(0x568da4,4,0),(0x568dbc,1,0),(0x568dc0,4,0xe),
 (0x568dc8,4,0),(0x568dcc,4,0),(0x568dd0,1,0),(0x568dd8,4,0),
 (0x568ddc,4,0),(0x568de0,4,0),(0x568df8,1,0),(0x568dfc,4,0xd),
 (0x568e00,1,0),(0x568e08,4,0),(0x568e0c,4,0),(0x568e30,1,0),
 (0x568e31,1,0),(0x568e34,4,0),(0x568e38,4,0xffffffff),(0x568e3c,1,0),
 (0x568e40,4,0),(0x568e44,4,0),(0x568e68,1,0),(0x568e6c,4,0),
 (0x568e70,1,0),(0x568e78,4,0),(0x568e7c,4,0),(0x568e80,1,0),
 (0x568e81,1,0),(0x568e82,1,0))

def _raw(v):
    if type(v) is not int or not 0<=v<=0xffffffff:raise ValueError('Raw bot-switch DWORD required')

@dataclass(frozen=True)
class BotSwitchObservation:
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    getter_executions:object=field(default_factory=dict)
    def __post_init__(self):
        values=dict(self.values);returns=dict(self.normal_returns)
        for v in values.values():_raw(v)
        if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate switch span normal-return receipts required')
        object.__setattr__(self,'values',MappingProxyType(values))
        object.__setattr__(self,'normal_returns',MappingProxyType(returns))
        getters=dict(self.getter_executions)
        if any(not isinstance(v,GenieGetterPlan) for v in getters.values()):raise ValueError('Typed getter child plans required')
        object.__setattr__(self,'getter_executions',MappingProxyType(getters))

@dataclass(frozen=True)
class SwitchStorePlan:
    address:int
    width:int
    value:int
    source:str
    def __post_init__(self):
        _raw(self.address);_raw(self.value)
        if type(self.width) is not int or self.width not in (1,4) or self.width==1 and self.value>255:
            raise ValueError('Exact BYTE/DWORD projected store required')

@dataclass(frozen=True)
class BotSwitchPlan:
    context:int
    argument_dword:int
    complete:bool
    status:str
    stores:tuple=()
    steps:tuple=()
    missing:str=''
    request:object=None
    native_execution_verified:bool=False
    whole_helper_effects_verified:bool=False
    getter_executions:tuple=()
    def __post_init__(self):
        _raw(self.context);_raw(self.argument_dword)
        if type(self.complete) is not bool or type(self.stores) is not tuple or any(not isinstance(s,SwitchStorePlan) for s in self.stores):
            raise ValueError('Typed bot-switch store plan required')
        if self.complete and (self.missing or self.request is not None):raise ValueError('Completed plan cannot retain an observation gap')
    @property
    def key(self):return 'bot_start' if self.argument_dword&255 else 'bot_stop'
    @property
    def helper(self):return '0040ae0c'
    @property
    def push_order(self):return (self.argument_dword,self.context)

class _Missing(Exception):
    def __init__(self,kind,label):self.request=(kind,label);super().__init__('bound getter: '+label if kind=='getter' else label+(' normal return' if kind=='normal' else ' value'))

def plan_bot_switch(context,argument_dword,o):
    _raw(context);_raw(argument_dword)
    if not isinstance(o,BotSwitchObservation):raise ValueError('Typed bot-switch observations required')
    stores=[];steps=[];enabled=bool(argument_dword&255);bindings=GetterBindings(o.getter_executions)
    def result(error=None):
        return BotSwitchPlan(context,argument_dword,error is None,'scoped_switch_span_returned' if error is None else 'needs_observation',
                             tuple(stores),tuple(steps),'' if error is None else str(error),None if error is None else error.request,getter_executions=tuple(bindings.used.items()))
    def normal(label):
        steps.append(('normal_return',label))
        if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
    def value(label,width=4):
        steps.append(('observed_value',label,width))
        if label not in o.values:raise _Missing('value',label)
        v=o.values[label]
        if width==1 and v>255:raise ValueError('Raw context BYTE observation required')
        return v
    def store(address,width,v,source):
        stores.append(SwitchStorePlan(address&0xffffffff,width,v,source));steps.append(('store_plan',address&0xffffffff,width,v,source))
    def ctx(offset,width,v,source):store(context+offset,width,v,source)
    def call(label,address,args=()):steps.append(('opaque_call',address,args));normal(label)
    try:
        normal('switch_frame_setup')
        # Base helper receives DL; upper24 bits of its pushed register are unspecified.
        steps.append(('base_helper','0040ac18',context,argument_dword&255,'upper24_unspecified'))
        normal('base_frame_setup')
        for offset,width,v in BASE_RESETS:ctx(offset,width,v,'base_reset')
        if enabled:
            if value('base_started_byte',1)==0:
                call('form_active','form_vtable_78')
                if value('form_active_eax')&255==0:call('form_activate','form_vtable_94',('DL=1',))
                call('start_caption_span','0040ac94..0040acd4')
                ctx(0x168,1,0,'base_start');ctx(0x2c,1,1,'base_start')
                call('start_notification_span','0040ace5..0040ad48')
        else:
            call('stop_caption_span','0040ad52..0040ad91')
            ctx(0x2c,1,0,'base_stop')
            call('stop_notification_span','0040ad98..0040adfb')
        normal('activation_helper')
        if enabled:
            # Source reloads context24 for each independent reached comparison.
            if value('mode_for_zero')==0:
                call('use_current_xy','form_checkbox_5ac_vtable130')
                if value('use_current_xy_eax')&255:
                    call('current_y','004625d8');y=value('current_y_eax')
                    call('current_x','004625ac');x=value('current_x_eax')
                    call('coordinate_helper','0040a2dc',(y,x,context))
                    ctx(0xcc,4,x,'coordinate_helper_normal');ctx(0xd0,4,y,'coordinate_helper_normal')
                    # Includes fresh repeated coordinate getters: no reuse asserted.
                    call('current_coordinates_label_span','0040ae77..0040afe6')
                else:
                    call('entered_y_text','0040afe6..0040b019');y=value('entered_y_eax')
                    call('entered_x_text','0040b019..0040b044');x=value('entered_x_eax')
                    call('coordinate_helper','0040a2dc',(y,x,context))
                    ctx(0xcc,4,x,'coordinate_helper_normal');ctx(0xd0,4,y,'coordinate_helper_normal')
                    call('entered_coordinate_cleanup','0040b050..0040b072')
                ctx(0x38,1,1,'mode_zero_start')
            elif value('mode_for_two')==2:
                call('mode_two_start','0047baa4',(1,0x569a98))
                if value('mode_two_start_eax')&255:ctx(0x38,1,1,'mode_two_start')
            elif value('mode_for_four')==4:
                for address,width,v in ((0x5697e4,4,0),(0x569838,1,0),(0x569870,1,0)):store(address,width,v,'mode_four_reset')
                ctx(0x38,1,1,'mode_four_start')
            elif value('mode_for_five')==5:ctx(0x38,1,1,'mode_five_start')
        else:
            if value('stop_mode_for_two')==2:call('mode_two_stop','0047baa4',(0,0x569a98))
            gap=bindings.enter('stop_genie_state','004631c8')
            if gap is not None:raise _Missing('getter','stop_genie_state')
            call('stop_genie_state','004631c8');eax=value('stop_genie_state_eax');bindings.check_eax('stop_genie_state',eax)
            if eax&255==1:call('stop_genie','004ca4c4',(0,0x561ef8))
            for offset,width,v in STOP_CONTEXT_RESETS:ctx(offset,width,v,'stop_context_reset')
            for address,width,v in STOP_GLOBAL_RESETS:store(address,width,v,'stop_global_reset')
            call('stop_movement','00464714')
        return result()
    except _Missing as error:return result(error)

class BotSwitchFrame:
    """One scoped invocation; projected stores are recomputed, never applied."""
    def __init__(self,context,argument_dword):
        _raw(context);_raw(argument_dword)
        self.context=context;self.argument_dword=argument_dword;self.observation=BotSwitchObservation();self.final=None
    def advance(self,o):
        if not isinstance(o,BotSwitchObservation):raise ValueError('Typed bot-switch observations required')
        if self.final is not None:return self.final
        for _ in range(40):
            p=plan_bot_switch(self.context,self.argument_dword,self.observation)
            if p.complete:self.final=p;return p
            kind,label=p.request
            if label in ('stop_genie_state','stop_genie_state_eax') and 'stop_genie_state' in o.getter_executions:
                child=retain_getter_snapshot(self.observation.getter_executions.get('stop_genie_state'),o.getter_executions['stop_genie_state'])
                candidate=replace(self.observation,getter_executions={**self.observation.getter_executions,'stop_genie_state':child})
                p=plan_bot_switch(self.context,self.argument_dword,candidate);self.observation=candidate
                if p.complete:self.final=p;return p
                kind,label=p.request
            if kind=='getter':return p
            if kind=='normal':
                if o.normal_returns.get(label) is not True:return p
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
            else:
                if label not in o.values:return p
                self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
        raise ValueError('Bot-switch frame exceeded source span budget')
