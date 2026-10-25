"""Owned Pet controls -> settings shadow -> captured worker invocation.

This adapter uses stable owned panel values, explicit observation tickets and
owned timer-store continuity. These are local UI policies, not native runtime
claims. It never executes planned helpers or sends a game action.
"""
import json
from pet_settings import PET_SETTING_FIELDS,PET_SETTING_INPUTS,OPS,PetSettingsFrame
from pet_engine import PetFrame,PetObservation,FOOD_IDS
from protection_panel_trial import (ProtectionSettingsTrial,protection_snapshot_digest,
                                    example_protection_sample,object_field)

CONTEXT=0x561f34
CONFIG_OFFSETS={'auto_initial':0x1a8,'auto_absent':0x1a8,'auto_present':0x1a8,
 'food_initial':0x1b0,'food_present':0x1b0,'mode_compare':0x1ac,'mode_send':0x1ac,
 'food_threshold':0x1b4}
TIMER_ADDRESSES={'mode_last':0x553c54,'food_last':0x553c58}

class PetSettingsTrial(ProtectionSettingsTrial):
    _frame_type=PetSettingsFrame
    _snapshot_error='Pet ayarları değişti; örneği yenileyin'
    def __init__(self,reader):super().__init__(reader,None)
    def current_snapshot(self):
        if self.reader is None:raise ValueError('Pet panel okuyucusu gerekli')
        values,_=self.reader();fields=[]
        for slot,path in PET_SETTING_FIELDS:
            value=values.get(path);kind='number' if slot==0xf1c else 'checked'
            if kind=='number' and type(value) is not str:raise ValueError('Pet besleme metni gerekli')
            if kind=='checked' and type(value) is not bool:raise ValueError('Pet seçim değeri gerekli: '+path)
            fields.append((slot,kind,value))
        return tuple(fields),None

def example_pet_settings_sample(snapshot):
    return example_protection_sample(snapshot,_ops=OPS,_prologue=False)

class PetTrial:
    def __init__(self,reader):self.settings=PetSettingsTrial(reader);self.reset()
    def reset(self):
        self.settings.reset();self.frame=None;self.last=None;self.active_token=None;self.last_token=0
        self.scalar_state={};self.applied_stores=0;self.config_shadow={};self.missing='Pet ayarları bekleniyor';self.document=None
    def sync_document(self):
        if self.settings.reader is None:raise ValueError('Pet panel okuyucusu gerekli')
        values,lists=self.settings.reader()
        if self.document is not None and self.document is not values:
            floor=self.last_token;self.reset();self.last_token=floor
        self.document=values
        return values,lists
    def _invalidate_worker(self):
        self.frame=None;self.active_token=None;self.applied_stores=0;self.config_shadow={}
    def _apply(self,p):
        if len(p.stores)<self.applied_stores:raise AssertionError('Pet store prefix retracted')
        for address,width,value in p.stores[self.applied_stores:]:self.scalar_state[address]=(width,value)
        self.applied_stores=len(p.stores)
    def step(self,settings_text,runtime_text):
        self.sync_document()
        self.last=None;previous=self.settings.frame
        try:settings=self.settings.step(settings_text)
        finally:
            if self.settings.frame is not previous:self._invalidate_worker()
        if not settings.complete:self.missing='Pet ayarları: '+settings.missing;return None
        try:data=json.loads(runtime_text)
        except (TypeError,ValueError) as error:raise ValueError('Pet çalışma gözlemleri nesne olmalı') from error
        if type(data) is not dict:raise ValueError('Pet çalışma gözlemleri nesne olmalı')
        if not data:self.missing='Pet çalışma örneği bekleniyor';return None
        digest=protection_snapshot_digest(self.settings.snapshot)
        if data.get('panel_snapshot_sha256')!=digest:raise ValueError('Pet paneli değişti; çalışma örneğini yenileyin')
        token=data.get('invocation_id')
        if type(token) is not int or not 0<token<=0xffffffff:raise ValueError('Pozitif DWORD Pet örnek numarası gerekli')
        if self.frame is None or token!=self.active_token:
            if token<=self.last_token:raise ValueError('Eski Pet örnek numarası yeniden kullanılamaz')
            entry=data.get('entry_reached',False)
            if type(entry) is not bool:raise ValueError('Pet yordam giriş gözlemi boolean olmalı')
            if not entry:self.missing='Pet yordamına giriş bekleniyor';return None
            self.frame=PetFrame();self.active_token=self.last_token=token;self.applied_stores=0
            self.config_shadow=dict(self.settings.scalar_state)
        try:
            for _ in range(512):
                p=self.frame.advance(PetObservation());self._apply(p)
                if p.complete:self.last=p;self.missing='';return p
                kind,key=p.needed;values=object_field(data,kind)
                if kind=='normal_returns':
                    if key not in values or values[key] is False:self.last=p;self.missing=p.missing;return p
                    if type(values[key]) is not bool:raise ValueError('Pet helper dönüşü boolean olmalı: '+key)
                    incoming=PetObservation(normal_returns={key:True})
                else:
                    known=None
                    if key in CONFIG_OFFSETS:known=self.config_shadow.get(CONTEXT+CONFIG_OFFSETS[key])
                    elif key in TIMER_ADDRESSES:known=self.scalar_state.get(TIMER_ADDRESSES[key])
                    if key in CONFIG_OFFSETS and known is None:
                        self.last=p;self.missing='Önceki Pet mod değeri bilinmiyor';return p
                    if known is not None:
                        value=known[1]
                        if key in values and (type(values[key]) is not int or values[key]!=value):
                            raise ValueError('Pet yerel alanı gözlemle değiştirilemez: '+key)
                    elif key in values:value=values[key]
                    else:self.last=p;self.missing=p.missing;return p
                    width=p.reads[-1][2]
                    if type(value) is not int or not 0<=value<1<<(8*width):raise ValueError('Pet alan genişliği geçersiz: '+key)
                    incoming=PetObservation(values={key:value})
                p=self.frame.advance(incoming);self._apply(p)
            raise AssertionError('Owned Pet adapter budget exceeded')
        except (ValueError,TypeError):
            self._apply(self.frame.advance(PetObservation()))
            raise

