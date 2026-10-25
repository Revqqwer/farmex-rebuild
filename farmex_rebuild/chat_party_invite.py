"""Reached 00456804 chat-invite decision and bounded own data plans.

No preceding chat branches, native calls, game input or network transmission.
The bounded parser is our policy, not vendor malformed-packet behavior.
"""
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from action_queue import QueueState, QueueDecision, enqueue
from name_codec import WindowsNameCodec
from party_invitation import ROOT, PARTY_LIST

CHAT_PARTY_INPUTS = tuple(ROOT+n for n in
                         ('chinvitechat', 'txtinvitechat', 'chPartyChatInviteListControl'))

def _raw(value, bits, optional=False):
    if optional and value is None:
        return
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError('Raw unsigned %d-bit observation required' % bits)

@dataclass(frozen=True)
class ChatPartyConfiguration:
    enabled_byte: int
    list_only_byte: int
    command: bytes
    names: object = None
    codepage: object = None

    def __post_init__(self):
        _raw(self.enabled_byte, 8); _raw(self.list_only_byte, 8)
        if type(self.command) is not bytes:
            raise ValueError('Immutable command bytes required')
        if self.names is not None and (type(self.names) is not tuple or
                                      any(type(n) is not bytes for n in self.names)):
            raise ValueError('Explicit stable ordered name bytes required')

def compile_chat_party(values, lists, codec):
    if not isinstance(codec, WindowsNameCodec):
        raise ValueError('Explicit local Windows codepage required')
    enabled, text, restricted = (values.get(p) for p in CHAT_PARTY_INPUTS)
    if type(enabled) is not bool or type(restricted) is not bool or type(text) is not str:
        raise ValueError('Known chat party panel values required')
    def encode(text):
        data, used = codec.encode(text)
        if used is True or codec.decode(data) != text:
            raise ValueError('Lossless command/name encoding required')
        return data.split(b'\0', 1)[0]
    rows = lists.get(PARTY_LIST)
    if type(rows) is not list:
        raise ValueError('Known shared party name rows required')
    names = []
    for row in rows:
        if type(row) is not dict or type(row.get('caption')) is not str:
            raise ValueError('Known party row caption required')
        names.append(encode(row['caption']))
    return ChatPartyConfiguration(int(enabled), int(restricted), encode(text), tuple(names), codec.code_page)

@dataclass(frozen=True)
class ChatPartyMessage:
    channel: int
    sender_dword: int
    name: bytes
    message: bytes

    def __post_init__(self):
        _raw(self.channel, 8); _raw(self.sender_dword, 32)
        if type(self.name) is not bytes or type(self.message) is not bytes:
            raise ValueError('Explicit immutable source string observations required')

@dataclass(frozen=True)
class ChatPrefixPlan:
    complete: bool
    status: str
    message: object = None
    missing: str = ''
    native_execution_verified: bool = False

def parse_chat_prefix(captured):
    if type(captured) is not bytes:
        raise ValueError('Immutable captured bytes required')
    def gap(label):
        return ChatPrefixPlan(False, 'needs_bytes', missing=label)
    if not captured:
        return gap('chat opcode')
    if captured[0] != 0x10:
        return ChatPrefixPlan(True, 'other_opcode')
    if len(captured) < 8:
        return gap('chat fixed prefix')
    name_length = captured[7]
    if len(captured) <= 8 + name_length:
        return gap('chat message length byte')
    message_length = captured[8 + name_length]
    start = 10 + name_length
    if len(captured) < start + message_length:
        return gap('bounded chat message span')
    msg = ChatPartyMessage(captured[1], int.from_bytes(captured[3:7], 'little'),
                           captured[8:8+name_length].split(b'\0', 1)[0],
                           captured[start:start+message_length].split(b'\0', 1)[0])
    return ChatPrefixPlan(True, 'bounded_owned_prefix', msg)

