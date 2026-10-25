"""Own TP panel snapshot -> bounded settings -> stable packet dispatcher."""
import hashlib,json
from dataclasses import dataclass,replace
from teleport_protection import TP_INPUTS,TPObservation,TPFrame,compile_tp_settings
from incoming_tp_dispatch import IncomingTPDispatchFrame

def tp_snapshot(values):
    compile_tp_settings(values)
    return tuple(values[k] for k in TP_INPUTS)

def snapshot_digest(snapshot):return hashlib.sha256(json.dumps(snapshot,separators=(',',':')).encode('ascii')).hexdigest()
def packet_digest(packet):return hashlib.sha256(packet).hexdigest()
def object_field(data,key):
    value=data.get(key,{})
    if type(value) is not dict:raise ValueError('TP '+key+' must be an object')
    return value

def settings_sample(frame,snapshot,data):
    capture=object_field(data,'settings');o=TPObservation()
    derived={'enabled_eax':int(snapshot[0]),'stop_eax':int(snapshot[1])}
    for _ in range(10):
        p=frame.advance(o)
        if p.complete:return p
        kind,label=p.needed
        if kind=='entry':
            entry=capture.get('entry_reached',False)
            if type(entry) is not bool:raise ValueError('Explicit TP settings entry required')
            if not entry:return p
            o=replace(o,entry_reached=True)
        elif kind=='normal':
            fields=object_field(capture,'normal_returns')
            if label in fields and type(fields[label]) is not bool:raise ValueError('Normal receipt must be boolean')
            if fields.get(label) is not True:return p
            o=replace(o,normal_returns={**o.normal_returns,label:True})
        else:
            value=derived[label];fields=object_field(capture,'values')
            if label in fields and (type(fields[label]) is not int or fields[label]!=value):
                raise ValueError('TP panel-derived getter cannot be overridden')
            o=replace(o,values={**o.values,label:value})
    raise AssertionError('TP settings source budget exceeded')

def dispatch_sample(frame,configuration,data):
    o=TPObservation();setup=data.get('dispatcher_setup_returned');seen=set()
    if setup is not None and type(setup) is not bool:raise ValueError('Dispatcher normal receipt must be boolean')
    derived={'tp_enabled_byte':configuration[0xb0],'action_first':configuration[0xb4],'action_second':configuration[0xb4]}
    for _ in range(64):
        p=frame.advance(o,dispatcher_setup_returned=setup)
        if p.complete or p.status!='needs_tp_observation':return p
        kind,label=p.child.needed
        if (kind,label) in seen:return p
        seen.add((kind,label))
        if kind=='normal':
            fields=object_field(data,'normal_returns')
            if label in fields and type(fields[label]) is not bool:raise ValueError('Normal receipt must be boolean')
            if fields.get(label) is not True:return p
            o=replace(o,normal_returns={**o.normal_returns,label:True})
        elif kind=='value':
            fields=object_field(data,'values')
            if label in derived:
                value=derived[label]
                if label in fields and (type(fields[label]) is not int or fields[label]!=value):
                    raise ValueError('Stable own TP configuration cannot be overridden')
            else:
                if label not in fields:return p
                value=fields[label]
            o=replace(o,values={**o.values,label:value})
        else:return p
    raise AssertionError('TP dispatch source budget exceeded')

@dataclass(frozen=True)
class TPTrialPlan:
    settings:object
    dispatch:object=None
    stable_configuration_fixture:bool=True
    native_execution_verified:bool=False
    live_compatibility_verified:bool=False

class TPProtectionTrial:
    def __init__(self,reader):self.reader=reader;self.reset()
    def reset(self):self.snapshot=None;self.settings=None;self.packet=None;self.dispatch=None;self.last=None
    def step(self,packet_hex,text):
        self.last=None
        if self.reader is None:raise ValueError('TP panel reader required')
        values,_=self.reader();snapshot=tp_snapshot(values)
        try:packet=bytes.fromhex(packet_hex);data=json.loads(text)
        except (TypeError,ValueError) as error:raise ValueError('TP packet HEX and JSON object required') from error
        if type(data) is not dict:raise ValueError('TP observation JSON must be an object')
        if snapshot!=self.snapshot:
            self.snapshot=snapshot;self.settings=TPFrame('settings');self.dispatch=None
        if packet!=self.packet:
            self.packet=packet;self.dispatch=None
        if 'panel_snapshot_sha256' in data and data['panel_snapshot_sha256']!=snapshot_digest(snapshot):
            raise ValueError('Panel değişti; TP örneğini yeniden doldurun')
        if 'packet_sha256' in data and data['packet_sha256']!=packet_digest(packet):
            raise ValueError('Paket değişti; TP örneğini yeniden doldurun')
        settings=settings_sample(self.settings,snapshot,data)
        if not settings.complete:
            self.last=TPTrialPlan(settings);return self.last
        if self.dispatch is None:self.dispatch=IncomingTPDispatchFrame(packet)
        result=dispatch_sample(self.dispatch,compile_tp_settings(dict(zip(TP_INPUTS,snapshot))),data)
        self.last=TPTrialPlan(settings,result);return self.last

def example_tp_sample(snapshot,packet):
    if type(packet) is not bytes:raise ValueError('Owned packet bytes required')
    area=packet[2] if len(packet)>=3 else 10
    return json.dumps(dict(panel_snapshot_sha256=snapshot_digest(snapshot),packet_sha256=packet_digest(packet),synthetic_example=True,
        settings=dict(entry_reached=True,normal_returns=dict(enabled_getter=True,stop_getter=True)),
        dispatcher_setup_returned=True,
        values=dict(first_area_eax=area,area_change_stop_byte=0,tick_eax=10000,start_low=0,start_high=0,
                    second_area_eax=area,third_area_eax=area,jail_enabled_byte=0,jail_list_only_byte=0),
        normal_returns={k:True for k in ('first_area','tick','second_area','notice_block','tp_stop','tp_disconnect','third_area','jail_all','jail_list')}),ensure_ascii=False)

def describe_tp_trial(trial):
    p=trial.last
    if p is None:return 'Geçerli TP sonucu yok'
    child=None if p.dispatch is None else p.dispatch.child
    return {'ayar_öneki_tamam':p.settings.complete,'ayar_eksiği':p.settings.missing,
        'olay_tamam':None if p.dispatch is None else p.dispatch.complete,
        'olay_eksiği':None if p.dispatch is None else p.dispatch.missing,
        'kaynak_dönüşü':None if p.dispatch is None else p.dispatch.source_return_dword,
        'planlanan_çağrılar':[] if child is None else [c[2] for c in child.calls],
        'planlanan_alan_yazımı':[] if child is None else list(child.stores),
        'Sabit ayar denemesi':True,'Oyunda işlem doğrulandı':False}
