"""Bounded TP settings and packet27 control replay; calls/stores are inert."""
from dataclasses import dataclass,field,replace
from types import MappingProxyType

ROOT='frmMain/MainTab/SheetKoruma/GroupBox1/'
TP_INPUTS=tuple(ROOT+n for n in ('chtpkontrol','rdtpkontrolstop','rdtpkontroldc'))

def compile_tp_settings(values):
    v=tuple(values.get(k) for k in TP_INPUTS)
    if any(type(x) is not bool for x in v):raise ValueError('Three TP checkbox/radio values required')
    # Source reads the stop radio only. The else path writes2 even if both
    # radios are false; there is no extra read of the DC radio in this span.
    return MappingProxyType({0xb0:int(v[0]),0xb4:1 if v[1] else 2})

@dataclass(frozen=True)
class TPObservation:
    entry_reached:bool=False
    values:object=field(default_factory=dict)
    normal_returns:object=field(default_factory=dict)
    def __post_init__(self):
        if type(self.entry_reached) is not bool:raise ValueError('Explicit bounded entry required')
        values=dict(self.values);normals=dict(self.normal_returns)
        for k,v in values.items():
            if type(v) is not int or not 0<=v<(256 if k.endswith('_byte') else 1<<32):raise ValueError('Raw TP BYTE/DWORD required')
        if any(type(v) is not bool for v in normals.values()):raise ValueError('Separate normal return receipts required')
        object.__setattr__(self,'values',MappingProxyType(values));object.__setattr__(self,'normal_returns',MappingProxyType(normals))

@dataclass(frozen=True)
class TPPlan:
    complete:bool
    kind:str
    reads:tuple=()
    calls:tuple=()
    stores:tuple=()
    next_address:object=None
    planned_eax:object=None
    missing:str=''
    needed:object=None
    whole_handler_verified:bool=False
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class _Wait(Exception):
    def __init__(self,kind,label):self.needed=(kind,label);super().__init__(label+' '+kind)

def plan_tp(kind,o,*,packet=b'',context=0x5690f8):
    if kind not in ('settings','event') or not isinstance(o,TPObservation):raise ValueError('Typed known TP model required')
    if type(context) is not int or not 0<=context<=0xffffffff or type(packet) is not bytes:raise ValueError('Raw context and owned packet bytes required')
    reads=[];calls=[];stores=[];next_address=None;eax=None
    def result(error=None):return TPPlan(error is None,kind,tuple(reads),tuple(calls),tuple(stores),next_address,eax,
        '' if error is None else str(error),None if error is None else error.needed)
    def value(label):
        if label not in o.values:raise _Wait('value',label)
        return o.values[label]
    def read(label,address,width=4):reads.append((address,width,label));return value(label)
    def normal(label,helper,args=()):
        calls.append((helper,args,label))
        if o.normal_returns.get(label) is not True:raise _Wait('normal',label)
    def byte(index):
        if index>=len(packet):raise _Wait('unsupported','packet_byte%d_outside_owned_span'%index)
        return packet[index]
    try:
        if not o.entry_reached:raise _Wait('entry','0046c0e1' if kind=='settings' else '004d88e4')
        if kind=='settings':
            normal('enabled_getter','VCL_Checked_getter_span',('form_field',0xb0c))
            stores.append(((context+0xb0)&0xffffffff,1,value('enabled_eax')&255))
            normal('stop_getter','VCL_Checked_getter_span',('form_field',0xb10))
            stores.append(((context+0xb4)&0xffffffff,4,1 if value('stop_eax')&255 else 2))
            next_address=0x46c134;return result()
        if byte(0)!=0x27:next_address=0x4d8a98;return result()
        area=byte(2)
        if area:
            normal('first_area','0046209c');first=value('first_area_eax')
            if first!=area and read('area_change_stop_byte',0x562251,1):
                normal('area_change_stop','0040ae0c',(0,0x561f34))
        normal('tick','GetTickCount');tick=value('tick_eax')
        low=read('start_low',0x561f74);high=read('start_high',0x561f78)
        delta=(tick-((high<<32)|low))&((1<<64)-1)
        if delta>=1<<63:delta-=1<<64
        if delta>=10000:
            normal('second_area','0046209c')
            if value('second_area_eax')==area:
                normal('notice_block','004d896c..004d89d1 opaque ANSI notice span')
                stores.append((0x56209c,1,1))
                if read('tp_enabled_byte',0x5691a8,1):
                    if read('action_first',0x5691ac)==1:
                        normal('tp_stop','0040ae0c',(0,0x561f34))
                    # A separate source load after the stop call; not elif.
                    if read('action_second',0x5691ac)==2:
                        normal('tp_disconnect','004c7e0c',(0x561ef8,))
        if byte(1)==3:
            normal('third_area','0046209c')
            if value('third_area_eax')!=area:
                stores.extend(((0x561f6e,1,1),(0x561f70,1,1)))
            if area==0x5c and read('jail_enabled_byte',0x5691b0,1):
                if read('jail_list_only_byte',0x5691b2,1):normal('jail_list','0046dc5c',(0x5690f8,))
                else:normal('jail_all','0046d66c',(0x5690f8,))
        if byte(1)==2:stores.append((0x561f70,1,0))
        next_address=0x4d8a84;eax=1
        return result()
    except _Wait as error:return result(error)

class TPFrame:
    def __init__(self,kind,*,packet=b'',context=0x5690f8):
        self.kind=kind;self.packet=packet;self.context=context;self.observation=TPObservation();self.final=None
        plan_tp(kind,self.observation,packet=packet,context=context)
    def advance(self,incoming):
        if not isinstance(incoming,TPObservation):raise ValueError('Typed TP observation required')
        if self.final is not None:return self.final
        for _ in range(48):
            p=plan_tp(self.kind,self.observation,packet=self.packet,context=self.context)
            if p.complete:self.final=p;return p
            kind,label=p.needed
            if kind=='unsupported':return p
            if kind=='entry':
                if not incoming.entry_reached:return p
                self.observation=replace(self.observation,entry_reached=True)
            elif kind=='normal':
                if incoming.normal_returns.get(label) is not True:return p
                self.observation=replace(self.observation,normal_returns={**self.observation.normal_returns,label:True})
            elif kind=='value':
                if label not in incoming.values:return p
                self.observation=replace(self.observation,values={**self.observation.values,label:incoming.values[label]})
            else:return p
        raise AssertionError('TP source observation budget exceeded')