@dataclass(frozen=True)
class ChatPartyObservation:
    actor_dword: object = None
    use_owned_filter: bool = False
    filter_eax: object = None
    helper_returns: object = field(default_factory=dict)
    invitation: object = None

    def __post_init__(self):
        _raw(self.actor_dword, 32, True); _raw(self.filter_eax, 32, True)
        if type(self.use_owned_filter) is not bool:
            raise ValueError('Explicit owned-filter selection required')
        if any(type(v) is not bool for v in self.helper_returns.values()):
            raise ValueError('Separate normal-return receipts required')
        object.__setattr__(self, 'helper_returns', MappingProxyType(dict(self.helper_returns)))
        if self.invitation is not None and not isinstance(self.invitation, ChatInviteEmissionPlan):
            raise ValueError('Typed own invitation plan required')

@dataclass(frozen=True)
class ChatPartyDecision:
    complete: bool
    status: str
    action: object = None
    matched: object = None
    calls: tuple = ()
    missing: str = ''
    native_execution_verified: bool = False

def plan_chat_party(c, msg, o):
    """Entry is explicitly the reached invite span, not the full chat handler."""
    if not isinstance(c, ChatPartyConfiguration) or not isinstance(msg, ChatPartyMessage) or not isinstance(o, ChatPartyObservation):
        raise ValueError('Typed reached chat span inputs required')
    calls = []; matched = None; action = None
    class Missing(Exception): pass
    def normal(label):
        calls.append(('normal_return', label))
        if o.helper_returns.get(label) is not True:
            raise Missing(label+' normal return')
    def result(ok, status, missing=''):
        return ChatPartyDecision(ok, status, action, matched, tuple(calls), missing)
    try:
        if msg.channel == 3:
            return result(True, 'excluded_channel')
        if c.enabled_byte == 0:
            return result(True, 'disabled')
        calls.append(('00457388', msg.message, c.command)); normal('command_compare')
        if msg.message != c.command:
            return result(True, 'command_mismatch')
        calls.append(('00462650',)); normal('actor')
        if o.actor_dword is None:
            raise Missing('actor DWORD')
        if o.actor_dword == msg.sender_dword:
            return result(True, 'self_sender')
        if c.list_only_byte:
            normal('filter_arguments')
            calls.append(('004cbecc', 0x569584, msg.name)); normal('name_filter')
            if o.use_owned_filter:
                if o.filter_eax is not None:
                    raise ValueError('Owned filter conflicts with raw EAX')
                if c.names is None:
                    raise Missing('owned stable name vector')
                matched = msg.name in c.names
            else:
                if o.filter_eax is None:
                    raise Missing('name-filter EAX')
                matched = bool(o.filter_eax & 255)
            if not matched:
                return result(True, 'unlisted')
        normal('invite_arguments')
        action = 'invite'
        calls.append(('004ca694', 0x561ef8, msg.name))
        if o.invitation is not None:
            if o.invitation.name != msg.name:
                raise ValueError('Bound invitation belongs to a different name')
            if not o.invitation.complete:
                raise Missing('bound invitation: '+o.invitation.missing)
        normal('invite')
        return result(True, 'reached_invite_span_returned')
    except Missing as error:
        return result(False, 'needs_observation', str(error))

@dataclass(frozen=True)
class ChatInviteEmissionPlan:
    complete: bool
    name: bytes
    queue: QueueState
    outcomes: tuple = ()
    missing: str = ''
    native_execution_verified: bool = False

    def __post_init__(self):
        if type(self.complete) is not bool or type(self.name) is not bytes or not isinstance(self.queue, QueueState):
            raise ValueError('Typed own invitation emission result required')
        if type(self.outcomes) is not tuple or any(not isinstance(d, QueueDecision) or d.state is None for d in self.outcomes):
            raise ValueError('Known ordered own enqueue outcomes required')
        if len(self.outcomes) > 2 or (self.outcomes and self.outcomes[-1].state != self.queue):
            raise ValueError('Emission outcomes must end at the reported own queue')
        if self.complete and (len(self.outcomes) != 2 or self.missing or len(self.name) > 96):
            raise ValueError('Both non-overlapping source enqueue outcomes required before completion')

