"""Fifty own panel fields -> source settings body -> persistent shadow fields."""
import hashlib,json,re
from pathlib import Path
from dataclasses import replace
from collections.abc import Mapping
from protection_settings import (OPS,label,ProtectionSettingsObservation,ProtectionSettingsFrame)
from source_integer import SourceIntegerObservation
from name_codec import WindowsNameCodec

_data=json.loads(Path(__file__).with_name('protection_fields.json').read_text(encoding='utf-8'))
PROTECTION_FIELDS=tuple((f['slot'],f['path']) for f in _data['fields'])
PROTECTION_INPUTS=tuple(path for slot,path in PROTECTION_FIELDS)
KINDS={}
for _op in OPS:
    for _slot in ([s for s,_ in _op[1]] if _op[0]=='enum' else [_op[1]]):
        KINDS[_slot]=_op[0] if _op[0] in ('number','string') else 'checked'
assert len(PROTECTION_FIELDS)==len(KINDS)==50 and {s for s,p in PROTECTION_FIELDS}==set(KINDS)

def protection_snapshot(values,route_sample):
    if type(route_sample) is not tuple or len(route_sample)!=2 or not isinstance(route_sample[0],Mapping):
        raise ValueError('Own route combo Text and explicit codepage reader required')
    texts,codepage=route_sample
    if type(codepage) is not int or not 1<=codepage<=65535:raise ValueError('Explicit route example codepage required')
    fields=[]
    for slot,path in PROTECTION_FIELDS:
        kind=KINDS[slot];v=texts.get(path) if kind=='string' else values.get(path)
        if kind=='checked' and type(v) is not bool:raise ValueError('Protection checkbox/radio value required: '+path)
        if kind in ('number','string') and type(v) is not str:raise ValueError('Protection panel Text required: '+path)
        fields.append((slot,kind,v))
    return (tuple(fields),codepage)

def protection_snapshot_digest(snapshot):
    return hashlib.sha256(json.dumps(snapshot,ensure_ascii=True,separators=(',',':')).encode('ascii')).hexdigest()

def object_field(data,key):
    value=data.get(key,{})
    if type(value) is not dict:raise ValueError('Protection '+key+' must be an object')
    return value

def advance_protection_sample(frame,snapshot,data):
    own={label(slot):value for slot,kind,value in snapshot[0]};o=ProtectionSettingsObservation();seen=set()
    for _ in range(512):
        p=frame.advance(o)
        if p.complete:return p
        kind,key=p.needed;marker=(kind,key)
        if kind=='child':
            child=dict(p.children)[key];field=child.needed;marker=(kind,key,field)
            if marker in seen:return p
            seen.add(marker)
            children=object_field(data,'integer_children')
            if key not in children:return p
            capture=children[key]
            if type(capture) is not dict:raise ValueError('Numeric child must be an object')
            if field not in capture:return p
            previous=o.integer_children.get(key,SourceIntegerObservation())
            child_input=replace(previous,**{field:capture[field]})
            o=replace(o,integer_children={**o.integer_children,key:child_input});continue
        if marker in seen:return p
        seen.add(marker)
        if kind=='entry':
            value=data.get('entry_reached',False)
            if type(value) is not bool:raise ValueError('Explicit common producer entry required')
            if not value:return p
            o=replace(o,entry_reached=True)
        elif kind=='normal':
            values=object_field(data,'normal_returns')
            if key in values and type(values[key]) is not bool:raise ValueError('Helper normal receipt must be boolean')
            if values.get(key) is not True:return p
            o=replace(o,normal_returns={**o.normal_returns,key:True})
        elif kind=='values':
            if key.startswith('checked_'):value=int(own[key[len('checked_'):]])
            elif key.startswith('index_'):value=own[key[len('index_'):]]&0xffffffff
            else:return p
            fields=object_field(data,'values')
            if key in fields and (type(fields[key]) is not int or fields[key]!=value):
                raise ValueError('Panel-derived protection getter cannot be overridden')
            o=replace(o,values={**o.values,key:value})
        elif kind=='texts':
            value=own[key];fields=object_field(data,'texts')
            if key in fields and fields[key]!=value:raise ValueError('Source text must match own panel Text')
            o=replace(o,texts={**o.texts,key:value})
        elif kind=='ansi_bytes':
            fields=object_field(data,'ansi_hex')
            if key not in fields:return p
            if type(fields[key]) is not str:raise ValueError('Captured ANSI HEX string required')
            try:value=bytes.fromhex(fields[key])
            except ValueError as error:raise ValueError('Invalid captured ANSI HEX') from error
            o=replace(o,ansi_bytes={**o.ansi_bytes,key:value})
        else:return p
    raise AssertionError('Protection panel reached-field budget exceeded')

