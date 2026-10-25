"""Bounded normal-path455ec0..4565c9 prelude, inert logging intent only.

Native buffers/strings and log sink effects are separate opaque boundaries.
Reaching this source handler is assumed; caller routing is not certified.
"""
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from chat_party_invite import ChatPartyMessage,parse_chat_prefix
from chat_commands import ChatCommandsConfiguration,ChatCommandsObservation,ChatCommandsFrame

CHAT_LOG_INPUT='frmMain/MainTab/sheetInfoLog/chChatInfoLog'
LOG_LABELS=MappingProxyType({1:b'All',2:b'PM',3:b'Party',4:b'Shout',5:b'Clan',
                             6:b'',14:b'Merchant',34:b'Noah Knights'})

def compile_chat_log(values):
    value=values.get(CHAT_LOG_INPUT)
    if type(value) is not bool:raise ValueError('Known Chat Log checkbox required')
    return int(value)

@dataclass(frozen=True)
class ChatPreludeObservation:
    normal_returns:object=field(default_factory=dict)
    assembled_log_bytes:object=None
    def __post_init__(self):
        returns=dict(self.normal_returns)
        if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate prelude normal returns required')
        object.__setattr__(self,'normal_returns',MappingProxyType(returns))
        if self.assembled_log_bytes is not None and type(self.assembled_log_bytes) is not bytes:
            raise ValueError('Immutable assembled log snapshot required')

@dataclass(frozen=True)
class ChatLogIntent:
    channel:int
    projected_line:bytes
    category:bytes=b''
    context:int=0x561f34
    observed_line:object=None
    sink_normal_return_observed:bool=False
    sink_effect_verified:bool=False

@dataclass(frozen=True)
class ChatPreludePlan:
    complete:bool
    status:str
    log_intent:object=None
    steps:tuple=()
    missing:str=''
    request:object=None
    command_entry_reached:bool=False
    native_execution_verified:bool=False

class _Missing(Exception):
    def __init__(self,kind,label):self.request=(kind,label);super().__init__(label+(' normal return' if kind=='normal' else ''))

def plan_chat_prelude(message,chat_log_byte,o):
    if not isinstance(message,ChatPartyMessage) or not isinstance(o,ChatPreludeObservation):raise ValueError('Typed bounded message/prelude inputs required')
    if type(chat_log_byte) is not int or not 0<=chat_log_byte<=255:raise ValueError('Raw source Chat Log BYTE required')
    steps=[];intent=None
    def normal(label):
        steps.append(('normal_return',label))
        if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
    def result(error=None):
        return ChatPreludePlan(error is None,'command_entry_reached' if error is None else 'needs_observation',
            intent,tuple(steps),'' if error is None else str(error),None if error is None else error.request,error is None)
    try:
        normal('input_copy_and_sender_parse')
        normal('text_buffers_prepare')
        normal('message_objects_construct')
        steps.append(('chat_log_flag',chat_log_byte))
        if chat_log_byte:
            normal('log_strings_construct')
            steps.append(('log_channel_filter',message.channel))
            if message.channel in LOG_LABELS:
                label=LOG_LABELS[message.channel]
                if message.channel!=6:normal('log_label_%d'%message.channel)
                # Own bounded byte projection, separately checked against an observation.
                line=b'['+label+b'] '+message.name.split(b'\0',1)[0]+b' : '+message.message.split(b'\0',1)[0]
                intent=ChatLogIntent(message.channel,line)
                normal('log_assembly')
                if o.assembled_log_bytes is None:raise _Missing('value','assembled log byte snapshot')
                if o.assembled_log_bytes!=line:raise ValueError('Observed log bytes differ from bounded own projection')
                intent=replace(intent,observed_line=o.assembled_log_bytes)
                normal('log_sink') #405738 normal return does not prove a displayed/stored log.
                intent=replace(intent,sink_normal_return_observed=True)
                normal('log_line_cleanup')
            normal('log_strings_cleanup')
        steps.append(('source_entry','004565c9'))
        return result()
    except _Missing as error:return result(error)

class ChatPreludeFrame:
    def __init__(self,message,chat_log_byte):
        # Validate stable constructor inputs without consuming a source observation.
        plan_chat_prelude(message,chat_log_byte,ChatPreludeObservation())
        self.message=message;self.chat_log_byte=chat_log_byte;self.observation=ChatPreludeObservation();self.final=None
    def advance(self,o):
        if not isinstance(o,ChatPreludeObservation):raise ValueError('Typed prelude observations required')
        if self.final is not None:return self.final
        for _ in range(16):
            p=plan_chat_prelude(self.message,self.chat_log_byte,self.observation)
            if p.complete:self.final=p;return p
            kind,label=p.request
            if kind=='normal':
                if o.normal_returns.get(label) is not True:return p
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
            else:
                if o.assembled_log_bytes is None:return p
                self.observation=replace(self.observation,assembled_log_bytes=o.assembled_log_bytes)
        raise ValueError('Prelude frame exceeded source prefix budget')

@dataclass(frozen=True)
class ChatCommandEntryPlan:
    complete:bool
    status:str
    prefix:object
    prelude:object=None
    commands:object=None
    missing:str=''
    native_execution_verified:bool=False
    full_handler_verified:bool=False
    @property
    def actions(self):return () if self.commands is None else self.commands.actions

class ChatCommandEntryFrame:
    """Owned bounded parsing -> prelude -> command span; no full handler claim."""
    def __init__(self,configuration,captured,chat_log_byte):
        if not isinstance(configuration,ChatCommandsConfiguration):raise ValueError('Stable command configuration required')
        self.prefix=parse_chat_prefix(captured);self.prelude=None;self.commands=None;self.final=None
        if self.prefix.complete and self.prefix.message is not None:
            self.prelude=ChatPreludeFrame(self.prefix.message,chat_log_byte)
            self.commands=ChatCommandsFrame(configuration,self.prefix.message)
    def advance(self,prelude_observation,command_observation):
        if not isinstance(prelude_observation,ChatPreludeObservation) or not isinstance(command_observation,ChatCommandsObservation):
            raise ValueError('Separate typed prelude/command observations required')
        if self.final is not None:return self.final
        if not self.prefix.complete:return ChatCommandEntryPlan(False,'needs_bytes',self.prefix,missing=self.prefix.missing)
        if self.prefix.message is None:
            self.final=ChatCommandEntryPlan(True,'other_opcode',self.prefix);return self.final
        pre=self.prelude.advance(prelude_observation)
        if not pre.complete:return ChatCommandEntryPlan(False,'needs_prelude',self.prefix,pre,missing=pre.missing)
        cmd=self.commands.advance(command_observation)
        p=ChatCommandEntryPlan(cmd.complete,'command_entry_span_returned' if cmd.complete else 'needs_commands',self.prefix,pre,cmd,cmd.missing)
        if p.complete:self.final=p
        return p
