"""Reached004565c9..00456804 command dispatch, no input/native execution.

Configuration and parsed message are explicit stable own snapshots. Prior chat
branches and command helper effects are not covered by this scoped plan.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from name_codec import WindowsNameCodec
from chat_party_invite import ChatPartyMessage
from command_helpers import CommandQueuePlan,TownPlan
from motion_genie_helpers import MotionGeniePlan
from bot_switch import BotSwitchPlan
from genie_getters import GenieGetterPlan,GetterBindings,retain_getter_snapshot

GETTER_FIELDS={'genie_start_state':'genie_start_state_eax','genie_remaining':'genie_remaining_eax','genie_stop_state':'genie_stop_state_eax'}

ROOT='frmMain/MainTab/SheetDiger/GroupBox36/'
# Source runtime order, not the producer's storage order.
SPECS=(('disconnect','chkmtdc','txtkmtdc',0x9,0x18,0x910),
       ('return_center','chkmtmerkezdon','txtkmtmerkezdon',0xa,0x40,0x918),
       ('bot_start','chkmtbotbaslat','txtkmtbotbaslat',0xb,0x68,0x920),
       ('bot_stop','chkmtbotdurdur','txtkmtbotdurdur',0xc,0x90,0x928),
       ('genie_start','chkmtgeniebaslat','txtkmtgeniebaslat',0xd,0xb8,0x930),
       ('genie_stop','chkmtgeniedurdur','txtkmtgeniedurdur',0xe,0xe0,0x938),
       ('stand','chkmtkalk','txtkmtkalk',0xf,0x108,0x940),
       ('town','chkmttown','txtkmttown',0x10,0x130,0x948))
CHAT_COMMAND_INPUTS=tuple(ROOT+name for spec in SPECS for name in spec[1:3])

def _raw(v,bits=32,optional=False):
    if optional and v is None:return
    if type(v) is not int or not 0<=v<1<<bits:raise ValueError('Raw chat command value required')

@dataclass(frozen=True)
class CommandSetting:
    key:str
    enabled_byte:int
    command:bytes
    def __post_init__(self):
        _raw(self.enabled_byte,8)
        if type(self.command) is not bytes:raise ValueError('Immutable source command string required')

@dataclass(frozen=True)
class ChatCommandsConfiguration:
    settings:tuple
    codepage:object=None
    def __post_init__(self):
        if type(self.settings) is not tuple or any(not isinstance(v,CommandSetting) for v in self.settings) or tuple(v.key for v in self.settings)!=tuple(s[0] for s in SPECS):
            raise ValueError('All eight source commands in runtime order required')

def compile_chat_commands(values,codec):
    if not isinstance(codec,WindowsNameCodec):raise ValueError('Explicit local Windows codepage required')
    settings=[]
    for key,check,text,*_ in SPECS:
        enabled=values.get(ROOT+check);command=values.get(ROOT+text)
        if type(enabled) is not bool or type(command) is not str:raise ValueError('Known command panel flag/text required')
        data,used=codec.encode(command)
        if used is True or codec.decode(data)!=command:raise ValueError('Lossless command encoding required')
        settings.append(CommandSetting(key,int(enabled),data.split(b'\0',1)[0]))
    return ChatCommandsConfiguration(tuple(settings),codec.code_page)

FIELD_LABELS={
    'center_y_dword':'center Y DWORD 00562004','center_y_f32_bits':'center Y post-FSTP binary32 bits',
    'center_x_dword':'center X DWORD 00562000','center_x_f32_bits':'center X post-FSTP binary32 bits',
    'genie_blocked_byte':'Genie-start blocker BYTE 00561f6f',
    'genie_start_state_eax':'Genie-start state EAX','genie_remaining_eax':'Genie-start remaining EAX',
    'genie_stop_state_eax':'fresh Genie-stop state EAX'}

@dataclass(frozen=True)
class ChatCommandsObservation:
    helper_returns:object=field(default_factory=dict)
    center_y_dword:object=None
    center_y_f32_bits:object=None
    center_x_dword:object=None
    center_x_f32_bits:object=None
    genie_blocked_byte:object=None
    genie_start_state_eax:object=None
    genie_remaining_eax:object=None
    genie_stop_state_eax:object=None
    action_executions:object=field(default_factory=dict)
    getter_executions:object=field(default_factory=dict)
    def __post_init__(self):
        for name in FIELD_LABELS:_raw(getattr(self,name),8 if name=='genie_blocked_byte' else 32,True)
        returns=dict(self.helper_returns)
        if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate command helper returns required')
        object.__setattr__(self,'helper_returns',MappingProxyType(returns))
        executions=dict(self.action_executions)
        if any(not isinstance(v,(CommandQueuePlan,TownPlan,MotionGeniePlan,BotSwitchPlan)) for v in executions.values()):
            raise ValueError('Typed bound command helper plans required')
        object.__setattr__(self,'action_executions',MappingProxyType(executions))
        getters=dict(self.getter_executions)
        if any(not isinstance(v,GenieGetterPlan) for v in getters.values()):raise ValueError('Typed getter child plans required')
        object.__setattr__(self,'getter_executions',MappingProxyType(getters))

@dataclass(frozen=True)
class ChatCommandAction:
    key:str
    helper:str
    push_order:tuple
    native_execution_verified:bool=False
    helper_execution:object=None

@dataclass(frozen=True)
class ChatCommandsPlan:
    complete:bool
    status:str
    actions:tuple=()
    steps:tuple=()
    missing:str=''
    native_execution_verified:bool=False
    getter_executions:tuple=()

def plan_chat_commands(c,message,o):
    if not isinstance(c,ChatCommandsConfiguration) or not isinstance(message,ChatPartyMessage) or not isinstance(o,ChatCommandsObservation):
        raise ValueError('Typed reached command span inputs required')
    actions=[];steps=[];bindings=GetterBindings(o.getter_executions)
    class Missing(Exception):pass
    def result(ok,missing=''):return ChatCommandsPlan(ok,'command_span_returned' if ok else 'needs_observation',tuple(actions),tuple(steps),missing,getter_executions=tuple(bindings.used.items()))
    def normal(label):
        steps.append(('normal_return',label))
        if o.helper_returns.get(label) is not True:raise Missing(label+' normal return')
    def value(field):
        v=getattr(o,field)
        if v is None:raise Missing(FIELD_LABELS[field])
        return v
    def action(key,helper,pushes):
        bound=o.action_executions.get(key)
        actions.append(ChatCommandAction(key,helper,pushes,helper_execution=bound))
        if bound is not None:
            bound_key=bound.key if isinstance(bound,(CommandQueuePlan,MotionGeniePlan,BotSwitchPlan)) else 'town'
            if key!=bound_key:raise ValueError('Bound command helper kind differs from reached action')
            if isinstance(bound,(MotionGeniePlan,BotSwitchPlan)) and (bound.helper!=helper or bound.push_order!=pushes):
                raise ValueError('Bound helper operands differ from reached command arguments')
            if not bound.complete:raise Missing('bound action:'+key+': '+bound.missing)
        normal('action:'+key)
    def helper(label,address,field):
        gap=bindings.enter(label,address)
        if gap is not None:raise Missing('bound getter:'+label)
        steps.append(('helper',address));normal(label)
        eax=value(field);bindings.check_eax(label,eax);return eax
    try:
        for setting in c.settings:
            key=setting.key
            # Source compares even when the corresponding checkbox is disabled.
            steps.append(('00457388',key,message.message,setting.command));normal('compare:'+key)
            if message.message!=setting.command or not setting.enabled_byte:continue
            if key=='disconnect':action(key,'004c7e0c',(0x561ef8,))
            elif key=='return_center':
                y=value('center_y_dword');steps.append(('FILD_signed32',0x562004,y,y-(1<<32) if y&0x80000000 else y))
                y_bits=value('center_y_f32_bits');steps.append(('FSTP_f32',y_bits))
                x=value('center_x_dword');steps.append(('FILD_signed32',0x562000,x,x-(1<<32) if x&0x80000000 else x))
                x_bits=value('center_x_f32_bits');steps.append(('FSTP_f32',x_bits))
                action(key,'004646b4',(y_bits,x_bits))
            elif key in ('bot_start','bot_stop'):action(key,'0040ae0c',(1 if key=='bot_start' else 0,0x561f34))
            elif key=='genie_start':
                if value('genie_blocked_byte')!=0:continue
                if helper('genie_start_state','004631c8','genie_start_state_eax')&255:continue
                if helper('genie_remaining','004631e8','genie_remaining_eax')&255==0:continue
                action(key,'00466cc4',(1,))
            elif key=='genie_stop':
                if helper('genie_stop_state','004631c8','genie_stop_state_eax')&255!=1:continue
                action(key,'00466cc4',(0,))
            elif key=='stand':action(key,'004c8d48',(0x561ef8,))
            else:action(key,'00465678',())
        return result(True)
    except Missing as error:return result(False,str(error))

class ChatCommandsFrame:
    """One reached invocation with consumed helper/read prefix retained."""
    def __init__(self,configuration,message):
        if not isinstance(configuration,ChatCommandsConfiguration) or not isinstance(message,ChatPartyMessage):
            raise ValueError('Stable own command/message snapshot required')
        self.configuration=configuration;self.message=message;self.observation=ChatCommandsObservation();self.final=None

    def advance(self,o):
        if not isinstance(o,ChatCommandsObservation):raise ValueError('Typed command observations required')
        if self.final is not None:return self.final
        for _ in range(48):
            p=plan_chat_commands(self.configuration,self.message,self.observation)
            if p.complete:self.final=p;return p
            getter_key=None
            if p.missing.startswith('bound getter:'):getter_key=p.missing[len('bound getter:'):]
            elif p.missing.endswith(' normal return'):
                candidate_key=p.missing[:-14]
                if candidate_key in GETTER_FIELDS:getter_key=candidate_key
            else:getter_key=next((key for key,field in GETTER_FIELDS.items() if FIELD_LABELS[field]==p.missing),None)
            if getter_key is not None and getter_key in o.getter_executions:
                child=retain_getter_snapshot(self.observation.getter_executions.get(getter_key),o.getter_executions[getter_key])
                candidate=replace(self.observation,getter_executions={**self.observation.getter_executions,getter_key:child})
                p=plan_chat_commands(self.configuration,self.message,candidate);self.observation=candidate
                if p.complete:self.final=p;return p
            if p.missing.startswith('bound getter:'):return p
            action_key=None
            if p.missing.startswith('action:') and p.missing.endswith(' normal return'):
                action_key=p.missing[len('action:'):-len(' normal return')]
            elif p.missing.startswith('bound action:'):
                action_key=p.missing[len('bound action:'):].split(':',1)[0]
            if action_key is not None and action_key in o.action_executions:
                self.observation=replace(self.observation,action_executions={**self.observation.action_executions,action_key:o.action_executions[action_key]})
                p=plan_chat_commands(self.configuration,self.message,self.observation)
            if p.missing.startswith('bound action:'):return p
            if p.missing.endswith(' normal return'):
                key=p.missing[:-14]
                if o.helper_returns.get(key) is not True:return p
                self.observation=replace(self.observation,helper_returns={**self.observation.helper_returns,key:True})
                continue
            name=next((name for name,label in FIELD_LABELS.items() if label==p.missing),None)
            if name is None or getattr(o,name) is None:return p
            self.observation=replace(self.observation,**{name:getattr(o,name)})
        raise ValueError('Chat command frame exceeded source prefix budget')
