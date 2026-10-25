"""Fresh panel adapter for reached chat-invite frames; no native sender.

One unchanged captured/configuration snapshot resumes one invocation. Reset or
changed packet/config starts a new local invocation with an empty own queue.
JSON fields are validated only when the source-shaped plan demands them.
"""
import json
import re
from chat_party_invite import (ChatPartyObservation, ChatPartyInvitationFrame,
                               compile_chat_party, parse_chat_prefix)
from name_codec import WindowsNameCodec

EXAMPLE_CHAT_HEX = '1001000700000005416c696365037f616464'

def example_chat_party_sample():
    return json.dumps(dict(actor_dword=9, use_owned_filter=True,
        helper_returns={k:True for k in ('command_compare','actor','filter_arguments','name_filter','invite_arguments','invite')},
        queue_samples={'1':{'gate':1,'tick':100},'2':{'gate':1,'tick':101}},
        enqueue_returns={'1':True,'2':True}, cleanup_returned=True))

def advance_chat_sample(frame, raw):
    if not isinstance(frame, ChatPartyInvitationFrame) or type(raw) is not dict:
        raise ValueError('Typed chat frame and JSON object required')
    seen = set()
    for _ in range(32):
        p = frame.advance(ChatPartyObservation())
        if p.complete:
            return p
        key = p.missing
        if key in seen:
            return p
        seen.add(key)
        o = ChatPartyObservation(); kwargs = {}
        if key.endswith(' normal return') and not key.startswith('bound invitation:'):
            label = key[:-14]
            values = raw.get('helper_returns', {})
            if type(values) is not dict:
                raise ValueError('Chat helper_returns must be an object')
            if label not in values:
                return p
            o = ChatPartyObservation(helper_returns={label:values[label]})
        elif key == 'actor DWORD':
            if 'actor_dword' not in raw:
                return p
            o = ChatPartyObservation(actor_dword=raw['actor_dword'])
        elif key == 'name-filter EAX':
            o = ChatPartyObservation(use_owned_filter=raw.get('use_owned_filter',False), filter_eax=raw.get('filter_eax'))
        elif key == 'bound invitation: invitation string cleanup normal return':
            if 'cleanup_returned' not in raw:
                return p
            kwargs['cleanup_returned'] = raw['cleanup_returned']
        else:
            queue = re.fullmatch(r'bound invitation: enqueue ([12]): enqueue (connection gate|GetTickCount)',key)
            normal = re.fullmatch(r'bound invitation: enqueue ([12]) normal return',key)
            if queue:
                number, field = queue.groups(); index = int(number)-1
                samples = raw.get('queue_samples',{})
                if type(samples) is not dict:
                    raise ValueError('Chat queue_samples must be an object')
                if number not in samples:
                    return p
                sample = samples[number]
                if type(sample) is not dict:
                    raise ValueError('Reached chat enqueue sample must be an object')
                name = 'gate' if field == 'connection gate' else 'tick'
                if name not in sample:
                    return p
                values = [None,None]; values[index] = sample[name]
                kwargs['gates' if name == 'gate' else 'ticks'] = tuple(values)
            elif normal:
                number = normal[1]; values = raw.get('enqueue_returns',{})
                if type(values) is not dict:
                    raise ValueError('Chat enqueue_returns must be an object')
                if number not in values:
                    return p
                returns = [None,None]; returns[int(number)-1] = values[number]
                kwargs['returned'] = tuple(returns)
            else:
                return p
        p = frame.advance(o, **kwargs)
        if p.complete:
            return p
    raise ValueError('Chat sample exceeded reached-field budget')

class ChatPartyTrial:
    def __init__(self, configuration_reader):
        self.configuration_reader = configuration_reader
        self.reset()

    def reset(self):
        self.last = None; self.configuration = None; self.captured = None; self.frame = None

    def step(self, packet_hex, sample_text, codepage):
        self.last = None
        try:
            if self.configuration_reader is None:
                raise ValueError('Chat trial needs a panel reader')
            if type(packet_hex) is not str:
                raise ValueError('Captured chat hex text required')
            captured = bytes.fromhex(packet_hex)
            raw = json.loads(sample_text)
            if type(raw) is not dict:
                raise ValueError('Chat observations must be a JSON object')
            values, lists = self.configuration_reader()
            c = compile_chat_party(values, lists, WindowsNameCodec(codepage))
            if captured != self.captured or c != self.configuration:
                self.frame = None
            self.captured = captured; self.configuration = c
            prefix = parse_chat_prefix(captured)
            if not prefix.complete or prefix.message is None:
                self.last = prefix
                return prefix
            if self.frame is None:
                self.frame = ChatPartyInvitationFrame(c, prefix.message)
            self.last = advance_chat_sample(self.frame, raw)
            return self.last
        except (ValueError, TypeError, OSError):
            self.reset()
            raise
