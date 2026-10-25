"""Own15-field panel trial for the bounded source settings producer."""
from control_settings import OPS,CONTROL_SETTING_FIELDS,ControlSettingsFrame
from protection_panel_trial import ProtectionSettingsTrial,example_protection_sample

CONTROL_SETTING_INPUTS=tuple(path for _,path in CONTROL_SETTING_FIELDS)

class ControlSettingsTrial(ProtectionSettingsTrial):
 _frame_type=ControlSettingsFrame
 _snapshot_error='Kontrol ayarları değişti; önizleme örneğini yenileyin'
 def __init__(self,reader):super().__init__(reader,None)
 def current_snapshot(self):
  if self.reader is None:raise ValueError('Kontrol panel okuyucusu gerekli')
  values,_=self.reader();fields=[]
  for op,(_,path) in zip(OPS,CONTROL_SETTING_FIELDS):
   kind,slot=op[:2];value=values.get(path)
   if kind=='flag' and type(value) is not bool:raise ValueError('Kontrol onay kutusu gerekli: '+path)
   if kind!='flag' and type(value) is not str:raise ValueError('Kontrol metin değeri gerekli: '+path)
   fields.append((slot,'checked' if kind=='flag' else kind,value))
  return tuple(fields),None

def example_control_settings_sample(snapshot):
 return example_protection_sample(snapshot,_ops=OPS,_prologue=False)

def describe_control_settings_trial(trial):
 p=trial.last
 if p is None:return 'Geçerli Kontrol ayar önizlemesi yok'
 low=trial.scalar_state.get(0x562194+0xc8);high=trial.scalar_state.get(0x562194+0xcc)
 coin=None
 if low is not None and high is not None:
  coin=low[1]|(high[1]<<32)
  if coin&(1<<63):coin-=1<<64
 return {'ayar_bloğu_tamam':p.complete,'eksik':p.missing,'bilinen_yerel_alan':len(trial.scalar_state),
         'coin_eşiği':coin,'yerel_önizleme':True,'oyunda_uygulama_doğrulandı':False}
