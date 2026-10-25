"""Compile confirmed UI fields into independent rules; no game side effects."""
from potion_engine import PotionSettings

HEALTH_PREFIX = 'frmMain/MainTab/SheetGenel/Groupdstk/'


def compile_potions(values):
    def get(name):
        key = HEALTH_PREFIX + name
        if key not in values:
            raise ValueError('Eksik sağlık ayarı: ' + name)
        return values[key]
    def threshold(name):
        value = get(name)
        if not isinstance(value, str):
            raise ValueError('Yüzde alanı metin olmalı: ' + name)
        try:
            result = int(value)
        except ValueError:
            raise ValueError('Yüzde tam sayı olmalı: ' + name)
        if not 0 <= result <= 100:
            raise ValueError('Yüzde 0–100 arasında olmalı: ' + name)
        return result
    def index(name):
        value = get(name)
        if type(value) is not int or not -1 <= value <= 12:
            raise ValueError('İksir seçimi geçersiz: ' + name)
        # -1 matches no explicit source branch, as does automatic index0.
        return max(0, value)
    return PotionSettings(hp_enabled=get('chhp'), hp_threshold=threshold('txthp'),
        hp_combo_index=index('cmbhppot'), mp_enabled=get('chmp'),
        mp_threshold=threshold('txtmp'), mp_combo_index=index('cmbmppot'))