def example_pet_runtime_sample(snapshot,trial):
    trial.sync_document()
    token=trial.last_token+1
    if token>0xffffffff:raise ValueError('Pet örnek sayacı doldu; önizlemeyi sıfırlayın')
    own={slot:value for slot,_,value in snapshot[0]}
    mode=next((number for slot,number in ((0xf28,1),(0xf24,2),(0xf20,3)) if own[slot]),0)
    clock=(token*10000)&0xffffffff
    v=dict(busy_vip_eax=0,busy_supply_eax=0,float_compare_status=0x4000,
      state_eax=0,pet_exists_eax=1,pet_mode_eax=mode,
      mode_clock_eax=clock,mode_post_clock_eax=(clock+1)&0xffffffff,
      food_clock_eax=clock,food_post_clock_eax=(clock+2)&0xffffffff,hunger_eax=5,
      class_eax=1,summon_item_eax=1,actor_eax=0,target_initial_eax=0,
      target_flag_eax=0,target_fresh_eax=0,summon_ready_eax=0,
      summon_clock_eax=clock,self_id_eax=7,food_item_14_eax=FOOD_IDS[0])
    for key,offset in (('state',16),('float_gate',20),('class',24),('actor',28),('target_flag',32)):
        v.update({key+'_root_slot':0x1000,key+'_root_eax':0x2000,key+'_offset':offset})
    for key,address in TIMER_ADDRESSES.items():
        if address not in trial.scalar_state:v[key]=0
    normals={key[:-4]:True for key in v if key.endswith('_eax')}
    normals.update({key:True for key in ('float_gate','summon','cancel_actor','clear_target','set_mode','feed')})
    return json.dumps(dict(panel_snapshot_sha256=protection_snapshot_digest(snapshot),
      invocation_id=token,entry_reached=True,synthetic_example=True,
      example_policy='owned stable panel and timers; explicit synthetic helper/FPU/clock captures; no game action',
      values=v,normal_returns=normals))

def describe_pet_trial(trial):
    settings=trial.settings.last;p=trial.last
    return {'ayarlar_tamam':settings.complete if settings else False,
      'pet_yordamı_tamam':p.complete if p else False,'sonuç':p.status if p else 'bekleniyor',
      'eksik':trial.missing,'bilinen_ayar':len(trial.settings.scalar_state),
      'yordam_yazım_öneki':len(p.stores) if p else 0,
      'yerel_önizleme':True,'oyun_eylemi_doğrulandı':False}
