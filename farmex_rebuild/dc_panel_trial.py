"""Actual own protection checkboxes -> explicit four-layer DC fixture trial."""
import hashlib,json
from jail_protection import JailObservation
from dc_sender_template import DCSenderObservation
from dc_full_chain import DCFullChainFrame,DCFullChainObservation

ROOT='frmMain/MainTab/SheetKoruma/GroupBox1/'
DC_PANEL_INPUTS=(ROOT+'chdckapat',ROOT+'chdchkapatlist')

def dc_panel_snapshot(values):
    snapshot=tuple(values.get(k) for k in DC_PANEL_INPUTS)
    if any(type(v) is not bool for v in snapshot):raise ValueError('Actual DC checkbox values required')
    return snapshot
def dc_panel_digest(snapshot):
    return hashlib.sha256(json.dumps(snapshot,separators=(',',':')).encode()).hexdigest()

def advance_dc_sample(frame,snapshot,data):
    def obj(value,name):
        if type(value) is not dict:raise ValueError(name+' must be an object')
        return value
    while True:
        p=frame.advance(DCFullChainObservation())
        if p.complete:return p
        scope,request=p.needed;sender=None
        if scope=='parent':section=obj(data.get('parent',{}),'parent');destination='parent'
        elif scope=='action' and request[0]=='consumer':
            section=obj(data.get('consumer',{}),'consumer');destination='consumer';request=request[1]
        elif scope=='action' and request[0]=='sender':
            sender=request[1];section=obj(obj(data.get('transfers',{}),'transfers').get(sender,{}),sender)
            destination='sender';request=request[2]
        else:return p
        kind,label=request
        if kind=='entry':
            value=section.get('entry_reached',False)
            if type(value) is not bool:raise ValueError('Explicit entry boolean required')
            if not value:return p
            incoming=JailObservation(True)
        elif kind=='normal':
            value=obj(section.get('normal_returns',{}),'normal_returns').get(label,False)
            if type(value) is not bool:raise ValueError('Explicit normal-return boolean required')
            if not value:return p
            incoming=JailObservation(normal_returns={label:True})
        elif kind=='value':
            values=obj(section.get('values',{}),'values')
            if destination=='parent' and label in ('enabled_byte','list_only_byte'):
                value=int(snapshot[0 if label=='enabled_byte' else 1])
                if label in values and (type(values[label]) is not int or values[label]!=value):
                    raise ValueError('DC scalar contradicts actual panel checkbox')
            else:
                if label not in values:return p
                value=values[label]
            incoming=JailObservation(values={label:value})
        else:return p
        if destination=='parent':o=DCFullChainObservation(parent=incoming)
        elif destination=='consumer':o=DCFullChainObservation(action=DCSenderObservation(consumer=incoming))
        else:o=DCFullChainObservation(action=DCSenderObservation(transfers={sender:incoming}))
        frame.advance(o)

class DCPanelTrial:
    def __init__(self,reader):self.reader=reader;self.reset()
    def reset(self):
        self.snapshot=None;self.frame=None;self.last=None;self.prefix=None;self.shadow_stores={};self.applied=0
    def current_snapshot(self):
        if self.reader is None:raise ValueError('Panel reader required')
        return dc_panel_snapshot(self.reader()[0])
    def _accept(self,p):
        self.prefix=p
        if len(p.parent.stores)<self.applied:raise AssertionError('DC timestamp prefix retracted')
        for address,width,value in p.parent.stores[self.applied:]:self.shadow_stores[address]=(width,value)
        self.applied=len(p.parent.stores)
    def step(self,text):
        self.last=None;snapshot=self.current_snapshot()
        if snapshot!=self.snapshot:
            self.snapshot=snapshot;self.frame=DCFullChainFrame();self.applied=0
            self.prefix=self.frame.advance(DCFullChainObservation())
        data=json.loads(text)
        if type(data) is not dict:raise ValueError('DC observations must be an object')
        if 'panel_snapshot_sha256' in data and data['panel_snapshot_sha256']!=dc_panel_digest(snapshot):
            raise ValueError('DC panel seçimi değişti; örneği yeniden doldurun')
        try:p=advance_dc_sample(self.frame,snapshot,data)
        except ValueError:
            self._accept(self.frame.advance(DCFullChainObservation()));raise
        self._accept(p);self.last=p;return p

def example_dc_sample(snapshot):
    return json.dumps(dict(panel_snapshot_sha256=dc_panel_digest(snapshot),synthetic_example=True,
      example_policy='Own stable checkboxes, captured context/ticks and empty list or failed snapshot; no live process data',
      parent=dict(entry_reached=True,values=dict(context_6e_byte=0,tick_eax=300000,stamp=0,post_tick_eax=300010),
                  normal_returns=dict(tick=True,consumer=True,post_tick=True)),
      consumer=dict(values=dict(payload_byte=1,snapshot_handle=0xffffffff,
                                **{'row0.count_initial_begin':0}),
                    normal_returns={k:True for k in ('prologue','scratch_init','initial_text','snapshot','final_cleanup','epilogue')}),
      transfers={}),ensure_ascii=False)

def describe_dc_trial(trial):
    p=trial.last
    return {'yerel_akış_tamam':False if p is None else p.complete,'eksik':None if p is None else p.needed,
            'planlanan_payload':0 if trial.prefix is None else len(trial.prefix.payload_intents),
            'planlanan_yazma':0 if trial.prefix is None else len(trial.prefix.write_intents),
            'yerel_zaman_damgası':trial.shadow_stores.get(0x553ce4),'Oyunda işlem doğrulandı':False}
