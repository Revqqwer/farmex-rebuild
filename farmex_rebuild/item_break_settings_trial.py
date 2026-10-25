"""Three real panel values -> bounded settings frame -> own persistent shadow."""
import json
from dataclasses import replace
from item_break_settings import OPS,ITEM_BREAK_FIELDS,ItemBreakSettingsFrame,ItemBreakSettingsObservation
from protection_panel_trial import (advance_protection_sample,example_protection_sample,
                                    object_field,protection_snapshot_digest)

ITEM_BREAK_SETTING_INPUTS=tuple(path for _,path in ITEM_BREAK_FIELDS)

class ItemBreakSettingsTrial:
    def __init__(self,reader):self.reader=reader;self.reset()
    def reset(self):
        self.snapshot=None;self.frame=None;self.last=None;self.scalar_state={};self.applied_stores=0
    def current_snapshot(self):
        if self.reader is None:raise ValueError('Item kırma panel okuyucusu gerekli')
        values,_=self.reader();fields=[]
        for slot,path in ITEM_BREAK_FIELDS:
            value=values.get(path);kind='number' if slot==0xec8 else 'checked'
            if kind=='number' and type(value) is not str:raise ValueError('Item kırma hız metni gerekli')
            if kind=='checked' and type(value) is not bool:raise ValueError('Item kırma onay/seçim değeri gerekli')
            fields.append((slot,kind,value))
        return tuple(fields),None
    def _apply(self,plan):
        if len(plan.stores)<self.applied_stores:raise AssertionError('Item settings prefix retracted')
        for address,width,value in plan.stores[self.applied_stores:]:self.scalar_state[address]=(width,value)
        self.applied_stores=len(plan.stores)
    def step(self,text):
        self.last=None;snapshot=self.current_snapshot()
        if snapshot!=self.snapshot:
            self.snapshot=snapshot;self.frame=ItemBreakSettingsFrame();self.applied_stores=0
        try:data=json.loads(text)
        except (TypeError,ValueError) as error:raise ValueError('Item kırma örneği JSON nesnesi olmalı') from error
        if type(data) is not dict:raise ValueError('Item kırma örneği JSON nesnesi olmalı')
        if 'panel_snapshot_sha256' in data and data['panel_snapshot_sha256']!=protection_snapshot_digest(snapshot):
            raise ValueError('Item kırma ayarları değişti; önizleme örneğini yenileyin')
        own={slot:value for slot,kind,value in snapshot[0]};incoming=ItemBreakSettingsObservation()
        try:
            advance_protection_sample(self.frame.prefix,snapshot,data)
            for _ in range(6):
                plan=self.frame.advance(incoming);self._apply(plan)
                if plan.complete or isinstance(plan.needed,tuple):self.last=plan;return plan
                if plan.needed in ('reset_checked_returned','toggle_returned'):
                    key='reset_checked_a28' if plan.needed=='reset_checked_returned' else 'toggle'
                    normals=object_field(data,'normal_returns')
                    if key in normals and type(normals[key]) is not bool:raise ValueError('Ayrı helper dönüşü boolean olmalı')
                    if normals.get(key) is not True:self.last=plan;return plan
                    incoming=replace(incoming,**{plan.needed:True})
                else:
                    # This is a stable OWN-state read, not a claim that native
                    # VCL helpers preserve the source process configuration.
                    value=int(own[0xa28]) if plan.needed=='reset_checked_eax' else self.scalar_state[0x569a20][1]
                    key='checked_a28' if plan.needed=='reset_checked_eax' else 'fresh_enabled_byte'
                    captures=object_field(data,'values')
                    if key in captures and (type(captures[key]) is not int or captures[key]!=value):
                        raise ValueError('Panel veya kendi yerel alan okuması değiştirilemez')
                    incoming=replace(incoming,**{plan.needed:value})
        except ValueError:
            self._apply(self.frame.advance(ItemBreakSettingsObservation()))
            raise
        raise AssertionError('Item settings panel capture budget exceeded')

def example_item_break_settings_sample(snapshot):
    data=json.loads(example_protection_sample(snapshot,_ops=OPS,_prologue=False))
    data['normal_returns'].update(reset_checked_a28=True,toggle=True)
    data['example_policy']='own signed-decimal64 subset and stable local shadow read; source native helpers/fresh state unverified'
    return json.dumps(data,ensure_ascii=False)

def describe_item_break_settings_trial(trial):
    plan=trial.last
    if plan is None:return 'Geçerli item kırma ayar önizlemesi yok'
    return {'ayar_bloğu_tamam':plan.complete,'beklenen':plan.needed,'bilinen_yerel_alan':len(trial.scalar_state),
            'başlat_durdur_argümanı':plan.toggle_argument,'yerel_önizleme':True,'oyunda_uygulama_doğrulandı':False}
