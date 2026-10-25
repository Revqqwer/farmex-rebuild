"""Party invitation source decision plan, owned byte list, no network actions."""
from dataclasses import dataclass,field
from types import MappingProxyType
from name_codec import WindowsNameCodec
from party_replies import PartyReplyPlan

ROOT='frmMain/MainTab/SheetDiger/GroupBox30/'
PARTY_LIST=ROOT+'GroupBox42/PartyList'
PARTY_INVITE_INPUTS=tuple(ROOT+n for n in ('chotoparty','rdAllPartyAccept','chpartyred','chDisablePtBug'))+(PARTY_LIST,)

@dataclass(frozen=True)
class PartyInviteConfiguration:
    enabled_byte:int
    list_only_byte:int
    reject_unlisted_byte:int
    party_bug_byte:int
    names:object=None
    codepage:object=None
    def __post_init__(self):
        for v in (self.enabled_byte,self.list_only_byte,self.reject_unlisted_byte,self.party_bug_byte):
            if type(v) is not int or not 0<=v<256:raise ValueError('Raw invitation BYTE required')
        if self.names is not None and (type(self.names) is not tuple or any(type(v) is not bytes for v in self.names)):raise ValueError('Owned ordered name byte strings required')

def compile_party_invitation(values,lists,codec):
    if not isinstance(codec,WindowsNameCodec):raise ValueError('Explicit local Windows codepage required')
    flags=[values.get(p) for p in PARTY_INVITE_INPUTS[:4]]
    if any(type(v) is not bool for v in flags):raise ValueError('Known invitation panel choices required')
    rows=lists.get(PARTY_LIST)
    if type(rows) is not list:raise ValueError('Known party list rows required')
    names=[]
    for row in rows:
        if type(row) is not dict or type(row.get('caption')) is not str:raise ValueError('Known party row caption required')
        text=row['caption'];data,used=codec.encode(text)
        if used is True or codec.decode(data)!=text:raise ValueError('Party name cannot be losslessly encoded')
        # Source converts the caption then constructs std::string from char*.
        names.append(data.split(b'\0',1)[0])
    return PartyInviteConfiguration(int(flags[0]),0 if flags[1] else 1,int(flags[2]),int(flags[3]),tuple(names),codec.code_page)

@dataclass(frozen=True)
class PartyInviteObservation:
    blocked_byte_56228d:object=None
    party_state_eax:object=None
    use_owned_filter:bool=False
    filter_eax:object=None
    helper_returns:object=field(default_factory=dict)
    reply_execution:object=None
    def __post_init__(self):
        for v in (self.party_state_eax,self.filter_eax):
            if v is not None and (type(v) is not int or not 0<=v<1<<32):raise ValueError('Raw invitation helper EAX required')
        if self.blocked_byte_56228d is not None and (type(self.blocked_byte_56228d) is not int or not 0<=self.blocked_byte_56228d<256):raise ValueError('Observed invitation blocker BYTE required')
        if type(self.use_owned_filter) is not bool:raise ValueError('Explicit owned-filter selection required')
        if any(type(v) is not bool for v in self.helper_returns.values()):raise ValueError('Separate invitation helper returns required')
        object.__setattr__(self,'helper_returns',MappingProxyType(dict(self.helper_returns)))
        if self.reply_execution is not None and not isinstance(self.reply_execution,PartyReplyPlan):raise ValueError('Typed party reply execution required')

@dataclass(frozen=True)
class PartyInvitePlan:
    complete:bool
    status:str
    handler_return_dword:object=None
    inviter_word:object=None
    name_bytes:object=None
    matched:object=None
    action:object=None
    calls:tuple=()
    missing:str=''
    native_execution_verified:bool=False
    reply_execution:object=None

def plan_party_invitation(c,captured,o):
    if not isinstance(c,PartyInviteConfiguration) or type(captured) is not bytes or not isinstance(o,PartyInviteObservation):raise ValueError('Typed invitation config/observation and captured bytes required')
    calls=[];inviter=None;name=None;matched=None;action=None
    class Missing(Exception):pass
    def need(v,label):
        if v is None:raise Missing(label)
        return v
    def normal(label):
        calls.append(('normal_return',label))
        if o.helper_returns.get(label) is not True:raise Missing(label+' normal return')
    def result(ok,status,returned=None,missing=''):
        return PartyInvitePlan(ok,status,returned,inviter,name,matched,action,tuple(calls),missing,reply_execution=o.reply_execution)
    def reply(kind,address):
        calls.append((address,0x561ef8))
        p=o.reply_execution
        if p is not None:
            if p.action!=kind:raise ValueError('Bound party reply action differs from reached decision')
            if not p.complete:raise Missing('bound party reply: '+p.missing)
        normal(kind)
    def finish(status,returned,cleanup=False):
        if cleanup:normal('name_cleanup')
        return result(True,status,returned)
    try:
        if not captured:raise Missing('captured opcode byte')
        if captured[0]!=0x2f:return result(True,'other_opcode')
        if len(captured)<2:raise Missing('captured party subtype byte')
        if captured[1]!=2:return finish('other_party_subtype',1)
        if need(o.blocked_byte_56228d,'0056228d BYTE')!=0:return finish('blocked',1)
        calls.append(('guarded_party_state',0x553e80,0x55419c));normal('party_state')
        if need(o.party_state_eax,'party-state EAX')&255==1:return finish('party_state_one',1)
        if c.enabled_byte==0:return finish('auto_accept_disabled',1)
        calls.append(('004cb3bd',2));normal('read_inviter')
        if len(captured)<4:raise Missing('bounded inviter WORD bytes')
        inviter=int.from_bytes(captured[2:4],'little')
        calls.append(('004cb3bd',4));normal('read_name_length')
        if len(captured)<6:raise Missing('bounded name length WORD bytes')
        length=int.from_bytes(captured[4:6],'little')
        calls.append(('004cb415',6,length));normal('read_name')
        if len(captured)<6+length:raise Missing('bounded name bytes')
        # The helper copies length bytes, adds a terminator, then constructs
        # std::string from char*. A captured embedded NUL truncates that value.
        name=captured[6:6+length].split(b'\0',1)[0]
        calls.append(('004cbecc',name));normal('name_filter')
        if o.use_owned_filter:
            if o.filter_eax is not None:raise ValueError('Owned filter conflicts with raw AL')
            names=need(c.names,'owned stable name vector')
            matched=name in names
        else:matched=bool(need(o.filter_eax,'name-filter EAX')&255)
        # The source evaluates the filter even in accept-all mode.
        if c.list_only_byte==0 or matched:
            action='accept';reply(action,'004ca770')
            return finish('accept_span_returned',0 if c.party_bug_byte else 1,True)
        if c.reject_unlisted_byte:
            action='reject';reply(action,'004ca7b4')
            return finish('reject_span_returned',0,True)
        return finish('unlisted_unchanged',1,True)
    except Missing as e:return result(False,'needs_observation',missing=str(e))
