"""Captured-data party trial, fresh own panel and reached-only observations."""
import json
from dataclasses import replace
from party_invitation import PartyInviteObservation,compile_party_invitation,plan_party_invitation
from name_codec import WindowsNameCodec

RETURNS=('party_state','read_inviter','read_name_length','read_name','name_filter','accept','reject','name_cleanup')

def parse_invitation_sample(text,c,captured):
    try:raw=json.loads(text)
    except (ValueError,TypeError) as e:raise ValueError('Invitation observations must be JSON') from e
    if type(raw) is not dict:raise ValueError('Invitation observations must be an object')
    o=PartyInviteObservation();seen=set()
    for _ in range(22):
        p=plan_party_invitation(c,captured,o)
        if p.complete:return o
        field={'0056228d BYTE':'blocked_byte_56228d','party-state EAX':'party_state_eax'}.get(p.missing)
        key=field
        if field:
            if field not in raw:return o
            value=raw[field]
        elif p.missing.endswith(' normal return') and p.missing[:-14] in RETURNS:
            label=p.missing[:-14];key=('return',label);field='helper_returns'
            returns=raw.get(field,{})
            if type(returns) is not dict:raise ValueError('Invitation helper returns must be an object')
            if label not in returns:return o
            if type(returns[label]) is not bool:raise ValueError('Invitation return must be boolean: '+label)
            value={**o.helper_returns,label:returns[label]}
        elif p.missing=='name-filter EAX':
            key='filter';owned=raw.get('use_owned_filter',False)
            if type(owned) is not bool:raise ValueError('Owned filter choice must be boolean')
            o=replace(o,use_owned_filter=owned,filter_eax=raw.get('filter_eax'))
            if key in seen:return o
            seen.add(key);continue
        else:return o # Bounds/unknown producer state remain explicit gaps.
        if key in seen:return o
        seen.add(key);o=replace(o,**{field:value})
    raise ValueError('Invitation sample exceeded reached-field budget')

def example_invitation_sample():
    return json.dumps(dict(blocked_byte_56228d=0,party_state_eax=0,use_owned_filter=True,
                           helper_returns={name:True for name in RETURNS}))

class PartyInvitationTrial:
    def __init__(self,configuration_reader):self.configuration_reader=configuration_reader;self.reset()
    def reset(self):self.last=None;self.configuration=None;self.captured=None
    def step(self,packet_hex,sample_text,codepage):
        self.last=None;self.captured=None
        if self.configuration_reader is None:raise ValueError('Invitation trial needs a panel reader')
        if type(packet_hex) is not str:raise ValueError('Captured hex text required')
        captured=bytes.fromhex(packet_hex)
        values,lists=self.configuration_reader()
        c=compile_party_invitation(values,lists,WindowsNameCodec(codepage));self.configuration=c
        o=parse_invitation_sample(sample_text,c,captured)
        self.last=plan_party_invitation(c,captured,o);self.captured=captured
        return self.last
