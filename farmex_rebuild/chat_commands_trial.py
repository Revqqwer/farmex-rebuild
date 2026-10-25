"""Fresh real-panel adapter for one explicitly reached command invocation."""
import json
from chat_commands import (SPECS,FIELD_LABELS,ChatCommandsObservation,ChatCommandsFrame,compile_chat_commands)
from chat_party_invite import parse_chat_prefix
from name_codec import WindowsNameCodec
from command_helper_trial import CommandHelpersTrial,synthetic_command_helpers

EXAMPLE_COMMAND_HEX='1001000700000005416c696365027f676f'

def example_chat_commands_sample():
    returns={prefix+key:True for key,*_ in SPECS for prefix in ('compare:','action:')}
    returns.update(genie_start_state=True,genie_remaining=True,genie_stop_state=True)
    return json.dumps(dict(helper_returns=returns,center_y_dword=20,center_y_f32_bits=0x41a00000,
        center_x_dword=10,center_x_f32_bits=0x41200000,genie_blocked_byte=0,
        genie_start_state_eax=0,genie_remaining_eax=1,genie_stop_state_eax=1))

def example_detailed_commands_sample():
    raw=json.loads(example_chat_commands_sample());raw['helpers']=synthetic_command_helpers()
    return json.dumps(raw)

def advance_command_sample(frame,raw,helper_trial=None):
    if not isinstance(frame,ChatCommandsFrame) or type(raw) is not dict:
        raise ValueError('Typed command frame and JSON object required')
    seen=set()
    for _ in range(64):
        p=frame.advance(ChatCommandsObservation())
        if p.complete:return p
        if p.missing in seen:return p
        seen.add(p.missing)
        if helper_trial is not None and p.actions and (p.missing.startswith('bound action:') or p.missing.startswith('action:')):
            action=p.actions[-1];samples=raw.get('helpers',{})
            if type(samples) is not dict:raise ValueError('Reached helpers must be an object')
            child=helper_trial.advance(action,samples.get(action.key,{}))
            before=p.missing
            p=frame.advance(ChatCommandsObservation(action_executions={action.key:child}))
            if p.complete:return p
            if not child.complete:return p
            if p.missing!=before:continue
        if p.missing.endswith(' normal return'):
            label=p.missing[:-14];returns=raw.get('helper_returns',{})
            if type(returns) is not dict:raise ValueError('Command helper_returns must be an object')
            if label not in returns:return p
            o=ChatCommandsObservation(helper_returns={label:returns[label]})
        else:
            field=next((name for name,label in FIELD_LABELS.items() if label==p.missing),None)
            if field is None or field not in raw:return p
            o=ChatCommandsObservation(**{field:raw[field]})
        p=frame.advance(o)
        if p.complete:return p
    raise ValueError('Command sample exceeded reached-field budget')

class ChatCommandsTrial:
    def __init__(self,configuration_reader):
        self.configuration_reader=configuration_reader;self.reset()
    def reset(self):
        self.last=None;self.configuration=None;self.captured=None;self.frame=None;self.helpers=None;self.detailed_helpers=None
    def step(self,packet_hex,sample_text,codepage,detailed_helpers=False):
        self.last=None
        try:
            if self.configuration_reader is None:raise ValueError('Command trial needs a panel reader')
            if type(packet_hex) is not str:raise ValueError('Captured command HEX text required')
            captured=bytes.fromhex(packet_hex);raw=json.loads(sample_text)
            if type(raw) is not dict:raise ValueError('Command observations must be a JSON object')
            if type(detailed_helpers) is not bool:raise ValueError('Explicit detailed-helper trial choice required')
            values,_=self.configuration_reader()
            c=compile_chat_commands(values,WindowsNameCodec(codepage))
            if captured!=self.captured or c!=self.configuration or detailed_helpers!=self.detailed_helpers:
                self.frame=None;self.helpers=None
            self.detailed_helpers=detailed_helpers
            self.captured=captured;self.configuration=c
            prefix=parse_chat_prefix(captured)
            if not prefix.complete or prefix.message is None:
                self.last=prefix;return prefix
            if self.frame is None:
                self.frame=ChatCommandsFrame(c,prefix.message)
                self.helpers=CommandHelpersTrial() if detailed_helpers else None
            self.last=advance_command_sample(self.frame,raw,self.helpers)
            return self.last
        except (ValueError,TypeError,OSError):
            self.reset();raise
