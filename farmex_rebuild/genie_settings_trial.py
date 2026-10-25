"""Five owned Genie flags -> bounded source producer -> local shadow only."""
import json
from genie_settings import GENIE_SETTING_FIELDS,GENIE_SETTING_INPUTS,GenieSettingsFrame
from protection_panel_trial import ProtectionSettingsTrial,protection_snapshot_digest


class GenieSettingsTrial(ProtectionSettingsTrial):
    _frame_type=GenieSettingsFrame
    _snapshot_error='Genie ayarları değişti; önizleme örneğini yenileyin'
    def __init__(self,reader):super().__init__(reader,None)
    def current_snapshot(self):
        if self.reader is None:raise ValueError('Genie panel okuyucusu gerekli')
        values,_=self.reader();fields=[]
        for slot,path in GENIE_SETTING_FIELDS:
            value=values.get(path)
            if type(value) is not bool:raise ValueError('Genie onay kutusu değeri gerekli: '+path)
            fields.append((slot,'checked',value))
        return tuple(fields),None


def example_genie_settings_sample(snapshot):
    return json.dumps(dict(panel_snapshot_sha256=protection_snapshot_digest(snapshot),synthetic_example=True,
      example_policy='own five panel flags and explicit synthetic getter returns; native VCL unverified',
      entry_reached=True,normal_returns={'checked_%03x'%slot:True for slot,_,_ in snapshot[0]}))


def describe_genie_settings_trial(trial):
    p=trial.last
    if p is None:return 'Geçerli Genie ayar önizlemesi yok'
    return {'ayar_bloğu_tamam':p.complete,'eksik':p.missing,'bilinen_yerel_alan':len(trial.scalar_state),
      'yerel_önizleme':True,'oyunda_uygulama_doğrulandı':False}
