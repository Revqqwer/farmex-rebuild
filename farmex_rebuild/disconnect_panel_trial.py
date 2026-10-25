"""Fourteen own DC controls -> bounded producer -> persistent local shadow."""
from collections.abc import Mapping
from disconnect_settings import OPS,DC_SETTING_FIELDS,DC_SETTING_INPUTS,DisconnectSettingsFrame
from protection_panel_trial import (ProtectionSettingsTrial,example_protection_sample,
                                    protection_snapshot_digest)
from name_codec import WindowsNameCodec

KINDS={op[1]:op[0] for op in OPS if op[0]!='constant'}
ROUTE_SLOT=0x84c


def disconnect_snapshot(values,route_sample):
    if type(route_sample) is not tuple or len(route_sample)!=2 or not isinstance(route_sample[0],Mapping):
        raise ValueError('DC rota Text ve açık kod sayfası gerekli')
    texts,codepage=route_sample
    if type(codepage) is not int or not 1<=codepage<=65535:raise ValueError('Geçerli kod sayfası gerekli')
    result=[]
    for slot,path in DC_SETTING_FIELDS:
        kind=KINDS[slot];value=texts.get(path) if slot==ROUTE_SLOT else values.get(path)
        if kind=='flag' and type(value) is not bool:raise ValueError('DC onay kutusu değeri gerekli: '+path)
        if kind=='index' and (type(value) is not int or not -1<=value<1<<31):raise ValueError('DC seçim indeksi gerekli: '+path)
        if kind in ('number','string') and type(value) is not str:raise ValueError('DC metin değeri gerekli: '+path)
        result.append((slot,'checked' if kind=='flag' else kind,value))
    return tuple(result),codepage


class DisconnectSettingsTrial(ProtectionSettingsTrial):
    _frame_type=DisconnectSettingsFrame
    _snapshotter=staticmethod(disconnect_snapshot)
    _snapshot_error='DC ayarları veya rota metni değişti; önizleme örneğini yenileyin'


def example_disconnect_sample(snapshot,codec_factory=WindowsNameCodec):
    return example_protection_sample(snapshot,codec_factory,_ops=OPS,_prologue=False)


def describe_disconnect_trial(trial):
    p=trial.last
    if p is None:return 'Geçerli DC ayar önizlemesi yok'
    selected=trial.scalar_state.get(0x562224,(None,None))[1]
    return {'ayar_bloğu_tamam':p.complete,'eksik':p.missing,
      'bilinen_yerel_sayısal_alan':len(trial.scalar_state),'bilinen_yerel_metin_alanı':len(trial.string_state),
      'işlem_seçimi':{0:'PC Kapat',1:'Oyunu Kapat',2:'Relog At'}.get(selected,'Henüz bilinmiyor'),
      'yerel_önizleme':True,'oyunda_uygulama_doğrulandı':False}
