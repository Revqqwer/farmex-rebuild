"""Scoped4d82a4 chat dispatch/filter plans; no packet hook or game effects.

455ec0 remains an opaque whole-handler normal-return boundary here. A completed
prelude/command submodel is not substituted for that whole handler's return.
"""
from dataclasses import dataclass,field,replace
from types import MappingProxyType

CHAT_BLOCK_LIST='frmMain/MainTab/SheetGenel/LwChatBlock'
# Actual source row->context mapping, not inferred from caption/channel names.
ROW_OFFSETS=(1,2,3,6,5,4,7,8)
CHANNEL_OFFSET=MappingProxyType({1:2,2:3,3:6,6:5,5:4,14:7,34:8})

def _raw(v,width=4):
    if type(v) is not int or not 0<=v<1<<(8*width):raise ValueError('Raw incoming value with exact width required')

@dataclass(frozen=True)
class ChatBlockConfiguration:
    context_bytes:tuple
    def __post_init__(self):
        if type(self.context_bytes) is not tuple or len(self.context_bytes)!=8:raise ValueError('Eight stable source context flags required')
        for v in self.context_bytes:_raw(v,1)

def compile_chat_block(rows):
    if not isinstance(rows,(tuple,list)) or len(rows)<8:raise ValueError('Eight known source checkbox rows required')
    values=[0]*8
    for row,offset in zip(rows[:8],ROW_OFFSETS):
        if type(row) is not dict or type(row.get('checked')) is not bool:raise ValueError('Known source row checked flag required')
        values[offset-1]=int(row['checked'])
    return ChatBlockConfiguration(tuple(values))

@dataclass(frozen=True)
class ChatBlockPlan:
    channel_byte:int
    low_al:int
    tested_offsets:tuple
    native_full_eax_verified:bool=False
    native_execution_verified:bool=False

def plan_chat_block(configuration,channel_dword):
    if not isinstance(configuration,ChatBlockConfiguration):raise ValueError('Typed stable chat filter flags required')
    _raw(channel_dword);channel=channel_dword&255;tested=[1]
    blocked=bool(configuration.context_bytes[0])
    if not blocked and channel in CHANNEL_OFFSET:
        offset=CHANNEL_OFFSET[channel];tested.append(offset);blocked=bool(configuration.context_bytes[offset-1])
    return ChatBlockPlan(channel,int(blocked),tuple(tested))

WIDTHS=dict(opcode_for_eight=1,opcode_for_chat=1,handler_length_dword=4,handler_buffer_dword=4,
            channel_for_exemption=1,channel_for_filter=1,channel_for_clan=1,
            clan_sender_word=2,clan_object_eax=4,clan_flag_offset_dword=4,clan_flag_eax=4)

@dataclass(frozen=True)
class IncomingChatObservation:
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    def __post_init__(self):
        values=dict(self.values);returns=dict(self.normal_returns)
        for key,v in values.items():_raw(v,WIDTHS.get(key,4))
        if any(type(v) is not bool for v in returns.values()):raise ValueError('Separate incoming normal receipts required')
        object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(returns))

@dataclass(frozen=True)
class IncomingChatPlan:
    complete:bool
    status:str
    source_return_dword:object=None
    handler_push_order:object=None
    filter_plan:object=None
    steps:tuple=()
    missing:str=''
    request:object=None
    native_execution_verified:bool=False
    packet_delivery_effect_verified:bool=False

class _Missing(Exception):
    def __init__(self,kind,label):self.request=(kind,label);super().__init__(label+(' normal return' if kind=='normal' else ' value'))

def plan_incoming_chat(configuration,o):
    if not isinstance(configuration,ChatBlockConfiguration) or not isinstance(o,IncomingChatObservation):raise ValueError('Typed incoming/filter inputs required')
    steps=[];pushes=None;filtered=None
    def result(value=None,error=None,status=None):
        return IncomingChatPlan(error is None,status or ('chat_branch_returned' if error is None else 'needs_observation'),
                                value,pushes,filtered,tuple(steps),'' if error is None else str(error),None if error is None else error.request)
    def value(label):
        steps.append(('source_value',label))
        if label not in o.values:raise _Missing('value',label)
        return o.values[label]
    def normal(label):
        steps.append(('normal_return',label))
        if o.normal_returns.get(label) is not True:raise _Missing('normal',label)
    try:
        normal('dispatcher_frame_setup')
        if value('opcode_for_eight')==8:
            raise _Missing('scope','earlier opcode08 branch outside scoped chat model')
        if value('opcode_for_chat')!=0x10:
            raise _Missing('scope','later nonchat dispatcher branches outside scope')
        length=value('handler_length_dword');buffer=value('handler_buffer_dword')
        pushes=(length,buffer,0x569220)
        steps.append(('opaque_handler','00455ec0',pushes));normal('whole_chat_handler')
        # Fresh original packet channel reads, not reuse of a prelude snapshot.
        if value('channel_for_exemption')!=7:
            channel=value('channel_for_filter')
            filtered=plan_chat_block(configuration,channel)
            steps.append(('own_filter','00455e0c',channel,filtered.low_al));normal('chat_filter')
            if filtered.low_al:return result(0)
        if value('channel_for_clan')==5:
            normal('clan_sender_parse');sender=value('clan_sender_word')
            if sender:
                steps.append(('opaque_call','00464a10',sender));normal('clan_lookup')
                pointer=value('clan_object_eax')
                if pointer:
                    offset=value('clan_flag_offset_dword')
                    steps.append(('guarded_BYTE_helper','0045dbdc',(pointer+offset)&0xffffffff))
                    normal('clan_flag_read')
                    if value('clan_flag_eax')&255==0:return result(0)
        return result(1)
    except _Missing as error:return result(error=error)

class IncomingChatFrame:
    def __init__(self,configuration):
        if not isinstance(configuration,ChatBlockConfiguration):raise ValueError('Stable source filter snapshot required')
        self.configuration=configuration;self.observation=IncomingChatObservation();self.final=None
    def advance(self,o):
        if not isinstance(o,IncomingChatObservation):raise ValueError('Typed incoming observations required')
        if self.final is not None:return self.final
        for _ in range(24):
            p=plan_incoming_chat(self.configuration,self.observation)
            if p.complete:self.final=p;return p
            kind,label=p.request
            if kind=='scope':return p
            if kind=='normal':
                if o.normal_returns.get(label) is not True:return p
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
            else:
                if label not in o.values:return p
                self.observation=replace(self.observation,values={**self.observation.values,label:o.values[label]})
        raise ValueError('Incoming chat frame exceeded source prefix budget')