class ChatInviteEmissionFrame:
    """004ca694 safe non-overlapping stack scope, two independent own enqueues.

    Source buffer starts EBP-0x90; cursor at EBP-0x2c overlaps byte 100.
    Names longer than 96 bytes remain unresolved, not silently truncated.
    Own queue outcomes and each native-call normal receipt are separate.
    """
    def __init__(self, name, queue=None):
        if type(name) is not bytes:
            raise ValueError('Immutable source name string required')
        self.name = name
        self.queue = QueueState() if queue is None else queue
        if not isinstance(self.queue, QueueState):
            raise ValueError('Own local queue required')
        self.stage = 0; self.outcomes = []; self.pending = False; self.final = None
        self.gates = [None, None]

    def advance(self, *, gates=(), ticks=(), returned=(), cleanup_returned=None):
        if self.final is not None:
            return self.final
        def result(complete, missing=''):
            return ChatInviteEmissionPlan(complete, self.name, self.queue, tuple(self.outcomes), missing)
        if len(self.name) > 96:
            return result(False, 'source stack overlap for name length >96; native behavior unresolved')
        for i in range(self.stage, 2):
            if not self.pending:
                if self.gates[i] is None:
                    gate = gates[i] if len(gates) > i else None
                    _raw(gate, 32, True)
                    if gate is not None:
                        self.gates[i] = gate
                gate = self.gates[i]
                tick = ticks[i] if len(ticks) > i else None
                payload = bytes((0x2f, 3 if i == 0 else 1)) + len(self.name).to_bytes(2, 'little') + self.name
                d = enqueue(self.queue, payload, len(payload), 0, gate, tick)
                if d.state is None:
                    return result(False, 'enqueue %d: %s' % (i+1, d.missing or d.status))
                self.queue = d.state; self.outcomes.append(d); self.pending = True
            normal = returned[i] if len(returned) > i else None
            if normal is not None and type(normal) is not bool:
                raise ValueError('Separate enqueue normal-return receipt required')
            if normal is not True:
                return result(False, 'enqueue %d normal return' % (i+1))
            self.pending = False; self.stage = i+1
        if cleanup_returned is not None and type(cleanup_returned) is not bool:
            raise ValueError('Separate string cleanup receipt required')
        if cleanup_returned is not True:
            return result(False, 'invitation string cleanup normal return')
        self.final = result(True)
        return self.final

class ChatPartyInvitationFrame:
    """One explicitly reached branch; resume consumed prefix without re-reading it."""
    def __init__(self, configuration, message, queue=None):
        if not isinstance(configuration, ChatPartyConfiguration) or not isinstance(message, ChatPartyMessage):
            raise ValueError('Typed reached chat branch snapshot required')
        self.configuration = configuration; self.message = message
        self.queue = QueueState() if queue is None else queue
        if not isinstance(self.queue, QueueState):
            raise ValueError('Own local queue required')
        self.observation = ChatPartyObservation()
        self.emission = None; self.final = None

    def advance(self, observation, *, gates=(), ticks=(), returned=(), cleanup_returned=None):
        if not isinstance(observation, ChatPartyObservation):
            raise ValueError('Typed reached chat observations required')
        if self.final is not None:
            return self.final
        for _ in range(16):
            p = plan_chat_party(self.configuration, self.message, self.observation)
            if p.complete:
                self.final = p
                return p
            if p.action == 'invite':
                if observation.invitation is not None:
                    raise ValueError('Owned chat frame conflicts with external invitation plan')
                if self.emission is None:
                    self.emission = ChatInviteEmissionFrame(self.message.name, self.queue)
                child = self.emission.advance(gates=gates, ticks=ticks, returned=returned, cleanup_returned=cleanup_returned)
                self.queue = child.queue
                self.observation = replace(self.observation, invitation=child)
                p = plan_chat_party(self.configuration, self.message, self.observation)
                if not child.complete:
                    return p
            if p.missing.endswith(' normal return'):
                label = p.missing[:-14]
                if observation.helper_returns.get(label) is not True:
                    return p
                self.observation = replace(self.observation, helper_returns={**self.observation.helper_returns, label: True})
                continue
            if p.missing == 'actor DWORD':
                if observation.actor_dword is None:
                    return p
                self.observation = replace(self.observation, actor_dword=observation.actor_dword)
                continue
            if p.missing == 'name-filter EAX':
                if not observation.use_owned_filter and observation.filter_eax is None:
                    return p
                self.observation = replace(self.observation, use_owned_filter=observation.use_owned_filter, filter_eax=observation.filter_eax)
                continue
            return p
        raise ValueError('Reached chat frame exceeded source prefix budget')
