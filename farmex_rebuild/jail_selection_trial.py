"""Actual own DCWindow rows -> captured checked-list producer observations."""
import hashlib,json
from jail_selection import JailSelectionFrame,JailSelectionObservation
from jail_protection import JailObservation
from name_codec import WindowsNameCodec
JAIL_LIST_PATH='frmDCWindow/GroupBox1/bancloselist'

def selection_snapshot(lists,codepage):
    if type(codepage) is not int or not 1<=codepage<=65535:raise ValueError('Explicit Windows codepage required')
    rows=lists.get(JAIL_LIST_PATH)
    if type(rows) is not list:raise ValueError('DC–Hapis list source required')
    out=[]
    for row in rows:
        if type(row) is not dict or type(row.get('caption')) is not str or type(row.get('checked')) is not bool:
            raise ValueError('Actual caption/checkbox values required')
        out.append((row['caption'],row['checked']))
    return tuple(out),codepage

def selection_digest(snapshot):
    return hashlib.sha256(json.dumps(snapshot,ensure_ascii=True,separators=(',',':')).encode()).hexdigest()

def advance_selection_sample(frame,snapshot,data):
    def obj(key):
        value=data.get(key,{})
        if type(value) is not dict:raise ValueError(key+' must be an object')
        return value
    while True:
        p=frame.advance(JailSelectionObservation())
        if p.complete:return p
        kind,label=p.needed
        if kind=='entry':
            value=data.get('entry_reached',False)
            if type(value) is not bool:raise ValueError('Explicit entry boolean required')
            if not value:return p
            incoming=JailSelectionObservation(JailObservation(True))
        elif kind=='normal':
            value=obj('normal_returns').get(label,False)
            if type(value) is not bool:raise ValueError('Explicit normal-return boolean required')
            if not value:return p
            incoming=JailSelectionObservation(JailObservation(normal_returns={label:True}))
        elif kind=='reset':
            if 'after_reset_hex' not in data:return p
            raw=data['after_reset_hex']
            if type(raw) is not list or any(type(v) is not str for v in raw):raise ValueError('Captured reset HEX rows required')
            incoming=JailSelectionObservation(after_reset=tuple(bytes.fromhex(v) for v in raw))
        elif kind=='bytes':
            captures=obj('ansi_hex')
            if label not in captures:return p
            if type(captures[label]) is not str:raise ValueError('Captured title HEX required')
            incoming=JailSelectionObservation(ansi_bytes={label:bytes.fromhex(captures[label])})
        elif kind=='value':
            index=int(label.split('.',1)[0][3:]);suffix=label.split('.',1)[1]
            if suffix=='count_eax':value=len(snapshot[0])
            elif suffix=='checked_eax':
                if index>=len(snapshot[0]):raise ValueError('Checked getter outside bound rows')
                value=int(snapshot[0][index][1])
            else:
                values=obj('values')
                if label not in values:return p
                value=values[label]
            if label in obj('values') and (type(obj('values')[label]) is not int or obj('values')[label]!=value):
                raise ValueError('Captured scalar contradicts actual panel rows')
            incoming=JailSelectionObservation(JailObservation(values={label:value}))
        else:return p
        frame.advance(incoming)

class JailSelectionTrial:
    def __init__(self,reader,route_reader):self.reader=reader;self.route_reader=route_reader;self.reset()
    def reset(self):self.snapshot=None;self.frame=None;self.last=None;self.saved_rows=()
    def current_snapshot(self):
        if self.reader is None or self.route_reader is None:raise ValueError('Panel/codepage readers required')
        return selection_snapshot(self.reader()[1],int(self.route_reader()[1]))
    def step(self,text):
        self.last=None;snapshot=self.current_snapshot()
        if snapshot!=self.snapshot:
            self.snapshot=snapshot;self.frame=JailSelectionFrame(initial_rows=self.saved_rows)
        data=json.loads(text)
        if type(data) is not dict:raise ValueError('Selection observations must be an object')
        if 'panel_snapshot_sha256' in data and data['panel_snapshot_sha256']!=selection_digest(snapshot):
            raise ValueError('DC–Hapis listesi veya kod sayfası değişti; örneği yeniden doldurun')
        try:p=advance_selection_sample(self.frame,snapshot,data)
        except ValueError:
            self.saved_rows=self.frame.advance(JailSelectionObservation()).rows
            raise
        self.saved_rows=p.rows;self.last=p;return p

def example_selection_sample(snapshot):
    rows,cp=snapshot;codec=WindowsNameCodec(cp);normals={k:True for k in
        ('prologue','scratch_init','reset_end','reset_begin','reset_erase','final_cleanup','epilogue')}
    values={};ansi={};defaults={};selected=0
    for i,(caption,checked) in enumerate(rows):
        p='row%d.'%i
        for name in ('count','item','checked'):normals[p+name]=True
        if checked:
            for name in ('text_prepare','text_get','ansi_convert','scratch_assign','ansi_cleanup','unicode_cleanup','size','capacity','insert'):
                normals[p+name]=True
            b,default=codec.encode(caption);ansi[p+'title']=b.hex();defaults[p+'title']=default
            values.update({p+'size_eax':selected,p+'capacity_eax':max(8,len(rows)),
                           p+'end_pointer':0x2000+selected*4,p+'insert_eax':0x2004+selected*4})
            selected+=1
    normals['row%d.count'%len(rows)]=True
    return json.dumps(dict(panel_snapshot_sha256=selection_digest(snapshot),synthetic_example=True,
       example_policy='Own stable UI rows, empty reset and explicit local Windows conversion; source RTL unverified',
       entry_reached=True,normal_returns=normals,after_reset_hex=[],values=values,ansi_hex=ansi,
       local_conversion_used_default=defaults),ensure_ascii=False)

def describe_selection_trial(trial):
    p=trial.last
    return {'kaydetme_modeli_tamam':False if p is None else p.complete,
            'eksik':None if p is None else p.needed,'yerel_kayıtlı_başlık':len(trial.saved_rows),
            'başlık_HEX':[v.hex() for v in trial.saved_rows],
            'Oyunda ayar uygulaması doğrulandı':False}
