"""Real-panel adapter for one reached chat-skill request; no skill execution."""
import json
from chat_skill_requests import SPECS,compile_chat_skills,ChatSkillFrame,ChatSkillObservation
from chat_party_invite import parse_chat_prefix
from name_codec import WindowsNameCodec

EXAMPLE_SKILL_HEX='1002000700000005416c696365027f676f'
def example_chat_skills_sample(family='Mage'):
    if family not in ('Mage','Rogue','Priest'):raise ValueError('Known synthetic family required')
    return json.dumps(dict(values=dict(channel_first=2,channel_second=3,channel_for_pm_alarm=2,pm_alarm_flag=0,
        runtime_ready_byte=1,pending_byte=0,mage_probe_eax=int(family=='Mage'),rogue_probe_eax=int(family=='Rogue'),
        priest_probe_eax=int(family=='Priest'),priest_buff_gate_eax=2),
        normal_returns={**{k:True for k in ('mage_probe_span','rogue_probe_span','priest_probe_span','priest_buff_gate','pm_alarm_span')},
                        **{'compare:'+s[0]:True for s in SPECS}}))

def advance_chat_skills_sample(frame,raw):
    if not isinstance(frame,ChatSkillFrame) or type(raw) is not dict:raise ValueError('Typed request frame and JSON object required')
    seen=set()
    for _ in range(32):
        p=frame.advance(ChatSkillObservation())
        if p.complete:return p
        if p.needed in seen:return p
        seen.add(p.needed);kind,label=p.needed
        sample=raw.get('normal_returns' if kind=='normal' else 'values',{})
        if type(sample) is not dict:raise ValueError('Reached skill observation group must be an object')
        if label not in sample:return p
        o=ChatSkillObservation(normal_returns={label:sample[label]}) if kind=='normal' else ChatSkillObservation(values={label:sample[label]})
        p=frame.advance(o)
        if p.complete:return p
    raise ValueError('Skill request sample exceeded reached-field budget')

class ChatSkillsTrial:
    def __init__(self,configuration_reader):self.configuration_reader=configuration_reader;self.reset()
    def reset(self):self.last=None;self.frame=None;self.configuration=None;self.captured=None
    def step(self,packet_hex,sample_text,codepage):
        self.last=None
        try:
            if self.configuration_reader is None:raise ValueError('Chat skill trial needs a panel reader')
            if type(packet_hex) is not str:raise ValueError('Captured chat HEX required')
            captured=bytes.fromhex(packet_hex);raw=json.loads(sample_text)
            if type(raw) is not dict:raise ValueError('Chat skill sample must be an object')
            values,_=self.configuration_reader();c=compile_chat_skills(values,WindowsNameCodec(codepage))
            if c!=self.configuration or captured!=self.captured:self.frame=None
            self.configuration=c;self.captured=captured
            prefix=parse_chat_prefix(captured)
            if not prefix.complete or prefix.message is None:self.last=prefix;return prefix
            if self.frame is None:self.frame=ChatSkillFrame(c,prefix.message)
            self.last=advance_chat_skills_sample(self.frame,raw);return self.last
        except (ValueError,TypeError,OSError):self.reset();raise
