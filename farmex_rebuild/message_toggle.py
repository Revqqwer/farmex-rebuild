"""0045cbac caption-based start/stop and ButtonAutoFlood caller; inert plans."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType

START_CAPTION=b'OTOMATIK FLOOD BASLAT'
STOP_CAPTION=b'OTOMATIK FLOOD DURDUR'
BUTTON_PATH='frmMain/MainTab/sheetFlood/grpFlood/btnAutoFlood'

@dataclass(frozen=True)
class MessageToggleObservation:
    entry_reached:bool=False
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit toggle post-prologue entry required')
        values=dict(self.values);normals=dict(self.normal_returns)
        if any(type(v) is not int or not 0<=v<=0xffffffff for v in values.values()):raise ValueError('Raw comparison EAX required')
        if any(type(v) is not bool for v in normals.values()):raise ValueError('Separate UI/string normal receipts required')
        object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(normals))

@dataclass(frozen=True)
class MessageTogglePlan:
    complete:bool
    status:str
    stores:tuple=()
    calls:tuple=()
    ui_updates:tuple=()
    needed:object=None
    enabled_byte:object=None
    next_address:object=None
    whole_function_verified:bool=False
    caption_equality_verified:bool=False
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class _Wait(Exception):
    def __init__(self,kind,key):self.needed=(kind,key);super().__init__(key)

def _plan(o,context):
    stores=[];calls=[];updates=[];enabled=None
    def result(status,wait=None):
        return MessageTogglePlan(wait is None,status,tuple(stores),tuple(calls),tuple(updates),
            None if wait is None else wait.needed,enabled,0x45ccd8 if wait is None else None)
    def normal(key,target,args=()):
        calls.append((target,args,key))
        if o.normal_returns.get(key) is not True:raise _Wait('normal',key)
    try:
        if not o.entry_reached:raise _Wait('entry','0045cbbd')
        stores.extend((((context+0x28)&0xffffffff,4,0),((context+0x2c)&0xffffffff,4,0),
                       ((context+0x24)&0xffffffff,4,0)))
        normal('comparison_literal_create','00505bb8',(START_CAPTION,))
        normal('current_text_init','00404a78')
        normal('current_text_get','VCL_Text_getter',('form_field',0xbc8))
        normal('caption_compare','00505d3c',('captured_button_text','captured_start_literal'))
        if 'compare_eax' not in o.values:raise _Wait('value','compare_eax')
        comparison=o.values['compare_eax']
        normal('comparison_literal_cleanup','00505c64')
        normal('current_text_cleanup','00505c64')
        enabled=int((comparison&255)!=0)
        caption=STOP_CAPTION if enabled else START_CAPTION
        normal('new_caption_create','00505bb8',(caption,))
        normal('new_caption_set','VCL_Text_setter',('form_field',0xbc8,'captured_new_caption'))
        updates.append((BUTTON_PATH,caption))
        normal('new_caption_cleanup','00505c64')
        stores.append(((context+0x20)&0xffffffff,1,enabled))
        return result('start_branch_returned' if enabled else 'stop_branch_returned')
    except _Wait as wait:return result('needs_observation',wait)

class MessageToggleFrame:
    def __init__(self,*,context=0x569910):
        if type(context) is not int or not 0<=context<=0xffffffff:raise ValueError('Raw source context required')
        self.context=context;self.observation=MessageToggleObservation();self.final=None
    def advance(self,incoming):
        if not isinstance(incoming,MessageToggleObservation):raise ValueError('Typed message toggle observations required')
        if self.final is not None:return self.final
        for _ in range(16):
            plan=_plan(self.observation,self.context)
            if plan.complete:self.final=plan;return plan
            kind,key=plan.needed
            if kind=='entry':
                if not incoming.entry_reached:return plan
                self.observation=replace(self.observation,entry_reached=True)
            elif kind=='normal':
                if incoming.normal_returns.get(key) is not True:return plan
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,key:True})
            else:
                if key not in incoming.values:return plan
                self.observation=replace(self.observation,values={**self.observation.values,key:incoming.values[key]})
        raise AssertionError('Toggle reached capture budget exceeded')

@dataclass(frozen=True)
class MessageToggleClickPlan:
    complete:bool
    toggle:object=None
    needed:object=None
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class MessageToggleClickFrame:
    """One bounded own callback invocation, with no source profile-load gate."""
    def __init__(self):
        self.entered=False;self.toggle=MessageToggleFrame();self.final=None
    def advance(self,child=None,*,entry_reached=False,handler_returned=None):
        if type(entry_reached) is not bool:raise ValueError('Explicit callback entry required')
        if handler_returned is not None and type(handler_returned) is not bool:raise ValueError('Separate callback normal receipt required')
        if child is not None and not isinstance(child,MessageToggleObservation):raise ValueError('Typed toggle child required')
        if self.final is not None:return self.final
        if not self.entered:
            if not entry_reached:return MessageToggleClickPlan(False,needed='callback_entry')
            self.entered=True
        plan=self.toggle.advance(child or MessageToggleObservation())
        if not plan.complete:return MessageToggleClickPlan(False,plan,('toggle',plan.needed))
        if handler_returned is not True:return MessageToggleClickPlan(False,plan,'handler_returned')
        self.final=MessageToggleClickPlan(True,plan);return self.final
