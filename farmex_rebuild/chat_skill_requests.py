"""Reached4569d9..457014 PM/party pending-request producer; never casts skills."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType
from chat_party_invite import ChatPartyMessage
from name_codec import WindowsNameCodec

# key, family, checkbox, text, flag offset, command offset, form flag/text slots, request kind
SPECS=(
 ('mage_tp','Mage','chChatTP','txtChatTP',0x18c,0x190,0xe5c,0xe60,1),
 ('rogue_sw','Rogue','chChatSW','txtChatSW',0x1b8,0x1c0,0x1040,0x104c,1),
 ('rogue_wolf','Rogue','chChatWolf','txtChatWolf',0x1e8,0x1f0,0x1050,0x1054,2),
 ('priest_buff','Priest','chChatBuff','txtChatBuff',0x218,0x220,0x1100,0x110c,1),
 ('priest_ac','Priest','chChatAC','txtChatAC',0x248,0x250,0x1118,0x1124,2),
 ('priest_und','Priest','chChatUnd','txtChatUnd',0x278,0x280,0x1120,0x111c,3),
 ('priest_str','Priest','chChatStr15','txtChatStr15',0x2a8,0x2b0,0x1104,0x1110,4),
 ('priest_cure','Priest','chChatCure','txtChatCure',0x2d8,0x2e0,0x1108,0x1114,5),
 ('priest_disease','Priest','chChatDisease','txtChatDisease',0x308,0x310,0x1128,0x112c,6))
ROOTS={'Mage':'frmMain/MainTab/SheetJob/pnlMage/GroupBox4/',
       'Rogue':'frmMain/MainTab/SheetJob/pnlRogue/GroupBox37/',
       'Priest':'frmMain/MainTab/SheetJob/pnlPri/GroupBox8/'}
CHAT_SKILL_INPUTS=tuple(ROOTS[s[1]]+n for s in SPECS for n in s[2:4])
def _raw(v,width=4):
    if type(v) is not int or not 0<=v<1<<(8*width):raise ValueError('Raw chat skill observation required')

@dataclass(frozen=True)
class ChatSkillSetting:
    key:str
    enabled_byte:int
    command:bytes
    def __post_init__(self):
        _raw(self.enabled_byte,1)
        if type(self.command) is not bytes:raise ValueError('Immutable source keyword required')

@dataclass(frozen=True)
class ChatSkillConfiguration:
    settings:tuple
    codepage:object=None
    def __post_init__(self):
        if type(self.settings) is not tuple or any(not isinstance(s,ChatSkillSetting) for s in self.settings) or tuple(s.key for s in self.settings)!=tuple(s[0] for s in SPECS):
            raise ValueError('All nine ordered source chat settings required')

def compile_chat_skills(values,codec):
    if not isinstance(codec,WindowsNameCodec):raise ValueError('Explicit Windows codepage required')
    settings=[]
    for key,family,check,text,*_ in SPECS:
        enabled=values.get(ROOTS[family]+check);command=values.get(ROOTS[family]+text)
        if type(enabled) is not bool or type(command) is not str:raise ValueError('Known chat skill checkbox/text required')
        data,used=codec.encode(command)
        if used is True or codec.decode(data)!=command:raise ValueError('Lossless source keyword encoding required')
        settings.append(ChatSkillSetting(key,int(enabled),data.split(b'\0',1)[0]))
    return ChatSkillConfiguration(tuple(settings),codec.code_page)

WIDTHS=dict(channel_first=1,channel_second=1,channel_for_pm_alarm=1,pm_alarm_flag=1,
            runtime_ready_byte=1,pending_byte=1,mage_probe_eax=4,rogue_probe_eax=4,priest_probe_eax=4,priest_buff_gate_eax=4)
@dataclass(frozen=True)
class ChatSkillObservation:
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    def __post_init__(self):
        values=dict(self.values);returns=dict(self.normal_returns)
        for key,v in values.items():_raw(v,WIDTHS.get(key,4))
        if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate chat skill normal receipts required')
        object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(returns))

@dataclass(frozen=True)
class PendingChatSkillRequest:
    key:str
    kind:int
    sender_dword:int
    context_stores:tuple
    skill_execution_verified:bool=False

@dataclass(frozen=True)
class ChatSkillPlan:
    complete:bool
    status:str
    queued_request:object=None
    steps:tuple=()
    next_address:str='0045730e'
    missing:str=''
    needed:object=None
    native_execution_verified:bool=False

class _Missing(Exception):
    def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+(' normal return' if kind=='normal' else ' value'))

def plan_chat_skill_requests(c,message,o):
    if not isinstance(c,ChatSkillConfiguration) or not isinstance(message,ChatPartyMessage) or not isinstance(o,ChatSkillObservation):raise ValueError('Typed reached chat skill inputs required')
    settings={s.key:s for s in c.settings};steps=[];queued=None
    def result(error=None,status='request_span_returned',next_address='0045730e'):
        return ChatSkillPlan(error is None,status if error is None else 'needs_observation',queued,tuple(steps),next_address,
                             '' if error is None else str(error),None if error is None else error.needed)
    def value(label):
        steps.append(('source_value',label))
        if label not in o.values:raise _Missing('value',label)
        return o.values[label]
    def normal(label):
        steps.append(('normal_return',label))
        if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
    def probe(family):
        normal(family.lower()+'_probe_span')
        return value(family.lower()+'_probe_eax')&255
    def compare(key):
        s=settings[key]
        if not s.enabled_byte:return False
        steps.append(('own_exact_compare',key,message.message,s.command));normal('compare:'+key)
        return message.message==s.command
    def queue(key):
        nonlocal queued
        spec=next(s for s in SPECS if s[0]==key);kind=spec[-1]
        queued=PendingChatSkillRequest(key,kind,message.sender_dword,((0x180,1,1),(0x184,4,kind),(0x188,4,message.sender_dword)))
    try:
        if value('channel_first')!=2 and value('channel_second')!=3:
            return result(status='outside_pm_party_span',next_address='00457014')
        if value('channel_for_pm_alarm')==2 and value('pm_alarm_flag'):
            steps.append(('opaque_alarm_span','00456a0d..00456a58','00404260',0x569568,b'Default'))
            normal('pm_alarm_span')
        if value('runtime_ready_byte')==0:return result(status='runtime_gate_closed')
        if value('pending_byte')!=0:return result(status='pending_request_preserved')
        if probe('Mage'):
            if compare('mage_tp'):queue('mage_tp')
            return result()
        if probe('Rogue'):
            for key in ('rogue_sw','rogue_wolf'):
                if compare(key):queue(key);break
            return result()
        if probe('Priest'):
            for key in ('priest_buff','priest_ac','priest_und','priest_str','priest_cure','priest_disease'):
                if not settings[key].enabled_byte:continue
                if key=='priest_buff':
                    normal('priest_buff_gate');raw=value('priest_buff_gate_eax')
                    signed=raw-(1<<32) if raw&0x80000000 else raw
                    if signed<2:continue
                if compare(key):queue(key);break
        return result()
    except _Missing as error:return result(error)

class ChatSkillFrame:
    def __init__(self,configuration,message):
        if not isinstance(configuration,ChatSkillConfiguration) or not isinstance(message,ChatPartyMessage):raise ValueError('Stable chat skill invocation required')
        self.configuration=configuration;self.message=message;self.observation=ChatSkillObservation();self.final=None
    def advance(self,o):
        if not isinstance(o,ChatSkillObservation):raise ValueError('Typed chat skill observations required')
        if self.final is not None:return self.final
        for _ in range(32):
            p=plan_chat_skill_requests(self.configuration,self.message,self.observation)
            if p.complete:self.final=p;return p
            kind,label=p.needed
            if kind=='normal':
                if o.normal_returns.get(label) is not True:return p
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
            else:
                if label not in o.values:return p
                self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
        raise ValueError('Chat skill frame exceeded source span budget')