class ProtectionSettingsTrial:
    _frame_type=ProtectionSettingsFrame
    _snapshotter=staticmethod(protection_snapshot)
    _snapshot_error='Panel veya rota Text değişti; Koruma örneğini yeniden doldurun'
    def __init__(self,reader,route_reader):self.reader=reader;self.route_reader=route_reader;self.reset()
    def reset(self):
        self.snapshot=None;self.frame=None;self.last=None
        self.scalar_state={};self.string_state={};self.applied_stores=0;self.applied_strings=0
    def current_snapshot(self):
        if self.reader is None or self.route_reader is None:raise ValueError('Protection panel/route Text readers required')
        values,_=self.reader();return self._snapshotter(values,self.route_reader())
    def step(self,text):
        self.last=None;snapshot=self.current_snapshot()
        if snapshot!=self.snapshot:
            self.snapshot=snapshot;self.frame=self._frame_type();self.applied_stores=0;self.applied_strings=0
        try:data=json.loads(text)
        except (TypeError,ValueError) as error:raise ValueError('Protection observations must be a JSON object') from error
        if type(data) is not dict:raise ValueError('Protection observations must be a JSON object')
        if 'panel_snapshot_sha256' in data and data['panel_snapshot_sha256']!=protection_snapshot_digest(snapshot):
            raise ValueError(self._snapshot_error)
        try:p=advance_protection_sample(self.frame,snapshot,data)
        except ValueError:
            # Invalid later capture data does not retract the earlier accepted
            # source prefix already held by the frame. No new receipts supplied.
            self._apply_prefix(self.frame.advance(ProtectionSettingsObservation()))
            raise
        self._apply_prefix(p)
        self.last=p;return p
    def _apply_prefix(self,p):
        if len(p.stores)<self.applied_stores or len(p.string_assignments)<self.applied_strings:
            raise AssertionError('Consumed protection prefix retracted')
        for address,width,value in p.stores[self.applied_stores:]:self.scalar_state[address]=(width,value)
        for address,value in p.string_assignments[self.applied_strings:]:self.string_state[address]=value
        self.applied_stores=len(p.stores);self.applied_strings=len(p.string_assignments)

def example_protection_sample(snapshot,codec_factory=WindowsNameCodec,*,_ops=OPS,_prologue=True):
    own={label(slot):value for slot,kind,value in snapshot[0]};normals={'prologue':True} if _prologue else {};children={};ansi={};used_defaults={}
    codec=None
    for op in _ops:
        kind,slot,_=op[:3]
        if kind=='constant':continue
        if kind=='index':normals['index_'+label(slot)]=True
        elif kind in ('flag','enum','choice_else'):
            for member in ([s for s,_ in slot] if kind=='enum' else [slot]):normals['checked_'+label(member)]=True
        else:
            key=label(slot)
            for stage in ('init_','text_','text_cleanup_'):normals[stage+key]=True
            if kind in ('number','number64'):
                text=own[key].strip()
                if not re.fullmatch(r'[+-]?[0-9]+',text):raise ValueError('Sentetik sayı örneği yalnız signed decimal64 alt kümesini destekler')
                value=int(text)
                if not -(1<<63)<=value<1<<63:raise ValueError('Sentetik sayı örneği signed64 aralığı dışında')
                normals['parser_outer_'+key]=True
                children[key]=dict(text_copy_returned=True,route='normal',parser_returned=True,
                                  parser_qword=value&((1<<64)-1),cleanup_returned=True)
            else:
                if codec is None:codec=codec_factory(snapshot[1])
                data,used_default=codec.encode(own[key]);ansi[key]=data.hex();used_defaults[key]=used_default
                for stage in ('ansi_','assign_','ansi_cleanup_'):normals[stage+key]=True
    return json.dumps(dict(panel_snapshot_sha256=protection_snapshot_digest(snapshot),synthetic_example=True,
        example_policy='own signed-decimal64 subset and explicit local Windows codepage; source RTL unverified',
        entry_reached=True,normal_returns=normals,integer_children=children,ansi_hex=ansi,
        local_conversion_used_default=used_defaults),ensure_ascii=False)

def describe_protection_trial(trial):
    p=trial.last
    if p is None:return 'Geçerli ortak Koruma sonucu yok'
    selections={name:trial.scalar_state.get(0x5690f8+offset,(None,'önceki değer bilinmiyor'))[1]
                for name,offset in (('AntiCR',0x10),('Karşı ırk',0x34),('Bildirim',0x44),('PM',0x84),('TP',0xb4))}
    return {'ayar_gövdesi_tamam':p.complete,'eksik':p.missing,'yeni_scalar_store':len(p.stores),
        'bilinen_yerel_scalar_alan':len(trial.scalar_state),'bilinen_yerel_rota':len(trial.string_state),
        'yerel_işlem_seçimleri':selections,
        'yazılmadan_korunan_enumlar':['%x'%x for x in p.unchanged_enum_offsets],
        'Yerel alan denemesi':True,'Oyunda ayar uygulaması doğrulandı':False}
