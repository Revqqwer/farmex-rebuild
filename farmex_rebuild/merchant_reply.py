"""Offline 4d82a4 opcode68 dispatcher slice. No capture, hooks, IO or ACK.

AL0/1 describes local dispatcher consumption/forwarding, not server acceptance.
Bounded truncation handling is our policy; the source raw reads lack these guards.
"""
from dataclasses import dataclass,replace

@dataclass(frozen=True)
class MerchantReplyState:
    close_pending_byte:int=0
    item_pending_byte:int=0
    session_ready_byte:int=0
    opening_pending_byte:int=0
    setup_stamp_qword:int=0
    established_stamp_qword:int=0
    scan_pending_byte:int=0
    def __post_init__(self):
        for name,value in vars(self).items():
            bits=64 if name.endswith('qword') else 8
            if type(value) is not int or not 0<=value<1<<bits:raise ValueError('Raw %dbit field required: '%bits+name)

@dataclass(frozen=True)
class MerchantReplyObservation:
    scan_active_byte:object=None
    local_actor_dword:object=None
    tick_dword:object=None
    scan_parse_returned:object=None
    scan_finish_returned:object=None
    def __post_init__(self):
        for value,bits in ((self.scan_active_byte,8),(self.local_actor_dword,32),(self.tick_dword,32)):
            if value is not None and (type(value) is not int or not 0<=value<1<<bits):raise ValueError('Raw reply observation required')
        for value in (self.scan_parse_returned,self.scan_finish_returned):
            if value is not None and type(value) is not bool:raise ValueError('Normal-return observation required')

@dataclass(frozen=True)
class MerchantReplyPlan:
    status:str
    complete:bool
    state:MerchantReplyState
    prospective_state:MerchantReplyState
    return_al:object=None
    reads:tuple=()
    calls:tuple=()
    writes:tuple=()
    missing:str=''
    independently_verified:bool=False

def plan_merchant_reply(state,payload,observation):
    if not isinstance(state,MerchantReplyState) or type(payload) is not bytes or not isinstance(observation,MerchantReplyObservation):
        raise ValueError('Typed reply state, immutable supplied bytes and observations required')
    o=observation;candidate=state;reads=[];calls=[];writes=[]
    class Missing(Exception):pass
    class Truncated(Exception):pass
    def need(value,label):
        if value is None:raise Missing(label)
        return value
    def read(at,width):
        reads.append((at,width))
        if at+width>len(payload):raise Truncated('supplied bytes[%d:%d]'%(at,at+width))
        return int.from_bytes(payload[at:at+width],'little')
    def write(name,value,offset):
        nonlocal candidate
        candidate=replace(candidate,**{name:value});writes.append((name,offset,value))
    def clock():
        calls.append(('GetTickCount',));return need(o.tick_dword,'reply GetTickCount')
    def matching_actor(offset):
        actor=read(offset,4);calls.append(('00462650',))
        return actor==need(o.local_actor_dword,'fresh local actor EAX')
    def output(status,complete,al=None,missing=''):
        return MerchantReplyPlan(status,complete,candidate if complete else state,candidate,al,
                                 tuple(reads),tuple(calls),tuple(writes),missing)
    try:
        if read(0,1)!=0x68:return output('not_applicable',True)
        subtype=read(1,1);active=need(o.scan_active_byte,'scan active BYTE69968')
        if active:
            if subtype in (0x27,0x02,0x11):
                write('scan_pending_byte',0,'scan+0x0f');return output('scan_consumed',True,0)
            if subtype in (0x05,0x23):
                mode=1 if subtype==5 else 2
                if read(2,1)==1:
                    calls.append(('004bc650','scan_object','payload','payload_length'))
                    if o.scan_parse_returned is not True:raise Missing('004bc650 normal return')
                calls.append(('004bf57c',mode))
                if o.scan_finish_returned is not True:raise Missing('004bf57c normal return')
                write('scan_pending_byte',0,'scan+0x0f');return output('scan_consumed',True,0)
        if subtype in (0x27,0x02):
            if matching_actor(2):
                write('setup_stamp_qword',clock(),8)
                write('close_pending_byte',0,0x18)
        if subtype==1:
            if read(2,1)==1:write('session_ready_byte',1,0x38)
        elif subtype==3:write('item_pending_byte',0,0x28)
        elif subtype in (7,0x28):
            if matching_actor(6 if subtype==7 else 2):
                write('opening_pending_byte',0,0x48)
                write('established_stamp_qword',clock(),0x10)
        return output('merchant_forwarded',True,1)
    except Truncated as error:return output('truncated',False,missing=str(error))
    except Missing as error:return output('needs_observation',False,missing=str(error))

def sell_setup_delay_from_reply(state,extra_wait_dword,tick_dword=None,
                               waiting_span_returned=None,ready_span_returns=()):
    """Own reply state +8 projection; fresh tick and opaque returns stay explicit."""
    from merchant_sell_setup_delay import SellSetupDelayObservation
    if not isinstance(state,MerchantReplyState):raise ValueError('Typed reply state required')
    return SellSetupDelayObservation(extra_wait_dword,state.setup_stamp_qword,tick_dword,
                                    waiting_span_returned,ready_span_returns)

def merchant_snapshot_from_reply(state,now_ms,**extra):
    """Bind supplied reply state; optional raw SELL setup clock has its own domain.

    This does not authenticate supplied packets or emulate native DWORD rollover.
    """
    from operation_engine import MerchantSnapshot
    if not isinstance(state,MerchantReplyState):raise ValueError('Typed reply state required')
    fields=dict(close_pending=bool(state.close_pending_byte),item_pending=bool(state.item_pending_byte),
        sale_session_ready=bool(state.session_ready_byte),opening_pending=bool(state.opening_pending_byte),
        setup_started_ms=state.setup_stamp_qword,established_ms=state.established_stamp_qword)
    if fields.keys()&extra.keys():raise ValueError('Raw producer flags/timestamps conflict with reply state')
    delay=extra.get('sell_setup_delay_inputs')
    if delay is not None:
        from merchant_sell_setup_delay import SellSetupDelayObservation
        if not isinstance(delay,SellSetupDelayObservation):raise ValueError('Typed SELL setup delay required')
        if delay.started_stamp_qword is not None and delay.started_stamp_qword!=state.setup_stamp_qword:
            raise ValueError('SELL setup-delay stamp conflicts with reply state')
        # A raw source stamp can exceed the unrelated outer monotonic epoch.
        # Do not project it into the legacy timestamp/future-time validator.
        fields['setup_started_ms']=None
    return MerchantSnapshot(now_ms,**fields,**extra)
